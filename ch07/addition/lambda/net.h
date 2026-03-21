#ifndef NET_H
#define NET_H

/*
 * net.h — minimal HTTP/1.1 server over lwIP raw TCP
 *
 * Two endpoints:
 *   GET  /      — static HTML form for browser testing
 *   POST /eval  — evaluate body as Forth, return plain-text result
 */

/* Initialise lwIP and start listening on port 80.
 * Call once from main() after cyw43_arch_init(). */
void net_init(void);

#endif /* NET_H */
