
## WAM

The Warren Abstract Machine (WAM) is a highly influential virtual machine designed
specifically for implementing the logic programming language Prolog. Developed by
David H. D. Warren in the early 1980s, it provides an efficient execution model by
transforming Prolog's high-level logic into lower-level operations tailored to a virtual
machine architecture.


### High-Level Purpose

The WAM efficiently executes Horn clause logic by compiling Prolog programs into a
sequence of low-level instructions. These instructions are interpreted or executed
by the WAM, leveraging Prolog’s core features like unification, backtracking, and
logical variables.

*Core Features of WAM*

1. *Unification*: Central to Prolog, unification matches terms (variables, constants,
   or structures). The WAM includes optimised instructions for unification, handling
   variable bindings and logical constraints.
2. *Backtracking*: Prolog uses backtracking to explore alternative solutions when a
   computation fails. The WAM implements this via a stack-based structure with choice
   points for efficient state restoration. (More on backtracking in ch07
   [WAM](./../../../ch07/mech/backtrack/).)
3. *Efficient Term Representation*: Terms (variables, constants, lists, structures)
   are compactly stored in memory using tagged cells to differentiate types.


### Components of the WAM

#### 1. Registers

The WAM employs registers to manage execution state:
- *Instruction Pointer (IP)*: Points to the next instruction.
- *Heap Pointer (HP)*: Tracks dynamic term allocation.
- *Current Predicate (CP)*: Manages the current predicate context.

In the Python implementation:

```python
self.registers = {
    'IP': 0,    # instruction pointer
    'CP': 0,    # current predicate
    'HP': 0,    # heap pointer
}
```

#### 2. Memory Areas

The WAM organises memory into distinct areas:
- *Heap*: Stores terms like variables and constants.
  
```python
self.heap = []  # term storage
```

- *Stack*: Holds intermediate values, such as variable bindings.

```python
self.stack = []  # execution stack
```

- *Call Stack*: Tracks return addresses for nested predicate calls.

```python
self.call_stack = []  # procedure return addresses
```

- *Choice Points*: Stores execution state snapshots for backtracking.

```python
self.choice_points = []  # backtrack points
```

- *Trail*: Records variable bindings for undoing during backtracking.

```python
self.trail = []  # trail for variable bindings
```

These areas enable unification, recursion, and nondeterministic execution.

#### 3. Instructions

The WAM uses a specialized instruction set for Prolog operations, stored as:

```python
self.instructions = []  # loaded program
```

Instructions are tuples, e.g.:

```python
('CALL', ('child', 1), 0)  # Invokes child/1 predicate
```

Key instructions include:
- *CALL*: Invokes a predicate.
- *GET_VARIABLE*: Allocates a variable reference.
- *PUT_CONSTANT*: Places a constant on the heap.
- *PROCEED*: Completes a predicate and returns.
- *CUT*: Discards choice points to prune alternatives.
- *TRY_ME_ELSE*, *RETRY_ME_ELSE*, *TRUST_ME*: Manage multiple clauses for backtracking.
- *UNIFY_VARIABLE*: Unifies a variable with a stack term.
- *BUILTIN*: Executes built-in predicates like `\=` (inequality).
- *HALT*: Terminates execution.

The `fetch_execute` method drives execution by fetching, decoding, and executing
instructions, updating registers and memory.


#### 4. Compilation

Prolog programs are compiled into WAM instructions via the `Compiler` class. It
transforms facts, rules, and queries into low-level instructions, managing:
- *Variables*: Mapped to indices (`self.vars`).
- *Constants*: Indexed for efficient access (`self.constants`).
- *Predicates*: Mapped to instruction addresses (`self.predicates`).

For example, a fact:

```prolog
parent(zeb, john).
```

Compiles to:

```python
[
    ('PUT_CONSTANT', 0, 0),  # 'zeb' -> argument 0
    ('PUT_CONSTANT', 1, 1),  # 'john' -> argument 1
    ('PROCEED', 0, 0)        # Return
]
```

A query:

```prolog
?- child(X).
```

Compiles to:

```python
[
    ('GET_VARIABLE', 0, 0),  # allocate variable 'X'
    ('CALL', ('child', 1), 0)  # call child/1
]
```

Multi-clause predicates use `TRY_ME_ELSE`, `RETRY_ME_ELSE`, and `TRUST_ME` to
handle backtracking across clauses.

#### 5. Execution

Execution begins by loading compiled instructions:

```python
vm.load(compiler)
```

The WAM starts at the query’s entry point, e.g.:

```python
vm.registers['IP'] = vm.predicates[('child', 1)]
```

The `fetch_execute` method cycles through:
- *Unification*: Matches terms using `unify` and `deref`.
- *Predicate Calls*: Invokes predicates via `CALL` and `PROCEED`.
- *Backtracking*: Restores state using `backtrack` and choice points.
- *Solution Storage*: Saves variable bindings in `self.solutions`.

For example, the query `?- child(X)` finds all `X` where `child(X)` holds, using
backtracking to explore multiple solutions.


#### 6. Built-in Predicates

The WAM supports built-in predicates like `\=` (inequality), compiled and executed via:

```python
self.builtins = {r'\=': self.compile_inequality}
```


#### 7. Example Program

The provided program includes facts, rules, and queries:

```python
program = [
    ['parent', 'zeb', 'john'],
    ['parent', 'zeb', 'jane'],
    ['parent', 'john', 'jim'],
    ['parent', 'jane', 'alice'],
    [':-', ['child', 'X'], ['parent', 'X', '_'], '!'],
    [':-', ['grandparent', 'X', 'Z'], ['parent', 'X', 'Y'], ['parent', 'Y', 'Z']],
    [':-', ['sibling', 'X', 'Y'], ['parent', 'Z', 'X'], ['parent', 'Z', 'Y'], [r'\=', 'X', 'Y']],
    ['?-', ['child', 'X']],
    ['?-', ['grandparent', 'zeb', 'Who']],
    ['?-', ['sibling', 'john', 'Sibling']]
]
```

This program defines family relationships and queries children, grandparents, and siblings, demonstrating
unification, backtracking, and cuts.

### Conclusion

The Python implementation in `wam.py` is a simplified yet functional abstraction of the WAM. It replicates
core components—registers, memory areas, instructions, and backtracking—while supporting Prolog’s unification
and predicate execution. The `Compiler` and `WAM` classes work together to compile and execute Prolog programs,
simulating the WAM’s model.

The WAM remains a cornerstone of logic programming, influencing modern Prolog systems like SWI-Prolog and
SICStus Prolog[^sics]. Its design has also impacted constraint logic programming and theorem proving systems,
underscoring its lasting significance.

[^sics]: In the effort to keep pace with developments in computing during the mid-1980s—particularly the
"Fifth Generation" initiative (cf. [SEASONS](./../../../ch08/ai/SEASONS.md))--the Swedish state established
the Swedish Institute of Computer Science (SICS): https://en.wikipedia.org/wiki/Swedish_Institute_of_Computer_Science.
Among the many projects produced there was, naturally, a Prolog engine: https://sicstus.sics.se/.
Professor Sten Åke Tärnlund at Uppsala was a leading figure in advancing the logic programming approach to AI,
along with several of his students. For a time, I attended Upmail, a seminar held near the institution where
Tärnlund was affiliated. The seminar brought together many topics that interested me, such as programming and
its connections to formal logic. (Bibliography of Tärnlund: https://dblp.org/pid/t/StenAkeTarnlund.html.)
