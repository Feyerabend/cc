
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

By the early 1990s, the idea of patterns in software had been circulating for years.
Developers had begun to notice that certain solutions kept reappearing, but these ideas
were still scattered, informal, and often difficult to communicate clearly.

Then, in 1994, four researchers brought structure to this growing body of knowledge.

Erich Gamma, Richard Helm, Ralph Johnson, and John Vlissides collaborated on a book that 
would fundamentally shape how developers think about design.

They later became known as the __Gang of Four__, or simply GoF.

Their book, Design Patterns: Elements of Reusable Object-Oriented Software, did something
subtle but powerful. It didn’t introduce entirely new ideas. Instead, it gave names,
structure, and clarity to solutions that many developers had already encountered.

Inside, they catalogued __23 design patterns for object-oriented systems__.

Each pattern captured a recurring problem, explained the context in which it appears,
and described a proven solution. More importantly, it provided a shared language.

Instead of explaining a solution from scratch, a developer could now say something like,
"this uses a factory," or "we apply an observer here," and others would immediately
understand the underlying structure.

__That was the real shift.__

Patterns were no longer just intuition or experience passed informally between developers.
They became documented knowledge. Transferable. Teachable. Reusable.

Where earlier developers had sensed the shapes that code tended to take, the Gang of Four
gave those shapes names—and in doing so, made them part of the foundation of modern software design.
 



### 3. Why the Book Was a Breakthrough


The influence of *Design Patterns: Elements of Reusable Object-Oriented Software*
was not in inventing something entirely new.

The patterns it described were already out there, discovered independently by developers
solving real problems. What the book did was something more fundamental.

It changed how that knowledge was captured, communicated, and applied.

First, it created a __catalog__.

Before the book, design knowledge lived mostly in experience. It was tacit, scattered
across teams, papers, and individual intuition. Developers often solved the same problems
without realizing others had already done the same.

The book gathered these recurring solutions into a structured collection.

Each pattern was described in a consistent way. Problem. Context. Solution. Consequences.

What had once been implicit became explicit.

And once something is explicit, it can be reused.

Second, it introduced a __shared vocabulary__.

This was one of its most immediate and lasting impacts.

Before, describing a design idea often meant explaining it from scratch. A developer
might say, "we need some object that notifies many others when its state changes,"
and then spend time walking through the mechanics.

After the book, that same idea could be expressed in a single phrase.

"Use an Observer pattern."

That single term carried with it an entire structure of relationships and behaviour.
Communication became faster, clearer, and less ambiguous. Teams could think at a higher
level because they no longer had to rebuild concepts from the ground up in every discussion.

Finally, it shifted attention __from coding to design__.

The book emphasized that writing software is not just about syntax or individual classes.
It is about how parts of a system fit together.

It encouraged developers to think in terms of relationships between objects, how systems
evolve over time, how components can be extended without breaking existing code,
and how to reduce tight coupling.

In other words, it pushed software engineering toward *architecture*.

Instead of focusing only on how to write code that works, developers were encouraged to
design systems that remain flexible, understandable, and resilient as they grow.

That shift, from implementation details to structural thinking, is what made the book enduring.



### 4. Structure of the Book

*Design Patterns: Elements of Reusable Object-Oriented Software* is not just a collection of patterns.
It is carefully structured to guide the reader from foundational ideas into practical application.

The book is divided into two main parts.

__Part I focuses on the principles of object-oriented design.__

Here, the authors lay the groundwork. They discuss how to think about objects, responsibilities,
and relationships. The emphasis is not on specific implementations, but on the underlying ideas
that make designs flexible, reusable, and maintainable.

It prepares the reader to understand not just what patterns are, but why they work.

__Part II contains the pattern catalog.__

This is the core of the book: 23 design patterns, each described in a consistent and methodical way.
Every pattern captures a recurring problem and presents a solution that has been proven in practice.

The structure makes it possible to move between patterns, compare them,
and understand how they relate to one another.

The examples throughout the book are primarily written in C++ and Smalltalk.

At the time, these were among the dominant object-oriented programming languages.
They provided a concrete way to illustrate abstract ideas, even though the patterns
themselves are not tied to any specific language.

That detail is important.

The patterns are meant to *transcend syntax*. The code examples serve only as a vehicle for expressing
deeper design concepts—concepts that can be applied in any language that supports object-oriented thinking.



### 5. The 23 GoF Design Patterns

In *Design Patterns: Elements of Reusable Object-Oriented Software*, the patterns are not presented as a flat list.
They are organised into three categories, each reflecting a different kind of design concern.

This organisation is not arbitrary. It mirrors the kinds of problems developers repeatedly encounter when building systems.

#### 5.1 Creational Patterns

Creational patterns deal with object creation.

At first glance, creating objects might seem trivial. But in larger systems, how objects are created has deep implications.
Tight coupling, inflexible code, and hidden dependencies often originate here.

These patterns abstract or hide the creation process, allowing systems to be more flexible and decoupled.

The creational patterns are:

* Abstract Factory
* Builder
* Factory Method
* Prototype
* Singleton

A simple example is the Factory Method.

The problem it addresses is straightforward: how do you create objects without hard-coding their exact class?

Instead of instantiating objects directly, the responsibility is delegated to subclasses. The system defines
an interface for creation, but allows derived classes to decide what concrete type is produced.

This introduces flexibility. Code can work with abstractions while deferring concrete decisions to specific contexts.

#### 5.2 Structural Patterns

Structural patterns focus on how classes and objects are composed.

As systems grow, the challenge is no longer just creating objects, but arranging them into larger structures
without making the design rigid or difficult to change.

These patterns provide ways to build complex structures while keeping them flexible and manageable.

The structural patterns are:

* Adapter
* Bridge
* Composite
* Decorator
* Facade
* Flyweight
* Proxy

A representative example is the Decorator.

Instead of modifying a class directly to add new behaviour, the decorator wraps the object and extends
its functionality dynamically. This avoids altering existing code while still enabling new features.

It reflects a broader principle: prefer composition over inheritance when extending behaviour.

#### 5.3 Behavioral Patterns

Behavioral patterns are concerned with communication between objects and the distribution of responsibilities.

In complex systems, the difficulty often lies not in the objects themselves, but in how they interact.
Poor communication structures can lead to tightly coupled systems that are hard to maintain or extend.

These patterns define clear ways for objects to collaborate while keeping them loosely coupled.

The behavioral patterns are:

* Chain of Responsibility
* Command
* Interpreter
* Iterator
* Mediator
* Memento
* Observer
* State
* Strategy
* Template Method
* Visitor

A classic example is the Observer.

Here, one object (the subject) maintains a list of dependents (observers) and notifies them
automatically when its state changes.

This pattern is widely used in user interface frameworks, where changes in data must be reflected
across multiple components without tightly binding them together.

Across all three categories, a common theme emerges.

The patterns are not about specific code. They are about shaping relationships—how objects are created,
how they are composed, and how they communicate.

That is what makes them enduring.


### 6. Design Philosophy of the GoF

Beyond the individual patterns, *Design Patterns: Elements of Reusable Object-Oriented Software*
promotes a set of underlying principles.

These ideas are quieter than the patterns themselves, but in many ways more important.
Patterns are applications of these principles. The principles are what guide good design in general.

__Program to interfaces, not implementations.__

This principle encourages developers to depend on abstractions rather than concrete classes.

Instead of tying code to a specific implementation, you define a contract.
The actual behaviour can then vary without affecting the rest of the system.

This reduces coupling and makes systems easier to extend. New implementations can be
introduced without rewriting existing code, as long as they respect the same interface.

__Favor composition over inheritance.__

Inheritance can be useful, but it often leads to rigid hierarchies that are difficult to change over time.

Instead of building deep class trees, this principle suggests composing objects from smaller, reusable parts.

Rather than:

```
class A extends B
```

you think in terms of:

```
A has a B
```

Composition allows behavior to be combined and modified dynamically. It leads to designs
that are more flexible and easier to evolve, especially as requirements change.

__Encapsulate what varies.__

In any system, some parts are stable while others are likely to change.

This principle encourages identifying those points of variation and isolating them.
By hiding or encapsulating what changes, the rest of the system can remain unaffected.

The result is code that is more robust in the face of change. Instead of changes
rippling through the system, they are contained within well-defined boundaries.

Taken together, these principles shift the focus from writing code that merely works
to designing systems that can adapt, grow, and remain understandable over time.


### 7. Immediate Impact (1990s)

The influence of Design Patterns: Elements of Reusable Object-Oriented Software was immediate and far-reaching.

The book sold over 100,000 copies and quickly established itself as a classic.
But its real impact cannot be measured in numbers alone. It changed how developers thought,
how they communicated, and how software was taught.

__It helped bring design patterns into the mainstream of programming.__

At the same time, the industry itself was undergoing a significant shift.

Object-oriented programming was moving from theory and niche use into the center of software development.
Systems were becoming larger, more complex, and more long-lived. The need for better design approaches was no longer optional.

Several languages were rising to prominence during this period:

* Java (Developed in the early 1990s and released in 1995 by James Gosling.)
* C++ (Developed by Bjarne Stroustrup in the early 1980s (first released around 1985). An 80s language.)
* Smalltalk (Developed in the 1970s at Xerox PARC, with major versions, like Smalltalk-80, around 1980.)
* Objective-C (Created in the early 1980s, ca 1984, by Brad Cox and Tom Love.)

These languages embraced object-oriented concepts, making them a natural fit for the ideas presented in the book.

As a result, the GoF patterns became standard teaching material.

They were incorporated into university courses, textbooks, and professional training.
Developers entering the field were no longer just learning syntax or algorithms.
They were learning how to think about structure, reuse, and communication at a higher level.

__The timing was critical.__

The book did not just introduce patterns—it arrived at a moment when the industry was ready for them.


### 8. Institutional Influence

The impact of *Design Patterns: Elements of Reusable Object-Oriented Software*
did not stop at individual developers or classrooms. It led to the emergence
of an entire ecosystem around patterns.

What began as a way of describing good design evolved into a community,
a body of literature, and a foundation for modern frameworks.

__Pattern conferences__

One of the clearest signs of this shift was the creation of dedicated conferences.

Pattern Languages of Programs, commonly known as PLoP, became a central meeting
place for both researchers and practitioners.

Here, patterns were not just consumed—they were discussed, refined, and expanded.
Participants would present new patterns, often drawn from real-world experience,
and subject them to collective scrutiny.

This process mirrored the original spirit of patterns: capturing solutions that had proven themselves in practice.

__Pattern literature__

Following the success of the original book, a vast body of pattern-oriented literature emerged.

Developers began documenting recurring solutions across many different domains.

This led to entire categories of pattern collections, such as:

* Enterprise patterns
* Concurrency patterns
* Distributed systems patterns
* Agile patterns
* Microservice patterns

Each of these extended the original idea: identifying common problems within a specific
context and describing solutions in a reusable, structured way.

Patterns were no longer limited to object-oriented design.
They became a general method for capturing engineering knowledge.

__Framework design__

Perhaps the most practical and widespread influence can be seen in software frameworks.

Many modern frameworks are built around the ideas popularised by the GoF patterns.
In some cases, they directly implement them. In others, the patterns are embedded more implicitly in the architecture.

Common examples include:

* MVC frameworks
* GUI toolkits
* Dependency injection frameworks

These frameworks do more than provide tools—they encode design decisions.
They guide developers toward certain structures and interactions,
often without requiring explicit knowledge of the underlying patterns.

In that sense, the ideas from the GoF book became part of the infrastructure of software development itself.

What started as a way to describe good design gradually became a way to standardise and distribute it.



### 9. Influence on Programming Languages

One of the most interesting long-term consequences of
*Design Patterns: Elements of Reusable Object-Oriented Software*
is how it indirectly shaped programming languages themselves.

Over time, many design patterns stopped being *patterns* in the original sense.

__They became built-in language features.__

This is a subtle but important shift. Patterns often exist to compensate for 
limitations in a language. When those limitations are removed, the pattern
becomes unnecessary--or at least less visible.

A number of well-known examples illustrate this transition:

* *Iterator --> foreach loops*
  Originally, the Iterator pattern provided a structured way to traverse
  collections without exposing their internal representation.
  Modern languages now include native iteration constructs, making this pattern largely implicit.

* *Strategy --> higher-order functions*
  The Strategy pattern encapsulates interchangeable behaviour.
  In languages with first-class functions, this can often be expressed directly by passing functions as values.

* *Singleton --> modules / static objects*
  The need to enforce a single instance can be handled at the language level
  through modules or static constructs, removing the need for explicit Singleton implementations.

* *Visitor --> pattern matching*
  Visitor was a way to perform operations across structured data without modifying the data types.
  Modern pattern matching features provide a more direct and expressive alternative.

* *Builder --> named parameters*
  Builder helped manage complex object construction with many optional parameters.
  Named and default parameters now address much of this problem more naturally.

| Pattern   | Modern language feature  |
|-----------|--------------------------|
| Iterator  | foreach loops            |
| Strategy  | higher-order functions   |
| Singleton | modules / static objects |
| Visitor   | pattern matching         |
| Builder   | named parameters         |


What this reveals is something deeper.

__Patterns often point to friction in a language.__

They show where developers are forced to build abstractions manually
because the language does not support them directly.

In that sense, __patterns act as signals__.

They highlight recurring problems strongly enough that language designers
eventually take notice. When a pattern becomes common enough, it may be absorbed into the language itself.

And when that happens, the pattern doesn’t disappear completely: it becomes invisible.

It turns from an explicit design decision into a natural part of how code is written.

This is why studying patterns remains valuable.

Even when specific patterns fade, the underlying insight remains:
they capture the boundary between what a language provides and what developers still need to build themselves.



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



### 13. Where GoF Stands Today

There is a certain way to read the *Design Patterns: Elements of Reusable Object-Oriented Software*
today that feels different from how it was read at its peak.
When it first spread through the industry, it was practical, almost tactical.
Developers reached for it as a toolbox. You needed flexibility? Use a Factory.
You needed communication between components? Try Observer. It was immediate,
concrete, and often applied quite literally.

__But time has a way of changing how books are used.__

Today, the GoF book feels less like a manual and more like a __foundation__.
Its role has shifted. It is still deeply important--but not always something
you follow line by line in everyday work. What remains, and what matters
 are not the individual patterns as rigid templates, but the ideas underneath them.

The book taught developers to see systems in terms of relationships
rather than just code. It emphasised that structure matters—that how
parts connect is just as important as what each part does.

Out of that came a set of principles that still quietly underpin modern software:
* __decoupling__, so that parts of a system can change without breaking everything else
* __abstraction__, so that complexity can be managed and hidden when necessary
* __composition__, so that behavior can be built by combining smaller pieces
  rather than inheriting rigid hierarchies
* __extensibility__, so that systems can evolve without constant rewriting

These are not tied to any specific language or era. You will find them in functional programming,
in microservices, in modern type systems, in UI frameworks--everywhere.
So while the patterns themselves may sometimes feel dated, or overly formal,
the shift they introduced has not faded. If anything, it has dissolved into the background.
You no longer need to name a pattern for it to shape your thinking. You no longer
need to implement it explicitly for its influence to be present. The language,
the frameworks, and the collective habits of developers now carry much of that weight.

And that is perhaps the clearest sign of something that has truly lasted:
*it stops feeling like a technique, and starts feeling like common sense*.



#### *What changed*


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
did not reject object-oriented ideas--they *absorbed and generalised them*.
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

