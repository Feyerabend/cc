
## Raspberry Pi Pico: Sending Temperatures Over Wire

The scripts (`receiver.py` and `main.py`) implement a UART-based communication system
for a Raspberry Pi Pico. The `receiver.py` script listens for incoming UART messages,
extracts content between `#` and `*` delimiters, and prints them. The `main.py` script
reads temperature data from an onboard sensor, converts it to Celsius and Fahrenheit,
and sends it over UART with a counter, blinking an LED to indicate transmission.

For more on its base see [hello](./../hello/).


__receiver.py__

Purpose: Continuously listens for UART messages on UART1 (baud rate 9600, TX: Pin 4, RX: Pin 5),
extracts the content between `#` and `*` delimiters, and prints received messages.

Key Functionality:
- Initialises UART1 with `machine.UART`.
- The `read_message` function checks for available data, decodes it as UTF-8, and
  returns the message content if it starts with `#` and ends with `*`.
- Runs in an infinite loop, printing valid messages every 0.1 seconds to avoid busy waiting.



__main.py__

Purpose: Reads temperature from the Pico’s onboard sensor, converts it to Celsius and
Fahrenheit, and sends a formatted message (e.g., `TEMP:25.5C,77.9F,COUNT:1`) over UART1
every 2 seconds, blinking the onboard LED (Pin 25) with each transmission.

Key Functionality:
- Initialises UART1 (baud rate 9600, TX: Pin 4, RX: Pin 5), ADC (Pin 4 for temperature sensor),
  and onboard LED (Pin 25).
- `read_temperature`: Converts ADC reading to voltage, then to Celsius using the sensor’s formula,
  rounded to one decimal place.
- `send_uart_message`: Sends a message with `#` and `*` delimiters, encoded as UTF-8.
- `blink_led`: Toggles the LED on for 0.1 seconds to signal transmission.
- Main loop: Sends temperature and counter data every 2 seconds, handles errors, and allows
  stopping via KeyboardInterrupt.



### Summary
- receiver.py: Simple UART receiver that listens for and prints delimited messages.
- main.py: Transmits temperature (Celsius/Fahrenheit) and a counter over UART, with
LED feedback, designed for monitoring or debugging via a logic analyzer or another device.

