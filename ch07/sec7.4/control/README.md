
### Control Flow & Dispatch

| Mechanism | Description  | Use Cases | Related Pattern(s) |
|-----------|--------------|-----------|--------------------|
| [Dispatch](./dispatch/) | Choose code to run based on input/state  | Message dispatch, interpreters, drivers | Command, Strategy |
| [Jump Table](./jump/) | Array of code addresses for fast branching | Opcode dispatch, switch-case replacement | Direct dispatch idiom |
| [Trampoline](./trampoline/) | Loop-based control flow instead of recursion | Tail-call optimisation, interpreter loops | Interpreter pattern |
| [State Machine](./state/) | Explicit modelling of transitions and states | Embedded control, protocols, parsing | State pattern |
| [Continuation](./continue) |  Representation of "what to do next" in execution | Functional languages, backtracking | CPS (Continuation-passing style) |

Dispatch sits at the heart of program flow control mechanisms. At its most fundamental
level, dispatch is about determining which code to execute next based on some criteria.
This core concept manifests in several related techniques that programmers use to control
execution flow.

Jump tables represent one of the most efficient implementations of dispatch. When a program
needs to select from multiple possible execution paths based on a value, a jump table provides
a direct mapping from that value to the corresponding code. Unlike sequential if-else chains or
switch statements that might require multiple comparisons, jump tables offer constant-time
performance regardless of how many options exist. This makes them particularly valuable in
performance-critical code paths like virtual machine instruction processing.

State machines connect naturally to these dispatch mechanisms. A state machine formally defines
a set of states, transitions between those states, and the rules that govern those transitions.
The implementation of a state machine typically relies on dispatch to determine the next state
based on the current state and input. Jump tables excel at implementing state transitions
efficiently, mapping from a state identifier to the code that handles that state. This
relationship makes state machines a higher-level abstraction built on the foundation
of dispatch.

Trampolines extend the dispatch concept by introducing a layer of indirection. Rather than
jumping directly to the target function, execution "bounces" through an intermediate
function--the trampoline. This extra step enables powerful capabilities like dynamically
changing behaviour at runtime, managing different calling conventions between language boundaries,
or implementing tail-call optimisation in environments that don't natively support it. Trampolines
trade a small performance cost for significant flexibility in how control flows through a program.

Continuations intersect with trampolines and represent a powerful control flow abstraction.
A continuation captures the "rest of the program" at a particular point in execution, essentially
reifying the future computation into a first-class object that can be stored, passed around,
and invoked. Trampolines often implement continuations by packaging the next step of execution
into a data structure that the trampoline can later invoke. This relationship becomes particularly
important in implementing cooperative multitasking, generators, or coroutines, where execution
needs to pause and resume. When a program uses continuations extensively, the trampoline pattern
helps manage them efficiently without overflowing the stack.

The interpreter pattern connects closely with all these mechanisms. In its broadest sense, an
interpreter represents code that reads and executes other code. Interpreters rely heavily on
dispatch to determine what operation to perform based on the current instruction or language
construct. Many interpreters use jump tables to efficiently map opcodes to their implementations,
while trampolines often handle the transitions between interpreted code and native code. Some
interpreters even represent their execution state as an explicit state machine, particularly for
handling complex parsing logic. Additionally, interpreters that support advanced control flow
features often use continuations internally to implement features like generators, exceptions,
or coroutines.

These concepts overlap significantly in real-world systems. In a typical language runtime, you
might find all of them working together: a main interpreter loop uses a state machine pattern
with jump table dispatch based on instruction opcodes, while trampolines manage calls and
continuations handle suspendable computations. A parser in the interpreter might use a state
machine to track its progress through the syntax, while using continuations to handle backtracking
when necessary.

Different variations exist within each approach. State machines might be implemented as finite
state machines (FSMs), pushdown automata, or even Turing machines depending on the complexity
needed. Continuations might be full continuations (capturing the entire program state) or delimited
continuations (capturing only a portion of the execution context). The choice between these
mechanisms typically depends on specific requirements and constraints of the system being built.

Together, these interconnected techniques form the foundation of how modern programming languages
and runtimes manage execution flow. While they can be studied separately, their true power emerges
when understanding how they complement each other in creating flexible, efficient program execution
models.