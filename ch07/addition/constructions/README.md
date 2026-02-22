
## Programming Language Constructions

Programming languages are not neutral tools; they reflect underlying theories of computation and
design philosophies. The constructions that a language emphasises--such as recursion, monads,
inheritance, or pattern matching--are deliberate choices that guide how programmers conceptualise
and solve problems.

For example, Haskell encourages recursion and pure functions, reflecting a foundation in lambda
calculus and category theory, where functions are transformations without mutable state. In
contrast, imperative languages like C prioritise explicit loops and mutable variables, aligning
with the von Neumann architecture and a view of programs as sequences of state changes.

Similarly, Haskell enforces explicit handling of side effects via monads, making the boundary
between pure and impure computations clear. In languages like Python or Java, side effects can
appear anywhere without explicit markers, placing the responsibility on the programmer to manage
them carefully.

These contrasts illustrate that programming languages encode theoretical commitments, influencing
the patterns of reasoning they support and the constructions they make convenient. Awareness of
these commitments helps programmers understand not just how to use a language,
but why it works the way it does.

| Language     | Constructions                                                                    |
|--------------|----------------------------------------------------------------------------------|
| C            | Mutable vars, loops, conditionals, explicit control flow, procedures             |
| C++          | Classes, inheritance, generics, composition, threads, locks, functions           |
| Java         | Classes, inheritance, interfaces, polymorphism, threads, futures, generics       |
| C#           | Classes, inheritance, LINQ (map/filter), events, delegates, async/await          |
| Python       | First-class funcs, OO (classes), dynamic typing, list comprehensions, decorators |
| Haskell      | Pure functions, ADTs, pattern matching, lazy evaluation, monads, type inference  |
| Scala        | Pure functions, pattern matching, traits (mixins), monads, generics              |
| JavaScript   | First-class funcs, closures, event loop, callbacks, promises, async/await        |
| Erlang       | Message passing, recursion, immutable state, pattern matching, processes         |
| Go           | Goroutines, channels, static typing, explicit control flow                       |
| Rust         | Ownership, pattern matching, ADTs, threads, generics, safe concurrency           |
| Prolog       | Facts, rules, queries, unification, backtracking                                 | 
| SQL          | Queries, constraints, rules, declarative relations                               |
| Forth        | Stack-based execution, postfix notation, small reusable combinators              |
| Elm          | Pure functions, pattern matching, ADTs, subscriptions, signals                   |
| AspectJ      | Aspects, join points, advice, weaving, cross-cutting concerns                    |


#### Learning a Language

One effective approach to learning a *new-to-you* programming language is to first study the
*programming constructions and abstractions* it supports, before delving into its concrete
syntax and language-specific details. By understanding the kinds of operations, control structures,
data abstractions, and paradigms that the language emphasises, you can better grasp *how* the
language is intended to be used and *why* certain patterns or idioms are common. Once you are
familiar with these underlying constructions, learning the actual syntax becomes a process
of mapping familiar concepts to their syntactic representations, rather than trying to memorise
isolated language rules without context. This strategy accelerates both comprehension and
practical fluency. But this approach is most beneficial when you are already confident in one or
several languages.

Most books and learning courses do not adopt this construction-first approach. Instead, they
typically begin with the *syntax* of the language, introducing variables, control structures,
and basic input/output in a bottom-up fashion. This method has clear benefits: it provides
immediate, tangible feedback, allowing learners to quickly write simple programs and gain
familiarity with how to express operations concretely. By starting with syntax, learners can
build confidence through hands-on experimentation and see quick results, which helps maintain
motivation in the early stages. Furthermore, for languages where syntax and semantics are
tightly coupled (such as C or Python), early exposure to syntax can give an implicit
understanding of some language behaviors even before formal abstractions are introduced.

Taken together, both approaches have complementary strengths. Starting with *constructions*
builds a deeper conceptual foundation and prepares you to recognise patterns across different
languages, while starting with *syntax* offers faster practical engagement and a smoother
entry into writing runnable code. Ideally, an effective learning process balances both--alternating
between abstract understanding and concrete application to reinforce both perspectives simultaneously.


### Constructions in Relation to Models / Paradigms

| Paradigm / Model          | Construction                                    |
|---------------------------|-------------------------------------------------|
| Imperative                | Mutable variables (1)                           |
|                           | Assignment statements (2)                       |
|                           | Sequence of statements (3)                      |
|                           | Loops (4)                                       |
|                           | Conditionals (5)                                |
|                           | Function/procedure calls (6)                    |
|                           | Explicit control flow* (3, 7)                   |
|                           | Side effects (8)                                |
|                           | Procedure abstraction (9)                       |
| Functional                | First-class functions* (10)                     |
|                           | Higher-order functions* (10)                    |
|                           | Pure functions* (11)                            |
|                           | Immutability* (12)                              |
|                           | Recursion* (13)                                 |
|                           | Lazy evaluation (14)                            |
|                           | Closures* (10)                                  |
|                           | Currying (15)                                   |
|                           | Partial application (16)                        |
|                           | Algebraic data types (ADTs)* (17)               |
|                           | Pattern matching* (17)                          |
|                           | Type inference (18)                             |
|                           | Parametric polymorphism (generics)* (19)        |
|                           | Monads (20)                                     |
|                           | Functors (21)                                   |
|                           | Applicatives (22)                               |
|                           | Tail call optimisation (23)                     |
| Object-Oriented           | Classes and objects (24)                        |
|                           | Encapsulation* (25)                             |
|                           | Inheritance (26)                                |
|                           | Polymorphism (subtype) (27)                     |
|                           | Method overriding (28)                          |
|                           | Method overloading (29)                         |
|                           | Constructors/destructors (30)                   |
|                           | Interfaces / Abstract classes (31)              |
|                           | Access modifiers (32)                           |
|                           | Composition (33)                                |
|                           | Generics* (19)                                  |
|                           | Static methods / Static variables (34)          |
|                           | Mixins / Traits (35)                            |
| Event-Driven              | Event loops (36)                                |
|                           | Event handlers (37)                             |
|                           | Callbacks* (38)                                 |
|                           | Asynchronous execution* (39)                    |
|                           | Observer pattern* (40)                          |
|                           | Signals and slots (41)                          |
|                           | Publish/subscribe pattern* (40)                 |
|                           | State machines* (42)                            |
| Concurrent                | Threads (43)                                    |
|                           | Processes (44)                                  |
|                           | Locks (45)                                      |
|                           | Semaphores (46)                                 |
|                           | Monitors (47)                                   |
|                           | Atomic operations (48)                          |
|                           | Message passing* (49)                           |
|                           | Futures / Promises* (50)                        |
|                           | Parallelism (51)                                |
|                           | Barriers (52)                                   |
|                           | Condition variables (53)                        |
|                           | Thread pools (54)                               |
|                           | Software transactional memory (55)              |
| Concatenative             | Stack-based execution (56)                      |
|                           | Postfix notation (57)                           |
|                           | Function composition* (10)                      |
|                           | Point-free style (58)                           |
|                           | Implicit argument passing (59)                  |
|                           | Small reusable combinators (60)                 |
|                           | Lack of named variables (61)                    |
| Logic                     | Facts (62)                                      |
|                           | Rules* (63)                                     |
|                           | Queries (64)                                    |
|                           | Unification (65)                                |
|                           | Backtracking (66)                               |
|                           | Cut operator (67)                               |
|                           | Definite clause grammars (68)                   |
|                           | Meta-programming (69)                           |
| Procedural                | Procedures (9)                                  |
|                           | Control structures (loops, conditionals)* (4,5) |
|                           | Modularisation (70)                             |
|                           | Call stack (71)                                 |
|                           | Pass-by-value / Pass-by-reference (72)          |
|                           | Static/global variables (73)                    |
|                           | Explicit sequencing* (3,7)                      |
| Declarative               | Pattern matching* (17)                          |
|                           | Constraints (74)                                |
|                           | Rules* (63)                                     |
|                           | SQL-style queries (75)                          |
|                           | Functional relations* (76)                      |
|                           | Property declarations (77)                      |
|                           | Comprehensions (78)                             |
| Reactive                  | Data streams (79)                               |
|                           | Observers/subscribers* (40)                     |
|                           | Push-based updates (80)                         |
|                           | Backpressure (81)                               |
|                           | Observable sequences (82)                       |
|                           | Operators (map, filter, merge, zip)* (83)       |
|                           | Hot vs cold observables (84)                    |
|                           | Reactive extensions (Rx) (85)                   |
|                           | Event emitters (86)                             |
| Aspect-Oriented           | Aspects (87)                                    |
|                           | Join points (88)                                |
|                           | Pointcuts (89)                                  |
|                           | Advice (before, after, around) (90)             |
|                           | Weaving (91)                                    |
|                           | Cross-cutting concerns (92)                     |
|                           | Interceptors / Decorators* (93)                 |

#### Common constructions

Features appearing across multiple paradigms:

- *(10)* First-class functions, higher-order functions, closures, function composition:  
  FP, Concatenative, Event-driven, Reactive --> Encourages abstraction and reuse

- *(13, 17)* Recursion, pattern matching, ADT (Algebraic data types):  
  FP, Declarative, Logic --> Strengthens declarative & structural expression

- *(38, 39, 40)* Callbacks, asynchronous execution, observers/subscribers:  
  Event-driven, Reactive, Concurrent --> Drives concurrency and reactive data flow

- *(3, 4, 5, 7)* Explicit control flow, procedures, control structures (loops/conditionals):  
  Imperative, Procedural --> Enables low-level control

- *(19)* Generics / Parametric polymorphism:  
  FP, OO --> Boosts type abstraction and reusable code

- *(40)* Observer pattern, publish/subscribe pattern:  
  Event-driven, Reactive --> Enables decoupled event propagation

- *(49, 50)* Message passing, futures/promises:  
  Concurrent, Event-driven --> Supports safe concurrency models

- *(93)* Interceptors / Decorators:  
  AOP, OO, FP --> Allows cross-cutting or extensible behavior injection

Implications:
- Functional + Declarative + Logic share many data-centric and structural abstractions --> good for reasoning and correctness
- Event-driven + Reactive + Concurrent share many asynchronous and event-based mechanisms --> good for scalability and responsiveness
- OO + FP increasingly blend via generics, higher-order functions, immutability --> modern multiparadigm languages exploit both
- Procedural + Imperative is often the "baseline" for control flow, extended by most paradigms


#### Examples

1. First-class functions / Higher-order functions (10)
2. Threads (Concurrent) — (43)


__Example 1__

*Concept*: Functions can be passed as arguments, returned from other
functions, and assigned to variables--just like data.

Python
```python
def square(x):
    return x * x

def apply_function(f, value):
    return f(value)

result = apply_function(square, 5)
print(result)
```

C
```c
#include <stdio.h>

int square(int x) {
    return x * x;
}

int apply_function(int (*func)(int), int value) {
    return func(value);
}

int main() {
    int result = apply_function(square, 5);
    printf("%d\n", result);
    return 0;
}
```

*Construction*: First-class functions enable abstraction over
behaviour--we pass functions as arguments to generalise computation patterns.


__Example 2__

*Concept*: Concurrent execution of multiple flows of control.

C (POSIX threads)

```c
#include <stdio.h>
#include <pthread.h>

void* say_hello(void* arg) {
    printf("Hello from thread!\n");
    return NULL;
}

int main() {
    pthread_t t;
    pthread_create(&t, NULL, say_hello, NULL);
    pthread_join(t, NULL);
    printf("Back in main thread.\n");
    return 0;
}
```

Python (threading)

```python
import threading

def say_hello():
    print("Hello from thread!")

t = threading.Thread(target=say_hello)
t.start()
t.join()
print("Back in main thread.")
```

*Construction*: Threads allow explicit concurrent execution: two (or more) flows of control in parallel.



### Projects

If you want to engage directly with how theoretical commitments shape programming languages,
there are several practical projects you can undertake. Each project forces you to make explicit
choices about which constructions you favour and why.


- *Design and implement a small programming language*  

  Building your own language naturally leads you to decide whether to emphasize constructions
  like recursion, mutable state, pattern matching, or message passing. You will make concrete
  design choices that reflect your theoretical preferences.


- *Implement a minimalist interpreter or virtual machine*  

  Even a simple interpreter for arithmetic expressions or stack-based operations will highlight
  how different control flow models (e.g. explicit loops vs recursion) shape language behavior.


- *Transpile code between paradigms*  

  Write a tool that translates between two languages or paradigms (e.g. from imperative to
  functional style). This will expose where constructions align or conflict and force you to
  understand their theoretical underpinnings.


- *Extend an existing language with a new feature*  

  Adding pattern matching, coroutines, or a type system extension to an existing interpreter
  (like a Lisp or Python subset) will show how constructions integrate into a broader system.


- *Compare idiomatic solutions across languages*  

  Choose one problem (such as file I/O, tree traversal, concurrency) and solve it idiomatically
  in different languages and paradigms. This reveals how constructions shape thinking and code
  organization.


- *Implement a language feature from theory*  

  Build concrete implementations of constructs like monads, continuations, backtracking, or
  actor models in a general-purpose language. This gives hands-on understanding of theoretical
  concepts.


These projects are manageable: if scoped carefully. They not only develop technical skill but
also deepen your understanding of how language design shapes program structure and reasoning.


### Extended Project

*Cross-language Programming Constructions Catalog*

Build a practical catalog that demonstrates fundamental language constructions
across multiple paradigms and languages.

Structure
- Each construction is documented with:
- A conceptual explanation (what it is, why it matters)
- Minimal working code examples in 2–3 languages (starting with C and Python)
- Comparative commentary (how it differs / is expressed differently in the languages)

#### Scope (Phase 1)

Pick 8–12 constructions that cover core paradigms
(Small enough to finish, broad enough to be useful)

Suggested initial constructions:

| Construction         | Paradigm               | Notes                       |
|----------------------|------------------------|-----------------------------|
| Mutable variables    | Imperative             | Foundational                |
| Loops                | Imperative             | Common control structure    |
| First-class functions| Functional             | Highlights abstraction      |
| Recursion            | Functional             | Alternative to loops        |
| Classes/objects      | Object-Oriented (OOP)  | Encapsulation / modeling    |
| Threads              | Concurrent             | Explicit concurrency        |
| Event handlers       | Event-driven           | Input/output responsiveness |
| Pattern matching     | Functional / Declarative | Structural decomposition  |


__Output Format (GitHub-friendly)__

One construction = one Markdown file
Folder structure something like:

```
/catalog/
    /01_mutable_variables/
        CONCEPT.md
        example.c
        example.py
    /02_loops/
        ..
```

'CONCEPT.md' contains:
- Definition
- Why important
- Examples in C/Python
- Commentary (language contrasts)


Benefits:
- Systematic, reusable reference for learners and teachers: Share
- Forces deep understanding of core cross-language ideas
- Clean project for GitHub portfolio (shows clarity, pedagogy, breadth)


__Possible extensions (Phase 2)__

- Add more languages (e.g. JavaScript, Haskell, Rust)
- Add unit tests / demo apps for each example
- Build interactive docs / web version later


### Reference

*	Sebesta, Robert W. (2016). *Concepts of Programming Languages*.
* Sethi, R. (1996). *Programming languages: Concepts and constructs* (2nd ed.). Addison-Wesley.

