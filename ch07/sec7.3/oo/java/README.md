
## Java Object Structures

In these folders, we explore Java, which has grown into a
substantial programming language.  Since we haven't assumed
any prior knowledge of Java (only C and Python), a brief introduction 
is provided. There are also two implementations of a simple interpreter.
The first implementation (in folder [01](./01/)) demonstrates the
*Interpreter pattern* and fundamental object-oriented principles,
and is included to give readers a straightforward approach to the code.
The second implementation (in folder [02](./02/)) illustrates the modern
approach to object-oriented programming in Java and
includes more advanced constructs.


### Imperative Programming within Object-Orientation

This section covers the fundamental object structures in Java,
which serve as the foundation for designing object-oriented programs.
Java combines object-oriented principles with practical considerations
to create a balanced programming environment suitable for many applications.

Java is an object-oriented language built on concepts like objects,
classes, methods, inheritance, and instances. However, it also accommodates
imperative programming within its object-oriented framework.
Imperative programming resembles algorithmic descriptions,
like a recipe with sequential steps.

Example of imperative code in Java:

```java
int lower, upper, step;
float fahr, celsius;

lower = 0;
upper = 300;
step = 20;

fahr = lower;

while (fahr <= upper) {
    celsius = (5.0f / 9.0f) * (fahr - 32.0f);
    System.out.println("Fahrenheit = " + fahr
        + " equals Celsius = " + celsius);
    fahr += step;
}
```

### Object Orientation Basics

Object orientation takes a different approach. Objects have state (data)
and behaviour (methods), while classes are abstractions of these objects.
Similar to how bicycle models (classes) can be instantiated
as actual bicycles (objects), each with specific properties and behaviours.

In object-oriented programming:
- Objects act as agents that receive and process messages
- Objects encapsulate implementation details
- Data can be protected and hidden from external access
- A clean separation exists between interface and implementation

Java has a simple class hierarchy where all classes inherit from the Object class.
Polymorphism allows methods to be varied so similar conceptual names can be used
for similar purposes.


### Classes and Methods

A basic class structure:

```java
class StoreClass {
    int x = 0;

    void setValue(int value) {
        x = value;
    }
    int getValue() {
        return x;
    }
}
```

Methods consist of a signature (return type, name, parameter list) and a body.
Instance variables like `x` above are created when an object is instantiated,
unlike local variables which exist only within blocks or methods.


### Object Instances and Method Calls

Objects are created using the `new` operator:

```java
StoreClass mem = new StoreClass();
```

Multiple objects can be instantiated from the same class:

```java
StoreClass firstMem = new StoreClass();
StoreClass secondMem = new StoreClass();
```

Methods are called on these objects:

```java
MemoryClass calc = new MemoryClass();
calc.memoryPlus(67);
calc.memoryPlus(23);
System.out.println(calc.remindMemory()); // Output: 90
calc.clearMemory();
```

### Memory Management: null and Garbage Collection

The `null` value indicates the absence of an object reference.
When objects are no longer referenced,
they become eligible for garbage collection.

The `finalize()` method is called before an object is garbage
collected and is typically overridden
when system resources need to be released:

```java
void finalize() {
    // Release resources
    super.finalize();
}
```

### Constructors and Method Overloading

Constructors are special methods called when objects are created:

```java
class AnotherNewMemory {
    int x, y;

    AnotherNewMemory() {
        x = 0;
        y = 0;
    }

    AnotherNewMemory(int x, int y) {
        this.x = x;
        this.y = y;
    }
}
```

Method overloading allows multiple methods with the
same name but different parameters:

```java
boolean equals(String s) { /*...*/ }
boolean equals(Name n) { /*...*/ }
```

### The "this" and "super" References

`this` refers to the current object:
```java
this.x = x; // Distinguishes instance variable from parameter
```

`super` refers to the superclass:
```java
super(x, y); // Calls superclass constructor
super.methodName(); // Calls superclass method
```


### Inheritance and Subclassing

Inheritance allows a class to extend another,
inheriting its properties:

```java
class ExtendedName extends Name {
    String pr, po;

    ExtendedName(String pr, String v, String po) {
        super(v);
        this.pr = pr;
        this.po = po;
    }
    
    // Additional methods..
}
```

### Method Overriding

Subclasses can override methods from superclasses:

```java
// In superclass
String toString() {
    return "Value: [" + v + "]";
}

// In subclass
String toString() {
    return "Pre: [" + pr + "]\n"
        + super.toString()
        + "Post: [" + po + "]";
}
```

### Abstract Classes and Methods

Abstract classes contain at least one abstract method
(a method without implementation):

```java
abstract class Pen {
    // Regular methods with implementation
    void drawTo(int a, int b) {
        drawFromTo(getX(), getY(), a, b);
        moveTo(a, b);
    }

    // Abstract method without implementation
    abstract void drawFromTo(int x, int y, int a, int b);
}
```

Abstract classes cannot be instantiated but must be extended.

### Interfaces

Interfaces define a contract of methods that implementing
classes must provide:

```java
interface Transferable {
    void subject(String subject);
    void letter(String letter) throws TransferException;
}

class Printer implements Transferable {
    public void subject(String subject) { /*...*/ }
    public void letter(String letter) throws TransferException { /*...*/ }
}
```

Interfaces can form hierarchies and enable
a form of multiple inheritance in Java:

```java
interface Access extends SetAccess, GetAccess { }
```

### The Object Class

All Java classes implicitly inherit from the Object class,
which provides methods like:
- `toString()` - creates a string representation
- `equals()` - compares objects for equality
- `clone()` - creates a copy of an object

These methods are commonly overridden to provide class-specific behaviour.


### Access Modifiers

Java provides several access modifiers that control
the visibility of classes, methods, and fields:

- `public`: Accessible from anywhere
- `protected`: Accessible within the same package and by subclasses
- `default` (no modifier): Accessible only within the same package
- `private`: Accessible only within the same class

Example:
```java
public class AccessExample {
    public int publicField;        // Accessible from anywhere
    protected int protectedField;  // Accessible in package and subclasses
    int defaultField;              // Accessible only in same package
    private int privateField;      // Accessible only in this class
    
    private void privateMethod() {
        // Only accessible within this class
    }
}
```

### Static Members

Static fields and methods belong to the class rather than to instances:

```java
class Counter {
    private static int count = 0;  // Shared across all instances
    
    public Counter() {
        count++;
    }
    
    public static int getCount() {  // Called on the class, not instances
        return count;
    }
}

// Usage
Counter c1 = new Counter();
Counter c2 = new Counter();
System.out.println(Counter.getCount());  // Outputs: 2
```

### Generics

Generics provide type safety for collections and other data structures:

```java
// Without generics (pre-Java 5)
List list = new ArrayList();
list.add("hello");
String s = (String) list.get(0);  // Requires explicit casting

// With generics
List<String> list = new ArrayList<>();
list.add("hello");
String s = list.get(0);  // No casting needed
```

Generic classes:
```java
class Box<T> {
    private T content;
    
    public void put(T content) {
        this.content = content;
    }
    
    public T get() {
        return content;
    }
}

// Usage
Box<Integer> integerBox = new Box<>();
integerBox.put(42);
Integer value = integerBox.get();
```

### Inner Classes

Java supports several types of nested classes:

__1. *Static nested classes*__

```java
class Outer {
    static class StaticNested {
        // Can be instantiated without an Outer instance
    }
}
```

__2. *Non-static inner classes*__

```java
class Outer {
    class Inner {
        // Requires an Outer instance to be instantiated
    }
}
```

__3. *Local classes* (defined inside methods)__

```java
void method() {
    class Local {
        // Only visible within this method
    }
}
```

__4. *Anonymous classes*__

```java
interface Clickable {
    void onClick();
}

// Anonymous implementation
Clickable button = new Clickable() {
    @Override
    public void onClick() {
        System.out.println("Button clicked!");
    }
};
```

### Exception Handling

Java uses try-catch blocks for exception handling:

```java
try {
    // Code that might throw exceptions
    FileReader file = new FileReader("file.txt");
    // Process file...
} catch (FileNotFoundException e) {
    // Handle specific exception
    System.err.println("File not found: " + e.getMessage());
} catch (IOException e) {
    // Handle more general exception
    System.err.println("IO error: " + e.getMessage());
} finally {
    // Always executed, regardless of exceptions
    // Used for cleanup operations
}
```

Checked vs. unchecked exceptions:
- Checked exceptions must be declared or caught (e.g., IOException)
- Unchecked exceptions (RuntimeException and its subclasses)
  don't need to be declared


### Functional Interfaces and Lambda Expressions (Java 8+)

Java 8 introduced lambda expressions for more concise code:

```java
// Traditional anonymous class
Runnable r1 = new Runnable() {
    @Override
    public void run() {
        System.out.println("Running");
    }
};

// Equivalent lambda expression
Runnable r2 = () -> System.out.println("Running");

// Lambda with parameters
Comparator<String> comparator = (s1, s2) -> s1.length() - s2.length();
```

### Streams API (Java 8+)

The Streams API enables functional-style operations on collections:

```java
List<String> names = Arrays.asList("Alice", "Bob", "Charlie", "David");

// Filter, transform, and collect
List<String> filteredNames = names.stream()
    .filter(name -> name.length() > 4)
    .map(String::toUpperCase)
    .collect(Collectors.toList());
// Result: [ALICE, CHARLIE, DAVID]

// Other common operations
long count = names.stream()
    .filter(name -> name.startsWith("A"))
    .count();
// Result: 1
```

These modern features complement Java's object-oriented
foundation with functional programming capabilities.
