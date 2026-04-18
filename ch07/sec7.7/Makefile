# Top-level Makefile for sec7.7
# Delegates to sub-Makefiles in c/ and python/
#
# Usage:
#   make c-all          compile all C programs
#   make c-tcp-demo     run C TCP server+client demo
#   make c-http         run C HTTP server
#   make c-threads      run C concurrency demo
#   make c-concurrent   run C multi-client server
#   make c-clean        remove C binaries
#
#   make py-install     install Python deps (flask, requests)
#   make py-tcp-demo    run Python TCP demo
#   make py-http        run Python HTTP server
#   make py-threads     run Python threading demo
#   make py-async       run Python asyncio demo
#   make py-services    run the full distributed-system demo
#   make py-kill        kill background Python services
#
#   make all            compile C + install Python deps

.PHONY: all \
        c-all c-tcp-demo c-http c-threads c-concurrent c-clean \
        py-install py-tcp-demo py-http py-threads py-async py-services py-kill

all: c-all py-install

# ── C targets ───────────────────────────────────────────────────────────

c-all:
	$(MAKE) -C c all

c-tcp-demo:
	$(MAKE) -C c tcp-demo

c-http:
	$(MAKE) -C c http

c-threads:
	$(MAKE) -C c threads

c-concurrent:
	$(MAKE) -C c concurrent

c-clean:
	$(MAKE) -C c clean

# ── Python targets ───────────────────────────────────────────────────────

py-install:
	$(MAKE) -C python install

py-tcp-demo:
	$(MAKE) -C python tcp-demo

py-http:
	$(MAKE) -C python http

py-threads:
	$(MAKE) -C python threads

py-async:
	$(MAKE) -C python async

py-services:
	$(MAKE) -C python microservices

py-kill:
	$(MAKE) -C python kill
