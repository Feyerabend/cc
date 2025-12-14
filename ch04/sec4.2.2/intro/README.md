
## An Introduction to Embedded Systems and Microelectronics

While both *microprocessors* and *microcontrollers* integrate a CPU on a chip,
they differ in scope and application. A microprocessor is usually intended as
the core of a general-purpose computer, relying on external components such as
RAM, ROM, and peripheral controllers. By contrast, a microcontroller integrates
these components on-chip, making it self-contained and ideal for embedded systems
where cost, size, and power efficiency are crucial. In short, microprocessors
excel at flexibility and computational power, whereas microcontrollers excel
at simplicity and dedicated control.

The development of microcontrollers can be traced back to the early 1970s, when
companies such as Texas Instruments and Intel began integrating CPU cores, memory,
and basic I/O functions onto a single chip. Intel's 8048 and later the 8051 family
became industry standards in the 1980s, setting the template for low-cost, versatile
embedded control. During the 1990s, microcontrollers proliferated in consumer
electronics, automobiles, and industrial equipment, largely due to falling costs of
semiconductor manufacturing and rising demand for programmable control. The 2000s
saw the rise of 16-bit and 32-bit microcontrollers, bringing greater performance,
larger address spaces, and improved peripherals, making them suitable for increasingly
complex embedded applications. Today, 32-bit architectures such as ARM Cortex-M
dominate, combining high efficiency with advanced features like low-power modes,
real-time performance, and secure communication. These advances have blurred the
line between microcontrollers and microprocessors: modern microcontrollers are often
powerful enough to run lightweight operating systems, support connectivity stacks,
and handle multimedia tasks, making them central to the Internet of Things (IoT)
and pervasive computing.


### Hardware Observations

First proposed by Gordon [Moore](./MOORE.md) in 1965, Moore's Law is the observation
that the number of transistors on a microchip doubles approximately every two years.
This trend drove decades of exponential growth in computing power and miniaturisation.
While the law has slowed in recent years due to physical limitations, its principles
continue to influence how we design and build technology.

A complementary concept by Robert Dennard et al., Dennard Scaling, observed that as
transistors shrank, their power consumption also decreased, allowing for more powerful
chips without increasing total heat or power usage. This trend broke down around 2005,
leading to a shift in the industry toward multicore processors and a focus on energy
efficiency.


### Embedded Systems with the Raspberry Pi Pico

Microcontrollers like the Pico are used in a huge range of
[applications](./USE.md), including:

* Sensor Interfacing: Reading data from the environment.  
* Actuator Control: Controlling motors, lights, and other outputs.  
* Real-Time Control: Managing tasks that require precise timing.  
* Human Interfaces: Responding to user input from buttons or touch sensors.  
* IoT and Networking: Connecting devices to the internet.

To perform these tasks, microcontrollers rely on various
[sensors](./SENSORS.md).

* Temperature & Humidity: For weather stations and smart home devices.  
* Light & Colour: For automatic brightness and colour recognition.  
* Motion & Position: For robotics and navigation.  
* Proximity & Distance: For object detection and collision avoidance.  
* Pressure & Gas: For air quality and altitude measurement.

Finally, there is a [list](./LIST.md) of real-world projects that
can be built using the Raspberry Pi Pico, from simple projects for
beginners to more advanced applications. Examples include:

* Gaming and Emulation: Building a retro game console.  
* Robotics: Creating a self-balancing robot.  
* IoT: Building a smart thermostat or an air quality monitor.  
* Audio and Music: Creating a simple synthesiser or a MIDI controller.  
* Wearables: Designing a fitness tracker.


