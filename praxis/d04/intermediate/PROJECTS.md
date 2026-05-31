## Projects

### Embedded Systems on the Raspberry Pi Pico

These projects use the Raspberry Pi Pico with the Pimoroni Display Pack 2.0.
All code runs in MicroPython unless otherwise stated. The additions under
`ch04/addition/` contain reference implementations — study them, but build
your own versions for the main project work.

Before writing any code, write down:
1. What states your program can be in.
2. What events cause transitions between those states.
3. What output is produced in each state.

This state machine analysis is your design document.


#### Project 1: Button Sequence Lock (CEP)

*Objective:* Use the four buttons on the Display Pack as event sources. Recognise
a specific sequence of button presses within a time window. Display feedback on-screen.

See `ch04/addition/cep/` for Complex Event Processing background and examples.

Steps:
- Implement event detection for each button using polling or interrupts.
- Record a time-stamped event log.
- Define a "correct sequence" (e.g. A-B-A-Y within 5 seconds).
- When the sequence is matched: show "Unlocked" in green with the RGB LED green.
- When an incorrect sequence is entered: show "Denied" in red.
- After 10 seconds of inactivity, reset to the locked state.

*Extension:* Allow the user to *set* the sequence using a programming mode triggered
by holding two buttons simultaneously.

*Questions:*
- How do you handle a partial match that has started but whose window has expired?
- What state machine underlies this program? Draw it.
- How does your debouncing strategy affect the reliability of sequence detection?


#### Project 2: ECS Game on the Display Pack

*Objective:* Build a small interactive game using the Entity-Component-System pattern.

See `ch04/addition/games/ecs/` for the ECS framework.

Choose a game with clear entities: Snake, Pong, or a simple obstacle-dodge game.
The requirement is that *every game object must be an entity*, and behaviour is
attached through components, not through class inheritance or special-case code.

Minimum components to implement: `Position`, `Velocity`, `Renderable`, `Controllable`.

Steps:
- Define your entities and components.
- Write systems that operate on components: a movement system, a rendering system,
  a collision system, an input system.
- Implement a game loop that calls each system in order.
- Display the game on the Display Pack screen.

*Questions:*
- What is the advantage of ECS over a traditional object-oriented approach for games?
- What happens when you add a new type of game object? How much code changes?
- What makes a system in ECS different from a method on a class?


#### Project 3: 2FA Attack and Defend

*Objective:* Implement a two-factor authentication protocol on the Pico, then try
to break it.

See `ch04/addition/2fa/` for the existing implementation skeleton (pico_a, pico_b, desktop).

This is a group project with two roles:

*Defending team:*
- Complete the Pico server (`pico_b`) that accepts only authenticated commands.
- A command is valid only if it carries a valid TOTP-style token *and* a correct
  password sent over the secure channel.
- Display current authentication status on screen.

*Attacking team:*
- Given only the protocol specification (not the source code), attempt to:
  1. Replay a captured valid token.
  2. Brute-force the password space within the token's validity window.
  3. Inject a malformed command that bypasses validation.

*Debrief:* Both teams present their findings. Defending team explains what was
protected. Attacking team explains what succeeded and what did not. Propose one
improvement to the protocol that would close any gap discovered.

*Questions:*
- What makes a token "time-based"? What assumption does this rely on?
- What would happen if the two Picos had clocks that drifted apart?
- Which attacks succeeded? What does that reveal about the protocol design?


#### Project 4: TDOS New Subsystem

*Objective:* Add a new subsystem to the TDOS tiny operating system.

See `ch04/addition/tdos/`: `tdos_kernel.py`, `tdos_protocol.py`,
`tdos_applications.py`. Read `TDOS.md` for the architecture.

Choose one:

*Option A — Scheduler:*
- Implement round-robin scheduling for TDOS tasks.
- Tasks must yield explicitly (cooperative multitasking).
- Display a task status list on the Display Pack screen.
- Demonstrate two tasks running "simultaneously" (one blinks the LED,
  one monitors a sensor).

*Option B — Filesystem layer:*
- Implement a simple key-value store on the Pico's flash memory.
- Support `read(key)`, `write(key, value)`, `delete(key)`, `list()`.
- Persist the store across reboots.
- Add a `store` and `fetch` command to the TDOS shell.

*Questions:*
- What invariants does TDOS's existing protocol depend on? Did your addition preserve them?
- What happens if the Pico loses power mid-write to flash? How would you make the
  filesystem crash-safe?


#### Project 5: Blockchain Voting on Pico

*Objective:* Extend the Pico blockchain to support a simple voting protocol.

See `ch04/addition/block/micropython/` and `block/PROJECTS.md` (project 1: Voting System).

Steps:
- Modify the `Block` class to store votes: a voter ID (anonymised), a choice, and a timestamp.
- Implement double-vote prevention using the hash chain.
- Add a tally function that traverses the chain and counts votes.
- Display the current tally on the Display Pack screen.
- Test tampering: modify a past vote block and show that the chain becomes invalid.

*Group extension:* Two Pico devices. One acts as a "polling station" that accepts votes.
The other acts as a "counting station" that receives the chain and tallies it. The attacking
group tries to inject a vote or modify a counted vote.

*Questions:*
- How does the hash chain prevent vote tampering? What exactly breaks?
- What is the difference between *detecting* tampering and *preventing* it?
- What real-world problem does blockchain voting solve — and what problems does it *not* solve?


#### Project 6: 6502 Retrocomputer Extension

*Objective:* Write a small program in 6502 assembly, run it on the Pico 6502 emulator,
and extend the emulator with one new instruction.

See `ch04/addition/pico6502rc/`: `fake6502/`, `compiler/`, `computer/`.

Steps:
- Study the 6502 instruction set (just the arithmetic and branching subset).
- Write a short 6502 assembly program: a loop that computes the sum of 1..10,
  or a Fibonacci sequence up to 100.
- Assemble and run it on the `fake6502` emulator inside the Pico.
- Choose one instruction not currently implemented. Add it to `fake6502`.
- Write a test program that uses your new instruction.

*Questions:*
- What is the relationship between the 6502 emulator and the virtual machines in ch02?
- What does emulating an old CPU on a microcontroller demonstrate about portability?
- What constraints of the 6502 architecture reflect the hardware limitations of 1975?
