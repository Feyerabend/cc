#!/usr/bin/env python3
"""
udp_send.py — test sender for Pico 2W UDP receiver

Usage:
    python3 udp_send.py <pico-ip>          # send "hello #N" once per second
    python3 udp_send.py <pico-ip> "msg"    # send a single message and exit
    python3 udp_send.py <pico-ip> --flood  # send as fast as possible

The Pico listens on UDP port 1234.
Find the IP on the display after it connects to WiFi.
"""

import socket
import time
import sys

PICO_PORT = 1234


def send_one(sock, ip, msg):
    data = msg.encode("utf-8")[:63]
    sock.sendto(data, (ip, PICO_PORT))
    print(f"→ {msg}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    pico_ip = sys.argv[1]
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Single message mode
    if len(sys.argv) == 3 and sys.argv[2] != "--flood":
        send_one(sock, pico_ip, sys.argv[2])
        sock.close()
        return

    flood = len(sys.argv) == 3 and sys.argv[2] == "--flood"
    interval = 0.0 if flood else 1.0

    print(f"Sending to {pico_ip}:{PICO_PORT}  ({'flood' if flood else '1 msg/sec'})  Ctrl-C to stop")
    count = 0
    try:
        while True:
            count += 1
            ts = time.strftime("%H:%M:%S")
            msg = f"#{count:05d}  {ts}  hello from Mac"
            send_one(sock, pico_ip, msg)
            if interval:
                time.sleep(interval)
    except KeyboardInterrupt:
        print(f"\nSent {count} datagrams.")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
