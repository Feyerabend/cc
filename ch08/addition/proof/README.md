
> *The aim:* A kernel where every type-theoretic concept is legible in C source,
> growing into a practical tool for specifying and verifying properties of programs
> using Homotopy Type Theory as the foundation.

The system is a programming language laboratory. A term `t : A` is simultaneously
a program of type `A`, a proof that `A` is inhabited, and a computation that the
graph reducer can normalize. The type checker is a proof checker. The normalizer
is an operational semantics. These are not analogies--they are the same object
seen from different angles.

The concrete endpoint is: write the type soundness proof for a small typed
language *inside the system itself*, as an inhabitant of a dependent type.
Getting there requires indexed inductive families, a module system, and
eventually implicit arguments.

.. eventually.