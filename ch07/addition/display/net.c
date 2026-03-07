/*
 * net.c — WiFi init + UDP DATA receive + UDP CONTROL send
 *
 * DATA socket (port 1234): receives VGTP packets, forwards to protocol_push_packet().
 * CONTROL socket (port 1235): sends ACK/FLOW/ERROR back to the sender.
 *
 * Sender IP is learned from the first DATA packet and reused for CONTROL replies.
 * In poll mode all lwIP calls happen on Core 0 with no concurrency — no locking needed.
 */

#include "net.h"
#include "vgtp.h"
#include <string.h>
#include "protocol.h"   /* PKT_QUEUE_LEN, PKT_MAX_SIZE */
#include "rtos.h"
#include "wifi_config.h"
#include "pico/cyw43_arch.h"
#include "lwip/udp.h"
#include "lwip/pbuf.h"
#include "lwip/netif.h"
#include "lwip/ip4_addr.h"

volatile bool     g_wifi_connected = false;
volatile uint32_t g_wifi_ip        = 0;
volatile uint32_t g_udp_rx_count   = 0;
volatile uint32_t g_last_rx_tick   = 0;

static uint8_t     recv_buf[512];
static struct udp_pcb *ctrl_pcb   = NULL;
static ip_addr_t   sender_ip;
static bool        sender_known   = false;

/* ------------------------------------------------------------------ */
/*  Ctrl TX queue — written by any Core 0 task, drained by net_task   */
/* ------------------------------------------------------------------ */
#define CTRL_TX_QUEUE_LEN 8
#define CTRL_TX_PKT_MAX   32

typedef struct { uint8_t data[CTRL_TX_PKT_MAX]; uint8_t len; } ctrl_tx_pkt_t;
static ctrl_tx_pkt_t    ctrl_tx_buf[CTRL_TX_QUEUE_LEN];
static volatile uint8_t ctrl_tx_head = 0;
static volatile uint8_t ctrl_tx_tail = 0;

void net_queue_control(const uint8_t *data, uint8_t len)
{
    uint8_t next = (ctrl_tx_head + 1) % CTRL_TX_QUEUE_LEN;
    if (next == ctrl_tx_tail) return;   /* full — drop */
    if (len > CTRL_TX_PKT_MAX) len = CTRL_TX_PKT_MAX;
    memcpy(ctrl_tx_buf[ctrl_tx_head].data, data, len);
    ctrl_tx_buf[ctrl_tx_head].len = len;
    ctrl_tx_head = next;
}

static void ctrl_tx_drain(void)
{
    while (ctrl_tx_tail != ctrl_tx_head) {
        ctrl_tx_pkt_t *p = &ctrl_tx_buf[ctrl_tx_tail];
        net_send_control(p->data, p->len);
        ctrl_tx_tail = (ctrl_tx_tail + 1) % CTRL_TX_QUEUE_LEN;
    }
}

/* ----------------------- */
/*  DATA receive callback  */
/* ----------------------- */

static void udp_recv_cb(void *arg, struct udp_pcb *pcb,
                        struct pbuf *p, const ip_addr_t *addr, u16_t port)
{
    (void)arg; (void)pcb; (void)port;
    if (!p) return;

    /* Learn sender IP for CONTROL replies */
    if (!sender_known) {
        ip_addr_copy(sender_ip, *addr);
        sender_known = true;
    }

    uint16_t len = p->tot_len < sizeof(recv_buf) ? p->tot_len : sizeof(recv_buf);
    pbuf_copy_partial(p, recv_buf, len, 0);
    pbuf_free(p);

    g_last_rx_tick = to_ms_since_boot(get_absolute_time());
    protocol_push_packet(recv_buf, len);
    g_udp_rx_count++;
}

/* -------------- */
/*  CONTROL send  */
/* -------------- */

void net_send_control(const uint8_t *data, uint16_t len)
{
    if (!ctrl_pcb || !sender_known) return;

    struct pbuf *p = pbuf_alloc(PBUF_TRANSPORT, len, PBUF_RAM);
    if (!p) return;

    pbuf_take(p, data, len);
    udp_sendto(ctrl_pcb, p, &sender_ip, VGTP_CTRL_PORT);
    pbuf_free(p);
}

/* ------------------------------------------------------ */
/*  CONTROL receive callback — handles HELLO → HELLO_ACK  */
/* ------------------------------------------------------ */

static void ctrl_recv_cb(void *arg, struct udp_pcb *pcb,
                         struct pbuf *p, const ip_addr_t *addr, u16_t port)
{
    (void)arg; (void)pcb; (void)port;
    if (!p) return;

    uint8_t buf[32];
    uint16_t len = p->tot_len < sizeof(buf) ? p->tot_len : sizeof(buf);
    pbuf_copy_partial(p, buf, len, 0);
    pbuf_free(p);

    if (len < sizeof(vgtp_ctrl_hdr_t)) return;
    const vgtp_ctrl_hdr_t *hdr = (const vgtp_ctrl_hdr_t *)buf;
    if (hdr->version != VGTP_VERSION) return;

    g_last_rx_tick = to_ms_since_boot(get_absolute_time());

    if (hdr->type == VGTP_CTRL_HEARTBEAT) {
        return;   /* tick already updated above */
    }

    if (hdr->type == VGTP_CTRL_HELLO) {
        /* Learn sender IP from HELLO (may arrive before any DATA packet) */
        ip_addr_copy(sender_ip, *addr);
        sender_known = true;

        /* Build HELLO_ACK: ctrl header + hello payload */
        struct __attribute__((packed)) {
            vgtp_ctrl_hdr_t      hdr;
            vgtp_hello_payload_t payload;
        } ack = {
            .hdr = {
                .version    = VGTP_VERSION,
                .type       = VGTP_CTRL_HELLO_ACK,
                .ack_seq    = 0,
                .ack_bitmap = 0,
                .adv_window = 1,
                .error_code = 0,
            },
            .payload = {
                .mtu             = PKT_MAX_SIZE - VGTP_HEADER_SIZE,
                .window          = PKT_QUEUE_LEN,
                .mode            = 0,   /* unreliable */
                .retx_timeout_ms = 0,
            },
        };
        net_send_control((const uint8_t *)&ack, sizeof(ack));
    }
}

/* -------------------- */
/*  WiFi + socket init  */
/* -------------------- */

void net_wifi_init(void)
{
    if (cyw43_arch_init() != 0) return;

    cyw43_arch_enable_sta_mode();
    cyw43_arch_wifi_connect_blocking(WIFI_SSID, WIFI_PASS, CYW43_AUTH_WPA2_AES_PSK);

    const ip4_addr_t *ip4 = netif_ip4_addr(&cyw43_state.netif[CYW43_ITF_STA]);
    g_wifi_ip = ip4_addr_get_u32(ip4);
    g_wifi_connected = (g_wifi_ip != 0);

    /* DATA socket */
    struct udp_pcb *data_pcb = udp_new_ip_type(IPADDR_TYPE_V4);
    if (data_pcb) {
        udp_bind(data_pcb, IP4_ADDR_ANY, VGTP_DATA_PORT);
        udp_recv(data_pcb, udp_recv_cb, NULL);
    }

    /* CONTROL socket — send ACKs + receive HELLO */
    ctrl_pcb = udp_new_ip_type(IPADDR_TYPE_V4);
    if (ctrl_pcb) {
        udp_bind(ctrl_pcb, IP4_ADDR_ANY, VGTP_CTRL_PORT);
        udp_recv(ctrl_pcb, ctrl_recv_cb, NULL);
    }
}

/* ---------- */
/*  net_task  */
/* ---------- */

void net_task(void *param)
{
    (void)param;
    while (1) {
        cyw43_arch_poll();
        ctrl_tx_drain();   /* send any queued CONTROL packets in the right context */
        task_delay(10);
    }
}
