## Exercises

### Embedded Systems and the Physical Layer

#### What Makes Embedded Different

1. *What is an embedded system? Give three examples that are not computers in the traditional sense.*
   - What do these systems have in common that distinguishes them from a laptop or server?

2. *What does it mean for a system to be "resource-constrained"?*
   - List the resources that are typically limited in an embedded device. How do these constraints
     affect the way you write programs?

3. *Why does a microcontroller often run without an operating system?*
   - What does an OS provide that an embedded program must then handle itself?

4. *What is the difference between a microcontroller and a microprocessor?*
   - Where are the peripherals in each? What is integrated on-chip?

5. *What is a GPIO pin?*
   - What does "general purpose" mean here? What can you connect to one?

6. *What is the difference between digital and analog signals?*
   - How does an ADC (analog-to-digital converter) allow a microcontroller to read an analog sensor?

7. *What is a PWM signal, and why is it used to control brightness or motor speed?*
   - What determines the brightness of an LED driven by a PWM signal?


#### Timing and Interrupts

1. *What is polling? Describe a program that uses polling to check a button.*
   - What are the disadvantages of polling? What resources does it waste?

2. *What is an interrupt?*
   - How does an interrupt differ from polling? What happens inside the CPU when an interrupt fires?

3. *What is an interrupt service routine (ISR)?*
   - What constraints apply to code inside an ISR that do not apply to regular code?

4. *What is debouncing, and why do physical buttons require it?*
   - What happens at the electrical level when you press a button that causes spurious readings?

5. *What is a timer peripheral?*
   - How does a hardware timer allow a microcontroller to do something at precise intervals without
     using a busy loop?

6. *What is the difference between a synchronous and asynchronous communication protocol?*
   - Give one example of each from the Pico's set of peripherals.

7. *What is I2C? What is SPI?*
   - How do they differ in the number of wires they require and the speed they can achieve?


#### State Machines

1. *What is a finite state machine?*
   - Define state, transition, and event. Give an example of each for a vending machine.

2. *Why are state machines a natural model for embedded software?*
   - Think about what embedded programs respond to. How does this differ from batch processing programs?

3. *What is the difference between a Moore machine and a Mealy machine?*
   - In which does the output depend only on the current state? In which does it also depend on
     the current input?

4. *Draw a state machine for a traffic light.*
   - What are the states? What are the transitions? What triggers each transition?

5. *What is the risk of "implicit state" in an embedded program?*
   - Describe a program whose state is spread across multiple boolean flags rather than a single
     explicit state variable. What problems does this cause?

6. *What does it mean for a state machine to be "deterministic"?*
   - Why is determinism especially important in safety-critical embedded systems?


#### Memory and Power

1. *Why does RAM scarcity matter so much more in embedded systems than in desktop software?*
   - What happens on a Pico if you allocate more memory than is available? Compare this to what
     happens on a desktop machine.

2. *What is flash memory? How does it differ from RAM?*
   - What can you store in flash? What are the write constraints?

3. *What is power consumption, and why does it matter in battery-powered embedded devices?*
   - What is "sleep mode"? How can a microcontroller save power when it has nothing to do?

4. *What is a watchdog timer?*
   - What problem does it solve? What happens if the watchdog is not "fed"?

5. *Why are floating-point operations expensive on microcontrollers without an FPU?*
   - What is the alternative representation that is commonly used instead?
