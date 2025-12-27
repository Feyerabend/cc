
## Category Theory as an Abstract Machine (VM / Interpreter)

This is not intended as a blueprint for building a VM using category-theoretic
concepts. Rather, it serves as an illustration of how these concepts operate.
Since we have consistently advocated the use of VMs as a tool for understanding,
this example demonstrates their explanatory power.


### Functors: mapping without changing structure

A functor captures the idea of applying a function inside a structure
without modifying the structure itself.

In Haskell-like pseudocode:

```haskell
class Functor f where
    fmap :: (A -> B) -> f A -> f B
```

The key idea is that fmap applies a function to the contents, not to the container.

For lists:

```haskell
map (+1) [1,2,3] == [2,3,4]
```

The list remains a list, with the same length and ordering. Only the elements change.

For optional values (Maybe):

```haskell
fmap (+1) (Just 3) == Just 4
fmap (+1) Nothing  == Nothing
```

No conditionals are needed. The functor handles absence uniformly.

What makes this powerful is that the same code shape works for many data types.
The functor laws guarantee predictable behaviour: mapping the identity function
does nothing, and mapping composed functions is the same as composing maps.



#### Endofunctors in programming

In most programming languages, functors map types to types within the same universe:

```haskell
List   :: Type -> Type
Maybe  :: Type -> Type
IO     :: Type -> Type
```

This "type-to-type" mapping is exactly what an endofunctor is. The mapping preserves
how functions compose, which allows generic code to work uniformly across containers and effects.



### Monads: sequencing computations with context

A monad extends a functor with a way to sequence computations that carry context.

In simplified form:

```haskell
class Monad m where
    return :: A -> m A
    (>>=)  :: m A -> (A -> m B) -> m B
```

The bind operator (>>=) takes the result of one computation and feeds it into the next,
while preserving the surrounding context.



#### Example: Maybe monad (failure handling)

```haskell
safeDiv x y =
    if y == 0 then Nothing else Just (x / y)

Just 10 >>= \x -> safeDiv x 2   == Just 5
Just 10 >>= \x -> safeDiv x 0   == Nothing
Nothing >>= \x -> safeDiv x 2   == Nothing
```

Failure propagates automatically. There is no need to check for errors at every step.

The monad laws ensure that this propagation behaves consistently, no matter how computations are grouped.



#### Example: State monad (implicit state threading)

A stateful computation can be modelled as a function:

```haskell
State s a = s -> (a, s)
```

Reading and writing state:

```haskell
get :: State s s
put :: s -> State s ()
```

Sequencing:

```haskell
put 5 >>= \_ -> get
```

This reads as: update the state to 5, ignore the trivial result, then read the state.
The explicit state-passing is hidden, but still fully controlled and predictable.



#### Example: IO monad (controlled side effects)

```haskell
getLine >>= \line ->
putStrLn line
```

Although input and output are inherently impure, the monad enforces an explicit order
of operations. Effects cannot be duplicated, reordered, or discarded accidentally.



#### Example: Parser monad (composable syntax)

A parser can be viewed as:

```haskell
Parser a = String -> Maybe (a, String)
```

Simple parsers are combined into larger ones:

```haskell
parseNumber >>= \n ->
parsePlus   >>
parseNumber >>= \m ->
return (n + m)
```

Each parser consumes input and passes the remainder along. Failure short-circuits automatically.




These abstractions are not about clever notation. They provide:
- a uniform way to structure programs,
- predictable composition guaranteed by laws,
- reusable patterns independent of concrete data.

Category theory supplies the rules that make these abstractions reliable.
Programming supplies the instances that make them useful.



### The core idea

A virtual machine is, at heart, a state transition system.

At each step, the machine:
- has some internal state,
- executes an instruction,
- produces a new state (and possibly a value),
- then continues.

A monad captures exactly this pattern.

Formally, a monadic computation can be read as:

```
current_state -> (result, next_state)
```

That is already a small-step operational semantics.



#### A minimal virtual machine

Consider a very small stack-based VM.

```
State = (stack, program_counter)
```

An instruction transforms the state:

```python
def step(state):
    stack, pc = state
    instr = program[pc]

    if instr == "PUSH 3":
        return ([3] + stack, pc + 1)

    if instr == "ADD":
        a, b, *rest = stack
        return ([a + b] + rest, pc + 1)
```

This is a pure function:

```
State -> State
```

No magic, no effects — just explicit state passing.



#### Encoding this as a monad

Now rewrite this idea in monadic form.

We define a computation type:

```
Computation = State -> (Value, State)
```

In Python-like pseudocode:

```python
def bind(m, f):
    def new_comp(state):
        value, state2 = m(state)
        return f(value)(state2)
    return new_comp
```

This bind is exactly the monadic (`>>=`).

The machine’s state is now implicitly threaded through computations.



#### Instructions as monadic actions

Each VM instruction becomes a computation.

```python
def push(n):
    def comp(state):
        stack, pc = state
        return None, ([n] + stack, pc + 1)
    return comp

def add():
    def comp(state):
        stack, pc = state
        a, b, *rest = stack
        return None, ([a + b] + rest, pc + 1)
    return comp
```

Sequencing instructions:

```
program =
    push(3) >>= \
    push(4) >>= \
    add()
```

This is not metaphorical.
This is a virtual machine, written in monadic form.



#### Operational semantics view

In operational semantics, we often write transitions like:

```
⟨ADD, (a :: b :: s, pc)⟩ → ⟨(), (a+b :: s, pc+1)⟩
```

The monadic version encodes the same transition as a function:

```
State -> ((), State)
```

Bind corresponds to sequencing of transitions.

So:
- VM step rules = monadic actions
- Instruction sequencing = bind
- Machine state = monad state
- Program execution = monadic composition



#### Why this is powerful

Once written this way:
- the VM is pure and compositional
- instruction effects are explicit
- reasoning becomes algebraic
- optimisation becomes lawful rewriting

For example, instruction fusion corresponds to monad law–preserving rewrites.

Associativity of bind:

```
(m >>= f) >>= g == m >>= (\x -> f x >>= g)
```

means instruction grouping does not affect behaviour--exactly what you want from a machine.



### From monads to abstract machines

Many well-known machines fit this pattern:
- State monad -> store-passing machines
- Writer monad -> tracing and logging machines
- Maybe monad -> machines with failure
- Continuation monad -> control-flow machines
- IO monad →-> interaction machines

The SECD machine, CEK machine, and many interpreters can be derived by choosing:
- a state space,
- a set of monadic actions,
- a sequencing rule.

Category theory does not replace operational semantics.
It organises it.



### Comments on the Categorical Stack VM

The accompanying `cat_vm.py` takes a different perspective from the monadic VM sketched above.
Instead of modelling the machine itself as a monad (implicitly threading a global state), it
treats the *stack-based machine as a category* in a more direct, structural way:

- *Objects* are stack configurations (`StackType` – a list of types).
- *Morphisms* are instructions, each transforming one stack type into another.
- *Composition* is simply sequencing instructions in a program.

This makes the VM an interpretation of a *strict cartesian closed category* (or at least a
cartesian category with coproducts) where:
- Products (`Pair`, `Fst`, `Snd`) model categorical products.
- Coproducts (`InL`, `InR`, `Case`) model sums (tagged unions).
- The stack acts as a context or environment.


#### What works well

- *Explicit categorical structure*: The implementation demonstrates how classic stack
  operations (dup, swap, drop) and arithmetic are ordinary morphisms, while products
  and coproducts are first-class. This makes the connection to category theory tangible.

- *Static type safety*: Every instruction carries both a runtime effect (`execute`) and
  a type-level effect (`type_transform`). In principle this enables full type checking
  of programs before execution (though the current code only checks at runtime).

- *Educational clarity*: Seeing `Pair`/`Fst`/`Snd` next to `Add`/`Mul` highlights that
  all operations are arrows between objects, regardless of whether they are "data" or
  "control".


#### Trade-offs and limitations (as noted in the source)

We explicitly marks the file as "a more decorative implementation of category
theory concepts".

- *No true monadic layering*: Unlike the earlier monadic VM example, the state (the stack)
  is passed explicitly and mutated in place. There is no hidden state threading via `>>=`.

- *Control flow is limited*: Branching is only provided via `Case` on sums, and higher-order
  functions via crude `Quote`/`Call`. No general recursion or loops are provided, making
  non-trivial algorithms (e.g., proper recursive factorial) awkward.

- *Type inference is minimal*: `type_transform` is implemented per-instruction, but there
  is no global type checker that verifies an entire program.

- *Performance and practicality*: This is deliberately not optimised for real use.
  It prioritises conceptual clarity over efficiency.

In short, `cat_vm.py` is a *categorical playground* rather than a production virtual machine.
It illustrates how a programming language can be viewed as a category with the stack as the
dominant structure, whereas the monadic view in the earlier sections shows how a VM can be
expressed *inside* a single monad (State, IO, etc.).

Both perspectives are complementary:
- The monadic view excels at *hiding plumbing* (state, effects) and enabling algebraic reasoning.
- The categorical stack view excels at *exposing structure* (products, coproducts, combinators)
  and making the type system the central organising principle.

Together they show why category theory is so powerful for language and machine design: it offers
multiple lenses, each revealing different opportunities for abstraction and correctness.

