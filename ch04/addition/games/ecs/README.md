
## The Evolution of Game Programming


#### Early Era: 1970s–1980s

Games were written in assembly or BASIC for limited hardware such as the Atari,
Commodore, or Apple II. Code was small and monolithic, tightly constrained by
memory and processing power. Performance considerations dominated every design
choice. Programs were often difficult to maintain or extend, but they were highly
tuned to the hardware.


#### Object-Oriented Design: 1990s

With the rise of C++ and other object-oriented languages, games became more modular.
- Objects represented game entities with properties and methods.
- Engines like Doom and Quake relied heavily on inheritance and encapsulation.

While OOP improved code organisation and reusability, it introduced deep hierarchies
and memory layouts that were inefficient for modern CPUs. Large numbers of game objects
could create bottlenecks due to cache misses.


#### Component-Based Design: 2000s

To overcome the limitations of deep inheritance, developers introduced component-based
design:
- Game entities became containers for modular components such as position, physics, or rendering.
- Behaviour was often decoupled from data, making it easier to reuse and extend functionality.

This design increased flexibility but still had performance constraints, especially
when scaling to thousands of entities.


#### Data-Oriented Design and ECS: 2010s–Present

Modern game engines increasingly adopt Entity-Component-System (ECS) architectures.
- Entities are identifiers.
- Components store data.
- Systems contain the logic that operates on components.

This separation allows:
- Cache-efficient processing by iterating over homogeneous data.
- Parallel execution, since systems can operate independently.
- Scalability, handling thousands of entities in simulations, MMOs, and complex games.

ECS represents a shift from behaviour-driven to data-oriented design,
optimising both CPU and memory usage. It has become a standard in high-performance
game development.


#### Compiler Optimisation in Game Development

Games remain performance-sensitive, and compiler optimisations are essential.
Key strategies include:
- Inlining and loop unrolling to reduce instruction overhead.
- Vectorisation and SIMD operations for math-heavy computations.
- Memory layout optimisation to improve cache performance.
- Profile-guided optimisation to focus on hot paths in actual gameplay.

Even with ECS and modern design patterns, thoughtful coding is required. Efficient
data organisation and algorithm choices work together with compiler optimisation
to deliver high-performance games.


#### Small Games on Microcontrollers

A parallel branch of game development has emerged on microcontrollers like the Raspberry Pi Pico.
- Hardware is extremely limited in CPU speed, memory, and display capabilities.
- Games are usually small, self-contained programs, often written in C or MicroPython.
- Developers must carefully manage memory, timing, and I/O, and simplify game logic to fit constraints.
- Despite limitations, microcontroller games encourage efficient, elegant code, sometimes resembling
  early home computer games in style and performance demands.

Microcontroller game development provides a hands-on perspective on optimisation,
resource management, and fundamental programming principles, making it an excellent
learning environment for understanding game architecture at its most elemental level.
This is the main purpose in this context.
