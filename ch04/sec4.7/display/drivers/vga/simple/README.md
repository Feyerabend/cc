
## Simple 3-bit VGA Setup Instructions

- Raspberry Pi Pico
- 3x 270Ω resistors (for RGB)
- VGA connector (DB15 female)
- Breadboard and jumper wires

```
Pico GPIO → Resistor → VGA Pin
─────────────────────────────────
GPIO 0 → 270Ω → Pin 1 (Red)
GPIO 1 → 270Ω → Pin 2 (Green)  
GPIO 2 → 270Ω → Pin 3 (Blue)
GPIO 3 (direct) → Pin 13 (HSYNC)
GPIO 4 (direct) → Pin 14 (VSYNC)

Pico GND → VGA Pins 5,6,7,8,10 (All grounds)
```

VGA Connector Pinout (DB15 Female):
```
  5  4  3  2  1
10 9  8  7  6
  15 14 13 12 11

Pin 1:  Red Video
Pin 2:  Green Video
Pin 3:  Blue Video
Pin 5:  Ground
Pin 6:  Red Ground
Pin 7:  Green Ground
Pin 8:  Blue Ground
Pin 10: Sync Ground
Pin 13: Horizontal Sync
Pin 14: Vertical Sync
```


### Building

1. Install the Pico C SDK
2. Set environment variable: `export PICO_SDK_PATH=/path/to/pico-sdk`
3. Install cmake and gcc-arm-none-eabi

```bash
mkdir build
cd build
cmake ..
make
```

1. Hold BOOTSEL button on Pico while plugging into USB
2. Copy `test.uf2` to the RPI-RP2 drive
3. Pico will reboot and start generating VGA signal



Static Pattern (default):
- 8 vertical colour bars: Black, Red, Green, Yellow, Blue, Magenta, Cyan, White
- White horizontal lines every 60 pixels

Moving Pattern (press any key in terminal):
- Animated diagonal stripes cycling through all 8 colours
- Pattern moves diagonally across the screen


### Troubleshooting

*No display:*
- Check all ground connections (very important!)
- Verify resistor values (270Ω)
- Ensure VGA monitor supports 640x480 @ 60Hz

*Wrong colours:*
- Check RGB pin connections (GPIO 0=Red, 1=Green, 2=Blue)
- Verify resistors are between GPIO and VGA pins

*Sync issues:*
- Check HSYNC (GPIO 3 → Pin 13) and VSYNC (GPIO 4 → Pin 14)
- Some monitors are (very) picky about sync timing!


Available Colours (3-bit):
```
Binary | Hex | Colour
-------|-----|--------
000    | 0   | Black
001    | 1   | Red
010    | 2   | Green  
011    | 3   | Yellow
100    | 4   | Blue
101    | 5   | Magenta
110    | 6   | Cyan
111    | 7   | White
```


### Code

- *PIO State Machines*: 3 separate programs handle HSYNC, VSYNC, and RGB data
- *Precise Timing*: PIO runs at exact frequencies needed for VGA standard
- *DMA Transfer*: Framebuffer data is automatically sent to display without CPU overhead
- *Real-time Update*: Pattern can be changed while display is running

This is a minimal but fully functional VGA implementation.

![Resistor](./../../../../../assets/image/game/270ohm.png)
