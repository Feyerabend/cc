
## Building a Retrocomputer

This project marks the beginning of your own retrocomputing adventure. We are emulating the
legendary MOS 6502 microprocessor on a Raspberry Pi Pico 2 (or Pico 2W) with larger memory
than the original Pico, and connecting it to the Pimoroni Display Pack 2.0
(a tiny 320x240 colour LCD with four buttons, see the section on displays).
Because we are starting almost from scratch (only a small driver layer for the
display and a well-known open-source 6502 emulator core), we have complete freedom to shape
"our computer" exactly as we want.

The 6502 is one of the most influential 8-bit CPUs ever designed. Released by MOS Technology
in 1975 for just $25 (at a time when an Intel 8080 cost $179), it democratised computing and
especially gaming:

- *Apple I (1976)* and *Apple II series (1977–1993)* – Steve Wozniak chose the 6502 for its
  simplicity and low cost; the Apple II became one of the first highly successful mass-produced
  microcomputers.
- *Commodore PET (1977)*, *VIC-20 (1980)*, and especially the *Commodore 64 (1982)* – the C64
  sold an estimated 12–17 million units, making it the best-selling single computer model of
  all time. Its advanced SID sound chip and colourful graphics (thanks to the VIC-II chip)
  turned it into a legendary gaming and demo-scene machine.
- *Atari 400/800 (1979)* and the Atari 2600 console (1977, using the 6507 variant).
- *BBC Micro (1981)* – the educational standard in UK schools.
- *Nintendo Entertainment System (1983)* – used a Ricoh 2A03/2A07
  (6502 core without decimal mode).

The 6502’s elegant instruction set, low pin count, and excellent price/performance ratio
made it the heart of the 8-bit revolution.

Here we bring that heart back to life on modern hardware. We run a tiny ROM that initialises
a C64-style text screen (40×30 characters), draws a border, displays a welcome message,
and reads the four buttons via a simulated CIA port. The display is double-buffered in RAM
to eliminate flicker, and everything is drawn using a classic 5×8 pixel font padded to 8×8
cells--exactly the spirit of 1980s home computers.


### A good starting point for many projects ..

Because we control every layer--the CPU emulation, memory map, I/O ports, display driver,
and input--this platform is extraordinarily extensible (and flexible to change):

1. *Graphics enhancements*
   - Add pixel-accurate drawing routines, multicolour modes, or hardware scrolling.
   - Implement sprites (moving objects) by extending the VIC-II emulation.
   - Experiment with higher resolutions or palette cycling for demos.

2. *Sound*
   - Drive a piezo buzzer or I²S DAC to emulate the SID chip
     (even a simple square-wave synthesizer is rewarding).

3. *Storage and filesystems*
   - Attach an SD card (SPI) and implement a simple disk loader
    (like the C64’s 1541 emulation).  
   - Load larger programs or games from "virtual floppy images".

4. *Networking (Pico 2W)*
   - Use the built-in Wi-Fi to fetch programs over HTTP, implement a tiny BBS,
     or even network two Picos for multiplayer games.

5. *Compilers and interpreters (Chapter 5 and beyond)*
   - Write a compiler that targets 6502 machine code and runs natively on our emulator.
   - Implement a BASIC interpreter, Forth, or Lisp directly in the emulated address space.
   - Cross-compile from the host ARM Cortex-M0+ cores to 6502, creating hybrid programs
     that use both processors (e.g., the ARM handles Wi-Fi while the 6502 runs the retro
     game logic; but don't be too optimistic on speed, in that confíguration).

6. *Educational and documentation projects*
   - Every change is visible: add logging of CPU cycles, disassembler overlays,
     or on-screen registers.
   - Create interactive tutorials ("watch how LDA works") displayed on the same screen.
   - Document the entire system as an open-source retrocomputer design.

In short, this tiny board becomes a complete, programmable 1980s-style computer that
you can evolve in any direction you like--graphics, sound, networking, languages,
or even new "peripherals" you invent. The next chapters 5 will explore many of these paths,
starting with language implementations. In that way you can continue with this project
into the next chapter.



#### NOTE: Using fake6502 project for the emulator

We are using the [fake6502](https://github.com/ivop/fake6502) project from GitHub as
our 6502 emulator. Although my background is primarily in Zilog Z80 assembly and most
of my low-level experience comes from that architecture in 1980/1981, working with
the MOS 6502 has been surprisingly straightforward. The 6502 instruction set is
significantly smaller and more orthogonal, which makes it easier to reason about and,
in many cases, simpler to write hand-crafted assembly for.

Compared to the Z80, the 6502 relies more on a limited set of registers and addressing
modes, which encourages quite a different programming style. While this can feel
restrictive at first, it often results in clearer and more predictable code. This
simplicity also makes the 6502 a good platform for learning, experimentation, and
emulator-based projects such as this one, where understanding the CPU’s behavior at
an instruction level is essential.


