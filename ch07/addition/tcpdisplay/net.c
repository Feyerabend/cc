#include "net.h"
#include "config.h"
#include "rtos.h"

#include "pico/cyw43_arch.h"
#include "lwip/tcp.h"
#include "lwip/ip_addr.h"

#include <string.h>
#include <stdio.h>

/* Receive ring buffer
 * recv_cb appends incoming TCP data here.
 * net_stream_poll() reads from it, looking for the FRAME\n delimiter.
 * With pico_cyw43_arch_lwip_poll both run on core 0 inside cyw43_arch_poll(),
 * so no locking is needed.
 */
#define RING_SIZE   16384u
static char          s_ring[RING_SIZE];
static size_t        s_ring_wr  = 0;    /* bytes written  */
static size_t        s_ring_rd  = 0;    /* bytes consumed */

static inline size_t ring_available(void) { return s_ring_wr - s_ring_rd; }
static inline char   ring_at(size_t i)    { return s_ring[i % RING_SIZE]; }

static void ring_append(const void *data, size_t len) {
    const char *p = (const char *)data;
    for (size_t i = 0; i < len; i++) {
        if (s_ring_wr - s_ring_rd < RING_SIZE)
            s_ring[(s_ring_wr++) % RING_SIZE] = p[i];
        /* if full, oldest data silently dropped - shouldn't happen at 30 fps */
    }
    g_total_bytes += (uint32_t)len;
}

/* TCP stream state */

typedef enum { SS_IDLE, SS_CONNECTING, SS_CONNECTED, SS_ERROR } stream_state_t;

static struct {
    volatile stream_state_t  state;
    struct tcp_pcb          *pcb;
} s;

/* lwIP callbacks */

static void stream_close(void) {
    if (s.pcb) {
        tcp_arg (s.pcb, NULL);
        tcp_recv(s.pcb, NULL);
        tcp_err (s.pcb, NULL);
        tcp_close(s.pcb);
        s.pcb = NULL;
    }
}

static void err_cb(void *arg, err_t err) {
    (void)arg; (void)err;
    s.pcb   = NULL;
    s.state = SS_ERROR;
}

static err_t recv_cb(void *arg, struct tcp_pcb *pcb, struct pbuf *p, err_t err) {
    (void)arg; (void)pcb;
    g_recv_cb_count++;
    if (!p || err != ERR_OK) {
        s.state = SS_ERROR;
        if (p) pbuf_free(p);
        return ERR_OK;
    }
    tcp_recved(pcb, p->tot_len);
    for (struct pbuf *q = p; q; q = q->next)
        ring_append(q->payload, q->len);
    pbuf_free(p);
    return ERR_OK;
}

static err_t connected_cb(void *arg, struct tcp_pcb *pcb, err_t err) {
    (void)arg; (void)pcb;
    if (err != ERR_OK) { s.state = SS_ERROR; return err; }
    s.state = SS_CONNECTED;
    return ERR_OK;
}

/* Public API */

bool net_init(void) {
    if (cyw43_arch_init()) return false;
    cyw43_arch_enable_sta_mode();
    return cyw43_arch_wifi_connect_timeout_ms(
               WIFI_SSID, WIFI_PASSWORD,
               CYW43_AUTH_WPA2_AES_PSK, 10000) == 0;
}

bool net_stream_connect(void) {
    s_ring_wr = 0;
    s_ring_rd = 0;
    s.state   = SS_CONNECTING;
    s.pcb     = NULL;

    ip_addr_t addr;
    if (!ipaddr_aton(SERVER_HOST, &addr)) return false;

    cyw43_arch_lwip_begin();
    struct tcp_pcb *pcb = tcp_new_ip_type(IPADDR_TYPE_V4);
    if (!pcb) { cyw43_arch_lwip_end(); return false; }

    tcp_arg (pcb, NULL);
    tcp_recv(pcb, recv_cb);
    tcp_err (pcb, err_cb);
    s.pcb = pcb;

    err_t err = tcp_connect(pcb, &addr, STREAM_PORT, connected_cb);
    cyw43_arch_lwip_end();

    if (err != ERR_OK) { s.pcb = NULL; tcp_abort(pcb); return false; }

    /* Wait for connection - yield to other tasks */
    uint32_t start = tick_count;
    while (s.state == SS_CONNECTING) {
        if (tick_count - start > NET_TIMEOUT_MS) { stream_close(); return false; }
        cyw43_arch_poll();
        task_yield();
    }
    return s.state == SS_CONNECTED;
}

/*
 * net_stream_poll - drive the network and check for a complete frame.
 *
 * Returns:
 *   > 0   complete frame written into buf (length returned)
 *     0   no complete frame yet
 *    -1   connection lost
 */
int net_stream_poll(char *buf, size_t buf_size) {
    g_poll_count++;
    cyw43_arch_poll();

    if (s.state == SS_ERROR) return -1;

    /* Search the ring buffer for the last complete "\nFRAME\n".
     * We want the LATEST frame so the display never lags behind. */
    static const char MARKER[] = "\nFRAME\n";
    const size_t      MLEN     = sizeof(MARKER) - 1;

    size_t avail     = ring_available();
    size_t frame_end = 0;     /* position just past the last marker found */
    bool   found     = false;

    if (avail < MLEN) return 0;

    /* Scan for rightmost marker */
    for (size_t i = s_ring_rd; i + MLEN <= s_ring_wr; i++) {
        bool match = true;
        for (size_t m = 0; m < MLEN && match; m++)
            if (ring_at(i + m) != MARKER[m]) match = false;
        if (match) { frame_end = i + MLEN; found = true; }
    }

    if (!found) {
        /* Drop data if buffer is getting full to avoid stall */
        if (avail > RING_SIZE * 3 / 4) s_ring_rd = s_ring_wr;
        return 0;
    }

    /* Find start of the frame that ends at frame_end:
     * search backwards for the previous marker (or start of ring) */
    size_t frame_start = s_ring_rd;
    if (frame_end > MLEN + s_ring_rd) {
        for (size_t i = frame_end - MLEN - 1; i > s_ring_rd; i--) {
            bool match = true;
            for (size_t m = 0; m < MLEN && match; m++)
                if (ring_at(i + m) != MARKER[m]) match = false;
            if (match) { frame_start = i + MLEN; break; }
        }
    }

    /* Copy frame body (excluding the trailing FRAME marker) into buf */
    size_t body_end = frame_end - MLEN;  /* stop before \nFRAME\n */
    size_t body_len = (body_end > frame_start) ? body_end - frame_start : 0;
    if (body_len >= buf_size) body_len = buf_size - 1;

    for (size_t i = 0; i < body_len; i++)
        buf[i] = ring_at(frame_start + i);
    buf[body_len] = '\0';

    /* Consume everything up to the end of this frame */
    s_ring_rd = frame_end;

    return (int)body_len;
}

bool net_stream_connected(void) {
    return s.state == SS_CONNECTED;
}

size_t net_ring_available(void) {
    return ring_available();
}
