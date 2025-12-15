
## PIO (Programmable I/O)

The Raspberry Pi Pico's RP2040 microcontroller features a unique Programmable I/O (PIO) subsystem,
a powerful and flexible tool for handling low-level, time-critical tasks. PIO allows developers
to create custom peripheral interfaces or offload repetitive I/O operations from the CPU, enabling
precise control over GPIO pins with minimal processor intervention.


## What is PIO?

PIO is a dedicated hardware block in the RP2040 that consists of eight state machines (four per PIO
block, with two PIO blocks available) and a small instruction memory. Each state machine can execute
a program written in a specialized assembly language, allowing fine-grained control over GPIO pins,
data shifting, and timing. PIO is particularly useful for tasks requiring high-speed or deterministic
I/O operations, such as driving LEDs, implementing communication protocols, or generating signals.


### Features of PIO

- *Eight State Machines*: Four per PIO block, each capable of running independent programs.
- *Instruction Memory*: Each PIO block has 32 instruction slots shared among its state machines.
- *Flexible I/O*: State machines can control GPIO pins for input, output, or side-set operations
  (e.g., toggling pins simultaneously with instruction execution).
- *FIFOs*: Each state machine has TX (transmit) and RX (receive) FIFOs for data exchange with the CPU.
- *Shift Registers*: Input (ISR) and Output (OSR) shift registers for serializing or deserializing data.
- *Clock Control*: Instructions can include delays for precise timing, and the clock can be divided
  for custom frequencies.
- *Interrupts*: State machines can set and wait on IRQs for synchronization with the CPU or other
  state machines.


### PIO Instructions

PIO programs use a simple instruction set, including:
- *JMP*: Jump to a program address, optionally with conditions (e.g., based on register values or pin states).
- *WAIT*: Pause execution until a condition is met (e.g., GPIO pin state or IRQ).
- *IN/OUT*: Shift data into or out of shift registers, sourcing or sinking to pins, registers, or FIFOs.
- *PUSH/PULL*: Move data between shift registers and FIFOs, with optional blocking behavior.
- *MOV*: Copy data between registers, pins, or other sources, with optional operations (e.g., bit reversal).
- *IRQ*: Set or clear interrupt flags for synchronization.
- *SET*: Set pin states, register values, or pin directions.
- *NOP*: No operation, often used for timing delays.

Each instruction can include a delay (extra cycles before execution completes) and a side-set operation 
(toggling specific pins).


### Examples

Below are explanations of the example PIO programs provided.
These examples demonstrate common use cases for PIO in real-world applications.


#### 1. LED Blink (`blink_program`)
*Purpose*: Toggles a single GPIO pin to create a blinking LED effect.

*What It Does*:
- The program continuously sets a GPIO pin high (LED on) and low (LED off) in a loop.
- It uses delays to control the blinking frequency, creating a visible on/off pattern.
- The program runs indefinitely, wrapping back to the start after each cycle.

*Use Case*:
- Ideal for simple status indicators or testing GPIO output functionality.
- Demonstrates basic pin control and timing using PIO's `SET` instruction and delays.


#### 2. WS2812 RGB LED Driver (`ws2812_program`)
*Purpose*: Drives WS2812 (NeoPixel) RGB LEDs by generating precise bit-banged serial data.

*What It Does*:
- The program sends RGB color data to WS2812 LEDs, which require a specific high-speed serial protocol.
- It shifts out bits from a FIFO, using side-set operations to toggle the data pin with precise timing.
- For each bit, it generates either a "1" or "0" waveform (different pulse widths) to encode the data.
- The program loops to process multiple bits, enabling continuous data streaming for multiple LEDs.

*Use Case*:
- Commonly used for controlling addressable LED strips in lighting projects.
- Shows PIO's ability to handle high-speed, timing-critical protocols without CPU intervention.


#### 3. UART Transmit (`uart_tx_program`)
*Purpose*: Implements a UART (serial) transmitter to send data over a single pin.

*What It Does*:
- The program transmits bytes of data as a UART serial signal, including start and stop bits.
- It pulls data from a FIFO, shifts out each bit (LSB first) on a GPIO pin, and maintains precise
  timing for the baud rate.
- Side-set operations manage the idle state of the TX pin (typically high).
- The program loops to transmit multiple bytes sequentially.

*Use Case*:
- Useful for serial communication with devices like sensors, displays, or other microcontrollers.
- Highlights PIO's capability to implement standard communication protocols with minimal CPU overhead.


#### 4. Counter with Conditional Jump (`counter_program`)
*Purpose*: Generates a counting sequence and triggers an interrupt when complete.

*What It Does*:
- The program initializes a register with a starting value (e.g., 31) and decrements it in a loop.
- Each iteration outputs the current count to a set of GPIO pins.
- When the counter reaches zero, it triggers an IRQ to signal completion and jumps to a new address
  (e.g., halting or restarting).
- The program demonstrates conditional branching based on register values.

*Use Case*:
- Suitable for applications requiring periodic counting or event signaling, such as timers or state machines.
- Illustrates PIO's use of conditional jumps and IRQs for program flow control and CPU interaction.


### Getting Started with PIO
To use PIO on the RP2040:
1. *Write a PIO Program*: Use the PIO assembly language to define the behavior (as shown in the examples).
2. *Configure the State Machine*: Set pin mappings, FIFO thresholds, clock dividers, and other parameters.
3. *Load and Run*: Load the program into a PIO block's instruction memory and start the state machine.
4. *Interact via FIFOs*: Use the CPU to push data to the TX FIFO or pull data from the RX FIFO as needed.

The provided code includes a simplified Python-based emulator to simulate these PIO programs, allowing you
to test and observe their behavior without hardware. Each demo function (`demo_blink`, `demo_ws2812`, etc.)
sets up a state machine, loads the respective program, and runs a simulation to show the output on virtual GPIO pins.

