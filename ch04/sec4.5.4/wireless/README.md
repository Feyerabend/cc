
## Raspberry Pi Pico W Networking

The Raspberry Pi Pico W is a powerful microcontroller with built-in Wi-Fi capabilities, thanks to its CYW43
module (based on the Cypress CYW4343 chip). This makes it an excellent platform for learning and experimenting
with networking in embedded systems. Whether you're building IoT devices, collecting sensor data over Wi-Fi,
or testing network performance, the Pico W offers a low-cost, flexible solution.


### Learning Networking with Pico W

To dive into networking with the Pico W, the official Raspberry Pi Pico examples repository is a good starting
point. It includes a variety of well-documented C code samples that demonstrate Wi-Fi connectivity, TCP/IP
communication, and more.
Visit [pico-examples/pico_w/wifi](https://github.com/raspberrypi/pico-examples/tree/master/pico_w/wifi)
for samples like:
- Connecting to a Wi-Fi network in *Station* (STA) or *Access Point* (AP) mode.
- Running an HTTP server or client.
- Performing network performance tests using iperf (e.g., measuring bandwidth with TCP).
- Using MQTT or other protocols for IoT applications.

These examples leverage the `pico-sdk` and its `cyw43_arch` library for Wi-Fi and `lwIP` (Lightweight IP) for
TCP/IP networking, licensed under the permissive BSD 3-Clause License. They are ideal for understanding low-level
networking concepts in C, though the code can be verbose due to the need to manage hardware, interrupts,
and network stacks explicitly.


### C vs. MicroPython for Networking

*C Programming*:
- *Pros*: Offers fine-grained control over the Pico W’s hardware and networking stack, making it suitable for
  performance-critical applications. The iperf example demonstrates this, using `lwiperf` to measure TCP throughput,
  with features like LED blinking and keypress handling.
- *Cons*: C code tends to be more complex and verbose, requiring manual memory management, interrupt handling,
  and configuration of the `lwIP` stack. For instance, the iperf test code includes detailed setup for Wi-Fi,
  async workers, and polling/interrupt modes, which can increase code size significantly.
- *Use Case*: Best for advanced users or projects needing maximum performance or custom low-level behavior.

*MicroPython*:
- *Pros*: Provides a higher-level, more concise way to write networking code, abstracting much of the hardware
  complexity. MicroPython scripts are typically shorter and easier to read, making them ideal for rapid prototyping
  and educational purposes. For example, a MicroPython script can connect to Wi-Fi and run a simple HTTP server
  in just a few lines.
- *Cons*: Less control over low-level details, potentially lower performance, and limited by MicroPython’s reduced
  feature set (e.g., missing some standard Python exceptions like `PermissionError`).
- *Use Case*: Perfect for beginners, quick experiments, or projects where code simplicity is prioritised over performance.

Explore MicroPython networking examples in the [micropython/](./micropython/) directory, which include scripts
for Wi-Fi connectivity, HTTP requests, and more, all designed to be compact and beginner-friendly.


### Getting Started with Pico W Networking

1. *Hardware Requirements*:
   - __Raspberry Pi Pico W__ (with CYW43 Wi-Fi module).
   - USB cable for programming and serial output.
   - Optional: SD card or sensors for advanced projects.

2. *Software Setup*:
   - *For C*:
     - Install the `pico-sdk` (see [Getting Started with Pico](https://www.raspberrypi.com/documentation/microcontrollers/c_sdk.html)).
     - Set up a build environment with CMake and a compiler (e.g., GCC for ARM).
     - Configure `WIFI_SSID` and `WIFI_PASSWORD` in your project (e.g., via CMake or a header file).
   - *For MicroPython*:
     - Flash the latest MicroPython firmware for Pico W from [micropython.org](https://micropython.org/download/rp2-pico-w/).
     - Use a tool like Thonny or rshell to upload and run scripts.
     - Ensure libraries like `network` and `urequests` are available.

3. *Example Projects*:
   - *C iperf Test*: The iperf example connects to a Wi-Fi network, runs a TCP performance test
     (client or server), and reports bandwidth. Build it by defining `CLIENT_TEST` and `IPERF_SERVER_IP`
     for client mode or leaving them undefined for server mode.
   - *MicroPython Wi-Fi*: A simple MicroPython script to connect to Wi-Fi and fetch a webpage:
     ```python
     import network
     import urequests

     wlan = network.WLAN(network.STA_IF)
     wlan.active(True)
     wlan.connect('your_ssid', 'your_password')
     while not wlan.isconnected():
         pass
     print('Connected:', wlan.ifconfig())
     response = urequests.get('http://example.com')
     print(response.text)
     ```

4. *Running the Code*:
   - For C: Build and flash using your IDE or command line, then monitor output via a serial
     terminal (e.g., minicom, 115200 baud).
   - For MicroPython: Upload scripts via Thonny or rshell and run them interactively or as `main.py`.


### Tips and Best Practices

- *Wi-Fi Configuration*: Ensure your `WIFI_SSID` and `WIFI_PASSWORD` match your network.
  For real security, avoid hardcoding credentials in production code—use a configuration file or environment variables.
- *Performance*: In C, use interrupt-driven mode (default) for better efficiency over polling
  mode (`PICO_CYW43_ARCH_POLL`). In MicroPython, keep scripts lean to avoid memory constraints.
- *Debugging*: Check serial output for errors (e.g., Wi-Fi connection failures). For C, ensure
  `lwIP` and `cyw43_arch` libraries are linked correctly. For MicroPython, verify module availability.
- *Extending Projects*: Add sensors, MQTT for IoT, or HTTP servers for web interfaces. The Pico W’s
  low cost makes it very suitable for experimentation.


### Resources

- *Official Pico W Examples*: [github.com/raspberrypi/pico-examples](https://github.com/raspberrypi/pico-examples/tree/master/pico_w/wifi)
- *Pico SDK Documentation*: [raspberrypi.com/documentation](https://www.raspberrypi.com/documentation/microcontrollers/c_sdk.html)
- *MicroPython for Pico W*: [micropython.org](https://micropython.org/download/rp2-pico-w/)
- *Community*: Check forums like [Raspberry Pi Forums](https://forums.raspberrypi.com) or Stack Overflow for troubleshooting, or LLMs!


### Notes

- *Code Size*: C programs, like the iperf example, can grow due to explicit hardware and network stack management.
  MicroPython scripts are more concise but may sacrifice some performance.
- *License*: The `pico-sdk` and related code (e.g., iperf example) are licensed under the BSD 3-Clause License,
  allowing free use and modification with proper attribution.
- *Limitations*: The Pico W’s CYW43 module supports 2.4 GHz Wi-Fi only. MicroPython’s memory constraints may
  limit complex networking tasks.

Start with the [micropython/](./micropython/) examples for quick prototyping, or dive into the
C samples at the official GitHub repository for deeper control.

