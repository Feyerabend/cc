
## π-calculus

The π-calculus is a foundational framework in theoretical computer science, designed to model and analyse
systems characterised by concurrent interactions and dynamic communication structures.[^pi] Developed in the
late 1980s by Robin Milner, Joachim Parrow, and David Walker, it extends earlier process calculi such as
Milner’s Calculus of Communicating Systems (CCS) by introducing a novel feature: the ability for processes
to transmit communication channels themselves as messages. This capability, termed *mobility*, enables the
π-calculus to elegantly represent systems where the network topology or communication links evolve during
execution, making it particularly suited for modelling modern distributed systems, network protocols, and
mobile applications.

[^pi]: Milner, R., Parrow, J., & Walker, D. (1992a). A calculus of mobile processes, I. *Information and
Computation*, 100(1), 1–40. https://doi.org/10.1016/0890-5401(92)90008-4. Milner, R., Parrow, J., & Walker,
D. (1992b). A calculus of mobile processes, II. *Information and Computation*, 100(1), 41–77.
https://doi.org/10.1016/0890-5401(92)90009-5.


At its core, the π-calculus revolves around the concept of *processes*--autonomous entities that execute
concurrently and interact by sending and receiving messages through named channels. A channel in this context
is a medium for communication, akin to a rendezvous point where processes synchronise to exchange data.
Unlike traditional models where communication channels are static, the π-calculus allows channels to be
dynamically created and shared. For instance, a process might send a newly created channel name over an
existing channel, thereby granting the recipient access to a private communication line or a fresh computational
resource. This mechanism of *name passing* underpins the calculus’s expressive power, enabling it to capture
scenarios such as service discovery in distributed systems or protocol negotiation in networked environments.

The syntax of the π-calculus is built from a small set of operators that define process behaviours. Processes
can perform *actions*--such as sending an output prefix (e.g., `x!y` to send name `y` over channel `x`) or
receiving an input prefix (e.g., `x?z` to bind a received name to variable `z`). These actions are combined
using operators for parallel composition (`P | Q`), which allows processes to run side by side; restriction
(`(νx)P`), which creates a new channel `x` private to process `P`; and replication (`!P`), which represents
an unbounded number of copies of `P`. Silent actions, denoted by `τ`, model internal steps not visible to
external observers. Reduction semantics govern how processes evolve: when two parallel processes perform
complementary send and receive actions on the same channel, they synchronise, leading to a state transition
where the communicated name replaces the bound variable in the receiving process. For example, if process
`x!y | x?z.P` executes, the name `y` is transmitted over `x`, and the receiver proceeds as `P` with `z`
replaced by `y`.

A hallmark of the π-calculus is *scope extrusion*, a phenomenon where a private channel name, initially
known only within a restricted process, becomes accessible to other processes through communication.
Consider a scenario where a process `(νa)(a!msg | x!a)` sends the restricted name `a` over a public channel
`x`. Upon reception, the recipient gains access to `a`, effectively extending the scope of `a` beyond its
original boundary. This feature mirrors real-world patterns such as capability delegation or the dynamic
reconfiguration of communication networks, where privileges or resources are distributed at runtime.

The expressive power of the π-calculus is profound: it is Turing-complete, capable of encoding arbitrary
computable functions, and its bisimulation equivalence--a behavioural equivalence relation--provides
a rigorous method for comparing process behaviours. Variants like the *spi-calculus* extend it with
cryptographic primitives for analysing security protocols, while the *applied π-calculus* incorporates
arbitrary data structures and functions, broadening its applicability to modern programming paradigms.
Practically, the π-calculus has influenced the design of programming languages such as Erlang and Go,
which emphasise concurrency and message-passing. Its theoretical insights underpin tools for protocol
verification, deadlock detection, and type safety in distributed systems.

In summary, the π-calculus offers a minimalist yet potent language for reasoning about concurrency, mobility,
and interaction. By abstracting away implementation details and focusing on communication dynamics, it
provides a unifying framework for understanding complex systems, from biological processes to cloud
computing architectures. Its legacy endures in both academic research and industrial practice, cementing
its role as a cornerstone of concurrency theory.

 
#### Mathematical Foundations
 
*Syntax*  
The π-calculus is defined by a small set of operators. Let \($` P, Q `$\) range over processes, \($` x, y, z `$\)
over channel names, and \($` \tau `$\) denote silent actions. The syntax is formally defined as:  
 
```text
P, Q ::=   0            (inactive process)
         | x!y.P        (send y on x, then P)
         | x?z.P        (receive on x, bind to z, then P)
         | τ.P          (internal action, then P)
         | P | Q        (parallel composition)
         | (ν x)P       (restrict x to P)
         | !P           (replication: infinite copies of P)
```

The *behavior of processes* in this system is precisely defined by *reduction rules* ($\rightarrow$)
and *structural congruence* ($\equiv$). These rules dictate how processes evolve and when they are
considered equivalent. Key rules include:

1.  *Communication*:

    $$\frac{}{x!y.P \mid x?z.Q \rightarrow P \mid Q[y/z]} \quad \text{(COMM)}$$

    This rule describes *synchronous communication*. When a process $P$ sends a value $y$ on channel
    $x$ and another process $Q$ receives a value $z$ on the same channel, they can *communicate*.
    Upon communication, $Q$ proceeds with its continuation where $z$ is replaced by the received value $y$.

2.  *Scope Extrusion*:

    $$(\nu x)(P \mid Q) \equiv P \mid (\nu x)Q \quad \text{if } x \notin \text{fn}(P)$$

    *Scope extrusion* allows a *restricted name* ($x$) to be moved out of a parallel composition.
    This is permissible *only if* the process $P$ does not depend on or use the name $x$, ensuring
    that the scope of $x$ is not unintentionally extended.

3.  *Replication*:

    $$!P \equiv P \mid !P$$

    The *replication operator* ($!$) enables the creation of an *unlimited supply of processes*.
    Essentially, $!P$ can always "spawn" a fresh copy of $P$ whenever needed, allowing for continuous
    or repeated actions.


#### Sample Programs
 
*Example 1: Simple Communication*  
Two processes exchange a message on channel \( a \):  
```pi-calculus  
(νa)(a!hello.0 | a?x.0)  
```  
- *Reduction*: The sender \( a!hello.0 \) and receiver \( a?x.0 \) synchronise.
  After communication, both reduce to \($` \mathbf{0} `$\).  
 
*Example 2: Recursive Server*  
A server that repeatedly receives requests on channel \( s \):  
```pi-calculus  
!s?req.(req!data.0)  
```  
- *Behavior*: The server infinitely replicates itself, waiting for requests on \( s \). When a request
\( req \) arrives, it sends \( data \) back on \( req \).  
 
*Example 3: Scope Extrusion*  
A restricted channel \( k \) is sent over a public channel \( pub \):  
```pi-calculus  
(νk)(k!secret.0 | pub!k.0) | pub?y.y?z.0  
```  
- *Reduction*: The private name \( k \) is transmitted over \( pub \). The recipient \( y?z.0 \)
reads \( secret \) from \( k \), demonstrating dynamic scope extension.  
 
 
#### Connection to Logic via Sequent Calculus

The $\pi$-calculus, a foundational model for concurrent computation, exhibits *deep and significant
ties to linear logic*. This connection is particularly evident through *session types*, which provide
a formal system for describing communication protocols as logical propositions. Furthermore,
*sequent calculus*, a powerful proof-theoretic formalism for constructing logical derivations, offers
a striking parallel to the communication patterns observed in the $\pi$-calculus. This alignment
allows us to understand process behaviour from a logical perspective.

*Mapping $`\pi`$-Calculus to Linear Logic*
The core elements of the $\pi$-calculus find direct logical counterparts in linear logic:

* *Channels* ($\nu x$ in $\pi$-calculus) $\approx$ *Linear logic propositions*. In linear logic, propositions
  represent resources that are consumed or produced exactly once. Channels behave similarly, as messages sent
  or received consume a resource.

* *Input ($`x?z.P`$)* $\approx$ *Right rule for implication ($`\multimap`$)*. An input operation corresponds to
  the introduction of an implication on the right side of a sequent, signifying the ability to receive a
  resource and then continue.

* *Output ($`x!y.P`$)* $\approx$ *Left rule for implication ($`\multimap`$)*. An output operation corresponds
  to the elimination of an implication on the left side of a sequent, representing the act of providing a resource.

* *Parallel ($`P \mid Q`$)* $\approx$ *Multiplicative conjunction ($`\otimes`$)*. The parallel composition of processes
  naturally aligns with the multiplicative conjunction in linear logic, where two resources (or processes) exist
  concurrently and can interact.

*Example: Logical Derivation of Communication*
Let's consider the fundamental communication step in the $`\pi`$-calculus: $`x!y.P \mid x?z.Q`$. In the context of
linear logic, specifically with session types, this interaction can be elegantly represented as a sequent:

$$\vdash x : A \otimes B, \; x : A \multimap C$$

Here, $x!y.P$ is interpreted as a proposition indicating the intention to send a value $y$ of type $B$ on channel
$x$, where $x$ itself has type $A$ for the communication (represented as $A \otimes B$). Conversely, $x?z.Q
represents the intention to receive a value of type $A$ on channel $x$, which will then enable the continuation
$Q$ to produce a result of type $C$ (represented as $A \multimap C$).

Using sequent calculus rules, the communication proceeds as a *cut elimination* step:

$$
\frac{
  \vdash y : B \quad \vdash Q[y/z] : C
}{
  \vdash x!y.P \mid x?z.Q \rightarrow P \mid Q[y/z] \quad \text{corresponds to} \quad \vdash P, Q[y/z] : \mathbf{0} \mid C
} \quad \text{(Cut Elimination)}
$$

The communication step in $\pi$-calculus, where $y$ is transmitted and $z$ is substituted, directly corresponds
to the *elimination of a "cut"* in the sequent calculus. This "cut" signifies the synchronisation point between
the multiplicative conjunction ($\otimes$, representing the sender) and the implication ($\multimap$, representing
the receiver), yielding the subsequent states of $P$ and $Q[y/z]$. This provides a powerful logical underpinning
for concurrent communication.

*Bisimulation as Logical Equivalence*
Perhaps one of the most profound connections lies in the equivalence notions. *Bisimulation*, the standard and
widely accepted notion of observational equivalence in process calculi like the $\pi$-calculus, directly aligns
with *proof equivalence* in logic. This means that two processes are bisimilar if and only if their corresponding
logical derivations (or proofs) can be transformed into one another in a way that preserves all observable behaviour.
This deep correspondence provides a robust logical foundation for understanding and verifying concurrent systems.


#### Summary

The π-calculus provides a rigorous mathematical framework for concurrency, enriched by its
operational semantics and structural congruence. Its connection to sequent calculus reveals
a profound duality: process interactions mirror logical derivations, and bisimulation corresponds
to proof normalisation. This interplay has inspired tools like session types, where protocols
are verified using type systems derived from linear logic, bridging programming languages and
formal logic.



### Programs

#### Threading-Based Version: PIVM

*Key Characteristics:*
- Uses Python's `threading` module
- Implements lightweight concurrency within a single process
- Shared memory access (no serialisation needed)
- Simpler channel implementation with `queue.Queue`
- Process registry maintained in a shared dictionary

*Example Flow (P and Q):*

```
P → [Channel a] → Q
1. P sends 42 on channel 'a'
2. Q receives from 'a', stores in variable x
3. Q logs the received value
```

#### Multiprocessing-Based Version: MPPI

*Key Characteristics:*
- Uses Python's `multiprocessing` module
- True parallel execution across CPU cores
- Requires explicit shared memory management
- Channels use managed queues with locks
- Objects are serialised when crossing process boundaries
- Includes process-safe printing with locks
- More robust process cleanup with timeouts

*Example Flow (P and Q):*
```
(Process P) → [Managed Channel a] → (Process Q)
1. P serializes and sends 42 via multiprocessing.Queue
2. Q receives and deserialises the value
3. Cross-process logging with lock synchronisation
```

#### Differences

| Feature          | Threading Version          | Multiprocessing Version                  |
|------------------|----------------------------|------------------------------------------|
| Concurrency Model| Preemptive threading       | True parallel processes                  |
| Memory           | Shared address space       | Isolated memory (requires serialisation) |
| Channel Implementation | Simple Queue.Queue   | Managed Queue with Lock                  |
| Safety           | Potential race conditions  | Process isolation prevents races         |
| Overhead         | Low (green threads)        | Higher (IPC serialisation)               |
| Use Case         | I/O-bound tasks            | CPU-bound parallel processing            |

Both implement the same π-calculus-inspired semantics but with different Python concurrency primitives
underneath. The multiprocessing version is heavier but avoids GIL limitations, while the threading
version is more lightweight but constrained to single-core execution for CPU-bound work.

