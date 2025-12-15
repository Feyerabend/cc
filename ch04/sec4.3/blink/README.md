
## Raspberry Pi Pico Family Development Environment Setup

- A Raspberry Pi Pico/Pico W board (or if you so wish also: RPi 2/RPi 2 W)
- A micro USB cable
- A computer running Windows, macOS, or Linux

The first reason the Raspberry Pi Pico was chosen as a starting point is its accessibility. 
Unlike many other development boards, you almost never--if ever--need to solder anything. 
This lowers the entry barrier considerably, since you can begin experimenting with 
breadboards, jumper wires, and simple components without needing to master soldering 
techniques first. In fact, you don’t even need to understand electronics in any great 
detail in order to get your first programs running and your first LEDs blinking. 
That said, this simplicity is only the beginning. If you want to progress beyond the 
introductory level, sooner or later you will need to get your hands dirty with 
electronics: understanding currents, voltages, and logic levels; reading datasheets; 
and eventually designing and wiring circuits from the ground up. The Pico provides a 
gentle introduction, but it also leaves room to grow.

Another reason for choosing the Pico is its orientation toward *software* compared to 
many other microcontrollers. While boards such as Arduino are certainly beginner-friendly, 
they tend to emphasise hardware-level control and embedded applications. The Pico, by 
contrast, makes it natural to approach microcontroller programming from a more "software 
first" perspective: Python support (via MicroPython) comes out of the box, and even the C 
SDK feels approachable, if you have prior experience in general-purpose programming. 
This makes it an excellent bridge for someone coming from a programming background 
who wants to explore electronics gradually, without being overwhelmed by hardware details 
from day one.

Finally, the Pico benefits from an enormous community and a wealth of tutorials, 
guides, and example projects. This means you are rarely left on your own when trying 
to figure out how to connect a sensor, control a display, or configure an input/output pin. 
The official Raspberry Pi Foundation provides a solid starting point with their 
"Getting Started with the Pico" guide:
https://projects.raspberrypi.org/en/projects/getting-started-with-the-pico.

By combining ease of entry, a software-friendly orientation, and abundant resources, 
the Pico is an ideal foundation for a journey that starts with blinking LEDs 
and gradually builds up toward a full blinkenlights computer.


### MicroPython Setup


#### 1. Install Thonny IDE
Thonny IDE provides a very convenient way for you to install it with one click, making
it the recommended editor for MicroPython development on the Pico/Pico W.

*Download and install Thonny:*
- Visit [thonny.org](https://thonny.org) and download the appropriate version for your
  operating system
- Install following the standard process for your OS


#### 2. Install MicroPython Firmware
*Method 1: Using Thonny (Recommended)*
1. Connect your Pico/Pico W while holding the BOOTSEL button
2. Release the BOOTSEL button after your Pico is mount as a
   Mass Storage Device called RPI-RP2
3. Open Thonny IDE
4. Go to Tools -> Options -> Interpreter
5. Select "MicroPython (Raspberry Pi Pico)" as the interpreter, or
   "MicroPython (Raspberry Pi Pico W)" as the interpreter
6. Click "Install or update MicroPython" and follow the prompts

*Method 2: Manual Installation*
1. Download the latest MicroPython UF2 file for
   Pico from [micropython.org](https://micropython.org/download/RPI_PICO/), or
   Pico W from [micropython.org](https://micropython.org/download/RPI_PICO_W/)
2. Hold BOOTSEL while connecting the Pico/Pico W to your computer
3. Drag and drop the UF2 file to the RPI-RP2 drive that appears
4. The Pico/Pico W will automatically reboot with MicroPython installed


#### 3. Verify Installation
- In Thonny, you should see the MicroPython REPL (command prompt) in the shell
- Try typing `print("Hello, Pico W!")` to test




### C/C++ SDK Setup

The C/C++ SDK provides more control and better performance but requires more setup.
The tools can be tricky, and versions of software confusing.


#### 1. Install Required Tools

*Windows:*
- Download and install the official Pico SDK installer from the Raspberry Pi website
- This includes CMake, Build Tools for Visual Studio, Git, and the ARM GCC compiler
- Alternatively, install manually: Visual Studio Code, CMake, Git, and ARM GCC toolchain
  (See below.)

*macOS:*
- Install Xcode command line tools: `xcode-select --install`
- Install CMake: `brew install cmake` (requires Homebrew)
- Install ARM GCC toolchain: `brew install --cask gcc-arm-embedded`
- Alternatively, see below on installing Visual Studio Code.

*Linux (Ubuntu/Debian):*
```bash
sudo apt update
sudo apt install cmake gcc-arm-none-eabi libnewlib-arm-none-eabi build-essential git
```

#### 2. Download the Pico SDK
```bash
git clone https://github.com/raspberrypi/pico-sdk.git
cd pico-sdk
git submodule update --init
```

#### 3. Set Environment Variables
*Windows:* Add `PICO_SDK_PATH` pointing to your SDK directory
*macOS/Linux:* Add to your shell profile:
```bash
export PICO_SDK_PATH=/path/to/pico-sdk
```

#### 4. Install Visual Studio Code Extensions (Recommended)
- C/C++ Extension Pack
- CMake Tools
- Raspberry Pi Pico extension (provides project templates)

#### 5. Create Your First Project
1. Create a new directory for your project
2. Include the pico_sdk_import.cmake file and
   set up your CMakeLists.txt
3. Use the basic project template structure

#### 6. Building and Flashing
1. Create a build directory: `mkdir build && cd build`
2. Configure: `cmake ..`
3. Build: `make` (or `cmake --build .`)
4. Hold down the BOOTSEL on the Pico W as you plug it in,
   and it will show as an external drive
5. Copy the generated UF2 file to the RPI-RP2 drive



### Alternative Setup C/C++ SDK

Installing the Raspberry Pi Pico C/C++ SDK Workflow in VS Code.

__1. Install prerequisites__

You’ll need:
- VS Code (latest release).
- CMake (≥ 3.13).
- Ninja build system (optional, but recommended).
- ARM GCC Toolchain (arm-none-eabi-gcc).
- Git (to fetch SDK and examples).

On Linux/macOS you can install from package managers.
On Windows, use the official installers.



__2. Install VS Code Extensions__

From the VS Code Marketplace, install:
- CMake Tools (by Microsoft).
- C/C++ Extension Pack (IntelliSense + debugging).
- Raspberry Pi Pico Project (official helper extension
  from Raspberry Pi Ltd).

The Pico extension gives you:
- "Create New Project" wizard.
- Auto-setup for the SDK.
- Build + flash buttons.
- Debug integration.



__3. Clone the SDK and Examples__

You need the SDK available on your system.

```
git clone -b master https://github.com/raspberrypi/pico-sdk.git
git clone -b master https://github.com/raspberrypi/pico-examples.git
```

Set an environment variable to tell CMake where the SDK is.
On Linux/macOS, in ~/.bashrc:

```
export PICO_SDK_PATH=$HOME/pico-sdk
```

On Windows (PowerShell):

```
setx PICO_SDK_PATH "C:\Users\YourName\pico-sdk"
```

Restart VS Code afterwards so it picks this up.


__4. Open a Project in VS Code__
- Open the pico-examples folder in VS Code.
- The Pico extension will detect it’s a Pico project.
- It'll generate a CMake build folder (e.g. build).

You’ll see build options appear in the CMake Tools
status bar at the bottom.



__5. Build a UF2 firmware__
- From the VS Code command palette (Ctrl+Shift+P),
  choose CMake: Configure.
- Then CMake: Build.

This produces a .uf2 file in the build folder.


__6. Flash onto the Pico__
- Hold BOOTSEL button while plugging in the Pico to your computer.
- It will appear as a USB drive.
- Copy the .uf2 file to it (or use the VS Code flash command if
  the extension supports direct upload).
- The Pico will reboot and run your program.



__7. (Optional) Debugging__

If you have a Raspberry Pi Debug Probe (or a Pico acting as a SWD probe),
you can use VS Code’s built-in debugger:
- Install OpenOCD.
- Connect via SWD.
- Use the Pico VS Code extension’s debug configuration.



#### Summary
- Install toolchain (CMake + GCC ARM).
- Install VS Code + Pico + CMake extensions.
- Set PICO_SDK_PATH.
- Clone pico-examples.
- Build .uf2 inside VS Code.
- Copy to Pico over USB.




### Key Differences C vs MicroPython

*MicroPython:*
- Easier to get started
- Interactive development with REPL
- Slower execution but faster development
- Great for prototyping and learning
- Built-in WiFi libraries for Pico W

*C/C++:*
- Better performance and memory efficiency
- More complex setup
- Full access to hardware features
- Industry-standard for production embedded systems
- Requires compilation step


### Official Resources

- [Raspberry Pi documentation](https://raspberrypi.com/documentation/microcontrollers/)
- [Pico SDK](https://github.com/raspberrypi/pico-sdk)
- [RP2040 Datasheet](https://datasheets.raspberrypi.org/rp2040/rp2040-datasheet.pdf)
- [Pico Datasheet](https://datasheets.raspberrypi.org/pico/pico-datasheet.pdf)
- [Pico W Datasheet](https://datasheets.raspberrypi.org/picow/pico-w-datasheet.pdf)
- [Raspberry Pi Pico SDK Documentation](https://raspberrypi.github.io/pico-sdk-doxygen/)
- [Datasheets](https://datasheets.raspberrypi.com)

Both development paths are well-supported, and your choice depends
on your project requirements, performance needs, and personal preferences.
MicroPython is excellent for beginners and rapid prototyping, while C/C++
offers maximum control and performance for production applications.
