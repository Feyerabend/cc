
## Alternative Routes: Functional and Structural Foundations

Although this chapter follows the imperative route, two other major perspectives on
programming foundations are worth understanding: the *functional* route and the *structural*
route. Both provide their own logic, their own way of thinking about computation,
and their own historical motivations. These routes are not merely stylistic choices;
they represent different answers to the question “What is computation?”


### The Functional Perspective

The functional perspective approaches computation as the evaluation of expressions rather
than the manipulation of changing state. In this view, a program is a collection of
definitions--functions that accept values and return new values. The key principle is
immutability: once a value is created, it does not change. Instead of updating variables,
new values are produced from old ones, much like in algebra.

This approach works because it eliminates a whole class of complications. If nothing
changes, then the meaning of an expression depends solely on the meaning of its parts.
This property, called *referential transparency*, makes reasoning about programs far easier.
A function call can be replaced by its result without altering the program’s behaviour.
Many optimisations, such as memoisation and lazy evaluation, rely on this stability.

Historically, the functional perspective arises from mathematical logic and the lambda
calculus, which was created to formalise the idea of functions and substitution long
before computers existed. Early researchers saw computation as a form of symbolic
reduction--expressions simplifying into other expressions--and functional programming
languages grew directly out of that tradition. Languages such as Lisp, ML, and Haskell
preserve this lineage.

In a functional system, the "flow" of computation is not described by commands but by
expressions nestingly applied to one another. A functional program therefore expresses
*what* something is, not *how* to update some state to achieve it. This difference sets
the functional route apart from the imperative foundations of state, memory, and sequential
steps.


### The Structural Perspective

The structural route focuses on the shape of both data and computation. Instead of loops
and mutable counters, it relies heavily on recursion: defining a problem in terms of smaller
instances of itself. Instead of manual branching, it uses pattern-matching to express how
different cases of a data structure should be handled.

This perspective works particularly well when dealing with rich, nested data--lists, trees,
syntax structures, and decomposable patterns. A structural program follows the form of the
data being processed: the structure of the argument determines which branch of the computation
is used. This leads to programs that are often clearer, shorter, and more directly aligned
with the problem itself.

Structurally oriented languages or styles were influenced by mathematical induction, logic,
and the desire to describe algorithms in a way that naturally mirrors the problem's conceptual
form. In this setting, "control flow" is handled not by jumps or mutable indices, but by
systematically breaking data apart and defining rules for each case. The programmer describes
the structure of the computation as a set of well-formed transformations.

Structurally oriented computation remains close to mathematical reasoning: one proves a
property about a program the same way one proves a property about inductively defined
objects--by analysing each structural case. This transparency is one of its major strengths.

The structural route is the style most strongly associated with languages such as ML,
OCaml, and early formulations of Algol-like recursion theory. It focuses on the idea
that both data and computation have a *shape*, and that programs should follow that
shape closely. Computation is expressed through recursion, and choices are expressed through
pattern-matching that mirrors the organisation of the data itself: lists, trees, variants, and
algebraic data types. Instead of state updates or loops, one works case by case, decomposing
the input and defining the result for each structural situation. This makes the structure
of the program correspond directly to the structure of the problem.


#### Then Why?

These routes exist because *computation* is not only a machine-level phenomenon but also
a conceptual one. Different models of programming emphasise different aspects of reasoning:

- The imperative route reflects how hardware actually executes instructions.
  It introduces programming as state changes and control flow, mapping naturally
  to the underlying architecture.
- The functional route emphasises mathematical purity, simplicity of reasoning,
  and expressions as the central unit of computation.
- The structural route emphasises decomposition, recursion, and pattern-directed
  computation, mirroring the shape of data.

Each route answers a different question.
Imperative programming asks: *How do we tell the machine what to do?*
Functional programming asks: *How do we describe computations cleanly and predictably?*
Structural programming asks: *How can computation follow the form of the data itself?*

Understanding these alternative routes provides valuable context. Even if this chapter
focuses on the imperative foundations--largely because they map directly onto the machine-level
concepts explored in the following VM chapter--the functional and structural routes show
that computation is broader and more varied than any single model. They offer powerful
abstractions and insights that become increasingly important as students progress beyond
the machine-level view.









--- FURTHER? AS TOPIC FOR PROJECT? FOR STUDY?

## Perspectives on Computation: Structural, Relational, Functional, and Automata-Based Views

When studying computation, it is easy to identify it with a particular implementation style or programming language. Yet computation admits several distinct conceptual perspectives. Each perspective emphasises a different organising principle: structure, relations, functions, or state transitions. None of these contradicts the formal theory of computability; instead, they offer different ways to understand and design programs within the boundaries of what is computable.

This section surveys *five* such viewpoints. The aim is not to argue that one is universally superior, but to show how each frames computation in a characteristic way and supports particular styles of reasoning, design, and implementation.

### 1. Structural Programming: JSP and JSD

Jackson Structured Programming (JSP) and its later extension, Jackson System Development (JSD), exemplify a structural perspective on computation. Their central assumption is that the structure of a program should correspond directly to the structure of the problem domain, especially the structure of input and output data.

The method begins by analysing the shapes of the data streams involved: sequences, iterations, alternatives, and hierarchies. Control structures in the program are then constructed to mirror these shapes. A program, in this view, is a structural mapping from input to output, and correctness consists in preserving or transforming this structure in a controlled way.

JSP operates at the level of single programs. JSD generalises the idea to systems: data structures, processes, and their life cycles are modelled explicitly, and the system is built as a coordinated network of structure-preserving components.

The structural perspective encourages a deterministic, comprehensible design style. It tends to produce programs in which control flow is predictable because it is anchored in the form of the data. This perspective is particularly effective for applications characterised by well-structured input streams, formatted records, and predictable interactions.

### 2. Algebraic Data Types and Pattern Matching

A related but more formally grounded structural view arises in languages with algebraic data types (ADTs) and pattern matching, such as Haskell, ML, or modern functional subsets of Python and Rust.

Here, the domain of computation is modelled explicitly using constructors that describe all valid shapes of data. Computation is organised around the idea of destructuring: matching incoming data against these known shapes and applying case-specific transformations.

Whereas JSP mirrors the structure of external data, ADTs capture the abstract internal structure of domain concepts. Pattern matching provides a direct mapping from data shape to control structure. Recursion replaces iteration as the fundamental control mechanism; the computation proceeds by navigating the structure of the data itself.

This perspective is more algebraic than the original Jackson methods and lends itself to equational reasoning, proof of correctness, and strong type safety. It shows how computation can be understood as a traversal of formally defined structures, guided by the constructors that define the domain.

### 3. Functional Decomposition

Functional decomposition views computation as the composition of functions. Program behaviour is the result of chaining operations through well-defined interfaces. The emphasis is on purity, referential transparency, and composability.

Unlike the structural perspective, which starts from data shapes, functional decomposition starts from the identification of meaningful transformations. The program is created by refining these transformations into simpler components until the desired level of detail is achieved.

This perspective supports a mathematically grounded style of reasoning using composition and higher-order functions. It works well when the domain can be described in terms of transformations rather than data-driven control flow. It also enables powerful abstractions such as map–reduce pipelines, monadic control structures, and separation of concerns between pure computation and effect handling.

Where structural programming stresses correspondence, functional programming stresses abstraction: what matters is how functions combine, not how they reflect the external world.

### 4. Relational Programming

Relational programming, typified by Prolog, views computation as the search for values that satisfy a set of logical relations. Programs are collections of facts and rules, and execution corresponds to proof search in a formal system.

This perspective replaces the procedural notion of control flow with a declarative notion of logical consequence. Instead of specifying how to compute a result, one specifies the properties that the result must satisfy. The runtime system determines the sequence of operations needed to derive the result.

The relational view highlights computation as inference. It is well-suited to domains in which constraints, dependencies, or deductive structures dominate, such as symbolic reasoning, database querying, and rule-based systems. It abstracts away the structure of data and the composition of functions, treating everything as a set of logical relationships.

In contrast to JSP’s focus on structure or the functionalist’s focus on composition, relational programming emphasises semantics: a solution is anything that satisfies the logical specification.

### 5. Automata-Based Perspectives

Automata-based perspectives view computation as transitions between states according to a defined transition function. Finite-state machines, pushdown automata, Turing machines, and statecharts are all instances of this view.

Here, computation is behaviour over time. A program is understood as a state machine, and its correctness concerns the validity of transitions and the reachability of states. This perspective is particularly suited to interactive, reactive, or embedded systems, where the primary challenge is handling sequences of events under constraints of timing or concurrency.

Automata-based models make explicit the relationship between computation and control. They reveal the temporal structure of computation in a way that structural or functional perspectives sometimes hide. They also align closely with hardware and communication protocols, where state transitions are fundamental.

In contrast to relational programming, which abstracts away time, automata place time and ordering at the centre of the model.

### 6. Comparison and Synthesis

The different perspectives do not compete; they complement one another by illuminating different dimensions of computation.
- Structural methods (JSP, JSD) emphasise the correspondence between program structure and data structure.
- Algebraic data types and pattern matching emphasise formal data modelling and case-based reasoning.
- Functional decomposition emphasises abstraction through composable transformations.
- Relational programming emphasises constraints and logical specification rather than procedural steps.
- Automata-based views emphasise state, time, and control.

Many modern programs mix these perspectives. A compiler, for example, may use algebraic data types to model syntax trees, functional transformations for optimisation passes, relational rules for type inference, and automata for lexical analysis.

Understanding computation through multiple perspectives helps designers choose the most effective model for each part of a system. Structural perspectives provide clarity; functional perspectives provide abstraction; relational perspectives provide semantic precision; automata provide temporal control. Their interplay enriches the practice of programming without altering the underlying theory of computability.
