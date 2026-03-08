#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* Debug counters updated by net.c, read by core1 display */
extern volatile uint32_t g_recv_cb_count;
extern volatile uint32_t g_poll_count;
extern volatile uint32_t g_total_bytes;

/* Connect to WiFi. Call once from main() before rtos_start(). */
bool net_init(void);

/* Open persistent TCP stream connection to the GFX server. */
bool net_stream_connect(void);

/* Drive the network stack and check for a complete frame.
 *   > 0  frame ready in buf
 *     0  no complete frame yet
 *    -1  connection lost — call net_stream_connect() to reconnect */
int  net_stream_poll(char *buf, size_t buf_size);

bool net_stream_connected(void);
size_t net_ring_available(void);
