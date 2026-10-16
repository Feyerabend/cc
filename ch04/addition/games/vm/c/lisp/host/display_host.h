#ifndef DISPLAY_HOST_H
#define DISPLAY_HOST_H

#include "../display.h"

// Extra functions for the PC version of the display
void host_set_button(button_t button, bool down);
uint32_t host_flush_count(void);
bool host_save_ppm(const char *path);
uint32_t host_screen_hash(void);
uint16_t host_get_pixel(int x, int y);

#endif // DISPLAY_HOST_H
