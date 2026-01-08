import socket
import network
import time
import json
import gc


# Wi-Fi Access Point setup

def start_ap():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)

    ap.config(
        essid="PICO_UDP",
        password="pico1234"
    )

    while not ap.active():
        time.sleep(0.1)

    print("Access Point active")
    print("SSID: PICO_UDP")
    print("IP:", ap.ifconfig()[0])

    return ap

# UDP Broadcast Server

class UDPBroadcastServer:
    def __init__(self, listen_port=8081, broadcast_port=9999):
        self.listen_port = listen_port
        self.broadcast_port = broadcast_port
        self.sock = None
        self.setup_socket()

    def setup_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Allow broadcast
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        self.sock.bind(("0.0.0.0", self.listen_port))
        print("UDP server listening on port", self.listen_port)

    def send_status_broadcast(self):
        status = {
            "device": "Pico W",
            "uptime_s": time.ticks_ms() // 1000,
            "free_memory": gc.mem_free(),
            "timestamp_ms": time.ticks_ms()
        }

        msg = json.dumps(status)

        try:
            self.sock.sendto(
                msg.encode(),
                ("255.255.255.255", self.broadcast_port)
            )
            print("Broadcast sent:", msg)
        except Exception as e:
            print("Broadcast error:", e)

    def handle_incoming(self):
        try:
            self.sock.settimeout(0.2)
            data, addr = self.sock.recvfrom(1024)

            msg = data.decode()
            print("UDP from", addr, ":", msg)

            ack = "ACK"
            self.sock.sendto(ack.encode(), addr)

        except OSError:
            pass

    def run(self):
        last = time.ticks_ms()
        interval = 5000  # ms

        while True:
            self.handle_incoming()

            now = time.ticks_ms()
            if time.ticks_diff(now, last) >= interval:
                self.send_status_broadcast()
                last = now

ap = start_ap()
udp = UDPBroadcastServer()
udp.run()

