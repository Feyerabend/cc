
## Introduction to Presburger Arithmetic

Presburger arithmetic is named after Mojżesz Presburger, a Polish mathematician who introduced this
theory in his 1929 Master's thesis at the University of Warsaw. At just 21 years old, Presburger
proved one of the most fundamental results in mathematical logic: that the first-order theory of
natural numbers with addition is decidable.

This was a remarkable achievement, especially considering it came just two years before Kurt Gödel's
incompleteness theorems would show that many seemingly simpler mathematical theories are undecidable.
Presburger's work demonstrated that while full arithmetic (with both addition and multiplication) is
undecidable, the fragment with only addition maintains decidability.


### Historical Context: Why Presburger's Result Was Astounding

To appreciate what Presburger achieved, you have to stand in 1929. David Hilbert had recently
articulated his famous *Entscheidungsproblem*--the decision problem: could there be a mechanical
procedure that, given any mathematical statement, determines in finite time whether it is true or
false? Hilbert was optimistic. Mathematics, he believed, could be made complete, consistent, and
fully mechanizable.

The Warsaw mathematical community where Presburger worked was exceptional. Jan Łukasiewicz--the
inventor of prefix (Polish) notation--was among his teachers. Stefan Banach, Hugo Steinhaus,
and Alfred Tarski were contemporaries in the broader Polish mathematical world. This was one of the
most fertile mathematical environments in Europe during the interwar years.

Into this climate, a 21-year-old Master's student showed that the first-order theory of addition over
natural numbers is *decidable*. An algorithm exists that, given any formula, will halt and correctly
answer "true" or "false." This was a positive contribution to Hilbert's program: at least one
non-trivial fragment of arithmetic could be mechanized.

But the result carried an implicit warning. Presburger's system worked precisely because it *lacked*
multiplication. Add multiplication back in, and the story changes completely.

Just two years later, in 1931, Kurt Gödel published his incompleteness theorems. Full
arithmetic--Peano arithmetic with both addition *and* multiplication--is not merely undecidable. It is
*incomplete*: there are true statements about the natural numbers that can never be proven from any
finite set of axioms. Hilbert's program was shattered.

The contrast is stark:

| Theory                         | Decidable?               | Complete?        |
|--------------------------------|--------------------------|------------------|
| Presburger arithmetic (+ only) | Yes (Presburger, 1929)   | Yes              |
| Peano arithmetic (+ and ×)     | No (Church/Turing, 1936) | No (Gödel, 1931) |

What makes this so striking is that multiplication, on the surface, seems like a mild extension.
But multiplication is where arithmetic gains the expressive power to talk about its *own* formulas
and proofs--which is precisely what Gödel's diagonalisation argument exploits. Without it,
Presburger arithmetic cannot even express "x is prime" or "y = x²", let alone refer to its own
derivations. This poverty of expression turns out to be its strength: the theory stays decidable
precisely because it cannot reach far enough to trap itself in self-reference.

Presburger's arithmetic therefore occupies a rare *sweet spot* in the logical landscape: expressive
enough to capture meaningful properties of programs (array bounds, loop counters, resource usage,
periodic schedules), yet restricted enough that a decision procedure exists.[^pn]

[^pn]: *A personal note.* Mojżesz Presburger published only this one paper--his Master's thesis. He did
not live to see it become foundational. He was killed in the Holocaust, most likely in 1943 at the
Treblinka extermination camp, at the age of approximately 35. The name "Presburger arithmetic" is
both an honour to a remarkable mathematical insight and a memorial to a life ended far too soon.


### What is Presburger Arithmetic?

Presburger arithmetic is the first-order theory of the natural numbers (0, 1, 2, 3, ...) with:
- *Addition* as the only arithmetic operation
- *Equality* and *ordering* relations
- *Quantification* over natural numbers

#### What's Included:
- Constants: 0, 1, 2, 3, ...
- Variables: x, y, z, ...
- Addition: x + y
- Successor function: S(x) = x + 1
- Equality: x = y
- Ordering: x < y, x ≤ y
- Logical connectives: ¬, ∧, ∨, →, ↔
- Quantifiers: ∀x, ∃x

#### What's *NOT* Included:
- *Multiplication* between variables (x × y)
- *Division* or modular arithmetic
- *Exponentiation*
- *Functions* other than successor and addition

However, multiplication by constants is often allowed: 2x, 3x, etc.,
since this can be expressed using repeated addition.


### Formal Definition

#### Syntax

*Terms (t):*
```
t ::= 0                    (zero constant)
    | x                    (variable)
    | S(t)                 (successor)
    | t₁ + t₂              (addition)
    | c·t                  (multiplication by constant c)
```

*Formulas (φ):*
```
φ ::= t₁ = t₂              (equality)
    | t₁ < t₂              (less than)
    | t₁ ≤ t₂              (less than or equal)
    | ¬φ                   (negation)
    | φ₁ ∧ φ₂              (conjunction)
    | φ₁ ∨ φ₂              (disjunction)
    | φ₁ → φ₂              (implication)
    | φ₁ ↔ φ₂              (biconditional)
    | ∀x.φ                 (universal quantification)
    | ∃x.φ                 (existential quantification)
```

#### Semantics

The standard model of Presburger arithmetic is the structure (ℕ, 0, S, +, =, <) where:
- Domain: Natural numbers ℕ = {0, 1, 2, 3, ...}
- Constants: 0 interpreted as zero
- Functions: S(n) = n + 1, addition as usual
- Relations: Equality and less-than as usual


#### Axioms

A typical axiomatization includes:

*Successor Axioms:*
1. ∀x. S(x) ≠ 0                    (zero is not a successor)
2. ∀x∀y. S(x) = S(y) → x = y       (successor is injective)
3. ∀x. x = 0 ∨ ∃y. S(y) = x        (every number is 0 or a successor)

*Addition Axioms:*
4. ∀x. x + 0 = x                   (additive identity)
5. ∀x∀y. x + S(y) = S(x + y)       (addition with successor)

*Additional Properties:*
6. ∀x. 0 + x = x                   (commutativity base)
7. ∀x∀y. x + y = y + x             (commutativity)
8. ∀x∀y∀z. (x + y) + z = x + (y + z) (associativity)


### Properties


__1. *Decidability*__

The most famous property: there exists an algorithm that can determine, for any
Presburger arithmetic formula, whether it is true or false in the standard model.


__2. *Completeness*__

Every valid statement in Presburger arithmetic can be proven from the axioms using logical rules.


__3. *Consistency*__

The axioms don't lead to contradictions.


__4. *Quantifier Elimination*__

Every Presburger formula is equivalent to a quantifier-free formula. This is crucial for decidability algorithms.


__5. *Model Completeness*__

Any two models of Presburger arithmetic that satisfy the same quantifier-free formulas are elementarily equivalent.


### Examples and Applications


__Basic Examples__

*Simple Equations:*
- `2x + 3y = 7` — Find natural number solutions
- `x + y = 5 ∧ x > y` — Constrained solutions

*Existential Statements:*
- `∃x. 2x + 1 = 7` — "There exists an x such that 2x + 1 = 7" (true, x = 3)
- `∃x. 2x = 7` — "There exists an x such that 2x = 7" (false in naturals)

*Universal Statements:*
- `∀x. x + 0 = x` — "For all x, x + 0 = x" (true)
- `∀x∀y. x + y = y + x` — "Addition is commutative" (true)


__Complex Examples__

*Linear Constraints:*
```
∃x∃y. (3x + 2y = 10 ∧ x ≥ 0 ∧ y ≥ 0)
```
"Can we express 10 as 3x + 2y with non-negative x, y?"

*Periodic Properties:*
```
∀x. ∃y. x = 3y ∨ x = 3y + 1 ∨ x = 3y + 2
```
"Every number has remainder 0, 1, or 2 when divided by 3"

*Ordering Relationships:*
```
∀x∀y∀z. (x < y ∧ y < z) → x < z
```
"Less-than is transitive"


### Decidability and Complexity

__Decision Procedures__

Several algorithms exist for deciding Presburger arithmetic:

1. *Quantifier Elimination*: Convert any formula to an equivalent quantifier-free form
2. *Automata-Based*: Represent solutions as regular languages
3. *Cooper's Algorithm*: Classic elimination procedure (see worked example below)
4. *Omega Test*: Practical algorithm for linear constraints


#### Cooper's Algorithm: A Worked Example

Cooper's algorithm eliminates existential quantifiers one at a time, working from the inside out.
Each step converts `∃x. φ(x)` into a quantifier-free formula by a finite case analysis.

**Example**: Eliminate `x` from `∃x. (2x + y = 6)`.

*Step 1 — Isolate.* Rewrite the equality as `2x = 6 − y`. The coefficient of `x` is 2.

*Step 2 — Divisibility constraint.* For a natural-number `x` to exist, 2 must divide `6 − y`,
i.e., `6 − y ≡ 0 (mod 2)`. Since 6 is even, this requires `y ≡ 0 (mod 2)`.

*Step 3 — Non-negativity.* We need `x = (6 − y)/2 ≥ 0`, so `y ≤ 6`.

*Result:*
```
∃x. (2x + y = 6)   ≡   (2 | y) ∧ y ≤ 6
```

The existential quantifier is gone, replaced by a *divisibility predicate* `(2 | y)` and an
inequality. This is exactly the pattern Cooper's algorithm generates: coefficients greater than 1
always introduce divisibility constraints.

*The general case (inequalities only).* For `∃x. φ(x)` where `φ` is a conjunction of
inequalities, Cooper's algorithm:

1. Collects all *lower bounds* `L₁, ..., Lₘ` and *upper bounds* `U₁, ..., Uₙ` on `x`
2. Computes `δ = lcm` of all divisibility coefficients in `φ` (δ = 1 if there are none)
3. Replaces the quantified formula with the finite disjunction over `j ∈ {1,...,m}` and
   `t ∈ {1,...,δ}` of `φ[x := Lⱼ + t]`

The key insight is that if a solution exists, one can always be found within `δ` steps of a lower
bound. This bounds the search, guaranteeing termination — and is where the double-exponential
worst-case complexity comes from when the algorithm is applied repeatedly to eliminate many variables.


__Complexity__

The decision problem for Presburger arithmetic is:
- *Decidable* but with *very high complexity*
- *Double exponential time* in the worst case
- Space complexity is also double exponential
- In practice, many useful fragments are much more tractable

This high complexity means that while Presburger arithmetic is theoretically decidable,
practical solvers often focus on restricted fragments or use heuristics.


### Semilinear Sets

A result of Ginsburg and Spanier (1966) gives a combinatorial characterisation of exactly which
sets Presburger arithmetic can define.

A *linear set* in ℕᵏ is a set of the form:
```
{ b + n₁·p₁ + n₂·p₂ + ... + nₘ·pₘ  :  n₁, ..., nₘ ∈ ℕ }
```
for a base vector *b* and period vectors *p₁, ..., pₘ* in ℕᵏ.
A *semilinear set* is a finite union of linear sets.

*Theorem (Ginsburg & Spanier)*: A subset of ℕᵏ is definable by a Presburger formula if and
only if it is semilinear.

*Examples in dimension k = 1:*
- Even numbers: `{0 + n·2 : n ∈ ℕ}` — a single linear set (base 0, period 2)
- Numbers with remainder 0 or 2 mod 3: `{0 + n·3} ∪ {2 + n·3}` — union of two linear sets
- The finite set `{0, 1, 4}` — three degenerate linear sets with period vector 0

This characterisation has practical consequences for verification and language theory:

- *Closure properties*: Semilinear sets are closed under union, intersection, and complement —
  corresponding directly to ∨, ∧, and ¬ in the logic
- *Projection*: Projecting a semilinear set (dropping a coordinate) gives a semilinear set —
  corresponding to existential quantification and quantifier elimination
- *Regular languages*: In dimension k = 1, the semilinear subsets of ℕ are exactly the
  *Parikh images* of regular languages (the sets of word lengths of words in the language),
  connecting Presburger arithmetic to automata theory
- *Automata-based decision procedures*: The semilinear characterisation underpins the
  automata-theoretic approach to Presburger arithmetic, where formulas are decided by constructing
  finite automata over binary representations of integers


### Relationship to Other Theories

__Stronger Theories (Undecidable)__
- *Peano Arithmetic*: Adds multiplication (undecidable by Gödel)
- *Robinson Arithmetic*: Minimal arithmetic with multiplication (undecidable)

__Weaker Theories (Decidable)__
- *Successor Arithmetic*: Only successor function, no addition
- *Linear Orders*: Pure ordering relations without arithmetic

__Related Decidable Theories__
- *Real Closed Fields*: Real numbers with addition, multiplication, and ordering
- *Algebraically Closed Fields*: Complex numbers with addition and multiplication
- *Boolean Algebra*: Logical operations on boolean values

__Fragments and Extensions__
- *Existential Presburger*: Only existential quantifiers (NP-complete)
- *Presburger with Division*: Adding divisibility predicates
- *Bounded Quantification*: Restricting quantifier ranges


### Modern Applications

__1. *Program Verification*__
Presburger arithmetic is fundamental in:
- *Loop Invariants*: Proving properties of iterative programs
- *Array Bounds Checking*: Ensuring array accesses are safe
- *Resource Analysis*: Analyzing memory usage and time complexity

Example:
```c
for (i = 0; i < n; i++) {
    a[2*i + 1] = b[i];  // Need to prove 2*i + 1 < array_size
}
```

__2. *Model Checking*__
- *Timed Systems*: Modeling systems with timing constraints
- *Hybrid Systems*: Combining discrete and continuous behavior
- *Parameterized Systems*: Systems with unbounded numbers of processes

__3. *Compiler Optimization*__
- *Loop Optimization*: Determining loop bounds and dependencies
- *Memory Layout*: Optimizing data structure placement
- *Parallelization*: Finding independent computation segments

__4. *Database Query Optimization*__
- *Constraint Databases*: Databases with arithmetic constraints
- *Query Planning*: Optimizing queries with numerical conditions
- *Data Integrity*: Checking consistency of numerical constraints

__5. *Artificial Intelligence*__
- *Planning*: Reasoning about resource constraints
- *Constraint Satisfaction*: Solving problems with linear constraints
- *Knowledge Representation*: Representing numerical relationships


### Implementation Considerations


__Practical Challenges__

1. *High Theoretical Complexity*: Double exponential worst-case
2. *Large Formula Growth*: Quantifier elimination can explode formula size
3. *Numerical Precision*: Handling large constants efficiently
4. *Memory Usage*: Space requirements can be prohibitive


__Implementation Strategies__

1. *Fragment Restrictions*: Focus on practically useful subsets
2. *Heuristics*: Use fast approximate methods when possible
3. *Preprocessing*: Simplify formulas before applying decision procedures
4. *Hybrid Approaches*: Combine multiple algorithms
5. *Incremental Methods*: Build solutions step by step


__Notable Tools and Libraries__

- *Omega Calculator*: Classic implementation from University of Maryland
- *LASH*: Liège Automata-based Symbolic Handler
- *PolyLib*: Polyhedral library with Presburger functionality
- *isl*: Integer Set Library used in compiler optimization
- *Z3*: Microsoft's SMT solver with Presburger support


### C Language Examples

The following examples show Presburger-style reasoning as it arises naturally in C programs,
followed by a C implementation of the core primitives. See `presburger.c` for the full runnable
version.

#### Linear Constraints as Structs

A linear term `c₀x₀ + c₁x₁ + ... + constant` maps directly to a C struct:

```c
#define MAX_VARS 8

typedef struct {
    int coeffs[MAX_VARS];   /* one coefficient per variable slot */
    int constant;
} LinTerm;

typedef enum { REL_EQ, REL_LT, REL_LE } Rel;

typedef struct {
    LinTerm lhs;
    Rel     rel;
    LinTerm rhs;
} LinConstraint;
```

Evaluation under a variable assignment is a straightforward loop:

```c
static int eval_term(const LinTerm *t, const int env[MAX_VARS]) {
    int v = t->constant;
    for (int i = 0; i < MAX_VARS; i++)
        v += t->coeffs[i] * env[i];
    return v;
}
```


#### Array Bounds as a Presburger Query

The compiler optimisation example from earlier becomes a concrete single-line check.
The Presburger query `∀i ∈ [0, n). a·i + b < size` reduces, for positive `a`, to checking
the maximum index at `i = n − 1`:

```c
/* Checks: forall i in [0, n).  a*i + b < size  */
static bool loop_access_safe(int a, int b, int n, int size) {
    if (n <= 0) return true;
    return a * (n - 1) + b < size;
}
```

```c
loop_access_safe(2, 1, 10, 22);   /* max index 19 < 22  ->  SAFE   */
loop_access_safe(2, 1, 10, 19);   /* max index 19 < 19  ->  UNSAFE */
```


#### Cooper Equality Elimination in C

The equality case of Cooper's algorithm reduces to a three-line arithmetic check, then no search needed:

```c
/* Decides  exists x in N. (a*x = c)
 * Satisfiable iff  a divides c  and  c/a >= 0. */
static bool cooper_eq(int a, int c, int *witness) {
    if (a == 0)       return c == 0;
    if (c % a != 0)   return false;   /* divisibility check */
    int x = c / a;
    if (x < 0)        return false;   /* naturals only */
    if (witness) *witness = x;
    return true;
}
```

This correctly handles:
- `cooper_eq(2, 6, &w)` → `true`, `w = 3`  (∃x. 2x = 6)
- `cooper_eq(2, 7, NULL)` → `false`        (∃x. 2x = 7, 7 not divisible by 2)
- `cooper_eq(3, 9, &w)` → `true`, `w = 3`  (∃x. 3x = 9)


#### Bounded Existential Search

When the formula is too complex for analytical elimination, a bounded brute-force search
establishes satisfiability for practical ranges:

```c
#define SEARCH_MAX 1000

static bool exists_bounded(const LinConstraint cs[], int n,
                            int idx, int env[MAX_VARS], int *witness) {
    for (int v = 0; v <= SEARCH_MAX; v++) {
        env[idx] = v;
        if (eval_all(cs, n, env)) {
            if (witness) *witness = v;
            return true;
        }
    }
    return false;
}
```

**Compile and run the full example:**
```bash
cc -std=c99 -o presburger presburger.c
./presburger
```


### Comparison with Full Arithmetic

| Aspect           | Presburger Arithmetic                          | Peano Arithmetic                     |
|------------------|------------------------------------------------|--------------------------------------|
| *Operations*     | Addition only                                  | Addition + Multiplication            |
| *Decidability*   | Decidable                                      | Undecidable                          |
| *Completeness*   | Complete                                       | Incomplete (Gödel)                   |
| *Complexity*     | Double exponential                             | N/A (undecidable)                    |
| *Applications*   | Program verification, optimization             | General mathematics                  |
| *Expressiveness* | Limited but sufficient for many practical uses | Can express all computable functions |


### Limitations and Extensions

#### What You Can't Express

Without multiplication, Presburger arithmetic cannot express:
- *Multiplication relationships*: "x is twice y squared"
- *Prime numbers*: "x is prime"
- *Factorial*: "y = x!"
- *Fibonacci sequences*: Require multiplication-like relationships
- *Most number-theoretic properties*


#### Common Extensions

1. *Divisibility Predicates*: x ≡ 0 (mod n)
2. *Bit-Vector Operations*: For computer arithmetic
3. *Real Number Extensions*: Extending to rational or real numbers
4. *Bounded Domains*: Restricting to finite ranges


### Advanced Topics

#### Quantifier Elimination

The process of converting a formula with quantifiers to an equivalent quantifier-free formula.
For example:
```
∃x. (2x + y = 6) 
```
becomes:
```
y ≡ 0 (mod 2) ∧ y ≤ 6
```

#### Automata-Theoretic Approach

Solutions to Presburger formulas can be represented as regular languages, enabling the use of
finite automata for decision procedures.

#### Geometric Interpretation

Presburger constraints define convex polyhedra in multi-dimensional space, connecting to:
- *Linear Programming*
- *Polytope Theory* 
- *Computational Geometry*


### Using the Code

This folder contains three Python implementations, one C implementation, and a test suite.

| File                 | Purpose                                                                                            |
|----------------------|----------------------------------------------------------------------------------------------------|
| `presburger.py`      | AST for terms and formulas, Presburger axioms, proof system, ground evaluator, interactive session |
| `cooper.py`          | Cooper's quantifier elimination algorithm                                                          |
| `presburger.c`       | Linear constraint checker and Cooper equality case in C                                            |
| `test_presburger.py` | Test suite (50 tests) covering all constructs including `Divisibility` and the evaluator           |

*Python quick-start:*
```bash
python3 presburger.py --demo     # term construction, axioms, evaluation, divisibility
python3 presburger.py            # interactive session (formula builder, proof attempts)
python3 cooper.py --examples     # Cooper's algorithm examples
python3 cooper.py --interactive  # interactive Cooper tester
python3 test_presburger.py       # run all tests
```

**C quick-start:**
```bash
cc -std=c99 -o presburger presburger.c
./presburger
```

**Key classes and functions in `presburger.py`:**

- `Term` subclasses: `Zero`, `Var`, `Succ`, `Add`, `Mult`
- `Formula` subclasses: `Eq`, `Lt`, `Le`, `Divisibility`, `Not`, `And`, `Or`, `Implies`, `Iff`,
  `ForAll`, `Exists`
- `get_free_vars(obj)` — returns the set of free variable names in a term or formula
- `substitute_formula(formula, varname, replacement)` — textual substitution
- `evaluate_term(term, env)` — evaluate a term under a variable assignment `{"x": 3, ...}`
- `evaluate_formula(formula, env)` — evaluate a quantifier-free formula under an assignment
- `PresburgerAxioms` — the eight standard axioms (successor, addition, commutativity, associativity)
- `ProofSystem` — modus ponens, universal instantiation, proof history


### Conclusion

Presburger arithmetic occupies a unique position in mathematical logic and computer science.
Despite its apparent simplicity--just natural numbers with addition--it captures a remarkable
amount of mathematical structure while remaining decidable. This makes it invaluable for
practical applications in program verification, compiler optimisation, and automated reasoning.

The theory demonstrates that sometimes, less is more: by restricting to addition only, we gain
decidability while retaining enough expressiveness for many real-world problems. Understanding
Presburger arithmetic provides insight into the delicate balance between expressiveness and
computability that characterises much of theoretical computer science.

Whether you're working on program analysis, constraint solving, or automated theorem proving,
Presburger arithmetic likely plays a role in the theoretical foundations of your tools and
techniques. Its continued relevance, nearly a century after Presburger's original work,
testifies to the deep importance of this "simple" arithmetic theory.


#### Classic Papers

- Presburger, M. (1929). "Über die Vollständigkeit eines gewissen Systems der Arithmetik"
  *Introduces Presburger arithmetic, the first-order theory over natural numbers with addition
  (no multiplication), and proves it’s decidable, consistent, and complete*

- Cooper, D. C. (1972). "Theorem proving in arithmetic without multiplication"
  *Presents methods for deciding arithmetic statements in systems like Presburger arithmetic,
  emphasizing theorem proving without multiplication*

- Ginsburg, S. & Spanier, E. (1966). "Semigroups, Presburger formulas, and languages"
  *Demonstrates that semilinear sets correspond exactly to languages definable by Presburger
  formulas, and gives a decision procedure for such sets*


#### Modern References

- Bradley, A. R. & Manna, Z. (2007). "The Calculus of Computation"
  *A comprehensive foundation in computational logic and decision procedures, with applications
  to formal methods and program verification*

- Kroening, D. & Strichman, O. (2016). "Decision Procedures"
  *Algorithmic decision procedures for theories widely used in software/hardware verification
  (e.g., linear arithmetic, arrays, SMT frameworks)*

- Habermehl, P. (1997). "On the complexity of the linear-time μ-calculus for Petri nets"
  *Analyzes the model-checking complexity of linear-time μ-calculus properties over Petri nets,
  showing it's decidable but with exponential space in the formula size*
