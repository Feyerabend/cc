
> [!IMPORTANT]  
> This example require a small LCD display, in this case *Pimironi Pico Display Pack*
> or *Pimironi Pico Display Pack 2.0* intended for Raspberry Pi Pico.
> The displays also requires a custom installation of MicroPython which can
> be found on GitHub for Pimironi accessories.


## Optimisation on Embedded Computers and Microprocessors

Optimisation in the context of embedded computers and microprocessors refers to the
process of improving software (and sometimes hardware) to make it run more efficiently,
using fewer resources while maintaining or enhancing functionality. Embedded systems
are specialised computing devices integrated into larger products, like sensors, IoT 
devices, wearables, or microcontrollers (e.g., in cars, appliances, or hobby projects).
They typically have constrained hardware: limited CPU power, small amounts of RAM
(often kilobytes), flash storage, and battery life concerns. Microprocessors, like the
RP2040 in the Raspberry Pi Pico, are the core computing units in these systems.



#### 1. What is Optimisation in Embedded Systems?

Optimisation involves techniques to reduce:
- *Execution time (speed/performance)*: Making code run faster to handle real-time
  tasks, like updating a display at 50 FPS.
- *Memory usage*: Minimising RAM (for runtime data) and flash (for code/storage)
  consumption, as embedded devices often have only 264KB RAM (like the RP2040).
- *Power consumption*: Extending battery life by reducing CPU cycles, I/O operations,
  or peripheral usage.
- *Code size*: Smaller binaries fit into limited storage and load faster.

Types of optimisation:
- *Algorithmic*: Choosing efficient algorithms (e.g., O(n) over O(n²) for loops).
- *Code-level*: Refactoring for fewer operations, like precomputing values or using
  bitwise operations instead of arithmetic.
- *Compiler-level*: Using flags (e.g., `-O2` in GCC for C) to let the compiler inline
  functions or unroll loops.
- *Hardware-specific*: Leveraging features like DMA (Direct Memory Access) for I/O
  without CPU intervention, or overclocking.
- *Language choice*: Switching from interpreted languages (e.g., Python) to compiled
  ones (e.g., C) for better performance.

In embedded systems, optimisation is often a trade-off: faster code might use more
memory, or vice versa.


#### 2. Why is Optimisation Important?

Embedded systems operate under tight constraints, unlike desktops or servers with
abundant resources.

- *Resource Limitations*: Devices like the RPi Pico have a dual-core ARM Cortex-M0+
  at 133 MHz, 264KB SRAM, and 2MB flash. Overusing these can cause crashes, slowdowns,
  or failure to meet real-time requirements (e.g., a game dropping frames or a sensor
  missing data).
  
- *Real-Time Performance*: Many applications require predictable timing, such as
  controlling motors, processing sensor data, or rendering graphics. Poor optimisation
  leads to jitter, delays, or missed deadlines, which could be critical (e.g., in
  medical devices or autonomous drones).

- *Power Efficiency*: Embedded devices often run on batteries or low-power sources.
  Inefficient code increases CPU usage, heat, and energy drain. For example, looping
  unnecessarily might keep the CPU at full throttle, shortening battery life from hours
  to minutes.

- *Cost and Scalability*: Optimised code allows cheaper hardware (e.g., a $4 Pico
  instead of a $35 Raspberry Pi). It also enables scaling to production, where thousands
  of units must work reliably without excess power or heat issues.

- *Reliability and Safety*: In safety-critical systems (e.g., automotive ECUs), unoptimised
  code could lead to overflows, race conditions, or failures. Optimisation ensures stability.

Without optimisation, software might not even run: e.g., a memory-intensive Python script
could exceed the Pico's RAM, causing a hard fault.


#### 3. How is Optimisation Done?

Optimisation is iterative: profile (measure bottlenecks), refactor, test. Tools include
profilers (e.g., MicroPython's `micropython.mem_info()`), oscilloscopes for timing, or
power meters.

General techniques:
- *Precompute Constants*: Calculate values once at startup instead of repeatedly (e.g.,
  scaling factors).
- *Reduce Loops and Conditionals*: Use lookup tables, unroll loops, or batch operations.
- *Memory Management*: Use fixed-size arrays over dynamic lists; avoid recursion (stack
  overflow risk).
- *I/O Optimisation*: Batch display updates or use hardware acceleration (e.g., SPI
  for displays).
- *Power-Saving Modes*: Put the CPU to sleep when idle; use interrupts over polling.
- *Multithreading*: On multi-core chips like RP2040, offload tasks to the second core.

For microprocessors:
- *Instruction Efficiency*: ARM Cortex-M (in RP2040) favours thumb instructions (16-bit)
  for smaller code.
- *Caching and Pipelining*: Avoid branch mispredictions by linearising code.
- *Peripherals*: Use PIO (Programmable I/O) on RP2040 for custom protocols without
  CPU overhead.


#### 4. Optimisation Specifically for the Raspberry Pi Pico (RP2040)

The RPi Pico is a low-cost microcontroller board based on the RP2040 chip. It's great for
embedded projects but has limitations: no floating-point unit (FPU) in hardware (emulated
in software, slowing floats), limited RAM, and a modest clock speed. Optimisation here
focuses on making the most of its strengths (e.g., dual cores, PIO for flexible I/O, USB
support) while mitigating weaknesses.

Why important for Pico:
- *Performance Bottlenecks*: Running interpreted languages like MicroPython (used in the
  .py files) is slower than native C due to overhead. Games or graphics (like the Pico Display
  pack) need smooth FPS, but unoptimised code can drop below 30 FPS.
- *Memory Constraints*: With only 264KB RAM, large data structures (e.g., lists of game
  objects) can fragment memory. Flash is 2MB, but code bloat reduces space for assets.
- *Power*: Pico draws ~100mA at 5V; inefficient loops spike this, heating the board or draining
  batteries in portable projects.
- *Real-World Use*: Pico is popular for robotics, displays, and sensors. Optimisation ensures
  responsiveness (e.g., button inputs without lag).

How to optimise on Pico:
- *Use Fixed-Point Math*: Avoid floats; use integers or scaled integers (e.g., multiply
  positions by 10 for sub-pixel precision).
- *Overclocking*: Safely boost to 250+ MHz via SDK functions, but monitor heat.
- *PIO and DMA*: Offload SPI/I2C to PIO for displays; DMA for fast data transfers.
- *MicroPython vs. C*: MicroPython is easier but slower (10-100x vs. C). For speed,
  use C/C++ with the Pico SDK.
- *Profiling*: Use GPIO toggles as "markers" and an oscilloscope to time functions.
- *Firmware Size*: Strip unnecessary libraries; use Thumb mode in C.

