
## Exploring Abstract Machines

- *[The SECD Machine](./secd/)*:
  The SECD machine, introduced by Peter Landin, is an abstract stack-based virtual machine for evaluating
  functional languages like Lisp, based on lambda calculus. Its state comprises Stack, Environment, Control,
  and Dump, handling operations like function application, conditionals, and recursion via instructions
  (e.g., `LDC`, `LDF`, `AP`). It supports closures and lexical scoping, serving as a compiler target or
  teaching tool. While simple and expressive, it's not optimised for hardware and lacks robust error handling.

- *[WAM (Warren Abstract Machine)](./wam/)*:
  The WAM is a virtual machine tailored for executing Prolog programs, acting as a compiler back-end
  and runtime environment. It translates Prolog code into an intermediate representation (WAM code)
  for efficient execution, supporting features like backtracking and unification. As an abstract machine,
  it ensures portability across platforms but is specific to Prolog's logical execution model,
  distinguishing it from general-purpose VMs like the JVM.


### Relation to Operational Semantics

Operational semantics, in general, describes the meaning of a program by specifying how it
executes step by step. Instead of defining meaning via mathematical objects (as in denotational
semantics) or logical relations (as in axiomatic semantics), it defines meaning by transitions
between states of an abstract machine.


#### SECD
The SECD machine state:
⟨S, E, C, D⟩ (Stack, Environment, Control, Dump) is an explicit operational
model of evaluation for the λ-calculus. Each instruction changes this state
in a precisely specified way. A λ-expression is "given meaning" by compiling
it into SECD instructions and then observing how these instructions transform
the machine state until a final value is reached. In that sense, the SECD
machine is not merely an implementation trick: it is an operational semantics
for a functional language. It tells you exactly what evaluation means, in
terms of concrete transitions.

The WAM (Warren Abstract Machine) plays the same role for Prolog.
It gives an operational account of:
- unification,
- backtracking,
- choice points,
- environment and trail management,
- and goal resolution.

A Prolog program is compiled into WAM instructions, and its semantics is
realised by how those instructions manipulate registers, stacks, and the
heap. Again, meaning is not defined abstractly but procedurally:
by the behaviour of the abstract machine.

However, there is an important nuance.

SECD and WAM are not small-step structural operational semantics in the
Plotkin sense, where one writes inference rules like

```
⟨e, σ⟩ → ⟨e', σ'⟩
```

They are instead *machine operational semantics*. They sit one level lower,
closer to implementation, but they are still abstract machines, not physical
hardware. Their states and transitions are idealised and mathematically describable.

So you can think of them like this:

|Form of semantics  |Level of abstraction|
|-------------------|--------------------|
|Denotational|Mathematical meaning|
|Structural operational|Language-level steps|
|Abstract machine (SECD, WAM)|Execution-level steps|
|Real hardware|Physical execution|

Another way to put it:
- A structural operational semantics explains what evaluation steps are.
- An abstract machine explains how those steps are realised.

But both are operational in spirit, because both define meaning by execution.

There is also a historical point: both machines were originally designed as efficient
execution models, not as semantic formalisms. Yet *later work* showed that they can be
'derived from, or correspond closely to, more abstract operational semantics.
For example:
- The SECD machine can be systematically derived from a call-by-value λ-calculus
  with environments and closures.
- The WAM can be related to SLD-resolution and the formal semantics of
  logic programming.

So their status is slightly dual:
- They are execution models used in real systems.
- They are also precise semantic artefacts that define how programs behave.

In short: SECD and WAM are operational semantics, but of a particularly
concrete kind. They define the meaning of programs by giving an explicit
abstract machine whose state transitions are the semantics.


