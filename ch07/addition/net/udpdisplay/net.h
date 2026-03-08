/*
 * net.h — WiFi init + UDP receive
 *
 * net_wifi_init() — call from main() before rtos_start() (blocking)
 * net_task()      — RTOS task; calls cyw43_arch_poll() every 10 ms
 *
 * Incoming UDP datagrams are forwarded to protocol_push_packet().
 */

#ifndef NET_H
#define NET_H

#include <stdint.h>
#include <stdbool.h>

#define UDP_PORT 1234

#define CONNECTION_TIMEOUT_MS  2000u   /* ms without any packet before "signal lost" */

/* WiFi state — net.c writes, anyone reads */
extern volatile bool g_wifi_connected;
extern volatile uint32_t g_wifi_ip;          /* IPv4 network byte order */
extern volatile uint32_t g_udp_rx_count;
extern volatile uint32_t g_last_rx_tick;     /* ms since boot, updated on any received packet */

void net_wifi_init(void);
void net_task(void *param);

/* Send immediately — only safe from within a cyw43_arch_poll() callback. */
void net_send_control(const uint8_t *data, uint16_t len);

/* Queue a CONTROL packet — safe to call from any Core 0 task.
 * net_task drains the queue after each cyw43_arch_poll(). */
void net_queue_control(const uint8_t *data, uint8_t len);

#endif /* NET_H */
