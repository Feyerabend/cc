/*
 * main.c — pico-lambda entry point
 */

#include "net.h"
#include "ui.h"
#include "config.h"

#include "pico/stdlib.h"
#include "pico/cyw43_arch.h"
#include "lwip/netif.h"
#include <stdio.h>

/* ------------------------------------------------------------------ */
static void wifi_connect(void)
{
    printf("Connecting to \"%s\" ...\r\n", WIFI_SSID);

    if (cyw43_arch_wifi_connect_timeout_ms(WIFI_SSID, WIFI_PASS,
                                           CYW43_AUTH_WPA2_AES_PSK,
                                           30000) != 0) {
        printf("WiFi connect failed\r\n");
        for (;;) {
            cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 1); sleep_ms(100);
            cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, 0); sleep_ms(100);
        }
    }

    printf("Connected.  IP: %s\r\n",
           ip4addr_ntoa(netif_ip4_addr(netif_default)));
}

/* ------------------------------------------------------------------ */
int main(void)
{
    stdio_init_all();
    sleep_ms(2000);
    printf("pico-lambda starting\r\n");

    if (cyw43_arch_init() != 0) {
        printf("cyw43_arch_init failed\r\n");
        for (;;) sleep_ms(1000);
    }
    printf("cyw43 ok\r\n");

    cyw43_arch_enable_sta_mode();
    wifi_connect();
    net_init();

    const char *ip = ip4addr_ntoa(netif_ip4_addr(netif_default));
    printf("Ready — http://%s/\r\n", ip);

    ui_init(ip);

    /* Event loop */
    bool     led        = false;
    uint32_t last_tick  = 0;

    for (;;) {
        cyw43_arch_poll();

        uint32_t now = to_ms_since_boot(get_absolute_time());
        if (now - last_tick >= 2000) {
            last_tick = now;
            led = !led;
            cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, led);
            printf("up  http://%s/eval\r\n", ip);
            ui_tick();
        }

        tight_loop_contents();
    }
}
