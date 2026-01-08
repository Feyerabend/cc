## TCP Echo Server (MicroPython)

This script implements a simple TCP echo server intended for MicroPython-based
boards with Wi-Fi support (for example Raspberry Pi Pico W).  
The device starts its own Wi-Fi Access Point and listens for incoming
TCP connections, echoing back any data it receives.

![]()


#### Features

- Runs a TCP echo server on port 8080
- Creates a Wi-Fi Access Point (`PICO_ECHO`)
- Accepts a single client connection at a time
- Useful for network testing, debugging, and teaching basic TCP/IP concepts

#### Requirements

- MicroPython
- Wi-Fi capable board (e.g. Pico W)
- Modules: `socket`, `network`, `time`

#### How it works

1. The board starts in Access Point mode.
2. The TCP server binds to `0.0.0.0:8080`.
3. A client connects to the AP and opens a TCP connection.
4. Any received data is sent back unchanged.

#### Usage

1. Flash MicroPython to the board.
2. Upload `main.py`.
3. Reset the board.
4. Connect to the Wi-Fi network `PICO_ECHO`.
5. Open a TCP connection to the printed IP address on port `8080`.

Example test from a client:

![]()

### Notes

- The server is blocking and handles one client at a time.
- Designed to be minimal and easy to extend (logging, protocols, concurrency).

