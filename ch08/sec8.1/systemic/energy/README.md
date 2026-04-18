
## Energy Use

Energy use governs the operational sustainability of computing systems--from battery-powered
devices to hyperscale data centers. Every computation, memory access, and I/O operation
consumes energy, which in turn shapes design decisions at every level of the stack: hardware,
operating systems, software, and system architecture. In mobile devices, energy efficiency
directly determines battery life, while in data centers, energy translates into operating cost,
thermal constraints, and environmental impact. At the micro scale, energy limits how long a
sensor can transmit data. At the macro scale, it governs how much computation can be sustained
under power and cooling budgets.

Unlike latency or throughput, energy is a physical budget--a finite supply in portable systems
and a hard constraint in grid-powered environments. Whereas latency can be hidden and computation
parallelised, energy cannot be virtually abstracted away. Even an idle CPU leaks energy through
static power draw, and DRAM refresh cycles persist whether memory is accessed or not. Thus,
energy accounting must consider both active and passive consumption.

Designing for energy efficiency often means making trade-offs across performance, cost, and
complexity. For instance, using a faster CPU may reduce the time to complete a task (saving
dynamic power), but increase peak energy demand (raising thermal load). In embedded systems,
aggressive duty cycling turns off subsystems when idle. In data centers, dynamic voltage and
frequency scaling (DVFS) adjusts power consumption to workload intensity. Across scales,
energy-aware computing means not just using less power, but using power well.


### Where Does the Energy Go?

Energy in computing systems is consumed across several domains:

1. CPU and GPU Power:
   The central processor dominates energy usage in compute-heavy tasks. Dynamic energy is spent
   switching transistors (charging/discharging capacitive loads), and static energy is lost
   through leakage current in transistors, even when idle.
   - DVFS (Dynamic Voltage and Frequency Scaling): Reduces voltage and clock speed under light
     load to save power, though at the cost of reduced performance.
   - Microarchitectural Optimisations: Features like branch prediction, out-of-order execution,
     or SIMD units increase performance per watt but also increase baseline complexity and
     static power draw.

2. Memory and Storage:
   - DRAM Power: Memory is kept alive via periodic refreshes. Energy cost includes row activation,
     precharge, and data I/O. High bandwidth memory access (e.g., in ML workloads) dramatically
     increases power draw.
   - SSDs vs HDDs: SSDs are more energy efficient in active use but may draw more baseline power
     when idle. HDDs consume mechanical energy for spinning platters and seek operations.
   - Storage Controllers: SSD controllers and RAID cards can introduce significant overhead for
     encryption, compression, or error correction.

3. Network and I/O Devices:
   - Network interfaces (Ethernet, WiFi, 5G) consume energy both while transmitting and while
     listening or idling.
   - Energy cost is proportional to data volume, but also to interface state (active vs idle
     vs sleep).
   - Polling interfaces and frequent interrupts are energy intensive compared to event-driven
     or DMA-based designs.

4. Displays and Peripherals:
   - In mobile devices, the display is often the single largest energy consumer.
   - Backlight brightness, refresh rate, and resolution directly affect power draw. OLED screens
     allow per-pixel control, making dark UI themes potentially more energy efficient.

5. Cooling and Power Delivery:
   - In data centers, non-computational energy use includes HVAC, fans, power supply units, and
     battery backups.
   - Power Usage Effectiveness (PUE) is a key metric: a PUE of 1.5 means only two-thirds of the
     energy powers computation; the rest goes to overhead.
   - Poor power delivery efficiency (voltage regulators, converters) increases waste heat and
     thermal load.

### From Energy Use to System Design

Energy-aware system design spans multiple layers:

1. Hardware-Level Strategies:
   - Low-Power Cores: ARM’s big.LITTLE architecture uses high-performance cores
     for bursts and energy-efficient cores for background tasks.
   - Near-Threshold Computing: Reduces voltage to just above transistor switching
     threshold--dramatically lowers energy per operation but increases latency
     and susceptibility to noise.
   - Hardware Acceleration: Specialised accelerators (e.g., for video decoding or
     ML inference) perform fixed operations with lower energy per bit than
     general-purpose CPUs.

2. Software-Level Strategies:
   - Algorithmic Efficiency: Reducing algorithmic complexity (e.g., $O(n^2)$ to
     $$O(n · \log n)$$) saves cycles and thus energy.
   - Energy-Proportional Computing: Programs that scale energy use with workload
     intensity avoid high baseline costs.
   - Idle Resource Management: Systems like Android aggressively suspend background
     services, while desktop OSes may rely on power-aware scheduling.

3. System-Level Coordination:
   - Dynamic Power Management (DPM): OS schedules devices into sleep states based on
     usage patterns.
   - Workload Placement: Cloud orchestrators schedule compute jobs to machines or
     regions with spare thermal headroom or lower electricity prices.
   - Data Locality: Avoiding data movement is often cheaper than moving computation
     to data. Memory access typically consumes 1-2 orders of magnitude more energy
     than an arithmetic instruction.

4. User-Level Practices:
   - Adaptive UIs: Mobile apps reduce animation or refresh rate when on low battery.
   - Energy Feedback Loops: Battery analytics and OS-level power monitors help users
     identify energy-intensive applications or behaviors.


### Trade-offs and Externalities

Optimising for energy is not free:

- Performance vs. Power: Energy-saving measures often reduce raw speed. Lower
  voltage or slower clocks improve energy per operation but increase task duration.

- Complexity vs. Simplicity: Energy-aware systems are more complex--managing sleep
  states, reinitialisation latency, or predicting workload characteristics.

- Centralisation vs. Distribution: Centralised computation (e.g., cloud) may be
  more energy efficient at scale due to shared infrastructure, but it introduces
  network energy costs.

- Environmental Cost: Energy efficiency improves carbon footprint, but materials
  used in low-power hardware (rare earths, lithium) have their own ecological cost.
  Lifecycle energy--manufacture, use, disposal--must be considered in sustainability
  metrics.



### Energy as a First-Class Constraint

Energy is no longer a side effect of computation--it is a design constraint, optimisation
goal, and operational risk. In embedded systems, exhausting energy means failure. In mobile
apps, it means frustrated users. In data centers, it means rising costs and environmental
scrutiny. Designing with energy in mind means treating power as an architectural layer:
measured, budgeted, and optimised--just like time or memory.

