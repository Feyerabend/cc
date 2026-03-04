
## Object-Oriented Programming in C with Coroutines

Comprehensive demonstration of OOP patterns in C using coroutines.

### Building

```bash
gcc -o oop_coroutines oop_coroutines.c -Wall
./oop_coroutines
```

### What It Demonstrates

1. *Polymorphism & Inheritance* - Shape hierarchy with virtual methods
2. *Iterator Pattern* - Coroutine-based iteration
3. *State Machines* - Animation controller
4. *Generator Pattern* - Fibonacci sequence
5. *Producer-Consumer* - Cooperative multitasking
6. *Task Scheduler* - Priority-based execution

### Key Features

- Virtual method tables (vtables) for polymorphism
- Inheritance by struct embedding
- Coroutine macros: CO_BEGIN, CO_YIELD, CO_END
- State preservation across function calls
- Clean abstraction for complex state management

Educational example showing how coroutines enable OOP in C.


### The Paradox

C is not an object-oriented language.
It has no classes, no inheritance, no polymorphism built into the syntax.
Yet some of the most sophisticated object-oriented systems ever
built—the Linux kernel, GTK+, GObject—are written in C.

__How?__

The answer lies not in mimicking C++ or Java, but in embracing C's true strength:
*direct control over memory layout and function pointers*.
And when you add *coroutines* to this foundation,
something remarkable happens:
object-oriented patterns that feel awkward in pure C suddenly become elegant and natural.


### Why Coroutines Change Everything

Traditional OOP in C faces a fundamental problem: *state management*. 

Consider a simple iterator in C++:

```cpp
class Iterator {
    int index;
public:
    bool next() {
        if (index < size) {
            current = array[index++];
            return true;
        }
        return false;
    }
};
```

The object naturally preserves `index` between calls. Easy.

In pure C, you'd typically do this:

```c
typedef struct {
    int* array;
    int size;
    int index;  // Must manually track state
} Iterator;

int iterator_next(Iterator* self) {
    if (self->index < self->size) {
        self->current = self->array[self->index++];
        return 1;
    }
    return 0;
}
```

This works, but notice: *you're manually managing state that should be implicit*.
For complex behaviours--state machines, generators, cooperative multitasking--this
manual state tracking becomes painful.

*Coroutines solve this*. They let functions suspend and resume, automatically
preserving execution state. This transforms how we implement object behaviors in C.


### The Core Insight

*Coroutines don't just enable OOP patterns in C—they make them more natural than in many OOP languages.*

And here's why:


#### 1. *State Becomes Implicit*

With coroutines, you write linear code that naturally suspends:

```c
int iterator_next(Iterator* self) {
    CO_BEGIN(&self->coroutine);
    
    while (self->current < self->count) {
        self->current_value = self->array[self->current];
        self->current++;
        CO_YIELD(&self->coroutine);  // Suspend here, resume next call
    }
    
    CO_END(&self->coroutine);
}
```

The coroutine infrastructure handles state preservation.
You focus on *what* happens, not *how* to track where you are.

#### 2. *Generators Are Native*

Python's generators are powerful:

```python
def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b
```

With coroutines, C can do this just as cleanly:

```c
int fibonacci_next(Generator* self) {
    CO_BEGIN(&self->coroutine);
    
    self->current = self->a;
    CO_YIELD(&self->coroutine);
    
    self->current = self->b;
    CO_YIELD(&self->coroutine);
    
    while (1) {
        int next = self->a + self->b;
        self->a = self->b;
        self->b = next;
        self->current = next;
        CO_YIELD(&self->coroutine);
    }
    
    CO_END(&self->coroutine);
}
```

No manual state machine.
No explicit state tracking.
Just *yield and resume*.

#### 3. *State Machines Become Readable*

Traditional state machines in C are verbose:

```c
// Traditional approach: explicit state tracking
typedef enum { STATE_IDLE, STATE_RUNNING, STATE_DONE } State;

void update(StateMachine* sm) {
    switch (sm->state) {
        case STATE_IDLE:
            if (sm->ready) {
                sm->state = STATE_RUNNING;
                sm->step = 0;
            }
            break;
        case STATE_RUNNING:
            if (sm->step == 0) {
                // Do step 0
                sm->step = 1;
            } else if (sm->step == 1) {
                // Do step 1
                sm->step = 2;
            } else {
                sm->state = STATE_DONE;
            }
            break;
        // ..
    }
}
```

With coroutines, you write the logic *linearly*:

```c
void update(StateMachine* sm) {
    CO_BEGIN(&sm->coroutine);
    
    // Wait until ready
    while (!sm->ready) {
        CO_YIELD(&sm->coroutine);
    }
    
    sm->state = STATE_RUNNING;
    
    // Do steps in sequence
    do_step_0();
    CO_YIELD(&sm->coroutine);
    
    do_step_1();
    CO_YIELD(&sm->coroutine);
    
    do_step_2();
    
    sm->state = STATE_DONE;
    CO_END(&sm->coroutine);
}
```

The control flow is obvious.
No mental tracking of state variables.



### OOP in C: The Essential Patterns

Before we dive into coroutines,
let's establish how basic OOP works in C
(or at least: could work):

#### Pattern 1: Structs as Objects

```c
typedef struct {
    char* name;
    int health;
    int x, y;
} Entity;

// Constructor pattern
Entity* entity_create(const char* name, int health) {
    Entity* e = malloc(sizeof(Entity));
    e->name = strdup(name);
    e->health = health;
    e->x = e->y = 0;
    return e;
}

// Destructor pattern
void entity_destroy(Entity* e) {
    free(e->name);
    free(e);
}

// Method pattern
void entity_move(Entity* e, int dx, int dy) {
    e->x += dx;
    e->y += dy;
}
```

This is straightforward: *structs hold data, functions operate on them*.
The first parameter is always `self`.

#### Pattern 2: Inheritance via Embedding

```c
// Base "class"
typedef struct {
    char* name;
    int health;
} Entity;

// Derived "class"
typedef struct {
    Entity base;  // Embedded base, but MUST BE FIRST
    int armor;
    int strength;
} Warrior;

// Works because Warrior* and Entity* have same address
Entity* e = (Entity*)warrior_create("Conan", 100, 50, 20);
```

The key: *embedding the base struct as the first member*
ensures the addresses match, making casts safe.

#### Pattern 3: Polymorphism via Function Pointers

```c
// Virtual method table
typedef struct Entity Entity;

typedef struct {
    void (*update)(Entity* self);
    void (*draw)(Entity* self);
    void (*destroy)(Entity* self);
} EntityVTable;

// Base struct with vtable pointer
struct Entity {
    EntityVTable* vtable;
    char* name;
    int health;
};

// Call polymorphically
entity->vtable->update(entity);  // Calls correct version at runtime
```

This is *runtime polymorphism*:
the vtable pointer determines which function gets called.


### Where Coroutines Supercharge OOP

Now combine these patterns with coroutines, and you get:

#### Stateful Methods

Methods can suspend and resume, maintaining complex internal state:

```c
int particle_system_update(ParticleSystem* self) {
    CO_BEGIN(&self->coroutine);
    
    // Initialisation phase
    spawn_particles(self);
    CO_YIELD(&self->coroutine);
    
    // Update phase: runs until all particles dead
    while (self->active_count > 0) {
        update_all_particles(self);
        CO_YIELD(&self->coroutine);
    }
    
    // Cleanup phase
    cleanup_particles(self);
    
    CO_END(&self->coroutine);
}
```

Each call continues where it left off.
The object's update logic is a *persistent process*.

#### Internal Iterators

Instead of exposing internal structure, 
objects can iterate themselves:

```c
int tree_traverse(Tree* self) {
    CO_BEGIN(&self->coroutine);
    
    // In-order traversal
    if (self->left) {
        tree_traverse(self->left);
    }
    
    self->current_node = self->root;
    CO_YIELD(&self->coroutine);
    
    if (self->right) {
        tree_traverse(self->right);
    }
    
    CO_END(&self->coroutine);
}
```

Clean interface, hidden implementation, lazy evaluation.

#### Cooperative Objects

Objects can cooperate without threads:

```c
// Producer object
int producer_run(Producer* self) {
    CO_BEGIN(&self->coroutine);
    
    while (self->items_to_produce > 0) {
        produce_item(self);
        self->items_to_produce--;
        CO_YIELD(&self->coroutine);  // Let consumer run
    }
    
    CO_END(&self->coroutine);
}

// Consumer object
int consumer_run(Consumer* self) {
    CO_BEGIN(&self->coroutine);
    
    while (!self->producer->finished || has_items(self)) {
        if (has_items(self)) {
            consume_item(self);
            CO_YIELD(&self->coroutine);  // Let producer run
        } else {
            CO_YIELD(&self->coroutine);  // Wait for items
        }
    }
    
    CO_END(&self->coroutine);
}
```

Cooperative multitasking *within* objects.
No threads, no locks, no race conditions.


### How Coroutines Actually Work

The magic is simpler than you think.
At its core, a coroutine needs two things:

1. *Save execution context* (where we are in the code)

2. *Restore execution context* (jump back to that point)

There are three main implementation strategies:

#### Strategy 1: setjmp/longjmp (Portable but Limited)

```c
typedef struct {
    jmp_buf context;
    int state;
} Coroutine;

#define CO_YIELD(co) \
    do { \
        (co)->state = __LINE__; \
        if (setjmp((co)->context) == 0) return; \
        case __LINE__:; \
    } while(0)
```

Uses C's exception-handling primitives to save/restore stack state.
Portable, but *can't preserve local variables* across yields.

#### Strategy 2: Computed Goto (GCC Extension)

```c
typedef struct {
    void* resume_point;
} Coroutine;

#define CO_YIELD(co) \
    do { \
        (co)->resume_point = &&LABEL_##__LINE__; \
        return; \
        LABEL_##__LINE__:; \
    } while(0)

#define CO_BEGIN(co) \
    if ((co)->resume_point) goto *(co)->resume_point;
```

Uses GCC's "labels as values" extension.
*Faster than setjmp*, supports local variables if stored in the struct.

#### Strategy 3: Duff's Device (Clever, Portable)

```c
#define CO_BEGIN(co) \
    switch((co)->state) { case 0:

#define CO_YIELD(co) \
    do { (co)->state = __LINE__; return; \
         case __LINE__:; } while(0)

#define CO_END(co) }
```

Exploits C's switch statement to create multiple entry points.
*Fully portable*, but locals must be in the struct.

### What This Demo Shows

This implementation demonstrates:
1. *Polymorphic Shape Hierarchy* - vtables + inheritance in pure C
2. *Coroutine-Based Iterators* - internal iteration with state preservation
3. *State Machine Controllers* - linear control flow for complex states
4. *Generator Pattern* - lazy sequence evaluation (Fibonacci)
5. *Producer-Consumer* - cooperative multitasking without threads
6. *Priority Task Scheduler* - polymorphic task execution with coroutines

Each pattern shows how *coroutines make OOP in C not just possible, but elegant*.


### Why It Matters

#### For Systems Programming
Embedded systems, kernels, and drivers often can't use C++ but
need complex state management. Coroutines provide that without overhead.

#### For Game Development
Entity systems, AI behaviors, animation controllers--all benefit from
stateful objects that can suspend/resume.

#### For Understanding Language Design
See how high-level features (iterators, async/await, generators)
map to machine-level primitives.

#### For Practical C
Even if you don't use coroutines daily, understanding them deepens your grasp of:
- Memory layout and ABI
- Function pointers and dispatch
- State machines and control flow
- The relationship between syntax and semantics


### The Bottom Line

*C can absolutely do object-oriented programming.*
The language gives you the raw materials—structs,
function pointers, controlled memory layout.
You build the abstractions you need.

*Coroutines amplify this dramatically.* 
They transform clunky manual state tracking into elegant,
linear code. They make patterns like iterators and
generators—awkward in plain C—feel natural.

This isn't about making C into C++.
It's about *using C's strengths* (direct control,
zero overhead abstractions, explicit memory management)
*while adding the expressiveness* of stateful, resumable functions.

The result is something unique:
object-oriented programming that's both *low-level* 
(you control everything) and *high-level* (the abstractions are clean).

Let's see how it works.



### Quick Start

```bash
# Compile
make

# Run
./oop_coroutines

# See all 6 patterns in action:
# - Polymorphic shapes
# - Coroutine iterators
# - State machines
# - Fibonacci generator
# - Producer-consumer
# - Task scheduler
```

*Note on Warnings:* The implementation uses `setjmp`/`longjmp`
which creates nested switch statements in the coroutine macros.
This is intentional and safe. Compile with `-Wno-switch` to
suppress these warnings, or see the code comments for alternative
dispatch strategies (computed goto, function pointers).





### A note on Duff's Device: The Clever Hack

#### What It Is

Duff's Device is a loop unrolling optimization discovered by Tom Duff in
1983 while working at Lucasfilm. It exploits an obscure feature of C:
you can put `case` labels anywhere inside a `switch` statement,
even inside nested loops. The original looked like this:

```c
send(short *to, short *from, int count) {
    int n = (count + 7) / 8;
    switch (count % 8) {
        case 0: do { *to = *from++;
        case 7:      *to = *from++;
        case 6:      *to = *from++;
        case 5:      *to = *from++;
        case 4:      *to = *from++;
        case 3:      *to = *from++;
        case 2:      *to = *from++;
        case 1:      *to = *from++;
               } while (--n > 0);
    }
}
```

Most programmers seeing this for the first time think
it's a typo. It's not. It's perfectly legal C.


#### The Reasoning Behind It

*The Problem:* Copying data one element at a time is slow.
Each iteration has overhead: increment the counter,
check the condition, jump back to the top of the loop.

*The Solution:* Unroll the loop—write out 8 copies of the
operation so you do 8 at once. But what if you have, say,
13 elements to copy? You need to handle the remainder.

*Duff's Insight:* The `switch` statement lets you jump
into the middle of the loop at exactly the right point.
If `count % 8 == 3`, jump to `case 3`, execute 3 iterations,
then loop around doing 8 at a time.

The brilliance is realising that `switch` and loops are both
just computed gotos under the hood. The C standard says
`case` labels can appear anywhere in a `switch`,
even inside a loop body. Duff combined them.

#### Why It Works for Coroutines

For coroutines, we exploit the same principle differently.
Instead of loop unrolling, we use it for *multiple entry points*:

```c
int coroutine(Coroutine* co) {
    switch (co->state) {
        case 0:  // First entry - start here
            printf("Step 1\n");
            co->state = 1;
            return 1;  // Suspend
        
        case 1:  // Resume here on second call
            printf("Step 2\n");
            co->state = 2;
            return 1;  // Suspend
        
        case 2:  // Resume here on third call
            printf("Step 3\n");
            return 0;  // Done
    }
}
```

Each call jumps to the right `case` based on `co->state`.
The function has multiple entry points.

#### The Macro Trick

We can make this automatic with macros:

```c
#define CO_BEGIN(co) \
    switch ((co)->state) { case 0:

#define CO_YIELD(co) \
    do { \
        (co)->state = __LINE__; \
        return 1; \
        case __LINE__:; \
    } while(0)

#define CO_END(co) \
    } \
    (co)->state = -1; \
    return 0;
```

Now you write:

```c
int coroutine(Coroutine* co) {
    CO_BEGIN(co);
    
    printf("Step 1\n");
    CO_YIELD(co);
    
    printf("Step 2\n");
    CO_YIELD(co);
    
    printf("Step 3\n");
    
    CO_END(co);
}
```

*The magic:* `CO_YIELD` expands to set `state = __LINE__`
(the current line number), return, and create a `case __LINE__:`
label at that exact spot. On the next call, the `switch`
in `CO_BEGIN` jumps straight there.

#### Why It's Useful

1. *Completely portable* - No compiler extensions, works on any C compiler
2. *Zero overhead* - Just a single computed goto (switch) per resume
3. *Type safe* - Compiler checks everything
4. *Simple* - ~10 lines of macros, no runtime library needed

The limitation: local variables don't persist across yields
(they're on the stack, which gets unwound when you return).
So you must store persistent state in the coroutine struct.

#### The Philosophy

Duff's Device represents a certain mindset:
*the C standard is a specification, not a suggestion*.
If the spec says you can do something, you can do it,
even if it looks weird. The compiler doesn't care about aesthetics.

This makes some people uncomfortable.
"Just because you can doesn't mean you should."
But for coroutines, it's the perfect tool: portable,
efficient, and surprisingly elegant once you understand what's happening.

The preprocessor transforms your linear-looking code into a state machine.
The switch statement dispatches to the right state. And you get cooperative
multitasking without platform-specific hacks.

That's the beauty of Duff's Device: it's not really about loop unrolling
or coroutines. It's about recognizing that C gives you low-level control,
and if you understand the primitives, you can build surprisingly powerful abstractions.
