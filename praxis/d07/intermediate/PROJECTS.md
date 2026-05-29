## Projects

### Advanced Programming: Concurrency, Types, and Distributed Systems

These projects require significant independent thinking. The additions under
`ch07/addition/` provide infrastructure and starting points. You are expected
to understand what you are building, not just run existing code.

For concurrency projects: write down, before coding, what can go wrong. Name
the failure mode. Then build. Then try to trigger the failure you predicted.

For type system projects: write down, before coding, what error the type system
will prevent. Then implement. Then verify that the system catches the error
you intended, and does not reject programs it should accept.


#### Project 1: Raft Fault Injection

*Objective:* Run the Raft implementation, inject failures, and document the recovery behavior.

Use `ch07/addition/raft/` — `raft_server.py`, `raft_database.py`, `main.py`.

*Stage 1 — Basic operation:*
Run 3 nodes. Perform a sequence of writes. Verify that all nodes agree on the final state.

*Stage 2 — Leader failure:*
Kill the current leader mid-write. Observe: does a new leader get elected? Does the
write commit, get lost, or get duplicated? Why?

*Stage 3 — Network partition:*
Prevent nodes 1 and 2 from communicating with node 3. Perform writes to the majority
partition. Then restore communication. What happens to the writes that node 3 may have
accepted independently?

*Stage 4 — Split brain attempt:*
Try to construct a scenario where two nodes simultaneously believe they are leaders.
Is this possible under Raft? What prevents it?

Document each experiment: what you expected, what happened, and why. Reference the
Raft paper or `raft/PROJECTS.md` for the theoretical guarantees.

*Questions:*
- Which Raft guarantee — safety or liveness — is violated during a partition?
- What is the minimum number of nodes needed to tolerate one failure?
- Why does Raft use randomised timeouts for leader election?


#### Project 2: Algebraic Effects Composition

*Objective:* Compose multiple algebraic effects into a single interpreter and demonstrate
that swapping handlers changes semantics without changing code.

Use `ch07/addition/effect/` for the individual effect implementations.

*Stage 1 — Single effect:*
Run and understand the `counter` effect. Write a program that uses it. Change the
handler from "increment by 1" to "increment by 2". Show that the program works
with either handler.

*Stage 2 — Composed effects:*
Write a program that uses `state`, `log`, and `exception` effects simultaneously.
The program reads state, logs the value, and throws an exception if the value exceeds
a threshold.

*Stage 3 — Handler swap:*
Implement two handlers for the `log` effect: one that prints to stdout, one that
silently discards. Swap them. Verify that the program's observable behaviour
(outside of logging) is identical.

*Stage 4 — Effect isolation:*
Write a test for your multi-effect program that uses the discard handler for `log`
and a mock handler for `exception` (one that records exceptions rather than stopping
execution). Show that this enables deterministic testing of programs with side effects.

*Questions:*
- What is the difference between an effect and a monad? Where do they overlap?
- What would it look like to handle the `exception` effect as a list of results
  rather than as a stop signal?
- Which of the ten effects in `ch07/addition/effect/` do you find most surprising?
  Why?


#### Project 3: Session Types Protocol Verifier

*Objective:* Design a communication protocol, express it as session types,
implement it, and show that the type checker catches a protocol violation.

Use `ch07/addition/sessions/session_vm.py`, `demo.py`, and `THEORY.md`.

*Stage 1 — Three-party protocol design:*
Design a simple protocol for a client, a server, and an auditor. Example:
the client sends a request, the server processes it and sends the result to both
the client and the auditor, the auditor logs it and sends an acknowledgment.

*Stage 2 — Session type specification:*
Write the session type for each participant's channel. Use the notation from `THEORY.md`.
Verify by hand that the three types are "dual" (compatible with each other).

*Stage 3 — Implementation:*
Implement the protocol using `session_vm.py`. All three parties execute concurrently.
Verify that the protocol runs to completion on valid inputs.

*Stage 4 — Violation detection:*
Modify one participant to violate the protocol (send a message out of order,
or send the wrong type). Show that the session type checker catches this
before or at runtime.

*Questions:*
- What is duality in session types? Why must communicating session types be dual?
- What class of errors do session types catch that regular type systems do not?
- What would you have to add to the session type system to express timeouts?


#### Project 4: Borrow Checker Extension

*Objective:* Extend the borrow checker in `ch07/addition/borrow/` with lifetime analysis.

Read `checker.c`, `checker.h`, `diagram.c`, `diagram.h`, `main.c`, and `README.md`.

The existing checker enforces:
- A value has exactly one owner.
- A value may be borrowed (read) multiple times simultaneously.
- A mutable borrow is exclusive.

*Stage 1 — Understand:*
Write five programs that the current checker accepts and five that it rejects.
Explain each decision.

*Stage 2 — Find the gap:*
Construct a use-after-free that the current checker does not catch: a value is
freed (ownership transferred), and a previously taken reference to it is used after
the transfer. Show that the checker incorrectly accepts this program.

*Stage 3 — Lifetime analysis:*
Add a lifetime to each value: a range of operations during which a reference to it
may be used. A reference is invalid after the owner is freed. Modify the checker
to track lifetimes and reject use-after-free programs.

*Questions:*
- Why does Rust's borrow checker use lifetimes? What does this prevent that ownership
  alone does not?
- What is the relationship between this borrow checker and the affine types from ch05?


#### Project 5: RTOS Multi-Task Application

*Objective:* Build a three-task application using the RTOS from `ch07/addition/rtosapi/`.

The three tasks must:
- *Sensor task:* Generate data at a fixed rate (use a timer or simulate it).
- *Processor task:* Receive data from the sensor, perform a non-trivial computation
  (e.g. a moving average or peak detection), and pass results onward.
- *Display task:* Receive processed results and output them (print to console or,
  if on hardware, to the display).

Tasks communicate via queues. No global variables shared between tasks.

*Demonstration of preemption:*
Make the processor task compute-heavy for a short period. Show that the sensor task
and display task continue running during this period (they are not blocked by the
processor's work).

*Extension:* Add a watchdog: if the processor task does not complete within a deadline,
the watchdog task resets it to a known state.

*Questions:*
- What happens if the sensor task produces data faster than the processor task consumes it?
  How does your queue handle backpressure?
- What is priority inversion? Is it possible in your implementation?
- How does this RTOS compare to what you saw in `ch04/addition/tdos`?


#### Project 6: Signal Processing Pipeline

*Objective:* Apply the DSP toolkit from `ch07/addition/signals/` to a signal processing problem.

Choose a problem from `signals/projects/`, or define your own.

Suggested problems:
- *Noise removal:* Generate a clean sine wave. Add Gaussian noise. Apply a low-pass
  filter to recover the original signal. Measure the SNR before and after.
- *Frequency identification:* Generate a signal composed of three frequencies.
  Apply FFT to identify those frequencies. Show the frequency spectrum.
- *Sampling artefacts:* Generate a signal above the Nyquist frequency for a given
  sample rate. Show aliasing in the reconstructed signal. Then show that
  downsampling with a proper anti-aliasing filter prevents it.

For each: show the input signal, the processing steps, and the output signal as plots.

*Questions:*
- What is the Nyquist theorem, and why does it set a fundamental limit?
- What is the difference between a FIR and an IIR filter? What are the tradeoffs?
- Where in the rest of the book does signal processing connect? (Think: embedded
  sensors in ch04, optimisation in ch03.)
