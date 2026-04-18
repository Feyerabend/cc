# C programs — compile and run targets
# Usage: make              build all
#        make tcp-demo     run server+client (two background processes)
#        make http         run HTTP server (Ctrl-C to stop)
#        make threads      run concurrency demo
#        make concurrent   run multi-client server
#        make clean        remove binaries

CC      = gcc
CFLAGS  = -Wall -Wextra -O2
TARGETS = tcp_server tcp_client http_server concurrent_server concurrency_threads

.PHONY: all tcp-demo http threads concurrent clean

all: $(TARGETS)

tcp_server: tcp_server.c
	$(CC) $(CFLAGS) -o $@ $<

tcp_client: tcp_client.c
	$(CC) $(CFLAGS) -o $@ $<

http_server: http_server.c
	$(CC) $(CFLAGS) -o $@ $<

concurrent_server: concurrent_server.c
	$(CC) $(CFLAGS) -o $@ $< -lpthread

concurrency_threads: concurrency_threads.c
	$(CC) $(CFLAGS) -o $@ $< -lpthread

# ── demos ──────────────────────────────────────────────────────────────

tcp-demo: tcp_server tcp_client
	@echo "Starting TCP server in background..."
	@./tcp_server &
	@sleep 0.3
	@echo "Running TCP client..."
	@./tcp_client
	@wait

http: http_server
	@echo "Starting HTTP server — press Ctrl-C to stop"
	./http_server

threads: concurrency_threads
	./concurrency_threads

concurrent: concurrent_server
	@echo "Starting concurrent server — press Ctrl-C to stop"
	./concurrent_server

clean:
	rm -f $(TARGETS)
