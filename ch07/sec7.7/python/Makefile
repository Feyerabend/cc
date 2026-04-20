# Python programs — run targets
# Usage: make install        install pip dependencies
#        make tcp-demo       run TCP server + client
#        make http           run HTTP server (Ctrl-C to stop)
#        make threads        run threading concurrency demo
#        make async          run asyncio concurrency demo
#        make microservices  start all three services + run client
#        make kill           kill any lingering service processes

PYTHON = python3

.PHONY: all install tcp-demo http threads async microservices kill help

all: help

install:
	$(PYTHON) -m pip install flask requests

# individual demos

tcp-demo:
	@echo "Starting TCP server in background..."
	@$(PYTHON) tcp_server.py &
	@sleep 0.5
	@echo "Running TCP client..."
	@$(PYTHON) tcp_client.py
	@wait

http:
	@echo "HTTP server on http://127.0.0.1:8000 — press Ctrl-C to stop"
	$(PYTHON) http_server.py

threads:
	$(PYTHON) concurrency_threads.py

async:
	$(PYTHON) concurrency_async.py

# ── distributed system demo ─────────────────────────────────────────────
# Starts all three services, waits, runs the client, then kills services.

microservices:
	@echo "Starting auth_service  on port 5001..."
	@$(PYTHON) auth_service.py &
	@echo "Starting data_service  on port 5002..."
	@$(PYTHON) data_service.py &
	@echo "Starting gateway       on port 5000..."
	@$(PYTHON) gateway.py &
	@echo "Waiting for services to start up..."
	@sleep 1.5
	@echo ""
	@echo "Running client:"
	@$(PYTHON) client.py
	@echo ""
	@echo "Done. Killing background services..."
	@$(MAKE) -s kill

kill:
	@pkill -f auth_service.py  2>/dev/null || true
	@pkill -f data_service.py  2>/dev/null || true
	@pkill -f gateway.py       2>/dev/null || true
	@pkill -f http_server.py   2>/dev/null || true
	@pkill -f tcp_server.py    2>/dev/null || true

help:
	@echo ""
	@echo "  make install       install flask + requests"
	@echo "  make tcp-demo      TCP client/server demo"
	@echo "  make http          HTTP server (Ctrl-C to stop)"
	@echo "  make threads       threading concurrency demo"
	@echo "  make async         asyncio concurrency demo"
	@echo "  make microservices full distributed-system demo"
	@echo "  make kill          stop any running background services"
	@echo ""
