
## Categorical Stack VM: A Toy Implementation for Exploring Category Theory

This project implements a very simple stack-based virtual machine (VM) in Python,
where core concepts from category theory are mapped to programming constructs.
The goal is *not* to create a practical VM for production use (it's deliberately
decorative and inefficient), but to provide a concrete, runnable example that
helps demystify *some* category theory through code. By seeing abstract ideas like
objects, morphisms, products, and coproducts "in action" on a stack, you can
experiment with how they compose and transform data.

If you're new to category theory, think of it as a mathematical framework for
describing structures and transformations in a general way. Here, we treat the
VM's stack as a "category" where:
- *Objects* are types (e.g., `Int`, `Bool`, or composite types like products).
- *Morphisms* (arrows between objects) are instructions that reliably transform
  the stack from one type configuration to another.
- *Composition* is simply running instructions in sequence, which must preserve
  type safety.

The code in `cat_vm.py` builds this out with a type system, typed values,
instructions, and a VM executor. It includes examples for arithmetic, stack
manipulation, pairs (products), either-types (sums), and basic control flow.
Running the code will execute demo programs and tests to illustrate these.

*Is this helpful or a hindrance?* It can be a great departure point if you're
a programmer looking to ground category theory in something tangible--run the
code, tweak instructions, and see how types flow. However, it might hinder if
you're expecting a rigorous mathematical treatment; the mapping is inspirational
rather than precise (e.g., the stack isn't a full category, and some type
transformations are simplified). Use it as a playground, not a textbook.
For deeper understanding, pair it with resources like *Category Theory for Programmers*
by Bartosz Milewski, or look at some other code such as [COOL](./../lang/cool/).

It even might feel like "crammed," as the nature of traditional stack-based
virtual machines is quite the opposite that of category theory. However,
if you come from a more "imperative" stance, it might help with some concepts.

Read on some more [concepts](./DETAILS.md) in CT.


### Core Concepts Mapped to Code

In category theory, *objects* are the "things" we work with--no internal
structure assumed, just their relationships via morphisms.

In the VM:
- Types (subclasses of `Type`) represent objects:
  `IntType`, `BoolType`, `StrType`, `UnitType`.
- Composite types:
  - `ProductType(left: Type, right: Type)`: Like a tuple `(A × B)`,
    holding two values together.
  - `SumType(left: Type, right: Type)`: Like an either/or type `(A + B)`,
    holding one value tagged as left or right.
- `StackType(types: list[Type])`: The entire stack's type, e.g., `[Int, Bool]`,
  treating the stack as a structured object.

Values are wrapped in `TypedValue(typ: Type, value: Any)` to enforce type awareness.
This prevents mismatches at runtime, mirroring how categories ensure morphisms
connect compatible objects.


#### Instructions as Morphisms
Morphisms are functions between objects: if `f: A → B`, applying
`f` to something of type `A` yields `B`.

In the VM:
- Each `Instruction` subclass is a morphism that transforms the stack:
  - `execute(stack: list[TypedValue]) → list[TypedValue]`:
    Applies the transformation to values.
  - `type_transform(stack_type: StackType) → StackType`:
    Describes the type-level change (like a type signature).
- Examples:
  - `Push(value: TypedValue)`: Morphism from stack `S` to `(T : S)`, where `T`
    is the pushed type. Adds a value without altering the rest.
  - `Add()`: Morphism from `(Int : Int : S)` to `(Int : S)`. Combines two ints via addition.
  - Stack ops like `Dup()`, `Swap()`, `Rot()`: Structural morphisms that rearrange
    without changing types fundamentally (like isomorphisms in categories).

This setup ensures instructions are composable: sequencing them
builds larger morphisms, as long as types align.


#### Categorical Products (Pairs/Tuples)
Products model "both A and B" with projections to extract each part.

In the VM:
- `Pair()`: Takes `(A : B : S)` and produces `((B × A) : S)`. Note the order (left is bottom,
  right is top--stack convention).
- `Fst()`: From `((A × B) : S)` to `(A : S)`—extracts the first (left) component.
- `Snd()`: Extracts the second (right).

Example from the code:
```python
program = [
    Push(TypedValue(IntType(), 42)),
    Push(TypedValue(IntType(), 17)),
    Pair(),  # Stack: [(42 × 17)]
    Dup(),
    Fst(),   # Stack: [42, (42 × 17)]
    Swap(),
    Snd()    # Stack: [42, 17]
]
```
This demonstrates universal property sketches: you can build and dismantle pairs predictably.


#### Categorical Coproducts (Sums/Eithers)
Coproducts model "either A or B" with injections to embed values and
case analysis to handle branches.

In the VM:
- `InL(right_type: Type)`: From `(A : S)` to `((A + right_type) : S)`--tags as "left".
- `InR(left_type: Type)`: Tags as "right".
- `Case(left_prog: list[Instruction], right_prog: list[Instruction])`: From `((A + B) : S)`
  branches to either program, feeding the untagged value.

Example from the code (simplified):
- Inject 42 as left in `(Int + Bool)`, then case: double if left, drop and push 0 if right.
This handles alternatives without explicit conditionals in the main flow--failure or variants propagate.


#### Control Flow and Quotations
- `Quote(program: list[Instruction])`: Pushes a program as data (like a function value).
- `Call()`: Executes a quoted program.
- This hints at higher-order morphisms, but it's basic--no full closures.

The `Case` instruction uses branching programs, showing how morphisms can compose
conditionally while staying type-safe.


#### The VM as a State Transformer
Tying back to the original README's monadic perspective: the entire VM is a state
machine where state = stack + (implicit) program counter.

Each instruction is like a monadic action:
- `State → (Value, State)` (though here, values are on the stack, no separate output).
- Sequencing via `run(program)` is like monadic bind: thread the stack through each step.

In category theory terms, this is an endofunctor on the category of states, but the
code keeps it simple. You could refactor the VM into a full `State` monad for purity.



### Getting Started
- Run `python cat_vm.py` to see examples: arithmetic, stack ops, products, sums, comparisons, and factorial.
- Experiment: Add new types/instructions (e.g., a `ListType` with functor-like `Map`).
- Trace mode (`vm.trace = True`) shows stack transformations step-by-step.

Limitations and Departure Points:
- *Type system is static-ish but runtime-checked*: No full inference; `type_transform` is for illustration.
- *Not a real category*: No formal proofs of laws (e.g., associativity, identities).
  Instructions compose, but edge cases (empty stacks) error out.
- *Still some departure ideas*:
  - Extend to functors: Add a `Map` instruction for `ProductType` or `SumType`
    to apply morphisms inside without unpacking.
  - Monadic refactor: Rewrite `execute` as a `State[list[TypedValue], None]` monad.
  - Explore Kleisli categories: Treat instructions as arrows in a category where
    composition handles effects (like errors in sums).

This VM shows category theory isn't just abstract--it's a lens for designing composable systems.
Start here, but then: dive into proper category theory for the math!

