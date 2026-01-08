
## Pico W UDP Status Broadcast (MicroPython)

Simple UDP-based status broadcaster + receiver for Raspberry Pi Pico W
(and other MicroPython Wi-Fi boards). The device creates its own Wi-Fi
Access Point and periodically broadcasts JSON status messages while
listening for incoming UDP packets.


#### Features

- Creates Wi-Fi Access Point: `PICO_UDP` / password: `pico1234`
- Periodically broadcasts device status (every ~5 seconds)
- Listens for incoming UDP messages and sends simple ACK reply
- Reports: uptime, free memory, device type and current timestamp
- Lightweight--suitable for network discovery & monitoring experiments


#### Broadcast Message Format (JSON)

```json
{
  "device": "Pico W",
  "uptime_s": 12345,
  "free_memory": 184320,
  "timestamp_ms": 123456789
}
```

Broadcast destination: `255.255.255.255:9999`


#### Requirements

- MicroPython firmware (recent version recommended)
- Wi-Fi capable board (Raspberry Pi Pico W, ESP32, etc.)
- Modules: `socket`, `network`, `time`, `json`, `gc`


#### Quick Start

1. Flash MicroPython to your Pico W
2. Save the script as `main.py`
3. Reset the board
4. Connect any device to Wi-Fi:  
   *SSID:* `PICO_UDP`  
   *Password:* `pico1234`
5. The board will print its IP (usually `192.168.4.1`)


#### How to receive broadcasts (examples)

*Linux / macOS (netcat)*

```bash
nc -lu 9999
```

*Python simple listener*

```python
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("", 9999))

print("Listening for Pico UDP broadcasts...")

while True:
    data, addr = sock.recvfrom(1024)
    print(f"From {addr}: {data.decode()}")
```

*Send test message to Pico (gets ACK back)*

```bash
echo "hello from laptop" | nc -u 192.168.4.1 8081
```

You should see `ACK` returned and the message printed in the Pico REPL.


#### Typical Use Cases

- Device discovery in local networks
- Simple IoT heartbeat/status monitoring
- Network debugging / learning UDP
- Feeding status to home automation, node-red, Grafana, etc.


#### Notes

- Single-threaded blocking loop with short timeout
- Broadcast interval is currently fixed at 5 seconds
- Very minimal implementation--easy to extend (add more status fields, commands, etc.)


