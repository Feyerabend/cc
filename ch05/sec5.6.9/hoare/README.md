
## Hoare Logic: From Theory to Compiler Applications

We will return to Hoare Logic in [Section 8.11](./../../../ch08/sec8.11).
Here we will focus on partly what it is actually more extensively due to lack
of space in the book, but also its relation to compilers.

A first implementation for verification checks in in `vcgen.py`.
It can be extended not only to generate, but also to *verify*:
This is done in `vcgen_enhanced.py`. However, it requires installation:
`pip install z3-solver`.

```python
# Add Z3 backend
pip install z3-solver

# Use in compiler pipeline:
# 1. Parse source -> AST
# 2. Type check
# 3. Generate VCs with HoareLogicAnnotator
# 4. Prove VCs with Z3
# 5. Emit verified binary
```



### The Logic

*Hoare Logic*, developed by Tony Hoare in 1969, is a formal system for 
reasoning about the correctness of computer programs. It provides a
mathematical framework to prove that a program satisfies its specification.

1. *Correctness Guarantees*: Mathematical proof that code does what it claims
2. *Bug Prevention*: Find errors before runtime through static analysis
3. *Documentation*: Formal specifications serve as precise documentation
4. *Compiler Optimisations*: Enables aggressive optimisations with correctness guarantees
5. *Critical Systems*: Essential for safety-critical software (aerospace, medical, finance)


A *Hoare triple* has the form:

```
{P} S {Q}
```

Where:
- *P* (Precondition): A logical assertion that must hold before executing S
- *S* (Statement): The program fragment being verified
- *Q* (Postcondition): A logical assertion guaranteed to hold after S executes

*Interpretation*: "If P is true before executing S, then Q will be true after S completes."


#### Simple Example

```
{x = 5}
y := x + 1
{y = 6}
```

This states: "If x equals 5 before the assignment, then y will equal 6 afterward."


### Core Concepts

#### 1. Assertions

*Assertions* are logical formulas that describe program state. They can include:
- *Arithmetic relations*: `x > 0`, `y ≤ 100`
- *Logical connectives*: `P ∧ Q` (and), `P ∨ Q` (or), `¬P` (not)
- *Quantifiers*: `∀x`, `∃x`
- *Implications*: `P → Q`

#### 2. Partial vs. Total Correctness

*Partial Correctness*: `{P} S {Q}`
- If P holds before S and S terminates, then Q holds after

*Total Correctness*: `[P] S [Q]`  
- If P holds before S, then S terminates AND Q holds after
- Requires termination proofs


#### 3. Weakest Precondition (WP)

For a statement S and postcondition Q, the *weakest precondition* WP(S, Q)
is the "weakest" (most general) condition that guarantees Q holds after executing S.

*Example*:
```
WP(x := x + 1, x > 5) = x > 4
```

The weakest condition before `x := x + 1` that guarantees `x > 5` afterward is `x > 4`.


#### 4. Strongest Postcondition (SP)

For a statement S and precondition P, the *strongest postcondition* SP(P, S) is
the "strongest" (most specific) condition guaranteed to hold after S.

*Example*:
```
SP(x = 5, x := x + 1) = x = 6
```



### Rules and Axioms


#### 1. Assignment Axiom

The fundamental rule for assignments:

```
{Q[E/x]} x := E {Q}
```

*Meaning*: To establish Q after `x := E`, we need Q with E substituted for x beforehand.

*Example*:
```
Goal: {?} x := x + 1 {x > 5}

Compute WP: Q = (x > 5), E = x + 1
Substitute: (x + 1 > 5) → (x > 4)

Answer: {x > 4} x := x + 1 {x > 5}
```

#### 2. Sequence Rule (Composition)

To verify sequential statements:

```
{P} S1 {Q}    {Q} S2 {R}
------------------------------
       {P} S1; S2 {R}
```

*Example*:
```
     {x = 0} x := x + 1 {x = 1}
     {x = 1} y := x * 2 {y = 2}
--------------------------------------
{x = 0} x := x + 1; y := x * 2 {y = 2}
```

#### 3. Conditional Rule (If-Then-Else)

```
  {P ∧ B} S1 {Q}    {P ∧ ¬B} S2 {Q}
  ---------------------------------
     {P} if B then S1 else S2 {Q}
```

*Key Insight*: Both branches must establish the same postcondition Q.

*Example*:
```
    {x ∈ ℤ ∧ x ≥ 0 ∧ x < 10}    x := x + 1   {x > 0}
 {x ∈ ℤ ∧ ¬(x ≥ 0 ∧ x < 10)}    x := 0       {x > 0 ∨ x = 0}
---------------------------------------------------------------
{x ∈ ℤ} if (x ≥ 0 ∧ x < 10) then x := x + 1 else x := 0 {x ≥ 0}
```

#### 4. While Loop Rule

The most complex rule - requires finding a *loop invariant* I:

```
     {I ∧ B} S {I}
-------------------------
{I} while B do S {I ∧ ¬B}
```

*Verification Obligations*:
1. *Initialisation*: Precondition implies invariant: `P → I`
2. *Preservation*: Invariant + condition implies invariant after body: `{I ∧ B} S {I}`
3. *Termination*: Eventually ¬B holds (for total correctness)
4. *Postcondition*: Invariant + ¬condition implies postcondition: `I ∧ ¬B → Q`

*Example* (Countdown Loop):
```
// Goal: Prove this loop terminates with y = 10

var x: int := 10;
var y: int := 0;

// Loop invariant: I = (x + y = 10 ∧ x ≥ 0)

while (x > 0) {
    x := x - 1;
    y := y + 1;
}

// Postcondition: x = 0 ∧ y = 10
```

*Proof*:
1. *Initialisation*: `x = 10 ∧ y = 0` → `x + y = 10 ∧ x ≥ 0` ✓
2. *Preservation*: If `x + y = 10 ∧ x ≥ 0 ∧ x > 0` before body, then `(x-1) + (y+1) = 10 ∧ (x-1) ≥ 0` after ✓
3. *Postcondition*: `x + y = 10 ∧ x ≥ 0 ∧ ¬(x > 0)` → `x = 0 ∧ y = 10` ✓

#### 5. Consequence Rule (Strengthening/Weakening)

Allows adapting preconditions and postconditions:

```
P' → P    {P} S {Q}    Q → Q'
------------------------------------
             {P'} S {Q'}
```

*Usage*: Strengthen preconditions (make them more restrictive) or weaken postconditions (make them more general).

#### 6. Procedure Call Rule

For procedures with contracts:

```
        {requires} body {ensures}
--------------------------------------------------------
{P ∧ P → requires} call proc() {ensures → Q}
```

Plus *frame conditions* specifying unmodified variables.



### Hoare Logic in Compilers

Hoare Logic intersects with compiler technology in several ways:


#### 1. Static Verification Passes

Modern compilers can include *verification passes* that:

- *Check array bounds*: Prove all array accesses are within bounds
- *Detect null pointer dereferences*: Prove pointers are non-null before use
- *Verify integer overflow*: Prove arithmetic stays within type bounds
- *Ensure initialisation*: Prove all variables are initialised before use

*Example* (Simplified Compiler Pass):

```python
def verify_array_bounds(ast, bounds_info):
    """Compiler pass using Hoare Logic to verify array safety."""
    
    for node in ast.walk():
        if node.type == "ARRAY_ACCESS":
            array = node.array
            index = node.index
            
            # Generate VC: 0 ≤ index < len(array)
            vc = f"0 ≤ {index} < len({array})"
            
            # Try to prove using constraint solver
            if not can_prove(vc, bounds_info):
                emit_warning(f"Possible out-of-bounds access: {array}[{index}]")
```

#### 2. Optimisations with Correctness Guarantees

Hoare Logic enables *aggressive optimizations* by proving they preserve semantics:

__Loop Invariant Code Motion (LICM)__

*Original*:
```c
while (i < n) {
    x = compute_expensive();  // Doesn't depend on i
    a[i] = x;
    i++;
}
```

*Optimized* (move invariant code outside loop):
```c
x = compute_expensive();
while (i < n) {
    a[i] = x;
    i++;
}
```

*Hoare Logic Verification*:
```
Invariant: I = (∀j < i: a[j] = x ∧ i ≤ n)

{I ∧ i < n} a[i] = x; i++ {I}  ✓ Proven

Therefore optimisation preserves correctness.
```

__Dead Code Elimination__

```c
x = 5;
y = x + 1;  // y = 6
if (y > 10) {
    // Dead code - y is always 6
    z = expensive_call();
}
```

*Hoare Logic Analysis*:
```
After y := x + 1: {y = 6}
Condition: y > 10
{y = 6} ∧ (y > 10) = ⊥ (contradiction)

Therefore branch is unreachable → eliminate safely.
```


#### 3. Undefined Behaviour Detection

Compilers use Hoare-style reasoning to detect *undefined behaviour*:

```c
int divide(int a, int b) {
    return a / b;  // UB if b == 0
}
```

*Verification Condition*:
```
Precondition: b ≠ 0
If cannot prove: emit warning or insert runtime check
```


#### 4. Register Allocation & Live Variable Analysis

*Live variable analysis* determines when variables are "live" (may be read later).

Hoare-style *backward reasoning*:
```
{y is live after} x := expr {x is live if used in expr, y remains live}
```

This enables safe register reuse:
- If variable x is dead after assignment, its register can be reused
- Proven formally via Hoare Logic


#### 5. Verification Condition Generation in Compilers

Many production compilers generate VCs:

*LLVM + KLEE Example*:
```llvm
define i32 @safe_array_access(i32* %arr, i32 %idx) {
  ; VC: 0 ≤ idx < array_length
  %is_safe = icmp ult i32 %idx, %array_len
  br i1 %is_safe, label %safe, label %error

safe:
  %ptr = getelementptr i32, i32* %arr, i32 %idx
  %val = load i32, i32* %ptr
  ret i32 %val

error:
  call void @report_bounds_error()
  unreachable
}
```

The compiler proves via Hoare Logic that `safe` block is only reachable when `idx < array_len`.


#### 6. Compiler-Assisted Proof (Pluggable Types)

Languages like *Rust* use Hoare-style reasoning for:

- *Borrow checker*: Proves at most one mutable reference exists
- *Lifetime tracking*: Proves references don't outlive their referents
- *Type safety*: Proves memory safety without GC

*Example* (Rust Borrow Checker as Hoare Logic):
```rust
let mut x = 5;
let r1 = &x;        // Precondition: x is borrowed immutably
let r2 = &x;        // OK: multiple immutable borrows allowed
// let r3 = &mut x; // ERROR: Cannot borrow as mutable while immutably borrowed

// Hoare triple:
// {x is immutably borrowed} create mutable borrow {⊥} (contradiction!)
```



### Practical Examples

#### Example 1: Array Sum (Complete Verification)

```python
def array_sum(arr, n):
    """
    Precondition: n = len(arr) ∧ n ≥ 0
    Postcondition: result = Σ(arr[0..n-1])
    """
    i = 0
    sum = 0
    
    # Loop invariant: I = (sum = Σ(arr[0..i-1]) ∧ 0 ≤ i ≤ n)
    
    while i < n:
        # {I ∧ i < n}
        sum = sum + arr[i]
        # {sum = Σ(arr[0..i]) ∧ 0 ≤ i < n}
        i = i + 1
        # {I} (invariant restored)
    
    # {I ∧ ¬(i < n)} → {sum = Σ(arr[0..n-1]) ∧ i = n}
    return sum
```

*Verification*:
1. *Initialisation*: `i = 0 ∧ sum = 0` → `sum = Σ([]) ∧ 0 ≤ 0 ≤ n` ✓
2. *Preservation*: Exercise for reader (use induction)
3. *Postcondition*: `i = n ∧ sum = Σ(arr[0..i-1])` → `sum = Σ(arr[0..n-1])` ✓


#### Example 2: Binary Search (Invariant)

```python
def binary_search(arr, target):
    """
    Precondition: arr is sorted ∧ len(arr) = n
    Postcondition: (result ≥ 0 → arr[result] = target) ∧ 
                   (result < 0 → target ∉ arr)
    """
    left = 0
    right = n - 1
    
    # Invariant: I = (target ∈ arr → target ∈ arr[left..right])
    
    while left <= right:
        mid = (left + right) // 2
        
        if arr[mid] == target:
            return mid  # {arr[mid] = target}
        elif arr[mid] < target:
            left = mid + 1  # {target ∈ arr → target ∈ arr[mid+1..right]}
        else:
            right = mid - 1  # {target ∈ arr → target ∈ arr[left..mid-1]}
    
    # {I ∧ left > right} → {target ∉ arr}
    return -1
```


#### Example 3: Procedure with Contract

```c
// Contract:
// Requires: n ≥ 0
// Ensures: result = n! ∧ result > 0
// Modifies: nothing (pure function)

int factorial(int n) {
    if (n == 0) {
        return 1;  // Base case: 0! = 1
    }
    
    // Recursive call - requires n-1 ≥ 0, i.e., n ≥ 1 ✓
    int sub_result = factorial(n - 1);  // {sub_result = (n-1)!}
    
    return n * sub_result;  // {result = n * (n-1)! = n!}
}
```



### Advanced Topics

#### 1. Separation Logic

Extension of Hoare Logic for *heap-manipulating programs*:

```
{emp} x := alloc() {x ↦ _}
{x ↦ v} free(x) {emp}
{x ↦ v} y := *x {x ↦ v ∧ y = v}
```

- `emp`: Empty heap
- `x ↦ v`: Heap cell at x contains v
- `P * Q`: Separating conjunction (P and Q hold on disjoint heap portions)

#### 2. Permission-Based Reasoning

Track *ownership* and *permissions*:

```
{Perm(x, 1.0)} // Full permission (can read and write)
y := x
{Perm(x, 0.5) * Perm(y, 0.5)} // Split permission (both can read)
```

Used in Rust's borrow checker!

#### 3. Rely-Guarantee Logic

For *concurrent programs*:

```
{P, R} S {G, Q}
```

- *P*: Precondition
- *R*: Rely (assumptions about environment)
- *S*: Statement
- *G*: Guarantee (promises about our actions)
- *Q*: Postcondition

#### 4. Automated Invariant Inference

*Abstract interpretation*, *predicate abstraction*, and *machine learning* can infer invariants:

- *Octagon domain*: Relations like `x - y ≤ c`
- *Polyhedra*: General linear constraints
- *AI-based*: Learn from verified code



### Tools and Integration {#tools}

#### SMT Solvers

*Z3*, *CVC4*, *Yices* automatically prove verification conditions:

```python
from z3 import *

x = Int('x')
y = Int('y')

solver = Solver()
solver.add(x == 10)  # Precondition
solver.add(y == x + 1)  # Assignment: y := x + 1

# Check: Does y = 11?
solver.push()
solver.add(Not(y == 11))  # Negate postcondition
result = solver.check()  # If UNSAT, postcondition is proven!

if result == unsat:
    print("Proven: {x = 10} y := x + 1 {y = 11}")
```

#### Verification Tools

1. *Dafny*: Programming language with built-in verification
2. *Why3*: Platform for deductive verification
3. *Frama-C*: Verification for C programs
4. *KLEE*: Symbolic execution for LLVM
5. *VeriFast*: Separation logic verifier for C


### Summary

*Hoare Logic* provides a rigorous foundation for program correctness. In compilers:
1. *Enables safe optimisations* by proving transformations preserve semantics
2. *Detects bugs statically* through verification condition generation
3. *Powers modern type systems* (Rust, TypeScript, Kotlin)
4. *Guides architecture* for safety-critical systems

- Hoare, C. A. R. (1969). An axiomatic basis for computer programming.
  *Communications of the ACM*, 12(10), 576-580.

- Wilhelm, R. & Seidl, H. (2010). *Compiler Design: Virtual Machines*.
  Berlin, Heidelberg: Springer Berlin Heidelberg. [electronic resource]
