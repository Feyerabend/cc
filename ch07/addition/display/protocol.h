/*
 * protocol.h — Raw packet queue + VGTP protocol task
 *
 * net_task pushes raw UDP bytes here.
 * protocol_task pops, parses VGTP headers, assembles frames into build_scene,
 * and swaps buffers on FRAME_END.
 */

#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <stdint.h>

#define PKT_MAX_SIZE  256   /* max bytes per UDP datagram we handle */
#define PKT_QUEUE_LEN 64    /* ring buffer depth — 64×258 B = 16 KB used in the Pico, fits a full image burst */

/* Called from udp_recv_cb (net_task context) — copies data into queue */
void protocol_push_packet(const uint8_t *data, uint16_t len);

/* RTOS task — call task_create() with this before rtos_start() */
void protocol_task(void *param);

#endif /* PROTOCOL_H */
