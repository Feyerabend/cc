/* http_server.c  minimal HTTP/1.1 server over raw sockets
 *
 * Handles one GET request at a time and returns a plain-text response.
 * Shows that HTTP is just text riding on top of TCP.
 *
 * Compile: gcc -o http_server http_server.c
 * Run:     ./http_server
 * Test:    curl http://127.0.0.1:8080/
 *          curl http://127.0.0.1:8080/hello
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#define HOST  "127.0.0.1"
#define PORT   8080
#define BUFSZ  4096

/* Build and send an HTTP response */
static void send_response(int fd, int status, const char *status_text, const char *body) {
    char header[512];
    int hlen = snprintf(header, sizeof(header),
        "HTTP/1.1 %d %s\r\n"
        "Content-Type: text/plain\r\n"
        "Content-Length: %zu\r\n"
        "Connection: close\r\n"
        "\r\n",
        status, status_text, strlen(body));

    send(fd, header, hlen, 0);
    send(fd, body, strlen(body), 0);
}

/* Parse "GET /path HTTP/1.1": writes path into buf (max len bytes) */
static int parse_request_line(const char *request, char *path, size_t len) {
    /* We only support GET */
    if (strncmp(request, "GET ", 4) != 0) return -1;

    const char *start = request + 4;
    const char *end   = strchr(start, ' ');
    if (!end) return -1;

    size_t plen = (size_t)(end - start);
    if (plen >= len) plen = len - 1;
    memcpy(path, start, plen);
    path[plen] = '\0';
    return 0;
}

static void handle_client(int fd) {
    char buf[BUFSZ];
    ssize_t n = recv(fd, buf, BUFSZ - 1, 0);
    if (n <= 0) { close(fd); return; }
    buf[n] = '\0';

    /* Print the raw HTTP request so students can see it */
    printf("--- Raw HTTP request ---\n%s\n------------------------\n", buf);

    char path[256];
    if (parse_request_line(buf, path, sizeof(path)) < 0) {
        send_response(fd, 405, "Method Not Allowed", "Only GET is supported.");
        close(fd);
        return;
    }

    if (strcmp(path, "/") == 0) {
        send_response(fd, 200, "OK", "Welcome to the C HTTP server!\n");
    } else if (strcmp(path, "/hello") == 0) {
        send_response(fd, 200, "OK", "Hello, HTTP world!\n");
    } else if (strcmp(path, "/status") == 0) {
        send_response(fd, 200, "OK", "status: running\n");
    } else {
        send_response(fd, 404, "Not Found", "Path not found.\n");
    }

    close(fd);
}

int main(void) {
    int server_fd;
    struct sockaddr_in addr, peer;
    socklen_t peer_len = sizeof(peer);

    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) { perror("socket"); exit(1); }

    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    memset(&addr, 0, sizeof(addr));
    addr.sin_family      = AF_INET;
    addr.sin_addr.s_addr = inet_addr(HOST);
    addr.sin_port        = htons(PORT);

    if (bind(server_fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("bind"); exit(1);
    }
    if (listen(server_fd, 16) < 0) { perror("listen"); exit(1); }

    printf("HTTP server running on http://%s:%d\n", HOST, PORT);
    printf("Try: curl http://%s:%d/\n", HOST, PORT);
    printf("     curl http://%s:%d/hello\n", HOST, PORT);
    printf("     curl http://%s:%d/status\n\n", HOST, PORT);

    /* Serve forever, one request at a time */
    while (1) {
        int client_fd = accept(server_fd, (struct sockaddr *)&peer, &peer_len);
        if (client_fd < 0) { perror("accept"); continue; }
        printf("Request from %s:%d\n", inet_ntoa(peer.sin_addr), ntohs(peer.sin_port));
        handle_client(client_fd);
    }

    close(server_fd);
    return 0;
}
