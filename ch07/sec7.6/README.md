
![GOF](./../assets/image/gof4.png)

[JHotDraw5.1](./../../ch06/addition/documentation/JHotDraw5.1/)

*There was a moment, roughly the mid-to-late 1990s into the early 2000s, when software engineering
felt like it had finally discovered its "architecture." Its golden calf. Not just code that worked,
but code that *made sense*. That moment revolved around three ideas that became deeply intertwined:
object-oriented programming, Java, and design patterns.*

*Object-oriented programming (OO) didn't begin there, of course. Its roots go back to languages like
Simula and later Smalltalk, where the idea was almost philosophical: model software as a collection
of interacting "objects," each with its own state and behaviour. But for years, this was more of an
academic curiosity than an industry standard.*

__Then the world changed.__

*As software systems grew, from small utilities into sprawling applications, developers began to struggle
with complexity. Codebases became tangled. Fixing one thing broke another. The promise of OO suddenly
felt practical: if you could model your system as cooperating objects, each responsible for its own
piece of the puzzle, maybe you could keep things understandable.*

__Enter Java.__

*When Java appeared in the mid-90s, it didn't just bring a new syntax. It arrived with a message:
write once, run anywhere. It offered a cleaner, safer alternative to C++, enforced object-oriented
structure more strictly, and removed many of the sharp edges that had made large systems fragile.
For many developers, Java was their first real immersion into OO thinking--not as theory,
but as daily practice.*

*And importantly, Java hit at exactly the right time. The web was exploding. Enterprises were investing
heavily in software. Suddenly, there was a massive demand for building large, maintainable systems--and
Java became one of the primary tools for doing it.*

*But even with OO and Java, a question remained*: how do you design systems well?

__That's where design patterns entered the story.__

*In 1994, four authors, often referred to as the "Gang of Four", published a book that would quietly
reshape how developers think: *Design Patterns: Elements of Reusable Object-Oriented Software*. What
they did was deceptively simple. They didn't invent new features or languages. Instead, they named
recurring solutions.*

__They gave developers a vocabulary.__

*Instead of vaguely describing "some object that creates other objects in a flexible way," you could
say __Factory__. Instead of explaining a complex subscription mechanism, you could say __Observer__.
These patterns captured hard-won experience and made it transferable.*

__And in the Java world, they spread like wildfire.__

*By the early 2000s, design patterns were everywhere. Books, conference talks, job interviews. Entire
frameworks were built around them. Learning Java often meant learning patterns alongside it--sometimes
even overusing them, as if every problem deserved a named solution.*

*Looking back, that era had a certain optimism. There was a belief that with the right abstractions,
the right patterns, and disciplined object-oriented design, software complexity could be tamed.*

*Reality, of course, turned out to be messier. Some patterns became overapplied. New paradigms--functional
programming, simpler architectures--pushed back against the heaviness that OO systems could accumulate.*

__But that doesn't diminish what that period achieved.__

* It gave developers a shared language for design.
* It made large-scale software development more systematic.
* And it shaped how we still think about structure, responsibility, and abstraction in code.

*Even today, when you see a well-factored class, a clean interface, or a familiar pattern quietly
doing its job, you're seeing echoes of that moment--when software engineering first felt like it
was becoming a true craft.*


### 1. Historical Origins of Design Patterns

In 1977, Christopher Alexander published *A Pattern Language*. He wasn’t writing about software at all.
He was trying to understand why some buildings, towns, and spaces simply *felt right*. Why they worked
for people in a way that went beyond blueprints.

His insight was deceptively simple: good design isn't invented from scratch every time. Instead,
it emerges from recurring solutions to recurring problems. A window placed to catch morning light.
A public square that naturally invites gathering. A doorway that creates a sense of transition.

He described each of these as a *pattern*. A structured idea consisting of three parts:
a problem, the context in which it appears, and a solution that has proven to work.

At the time, this had nothing to do with programming. But the idea lingered.

__Enter Software.__

A decade later, in a very different kind of construction site, software engineers were facing
their own version of the same struggle.

Systems were getting larger. Codebases were no longer small, self-contained programs--they were
evolving into complex, interconnected systems. And as object-oriented programming began to spread
in the late 1980s, it brought both promise and confusion.

OOP encouraged developers to think in terms of objects, responsibilities, and interactions.
It offered a way to model the world. But once people started building real systems, patterns
of difficulty began to emerge.

- How do you create objects without hard-coding dependencies everywhere?
- How do you decouple components so changes don’t ripple through the entire system?
- How do objects communicate without becoming tightly entangled?
- How do you represent hierarchies without making them rigid and brittle?

Different teams, in different places, kept running into the same kinds of problems.

And, quietly, they started discovering similar kinds of solutions.

__Patterns.__

At first, these solutions weren’t formalised. They lived in conversations, in research papers,
in shared intuition. A developer might say, "We solved this by introducing an intermediate object,"
or "We let one object notify others when something changes."

These ideas circulated informally, especially in academic and research environments where
object-oriented design was being explored more deeply. People began to recognise a pattern.
And not just in the code, but in the *solutions themselves*.

- The same problems.
- The same kinds of fixes.
- Appearing again and again.

__Applications.__

That's when Alexander's idea found new ground.

What if software design, like architecture, could be described through patterns?
What if these recurring solutions could be named, structured, and shared? What if
experience could be captured in a way that made it reusable?

The shift wasn’t dramatic at first. There was no single moment where everything changed.
But the perspective slowly took hold, that software wasn't just about writing instructions.
It was about shaping systems. And like buildings, those systems had forms that worked better than others.

By the end of the 1980s, the seeds were planted.
Developers didn’t just write code anymore.
They began to recognise the shapes that code tended to take.




### 2. The Gang of Four

The famous book was written by:

* Erich Gamma
* Richard Helm
* Ralph Johnson
* John Vlissides

They became known as the *Gang of Four (GoF)*.

Their book:

```
Design Patterns: Elements of Reusable Object-Oriented Software
```

published in *1994*.

The book catalogued *23 design patterns* for object-oriented systems. 



## 3. Why the Book Was a Breakthrough

The importance of the book was *not that it invented patterns*.

Instead, it did three crucial things.

#### 1. Cataloguing

It collected common design solutions into a *structured catalog*.

Before the book:

```
knowledge was tacit and scattered
```

After the book:

```
knowledge became explicit and reusable
```



#### 2. Vocabulary

One of the most profound effects:

It gave programmers a *shared language*.

Example conversation:

Before:

```
We need some object that notifies many observers when state changes.
```

After:

```
Use an Observer pattern.
```

A single word represented an entire design structure.



#### 3. Design over coding

The book emphasized:

```
software architecture matters more than syntax
```

It encouraged thinking about:

* object relationships
* extensibility
* reuse
* decoupling

This helped push *software engineering toward architectural thinking*. ([Software Patterns Lexicon][2])



## 4. Structure of the Book

The book is organized into:

```
Part I   Principles of object-oriented design
Part II  Pattern catalog (23 patterns)
```

The examples were mainly written in:

```
C++
Smalltalk
```

These were dominant OO languages at the time.



## 5. The 23 GoF Design Patterns

They are grouped into *three categories*.



## 5.1 Creational Patterns

Concerned with *object creation*.

They hide or abstract the creation process.

#### Patterns

```
Abstract Factory
Builder
Factory Method
Prototype
Singleton
```

#### Example: Factory Method

Problem:

```
Create objects without specifying exact class.
```

Solution:

```
Subclass decides what object is created.
```

([Wikipedia][3])



## 5.2 Structural Patterns

Concerned with *how classes and objects are composed*.

#### Patterns

```
Adapter
Bridge
Composite
Decorator
Facade
Flyweight
Proxy
```

Example:

```
Decorator -> add behavior without modifying class
```



## 5.3 Behavioral Patterns

Concerned with *object communication and responsibilities*.

#### Patterns

```
Chain of Responsibility
Command
Interpreter
Iterator
Mediator
Memento
Observer
State
Strategy
Template Method
Visitor
```

Example:

```
Observer
  subject -> notifies observers when state changes
```

Widely used in UI frameworks.



## 6. Design Philosophy of the GoF

The book promoted several important principles.

#### Program to interfaces

```
depend on abstractions
not concrete classes
```

#### Favor composition over inheritance

Instead of:

```
class A extends B
```

prefer:

```
A has a B
```

#### Encapsulate variation

Hide parts likely to change.



## 7. Immediate Impact (1990s)

The impact was massive.

The book:

* sold over 100,000 copies
* quickly became a classic
* helped bring patterns into mainstream programming.

At the same time, the software industry was transitioning to:

```
object-oriented programming
```

Languages rising during this period:

* Java
* C++
* Smalltalk
* Objective-C

The GoF patterns became *standard teaching material*.



## 8. Institutional Influence

The book led to an entire ecosystem:

#### Pattern conferences

PLoP:

```
Pattern Languages of Programs
```

Researchers and practitioners shared new patterns.



#### Pattern literature

Hundreds of books followed:

Examples:

```
Enterprise patterns
Concurrency patterns
Distributed systems patterns
Agile patterns
Microservice patterns
```



#### Framework design

Many frameworks embed GoF patterns.

Examples:

```
MVC frameworks
GUI toolkits
dependency injection frameworks
```



## 9. Influence on Programming Languages

One of the most interesting consequences:

*many design patterns later became language features.*

Examples:

| Pattern   | Modern language feature  |
|-----------|--------------------------|
| Iterator  | foreach loops            |
| Strategy  | higher-order functions   |
| Singleton | modules / static objects |
| Visitor   | pattern matching         |
| Builder   | named parameters         |

So patterns often reveal:

```
missing language features
```

When languages evolve, some patterns disappear.



## 10. Criticisms

Despite its importance, the GoF book also received criticism.



### 10.1 Pattern obsession

Some developers began writing code like:

```
pattern-first programming
```

Meaning:

```
"I must use a pattern"
```

Instead of:

```
"I must solve the problem simply"
```

This produced *over-engineered systems*.



### 10.2 OOP bias

The book assumes:

```
class-based object-oriented programming
```

Functional languages often don't need many patterns.

Example:

```
Visitor pattern
```

In functional languages:

```
algebraic data types + pattern matching
```

replace it naturally.



### 10.3 Language limitations

Many patterns exist only because languages lacked features.

Example:

```
Singleton
```

In modern languages:

```
module or static object
```

makes it unnecessary.



## 11. Influence on Software Engineering Thinking

Despite criticisms, the intellectual influence is enormous.

The book helped establish several ideas.



#### Software architecture as a discipline

Before:

```
coding dominated thinking
```

After:

```
architecture became a first-class concept
```



#### Knowledge sharing

Patterns capture *expert knowledge*.

Instead of reinventing solutions.



#### Design vocabulary

Today terms like:

```
Observer
Factory
Strategy
Decorator
```

are universal.



## 12. Evolution After GoF

After 1994 the pattern idea expanded.

Important domains include:

#### Enterprise architecture

Martin Fowler:

```
Patterns of Enterprise Application Architecture
```

Examples:

```
Repository
Unit of Work
Data Mapper
```



#### Distributed systems

Examples:

```
Circuit Breaker
Saga
Event Sourcing
CQRS
```



#### Microservices

Modern architecture patterns for cloud systems.



## 13. Where GoF Stands Today

The GoF book is now *historically foundational but not always practical*.

Think of it like:

```
Euclid's Elements for software architecture
```

Important for understanding concepts.

But not necessarily used literally every day.



### What remains essential

The *principles* remain crucial:

```
decoupling
abstraction
composition
extensibility
```

These ideas underpin modern architecture.



### What changed


__a.) Object Creation -> Factory Pattern vs Language Features__

In classic OO, object creation was often wrapped in patterns like *Factory* to avoid tight coupling.


Old Java-style Factory:

```java
interface Shape {
    void draw();
}

class Circle implements Shape {
    public void draw() { System.out.println("Circle"); }
}

class ShapeFactory {
    static Shape create(String type) {
        if (type.equals("circle")) {
            return new Circle();
        }
        throw new IllegalArgumentException();
    }
}
```

This solves a real problem: avoiding direct dependencies on concrete classes.


__Modern Kotlin / Scala__

You often don't need a factory at all:

```kotlin
sealed interface Shape

data class Circle(val radius: Double) : Shape

fun createShape(type: String): Shape = when (type) {
    "circle" -> Circle(1.0)
    else -> error("Unknown")
}
```

Or even more directly, you pass constructors/functions:

```kotlin
val creator: () -> Shape = { Circle(1.0) }
```

What changed?
* First-class functions replace factories
* Sealed types give controlled hierarchies
* Pattern matching replaces manual branching

The *intent* of Factory is still there--but the ceremony is gone.



__b.) Strategy Pattern -> Functions as Values__


Classic OO Strategy in Java:
```java
interface SortStrategy {
    void sort(List<Integer> list);
}

class QuickSort implements SortStrategy {
    public void sort(List<Integer> list) { /* ... */ }
}

class Context {
    private SortStrategy strategy;

    Context(SortStrategy strategy) {
        this.strategy = strategy;
    }

    void execute(List<Integer> list) {
        strategy.sort(list);
    }
}
```



__Modern Scala / Kotlin / Swift__

```kotlin
fun execute(list: List<Int>, strategy: (List<Int>) -> List<Int>) {
    strategy(list)
}

val quickSort = { l: List<Int> -> l.sorted() }

execute(listOf(3,1,2), quickSort)
```

What changed?
* Functions are first-class citizens
* No need for interfaces + classes + wiring

The *Strategy pattern collapses into a function parameter.*



__c.) Observer Pattern -> Reactive / Built-in Constructs__

Classic Observer in Java:
```java
interface Observer {
    void update(String data);
}

class Subject {
    private List<Observer> observers = new ArrayList<>();

    void subscribe(Observer o) {
        observers.add(o);
    }

    void notifyAll(String data) {
        for (Observer o : observers) {
            o.update(data);
        }
    }
}
```



__Kotlin / Swift (simplified reactive style)__

```kotlin
val listeners = mutableListOf<(String) -> Unit>()

fun subscribe(listener: (String) -> Unit) {
    listeners += listener
}

fun notifyAll(data: String) {
    listeners.forEach { it(data) }
}
```

Or in more advanced systems (e.g. flows, streams):

```kotlin
val flow = MutableStateFlow("")

flow.collect { println(it) }
flow.value = "new data"
```

What changed?
* Built-in reactive abstractions
* Language + libraries model data flow directly

Observer becomes *part of the ecosystem*, not a pattern you manually implement.



__d.) Null Handling -> Option / Maybe Types__

A major pain in classic OO:
```java
String name = getUser();
if (name != null) {
    System.out.println(name.length());
}
```


__Modern languages (Rust, Scala, Kotlin)__

```kotlin
val name: String? = getUser()
println(name?.length)
```

Or Rust:

```rust
fn print_len(name: Option<String>) {
    if let Some(n) = name {
        println!("{}", n.len());
    }
}
```

What changed?
* Null handling becomes part of the type system
* Eliminates entire classes of bugs

This replaces many defensive patterns with *language guarantees*.



__e.) Immutability -> No Need for Defensive Patterns__

Older OO often required defensive copying:
```java
class Person {
    private final List<String> items;

    Person(List<String> items) {
        this.items = new ArrayList<>(items);
    }
}
```


__Modern (e.g. Haskell / Scala / Rust)__

```scala
case class Person(items: List[String])
```

or Rust:

```rust
struct Person {
    items: Vec<String>,
}
```

But immutability (especially in functional languages like Haskell) is the default.

What changed?
* Immutability is enforced or encouraged
* No need for defensive design patterns


 
__f.) Algebraic Data Types -> Replace Complex Hierarchies__

In classic OO, representing variants required inheritance:
```java
abstract class Shape {}

class Circle extends Shape {}
class Rectangle extends Shape {}
```


__Modern (Scala / Rust / Haskell)__

```rust
enum Shape {
    Circle(f64),
    Rectangle(f64, f64),
}
```

What changed?
* Data + variants are modeled directly
* Pattern matching replaces polymorphic dispatch

This removes the need for certain Visitor-like patterns.


__So What Happened?__

Languages like Scala, Rust, Haskell, Kotlin, or Swift
did not reject object-oriented ideas—they *absorbed and generalised them*.
They took recurring patterns and asked:
"Why is this a pattern instead of a language feature?"
And then they encoded those ideas directly into: type systems, function semantics,
pattern matching, immutability, and concurrency models.

This is evolution. For early OO you *manually encode structure* using patterns.
But modern languages *encodes the structure for you*.
So patterns didn’t disappear. Rather, they became invisible.
And that’s actually their greatest success.


### 14. Insights from the Book

If you look closely, the most important idea behind patterns is not technical at all. It's "philosophical".

For a long time, software engineering leaned toward the algorithmic mindset. Problems were things you *solved*:
with logic, with mathematics, with correctness proofs. The focus was on deriving the right answer, the optimal
procedure, the cleanest computation.

*Patterns quietly shifted that perspective.*

They suggested that not all knowledge in software comes from deduction. Some of it comes from experience.
Not just your own experience, but the accumulated experience of many developers, across many systems, over time.
Instead of asking, "What is the correct algorithm?" patterns ask a different kind of question:
What has worked before, in situations like this? That is a fundamentally empirical stance.
It treats software design less like solving a theorem and more like practicing a craft. You observe.
You try. You fail. You refine. And eventually, certain structures keep reappearing. Not because they are
proven optimal, but because they are *reliably useful*.

A pattern, then, is not just a clever trick. It is a distillation of repeated success.

This is the real shift: design knowledge can be reused, not just code.
Code reuse had always been the obvious goal. Libraries, functions, modules. Take something that works
and plug it in somewhere else.
But patterns operate at a different level. They don’t give you finished components.
They give you *ways of thinking*, *ways of structuring*, *ways of approaching problems*.

They encode things that are harder to write down:

* when a certain structure becomes necessary
* how responsibilities tend to distribute themselves
* where complexity tends to accumulate
* how systems tend to break if designed poorly

In that sense, patterns are closer to *case studies* than formulas.

And importantly, they carry with them a kind of humility.
They don't claim: "this is the best solution."
They suggest: "this has worked, many times, under these conditions."
That distinction matters.
It leaves room for judgment. For context. For variation. It acknowledges that software systems
are not identical, and that design is rarely about applying a rule blindly.


Seen this way, patterns are less about prescribing structure and more about preserving memory.
They are fragments of collective experience, gathered from thousands of systems, compressed into
forms that can be shared. Not to eliminate thinking, but to guide it--to give developers a starting
point that is informed by what came before.

And that may be their most enduring contribution: they remind us that building software is not
just an exercise in logic, but an ongoing conversation with experience.



### 15. The Legacy


When *Design Patterns: Elements of Reusable Object-Oriented Software* appeared,
it didn't just catalog clever techniques--it changed how developers *saw* their work.
Over time, its influence crystallised:

* pattern-based thinking
* a stronger culture around software architecture
* a shared vocabulary for design discussions
* the foundation for many frameworks and libraries

Even today, you can hear echoes of it in everyday conversations: "this is basically an Observer,"
or "we should hide that behind a Factory." The specific patterns may come and go. Some feel
heavy or outdated, but the deeper shift remains. Developers learned to recognise structure,
to reason about systems at a higher level than individual lines of code.

That comparison, to architecture, is more than a historical curiosity.
It reveals something fundamental about how technology evolves.


### 16. The Context and Evolution

Technology does not grow in a vacuum.

Object-oriented programming did not rise purely because it was elegant.
Java did not succeed solely because it was well-designed. Design patterns
did not spread just because they were insightful.

__They all emerged within a particular context.__

There was a growing need to manage large, complex systems. There were organisations
investing heavily in long-lived software. There was an industry searching for
discipline Something that could make software development feel less like improvisation,
and more like engineering.

In that environment, patterns made sense. They offered stability, shared understanding,
and a way to transfer experience across teams and projects. They fit the moment.

__But the same context that enables an idea can also shape its limitations.__

Patterns, in some cases, became overused--applied mechanically rather than thoughtfully.
Systems grew layered and abstracted to the point of heaviness. What began as a way to
manage complexity sometimes *introduced* new forms of it. The surrounding forces--enterprise
needs, tooling, education, even hiring practices--amplified both the strengths and the weaknesses.

That is the quiet cautionary tale: *good ideas do not exist independently of the environment
that adopts them*. They are interpreted, stretched, and sometimes distorted by it.


### 17. The Lessons

__That lesson feels especially relevant today.__

Consider the rapid rise of AI systems. Their technical foundations are impressive,
but their trajectory is shaped just as much by context:

* large technology companies driving development and deployment
* economic incentives favoring scale, speed, and market dominance
* expectations from users, investors, and society about what AI *should* do
* the availability of massive datasets and computing infrastructure
* cultural narratives about automation, intelligence, and progress

These forces don't just influence how AI is used: they influence what gets built in
the first place, how it is evaluated, and what trade-offs are considered acceptable.

__In other words, AI is not just a technological phenomenon. It is a socio-technical one.__

Looking back at the rise of design patterns, we can see both inspiration and warning.

The inspiration is clear: capturing and sharing knowledge can elevate an entire field.
It can give practitioners a language, a sense of structure, and a way to build on each
other's work.

The warning is quieter: once ideas enter a larger system--organisations, markets,
expectations--they evolve in ways that are not always intentional.

*The comparison is revealing because it reminds us that programming is not just about code.
It is about the conditions under which code is written, the forces that shape decisions,
and the assumptions that quietly become standard practice.*

__And those conditions are always changing.__

