
## Cores on the Raspberry Pi Pico


### Raspberry Pi Pico (RP2040)

The RP2040 contains two ARM Cortex-M0+ cores, both intended for general-purpose programmability.
They are symmetric, meaning they have the same capabilities and neither has a special predefined
"system" or "application" role. Their key characteristics are:

1. Shared Responsibilities
Both cores can run any part of your program. You decide in software how to divide the work.
A common pattern is to let:
- Core 0 run the main application logic.
- Core 1 handle continuous or time-critical tasks, such as real-time sensor polling or
  feeding the PIO with data.
This is only a convention; nothing enforces it.

2. Shared Memory Model
The two cores share the same memory space (SRAM and flash), so they can operate on the
same data structures. Because of this, synchronisation primitives are needed to avoid
race conditions. The chip provides:
- Hardware spinlocks
- FIFOs and IRQs
- Mutexes and semaphores in the SDK

3. Use With PIO
The RP2040 has PIO state machines that offload deterministic I/O. A common design is:
- A PIO program handles a protocol (for example WS2812 output or UART)
- One of the cores acts as a data feeder
- The other core performs calculations or system tasks
Again, the cores are not required to divide work this way, but this is an effective pattern.

In short, the two cores in the Pico are fully symmetric general-purpose compute units,
cooperatively sharing memory and peripherals.



### Raspberry Pi Pico 2 (RP2350)

The Pico 2’s RP2350 continues the dual-core approach, but with stronger and more flexible
cores. The architecture is still dual-core symmetric, but the big difference is that each
core can run either an ARM Cortex-M33 or a RISC-V Ibex (selected at boot). Regardless of
which ISA you choose, both cores have the same role:

1. Symmetric Dual-Core Execution
Just like the RP2040, both cores can run application code, handle interrupts, and share
system responsibilities. There is still no dedicated "supervisor" core.

2. Improved Performance and Security
The ARM option (Cortex-M33) adds TrustZone and DSP extensions, giving:
- Faster general arithmetic
- Hardware acceleration for certain operations
- Optional separation of secure/non-secure workload
This does not change the role of the core, only what it can efficiently execute.

3. Same General Usage Pattern as RP2040
Firmware design on Pico 2 typically follows the same strategies as on the original Pico:
- One core can drive I/O or time-critical tasks
- The other can do calculations or system logic
- Both can interact with PIO and shared memory
Synchronisation mechanisms and the shared memory model remain very similar,
just with a faster engine underneath.

In short, Pico 2 keeps the same conceptual dual-core model as Pico 1,
but with more powerful and configurable cores.


Both Pico and Pico 2 use two fully symmetric general-purpose cores that
share memory and peripherals, and it is always the programmer who decides
how to divide tasks between them; the difference is simply that Pico 2’s
cores are more advanced and optionally RISC-V.

