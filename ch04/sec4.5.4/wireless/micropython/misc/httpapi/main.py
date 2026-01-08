import socket
import network
import time
import json
from machine import Pin

# ------------------------------------------------------------
# Wi-Fi Access Point setup
# ------------------------------------------------------------

def start_ap():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)

    ap.config(
        essid="PICO_HTTP",
        password="pico1234"
    )

    while not ap.active():
        time.sleep(0.1)

    print("Access Point active")
    print("SSID: PICO_HTTP")
    print("IP:", ap.ifconfig()[0])

    return ap


class HTTPAPIServer:
    def __init__(self, port=80):
        self.port = port
        self.server_socket = None
        self.led = Pin(25, Pin.OUT)

        self.device_state = {
            "led": False,
            "uptime": 0,
            "requests_served": 0
        }

        self.setup_server()

    def setup_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("0.0.0.0", self.port))
        self.server_socket.listen(1)
        print("HTTP API Server listening on port", self.port)

    def parse_http_request(self, request):
        lines = request.split("\r\n")
        if not lines:
            return None, None, {}

        parts = lines[0].split(" ")
        if len(parts) < 3:
            return None, None, {}

        method, path = parts[0], parts[1]

        headers = {}
        for line in lines[1:]:
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip().lower()] = v.strip()

        return method, path, headers

    def json_response(self, data, status=200):
        body = json.dumps(data)

        status_text = {
            200: "OK",
            400: "Bad Request",
            404: "Not Found",
            405: "Method Not Allowed",
            500: "Internal Server Error"
        }.get(status, "OK")

        return (
            "HTTP/1.1 {} {}\r\n"
            "Content-Type: application/json\r\n"
            "Content-Length: {}\r\n"
            "Access-Control-Allow-Origin: *\r\n"
            "Connection: close\r\n"
            "\r\n"
            "{}"
        ).format(status, status_text, len(body), body)

    def handle_api(self, method, path):
        self.device_state["uptime"] = time.ticks_ms() // 1000
        self.device_state["requests_served"] += 1

        if path == "/api/status" and method == "GET":
            return self.json_response(self.device_state)

        if path == "/api/led" and method == "POST":
            self.device_state["led"] = not self.device_state["led"]
            self.led.value(self.device_state["led"])
            return self.json_response(self.device_state)

        if path == "/api/led/on" and method in ("GET", "POST"):
            self.device_state["led"] = True
            self.led.value(1)
            return self.json_response(self.device_state)

        if path == "/api/led/off" and method in ("GET", "POST"):
            self.device_state["led"] = False
            self.led.value(0)
            return self.json_response(self.device_state)

        return self.json_response({"error": "Not found"}, 404)

    def handle_client(self, client, addr):
        try:
            client.settimeout(5)
            request = client.recv(1024).decode()

            if not request:
                return

            method, path, headers = self.parse_http_request(request)
            print(method, path, "from", addr)

            if not method:
                response = self.json_response({"error": "Bad request"}, 400)
            else:
                response = self.handle_api(method, path)

            client.send(response.encode())

        except Exception as e:
            print("HTTP error:", e)

        finally:
            client.close()

    def run(self):
        print("HTTP API running")
        while True:
            client, addr = self.server_socket.accept()
            self.handle_client(client, addr)


ap = start_ap()
server = HTTPAPIServer(port=80)
server.run()

