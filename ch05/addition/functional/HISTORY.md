
## Evolution of Functional Languages & Concepts

Early functional languages grew out of lambda calculus, both historically and conceptually.
Lambda calculus was invented as a minimal model of computation: everything is an expression,
and computation proceeds by reduction. A function is applied, a substitution happens, and
eventually an expression reduces to a value. This worldview is fundamentally operational.
You reason about what a program does by imagining how it rewrites itself step by step.

Lisp and later Scheme embody this directly. They are essentially executable lambda calculus
with conveniences: numbers, conditionals, mutation, and I/O. Their defining intellectual
move is not strong static structure, but freedom. Code is data, evaluation is transparent,
and the language gets out of the programmer’s way. Correctness is something the programmer
enforces through discipline, conventions, and understanding of evaluation. The language
provides power, not guardrails. This is why macros are often very central: programs are
meant to be transformed, reshaped, and extended by other programs.

In this world, types are either absent or lightweight. They do not define the meaning of
a program; they merely annotate it. The semantics live in evaluation, not in static structure.
If you understand substitution and reduction, you understand the language.

Haskell represents a decisive conceptual shift. It is still based on lambda calculus at runtime,
but it is designed around a different question. Instead of asking "how does this expression reduce?",
it asks "how do computations compose, and what structure do they preserve?" That question does
*not* come from lambda calculus; it comes from category theory.

Category theory does not care about the internal steps of computation. It abstracts them away.
What matters are the connections between computations, the identities they respect, and the laws
that make composition predictable. When this perspective enters programming, types stop being
annotations and become the primary carriers of meaning. A program is no longer just an expression
that reduces; it is a morphism between types that must respect certain laws.

This is why Haskell is pure by default. Purity is not a moral stance, but a structural one.
Referential transparency is what allows equational reasoning: you can replace equals with equals
without changing meaning. That property is essential if you want to reason about programs
compositionally rather than operationally. Effects therefore cannot be "just things functions do";
they must be represented explicitly as structure. Monads, applicatives, and functors are not
tricks--they are ways of reintroducing effects without abandoning compositional reasoning.

Seen this way, the difference between Lisp and Haskell is not mainly about static typing or laziness.
It is about where *meaning* lives. In Lisp, meaning lives in evaluation. In Haskell, meaning lives
in types and the laws they imply. Evaluation becomes almost an implementation detail.

Rust enters later, and from a different direction, but it reflects the same conceptual migration.
Rust is not a purely functional language, and it does not present itself in categorical terms.
Yet its design clearly assumes that unrestricted freedom is too costly at scale. Ownership, borrowing,
and lifetimes are not runtime mechanisms; they are static structure enforced by the compiler.
They encode invariants about aliasing and resource usage in the type system. This is the same
move Haskell made with effects, applied to memory and performance rather than purity.

Importantly, none of this replaces lambda calculus. Modern functional languages still use lambda
abstraction, application, and reduction as their computational core. What changed is the layer above.
Early languages trusted programmers to reason operationally. Later languages push reasoning into
the compiler by making structure explicit and illegal states unrepresentable.

There is a foundational change in the view of functional programming during the years.
Early functional languages asked: what is the smallest, most expressive model of computation
we can give humans? Later functional languages ask: what is the strongest model of correctness
we can enforce while still allowing useful programs to be written?

That shift--from reduction to composition, from freedom to law, from informal
reasoning to enforced invariants--is exactly the shift from a lambda-calculus-centered
worldview to a category-theoretic one (see [category](./../../../ch08/addition/category/)).

