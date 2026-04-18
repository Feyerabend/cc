"""http_server.py — minimal HTTP server using Python's standard library

Shows how HTTP is a text protocol sitting on top of TCP/IP.
Run:  python http_server.py
Test: curl http://127.0.0.1:8000/
      curl http://127.0.0.1:8000/hello
      curl http://127.0.0.1:8000/status
"""

from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):

    # Silence the default request log so output is cleaner for learning
    def log_message(self, fmt, *args):
        print(f"  [HTTP] {self.address_string()} -> {fmt % args}")

    def do_GET(self):
        if self.path == "/":
            body = b"Welcome to the Python HTTP server!\n"
            code = 200
        elif self.path == "/hello":
            body = b"Hello, HTTP world!\n"
            code = 200
        elif self.path == "/status":
            body = b"status: running\n"
            code = 200
        else:
            body = b"Not found\n"
            code = 404

        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8000), Handler)
    print("HTTP server running on http://127.0.0.1:8000")
    print("Try:  curl http://127.0.0.1:8000/")
    print("      curl http://127.0.0.1:8000/hello")
    print("      curl http://127.0.0.1:8000/status")
    print("Press Ctrl-C to stop.\n")
    server.serve_forever()
