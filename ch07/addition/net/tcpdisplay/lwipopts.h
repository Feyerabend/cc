#pragma once

/* lwIP configuration for Pico 2W bare-metal RTOS project.
 * NO_SYS=1: raw API only (no netconn / socket), which fits our custom RTOS. */

#define NO_SYS                      1
#define LWIP_SOCKET                 0
#define LWIP_NETCONN                0

/* Memory */
#define MEM_LIBC_MALLOC             1   /* use newlib malloc (compatible with poll arch) */
#define MEM_ALIGNMENT               4
#define MEM_SIZE                    8000
#define MEMP_NUM_TCP_SEG            16
#define PBUF_POOL_SIZE              16

/* TCP */
#define LWIP_TCP                    1
#define TCP_WND                     (4 * TCP_MSS)
#define TCP_MSS                     1460
#define TCP_SND_BUF                 (4 * TCP_MSS)
#define TCP_SND_QUEUELEN            ((4 * (TCP_SND_BUF) + (TCP_MSS - 1)) / (TCP_MSS))
#define LWIP_TCP_KEEPALIVE          1

/* Protocols */
#define LWIP_ARP                    1
#define LWIP_ETHERNET               1
#define LWIP_ICMP                   1
#define LWIP_DHCP                   1
#define LWIP_IPV4                   1
#define LWIP_UDP                    1
#define LWIP_DNS                    0   /* not needed - we use dotted-decimal IPs */

/* Callbacks */
#define LWIP_NETIF_STATUS_CALLBACK  1
#define LWIP_NETIF_LINK_CALLBACK    1
#define LWIP_NETIF_HOSTNAME         1
#define LWIP_NETIF_TX_SINGLE_PBUF   1

/* Misc */
#define DHCP_DOES_ARP_CHECK         0
#define LWIP_DHCP_DOES_ACD_CHECK    0
#define LWIP_CHKSUM_ALGORITHM       3

/* Stats - off for release */
#define MEM_STATS                   0
#define SYS_STATS                   0
#define MEMP_STATS                  0
#define LINK_STATS                  0

/* Debug - all off */
#define LWIP_DEBUG                  0
