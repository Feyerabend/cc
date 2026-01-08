import socket
import network
import time

class TCPEchoServer:
    def __init__(self, port=8080):
        self.port = port
        self.server_socket = None
        self.setup_socket()

    def setup_socket(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("0.0.0.0", self.port))
        self.server_socket.listen(1)
        print("TCP Echo Server listening on port", self.port)

    def handle_client(self, client_socket, client_addr):
        print("Client connected:", client_addr)

        try:
            client_socket.send(b"TCP Echo Server ready\n")

            while True:
                data = client_socket.recv(1024)
                if not data:
                    break

                msg = data.decode().strip()
                print("Received:", msg)

                if msg.upper() == "QUIT":
                    client_socket.send(b"Goodbye\n")
                    break

                client_socket.send(b"Echo: " + data)

        finally:
            client_socket.close()
            print("Client disconnected")

    def run(self):
        while True:
            client, addr = self.server_socket.accept()
            self.handle_client(client, addr)

def start_ap():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)

    ap.config(
        essid="PICO_ECHO",
        password="pico1234"   # WPA2 is implied by password length
    )

    while not ap.active():
        time.sleep(0.1)

    print("Access Point active")
    print("SSID: PICO_ECHO")
    print("IP:", ap.ifconfig()[0])

    return ap

# --- main ---

ap = start_ap()
server = TCPEchoServer(port=8080)
server.run()

