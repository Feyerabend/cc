
![GOF](./../assets/image/gof4.png)

[JHotDraw5.1](./../../ch06/addition/documentation/JHotDraw5.1/)


### Design Patterns

There was a moment in the mid-to-late 1990s and early 2000s when software
engineering began to feel like it had found a stable conceptual center.
Object-oriented programming had moved from academic origin into industrial
practice, Java had become a dominant language, and design patterns were
introduced as a way of naming recurring solutions in software structure.

Object-oriented programming itself began earlier, in systems such as Simula
and Smalltalk, where software was described as interacting objects with
state and behavior. For a long time, this remained closer to an academic
model than an industrial standard.

As systems grew, a structural problem emerged: local correctness was no
longer sufficient. Changes in one part of a system began to affect unrelated
parts. Object-oriented design became attractive because it allowed systems
to be decomposed into interacting units, each responsible for a bounded
part of behaviour.

Java arrived into this environment. It enforced object-oriented structure
more strictly than earlier mainstream languages, reduced low-level complexity,
and introduced platform independence as a practical feature. At the same time,
the industry was expanding rapidly due to enterprise systems and the rise
of the web, making large-scale maintainability a central concern.

__It was in this environment that design patterns became meaningful.__

The key idea behind design patterns was not invention, but recognition.
Developers were already solving the same structural problems repeatedly,
but without shared terminology.

This can be seen in a simple recurring problem: __object creation without tight coupling.__

Instead of directly constructing concrete implementations everywhere,
systems often introduce an indirection layer:

```java id="factory-java"
interface Shape {
    void draw();
}

class Circle implements Shape {
    public void draw() {
        System.out.println("Circle");
    }
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

This structure became known as a Factory. Its purpose is not the code itself,
but the separation between *what is requested* and *what is constructed*.

The same structural need appears again later in different form when languages evolve:

```kotlin id="factory-modern"
sealed interface Shape

data class Circle(val radius: Double) : Shape

fun createShape(type: String): Shape = when (type) {
    "circle" -> Circle(1.0)
    else -> error("Unknown type")
}
```

Here the same idea remains—controlled construction—but the mechanism shifts.
The language now provides algebraic data types and pattern matching, reducing
the need for explicit factory structures.

A similar transformation appears in behavioral composition. The Strategy
pattern originally expresses interchangeable behavior through objects:

```java id="strategy-java"
interface SortStrategy {
    void sort(List<Integer> list);
}

class QuickSort implements SortStrategy {
    public void sort(List<Integer> list) {
        // sorting logic
    }
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

The same structure later becomes direct function passing:

```kotlin id="strategy-modern"
fun execute(list: List<Int>, strategy: (List<Int>) -> List<Int>) {
    strategy(list)
}

val quickSort = { l: List<Int> -> l.sorted() }
```

What changes is not the intent but the representation. The abstraction
that once required class hierarchies becomes a first-class function.

Communication between components shows a similar pattern. The Observer
structure originally requires explicit subscription management:

```java id="observer-java"
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

This evolves into direct function-based event handling:

```kotlin id="observer-modern"
val listeners = mutableListOf<(String) -> Unit>()

fun subscribe(listener: (String) -> Unit) {
    listeners += listener
}

fun notifyAll(data: String) {
    listeners.forEach { it(data) }
}
```

In more advanced systems, this structure disappears entirely into
reactive streams, where subscription and propagation are handled
by the runtime rather than manually encoded.

A similar shift occurs in the handling of missing values. In early
object-oriented systems, null checks are manual:

```java id="null-java"
String name = getUser();
if (name != null) {
    System.out.println(name.length());
}
```

Later, optional types encode the possibility of absence explicitly:

```kotlin id="null-modern"
val name: String? = getUser()
println(name?.length)
```

In strongly typed systems like Rust, absence becomes part of the type itself:

```rust id="null-rust"
fn print_len(name: Option<String>) {
    if let Some(n) = name {
        println!("{}", n.len());
    }
}
```

At this stage, the absence of a value is no longer a convention but a structural guarantee.

Data modeling follows a similar trajectory. Traditional inheritance-based hierarchies:

```java id="adt-java"
abstract class Shape {}

class Circle extends Shape {}
class Rectangle extends Shape {}
```

are replaced by algebraic data types:

```rust id="adt-rust"
enum Shape {
    Circle(f64),
    Rectangle(f64, f64),
}
```

The structure becomes explicit at the type level rather than
distributed across inheritance trees.

Across all of these cases, the same pattern appears: structures
that once had to be manually encoded in object-oriented systems
gradually move into language features and then into type system
guarantees.

This shift explains why design patterns became less visible over
time. Many of them describe solutions to constraints that modern
languages no longer impose.

Originally, patterns captured recurring structural needs in systems
where those needs had no direct language support. As languages
evolved, those needs were absorbed into core constructs: functions,
algebraic types, pattern matching, and type safety.

The consequence is not that the ideas disappeared, but that their
implementation moved downward—from application code into language
design itself.

This also changes how software design is understood. Earlier development
required explicit construction of structure through patterns.
Later systems express much of that structure directly, reducing
the need for external architectural scaffolding.

What remains consistent is the underlying observation: software systems
repeatedly generate similar structural problems, and those structures
can be recognised and reused. The difference lies in where that
structure is represented.

In early systems, structure is built manually. In intermediate systems,
structure is expressed through language features. In modern systems,
structure is enforced through types and runtime models.

Design patterns sit at the transition point between these phases.
They document the intermediate stage where structure still had
to be expressed explicitly.

The long-term result is that many of the ideas from the Gang of Four
persist, but not as named patterns. They persist as language capabilities
and default design expectations.

What remains from that period is not a fixed catalog of solutions,
but a way of seeing software as structure rather than only as instructions.



### The Critique

The evolution of design patterns into language features created a powerful
shift in how software structure is understood, but it also introduced a
subtle distortion: *the idea that all complexity in software can or should
be framed as structured object interaction.*

This assumption holds reasonably well in classical object-oriented systems,
but begins to weaken once we move outside that domain. In languages that
are not centered on objects—such as C, Python, or JavaScript—the same
problems exist, but the “pattern-first” framing often becomes unnecessary
or even misleading.

A useful starting point is C, where there is no object model at all.
Consider a simple resource management problem: opening and closing a file.
In a pattern-oriented OO framing, this might be described in terms of
objects, lifecycles, and encapsulated responsibilities.
In C, the structure is far more direct:

```c id="c-file-basic"
FILE *f = fopen("data.txt", "r");

if (f != NULL) {
    char buffer[256];
    fgets(buffer, sizeof(buffer), f);
    fclose(f);
}
```

There is no Factory, no Strategy, no Observer structure here.
The program simply expresses sequencing and ownership explicitly.
If one attempts to force a pattern vocabulary onto this code,
it becomes artificial rather than clarifying. The concept of
"encapsulating creation" or "abstracting behaviour" exists,
but it is not naturally represented as a reusable pattern
structure--it is just procedural control flow.

This reveals the first limitation: patterns often emerge as
*compensations for abstraction-heavy environments*,
not as universal truths about computation.

The same issue appears in JavaScript, where functions and
dynamic objects collapse many traditional patterns into
language primitives. For example, the Strategy pattern:

```javascript id="js-strategy"
function execute(list, strategy) {
    return strategy(list);
}

const quickSort = (arr) => arr.slice().sort((a, b) => a - b);

console.log(execute([3, 1, 2], quickSort));
```

In a classical OO interpretation, this is "Strategy implemented via polymorphism."
But in practice, nothing in the language requires that framing. There is no
interface, no class hierarchy, no explicit design structure beyond passing a function.

If we try to reintroduce pattern vocabulary here, it becomes retrofitted rather
than descriptive. The language already contains the abstraction directly.

This leads to a second distortion: design patterns sometimes encourage unnecessary
structural layering even when the language already provides a simpler mechanism.

A similar phenomenon appears in Python, particularly with patterns like Singleton.
In classical OO terms, Singleton is used to ensure a single instance of a class.
In Python, the same behaviour is often achieved simply through module-level state:

```python id="py-singleton"
class Config:
    def __init__(self):
        self.value = 42

config = Config()
```

Or even more directly:

```python id="py-module-state"
value = 42
```

The “pattern” dissolves entirely into the module system. Introducing a
Singleton class here does not improve clarity—it adds structure that the
language does not require.

This exposes a broader issue: many design patterns were historically
solutions to language limitations rather than intrinsic design necessities.
As those limitations disappear, the patterns can become conceptual
overhead rather than insight.

The overestimation of patterns becomes more visible in systems where
developers attempt to preserve object-oriented structure even when it
is not the most natural model. A typical example is JavaScript frameworks
that emulate classical inheritance hierarchies:

```javascript id="js-class-emulation"
class Animal {
    speak() {
        console.log("generic sound");
    }
}

class Dog extends Animal {
    speak() {
        console.log("bark");
    }
}
```

While this is syntactically valid, it often does not reflect how
JavaScript systems are actually structured in modern practice, where
composition and function pipelines are more common than inheritance
trees. The pattern vocabulary (Factory, Observer, Strategy, etc.)
can still be applied here, but it often leads to architectural weight
that is not required by the problem.

This reveals a third issue: patterns can shift from descriptive tools
into prescriptive habits. Instead of emerging from the problem, they
become templates that are applied before the problem is fully understood.

The consequences of this are not purely theoretical. Overuse of
pattern-based thinking can lead to systems where structure is optimised
for conceptual cleanliness rather than practical simplicity. Layers of
abstraction accumulate not because they are needed, but *because they are familiar*.

At the same time, it is important not to discard the insight entirely.
The value of design patterns becomes clearer when viewed as historical
compression of experience rather than as strict implementation rules.

Even in non-OO languages, the underlying problems that patterns describe
still exist. For example, communication between components still matters,
even if Observer is not explicitly implemented:

```javascript id="js-event-simple"
const listeners = [];

function subscribe(fn) {
    listeners.push(fn);
}

function emit(data) {
    listeners.forEach(fn => fn(data));
}
```

Here, the structure is minimal, but the idea is identical: decoupled notification.
The difference is that the language no longer requires a formal pattern to express it.

Similarly, in Python, handling variation in behaviour (traditionally Strategy)
is often naturally expressed through functions:

```python id="py-strategy"
def execute(data, strategy):
    return strategy(data)

def quick_sort(arr):
    return sorted(arr)

execute([3, 1, 2], quick_sort)
```

Again, the pattern survives conceptually, but not structurally.

What emerges from this comparison is a more precise view of what design
patterns actually represent. They are not fundamental building blocks of
software design, but rather artifacts of a particular phase in language
evolution--specifically a phase where abstraction had to be manually constructed.

As languages evolved, many of these constructions were absorbed directly
into core features: first-class functions, modules, type systems, and
compositional runtime models. In this transition, the boundary between
"pattern" and "feature" becomes blurred.

The risk in treating patterns as universal truths is that it hides this
transition. It can make older structural solutions appear more fundamental
than they actually are, leading to unnecessary complexity in environments
where simpler models already exist.

However, the disappearance of explicit patterns does not mean the disappearance
of their ideas. Instead, it reveals that their most important contribution
was not structural form, but recognition of recurring design pressure points:
variation, communication, creation, and composition.

In modern systems, those pressures are still present, but they are addressed
at different levels. In C, they are handled through explicit control flow.
In Python and JavaScript, through functions and dynamic objects. In Rust,
Kotlin, and Scala, through type systems and functional composition.

The shift is therefore not a rejection of design patterns, but a redistribution
of their concerns into different layers of abstraction.

The value that remains is not the pattern itself, but the awareness that such
pressures exist at all—and that they can be solved in multiple ways depending
on the expressive power of the language being used.

In that sense, the legacy of design patterns is not architectural rigidity,
but interpretive flexibility: the ability to recognize when a structure is
genuinely needed, and when it is merely a relic of an earlier constraint.
