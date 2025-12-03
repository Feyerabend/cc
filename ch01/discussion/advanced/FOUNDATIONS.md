
## Perspectives on Computation: Structural, Relational, Functional, and Automata-Based Views

When studying computation, it is easy to identify it with a particular implementation
style or programming language. Yet computation admits several distinct conceptual
perspectives. Each perspective emphasises a different organising principle: structure,
relations, functions, or state transitions. None of these contradicts the formal theory
of computability; instead, they offer different ways to understand and design programs
within the boundaries of what is computable.

This section surveys five such viewpoints. The aim is __not__ to argue that one is universally
superior, but to show how each frames computation in a characteristic way and supports
particular styles of reasoning, design, and implementation.


### 1. Structural Programming: JSP and JSD

Jackson Structured Programming (JSP) and its later extension, Jackson System Development (JSD),
exemplify a structural perspective on computation. Their central assumption is that the structure
of a program should correspond directly to the structure of the problem domain, especially
the structure of input and output data.

The method begins by analysing the shapes of the data streams involved: sequences, iterations,
alternatives, and hierarchies. Control structures in the program are then constructed to mirror
these shapes. A program, in this view, is a structural mapping from input to output, and
correctness consists in preserving or transforming this structure in a controlled way.

JSP operates at the level of single programs. JSD generalises the idea to systems:
data structures, processes, and their life cycles are modelled explicitly, and the system
is built as a coordinated network of structure-preserving components.

The structural perspective encourages a deterministic, comprehensible design style. It tends
to produce programs in which control flow is predictable because it is anchored in the form
of the data. This perspective is particularly effective for applications characterised by
well-structured input streams, formatted records, and predictable interactions.


### 2. Algebraic Data Types and Pattern Matching

A related but more formally grounded structural view arises in languages with algebraic
data types (ADTs) and pattern matching, such as Haskell, ML, or modern functional subsets
of Python and Rust.

Here, the domain of computation is modelled explicitly using constructors that describe
all valid shapes of data. Computation is organised around the idea of destructuring:
matching incoming data against these known shapes and applying case-specific transformations.

Whereas JSP mirrors the structure of external data, ADTs capture the abstract internal
structure of domain concepts. Pattern matching provides a direct mapping from data shape
to control structure. Recursion replaces iteration as the fundamental control mechanism;
the computation proceeds by navigating the structure of the data itself.

This perspective is more algebraic than the original Jackson methods and lends itself to
equational reasoning, proof of correctness, and strong type safety. It shows how computation
can be understood as a traversal of formally defined structures, guided by the constructors
that define the domain.


### 3. Functional Decomposition

Functional decomposition views computation as the composition of functions. Program behaviour
is the result of chaining operations through well-defined interfaces. The emphasis is on purity,
referential transparency, and composability.

Unlike the structural perspective, which starts from data shapes, functional decomposition starts
from the identification of meaningful transformations. The program is created by refining these
transformations into simpler components until the desired level of detail is achieved.

This perspective supports a mathematically grounded style of reasoning using composition and
higher-order functions. It works well when the domain can be described in terms of transformations
rather than data-driven control flow. It also enables powerful abstractions such as map–reduce
pipelines, monadic control structures, and separation of concerns between pure computation and
effect handling.

Where structural programming stresses correspondence, functional programming stresses abstraction:
what matters is how functions combine, not how they reflect the external world.


### 4. Relational Programming

Relational programming, typified by Prolog, views computation as the search for values that
satisfy a set of logical relations. Programs are collections of facts and rules, and execution
corresponds to proof search in a formal system.

This perspective replaces the procedural notion of control flow with a declarative notion of
logical consequence. Instead of specifying how to compute a result, one specifies the properties
that the result must satisfy. The runtime system determines the sequence of operations neede
to derive the result.

The relational view highlights computation as inference. It is well-suited to domains in which
constraints, dependencies, or deductive structures dominate, such as symbolic reasoning,
database querying, and rule-based systems. It abstracts away the structure of data and the
composition of functions, treating everything as a set of logical relationships.

In contrast to JSP’s focus on structure or the functionalist’s focus on composition, relational
programming emphasises semantics: a solution is anything that satisfies the logical specification.


### 5. Automata-Based Perspectives

Automata-based perspectives view computation as transitions between states according to a defined
transition function. Finite-state machines, pushdown automata, Turing machines, and statecharts
are all instances of this view.

Here, computation is behaviour over time. A program is understood as a state machine, and its
correctness concerns the validity of transitions and the reachability of states. This perspective
is particularly suited to interactive, reactive, or embedded systems, where the primary challenge
is handling sequences of events under constraints of timing or concurrency.

Automata-based models make explicit the relationship between computation and control. They reveal
the temporal structure of computation in a way that structural or functional perspectives sometimes
hide. They also align closely with hardware and communication protocols, where state transitions
are fundamental.

In contrast to relational programming, which abstracts away time, automata place time and ordering
at the centre of the model.


### 6. Comparison and Synthesis

The different perspectives do not compete; they complement one another by illuminating 
different dimensions of computation.
- Structural methods (JSP, JSD) emphasise the correspondence between program structure and data structure.
- Algebraic data types and pattern matching emphasise formal data modelling and case-based reasoning.
- Functional decomposition emphasises abstraction through composable transformations.
- Relational programming emphasises constraints and logical specification rather than procedural steps.
- Automata-based views emphasise state, time, and control.

Many modern programs mix these perspectives. A compiler, for example, may use algebraic data
types to model syntax trees, functional transformations for optimisation passes, relational
rules for type inference, and automata for lexical analysis.

Understanding computation through multiple perspectives helps designers choose the most effective
model for each part of a system. Structural perspectives provide clarity; functional perspectives
provide abstraction; relational perspectives provide semantic precision; automata provide temporal
control. Their interplay enriches the practice of programming without altering the underlying
theory of computability.


---

### Concrete Examples and Project Sketches

To make these perspectives tangible, you can anchor each one in a small but meaningful
project. None of the projects requires large infrastructure, and each can be implemented
in several languages depending on your preference.


#### 1. Structural Programming (JSP, JSD)

A natural example is a program whose control flow mirrors the structure of a data stream.

Example sketch:
- Parse a simple log file where each record has a clear structure: timestamp,
  event type, payload. You can design the program so that its control structure
  is dictated entirely by the structure of the records.

Possible project:
- Write a "data transformer" that reads a sequence of structured records and outputs
  summarised results. The task is to make the control flow match the data shape as
  closely as possible. Variants include transforming CSV records, telemetry streams,
  or simple network logs.

This is a good way to make explicit how JSP's structure diagrams correspond to program structure.


#### 2. Algebraic Data Types and Pattern Matching

Algebraic data types suit domains where every input can be described by a small set of constructors.

Example sketch:
- Represent a minimal expression language using variants such as
  Add(x,y), Mul(x,y), Const(n), Var(name). Write an evaluator using pattern matching.

Possible project:
- Create a tiny calculator language with integers, variables, and functions.
  The main task is to model the domain using algebraic data types, then implement
  evaluation by matching on data shapes. You could extend this gradually with
  new constructs to show how ADTs scale.

This gives you a clean demonstration of how computation follows the structure of the data itself.


#### 3. Functional Decomposition

Here the focus is on breaking a task into composable transformations rather
than following data structure.

Example sketch:
- Take a text-processing pipeline and implement it entirely as a composition
  of pure functions: normalisation, tokenisation, filtering, transformation, aggregation.

Possible project:
- Build a "text pipeline library" where each transformation is a pure function,
  and results are produced by composing these functions. Challenge yourself to
  implement it twice: once using a low-level imperative style, and once using
  pure compositions, to see how the two differ in reasoning clarity.

This demonstrates the value of referential transparency in practice.


#### 4. Relational Programming

Relational programming becomes intuitive when the domain involves constraints or logical conditions.

Example sketch:
- Specify a family tree as a set of facts and rules, and query the system for
  relationships such as siblings or ancestors.

Possible project:
- Implement a small Prolog-like engine (or use an existing one, or even a tiny
  embedded DSL in Python) to model a constrained problem: timetabling, dependency
  solving, simple graph reachability. You define relations and rules, then ask
  queries of the system.

This reveals computation as search and inference rather than execution of a predetermined sequence.


#### 5. Automata-Based Perspectives

Automata shine when the problem involves sequences of events or well-defined states.

Example sketch:
- Model a turnstile, traffic light, or vending machine as a finite state machine,
  and simulate its behaviour for a sequence of events.

Possible project:
- Build a lexical analyser for a tiny language using a hand-written deterministic
  finite automaton. Alternatively, create an interactive simulation of a traffic-light
  controller or a simple protocol handler. The emphasis is on defining states,
  transitions, and events.

This shows how computation can be framed as controlled movement through a space of states.



### Integrating the Projects

You can also combine perspectives across projects:
- A compiler front end:
- lexical analysis as automata;
- syntax trees as algebraic data types;
- optimisation passes as functional decompositions;
- static analyses or type inference as relational rules.
- A miniature database system:
- relational queries for logic;
- structural mapping between input and output formats;
- automata controlling transaction states.
- A network protocol or embedded controller:
- automata for the protocol states;
- structural parsing of packets;
- functional transformations for routing or filtering.

Each of these gives you an opportunity to illustrate how perspectives can coexist
within a single system while each contributes something conceptually different.

