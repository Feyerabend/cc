/*
 * protocol.c — VGTP DATA channel parser and frame assembler
 *
 * Raw packet queue (SPSC, both sides on Core 0 under RTOS):
 *   net_task   → protocol_push_packet() → ring buffer (producer)
 *   protocol_task                       → ring buffer (consumer)
 * No locking needed: tasks never run concurrently on the same core.
 *
 * Frame assembly:
 *   CLEAR       → reset build_scene, record clear color
 *   DRAW        → parse primitive, append to build_scene
 *   FRAME_END   → swap buffers (scene_swap)
 *   HEARTBEAT   → ignored for now
 */

#include "protocol.h"
#include "vgtp.h"
#include "scene.h"
#include "display.h"
#include "net.h"
#include "rtos.h"
#include <string.h>

/* ------------------ */
/*  Raw packet queue  */
/* ------------------ */

typedef struct {
    uint8_t  data[PKT_MAX_SIZE];
    uint16_t len;
} raw_pkt_t;

static raw_pkt_t pkt_ring[PKT_QUEUE_LEN];
static volatile uint8_t pkt_head = 0;   /* writer index (net_task) */
static volatile uint8_t pkt_tail = 0;   /* reader index (protocol_task) */

void protocol_push_packet(const uint8_t *data, uint16_t len)
{
    uint8_t next_head = (pkt_head + 1) % PKT_QUEUE_LEN;
    if (next_head == pkt_tail) return;   /* queue full — drop */

    uint16_t copy_len = len < PKT_MAX_SIZE ? len : PKT_MAX_SIZE;
    memcpy(pkt_ring[pkt_head].data, data, copy_len);
    pkt_ring[pkt_head].len = copy_len;
    pkt_head = next_head;
}

static bool queue_pop(raw_pkt_t **out)
{
    if (pkt_tail == pkt_head) return false;
    *out = &pkt_ring[pkt_tail];
    return true;
}

static void queue_advance(void)
{
    pkt_tail = (pkt_tail + 1) % PKT_QUEUE_LEN;
}

/* ------------------------------------------------------------------ */
/*  Colour byte-swap                                                  */
/*                                                                    */
/*  display_blit_full uses 8-bit DMA (sends low byte first).          */
/*  The ST7789V2 expects the high byte first, so every RGB565 colour  */
/*  written to the framebuffer must be byte-swapped.                  */
/*  We do this once here when reading colours off the wire.           */
/* ------------------------------------------------------------------ */
static inline uint16_t color_for_fb(uint16_t c)
{
    return (uint16_t)((c >> 8) | (c << 8));
}

/* ------------- */
/*  Frame state  */
/* ------------- */

static uint16_t build_frame_id  = 0xFFFF;   /* sentinel: no frame started */
static uint16_t frame_highest_seq = 0;      /* highest seq seen in current frame */

/* Temp buffer for canvas tile pixel byte-swap (static avoids ~230 B stack hit) */
static uint16_t canvas_tmp[CANVAS_MAX_PIXELS];

static void reset_build_scene(uint16_t frame_id, uint16_t clear_color, bool has_clear)
{
    /* Cast away volatile for the memset — safe since Core 1 only reads render_scene */
    scene_buffer_t *s = (scene_buffer_t *)build_scene;
    s->frame_id    = frame_id;
    s->has_clear   = has_clear;
    s->clear_color = clear_color;
    s->prim_count  = 0;
    build_frame_id = frame_id;
}

/* --------------- */
/*  Packet parser  */
/* --------------- */

static void process_packet(const raw_pkt_t *pkt)
{
    if (pkt->len < VGTP_HEADER_SIZE) return;

    const vgtp_data_hdr_t *hdr = (const vgtp_data_hdr_t *)pkt->data;

    if (hdr->version != VGTP_VERSION)    return;
    if (!vgtp_packet_crc_ok(pkt->data, pkt->len)) return;

    const uint8_t *payload     = pkt->data + VGTP_HEADER_SIZE;
    uint16_t       payload_len = hdr->payload_len;

    /* Canvas types bypass the scene buffer entirely */
    if (hdr->type == VGTP_TYPE_CANVAS) {
        if (payload_len < sizeof(vgtp_canvas_tile_t)) return;
        const vgtp_canvas_tile_t *ct = (const vgtp_canvas_tile_t *)payload;
        uint16_t npix = (uint16_t)ct->w * ct->h;
        if (npix > CANVAS_MAX_PIXELS) return;
        if (payload_len < sizeof(vgtp_canvas_tile_t) + npix * 2u) return;
        const uint16_t *src = (const uint16_t *)(payload + sizeof(vgtp_canvas_tile_t));
        for (uint16_t j = 0; j < npix; j++)
            canvas_tmp[j] = color_for_fb(src[j]);
        uint16_t dw = ct->dw ? ct->dw : ct->w;
        uint16_t dh = ct->dh ? ct->dh : ct->h;
        fb_blit_scaled(canvas_buf, canvas_tmp, ct->w, ct->h, ct->x, ct->y, dw, dh);
        g_canvas_used = true;
        return;
    }

    if (hdr->type == VGTP_TYPE_CANVAS_CLEAR) {
        uint16_t color = 0x0000;
        if (payload_len >= 2) {
            const vgtp_payload_clear_t *c = (const vgtp_payload_clear_t *)payload;
            color = color_for_fb(c->color);
        }
        canvas_clear(color);
        return;
    }

    /* Track highest seq in this frame */
    if (vgtp_seq_newer(hdr->seq, frame_highest_seq) || build_frame_id == 0xFFFF)
        frame_highest_seq = hdr->seq;

    /* If this packet belongs to a new frame, reset the build buffer */
    if (hdr->frame_id != build_frame_id) {
        reset_build_scene(hdr->frame_id, 0x0000, false);
    }

    scene_buffer_t *s = (scene_buffer_t *)build_scene;

    switch (hdr->type) {

    case VGTP_TYPE_CLEAR: {
        if (payload_len >= sizeof(vgtp_payload_clear_t)) {
            const vgtp_payload_clear_t *c = (const vgtp_payload_clear_t *)payload;
            s->has_clear   = true;
            s->clear_color = color_for_fb(c->color);
        } else {
            s->has_clear   = true;
            s->clear_color = 0x0000;   /* default black */
        }
        break;
    }

    case VGTP_TYPE_DRAW: {
        if (payload_len < 1) break;
        if (s->prim_count >= MAX_PRIMS) break;

        primitive_t *p = &s->prims[s->prim_count];

        switch (payload[0]) {

        case VGTP_PRIM_RECT: {
            if (payload_len < sizeof(vgtp_prim_rect_t)) break;
            const vgtp_prim_rect_t *r = (const vgtp_prim_rect_t *)payload;
            p->type       = PRIM_RECT;
            p->rect.x     = r->x;
            p->rect.y     = r->y;
            p->rect.w     = r->w;
            p->rect.h     = r->h;
            p->rect.color = color_for_fb(r->color);
            s->prim_count++;
            break;
        }

        case VGTP_PRIM_TEXT: {
            if (payload_len < sizeof(vgtp_prim_text_hdr_t)) break;
            const vgtp_prim_text_hdr_t *t = (const vgtp_prim_text_hdr_t *)payload;
            uint8_t text_len = t->len < PRIM_TEXT_MAX ? t->len : PRIM_TEXT_MAX;
            /* ensure there are enough bytes for the text */
            if (payload_len < sizeof(vgtp_prim_text_hdr_t) + text_len) break;
            p->type    = PRIM_TEXT;
            p->text.x  = t->x;
            p->text.y  = t->y;
            p->text.fg = color_for_fb(t->fg);
            p->text.bg = color_for_fb(t->bg);
            memcpy(p->text.text, payload + sizeof(vgtp_prim_text_hdr_t), text_len);
            p->text.text[text_len] = '\0';
            s->prim_count++;
            break;
        }

        case VGTP_PRIM_LINE: {
            if (payload_len < sizeof(vgtp_prim_line_t)) break;
            const vgtp_prim_line_t *l = (const vgtp_prim_line_t *)payload;
            p->type        = PRIM_LINE;
            p->line.x0     = l->x0;
            p->line.y0     = l->y0;
            p->line.x1     = l->x1;
            p->line.y1     = l->y1;
            p->line.color  = color_for_fb(l->color);
            s->prim_count++;
            break;
        }

        case VGTP_PRIM_BITMAP: {
            if (payload_len < sizeof(vgtp_prim_bitmap_hdr_t)) break;
            const vgtp_prim_bitmap_hdr_t *bm = (const vgtp_prim_bitmap_hdr_t *)payload;
            uint16_t npix = (uint16_t)bm->w * bm->h;
            if (npix > BITMAP_MAX_PIXELS) break;
            if (payload_len < sizeof(vgtp_prim_bitmap_hdr_t) + npix * 2u) break;
            p->type      = PRIM_BITMAP;
            p->bitmap.x  = bm->x;
            p->bitmap.y  = bm->y;
            p->bitmap.w  = bm->w;
            p->bitmap.h  = bm->h;
            p->bitmap.dw = bm->dw ? bm->dw : bm->w;
            p->bitmap.dh = bm->dh ? bm->dh : bm->h;
            const uint16_t *src = (const uint16_t *)(payload + sizeof(vgtp_prim_bitmap_hdr_t));
            for (uint16_t j = 0; j < npix; j++)
                p->bitmap.pixels[j] = color_for_fb(src[j]);
            s->prim_count++;
            break;
        }

        case VGTP_PRIM_CIRCLE: {
            if (payload_len < sizeof(vgtp_prim_circle_t)) break;
            const vgtp_prim_circle_t *c = (const vgtp_prim_circle_t *)payload;
            p->type         = PRIM_CIRCLE;
            p->circle.cx    = c->cx;
            p->circle.cy    = c->cy;
            p->circle.r     = c->r;
            p->circle.color = color_for_fb(c->color);
            s->prim_count++;
            break;
        }

        default:
            break;
        }
        break;
    }

    case VGTP_TYPE_FRAME_END: {
        scene_swap();

        /* Send CONTROL ACK back to sender */
        vgtp_ctrl_hdr_t ack = {
            .version    = VGTP_VERSION,
            .type       = VGTP_CTRL_ACK,
            .ack_seq    = frame_highest_seq,
            .ack_bitmap = 0,
            .adv_window = 1,
            .error_code = 0,
        };
        net_queue_control((const uint8_t *)&ack, sizeof(ack));

        build_frame_id = 0xFFFF;
        break;
    }

    case VGTP_TYPE_HEARTBEAT:
        break;   /* nothing for now */

    default:
        break;
    }
}

/* ----------- */
/*  RTOS task  */
/* ----------- */

void protocol_task(void *param)
{
    (void)param;
    while (1) {
        raw_pkt_t *pkt;
        if (queue_pop(&pkt)) {
            process_packet(pkt);
            queue_advance();
        } else {
            task_delay(2);   /* nothing to do — yield for 2 ms */
        }
    }
}
