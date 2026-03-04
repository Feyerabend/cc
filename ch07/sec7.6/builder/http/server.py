from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from urllib.parse import parse_qs, urlparse


class SimpleAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/users":
            role = query.get("role", ["guest"])[0]
            limit = int(query.get("limit", ["10"])[0])

            data = {
                "users": [
                    {"id": i, "name": f"user-{i}", "role": role}
                    for i in range(1, limit + 1)
                ],
                "total": limit,
                "filters": {"role": role}
            }

            self._send_json(200, data)
            return

        self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        if self.path == "/orders":
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length)
            try:
                body = json.loads(raw_body)
            except json.JSONDecodeError:
                self._send_json(400, {"error": "Invalid JSON"})
                return

            # Simulate order creation
            order_id = 1001  # fake
            response = {
                "status": "created",
                "order_id": order_id,
                "items": body.get("items", []),
                "total": body.get("total", 0.0)
            }

            self._send_json(201, response)
            return

        self._send_json(404, {"error": "Not found"})

    def _send_json(self, status: int, data: dict):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    # Optional: log requests
    def log_message(self, format, *args):
        pass  # silent, or print if you want


def run_server(host="127.0.0.1", port=8000):
    server = HTTPServer((host, port), SimpleAPIHandler)
    print(f"Server running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
