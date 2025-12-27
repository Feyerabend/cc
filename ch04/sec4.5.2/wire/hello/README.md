
## Raspberry Pi Pico: Communicating Through UART

The code implements a simple UART (Universal Asynchronous Receiver/Transmitter) communication system
for sending and receiving messages between two devices, such as Raspberry Pi Pico microcontrollers.
The system consists of a sender and a receiver, with implementations in both C and Python (MicroPython).
The sender transmits a message encapsulated with start (`#`) and end (`*`) delimiters, while the receiver
reads incoming data, identifies complete messages based on these delimiters, and extracts the content
for display. The communication occurs over UART1 at a baud rate of 9600, using GPIO pins 4 (TX) and 5 (RX)
on the Raspberry Pi Pico.

The sender repeatedly sends the message "Hello, World!" every 2 seconds, and the receiver continuously
listens for incoming messages, printing them when received. Both implementations ensure reliable message
framing by using the `#` and `*` delimiters to mark the start and end of messages, respectively. The C
and Python versions achieve the same functionality but differ in their approach due to language-specific
features and the environments they target (bare-metal C for Pico SDK vs. MicroPython interpreter).



#### C Implementation

The C implementation consists of two programs: `sender.c` and `receiver.c`, along with a `CMakeLists.txt`
file for building the project using the Raspberry Pi Pico SDK. These programs are designed to run on a
Raspberry Pi Pico microcontroller using the Pico SDK, which provides low-level hardware access.


__Sender (`sender.c`)__

Purpose: Sends the message "Hello, World!" every 2 seconds over UART1,
encapsulated with `#` and `*` delimiters.

Components:
- Initialisation:
  - `stdio_init_all()`: Initializes standard I/O for `printf` output (via USB serial).
  - `uart_init(UART_ID, BAUD_RATE)`: Initializes UART1 with a baud rate of 9600.
  - `gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART)` and `gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART)`:
    Configures GPIO pins 4 (TX) and 5 (RX) for UART functionality.
- Message Sending:
  - The `send_message` function sends a message by:
    1. Transmitting the start character `#` using `uart_putc`.
    2. Sending the message string using `uart_puts`.
    3. Transmitting the end character `*` using `uart_putc`.
  - In the `main` loop, the program sends "Hello, World!" every 2 seconds (`sleep_ms(2000)`)
    and prints the sent message to the console via `printf`.
- Infinite Loop: The program runs indefinitely, sending the message repeatedly.

Technical Details:
- Uses the Pico SDK’s `hardware/uart.h` for UART operations and `pico/stdlib.h` for
  general utilities like `sleep_ms`.
- UART communication is asynchronous, and the sender does not check for receiver acknowledgment,
  assuming the receiver is listening.
- The `printf` output is typically routed to a USB serial connection for debugging.


__Receiver (`receiver.c`)__

Purpose: Continuously listens for incoming UART messages, extracts the content between
`#` and `*` delimiters, and prints the received message.

Components:
- Initialisation:
  - Similar to the sender, it initializes standard I/O and UART1 with the same baud
    rate (9600) and pin configuration (TX: 4, RX: 5).
- Message Reading:
  - The `read_message` function buffers incoming characters into a `temp_buffer` until
    a complete message (starting with `#` and ending with `*`) is received or the buffer overflows.
  - It checks for the start (`#`) and end (`*`) delimiters to identify a complete message.
  - If a valid message is received, it extracts the content (excluding delimiters), null-terminates it, and returns `true`.
  - If the buffer overflows (`buffer_index >= max_len`), it resets to prevent memory issues.
- Main Loop:
  - Continuously calls `read_message` to check for new messages.
  - If a message is received, it prints it using `printf`.
  - A 100ms delay (`sleep_ms(100)`) prevents busy waiting and reduces CPU load.

Technical Details:
- Uses a static buffer (`temp_buffer`) to accumulate characters, ensuring persistence across function calls.
- Handles edge cases like buffer overflow and empty messages (when only `#` and `*` are received).
- Relies on `uart_is_readable` to check for available data, making it non-blocking.


__Build Configuration (`CMakeLists.txt`)__

Purpose: Configures the build process for the C programs using the Pico SDK.

Key Components:
- Sets the minimum CMake version and includes the Pico SDK.
- Defines the project (`uart_example`) with C, C++, and assembly support.
- Initializes the Pico SDK and adds the executable (named `uart_example`).
- References `uart_send.c` (should be updated to `sender.c` or `receiver.c`
  depending on the program being built).
- Enables USB standard I/O and disables UART standard I/O.
- Links the executable with `pico_stdlib` and `hardware_uart` libraries for
  UART and standard library functions.

Note: The `CMakeLists.txt` file contains a comment suggesting replacing `uart_send.c`
with `uart_receive.c`, indicating it’s a template for either program. In practice,
separate build configurations or a unified project with both files might be needed.


#### Python (MicroPython) Implementation

The Python implementation consists of two scripts: `sender.py` and `receiver.py`, designed
to run on a Raspberry Pi Pico running MicroPython. These scripts leverage MicroPython’s
`machine` module for hardware access and provide a higher-level abstraction compared to
the C implementation.


__Sender (`sender.py`)__

Purpose: Sends the message "Hello, World!" every 2 seconds over UART1, encapsulated
with `#` and `*` delimiters.

Components:
- Initialisation:
  - Initializes UART1 with `UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))`, configuring
    pins 4 (TX) and 5 (RX).
- Message Sending:
  - The `send_message` function constructs a full message by concatenating the start
    character `#`, the message, and the end character `*`.
  - Uses `uart.write` to send the entire string at once.
  - In the main loop, sends "Hello, World!" every 2 seconds (`time.sleep(2)`) and
    prints the sent message to the console.
- Infinite Loop: Runs indefinitely, similar to the C sender.

Technical Details:
- MicroPython’s `machine.UART` handles UART communication, abstracting low-level
  details like GPIO configuration.
- The message is encoded as a UTF-8 string implicitly by `uart.write`.
- The script is simpler than the C version due to MicroPython’s high-level API.

##### Receiver (`receiver.py`)

Purpose: Continuously listens for incoming UART messages, extracts the content
between `#` and `*` delimiters, and prints the received message.

Components:
- Initialisation:
  - Initialises UART1 with the same configuration as the sender (baud rate 9600, TX: 4, RX: 5).
- Message Reading:
  - The `read_message` function checks for available data using `uart.any()`.
  - Reads all available data with `uart.read()` and decodes it as UTF-8.
  - Checks if the message starts with `#` and ends with `*`, returning the content (excluding
    delimiters) if valid, or `None` otherwise.
- Main Loop:
  - Continuously calls `read_message`.
  - Prints received messages when available.
  - A 0.1-second delay (`time.sleep(0.1)`) prevents busy waiting.

Technical Details:
- Unlike the C receiver, it reads all available data at once, relying on MicroPython’s buffering.
- Assumes the entire message is received in one `uart.read()` call, which may not handle
  partial messages as robustly as the C version.
- Simpler implementation due to MicroPython’s high-level abstractions.




### Comparison of C and Python Implementations

| Aspect | C Implementation (Pico SDK) | Python Implementation (MicroPython) |
|---|---|---|
| Environment | Bare-metal, compiled with Pico SDK | Interpreted, runs on MicroPython firmware |
| Code Complexity | More complex due to low-level hardware control | Simpler due to high-level `machine` module APIs |
| Message Handling  | Sender: Sends character-by-character<br>Receiver: Buffers characters, handles partial messages | Sender: Sends entire message at once<br>Receiver: Reads all available data, assumes complete messages |
| Buffer Management | Explicit static buffer with overflow handling | Relies on MicroPython’s internal buffering |
| Error Handling | Handles buffer overflow, empty messages | Minimal error handling, assumes valid input |
| Performance | Faster, lower memory footprint due to compiled code | Slower, higher memory usage due to interpreter |
| Portability | Tied to Pico SDK and RP2040 hardware | Portable to any MicroPython-supported platform |
| Development Ease | Requires CMake setup, compilation, and flashing | Easier to edit and deploy (copy to device) |



### Summary

Both implementations achieve the same goal: sending and receiving "Hello, World!" messages
over UART with `#` and `*` delimiters. The C implementation offers fine-grained control and
efficiency, suitable for resource-constrained environments, but requires more setup and error
handling. The Python implementation is simpler and more accessible, leveraging MicroPython’s
abstractions, but may be less robust for partial messages or high-performance scenarios.
The choice between them depends on the project’s requirements: C for performance and control,
Python for rapid development and ease of use.


