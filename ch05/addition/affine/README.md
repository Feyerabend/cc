
## What Are Affine Types?

*Affine types* are types where values can be used *at most once*.
This is a constraint from linear logic/type theory.

The type system hierarchy:
- *Unrestricted types*: Use as many times as you want (normal types in most languages)
- *Affine types*: Use *at most once* (0 or 1 times)
- *Linear types*: Use *exactly once* (must use, cannot drop)
- *Relevant types*: Use *at least once* (must use, can use many times)

Ownership systems are essentially *affine type systems* with
explicit operations for copying and dropping.


### The Core Mechanism: Use Tracking

An affine type system tracks, for each variable, whether it has been "consumed"
(used in a way that invalidates further use).


#### Traditional Compiler Symbol Table:
```
Variable | Type  | In Scope
---------|-------|----------
x        | int   | yes
y        | File  | yes
```

#### Affine Type System Symbol Table:
```
Variable | Type  | In Scope | Consumed | Last Use Location
---------|-------|----------|----------|------------------
x        | int   | yes      | no       | -
y        | File  | yes      | yes      | line 42
```



### How The Compiler Enforces Affine Types

#### Step 1: Mark Consuming Operations

The compiler needs to know which operations "consume" a value:

```
// Type signatures with consumption markers
fn move_value(x: T) -> U           // consumes x (takes ownership)
fn borrow_value(x: &T) -> U        // borrows x (doesn't consume)
fn copy_value(x: T) -> T where T: Copy  // doesn't consume (copies)
```

*Consuming operations*:
- Moving into another variable
- Passing to a function that takes ownership
- Returning from a function
- Storing in a data structure

*Non-consuming operations*:
- Passing by reference
- Reading primitive values (if they're copyable)


#### Step 2: Track Consumption During Type Checking

The compiler does a flow-sensitive analysis:

```
let x = File::open("data.txt")    // x: File (affine type)
                                   // State: x=[unconsumed]

send_file(x)                       // consumes x
                                   // State: x=[consumed at line N]

print(x)                           // ERROR: x already consumed
                                   // Compiler: "value used after move"
```

*The algorithm*:
```
for each variable v of affine type T:
    consumed[v] = false
    
for each statement S in control flow order:
    if S uses v in consuming way:
        if consumed[v]:
            ERROR: "use after consume"
        consumed[v] = true
        record_consumption_site(v, S)
    elif S uses v in non-consuming way:
        if consumed[v]:
            ERROR: "use after consume"
```


#### Step 3: Handle Control Flow

The tricky part: branches and loops.

*Example problem*:
```
let x = allocate()

if condition:
    consume(x)     // x consumed in this branch
else:
    print("skip")  // x not consumed here

// Is x consumed here? Depends on runtime value of condition!
```

*Solution: Conservative join*

At control flow joins (where branches meet), the compiler takes the *conservative union*:

```
Branch 1: x=[consumed]
Branch 2: x=[unconsumed]
Join: x=[may be consumed] = treat as [consumed]
```

This is pessimistic but safe - it may reject valid programs:

```
let x = allocate()

if condition:
    consume(x)
    x = allocate_new()  // re-bind x
else:
    // x still valid
    
use(x)  // Actually safe but many compilers reject this
```

*More sophisticated approach*: Path-sensitive analysis

Track consumption state along each path:
```
Path 1 (condition=true): consume(x), rebind x, use(x)
Path 2 (condition=false): use(x)
Result: Accept
```

This requires more complex analysis (symbolic execution or abstract interpretation).


#### Step 4: Loops Are Special

Loops are the hardest case:

```
let x = allocate()

while condition:
    consume(x)  // What about second iteration?
```

*The rule*: A loop body cannot partially consume affine values from outer scopes.

```
let x = allocate()

while condition:
    consume(x)  // ERROR: x might be consumed multiple times
```

*Why?* If the loop runs twice, x is consumed on iteration 1, but iteration 2 tries to consume it again.

*Solution patterns*:

1. *Consume before loop*:
```
let x = allocate()
consume(x)
while condition:
    // x not accessible here
```

2. *Create fresh value each iteration*:
```
while condition:
    let x = allocate()  // Fresh each time
    consume(x)
```

3. *Move consumption outside*:
```
let x = allocate()
let result = process(x)  // consume once
while condition:
    use(result)  // use result repeatedly
```


### Affine Types + Borrowing

Pure affine types are too restrictive--you can't use anything twice!
This is where *borrowing* comes in as an escape hatch.

*The insight*: Borrowing creates a *new* affine type (the reference)
that's separate from the original:

```
let x = allocate()           // x: T (affine)
let r = borrow(x)            // r: &T (also affine!)
use(r)                       // consumes r
// But x is still valid!
```

*How this works*:
- Borrowing doesn't consume the original
- But it creates restrictions (borrow checking)
- The reference `r` is itself affine (can use at most once, unless copyable)

*The compiler tracks two things*:
1. *Consumption state* (affine types)
2. *Borrow state* (what's currently borrowed)

```
Variable | Consumed | Borrowed By
---------|----------|------------
x        | no       | {r1, r2}
r1       | no       | {}
r2       | yes      | {}
```


### Implementation: Type System Rules

Formally, the compiler implements these typing rules:

*Variable use (unrestricted types)*:
```
Γ ⊢ e: T    (x: T unrestricted)
--------------------------------
Γ, x:T ⊢ x: T    (Γ unchanged)
```

*Variable use (affine types)*:
```
Γ ⊢ e: T    (x: T affine)    x ∉ used(Γ)
-----------------------------------------
Γ, x:T ⊢ x: T    (mark x as used in Γ)
```

*The key difference*: Affine types modify the context Γ to mark the variable as used.

*Sequential composition*:
```
Γ₁ ⊢ e₁: T₁    Γ₂ ⊢ e₂: T₂
-----------------------------  where Γ₂ is Γ₁ after e₁
Γ₁ ⊢ e₁; e₂: T₂
```

The environment "flows" through the program, accumulating consumption information.


### Practical Compiler Passes

A real compiler implements this in several passes:

#### Pass 1: Type Inference with Affine Annotations
```
fn infer_types(ast):
    for each expression e:
        type_of[e] = infer(e)
        if is_affine(type_of[e]):
            mark_affine[e] = true
```

#### Pass 2: Build Use-Def Chains
```
fn build_chains(ast):
    for each variable use u:
        find definition d
        add_edge(d -> u)
```

#### Pass 3: Consumption Analysis
```
fn check_affine(cfg: ControlFlowGraph):
    worklist = [entry_block]
    state = {var: Unconsumed for var in affine_vars}
    
    while worklist:
        block = worklist.pop()
        
        for stmt in block:
            if consumes(stmt, var):
                if state[var] == Consumed:
                    error("use after move")
                state[var] = Consumed
        
        for successor in block.successors:
            new_state = merge(state, successor.state)
            if new_state != successor.state:
                successor.state = new_state
                worklist.append(successor)
```

#### Pass 4: Borrow Checking (if combined with borrowing)
```
fn check_borrows(cfg):
    for each block:
        active_borrows = set()
        
        for stmt in block:
            if creates_borrow(stmt, var):
                check_borrow_rules(var, active_borrows)
                active_borrows.add(borrow_ref)
            
            if ends_borrow(stmt, ref):
                active_borrows.remove(ref)
```


### Why Affine Types Enable Optimisation

Once the compiler proves affine properties, it can optimise aggressively:

*1. No alias analysis needed*:
```
let x = allocate()
modify(x)
// Compiler knows: no other reference to x exists
// Can optimize assuming x is not aliased
```

*2. Automatic cleanup at consumption*:
```
consume(x)  // Compiler inserts: free(x) immediately after
```

*3. Move operations compile to simple pointer copies*:
```
let y = x   // Just copy pointer, no ref counting or checks
```

*4. Stack allocation of "heap" objects*:
```
let x = allocate()  // Compiler: x is never shared
consume(x)           // Compiler: x dies here
// Compiler: allocate x on stack instead!
```


### The Tradeoff

Affine types enforce *spatial safety* (memory safety)
but sacrifice some *expressiveness*:

*Cannot express*:
```
let x = allocate()
let y = x
let z = x  // Would need x three times - not affine!
```

*Must explicitly copy*:
```
let x = allocate()
let y = copy(x)  // Explicit
let z = copy(x)
```

This is the fundamental tradeoff: *safety and optimisation vs. convenience*.




### Python Example `affine.py`


#### 1. *AffineChecker Class*
This tracks the consumption state:
```python
def consume(self, var: str):
    if info.consumed:
        error("Use after move")  # ← The key check!
    info.consumed = True
```


#### 2. *Type System*
- `VALUE`: Normal copyable types (unrestricted)
- `AFFINE`: Use at most once (heap-allocated values)
- `REFERENCE`: Borrowed references


#### 3. *Memory Management*
- `new(42)` allocates on simulated heap
- Returns affine type (can only use once)
- Must explicitly `drop()` to free


### When Running ..

The interpreter shows:
- *DECLARE*: When variables are created
- *CONSUME*: When affine values are moved (the crucial operation!)
- *USE/READ*: When values are accessed
- *ALLOC/FREE*: Memory operations
- *Errors*: Use-after-move caught at runtime (would be compile-time in real compiler)


You'll see 5 examples showing:
1. Basic move semantics
2. Use-after-move error
3. Explicit copy (original still valid)
4. Arithmetic with affine types
5. Memory leak (forgot to drop)

The `AffineChecker` is doing what a real compiler does--tracking which variables
are consumed and catching violations. The only difference is this checks at *runtime*;
a real compiler does it during *type checking* (compile time).


