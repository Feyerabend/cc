
## When Computing Becomes a Laboratory Again

What is striking today is not that we suddenly have more powerful machines, but that the cost of
experimentation has collapsed at two levels at once. Hardware has become cheap and abundant, and
conceptual labor has become lighter because we can externalise parts of our thinking into tools
like LLMs. That combination changes what it means to build systems. It moves computing away from
large, centralised projects and back toward something closer to laboratory science, where ideas
can be tested quickly, broken cheaply, and refined through direct contact with reality.

The Raspberry Pi Pico, and such hardware like it, is not interesting because it is powerful.
It is interesting because it is small, simple, and plentiful. When you have one board, you build a
device. When you have ten or twenty, you build a system. A distributed computer stops being a
metaphor and becomes a physical object on your desk. Wires replace abstract networks, clock
drift replaces simulated timing errors, and failure becomes something you can touch. Nodes can
be unplugged, power-starved, or flooded with messages, and the system's behaviour under stress
is no longer theoretical. It is observable.

In earlier decades, this kind of experimentation was expensive and slow. You needed custom boards,
deep hardware expertise, and a team large enough to maintain the infrastructure. Now the
infrastructure is almost trivial. The physical substrate is solved. What remains is architecture
and code. That is a profound shift, because it means the bottleneck is no longer material capability
but conceptual clarity. You are constrained not by what you can build, but by what you can imagine.

What emerges is a new style of computing research and development. Instead of designing large
systems top-down, you grow them bottom-up. One Pico becomes a node, two become a link, five become
a network, and ten become a distributed computer. The LLM helps you write the glue code, the message
handlers, the timing logic, and the diagnostics, so your energy is spent on structure rather
than syntax. The code becomes a living document of your architectural thinking.

This returns computer science to a more physical and experimental discipline. Distributed systems
are no longer something that only exist in data centres or in academic papers. They can exist on
a tabletop. Fault tolerance is no longer a property of diagrams but of wires, clocks, and power rails.
Consensus is no longer an algorithm alone, but a phenomenon that emerges from real delays, real
failures, and real constraints.

In that sense, the Pico is not a weak computer. It is a microscope. It lets you isolate the essential
mechanics of computation and coordination. The LLM, in turn, becomes a kind of intellectual amplifier.
It accelerates design, challenges assumptions, and helps you explore variations that would otherwise
be too tedious to try. Together, they make it possible to treat computing systems the way physicists
treat apparatus: something to assemble, probe, and modify repeatedly until the underlying structure
becomes visible.

This is why building a distributed computer from small microcontrollers today is not merely a technical
exercise. It is a methodological shift. It suggests that the future of systems research may look less
like industrial engineering and more like experimental science. Cheap hardware gives us the physical
freedom to build. LLMs give us the cognitive freedom to explore. Between them, they make complex
systems approachable, playful, and deeply empirical again.


### Suggested Implementation: Build a Distributed OS

This is an untested *idea*, which you can choose to work on.
These are the given parts:

__1. protocol.py - Core protocol library with:__

- Message serialization/deserialization
- Service registry with health tracking
- Circuit breaker pattern
- Full error handling


__2. sensor_node.py - Sensor nodes supporting:__

- Simulated sensors (temp, humidity, light)
- Real ADC sensors
- DHT22 temperature/humidity sensors
- Digital inputs
- Automatic service announcement and heartbeats


__3. tinyos.py - Kernel node providing:__

- Service discovery and registry
- Unified API for accessing sensors
- Display abstraction (Pimoroni, SSD1306, or console)
- Fault tolerance with retries and circuit breakers


__4. Applications - Four complete example apps:__

- Weather station (multi-sensor monitoring)
- Data logger (persistent logging to file)
- System monitor (health and diagnostics)
- Alert system (threshold monitoring)


__5. wifi_ap.py - WiFi access point setup:__

- Create standalone AP
- Run AP with kernel or sensor
- Client monitoring


