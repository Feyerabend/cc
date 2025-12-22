
## What Are Device Drivers?

Device drivers are specialised software components that act as intermediaries between
an operating system (or in embedded systems, the firmware/microcontroller code) and
hardware peripherals. They translate high-level commands from applications or the OS
into low-level instructions that the hardware can understand, such as reading/writing
to registers, handling interrupts, or managing data transfers. In essence, drivers
abstract the complexities of hardware, making it easier for software to interact with
devices like displays, sensors, keyboards, or network cards without needing to know
the intricate details of each piece of hardware.


#### A Short History of Drivers

The concept of drivers emerged in the early days of computing. In the 1950s and 1960s,
with mainframes like the IBM 7090, hardware interaction was often hardcoded into programs,
leading to inefficiency and portability issues. As operating systems evolved—think UNIX
in the 1970s—drivers became modular components within the kernel to standardise hardware
access. Microsoft's MS-DOS in the 1980s popularised user-installable drivers for peripherals
like printers. The 1990s saw plug-and-play standards in Windows, automating driver
installation. In the 2000s, with Linux's open-source model, drivers became community-driven,
covering vast hardware ecosystems. Today, in embedded systems (e.g., IoT devices like
Raspberry Pi), drivers are often lightweight and integrated into firmware, with frameworks
like Linux's device tree or MicroPython's modules simplifying development. The shift has
been from monolithic, hardware-specific code to modular, reusable abstractions, driven by
the explosion of diverse hardware.


#### What Are Drivers Used For?

Drivers serve several core purposes:
- *Hardware Abstraction*: They hide device-specific quirks, allowing the same software to
  work across different hardware (e.g., a graphics driver letting apps draw on various GPUs).
- *Resource Management*: Handling interrupts, DMA (Direct Memory Access), power states, and
  concurrency to prevent conflicts.
- *Performance Optimisation*: Fine-tuning data paths for speed, like buffering in network
  drivers.
- *Security and Isolation*: In OS kernels, drivers enforce access controls to prevent
  user-space apps from directly manipulating hardware.
- *Extensibility*: Enabling new hardware support without rewriting the entire system.

In modern contexts, drivers are crucial for everything from desktop OSes (e.g., Windows
drivers for USB devices) to embedded systems (e.g., controlling motors in robotics).
Without them, software would be brittle and hardware-locked.


### Writing Drivers for the Raspberry Pi Pico (e.g., for Pimoroni Display Pack)

The Raspberry Pi Pico is a microcontroller based on the RP2040 chip, popular for embedded
projects due to its low cost, dual-core ARM Cortex-M0+ processor, and flexible PIO
(Programmable I/O) for custom interfaces. It's often programmed in C/C++ via the Pico
SDK or in MicroPython/CircuitPython for quicker prototyping.

The Pimoroni Pico Display Pack is a good example: it's a small add-on board with an
ST7789-based LCD display (240x135 pixels), buttons, and RGB LED, connected via SPI
(Serial Peripheral Interface). High-level APIs, like those in MicroPython's `pimoroni`
library, provide easy functions like `display.text("Hello", x, y)` to draw on the screen.


#### Why Write Low-Level Drivers Instead of Using High-Level APIs?

- *Deep Understanding and Learning*: High-level APIs abstract away the hardware, but
  writing from scratch teaches you protocols like SPI/I2C, timing requirements, and
  register maps. This is invaluable for debugging or hardware hacking.
- *Customisation and Optimisation*: APIs might include overhead (e.g., unnecessary
  buffering or error checks). Low-level code lets you optimise for speed (critical
  in real-time apps like games) or power (e.g., minimising SPI transactions in
  battery-powered devices).
- *When No API Exists*: For obscure or custom chips, or if you're porting to a new
  platform, you build from the datasheet.
- *Portability and Control*: Avoid dependency on third-party libraries that might change
  or have bugs. Direct access ensures your code works exactly as the hardware intends.
- *Edge Cases*: Handle unique scenarios, like overclocking the Pico's PIO for faster SPI,
  or integrating with other peripherals without library conflicts.

However, it's not always ideal—high-level APIs save time for rapid prototyping,
reduce errors, and handle common pitfalls like initialisation sequences.


#### When to Do It?

- *Prototyping Phase*: Stick to high-level APIs for quick iteration.
- *Production or Optimisation*: Switch to low-level when performance bottlenecks
  appear (e.g., slow screen refreshes in a UI-heavy project) or when integrating
  multiple devices requiring tight coordination.
- *Educational Projects*: Always, if your goal is learning embedded systems.
- *Custom Hardware*: If you're designing your own board with the ST7789 or similar
  chips (e.g., ILI9341 for other displays).
- *Constraints*: In memory-tight environments (Pico has 264KB SRAM), low-level
  code can be leaner than bloated libraries.

Avoid it if deadlines are tight or you're new to embedded programming—start with
APIs and peel back layers gradually.


#### How to Write Low-Level Drivers for the Pico and Chips Like ST7789?

Here's a step-by-step guide, focusing on C/C++ with the Pico SDK (free from
Raspberry Pi's GitHub). Assume you've set up the SDK and CMake for building.

1. *Gather Documentation*:
   - RP2040 Datasheet: For Pico's SPI hardware (it has two SPI controllers).
   - ST7789 Datasheet: Details commands (e.g., 0x36 for memory access control),
     register addresses, and timing (e.g., SPI clock up to 62.5 MHz).
   - Pimoroni Schematics: Confirm pinouts (e.g., SPI0 on GPIO 16-19, CS on GPIO 17, DC on GPIO 20).

2. *Set Up the Environment*:
   - Initialise the Pico's SPI peripheral using SDK functions like `spi_init(spi0, baudrate)`.
   - Configure GPIO pins for SPI mode.

3. *Implement Basic Communication*:
   - SPI is master-slave: Pico as master sends clock, MOSI (data out), selects slave with CS (Chip Select).
   - For ST7789, commands are 8-bit (DC low), data 8/16-bit (DC high).

   Example code skeleton (in C):

   ```c
   #include <stdio.h>
   #include "pico/stdlib.h"
   #include "hardware/spi.h"

   // Pin definitions (adjust for your setup)
   #define SPI_PORT spi0
   #define PIN_MISO 16
   #define PIN_CS   17
   #define PIN_SCK  18
   #define PIN_MOSI 19
   #define PIN_DC   20
   #define PIN_RST  21  // Optional reset pin

   // Function to send command (DC low)
   void st7789_command(uint8_t cmd) {
       gpio_put(PIN_DC, 0);  // Command mode
       gpio_put(PIN_CS, 0);  // Select chip
       spi_write_blocking(SPI_PORT, &cmd, 1);
       gpio_put(PIN_CS, 1);  // Deselect
   }

   // Function to send data (DC high)
   void st7789_data(const uint8_t *data, size_t len) {
       gpio_put(PIN_DC, 1);  // Data mode
       gpio_put(PIN_CS, 0);
       spi_write_blocking(SPI_PORT, data, len);
       gpio_put(PIN_CS, 1);
   }

   // Initialization sequence from datasheet
   void st7789_init() {
       // Reset the display (if using RST pin)
       gpio_put(PIN_RST, 0);
       sleep_ms(10);
       gpio_put(PIN_RST, 1);
       sleep_ms(120);

       st7789_command(0x01);  // Software reset
       sleep_ms(150);

       st7789_command(0x11);  // Sleep out
       sleep_ms(120);

       // Set color mode (e.g., 16-bit RGB565)
       st7789_command(0x3A);
       uint8_t colmod = 0x05;  // 16-bit/pixel
       st7789_data(&colmod, 1);

       // Invert colors if needed (0x21)
       st7789_command(0x21);

       // Display on
       st7789_command(0x29);
   }

   int main() {
       stdio_init_all();
       // Init GPIO pins
       gpio_init(PIN_CS); gpio_set_dir(PIN_CS, GPIO_OUT); gpio_put(PIN_CS, 1);
       gpio_init(PIN_DC); gpio_set_dir(PIN_DC, GPIO_OUT);
       gpio_init(PIN_RST); gpio_set_dir(PIN_RST, GPIO_OUT);

       // Init SPI
       spi_init(SPI_PORT, 10000000);  // 10 MHz baudrate
       gpio_set_function(PIN_MISO, GPIO_FUNC_SPI);
       gpio_set_function(PIN_SCK, GPIO_FUNC_SPI);
       gpio_set_function(PIN_MOSI, GPIO_FUNC_SPI);

       st7789_init();

       // Example: Fill screen with red (RGB565: 0xF800)
       st7789_command(0x2A);  // Column address set (0-239)
       uint8_t col[] = {0x00, 0x00, 0x00, 0xEF};
       st7789_data(col, 4);

       st7789_command(0x2B);  // Row address set (0-134 for 135px)
       uint8_t row[] = {0x00, 0x00, 0x00, 0x86};
       st7789_data(row, 4);

       st7789_command(0x2C);  // Memory write
       for (int i = 0; i < 240 * 135; i++) {
           uint8_t pixel[] = {0xF8, 0x00};  // Red in RGB565
           st7789_data(pixel, 2);
       }

       while (true) {
           tight_loop_contents();
       }
   }
   ```

   This is a basic driver: it initialises the ST7789 and fills the screen. Expand
   it for drawing pixels, text (via font rendering), or handling buttons (via GPIO
   interrupts).

4. *Handle Advanced Features*:
   - *Interrupts and DMA*: For efficient data transfer, use Pico's DMA to
     offload SPI writes.
   - *PIO for Custom SPI*: If standard SPI isn't fast enough, program PIO
     state machines for bit-banged or accelerated interfaces.
   - *Error Handling*: Check for SPI errors, timeouts.
   - *Testing*: Use an oscilloscope or logic analyser to verify signals
     match the datasheet.

5. *Tools and Resources*:
   - Pico SDK Examples: Start with `spi` demos.
   - Datasheets: Search for "ST7789 datasheet PDF".
   - Communities: Raspberry Pi forums, Reddit's r/raspberry_pi, or GitHub
     repos for open-source drivers.
   - Alternatives: In MicroPython, you can still go low-level with
     `machine.SPI` instead of `Pimoroni` modules.

Writing low-level drivers is rewarding but error-prone—start small, test incrementally,
and refer to existing open-source implementations for inspiration.

