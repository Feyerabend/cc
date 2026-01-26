
## A Project For Building A Minimal Object-Oriented Language (MOL)

It might seem quite tedious and uninspiring to develop yet another procedural programming
language (such as PL/0), complete with its grammar, abstract syntax tree (AST), optimisations,
compiler, and all the associated components. All that is suggested in the book. The suggestion
is made as it is perhaps the easiest to get a grasp of concepts through it. However, even
though it might be the most straightforward and accessible option for beginners or those
new to language design, building yet another procedural language can feel like an obsolete
chore--a tedious legacy task straight out of computing's distant past.

Instead, we propose here creating an object-oriented language as an alternative. This could
serve as an engaging project specifically tailored for individuals who are passionate about
exploring object-oriented programming (OOP) features. Building an OOP language allows
for a deeper dive into concepts that emphasise objects and their interactions, making the project
more stimulating for OOP enthusiasts. Furthermore, this suggestion aligns with contemporary trends
in programming: many modern languages, such as Python, Java, or Rust, incorporate a blend of
paradigms--including functional elements (like higher-order functions and immutability),
procedural aspects (sequential execution and modularity), but also object-oriented principles.
This hybrid approach enables more flexible, expressive, and efficient code, reflecting how
the field has evolved to borrow the best ideas from multiple styles rather than adhering strictly to one.


#### The Core of Object-Oriented Programming

Object-oriented programming (OOP) might appear elusive: objects, classes, inheritance, polymorphism.
But beneath the syntax, every OOP language compiles down to three primitive ideas:
*structs*,
*function pointers*,
and *discipline*.
This document explains the minimal mechanisms that make OOP work, traces their history,
and shows how to build from this foundation toward a complete compiler.

As we actually starts with a familiarity of implementation, we can build from the ground up,
in contrast to common ways through the theory first.


### Part 1: The Three Core Mechanisms

#### 1.1 Memory Layout: Objects Are Just Structs

An "object" is a contiguous block of memory containing:
- A *vtable pointer* (vptr) as the first field (a bit more on [vtables](./../../addition/vtable/))
- Instance data (fields/attributes)

```c
struct Object {
    const struct VTable *vptr;  // MUST be first
    // .. other fields follow
};

struct IntObject {
    const struct VTable *vptr;  // Inherits layout
    int value;
};
```

*Why the vptr comes first*: This enables subtyping through prefix layout.
A pointer to `IntObject` can be safely cast to `Object*` because they
share the same initial memory layout.


#### 1.2 Dispatch: VTables Are Function Pointer Tables

A *vtable* (virtual method table) is a struct containing function pointers:

```c
struct VTable {
    void (*destroy)(void *self);
    void (*print)(void *self);
    int  (*compare)(void *self, void *other);
};
```

Each object type has its own vtable with its own implementations:

```c
// IntObject's implementations
void int_print(void *self) {
    struct IntObject *obj = self;
    printf("%d\n", obj->value);
}

void int_destroy(void *self) {
    free(self);
}

// The vtable constant
const struct VTable IntVTable = {
    .destroy = int_destroy,
    .print   = int_print,
    .compare = int_compare
};
```

#### 1.3 Discipline: Methods Take Self

Every method receives a `void *self` pointer (the "this" pointer in C++/Java):

```c
void method(void *self, /* other args */) {
    struct ConcreteType *obj = self;
    // Use obj->fields
}
```

This discipline makes dynamic dispatch work:

```c
struct Object *obj = create_some_object();
obj->vptr->print(obj);  // Calls the right implementation!
```

The runtime:
1. Dereferences `obj->vptr` to get the vtable
2. Looks up the `print` function pointer
3. Calls it with `obj` as the first argument

*This is the entire mechanism.* Everything else is convenience.



### Part 2: Core OOP Features Explained

#### 2.1 Polymorphism (Dynamic Dispatch)

Different types can respond to the same message differently:

```c
void print_any(struct Object *obj) {
    obj->vptr->print(obj);  // Works for ANY object!
}

struct Object *int_obj = (struct Object*)make_int(42);
struct Object *str_obj = (struct Object*)make_string("hello");

print_any(int_obj);  // Prints: 42
print_any(str_obj);  // Prints: hello
```

The key: *different vtables, same interface*. As long as both vtables have a `print`
function pointer at the same offset, the call works.

#### 2.2 Inheritance (Struct Embedding)

Inheritance is just struct prefix layout:

```c
struct Animal {
    struct VTable *vptr;
    int age;
};

struct Dog {
    struct Animal base;  // MUST be first
    int tail_length;
};

struct Dog *dog = make_dog();
struct Animal *animal = (struct Animal*)dog;  // Safe upcast
animal->vptr->speak(animal);  // Dynamic dispatch works
```

*Vtable chaining* for method lookup:

```c
struct VTable {
    struct VTable *parent;  // Pointer to parent vtable
    void (*method1)(void *self);
    void (*method2)(void *self);
};
```

When a method isn't found, check `parent` vtable.
This is how Python's MRO (Method Resolution Order) works.

#### 2.3 Encapsulation

Encapsulation isn't enforced at runtime--it's a compile-time fiction.
The compiler prevents you from accessing private fields, but at the
machine level, they're just offsets in memory.

In C, you achieve encapsulation through *opaque pointers*:

```c
// header file
struct Widget;  // Incomplete type
struct Widget* widget_create(void);
void widget_destroy(struct Widget *w);

// implementation file
struct Widget {
    struct VTable *vptr;
    int private_data;  // Not visible to users
};
```

#### 2.4 Interfaces / Abstract Base Classes

An interface is just a vtable with no data:

```c
struct Printable {
    void (*print)(void *self);
};

struct IntObject {
    struct Printable *printable_vptr;  // Implements Printable
    int value;
};
```

Or in languages with multiple inheritance, objects have multiple vptrs:

```c
struct Dog {
    struct Animal_VTable *animal_vptr;
    struct Printable_VTable *printable_vptr;
    // ... data
};
```



### Part 3: How Real Languages Implement This

#### 3.1 C++

C++ invented the term "vtable" and made it famous.
Every class with virtual methods gets a compiler-generated vtable.

```cpp
class Animal {
public:
    virtual void speak() = 0;  // Pure virtual
    virtual ~Animal() {}
};

class Dog : public Animal {
    void speak() override { cout << "Woof"; }
};
```

Compiles to approximately:

```c
struct Animal {
    struct Animal_VTable *vptr;
};

struct Animal_VTable {
    void (*speak)(struct Animal *self);
    void (*destructor)(struct Animal *self);
};

struct Dog {
    struct Animal_VTable *vptr;  // Inherited layout
};

void dog_speak(struct Animal *self) {
    printf("Woof\n");
}

struct Animal_VTable Dog_VTable = {
    .speak = dog_speak,
    .destructor = dog_destructor
};
```

*Key insight*: The compiler does all the work. It generates vtables,
inserts vptr initialisation in constructors, and transforms method calls into vtable lookups.

#### 3.2 Python

Python objects are dictionaries with special handling.
The `__class__` attribute points to a type object, which contains the method dictionary:

```python
class Dog:
    def speak(self):
        print("Woof")

dog = Dog()
dog.speak()  ## Roughly: dog.__class__.__dict__['speak'](dog)
```

Under the hood (CPython):

```c
struct PyObject {
    Py_ssize_t ob_refcnt;
    struct PyTypeObject *ob_type;  // This is the "vptr"
};

struct PyTypeObject {
    // ... lots of fields
    PyObject *tp_dict;  // Method dictionary
    // Function pointers for operators:
    binaryfunc tp_add;
    reprfunc tp_repr;
    // ...
};
```

*Python's twist*: Methods are looked up at runtime in dictionaries.
This is slower but more flexible (you can add methods dynamically).

#### 3.3 Java

Java uses vtables but adds an extra layer: the *method area* in the JVM.

```java
class Animal {
    void speak() { }
}

class Dog extends Animal {
    void speak() { System.out.println("Woof"); }
}
```

At runtime:
1. Each object has a header pointing to its class metadata
2. Class metadata includes a vtable
3. `invokevirtual` bytecode does vtable dispatch

*Java's optimisation*: The JIT compiler often *inlines* virtual calls
when it can prove the type (speculative optimisation).

#### 3.4 Rust

Rust uses *trait objects* for dynamic dispatch:

```rust
trait Speak {
    fn speak(&self);
}

struct Dog;
impl Speak for Dog {
    fn speak(&self) { println!("Woof"); }
}

let animal: &dyn Speak = &Dog;  // Fat pointer
animal.speak();
```

A `dyn Trait` is a *fat pointer*: (data pointer, vtable pointer).

```c
struct TraitObject {
    void *data;      // Points to actual object
    void *vtable;    // Points to trait vtable
};
```

*Rust's innovation*: No inheritance, only composition + traits.
Cleaner semantics, same mechanism.



### Part 4: Historical Notes

#### 4.1 Simula 67 (1967)

The first OOP language. Introduced:
- Classes
- Inheritance
- Virtual methods

```simula
CLASS Animal;
    VIRTUAL: PROCEDURE speak;
BEGIN
    PROCEDURE speak; BEGIN OutText("..."); END;
END Animal;

CLASS Dog;
BEGIN
    PROCEDURE speak; BEGIN OutText("Woof"); END;
END Dog;
```

Simula compiled to ALGOL and used vtables internally.

#### 4.2 Smalltalk (1972-1980)

Everything is an object. Methods are messages sent to objects:

```smalltalk
dog := Dog new.
dog speak.  "Send 'speak' message to dog"
```

Smalltalk didn't use vtables—it used *message dispatch* through dictionaries.
This was slower but enabled features like `method_missing` (handling unknown messages).

*Legacy*: Ruby, Python, and Objective-C all borrowed this message-passing model.

#### 4.3 C++ (1985)

Bjarne Stroustrup wanted OOP in C. He added:
- Classes with vtables
- Multiple inheritance (multiple vptrs)
- Static typing

C++ proved you could have OOP performance without sacrificing low-level control.
This made it dominant for systems programming.

#### 4.4 Java (1995)

Simplified C++ by removing:
- Multiple inheritance (replaced with interfaces)
- Manual memory management (added GC)
- Pointer arithmetic

But kept the same vtable-based dispatch model.

#### 4.5 Modern Developments

- *Go*: No inheritance, only interfaces. Uses fat pointers like Rust.
- *Swift*: Protocol-oriented programming with "protocol witness tables" (PWTs)—same as vtables.
- *JavaScript*: Prototypal inheritance (objects inherit from objects, not classes).
  Still uses hidden class maps similar to vtables.

*The pattern*: Every language reinvents vtables with different names and minor variations.



### Part 5: Beyond the Core—Building a Compiler

Now you've implemented the runtime.
How do you build a full compiler?

#### 5.1 Frontend: Parsing and Type Checking

*Lexer*: Text → Tokens
```
class Dog { void speak() { ... } }
↓
[CLASS, IDENT("Dog"), LBRACE, VOID, IDENT("speak"), ...]
```

*Parser*: Tokens → AST
```
ClassDecl(
    name="Dog",
    methods=[
        MethodDecl(name="speak", return_type="void", body=...)
    ]
)
```

*Type Checker*: Verify correctness
- Does method exist?
- Are argument types correct?
- Is subtyping valid?

#### 5.2 Middle-End: IR Generation

Translate AST to *Intermediate Representation* (IR):

```
class Dog {
    void speak() { print("Woof"); }
}

Dog d = new Dog();
d.speak();
```

Becomes:

```
// Allocate object
%1 = alloc Dog                    ; Allocate memory
store %1.vptr, Dog_VTable         ; Set vtable pointer

// Virtual call
%2 = load %1.vptr                 ; Load vtable
%3 = load %2.speak                ; Load function pointer
call %3(%1)                       ; Call with self
```

Popular IRs:
- *LLVM IR*: Used by Clang, Rust, Swift
- *JVM Bytecode*: Used by Java, Kotlin, Scala
- *WASM*: Used by web compilers

#### 5.3 Backend: Code Generation

*IR → Assembly*

```llvm
%1 = alloc Dog
store %1.vptr, Dog_VTable
```

Becomes (x86-64):

```asm
mov rdi, 16           ; Size of Dog object
call malloc           ; Allocate
lea rsi, [Dog_VTable] ; Address of vtable
mov [rax], rsi        ; Store vptr
```

*Optimisations*:
- *Inlining*: Replace virtual call with direct call if type is known
- *Devirtualisation*: Convert `obj->vptr->method(obj)` to `method(obj)` when type is statically known
- *Dead code elimination*: Remove unused methods from vtables

#### 5.4 Memory Management

*Manual (C++)*:
```cpp
Dog *d = new Dog();
delete d;  // User's responsibility
```

*Reference Counting (Swift, Python)*:
```c
struct Object {
    struct VTable *vptr;
    int refcount;
};

void retain(struct Object *obj) { obj->refcount++; }
void release(struct Object *obj) {
    if (--obj->refcount == 0) {
        obj->vptr->destroy(obj);
        free(obj);
    }
}
```

*Tracing GC (Java, Go, JavaScript)*:
- Mark: Find all reachable objects from roots
- Sweep: Free unreachable objects

*Implementation approaches*:
- Stop-the-world GC (simple but pauses program)
- Concurrent GC (complex but no pauses)
- Generational GC (optimise for short-lived objects)

#### 5.5 Advanced Features

*Closures with Environment Capture*:

```c
struct Closure {
    void (*call)(void *env, int x);
    void *env;  // Captured variables
};
```

*Generics (Templates)*:
```cpp
template<typename T>
class List { ... };
```

Implementation:
- *Monomorphization* (C++, Rust): Generate separate code for each type
- *Type erasure* (Java): Use single implementation with runtime casts
- *Dictionaries* (Haskell): Pass vtable-like dictionaries for type operations

*Multiple Dispatch* (Julia, Common Lisp):

Instead of `obj.method(args)`, dispatch on ALL argument types:

```julia
function fight(a::Dog, b::Cat)
    println("Dog chases cat")
end

function fight(a::Cat, b::Dog)
    println("Cat scratches dog")
end
```

Implemented with multi-dimensional dispatch tables.



### Part 6: Project Roadmap—From Core to Compiler

#### Phase 1: Runtime (You Are Here)
- Values (int, struct, vtable, closure)
- Environments
- Evaluation
- Virtual dispatch

#### Phase 2: Nicer Syntax
Add a parser for syntax like:

```
class Dog {
    value: int
    
    method speak() {
        print(self.value)
    }
}

let d = Dog(42)
d.speak()
```

Parser converts this to your existing AST.

#### Phase 3: Type System
Add type checking:

```
type Dog = { value: int }
type Cat = { value: string }

// Type error: can't pass Cat where Dog expected
let d: Dog = Cat("Mittens")  // ERROR
```

Implement:
- Type inference (Hindley-Milner algorithm)
- Subtyping rules
- Generic types

#### Phase 4: Optimise
Current interpreter is slow (tree-walk). Options:

*Bytecode VM*:
```
LOAD_CONST 42
STORE_VAR d
LOAD_VAR d
LOAD_ATTR value
CALL_METHOD speak
```

Faster than AST interpretation, simpler than native compilation.

*JIT Compilation*:
- Compile hot code paths to machine code
- Libraries: LLVM, Cranelift, or custom x86-64 codegen

#### Phase 5: Memory Management
Add GC:

1. *Mark-sweep*: Simple, educational
2. *Reference counting*: Easier to implement
3. *Generational GC*: Production-ready

#### Phase 6: Advanced Features
- *Pattern matching*: Algebraic data types
- *Async/await*: Coroutines, futures
- *Module system*: Namespaces, imports
- *FFI*: Call C libraries

#### Phase 7: Self-Hosting
Rewrite your compiler in your own language.
This will be the ultimate test.



### Conclusion

Object-oriented programming have three simple mechanisms:
1. *Structs* for memory layout
2. *Function pointers* for dispatch
3. *Discipline* for passing `self`

Everything else—classes, inheritance, polymorphism, encapsulation--is
mostly light weight constructions that are not part of the core.
But once you understand the core, you can:

- Understand how ANY OOP language works internally
- Debug strange behavior (vtable corruption, memory layout issues)
- Design your own language features
- Optimise OOP code by understanding costs

