
## Introduction to CSP

*Communicating Sequential Processes (CSP)* is a formal language
for describing and analysing concurrent systems.[^hoare]
Developed by Tony Hoare in the late 1970s, it provides a mathematical
framework for understanding how independent processes can interact
with each other. Think of it as a blueprint language for building
complex software systems where multiple parts run at the same time
and need to coordinate their actions.

[^hoare]: Hoare, C. A. R. (1978). Communicating sequential processes. *Communications of the ACM*, 21(8), 666–677.
https://doi.org/10.1145/359576.359585. https://www.cs.cmu.edu/~crary/819-f09/Hoare78.pdf.

Here are the core ideas behind CSP:

* *Processes:* In CSP, a system is modelled as a collection of
  independent processes. Each process performs a sequence of actions.
  These actions can be internal (like a calculation) or external
  (communicating with another process).

* *Communication:* Processes communicate exclusively through *channels*.
  A channel is a medium through which two processes can exchange information.
  This communication is *synchronous*, meaning both the sending and receiving
  process must be ready for the communication to occur. If one process is ready
  but the other isn't, the ready process waits (or "blocks") until the other
  is also ready. This synchronised exchange is called a *rendezvous*.

* *Actions:* The fundamental building blocks of a CSP process are *actions*.
  These include:
    * *Send (!):* A process sends a message on a channel.
    * *Receive (?):* A process receives a message on a channel.
    * *Tau ($`\tau`$):* An internal, unobservable action. This represents
      an action that happens within a process and doesn't
      involve communication with other processes.

* *Operators:* CSP provides a set of operators to combine basic actions and
  processes into more complex behaviours:
    * *Prefix (a $`\rightarrow`$ P):* An action `a` followed by a process
      `P`. `P` can only start after `a` has completed.
    * *Sequential Composition (P; Q):* Process `P` runs to completion,
      and then process `Q` starts.
    * *Choice (P $`\Box`$ Q or P $`\sqcap`$ Q):*
        * *External Choice ($`\Box`$):* The environment (or an external event)
          determines which of `P` or `Q` will execute.
        * *Internal Choice ($`\sqcap`$):* The process itself non-deterministically
          chooses to behave as `P` or `Q`.
    * *Parallel (P || Q):* Processes `P` and `Q` execute concurrently.
      If they share channels, communication on those channels must be synchronised.
    * *Interleaving (P ||| Q):* Processes `P` and `Q` execute concurrently without
      any shared channels, meaning their actions can be interleaved in any order.
    * *Recursion ($`\mu`$ X . P):* Allows for repeating behaviours, where `X`
      refers to the process `P` itself, enabling loops.

* *Trace Semantics:* CSP uses traces (sequences of observable actions) to describe
  the behaviour of processes. This allows for formal reasoning about properties
  like deadlock (where processes are stuck waiting for each other indefinitely) and
  livelock (where processes are busy but make no progress).

CSP is widely used in areas like:

* *Design and Verification of Concurrent Systems:* It helps engineers rigorously
  define and prove properties about parallel and distributed software.
* *Network Protocols:* Modelling and analysing how different components of a network interact.
* *Operating Systems:* Understanding the synchronisation mechanisms between various parts of an OS.


### Core Implementation Overview

This is a *formal CSP interpreter* in Python that implements Hoare-style
CSP semantics with these key features:

1. *Process Algebra Foundation*:
   - Implements core CSP operators: prefix (`→`), sequential (`;`), choice (`□`),
     external choice (`⊓`), parallel (`||`), and recursion
   - Supports guarded processes with conditions

2. *Channel Communication*:
   - Synchronous (rendezvous) message passing
   - Channels maintain queues of blocked senders/receivers
   - Strict 1:1 matching between sends and receives

3. *Advanced Features*:
   - Recursive process definitions
   - Deadlock detection via dependency graph analysis
   - Tau (τ) silent actions
   - Nondeterministic choice

4. *Debugging Support*:
   - Verbose execution logging
   - Step-by-step process execution tracing
   - Timeout and step limits

#### Example Program Components

The demo includes these representative processes:

1. *Producer*:
   ```python
   Rec("P", Seq(
       Prefix(Send("data_channel", {"id": 2, "value": "item"}), SKIP()),
       Seq(Prefix(Tau(), Var("P")), STOP())
   ))
   ```
   - Continuously sends structured data
   - Uses τ-action for pacing

2. *Consumer*:
   ```python
   Rec("C", Seq(
       Prefix(Receive("data_channel", "msg"), SKIP()),
       If(Eq("msg", {...}), STOP(), Var("C"))
   ))
   ```
   - Pattern-matches received messages
   - Terminates on specific message match

3. *Monitor*:
   ```python
   Rec("M", Choice(
       Prefix(Send("status_channel", "active"), Var("M")),
       ExtChoice(Prefix(Tau(), Var("M")), SKIP())
   ))
   ```
   - Demonstrates internal vs external choice
   - Non-deterministic behavior

4. *Deadlock Detector*:
   ```python
   Prefix(Receive("data_channel", "dummy"), STOP())
   ```
   - Shows blocked process detection

#### Execution Model

1. *Scheduler* manages parallel composition:
   - Tracks all active processes
   - Handles channel synchronisation
   - Detects deadlocks via cycle detection

2. *State Management*:
   - Shared variables environment
   - Dynamic channel creation
   - Process dependency tracking

3. *Safety Mechanisms*:
   - Maximum step limits
   - Execution timeouts
   - Verbose diagnostics

### Differentiators
- *Formal Semantics*: Closely mirrors theoretical CSP
- *Diagnostic Capabilities*: Goes beyond basic execution with deadlock detection
- *Python Integration*: Implements process calculus in an OOP style while preserving algebraic properties

This implementation can be useful for:
- Protocol verification
- Concurrency pattern experimentation
- Model checking foundations





### 1. Process Algebra Formalisation

To give a more formal approach to CSP, some concepts can be introduced
which corresponds with both implementation and theory.

#### Basic Processes
| CSP Math Notation | Python Class    | Example Usage            | Semantics                   |
|-------------------|-----------------|--------------------------|-----------------------------|
| `STOP`            | `STOP()`        | Terminal deadlock        | Inaction (deadlock)         |
| `SKIP`            | `SKIP()`        | Graceful termination     | Successful termination      |
| `a → P`           | `Prefix(a, P)`  | `Prefix(Send(c,x), Q)`   | Action `a` then process `P` |

#### Communication Primitives
| CSP Notation | Python Class  | Example                          | Channel Behaviour                      |
|--------------|---------------|----------------------------------|----------------------------------------|
| `c!v`        | `Send(c,v)`   | `Send("chan1", 42)`              | Output value `v` on channel `c`        |
| `c?x`        | `Receive(c,x)`| `Receive("chan1", "data")`       | Input to variable `x` from channel `c` |
| `τ`          | `Tau()`       | `Prefix(Tau(), P)`               | Internal silent action                 |

### 2. Composition Operators
| CSP Operator | Python Class    | Example Code                         | Implementation Behaviour             |
|--------------|-----------------|--------------------------------------|--------------------------------------|
| `P ; Q`      | `Seq(P, Q)`     | `Seq(Send(c,x), Receive(c,y))`       | Sequential composition               |
| `P □ Q`      | `ExtChoice(P,Q)`| `ExtChoice(recv1, recv2)`            | External (environment-driven) choice |
| `P ⊓ Q`      | `Choice(P,Q)`   | `Choice(Send(a,x), Send(b,y))`       | Non-deterministic internal choice    |
| `P ⟦C⟧ Q`    | `Parallel(P,Q,C)`| `Parallel(P,Q,{"chan1","chan2"})`    | Synchronized parallel on channels `C`|

### 3. Recursion & Variables
| CSP Notation  | Python Class | Example                          | Compilation Behaviour         |
|---------------|--------------|----------------------------------|-------------------------------|
| `μX.P`        | `Rec(X,P)`   | `Rec("P", Prefix(a, Var("P")))`  | Creates recursive process     |
| `X`           | `Var(X)`     | `Var("P")`                       | Unfolds recursive definition  |

### 4. Conditionals
| CSP Math          | Python Class       | Example                                   |
|-------------------|--------------------|-------------------------------------------|
| `[b]→P`           | `If(b,P,Q)`        | `If(Eq(x,1), P, Q)`                       |
| Boolean conditions | `Eq/LogicalOp`    | `LogicalOp("and", cond1, cond2)`          |


### 5. Operational Semantics Correspondence

*Prefix Rule*:
```
⟨a → P, σ⟩ ─[α]→ ⟨P, σ'⟩ 
```
↔ `Prefix.execute_action()`:
```python
def execute_action(action, cont):
    if action is Tau:
        return cont  # τ-transition
    elif channel_match(action):
        return cont  # communication transition
```

*Parallel Composition*:
```
⟨P ⟦C⟧ Q, σ⟩ ─[τ]→ ⟨P' ⟦C⟧ Q', σ'⟩ 
```
↔ `Parallel` handling:
```python
class Parallel:
    def step(self):
        # sync on shared channels
        for chan in self.channels:
            match_actions(chan)  # CSP's sync rule
```

### 6. Channel Semantics
`Channel.try_match()` implements CSP's synchronous communication:
```python
def try_match(action, cont):
    if isinstance(action, Send):
        for (recv_action, recv_cont) in waiting_receives:
            if compatible(action, recv_action):  # CSP handshake
                return (cont, recv_cont)  # both progress
    # .. similar for receives
```
This directly models CSP's:
```
⟨c!v → P ⟦{c}⟧ c?x → Q, σ⟩ ─[τ]→ ⟨P ⟦{c}⟧ Q[v/x], σ⟩
```

### 7. Deadlock Detection
Dependency graph analysis corresponds to CSP's:
```
deadlock ≡ ∃ processes where ∀P ∈ processes, blocked(P, waiting_channels)
```
Implemented via:
```python
def detect_deadlock():
    cycles = find_cycles(dependency_graph)
    return any(processes_blocked_on(cycle) for cycle in cycles)
```

### 8. Example Mappings

*Theoretical CSP*:
```
μP. (coin?x → (if x=£1 then tea!P → STOP 
               else coffee!P → STOP))
```

*Implementation*:
```python
Rec("P", 
    Prefix(Receive("coin", "x"),
    If(Eq("x", "£1"),
       Prefix(Send("tea", "P"), STOP()),
       Prefix(Send("coffee", "P"), STOP())))
```

### 9. Trace Semantics Connection
The interpreter's step-by-step execution generates CSP-style traces:
```
[ (P1, Send(c,1)), (P2, Receive(c,x)), τ, ... ]
```
Matching CSP's:
```
traces(P) = {⟨⟩, ⟨c!1⟩, ⟨c!1, c?1⟩, ...}
```

This formalisation shows how the Python implementation:
1. Preserves CSP's algebraic laws
2. Implements the operational semantics
3. Extends the formalism with practical debugging
4. Maintains the synchronous communication model

