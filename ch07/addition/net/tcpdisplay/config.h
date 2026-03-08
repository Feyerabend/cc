#pragma once

/*  wifi  */
#define WIFI_SSID        "YOUR_SSID" /* this requires that a network exists */
#define WIFI_PASSWORD    "YOUR_PASSWORD" /* and a password */

/* GFX server -- Mac/PC/Linux on YOUR_SSID */
#define SERVER_HOST      "0.0.0.0" /* its IP address */
#define SERVER_PORT      8080
#define STREAM_PORT      8081    /* persistent TCP stream                 */
#define SERVER_PATH      "/next"

/*  Timing */
#define NET_POLL_MS      200             /* poll server every 200 ms     */
#define NET_TIMEOUT_MS   5000            /* HTTP request timeout          */
