/* tcp_server.c   minimal TCP server using POSIX sockets
 *
 * Waits for one client, reads a message, replies, and exits.
 * Compile: gcc -o tcp_server tcp_server.c
 * Run:     ./tcp_server          (then run tcp_client in another terminal)
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#define HOST "127.0.0.1"
#define PORT  5000
#define BUFSZ 1024

int main(void) {
    int server_fd, client_fd;
    struct sockaddr_in addr, peer;
    socklen_t peer_len = sizeof(peer);
    char buf[BUFSZ];
    ssize_t n;

    /* 1. Create TCP socket */
    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) { perror("socket"); exit(1); }

    /* Allow reuse so we can restart quickly after Ctrl-C */
    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    /* 2. Bind to address */
    memset(&addr, 0, sizeof(addr));
    addr.sin_family      = AF_INET;
    addr.sin_addr.s_addr = inet_addr(HOST);
    addr.sin_port        = htons(PORT);

    if (bind(server_fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("bind"); exit(1);
    }

    /* 3. Listen: backlog of 1 pending connection */
    if (listen(server_fd, 1) < 0) { perror("listen"); exit(1); }
    printf("TCP server listening on %s:%d ...\n", HOST, PORT);

    /* 4. Accept one incoming connection */
    client_fd = accept(server_fd, (struct sockaddr *)&peer, &peer_len);
    if (client_fd < 0) { perror("accept"); exit(1); }
    printf("Connected by %s:%d\n", inet_ntoa(peer.sin_addr), ntohs(peer.sin_port));

    /* 5. Read data from client */
    n = recv(client_fd, buf, BUFSZ - 1, 0);
    if (n < 0) { perror("recv"); exit(1); }
    buf[n] = '\0';
    printf("Received: %s\n", buf);

    /* 6. Send reply */
    const char *reply = "Hello from C server";
    send(client_fd, reply, strlen(reply), 0);

    close(client_fd);
    close(server_fd);
    return 0;
}
