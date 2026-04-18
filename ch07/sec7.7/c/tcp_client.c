/* tcp_client.c   minimal TCP client using POSIX sockets
 *
 * Connects to tcp_server, sends a message, prints the reply.
 * Compile: gcc -o tcp_client tcp_client.c
 * Run:     ./tcp_client          (server must already be running)
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
    int fd;
    struct sockaddr_in addr;
    char buf[BUFSZ];
    ssize_t n;

    /* 1. Create TCP socket */
    fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) { perror("socket"); exit(1); }

    /* 2. Set server address */
    memset(&addr, 0, sizeof(addr));
    addr.sin_family      = AF_INET;
    addr.sin_addr.s_addr = inet_addr(HOST);
    addr.sin_port        = htons(PORT);

    /* 3. Connect: three-way handshake happens here */
    if (connect(fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("connect"); exit(1);
    }
    printf("Connected to %s:%d\n", HOST, PORT);

    /* 4. Send message */
    const char *msg = "Hello from C client";
    send(fd, msg, strlen(msg), 0);
    printf("Sent: %s\n", msg);

    /* 5. Receive reply */
    n = recv(fd, buf, BUFSZ - 1, 0);
    if (n < 0) { perror("recv"); exit(1); }
    buf[n] = '\0';
    printf("Received: %s\n", buf);

    close(fd);
    return 0;
}
