
## 6. Lazy Evaluation and Generators


Lazy evaluation means computing a value only when it is actually needed, and
not before. The opposite -- computing everything up front and storing it -- is
*eager* evaluation.

A Python generator is the clearest example: it produces one value at a time,
suspending between each, resuming only when the next value is requested. The
computation is not done in advance; it is deferred until the consumer is ready.



### Why It Exists

Three problems that laziness solves:

*Memory efficiency.* A list of one million integers occupies memory for all one
million integers at once. A generator that counts to one million occupies
memory for one integer at a time -- the current one. The total work is the
same; the peak memory is not.

*Pipeline streaming.* In an eager pipeline, each stage produces its entire
output before the next stage begins. In a lazy pipeline, each stage produces
one element, passes it to the next stage, and both advance in lockstep. Data
flows through without accumulating. This matters for large data sets and for
data that arrives continuously.

*Infinite sequences.* An eager list cannot represent an infinite sequence. A
lazy generator can: it produces values without bound, stopping only when the
consumer stops asking. The program does not need to know in advance how many
values it will use.



### Python: The Exposition Language

#### Basic Generator

```python
def count_up():
    i = 0
    while True:
        yield i
        i += 1
```

`yield` is a suspension point. When the generator reaches `yield i`, it
produces the value `i` and pauses. Its entire local state -- the value of `i`,
the position in the code -- is preserved. The next call to `next()` resumes
from exactly that point.

```python
gen = count_up()
print(next(gen))   # 0
print(next(gen))   # 1
print(next(gen))   # 2
```

Nothing runs until `next()` is called. No values are computed in advance.

#### Finite Generator with StopIteration

```python
def range_gen(start, stop):
    i = start
    while i < stop:
        yield i
        i += 1
    # falling off the end raises StopIteration automatically
```

A `for` loop calls `next()` repeatedly until `StopIteration` is raised, then
stops. This is the protocol that all iterables in Python follow.

#### Fibonacci: Infinite Sequence

```python
def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b
```

An infinite sequence expressed finitely. The generator holds only two
integers at any moment; it does not pre-compute the sequence.

#### Generator Expressions

The generator equivalent of a list comprehension:

```python
squares_gen  = (x * x for x in range(10))    # lazy
squares_list = [x * x for x in range(10)]    # eager

print(type(squares_gen))    # <class 'generator'>
print(type(squares_list))   # <class 'list'>
```

`squares_gen` holds no computed values until iterated. `squares_list` holds
all ten immediately.

#### Lazy Pipeline

Generators chain without creating intermediate collections:

```python
def integers():
    i = 0
    while True:
        yield i
        i += 1

def evens(source):
    for x in source:
        if x % 2 == 0:
            yield x

def squares(source):
    for x in source:
        yield x * x

def take(n, source):
    for _, x in zip(range(n), source):
        yield x

pipeline = take(5, squares(evens(integers())))
print(list(pipeline))   # [0, 4, 16, 36, 64]
```

Each generator pulls one value from the previous stage, transforms it, and
passes it on. At any moment, only one value per stage is in flight. The
`integers()` generator runs forever; `take(5, ...)` stops it after five
results. No intermediate list of all integers, all evens, or all squares is
ever created.

#### send() -- Bidirectional Generators

A generator can also receive values from the consumer:

```python
def accumulator():
    total = 0
    while True:
        value = yield total   # yield current total, receive next addend
        if value is None:
            break
        total += value

acc = accumulator()
next(acc)          # prime the generator (run to first yield)
acc.send(10)       # total -> 10
acc.send(20)       # total -> 30
print(acc.send(5)) # total -> 35
```

`send(value)` resumes the generator and delivers `value` as the result of the
`yield` expression. This turns the generator into a coroutine: a function that
can both produce and consume values, suspending between each exchange.



### Key Discussion Points

#### The Generator as a State Machine

Under the hood, a Python generator is compiled into a state machine. Each
`yield` statement becomes a state transition:

```
state 0: run until first yield, emit value, -> state 1
state 1: run until second yield, emit value, -> state 2
...
state N: run to end, raise StopIteration
```

The "program counter" -- which state to resume in -- is stored in the
generator object alongside all local variables. This is the generator's
*frame*: a snapshot of the execution context at the point of suspension.

For a simple generator like `count_up`, the state machine has two states:
*before first yield* and *after yield, before loop repeats*. For a more
complex generator with multiple yield points, there are more states.

#### Heap-Allocated Frame

Normally, a function's local variables live on the call stack. When the
function returns, the frame is discarded. A generator cannot use the call
stack for its frame, because the frame must survive across calls to `next()`.

Python therefore allocates the generator's frame on the heap. The generator
object holds a pointer to this heap frame. `next()` restores the interpreter
to that frame, runs until the next `yield`, then suspends again -- leaving
the frame intact on the heap.

This is the same mechanism that closures use for captured variables (section
2), extended to entire execution frames.

#### Generator vs. Thread

A generator and a thread both represent suspended computation. The difference
is in who controls the suspension:

- A *generator* suspends itself voluntarily at `yield`. The consumer calls
  `next()` to resume it. Scheduling is cooperative and explicit.
- A *thread* can be suspended by the OS scheduler at any point. Scheduling
  is preemptive and invisible to the code.

Because a generator suspends only at `yield`, no locking is needed between
the generator and its consumer: they never run simultaneously. This is the
defining property of cooperative multitasking. Python's `asyncio` is built
on this: coroutines (`async def` + `await`) are generators that yield control
to an event loop, which decides what to resume next.

A thread requires synchronisation whenever shared state is touched, because
the scheduler can interrupt anywhere. A generator requires no synchronisation,
because only one side runs at a time.



### Under the Hood: C

Python implements generators in CPython's bytecode interpreter. In C you
implement the same idea manually: a struct holds the generator's state (its
frame), and a `next` function advances it by one step.

#### The State Machine Pattern

```c
typedef struct {
    int value;    /* the yielded value    */
    int done;     /* 1 when exhausted     */
    /* -- frame -- */
    int i;        /* local variable       */
} counter_gen;

void counter_init(counter_gen *g) { g->i = 0; g->done = 0; }

void counter_next(counter_gen *g) {
    if (g->done) return;
    g->value = g->i;
    g->i++;
    /* never done -- infinite sequence */
}
```

This is a counter generator. Each call to `counter_next` advances the frame
by one step and writes the new value into `g->value`. The consumer reads
`g->value` after each call, exactly as it would read from `next()` in Python.

#### Fibonacci Generator in C

```c
typedef struct {
    long value;
    int  done;
    long a, b;     /* frame: two local variables */
} fib_gen;

void fib_init(fib_gen *g) { g->a = 0; g->b = 1; g->done = 0; }

void fib_next(fib_gen *g) {
    if (g->done) return;
    g->value = g->a;
    long tmp = g->a + g->b;
    g->a     = g->b;
    g->b     = tmp;
}
```

#### Chained Generators: Filter

A filter generator wraps another generator and skips elements that fail a
predicate:

```c
typedef int (*pred_fn)(long);

typedef struct {
    long    value;
    int     done;
    fib_gen *source;    /* pointer to upstream generator */
    pred_fn  pred;
} fib_filter_gen;

void fib_filter_next(fib_filter_gen *g) {
    while (!g->source->done) {
        fib_next(g->source);
        if (g->pred(g->source->value)) {
            g->value = g->source->value;
            return;
        }
    }
    g->done = 1;
}
```

The filter pulls from its source until it finds a matching element or the
source is exhausted. This is the C equivalent of chaining generators in
Python: each generator holds a pointer to the upstream generator, and pulls
from it on demand.

#### The Program Counter Problem

The pattern above works cleanly when the generator has a single yield point
per iteration (a while loop with one `yield`). When a Python generator has
*multiple* yield points, the state machine needs an explicit program counter
field:

```c
typedef struct {
    int   value;
    int   done;
    int   pc;     /* program counter: which yield to resume at */
    int   x;
} multi_gen;

void multi_next(multi_gen *g) {
    switch (g->pc) {
    case 0: g->value = 1;      g->pc = 1; return;
    case 1: g->value = g->x;   g->pc = 2; return;
    case 2: g->value = g->x*2; g->pc = 3; return;
    case 3: g->done  = 1;      return;
    }
}
```

Each `case` corresponds to a yield point. `g->pc` stores where to resume.
This is exactly what CPython stores in the generator frame as the bytecode
instruction pointer.

This technique -- a struct with a `pc` field and a `switch` -- is called a
*Duff's device* or a *protothreads* pattern. Simon Tatham's essay on
coroutines in C formalises it. It is also the basis of C++20 coroutines,
which compile `co_yield` into a state machine with an explicit resume index.

#### Why C Makes This Painful

Python automates the frame allocation, the state machine compilation, and the
program counter management. In C you write all of that by hand, for each
generator, with no language support. This is not a fundamental limitation --
the computation is the same -- but the boilerplate cost is high, and the risk
of frame-lifetime bugs (the same pointer hazard as in section 2) is real.



### Cost Model

| Feature | Python generator | C state machine |
|---------|------------------|-----------------|
| Frame allocation | heap, automatic | stack or heap, manual |
| Suspension | automatic at `yield` | explicit `return` + `pc` |
| Chaining | natural (for x in source) | pointer to upstream struct |
| Infinite sequences | supported | supported |
| Per-step overhead | frame restoration + bytecode | one function call + switch |
| Memory per generator | ~200 bytes (CPython frame) | sizeof(struct) |

The C state machine is leaner in memory and faster per step, but requires
substantially more code per generator. Python's overhead is high enough that
for numerical work, generators over raw Python values are slower than
equivalent C loops by an order of magnitude. For I/O-bound or large-data
work, the memory and streaming benefits dominate.



### Concurrency Link

Generators connect to concurrency in two ways.

*As lightweight coroutines.* A generator suspends cooperatively at `yield`,
resuming only when the consumer calls `next()`. Multiple generators can
interleave on a single thread without OS scheduling overhead, without locks,
and without the memory cost of a full thread stack (typically 1--8 MB per
thread vs. a few hundred bytes per generator frame).

Python's `asyncio` event loop is built on this: it holds a queue of
coroutines, resumes each one when its awaited I/O is ready, and lets it run
until it yields again. No thread switching, no kernel involvement per
coroutine switch, no synchronisation needed between coroutines that share no
mutable state.

*As backpressure.* In a lazy pipeline, the consumer controls the rate. If the
consumer slows down, the producer does not run ahead -- it simply is not
called. This is *backpressure*: the downstream stage applies pressure upstream
by not requesting the next value. In an eager pipeline there is no such
mechanism; the producer runs at full speed and the consumer must buffer or
drop. Lazy pipelines are naturally bounded in memory without explicit
buffering logic.

The contrast with threads is sharp. Two threads in a producer-consumer
relationship require a bounded queue, locks on the queue, condition variables
for signalling, and careful management of what happens when the queue is full
or empty. Two chained generators need none of this: the consumer's call to
`next()` is the signal, and the generator's return is the handoff.



*Next: [7. Functors](../functors/README.md)--mapping over values inside a
context, and why the container should not dictate the transformation.*
