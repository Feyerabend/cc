
## Practice: Your Own Homebrew Computer


### 1.

If you are curious about exploring electronics more directly, you might want to start by
reading a little about the basics--for example, see [electronics](./electro/) for some
inspiration. This will give you a sense of how components like resistors, capacitors, and
sensors fit together, and how they can be combined into working circuits.

I should note that I do not have much personal experience with practical electronics myself,
so in this area you will largely be experimenting on your own. That being said, there are many
excellent resources, tutorials, and communities available online to help you get started.

When you move into hands-on projects, you might decide to work with a microcontroller. Some
platforms are especially well-suited for beginners who want to bridge the gap between software
and hardware. Popular choices include:
* Arduino boards, which are widely used in education and hobbyist projects thanks to their
  simplicity and vast ecosystem of tutorials and add-on modules.
* The ESP32 family, which combines microcontroller capabilities with built-in Wi-Fi and
  Bluetooth, making it ideal if you want to experiment with connected devices
  (the "Internet of Things").

Both of these platforms bring you closer to the "electronics" side of computing, since
you are not only writing code but also wiring components together, powering circuits,
and dealing with the physical reality of signals and sensors.


### 2.

But if you want to keep your hands clean then? Consider a middle path: [ready-made](./readymade/).
Building your own computer from scratch can be an immensely rewarding and highly educational
experience, offering hands-on insight into hardware design, assembly, and
troubleshooting. However, this endeavour will inevitably lead you into the broader territory of
electronics fundamentals--such as understanding circuits, voltages, and soldering techniques--which
may feel overwhelming if that's not your primary interest. If you prefer *not* to dive that deeply
into electronics, a balanced middle path exists: leveraging ready-made development kits and modules.
These tools provide modular components that simplify the build process while still allowing you to
customise and learn at your own pace, without requiring extensive electrical engineering knowledge.

A prime example is the Raspberry Pi Foundation's versatile lineup of single-board computers and
accessories, particularly those centred around the Raspberry Pi Pico microcontroller. The "Demo Board"
specifically refers to the VGA, SD Card & Audio Demo Board for Raspberry Pi Pico, detailed in
Chapter 3 of the official Hardware Design with RP2040 document. This open-source reference design
showcases the capabilities of the low-cost RP2040 chip, enabling features like VGA video output
(up to QVGA resolution at 30 fps), SD card storage for media playback, and digital I2S audio
output--all without overburdening the microcontroller's resources, but overclocking might come in to play.
It includes onboard components such as resistors for analog RGB video generation, user buttons
(multiplexed with video signals for I/O efficiency), an SD card slot, and headers for easy integration
with a Raspberry Pi Pico. The board's schematics, PCB layouts, and KiCad files are publicly available
from Raspberry Pi, making it ideal for hobbyists to prototype or even fabricate their own versions.

Commercial implementations, like the Pimoroni Pico VGA Demo Base (based directly on Raspberry Pi's
reference design), make it even more accessible for experimentation. Priced around $22–25, it runs
example programs from Raspberry Pi's pico-playground repository using the C/C++ Pico SDK, demonstrating
fun applications like retro-style VGA graphics, PWM-filtered audio, and video playback from SD
cards--perfect for demos without deep soldering or custom PCB work. For more advanced video needs,
the related Pico DV Demo Base extends this with DVI/HDMI output for higher-resolution digital video
and graphics processing. In a similar vein, community-inspired extensions like the PicoCalc (a compact
add-on for computational tasks, such as embedded calculators or math simulations using the RP2040's
PIO for custom peripherals) highlight how these kits can be tailored for niche projects while keeping
electronics involvement minimal.

In essence, starting with the Demo Board or its variants not only accelerates your project but also
builds confidence for future expansions, bridging the gap between hobbyist tinkering and more advanced
custom builds.

Start with reading the *Hardware Design with RP2040*:
* https://datasheets.raspberrypi.com/rp2040/hardware-design-with-rp2040.pdf

