#!/usr/bin/env python3
"""
PicoGFX server: HTTP + TCP stream server for the Pico 2W display.

Protocol  (text/plain, one command per line, UTF-8):
  CLEAR RRGGBB              clear the full screen
  RECT  x y w h RRGGBB      filled rectangle
  TEXT  x y RRGGBB msg      draw a string (msg is rest of line)
  FRAME                     end-of-frame marker (stream mode)
  NOP                       no-op / keep-alive

HTTP endpoint  (port 8080):
  GET /next       one frame of commands (polling fallback)
  GET /health     "ok"

Stream endpoint  (port 8081):
  Raw TCP:  server pushes frames continuously at TARGET_FPS.
  Each frame ends with "FRAME\n". Client reads until FRAME, renders, repeats.
"""

import math
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST        = "0.0.0.0" # you might have to change this also ...
HTTP_PORT   = 8080
STREAM_PORT = 8081
TARGET_FPS  = 30

DISPLAY_W = 320
DISPLAY_H = 240


# color helpers

def rgb(r: int, g: int, b: int) -> str:
    return f"{max(0,min(255,r)):02X}{max(0,min(255,g)):02X}{max(0,min(255,b)):02X}"

def hsv(h: float, s: float, v: float) -> str:
    h6 = h * 6.0
    i  = int(h6)
    f  = h6 - i
    p  = v * (1 - s)
    q  = v * (1 - s * f)
    t  = v * (1 - s * (1 - f))
    r, g, b = [(v,t,p),(q,v,p),(p,v,t),(p,q,v),(t,p,v),(v,p,q)][i % 6]
    return rgb(int(r*255), int(g*255), int(b*255))


# frame generator

def generate_frame() -> list[str]:
    t    = time.time()
    cmds = []

    cmds.append("CLEAR 001428")

    cmds.append("RECT 0 0 320 16 0A1A40")
    cmds.append("TEXT 4 4 AACCFF PICO 2W  GFX")
    cmds.append(f"TEXT 220 4 88DDFF {time.strftime('%H:%M:%S')}")

    bx    = int(160 + 110 * math.sin(t * 1.1))
    by    = int(128 +  80 * math.sin(t * 0.71))
    color = hsv((t * 0.13) % 1.0, 0.85, 1.0)
    cmds.append(f"RECT {bx-12} {by-12} 24 24 {color}")

    for x in range(0, DISPLAY_W, 4):
        y = int(128 + 30 * math.sin(x * 0.04 + t * 3.0))
        c = hsv(((x / DISPLAY_W) + t * 0.1) % 1.0, 1.0, 0.8)
        cmds.append(f"RECT {x} {y} 3 3 {c}")

    cmds.append(f"TEXT 4 226 33BB55 server ok   uptime {t:.0f}s")
    return cmds


# HTTP handler (polling fallback)

class GFXHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/next":
            body = ("\n".join(generate_frame()) + "\n").encode()
            self._respond(200, "text/plain", body)
        elif self.path == "/health":
            self._respond(200, "text/plain", b"ok\n")
        else:
            self._respond(404, "text/plain", b"not found\n")

    def _respond(self, code, ctype, body):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f"[{time.strftime('%H:%M:%S')}] HTTP {self.address_string()} {fmt % args}")


# TCP stream server

def handle_stream_client(conn: socket.socket, addr):
    """Push frames to one connected Pico client until it disconnects."""
    interval = 1.0 / TARGET_FPS
    print(f"[{time.strftime('%H:%M:%S')}] STREAM connect {addr[0]}:{addr[1]}")
    try:
        while True:
            t0   = time.monotonic()
            data = ("\n".join(generate_frame()) + "\nFRAME\n").encode()
            conn.sendall(data)
            elapsed = time.monotonic() - t0
            wait    = interval - elapsed
            if wait > 0:
                time.sleep(wait)
    except OSError:
        pass
    finally:
        conn.close()
        print(f"[{time.strftime('%H:%M:%S')}] STREAM disconnect {addr[0]}:{addr[1]}")


def run_stream_server():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, STREAM_PORT))
    srv.listen(4)
    print(f"PicoGFX stream  listening on port {STREAM_PORT}  ({TARGET_FPS} fps)")
    while True:
        conn, addr = srv.accept()
        threading.Thread(target=handle_stream_client, args=(conn, addr),
                         daemon=True).start()


# entry point

if __name__ == "__main__":
    threading.Thread(target=run_stream_server, daemon=True).start()

    http = HTTPServer((HOST, HTTP_PORT), GFXHandler)
    print(f"PicoGFX HTTP    listening on port {HTTP_PORT}")
    print()
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
