#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/select.h>

#define SERVER_IP "127.0.0.1"
#define PORT 8080
#define BUFFER_SIZE 1024

int main() {
    int client_fd;
    struct sockaddr_in server_addr;
    fd_set read_fds;
    char buffer[BUFFER_SIZE];
    int running = 1;

    client_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (client_fd < 0) {
        perror("Socket creation failed");
        exit(1);
    }

    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(PORT);
    if (inet_pton(AF_INET, SERVER_IP, &server_addr.sin_addr) <= 0) {
        perror("Invalid address");
        exit(1);
    }

    if (connect(client_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("Connection failed");
        close(client_fd);
        exit(1);
    }
    printf("Connected to server %s:%d\n", SERVER_IP, PORT);

    // event loop
    while (running) {
        FD_ZERO(&read_fds);
        FD_SET(STDIN_FILENO, &read_fds); // monitor stdin
        FD_SET(client_fd, &read_fds);   // monitor server socket
        int max_fd = client_fd > STDIN_FILENO ? client_fd : STDIN_FILENO;

        if (select(max_fd + 1, &read_fds, NULL, NULL, NULL) < 0) {
            perror("Select failed");
            break;
        }

        if (FD_ISSET(STDIN_FILENO, &read_fds)) {
            if (fgets(buffer, BUFFER_SIZE, stdin) == NULL) {
                running = 0; // EOF (e.g., Ctrl+D)
                continue;
            }
            int len = strlen(buffer);
            if (len > 0 && buffer[len - 1] == '\n') buffer[len - 1] = '\0'; // strip newline
            if (strcmp(buffer, "quit") == 0) {
                running = 0;
                continue;
            }
            // message to server
            strcat(buffer, "\n"); // newline for server
            if (send(client_fd, buffer, strlen(buffer), 0) < 0) {
                perror("Send failed");
                break;
            }
        }

        // handle server response
        if (FD_ISSET(client_fd, &read_fds)) {
            int bytes_read = recv(client_fd, buffer, BUFFER_SIZE - 1, 0);
            if (bytes_read <= 0) {
                printf("Server disconnected\n");
                running = 0;
            } else {
                buffer[bytes_read] = '\0';
                printf("Server: %s", buffer);
            }
        }
    }

    // cleanup
    close(client_fd);
    printf("Client disconnected\n");
    return 0;
}
