/*
 * vgtp.h — Vector Graphics Transport Protocol, DATA channel
 *
 * Wire format is little-endian throughout (Pico-native).
 * All multi-byte fields are LE.
 *
 * DATA packet layout (14-byte header + payload):
 *
 *   offset  size  field
 *   0       1     version       (0x01)
 *   1       1     type          (VGTP_TYPE_*)
 *   2       2     seq           monotonic, 16-bit wrapping
 *   4       2     frame_id      groups packets into one rendered frame
 *   6       2     payload_len   bytes of payload following the header
 *   8       4     timestamp     sender ms tick (informational)
 *   12      2     crc           CRC16-CCITT over full packet with crc=0; 0=skip check
 *   14      *     payload       type-specific (see below)
 *
 * DRAW payload contains exactly one primitive:
 *
 *   RECT:  [ uint8 prim_type=0x01 | int16 x | int16 y | uint16 w | uint16 h | uint16 color ]
 *   TEXT:  [ uint8 prim_type=0x02 | int16 x | int16 y | uint16 fg | uint16 bg | uint8 len | char text[len] ]
 *   LINE:  [ uint8 prim_type=0x03 | int16 x0 | int16 y0 | int16 x1 | int16 y1 | uint16 color ]
 *   BITMAP:[ uint8 prim_type=0x04 | int16 x | int16 y | uint8 w | uint8 h | uint16 dw | uint16 dh | uint16 pixels[w*h] ] (max 115 px)
 *   CIRCLE:[ uint8 prim_type=0x05 | int16 cx | int16 cy | uint16 r | uint16 color ]
 *
 * CLEAR payload: [ uint16 color ]
 * FRAME_END / HEARTBEAT: no payload
 */

#ifndef VGTP_H
#define VGTP_H

#include <stdint.h>
#include <stdbool.h>

/* ----------- */
/*  Constants  */
/* ----------- */

#define VGTP_VERSION         0x01

#define VGTP_DATA_PORT       1234   /* DATA channel UDP port  */
#define VGTP_CTRL_PORT       1235   /* CONTROL channel UDP port */

/* Packet types */
#define VGTP_TYPE_DRAW         0x01
#define VGTP_TYPE_CLEAR        0x02
#define VGTP_TYPE_FRAME_END    0x03
#define VGTP_TYPE_HEARTBEAT    0x04
#define VGTP_TYPE_CANVAS       0x05   /* write tile directly into persistent canvas_buf */
#define VGTP_TYPE_CANVAS_CLEAR 0x06   /* fill canvas_buf with color (or black) */

/* Max pixels per CANVAS tile: (PKT_MAX_SIZE - VGTP_HEADER_SIZE - sizeof(vgtp_canvas_tile_t)) / 2 */
#define CANVAS_MAX_PIXELS      116

/* Primitive sub-types (first byte of DRAW payload) */
#define VGTP_PRIM_RECT       0x01
#define VGTP_PRIM_TEXT       0x02
#define VGTP_PRIM_LINE       0x03
#define VGTP_PRIM_BITMAP     0x04
#define VGTP_PRIM_CIRCLE     0x05

#define VGTP_HEADER_SIZE     14     /* sizeof(vgtp_data_hdr_t) */

/* -------------------------------------------------------------------- */
/*  Wire structs  (packed — do not access fields unaligned on non-x86)  */
/* -------------------------------------------------------------------- */

typedef struct __attribute__((packed)) {
    uint8_t  version;
    uint8_t  type;
    uint16_t seq;
    uint16_t frame_id;
    uint16_t payload_len;
    uint32_t timestamp;
    uint16_t crc;
    /* payload follows immediately */
} vgtp_data_hdr_t;

/* DRAW payload — RECT primitive */
typedef struct __attribute__((packed)) {
    uint8_t  prim_type;     /* VGTP_PRIM_RECT */
    int16_t  x, y;
    uint16_t w, h;
    uint16_t color;         /* RGB565 */
} vgtp_prim_rect_t;         /* 11 bytes */

/* DRAW payload — TEXT primitive */
typedef struct __attribute__((packed)) {
    uint8_t  prim_type;     /* VGTP_PRIM_TEXT */
    int16_t  x, y;
    uint16_t fg, bg;        /* RGB565 */
    uint8_t  len;
    /* char text[len] follows */
} vgtp_prim_text_hdr_t;     /* 10 bytes + text */

/* DRAW payload — LINE primitive */
typedef struct __attribute__((packed)) {
    uint8_t  prim_type;     /* VGTP_PRIM_LINE */
    int16_t  x0, y0;
    int16_t  x1, y1;
    uint16_t color;         /* RGB565 */
} vgtp_prim_line_t;         /* 11 bytes */

/* DRAW payload — BITMAP primitive */
typedef struct __attribute__((packed)) {
    uint8_t  prim_type;     /* VGTP_PRIM_BITMAP */
    int16_t  x, y;          /* top-left destination corner */
    uint8_t  w, h;          /* source tile dimensions; max w*h = 115 pixels */
    uint16_t dw, dh;        /* destination display size (0,0 = use src size) */
    /* uint16_t pixels[w*h] follow — RGB565, row-major */
} vgtp_prim_bitmap_hdr_t;   /* 11 bytes */

/* DRAW payload — CIRCLE primitive */
typedef struct __attribute__((packed)) {
    uint8_t  prim_type;     /* VGTP_PRIM_CIRCLE */
    int16_t  cx, cy;
    uint16_t r;
    uint16_t color;         /* RGB565 */
} vgtp_prim_circle_t;       /* 9 bytes */

/* CANVAS tile payload — no prim_type prefix (packet type alone identifies it) */
typedef struct __attribute__((packed)) {
    int16_t  x, y;          /* top-left destination corner in canvas_buf */
    uint8_t  w, h;          /* source tile dimensions; max w*h = CANVAS_MAX_PIXELS */
    uint16_t dw, dh;        /* destination display size (0,0 = use src size) */
    /* uint16_t pixels[w*h] follow — RGB565, row-major */
} vgtp_canvas_tile_t;       /* 10 bytes */

/* CLEAR payload */
typedef struct __attribute__((packed)) {
    uint16_t color;         /* RGB565 */
} vgtp_payload_clear_t;     /* 2 bytes */

/* ---------------------------------------------------------------------- */
/*  CONTROL channel                                                       */
/*                                                                        */
/*  CONTROL packet layout (11 bytes, little-endian):                      */
/*                                                                        */
/*   offset  size  field                                                  */
/*   0       1     version                                                */
/*   1       1     type          (VGTP_CTRL_*)                            */
/*   2       2     ack_seq       highest contiguous DATA seq received     */
/*   4       4     ack_bitmap    bit i = packet ack_seq+i+1 received      */
/*   8       2     adv_window    receiver free buffer capacity (packets)  */
/*   10      1     error_code    0 = no error                             */
/* ---------------------------------------------------------------------- */

/* CONTROL packet types */
#define VGTP_CTRL_ACK        0x01
#define VGTP_CTRL_FLOW       0x02
#define VGTP_CTRL_ERROR      0x03
#define VGTP_CTRL_HEARTBEAT  0x04
#define VGTP_CTRL_HELLO      0x05
#define VGTP_CTRL_HELLO_ACK  0x06

typedef struct __attribute__((packed)) {
    uint8_t  version;
    uint8_t  type;
    uint16_t ack_seq;
    uint32_t ack_bitmap;
    uint16_t adv_window;
    uint8_t  error_code;
} vgtp_ctrl_hdr_t;   /* 11 bytes */

/*
 * HELLO / HELLO_ACK payload — appended after vgtp_ctrl_hdr_t.
 * Sender proposes params; receiver echoes back accepted values.
 */
typedef struct __attribute__((packed)) {
    uint16_t mtu;              /* max DATA payload bytes per packet    */
    uint16_t window;           /* packet queue depth (flow control)    */
    uint8_t  mode;             /* delivery mode: 0=unreliable          */
    uint16_t retx_timeout_ms;  /* retransmit timeout (0 = N/A mode 0)  */
} vgtp_hello_payload_t;  /* 7 bytes */

/* --------------------------------------- */
/*  Sequence number comparison (mod-2^16)  */
/* --------------------------------------- */
static inline bool vgtp_seq_newer(uint16_t a, uint16_t b)
{
    return (int16_t)(a - b) > 0;
}

/* ------------------------------------------------------------------ */
/*  CRC16-CCITT (poly 0x1021, init 0xFFFF)                            */
/*  Computed over the full packet with the crc field set to 0.        */
/*  Returns 0 if crc field in packet is 0 (skip check convention).    */
/* ------------------------------------------------------------------ */
uint16_t vgtp_crc16(const uint8_t *data, uint16_t len);
bool     vgtp_packet_crc_ok(const uint8_t *packet, uint16_t total_len);

#endif /* VGTP_H */
