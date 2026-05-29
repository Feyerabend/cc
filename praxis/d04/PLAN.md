## Learning Blueprint: Hardware as a Mirror for Software Concepts

This chapter changes the register of the book. The Raspberry Pi Pico is a
physical object. Programmes run on real hardware and produce visible, audible,
or measurable output in the world. This concreteness is pedagogically powerful:
abstractions that floated free in earlier chapters — state machines, memory
constraints, event-driven execution — now have direct physical referents.

The approach is empirical from the start. Students observe before they theorise.
A blinking LED is not a toy; it is a timing experiment with a clear, verifiable
outcome. A button debounce is not a detail; it is a lesson in the gap between
an idealised model and physical reality.

LLMs may be used as tools throughout this chapter. Their role is to assist with
unfamiliar APIs, explain error messages, and generate alternative implementations
for comparison. Students should verify every LLM claim by running the code.
On embedded hardware, claims about timing, memory, and peripheral behaviour
that are not verified by observation are not trustworthy.


### Pedagogical Principles

__1. The hardware tells the truth__

The Pico does not accept polite fictions. A program that is logically plausible
but physically incorrect will fail visibly. This immediate feedback is a powerful
corrective for over-confident reasoning.

__2. Build first, name later__

Students encounter blinking, state changes, and event detection before those
phenomena are given formal names. This lets the concepts arrive as explanations
of things already observed, not as abstractions to be memorised.

__3. Resource constraints are not obstacles but teachers__

Memory limits, timing windows, and power budgets are the curriculum. A program
that cannot fit in 256 KB of RAM teaches more about representation than a
lecture on the same topic.

__4. Security is a design property, not an add-on__

The 2FA project introduces adversarial thinking early: a system is only secure
against an attacker you have modelled. Students who build the attack understand
the defence far better than those who only build the defence.


### Structure of the Chapter

#### Sequence 1: The Minimal Hardware Loop

*Experience*

Teacher and students together write and run a minimal blink program.
Change the blink rate by modifying a single number. Observe the effect.
Then modify it to respond to a button press.

The first question to surface: *why does the button sometimes seem to press twice?*
Do not explain. Let the students observe and form their own theories.

*Reflection*

Each student writes down one thing they observed that they cannot yet explain.
Share these with the class. Collect them on a board.

LLM-assisted task: "I observed [X] when I pressed the button. Give me three
different explanations for why this might happen. Do not tell me which is correct."

*Conceptualisation*

Introduce debouncing only after the problem has been named by students.
Connect to the electrical model: mechanical contacts bounce; the GPIO pin
samples faster than human perception. A physical phenomenon requires a
physical explanation.

*Extension*

Students modify their debounce threshold and measure its effect. What is the
minimum threshold that works reliably? Does it depend on the specific button?


#### Sequence 2: State Machines on Real Hardware

*Experience*

Students implement a traffic light controller: three LEDs, timed transitions.
They are given only the wiring diagram and the timing requirements. No code scaffold.

*Reflection*

"Draw the state machine you implemented. Is it the same as what you coded?
Did the code match the diagram, or did you discover the diagram only after writing the code?"

LLM-assisted task: "Here is my traffic light code. Describe the state machine
it implements. Do not add, change, or improve it — just describe what it does."

*Conceptualisation*

Introduce state machines formally now: states, transitions, events, outputs.
Moore vs Mealy distinction. The difference between implicit state (flags scattered
across the program) and explicit state (a single state variable).

Ask: which does the student's own code use? Which is easier to reason about?

*Extension*

Add a "pedestrian crossing" button. The state machine must now handle an external
event that can arrive in any state. Students discover that their implicit-state
program is harder to extend than one with an explicit state variable.


#### Sequence 3: Events, Timing, and the Interrupt Model

*Experience*

Students first implement a sensor-reading loop using polling. They measure the
maximum responsiveness they can achieve. Then they implement the same sensor
using an interrupt handler.

The question to surface: *what happens to the main loop while the interrupt runs?*

*Reflection*

"Write down what you think happens to all the variables your main loop uses
when an interrupt fires. Are any of them in an inconsistent state?"

LLM-assisted task: "Explain the term 'race condition' in the context of an
embedded interrupt handler. Give me a concrete example involving a counter
that is modified by both the main loop and an ISR."

*Conceptualisation*

Introduce interrupts, ISRs, and shared state. The concept of atomicity.
Why ISRs must be short. The dangers of calling complex functions (allocation,
I/O, LLM APIs) from within an ISR.

Connect to ch07: this is concurrency without an OS, and the same fundamental
problems apply.

*Extension*

Students find and fix a race condition in a provided program that increments
a counter from both the main loop and a timer interrupt. They must explain the
fix in terms of the underlying hardware behaviour.


#### Sequence 4: Protocols and Trust

*Experience*

Students receive a short specification: a command protocol over serial. They
implement a client that sends commands and a server that executes them.

Then they receive a second task: *without access to the server's source code,
send a command that the server was not designed to receive.*

*Reflection*

"What assumptions did the server make that allowed the unexpected command to work?
Were those assumptions stated anywhere? Should they have been?"

LLM-assisted task: "I built a protocol with these properties. What attacks are
possible? For each, tell me what assumption it exploits."

*Conceptualisation*

Introduce threat modelling: what an attacker can observe, replay, and modify.
The difference between a protocol that assumes a trusted channel and one that
does not. Connect to the 2FA project.

*Extension*

Students add one countermeasure to their protocol. Then the attacking group
tries again. Document what the countermeasure prevented and what it did not.


#### Sequence 5: The Central Project

Students choose one of the projects from
[PROJECTS.md](./intermediate/PROJECTS.md) as the main deliverable for the chapter.

The recommended project for classroom use is the **2FA attack/defend** exercise,
because it naturally divides a class into two groups with complementary goals and
produces visible, discussable results.

For individual study, the **ECS game** or **TDOS subsystem** projects are recommended:
they are self-contained, have clear success criteria, and connect hardware
constraints directly to software design decisions.

*Assessment suggestion:*

After the central project, each student or group gives a short (5-minute) live
demonstration. The demonstrator must:
1. Show the system working on the hardware.
2. Answer one question about a design decision they made.
3. Explain one thing that went wrong and how they found it.

This format rewards genuine understanding and is difficult to fake with LLM assistance.


#### Self-Study Path

A learner working without a classroom follows this order:
1. Blink, then respond to a button. Confirm debouncing is needed and implement it.
2. Build the traffic light state machine. Draw the state machine before writing code.
3. Implement one of the simpler CEP examples from `ch04/addition/cep/`.
4. Choose one project from PROJECTS.md. Complete it, including the reflection questions.
5. Read `advanced/FOUNDATIONS.md`. Connect what you observed to the theoretical concepts.

*Outcome:*

By the end of this chapter the learner will:
- Understand that software abstractions have physical consequences.
- Be able to design and implement a state machine in hardware.
- Have experience with event-driven, interrupt-driven, and protocol-driven programming.
- Have designed or attacked a small security protocol.
- Understand that resource constraints are design parameters, not obstacles.
