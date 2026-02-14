
## Sustainable computing

*Project: Discuss how a new way of building computers could be done. A seed for such a
study would be "microcontrollers" or very simple computers that could handle in principle
easy tasks, like e.g. in an office text processing, and connected things like storage,
printing, layout, conversions between legacy formats etc.*

Re-imagining computing in a distributed, energy-efficient way--especially using microcontroller-like
architectures running simple, specialised programs--could indeed be a promising direction for future,
*sustainable computing*. For certain tasks, like text processing, this approach could provide a
remarkably efficient and lightweight alternative to the current paradigm of general-purpose,
power-hungry computers. And perhaps also more secure, as the simpler the software gets.

Historically, the early Unix philosophy emphasised small, single-purpose tools that
could be combined in flexible ways, and this model could adapt well to a microcontroller-based,
distributed computing environment.

1. *Efficiency and Energy Usage*: Microcontrollers are incredibly efficient in terms of energy usage,
   often drawing only milliwatts of power compared to the hundreds of watts consumed by a modern CPU.
   In a system where each microcontroller handles a specific task (text processing, file handling,
   or network communication, for example), the system could be both highly efficient and easily
   scalable. Since microcontrollers enter low-power modes when idle, they would be especially
   well-suited to applications with sporadic, lightweight demands.

2. *Distributed and Modular Processing*: Just as with Unix pipes, tasks could be split into a sequence
   of discrete operations. For instance, one microcontroller could handle reading from a text file,
   piping the text to another that formats it, which then sends it to yet another that displays it.
   This pipeline would resemble a hardware-implemented version of a Unix shell script, with tasks
   distributed across different microcontrollers. Such a system would be resilient, as individual
   components could be isolated and optimised for their specific roles.

3. *Simplicity and Specialisation*: Since each microcontroller would handle a specific, simple task,
   the software complexity on each node could be minimal. For tasks like document editing, basic
   text transformations, and data manipulation, this model could be very efficient. We wouldn't
   need sophisticated operating systems with memory management, multitasking, or graphical interfaces,
   which would also contribute to reducing energy consumption.

4. *Scalability and Redundancy*: If more power or additional functionality is needed, it's easy to
   add more microcontrollers, each handling a specific new task. This approach also lends itself
   well to redundancy--if a microcontroller fails, another could take over its task without affecting
   the entire system. Unlike a central processor that could represent a single point of failure
    distributed microcontrollers would make the system more resilient and adaptable.

5. *Adaptation to Modern Needs*: While today's office tasks do require powerful systems for heavy
   multitasking and media-rich applications, simpler, text-centric workflows could indeed be handled
   by lightweight systems. If society as a whole re-evaluated computing needs--prioritising function
   over multimedia capabilities in some areas--this model could potentially extend to a broader scope.
   Furthermore, as people grow accustomed to minimalist, function-focused devices, the software
   design could adapt accordingly, leading to new applications that maximise utility while minimising
   resource requirements.

6. *Communication and Data Offloading*: One of the biggest energy costs in modern computing is data
   transfer, particularly with cloud computing. In a distributed microcontroller system, minimal
   amounts of data would need to be transferred at a time, and local processing could minimise the
   need for constant connectivity. For collaborative work, this kind of system could even operate
   on a peer-to-peer model, with microcontroller networks directly communicating without a centralised
   server, further reducing energy costs associated with data centres.

In the context of sustainable computing, this could indeed represent a fascinating alternative,
especially in low-power applications. Not every computing environment requires the power and
versatility of modern CPUs, and focusing on the Unix-like philosophy of small, efficient, and
composable tools might allow us to develop computing solutions that are energy-conscious yet
effective for specific tasks. While it would require a significant shift in how we think about
software and interaction design, it's an idea worth exploring as we look to the future of
sustainable technology.



### Software

In a scenario where computing is re-imagined around distributed microcontroller-based systems and modular,
single-purpose programs, software development would indeed look very different. It would emphasise
efficiency, simplicity, and modularity, drawing from principles of embedded systems programming and
Unix-like philosophies.

#### Software Development Approach and Tooling

1. *Low-Level Languages and Lightweight Libraries*: Development would likely focus on low-level
   languages like C or Rust, which are known for their efficiency and low memory footprint.
   Rust, in particular, could be ideal for building safe and efficient microcontroller-based
   systems due to its focus on memory safety. Instead of large, monolithic libraries, developers
   would use lightweight libraries or even write their own, optimised specifically for minimal
   resource usage.

2. *Modular, Microservice-Oriented Design*: Each piece of software would be a specialised, standalone
   module with well-defined input and output interfaces, much like Unix commands. The idea would be
   to create small, reusable modules that can be combined to perform more complex tasks through "piping"
   data between them. Each module might reside on a separate microcontroller, so communication protocols
   (such as I2C, SPI, or even serial communication) would need to be designed for reliability and efficiency.

3. *Event-Driven or Task-Specific Programming*: Since microcontrollers are generally low-powered and
   might need to enter sleep modes to save energy, software would be event-driven, triggering specific
   modules only when needed. This would avoid unnecessary processing, further reducing power consumption.
   Development would focus on task-specific functions, ensuring each module is "on" only as long as required.

4. *Development Environments and Toolchains*: Startups would need to adopt specialized Integrated Development
   Environments (IDEs) and toolchains suited for microcontroller development, such as the ARM Mbed or
   PlatformIO for embedded systems. Simulation tools that allow developers to model and test interactions
   across microcontroller networks would be essential. Debugging tools would need to be designed for
   distributed systems, ideally supporting remote debugging across several microcontrollers.

5. *Communication Protocols and Interfacing*: To facilitate data "piping" between microcontrollers, lightweight
   and reliable communication protocols would be crucial. Protocols like MQTT, designed for lightweight
   messaging, or custom low-overhead protocols could be adapted for quick data transfer. This might involve
   creating simple message-passing interfaces or shared memory areas to pass data between modules efficiently.

6. *Energy and Resource Profiling*: Since the focus would be on minimizing energy consumption, development
   would include rigorous energy profiling and optimization. Tools for monitoring energy use per microcontroller
   and per task would become essential for continuous optimization, ensuring that energy costs remain low
   across the entire network.


### Suitability for Startups

A startup could carve out a niche in this area, particularly if they focused on applications where
resource efficiency is paramount. For instance, many modern software applications, especially those for personal
productivity or simple data processing, don't require the massive processing power of today's general-purpose
computers.

1. *Focusing on High-Value Niche Applications*: Certain applications, especially those in resource-constrained
   environments, would benefit most. These could include:
   - Energy-sensitive applications: Such as environmental monitoring, data logging, and distributed sensor
     networks, where microcontrollers could operate efficiently in remote locations.
   - Personal productivity tools: Simple text processing, note-taking, and basic data manipulation applications
     could run on this system.
   - Educational tools: Lightweight, modular computing systems would be excellent for teaching programming
     and systems design, helping students learn about distributed computing without high infrastructure costs.
   - Lightweight IOT Systems: Applications where users want a low-energy alternative to traditional computers,
     possibly in remote offices or minimalistic digital workspaces.

2. *Start with Open Source and Leverage Existing Microcontroller Ecosystems*: Leveraging open-source software
   and community-driven projects could help startups get a head start. Libraries, frameworks, and even hardware
   interfaces from the embedded systems community could provide a foundation, minimising upfront costs.
   For instance, the Raspberry Pi Pico and ESP32 microcontrollers have large ecosystems and community support,
   which would provide resources and reduce development time.

3. *Partner with Energy-Conscious Markets*: Industries like environmental tech, remote education, low-cost
   healthcare, or energy-efficient office equipment could be early adopters, creating specific tools with
   minimal energy footprints. Startups could partner with these sectors to deliver products designed around
   efficiency and distributed functionality.

4. *Hardware Innovation and Optimisation*: To create highly energy-efficient modules, the startup might also
   invest in custom microcontroller boards optimised for specific applications. For instance, they might
   design boards with enhanced communication interfaces or add low-energy memory solutions to store data
   without power.


#### Starting Point for Development

1. *Prototype a Minimalist Platform*: Start by designing a simple platform that emulates a Unix-like environment,
   where basic utilities (for file handling, text processing, etc.) are distributed across multiple microcontrollers.
   This could serve as a minimal "OS" prototype, showcasing how distributed microcontrollers can work together.

2. *Create Basic Productivity Tools*: Build text-based tools that handle tasks like note-taking, data entry, and
   processing. These applications would be low-demand but essential in demonstrating the viability of the platform.

3. *Focus on Energy Profiling from the Start*: Develop and test these tools while monitoring energy consumption
   closely. By doing this early, the startup can validate whether the system meets energy efficiency goals and
   improve any high-demand areas.

4. *Develop Simulation and Testing Environments*: Building robust testing tools, especially for debugging interactions
   across microcontrollers, would be crucial. The startup might create simulation environments to model task
   distribution, data flow, and system resilience under various conditions, providing a proof of concept before scaling up.


#### Long-Term Vision

If successful, such a startup could establish a new model for sustainable computing,
where minimal hardware is used for maximum productivity, specifically in environments
that don't need multimedia processing or heavy computing. This model could encourage a
shift back to efficient, purpose-built systems, helping reduce computing energy costs
industry-wide and influencing software design to prioritise simplicity and modularity.

