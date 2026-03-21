#ifndef UI_H
#define UI_H

#include "dispatch.h"

/* Initialise the display and paint the static layout.
 * Call once from main() after the IP address is known. */
void ui_init(const char *ip);

/* Call from the event loop every ~100 ms to refresh uptime. */
void ui_tick(void);

/* Call from net.c after each dispatch_eval() to update the
 * "last expression / last result" panel. */
void ui_on_request(const char *src, const dispatch_result_t *result);

#endif /* UI_H */
