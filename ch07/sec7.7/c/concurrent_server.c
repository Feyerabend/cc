/* concurrent_server.c  multi-client TCP server using pthreads
 *
 * Each accepted connection is handed off to its own thread,
 * so many clients can be served simultaneously.
 *
 * Compile: gcc -o concurrent_server concurrent_server.c -lpthread
 * Run:     ./concurrent_server
 * Test:    for i in 1 2 3 4 5; do (nc 127.0.0.1 5100 <<< "hello $i" &); done
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <pthread.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#define HOST  "127.0.0.1"
#define PORT   5100
#define BUFSZ  1024

typedef struct {
    int     fd;
    struct  sockaddr_in peer;
} client_t;

static void *handle_client(void *arg)
{
    client_t *c = (client_t *)arg;
    char buf[BUFSZ];
    ssize_t n;

    printf("[thread %lu] Client %s:%d connected\n",
           (unsigned long)pthread_self(),
           inet_ntoa(c->peer.sin_addr),
           ntohs(c->peer.sin_port));

    n = recv(c->fd, buf, BUFSZ - 1, 0);
    if (n > 0) {
        buf[n] = '\0';
        printf("[thread %lu] Received: %s\n",
               (unsigned long)pthread_self(), buf);

        /* Echo back with a prefix */
        char reply[BUFSZ + 32];
        int rlen = snprintf(reply, sizeof(reply), "Echo: %s", buf);
        send(c->fd, reply, rlen, 0);
    }

    close(c->fd);
    free(c);
    return NULL;
}

int main(void)
{
    int server_fd;
    struct sockaddr_in addr;

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
    if (listen(server_fd, 32) < 0) { perror("listen"); exit(1); }

    printf("Concurrent TCP server on %s:%d (thread-per-client)\n", HOST, PORT);

    while (1) {
        client_t *c = malloc(sizeof(client_t));
        if (!c) { perror("malloc"); continue; }

        socklen_t peer_len = sizeof(c->peer);
        c->fd = accept(server_fd, (struct sockaddr *)&c->peer, &peer_len);
        if (c->fd < 0) { perror("accept"); free(c); continue; }

        pthread_t tid;
        pthread_attr_t attr;
        pthread_attr_init(&attr);
        /* Detach: thread cleans itself up, we don't join */
        pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_DETACHED);
        pthread_create(&tid, &attr, handle_client, c);
        pthread_attr_destroy(&attr);
    }

    close(server_fd);
    return 0;
}
