
> *The Pimoroni display packs chosen here are used primarily for convenience and simplicity, and
we do not endorse any particular display over another. The same applies to the choice of the
Raspberry Pi Pico, which is used here for practical reasons rather than as a recommendation
over other microcontrollers.*

> [!NOTE]
> For greater performance and the highly resource demanding properties of both displays and images, we will use the Raspberry Pi Pico 2 (RP2350: dual-core Cortex-M33 or dual Hazard3 RISC-V cores, 150 MHz, 520 KB SRAM, 4 MB flash) in the following folders. Also as file handling differs a bit between Pico variations, we will assume that a SD card setup as it is used in [file storage](./../storage/file/).
> For display work, we use the Pimoroni Display Pack 2.0, though the older Display Pack can often work with small modifications. Note that displays commonly demand significant power, substantial memory, and high update speed--especially for applications that make use of images.


## Displays for the Raspberry Pi Pico

There are many options for displays even for such very simple microcontrollers as the
Raspberry Pi Pico. From tiny monochrome screens for basic readouts to vibrant colour
panels for games and GUIs, these add-ons connect via simple interfaces like SPI, I2C,
or GPIO, making them a breeze to integrate with MicroPython or C/C++. Whether you're
building a retro game like our Atari-inspired tank combat or a weather station, there's
a display to fit your power budget, size needs, and style. Below, we will break down the
main types (LCD, OLED, TFT, and ePaper) with pros/cons, followed by a table of popular
picks as of 2025.


#### Quick Primer on Display Types

- *LCD (Liquid Crystal Display)*: Affordable and widely available, these use backlighting
  for visibility. Great for colourful projects but can drain battery faster due to the light
  source. Often character-based (e.g., 16x2 text) or graphic.
- *TFT (Thin-Film Transistor LCD)*: A step up from basic LCDs--sharper, faster refresh rates,
  and better colours thanks to transistor tech. Ideal for animations or games on the Pico's
  limited pins.
- *OLED (Organic Light-Emitting Diode)*: Self-lit pixels mean true blacks, infinite contrast,
  and super-low power (no backlight!). Perfect for text-heavy or battery-powered apps,
  though pricier and limited in size.
- *ePaper (Electronic Paper)*: Mimics ink on paper-bistable (holds image without power),
  sunlight-readable, and ultra-efficient. Best for static info like labels or sensors,
  not fast video.

Most are Pico-ready with libraries like `picographics` (Pimoroni), `adafruit_ssd1306`
(OLEDs), or `st7735` (TFTs) in MicroPython. Power draw varies: OLED/ePaper ~mW, LCD/TFT ~10-50mW.


#### Popular Display Options for Pico

Here's a selection of current favourites from major vendors. Prices are approximate USD
(as of mid-2025) and can fluctuate; check retailers like Adafruit, Pimoroni, Waveshare,
or PiShop for stock.

| Vendor     | Type  | Size / Resolution       | Interface | Price | Notes & Pico Fit |
|------------|-------|-------------------------|-----------|-------|------------------|
| Pimoroni  | TFT (IPS LCD) | 1.14" / 240x135 | SPI | $20 | Original Display Pack: Buttons + RGB LED included. Great for small games like our tank combat. |
| Pimoroni  | TFT (IPS LCD) | 2.0" / 320x240 | SPI | $25 | Display Pack 2.0: Larger, vibrant colours; easy backpack mount. Updated for Pico 2 (RP2350). |
| Adafruit  | OLED (Monochrome) | 0.96" / 128x64 | I2C/SPI | $12-18 | STEMMA QT connector for easy wiring. Low-power text display; use with `adafruit_displayio`. |
| Adafruit  | OLED (Monochrome) | 1.3" / 128x64 | I2C/SPI | $20 | SH1106 driver; compact for wearables. Excellent contrast for dark environments. |
| Adafruit  | TFT | 1.14" / 240x135 | SPI | $10 | ST7789 chip + microSD; cooler breakout for prototypes. Matches Pimoroni's original res. |
| Adafruit  | TFT | 1.8" / 128x160 | SPI | $20 | ST7735R + microSD; adds storage for game assets. |
| Adafruit  | TFT (Touch) | 2.8" / 320x240 | SPI | $30 | ILI9341 + cap touch; bigger for GUIs, but uses more pins. |
| Waveshare | LCD (Colour) | 1.8" / 160x128 | SPI | $15 | ST7735S driver; 65K coolers, MicroPython demos included. Simple embed. |
| Waveshare | TFT (Touch IPS) | 3.5" / 480x320 | SPI | $25 | Dedicated touch controller; smooth for interactive apps. |
| Waveshare / Pi Hut | ePaper | 2.13" / 250x122 | SPI | $20-25 | Bistable, black/white; holds updates forever. Ideal for low-power IoT. |
| Adafruit  | ePaper | 2.7" / 264x176 | SPI | $30 | Monochrome; sunlight-readable for outdoor Pico projects. |


### Pimoroni Pico Display Pack (Original)

The *Pimoroni Pico Display Pack* is a compact add-on board for the Raspberry Pi Pico
(or Pico W), designed to give your Pico a colourful display and basic input for projects
like mini games, interfaces, or sensor readouts. Released around early 2021, it’s a
"backpack" that attaches to the underside of the Pico, making it ideal for portable
or embedded applications.


#### Key Features

| Feature | Details |
|---------|---------|
| *Display* | 1.14-inch IPS LCD, 240x135 pixels (~210 PPI), 18-bit cooler (65K colours), decent viewing angles, and backlit. Uses SPI interface (pins: CS, DC, SCLK, MOSI) with PWM brightness control. |
| *Input/Output* | Four tactile buttons (A/B/X/Y, mapped to GPIO 12-15 by default). One RGB LED for status or effects. |
| *Compatibility* | Works with Raspberry Pi Pico/Pico W (needs male headers on the Pico). Supports MicroPython (via Pimoroni’s UF2 build with `picodisplay` library), CircuitPython (ST7789 driver), or C/C++. Stackable with other Pico add-ons. |
| *Dimensions & Build* | ~35mm x 25mm x 9mm (L x W x H). No soldering if Pico has headers. Compact but slightly delicate buttons. |
| *Power* | Runs off Pico’s 3.3V, low power for battery setups. |


#### Comparison to Pico Display Pack 2.0

- *Screen Size*: Original has a 1.14-inch, 240x135 display; the 2.0 version upgrades to a 2.0-inch,
  320x240 screen for sharper, larger visuals.
- *Code*: Uses `picodisplay` in MicroPython (vs. `picodisplay2` for 2.0). Swap the display constant
  (`DISPLAY_PICO_DISPLAY` vs. `DISPLAY_PICO_DISPLAY_2`) and adjust resolution in code to port projects.
- *Form Factor*: Same button layout and RGB LED, but the original is smaller, fitting tightly on the Pico.


#### Getting Started

1. *Setup*: Attach to a Pico with headers. No soldering needed if prepped.

2. *Software*: Flash Pimoroni’s MicroPython UF2 (from their GitHub). Basic example:
   ```python
   from picodisplay import PicoDisplay
   import time

   display = PicoDisplay()
   display.set_backlight(1.0)  # Max brightness
   display.set_pen(255, 255, 255)  # White
   display.text("Hello, Pico Display!", 10, 60, scale=2)
   display.update()
   time.sleep(1)
   ```
   Check Pimoroni’s tutorials for more (GitHub or their site).

3. *Use Cases*: Great for simple games, small dashboards, or IoT displays.



### Pimoroni Pico Display Pack 2.0

The *Pico Display Pack 2.0* is a compact add-on board from Pimoroni designed specifically
for the Raspberry Pi Pico (or Pico W). It's essentially a "backpack" that snaps onto the
underside of your Pico, turning it into a portable display-equipped device perfect for
embedded projects, games, or interfaces. Released around mid-2024, it's an upgraded version
of the original Pico Display Pack, offering a larger, higher-resolution screen while keeping
the same easy-to-use form factor.


#### Key Features

| Feature | Details |
|---------|---------|
| *Display* | 2.0-inch (50.8mm) IPS LCD, 320 x 240 pixels (~220 PPI), 18-bit cooler (65K coolers), wide viewing angles, and vibrant backlighting. Communicates via SPI (pins: CS, DC, SCLK, MOSI) with PWM-controlled brightness. |
| *Input/Output* | Four tactile buttons (labeled A/B/X/Y, connected to GPIO 12-15 by default) for user interaction. Includes a single RGB LED for status indicators. |
| *Compatibility* | - Raspberry Pi Pico/Pico W (requires male headers soldered on the Pico).<br>- Works with MicroPython (Pimoroni's custom UF2 build), CircuitPython (via Adafruit DisplayIO), or C/C++.<br>- Stackable with other Pico add-ons like Pico Omnibus or Pico Decker (though it may overhang slightly). |
| *Dimensions & Build* | Approx. 53mm x 25mm x 9mm (L x W x H). No soldering needed if your Pico has headers. The screen protrudes slightly above the buttons, so use gentle fingertip presses to avoid accidental touches. |
| *Power* | Draws from the Pico (3.3V logic), low power for battery projects. |


#### What's New vs. Original Pico Display Pack?

- *Bigger Screen*: Original is 1.14-inch at 240x135; 2.0 is double the diagonal and resolution
  for sharper graphics and more real estate.
- *Code Migration*: Super simple-- in MicroPython, swap `import picodisplay` to `import picodisplay2`
  or use `DISPLAY_PICO_DISPLAY_2` constant.
- Same button layout and RGB LED, but more space for custom Pico projects (e.g., mounting on larger bases).



#### Getting Started

1. *Hardware Setup*: Buy a Pico with headers (or solder your own). Snap the pack onto the Pico's
   underside--pins align automatically.

2. *Software*:
   - *MicroPython*: Flash Pimoroni's custom UF2 from their GitHub (includes `picographics` library).
     Example code for basics:
     ```python
     import picodisplay2 as picodisplay
     import time

     display = picodisplay.PicoDisplay2()
     display.set_backlight(1.0)  # Full brightness

     while True:
         display.set_pen(picodisplay.WHITE)
         display.clear()
         display.text("Hello, Pico Display 2.0!", 10, 100, scale=2)
         display.update()
         time.sleep(1)
     ```
     Tutorials and full examples are on Pimoroni's site.
   - *CircuitPython*: Use Adafruit's bundle; look for the ST7789 driver example.

3. *Projects Ideas*: Retro games (like the Atari-style tank combat I coded
   earlier--just update the display init to `DISPLAY_PICO_DISPLAY_2` and scale
   graphics to 320x240), sensors dashboards, portable music players,
   or even a mini weather station.

Upgrade is trivial from the original to the newer: Change `DISPLAY_PICO_DISPLAY_PACK`
to `DISPLAY_PICO_DISPLAY_2`, bump WIDTH/HEIGHT to 320/240, and adjust coordinates/scaling.

