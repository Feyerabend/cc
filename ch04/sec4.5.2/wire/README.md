
## Wired Connections

UART, or Universal Asynchronous Receiver/Transmitter, is one of the simplest ways
the Raspberry Pi Pico can communicate with other devices. It uses just two wires--one
for transmitting (TX) and one for receiving (RX)--to exchange data in a straightforward,
point-to-point manner. This makes it ideal for connecting to GPS receivers, Bluetooth
or Wi-Fi modules, or even another Pico. Because it is asynchronous, both ends must
agree on the same baud rate, but once set up, UART provides a reliable and widely
supported channel for serial communication.

*We will here only focus on a simple UART connection.*

But the Raspberry Pi Pico offers in general many ways to connect with the outside world, and
these wired connections allow it to control and sense a wide variety of devices.
At the most basic level, the Pico’s GPIO pins can be used for simple digital input
and output. A pin can be configured to read the state of a button or a switch,
or to drive an LED or a relay. Since the Pico operates at 3.3 volts, care is
needed when working with devices that expect 5 volts or more.

Beyond digital signals, the Pico also supports analogue inputs through its built-in
analogue-to-digital converters. These allow it to measure varying voltages, such as
those from a potentiometer or an analogue temperature sensor, with 12-bit resolution.
For output, many of the digital pins can generate pulse-width modulation signals.
This feature makes it possible to dim LEDs smoothly, control the speed of DC motors,
or send the precise timing signals needed to position servo motors.

For more complex communication, the Pico provides several serial interfaces. With I²C,
two wires are enough to connect to sensors, displays, or other microchips, often allowing
many devices to share the same bus as long as each one has a different address. When
speed is more important, the SPI interface can be used. It requires more wires, but is
common when working with devices like displays, SD cards, or high-speed converters.

Motors deserve special attention. The Pico itself cannot deliver the power required to
drive them directly, but with the help of motor driver boards—such as H-bridges for DC
motors, or dedicated stepper controllers—it can regulate speed, direction, and position.
Servo motors, by contrast, only need a carefully timed PWM signal, something the Pico
can generate natively.

All of these connections must be supported by proper power handling. The Pico runs at 3.3
volts logic and can be powered from USB or the VSYS pin, but many peripherals require
higher voltages. Motors often need 5, 9, or even 12 volts, and these supplies must be
provided separately. Level shifters or driver circuits are often used to bridge the gap
between the Pico’s logic and the demands of more powerful hardware.

Through this range of options—digital and analogue signals, PWM, serial buses, and careful
power management—the Pico can serve as the central hub in projects that combine sensors,
motors, and other electronic components into coherent and responsive systems.

| Connection Type | Typical Use | Notes | Example Components |
|-----------------|-------------|-------|--------------------|
| Digital I/O (GPIO) | Buttons, switches, LEDs, relays | 3.3V logic, avoid direct 5V input | DHT11/DHT22 (temp/humidity sensor), push buttons, 5mm LEDs, KY-040 rotary encoder |
| Analogue Input (ADC) | Potentiometers, analogue sensors | 12-bit resolution (0–4095 for 0–3.3V) | 10k potentiometer, LDR (light-dependent resistor), TMP36 temperature sensor |
| PWM (Pulse-Width Modulation) | Motor speed, LED dimming, servo control | Available on most GPIO pins | SG90 servo motor, WS2812B NeoPixel LEDs, DC motor with L298N driver |
| I²C | Displays, accelerometers, integrated sensors | Two wires (SDA, SCL); multiple devices on one bus | SSD1306 OLED (0.96" or 1.3"), MPU6050 (gyro/accelerometer), BME280 (temp/pressure/humidity) |
| SPI | Displays, SD cards, high-speed ADC/DAC | Faster than I²C; requires more pins (MISO, MOSI, SCK, CS) | ST7789 TFT (1.14" or 2.0"), microSD card module, MCP3008 (8-channel ADC) |
| UART | Debugging, GPS modules, microcontroller links | Simple point-to-point TX/RX communication | NEO-6M GPS module, HC-05 Bluetooth module, serial LCD modules |
| Motor Drivers | DC, stepper, and servo motors | Requires external driver (H-bridge, A4988, DRV8825, etc.) | L298N H-bridge (DC motors), A4988 (stepper motor), ULN2003 (28BYJ-48 stepper) |
| Power | Supplying Pico and peripherals | Pico runs at 3.3V logic; higher-voltage devices need separate supplies | 3.3V regulator (e.g., AMS1117), 5V USB power bank, 3.7V LiPo battery with boost converter |

### Notes:
- *GPIO*: Use resistors (e.g., 220Ω for LEDs) to protect Pico’s 3.3V pins. DHT11 is great for simple temp/humidity projects.
- *ADC*: Pico’s 4 ADC channels (GPIO 26-29) are perfect for analog sensors like LDRs for light-based games.
- *PWM*: NeoPixels are fun for lighting effects in projects like the tank game (e.g., explosion flashes).
- *I²C*: SSD1306 OLEDs are low-power and great for text or simple graphics; BME280 adds environmental data.
- *SPI*: ST7789 TFTs (like Pimoroni’s Display Pack) are ideal for colorful games, as used in the tank combat code.
- *UART*: GPS modules like NEO-6M suit outdoor Pico projects; Bluetooth adds wireless control.
- *Motor Drivers*: L298N is cheap for DC motors but needs external power; A4988 for precise stepper control.
- *Power*: Use a 3.3V regulator or battery setup for portable projects. Avoid 5V direct to GPIO.

