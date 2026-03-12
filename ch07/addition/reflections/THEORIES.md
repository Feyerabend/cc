
## Code, Computation, and the Logic Beneath

There is a way of looking at programming that most working programmers never encounter,
and yet it underlies virtually everything about how modern languages are designed.
Not only that but also how compilers enforce correctness, and how researchers think about
what software fundamentally *is*. It begins with a deceptively simple observation:
that code is not merely instruction. It is, in a precise and technical sense, argument.

To arrive at this view requires moving through several layers of abstraction.
At the most immediate level, a program is syntax--a structured arrangement of symbols,
built according to grammatical rules, that produces trees of nested expressions.
At this level code has no meaning. A function application like `f(x + 1)` is simply a
shape, a hierarchical organisation of tokens. It says nothing yet about what will
happen when it runs. Or whether it is even coherent. This is the level of pure structure.
This is the level at which a compiler first encounters a program and has no more insight
into it than a reader scanning an unfamiliar alphabet.

Meaning enters through semantics. This is the layer where computation lives. Semantics
defines how code *behaves*. That is how expressions transform into other expressions,
how functions consume arguments and yield results, how programs step forward through
their execution. In the lambda calculus, the foundational model of functional computation,
this transformation is described by a single beautiful rule: apply a function to a value,
and replace every occurrence of the parameter in the body with that value. Everything
else follows from repetition of this substitution. Computation, under this view, is nothing
more than *rewriting*. This same basic idea extends to every computational model we know of,
whether Turing machines stepping through tape, processes exchanging messages in the
pi-calculus, or dataflow graphs propagating values through networks of operations.

What changes between these models is not the essence of computation but its shape.
Functional computation flows through nested substitution; concurrent computation unfolds
across simultaneously evolving processes; sequential computation maintains explicit state
and steps through mutation. Each model illuminates something different about what it
means to transform information. Each corresponds to a different class of programming language.

But syntax and semantics together are still not enough to understand what makes modern
language design so intellectually rich. The third layer, and the one that connects
programming most deeply to mathematics, is the layer of types.

#### Types then ..

Types, at first glance, seem like a practical device. A way to prevent a programmer from
accidentally adding a string to an integer, or calling a function with the wrong number
of arguments. This is true. But it is almost trivially true, and it misses most of what
types actually are. A type is a *logical proposition about a program*. When we write that
a function has type `Int -> Int`, we are not merely saying it accepts integers and returns
integers. We are asserting a logical claim: given evidence of an integer, this function
can produce evidence of another integer. The function itself, when written, is not just
code. But it is a *proof* of that claim. Proof exists in code.

This is the Curry-Howard correspondence. Independently arrived at by Haskell Curry and
William Alvin Howard in the mid-twentieth century, it reveals a structural equivalence
between logic and computation that goes far deeper than analogy. Propositions correspond
exactly to types. Proofs correspond exactly to programs. The process of checking a proof
corresponds to the process of type-checking a program. And the simplification of a proof
corresponds exactly to the evaluation of a program. When you run `(λx. x + 1) 3` and
obtain `4`, you are not merely executing code. You are normalising a proof:
reducing a complex logical derivation to its simplest, most direct form.

Under this correspondence, the logical connectives of classical reasoning translate directly
into programming constructs. Conjunction (both A and B are true) becomes the pair type,
because a value witnessing both A and B must carry evidence of each. Disjunction (A or B)
becomes the sum type, or variant, because the value is one or the other alternative.
Universal quantification becomes parametric polymorphism: a function that works for
all types is a proof that a proposition holds for all possible inputs. Existential
quantification allows a component to package a type together with values that depend
on that type, while hiding the actual type from the outside world. The logical structure
of reasoning and the structural architecture of programs are, beneath the surface,
the same thing written in different notation.

What the Curry-Howard correspondence does, above all, is reframe what programming is.
It is not the composition of instructions for a machine. It is the construction of formal
mathematical objects. A program inhabiting a type is a witness to the satisfiability
of a proposition. A type checker is not a mechanical filter: it is a proof verifier.
And this framing opens up a vast landscape of possibility.


#### Types, types, types ..

[Dependent types](./../../../ch08/sec8.13.2) push this logic furthest.
In a dependently typed language, types are permitted to *depend on values*.
A vector can carry its length in its type: `Vector(n)`. A function that
concatenates two vectors can declare in its type that the result has
length `n + m`. The type becomes a specification, and the program becomes a proof that
the specification can be fulfilled. Crucially, it becomes *impossible* to call a
function expecting a nonempty list on an empty one, because the type system literally
forbids the construction of such a call. The compiler enforces this at the level of logic,
not merely convention. This is what is meant by *correct-by-construction* software.
This is not that software has been tested, but software whose correctness is guaranteed
by the same mechanism that guarantees the correctness of a mathematical proof.

[Refinement types](./../../../ch05/addition/refinement/) occupy a more pragmatic
position in this space. Rather than allowing full value-dependent types, they attach
logical predicates to existing types: an integer greater than zero, a string of
exactly sixteen characters, a list whose elements are sorted. These predicates are
discharged not by type inference alone but by external solvers. The compiler passes
the obligation to an SMT solver, which checks whether the predicate can be violated.
The result is a powerful middle ground: far more expressive than simple type systems,
far more tractable than full dependent types, and capable of catching a remarkable
range of errors before any code runs.

Linear and [affine types](./../../../ch05/addition/affine/) pursue a different
dimension of logical control. They do not ask *what* a value is, but *how many times*
it is used. Linear logic, developed by Jean-Yves Girard, treats logical propositions
as *resources* that are consumed by proof. It corresponds directly to the intuition
that some values: file handles, network connections, allocated memory must be used
exactly once: opened and closed, sent and acknowledged, allocated and freed.
Affine types relax this to *at most once*: a value may be used or discarded, but not duplicated.
Rust's ownership system is, at its core, an affine type system implemented with practical
engineering constraints, and its famous memory safety guarantees (no use-after-free,
no double-free, no data races) follow directly from this logical foundation. The compiler is
not performing heuristic analysis. It is enforcing the rules of a formal logic.

[Session types](./../sessions/) extend this resource-aware thinking into the domain
of communication. A session type describes a protocol: not just the shape of messages
but their *order* and *direction*. A type `!Int.?Bool.end` specifies a channel that
first sends an integer, then receives a boolean, then terminates. Two processes communicating
over such a channel can be checked at compile time for protocol conformance:
the type system ensures they will never deadlock by disagreeing about who speaks next,
never violate the protocol by sending a string when an integer was expected.
This is behavioral typing: types that describe not what a value is but how a computation
*evolves over time*. The logical foundation here loops back to linear logic,
which provides the formal semantics for these protocols, with each channel viewed
as a resource that is consumed by communication.

[Effect systems](./../../../ch08/addition/effect/) add yet another dimension.
A purely functional program, one that performs no I/O, modifies no state,
throws no exceptions, is in a certain sense the cleanest kind of logical object:
a deterministic mapping from inputs to outputs, with no hidden dependencies
on the world. But real programs *do* have effects, and effect systems track these explicitly
in the type. A function's type declares not just what it returns but what it *does* to the
world in doing so. This turns effects from an implicit background assumption into a
first-class part of the type-level specification. Algebraic effect systems go further,
treating effects as abstract operations that can be handled (intercepted and given meaning)
at any point in the call stack, separating the description of an effect from its interpretation
in a way that makes programs modular and composable even when they interact with state,
exceptions, or asynchrony.

### Conclusion

Taken together, these systems reveal that the design of a programming language is not primarily
an engineering problem but a *logical one*. The central decisions, that is how memory is managed,
how concurrency is structured, how side effects are tracked, how protocols are enforced, they
all correspond to choices about which logical framework underlies the language. A language
built on linear logic will have different guarantees, different expressiveness, and a different
relationship between programmer and program than one built on intuitionistic logic or classical
logic. The type system is, in this sense, the logical system made concrete and computational.

None of this is actually purely theoretical. The most consequential software verification projects
of recent decades all rest on this foundation. There is the [CompCert](https://compcert.org/),
the formally verified C compiler, the [seL4](https://sel4.systems/), microkernel whose correctness
is machine-checked, or the cryptographic protocols verified in [F*](https://fstar-lang.org/).
They treat programs as proofs, compilers as proof transformers, and type checkers as formal
verifiers. The result is software whose correctness is not merely believed but *demonstrated*,
in the same sense that a mathematical theorem is demonstrated: by construction of an explicit,
checkable argument that no counterexample can exist.

What emerges, looking across all of this, is a unified picture of what computation and code actually are.
Code is a formal symbolic object, structured according to grammatical rules, inhabiting a world of types
that are logical propositions about its behaviour. Computation is the normalisation of proofs:
the reduction of complex derivations to their simplest direct form. And programming languages are
logical frameworks: formal systems in which reasoning and calculation are the same activity,
expressed in different notations depending on which level of the correspondence you happen to be looking at.

The machine, at the bottom of all this abstraction, does something much simpler and much more
physical. Here transistors switch, memory changes state, signals propagate. But the conceptual
distance between that physical substrate and the logical structures a programmer works with is
bridged by theoretical insight. The bridge is type theory, and once you see it clearly, it is
difficult to see programming as anything other than mathematics/certain logic that happens to run.

