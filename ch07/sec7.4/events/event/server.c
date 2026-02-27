#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/select.h>

#define PORT 8080
#define MAX_CLIENTS 10
#define BUFFER_SIZE 1024

void handle_client_message(int client_fd, char *buffer) {
    printf("Received from client %d: %s", client_fd, buffer);
    char response[] = "ACK\n";
    send(client_fd, response, strlen(response), 0);
}

int main() {
    int server_fd, client_fds[MAX_CLIENTS], max_fd;
    struct sockaddr_in server_addr, client_addr;
    fd_set read_fds;
    char buffer[BUFFER_SIZE];
    int client_count = 0;

    // server socket
    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        perror("Socket creation failed");
        exit(1);
    }

    // socket options
    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    // server address
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(PORT);

    // bind and listen
    if (bind(server_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("Bind failed");
        exit(1);
    }
    if (listen(server_fd, MAX_CLIENTS) < 0) {
        perror("Listen failed");
        exit(1);
    }

    printf("Server listening on port %d...\n", PORT);

    // init client_fds
    for (int i = 0; i < MAX_CLIENTS; i++) client_fds[i] = -1;

    // event loop
    while (1) {
        FD_ZERO(&read_fds);
        FD_SET(server_fd, &read_fds);
        max_fd = server_fd;

        // add active client sockets to set
        for (int i = 0; i < MAX_CLIENTS; i++) {
            if (client_fds[i] != -1) {
                FD_SET(client_fds[i], &read_fds);
                if (client_fds[i] > max_fd) max_fd = client_fds[i];
            }
        }

        // wait for activity
        if (select(max_fd + 1, &read_fds, NULL, NULL, NULL) < 0) {
            perror("Select failed");
            exit(1);
        }

        // check for new connection
        if (FD_ISSET(server_fd, &read_fds)) {
            socklen_t client_len = sizeof(client_addr);
            int new_fd = accept(server_fd, (struct sockaddr *)&client_addr, &client_len);
            if (new_fd < 0) {
                perror("Accept failed");
                continue;
            }
            // add new client to array
            for (int i = 0; i < MAX_CLIENTS; i++) {
                if (client_fds[i] == -1) {
                    client_fds[i] = new_fd;
                    client_count++;
                    printf("New client connected: %d\n", new_fd);
                    break;
                }
            }
        }

        // check for client messages
        for (int i = 0; i < MAX_CLIENTS; i++) {
            if (client_fds[i] != -1 && FD_ISSET(client_fds[i], &read_fds)) {
                int bytes_read = recv(client_fds[i], buffer, BUFFER_SIZE - 1, 0);
                if (bytes_read <= 0) {
                    // client disconnected
                    printf("Client %d disconnected\n", client_fds[i]);
                    close(client_fds[i]);
                    client_fds[i] = -1;
                    client_count--;
                } else {
                    buffer[bytes_read] = '\0';
                    handle_client_message(client_fds[i], buffer);
                }
            }
        }
    }

    close(server_fd);
    return 0;
}