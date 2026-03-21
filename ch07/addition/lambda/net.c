/*
 * net.c — minimal HTTP/1.1 server over lwIP raw TCP API
 *
 * Design constraints:
 *   - No RTOS; runs entirely in the Core 0 polling loop
 *   - No keep-alive; each connection is closed after one response
 *   - No chunked encoding; Content-Length is always known before sending
 *   - No TLS
 *
 * Request handling:
 *   Each connection gets a heap-allocated conn_t that accumulates
 *   incoming bytes.  When the full HTTP request is detected (headers
 *   complete + Content-Length bytes of body present), the request is
 *   dispatched and the response is written in one shot via tcp_write().
 *   tcp_close() is called immediately after; lwIP flushes the send
 *   buffer and sends the FIN automatically.
 */

#include "net.h"
#include "dispatch.h"
#include "ui.h"
#include "lwip/tcp.h"
#include "pico/stdlib.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/* memmem is a GNU extension not available in newlib-nano */
static void *find_mem(const void *hay, size_t hlen,
                      const void *needle, size_t nlen)
{
    if (nlen == 0) return (void *)hay;
    if (hlen < nlen) return NULL;
    const char *h = (const char *)hay;
    const char *n = (const char *)needle;
    for (size_t i = 0; i <= hlen - nlen; i++)
        if (memcmp(h + i, n, nlen) == 0) return (void *)(h + i);
    return NULL;
}

/* ------------------------------------------------------------------ */
/*  Constants                                                         */
/* ------------------------------------------------------------------ */
#define HTTP_PORT       80

/* Maximum bytes we buffer per request (headers + body).
 * Requests larger than this get a 413 response. */
#define REQ_BUF_SIZE    4096

/* Static HTML served at GET / — the browser UI.
 * fetch() sends the body as text/plain so the server receives raw
 * Forth source without any URL-encoding to undo. */
static const char HTML_FORM[] =
    "<!DOCTYPE html><html><head><meta charset=utf-8>"
    "<title>pico-lambda</title></head><body>"
    "<h2>pico-lambda</h2>"
    "<textarea id=s rows=8 cols=60 placeholder=\"2 3 + .\"></textarea><br>"
    "<button onclick=run()>Eval</button>"
    "<pre id=o></pre>"
    "<script>"
    "async function run(){"
    "const r=await fetch('/eval',{method:'POST',"
    "body:document.getElementById('s').value});"
    "document.getElementById('o').textContent=await r.text();}"
    "</script></body></html>";

/* ------------------------------------------------------------------ */
/*  Connection state                                                  */
/* ------------------------------------------------------------------ */
typedef struct {
    char buf[REQ_BUF_SIZE];
    int  rxlen;
} conn_t;

/* ------------------------------------------------------------------ */
/*  Helpers                                                           */
/* ------------------------------------------------------------------ */

/* Case-insensitive search for header value, e.g. "Content-Length: " */
static const char *find_header(const char *headers, int hlen,
                                const char *name)
{
    int namelen = (int)strlen(name);
    for (int i = 0; i < hlen - namelen; i++) {
        if (strncasecmp(headers + i, name, namelen) == 0)
            return headers + i + namelen;
    }
    return NULL;
}

/* Detach callbacks, free state, close PCB. */
static void close_conn(struct tcp_pcb *pcb, conn_t *c)
{
    tcp_arg(pcb, NULL);
    tcp_recv(pcb, NULL);
    tcp_err(pcb, NULL);
    tcp_sent(pcb, NULL);
    free(c);
    tcp_close(pcb);
}

/* Write a fixed C string followed by optional body bytes.
 * Using TCP_WRITE_FLAG_MORE on the header tells lwIP to coalesce
 * both writes into as few segments as possible. */
static err_t write_response(struct tcp_pcb *pcb,
                             const char *hdr,
                             const char *body, int bodylen)
{
    err_t e;
    int hdrlen = (int)strlen(hdr);

    if (bodylen > 0) {
        e = tcp_write(pcb, hdr, hdrlen,
                      TCP_WRITE_FLAG_COPY | TCP_WRITE_FLAG_MORE);
        if (e != ERR_OK) return e;
        e = tcp_write(pcb, body, bodylen, TCP_WRITE_FLAG_COPY);
    } else {
        e = tcp_write(pcb, hdr, hdrlen, TCP_WRITE_FLAG_COPY);
    }
    if (e != ERR_OK) return e;
    return tcp_output(pcb);
}

/* ------------------------------------------------------------------ */
/*  Request processing                                                */
/* ------------------------------------------------------------------ */
static void handle_request(struct tcp_pcb *pcb, conn_t *c)
{
    char *buf = c->buf;
    int   len = c->rxlen;

    /* Parse request line */
    char *line_end = (char *)find_mem(buf, len, "\r\n", 2);
    if (!line_end) goto bad_request;

    /* Method */
    char *p = buf;
    char *sp = (char *)memchr(p, ' ', line_end - p);
    if (!sp) goto bad_request;
    char method[8];
    int  mlen = (int)(sp - p);
    if (mlen >= (int)sizeof(method)) goto bad_request;
    memcpy(method, p, mlen); method[mlen] = '\0';

    /* Path */
    p = sp + 1;
    sp = (char *)memchr(p, ' ', line_end - p);
    if (!sp) goto bad_request;
    char path[64];
    int  plen = (int)(sp - p);
    if (plen >= (int)sizeof(path)) goto bad_request;
    memcpy(path, p, plen); path[plen] = '\0';

    /* Find end of headers */
    char *hdr_end = (char *)find_mem(buf, len, "\r\n\r\n", 4);
    if (!hdr_end) goto bad_request;

    char *body       = hdr_end + 4;
    int   hdr_len    = (int)(hdr_end - buf);
    int   body_avail = len - (int)(body - buf);

    /* Content-Length (0 for GET) */
    int content_length = 0;
    const char *cl = find_header(buf, hdr_len, "Content-Length: ");
    if (cl) content_length = (int)strtol(cl, NULL, 10);

    if (body_avail < content_length) goto bad_request;   /* shouldn't happen */

    /* Route */
    if (strcmp(method, "GET") == 0 && strcmp(path, "/") == 0) {
        /* Browser UI */
        char hdr[128];
        snprintf(hdr, sizeof(hdr),
                 "HTTP/1.1 200 OK\r\n"
                 "Content-Type: text/html\r\n"
                 "Content-Length: %d\r\n"
                 "Connection: close\r\n"
                 "\r\n",
                 (int)(sizeof(HTML_FORM) - 1));
        write_response(pcb, hdr, HTML_FORM, (int)(sizeof(HTML_FORM) - 1));

    } else if (strcmp(method, "POST") == 0 && strcmp(path, "/eval") == 0) {
        /* Forth evaluation */
        if (content_length >= REQ_BUF_SIZE) {
            /* Body too large — would overflow buf if we tried to NUL-terminate */
            static const char R413[] =
                "HTTP/1.1 413 Content Too Large\r\n"
                "Content-Length: 0\r\n"
                "Connection: close\r\n"
                "\r\n";
            write_response(pcb, R413, NULL, 0);
            goto done;
        }
        body[content_length] = '\0';   /* safe: REQ_BUF_SIZE-1 guard above */

        static dispatch_result_t result;   /* static: too large for stack */
        dispatch_eval(body, &result);
        ui_on_request(body, &result);

        char hdr[128];
        snprintf(hdr, sizeof(hdr),
                 "HTTP/1.1 200 OK\r\n"
                 "Content-Type: text/plain\r\n"
                 "Content-Length: %d\r\n"
                 "Connection: close\r\n"
                 "\r\n",
                 result.len);
        write_response(pcb, hdr, result.buf, result.len);

    } else {
        static const char R405[] =
            "HTTP/1.1 405 Method Not Allowed\r\n"
            "Content-Length: 0\r\n"
            "Connection: close\r\n"
            "\r\n";
        write_response(pcb, R405, NULL, 0);
    }

done:
    close_conn(pcb, c);
    return;

bad_request:;
    static const char R400[] =
        "HTTP/1.1 400 Bad Request\r\n"
        "Content-Length: 0\r\n"
        "Connection: close\r\n"
        "\r\n";
    write_response(pcb, R400, NULL, 0);
    close_conn(pcb, c);
}

/* ------------------------------------------------------------------ */
/*  lwIP callbacks                                                    */
/* ------------------------------------------------------------------ */
static err_t recv_cb(void *arg, struct tcp_pcb *pcb, struct pbuf *p, err_t err)
{
    conn_t *c = (conn_t *)arg;

    if (!p) {
        /* Remote closed the connection */
        close_conn(pcb, c);
        return ERR_OK;
    }
    if (err != ERR_OK) {
        pbuf_free(p);
        return err;
    }

    /* Accumulate pbuf chain into our flat buffer */
    struct pbuf *q;
    for (q = p; q; q = q->next) {
        int space = REQ_BUF_SIZE - 1 - c->rxlen;
        if (space <= 0) break;
        int copy = q->len < space ? q->len : space;
        memcpy(c->buf + c->rxlen, q->payload, copy);
        c->rxlen += copy;
    }
    c->buf[c->rxlen] = '\0';

    tcp_recved(pcb, p->tot_len);
    pbuf_free(p);

    /* Is the request complete?
     * Condition: headers received (\r\n\r\n found) AND all body bytes present */
    char *hdr_end = (char *)find_mem(c->buf, c->rxlen, "\r\n\r\n", 4);
    if (!hdr_end) return ERR_OK;   /* headers still streaming in */

    int content_length = 0;
    int hdr_len = (int)(hdr_end - c->buf);
    const char *cl = find_header(c->buf, hdr_len, "Content-Length: ");
    if (cl) content_length = (int)strtol(cl, NULL, 10);

    int body_avail = c->rxlen - (hdr_len + 4);
    if (body_avail < content_length) return ERR_OK;   /* body still streaming in */

    /* Check for oversize request before dispatching */
    if (c->rxlen >= REQ_BUF_SIZE - 1) {
        static const char R413[] =
            "HTTP/1.1 413 Content Too Large\r\n"
            "Content-Length: 0\r\n"
            "Connection: close\r\n"
            "\r\n";
        write_response(pcb, R413, NULL, 0);
        close_conn(pcb, c);
        return ERR_OK;
    }

    handle_request(pcb, c);
    return ERR_OK;
}

static void err_cb(void *arg, err_t err)
{
    (void)err;
    /* conn_t is already freed by lwIP before calling err_cb */
    free(arg);
}

static err_t accept_cb(void *arg, struct tcp_pcb *newpcb, err_t err)
{
    (void)arg;
    if (err != ERR_OK || !newpcb) return ERR_VAL;

    conn_t *c = (conn_t *)calloc(1, sizeof(conn_t));
    if (!c) {
        tcp_abort(newpcb);
        return ERR_ABRT;
    }

    tcp_arg(newpcb, c);
    tcp_recv(newpcb, recv_cb);
    tcp_err(newpcb, err_cb);

    /* Reduce priority so the listening PCB stays at normal priority */
    tcp_setprio(newpcb, TCP_PRIO_MIN);

    return ERR_OK;
}

/* ------------------------------------------------------------------ */
/*  Public API                                                        */
/* ------------------------------------------------------------------ */
void net_init(void)
{
    struct tcp_pcb *pcb = tcp_new_ip_type(IPADDR_TYPE_ANY);
    if (!pcb) {
        printf("net_init: tcp_new failed\r\n");
        return;
    }

    err_t e = tcp_bind(pcb, IP_ANY_TYPE, HTTP_PORT);
    if (e != ERR_OK) {
        printf("net_init: tcp_bind failed: %d\r\n", (int)e);
        tcp_abort(pcb);
        return;
    }

    struct tcp_pcb *listen_pcb = tcp_listen(pcb);
    if (!listen_pcb) {
        printf("net_init: tcp_listen failed\r\n");
        tcp_abort(pcb);
        return;
    }

    tcp_accept(listen_pcb, accept_cb);
    printf("HTTP server listening on port %d\r\n", HTTP_PORT);
}
