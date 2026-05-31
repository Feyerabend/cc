
## CTL Model Checking: Logic, Semantics, and Verification

This document covers Computation Tree Logic (CTL) from its philosophical and mathematical roots
through to the implementation in `ctlmodel.py`. The parent directory's
[`README.md`](../README.md) situates model checking within the broader tradition of model theory
stretching from Tarski to Kripke; this document takes up the story from the point where modal
logic meets computer systems and works inward toward the specific algorithms and examples.



### I. Time and Logic

Classical propositional and first-order logic are *atemporal*. A sentence is true or false in a
structure, full stop. There is no room for "it was true", "it will be true", "it is necessarily
true", "it could have been otherwise." This is appropriate for mathematics--the Pythagorean theorem
does not become true on Tuesdays--but it is inadequate for reasoning about processes, programs,
protocols, or anything that changes over time.

The philosophical problem of tense had been noticed long before formal logic made it precise.
Aristotle's sea-battle argument (*De Interpretatione*, ch. 9) wrestles with whether a statement
about a future contingent event is presently true or false. If "there will be a sea-battle tomorrow"
is already determinately true, it seems to follow that the outcome is predetermined--a conclusion
Aristotle found troubling. The argument turns on whether truth is timeless or indexed to a moment.

The formal answer, developed in the twentieth century, is to *index* truth to a point of evaluation.
Just as Kripke semantics for modal logic indexes truth to a possible world, temporal logic indexes
truth to a moment in time--a *time point* within a *temporal structure*. The operators of temporal
logic then quantify over time points accessible from the current one, in much the way that □ and ◇
quantify over possible worlds accessible via the accessibility relation.

**Arthur Prior** (New Zealand/Oxford) is the founder of modern formal temporal logic. His 1957
book *Time and Modality* and the 1967 *Past, Present and Future* introduced the operators:
- **P** (*it was the case that*) — true at t if the operand holds at some earlier time.
- **F** (*it will be the case that*) — true at t if the operand holds at some later time.
- **H** (*it has always been the case that*) — true at t if the operand holds at all earlier times.
- **G** (*it will always be the case that*) — true at t if the operand holds at all later times.

Prior's motivation was partly philosophical (analyzing tense in natural language and debating
fatalism) and partly theological (the problem of divine foreknowledge and free will). He did not
anticipate that the same formal apparatus would become a standard tool of computer-aided
verification twenty years later. The shift happened when researchers in computer science recognized
that *execution traces* of a program have the same structure as a *temporal model*: a sequence (or
tree) of states, where each state is a time point and the transitions are the temporal steps.



### II. Linear vs. Branching Time: The Fundamental Debate

When temporal logic was imported into computer science in the late 1970s and early 1980s, a
foundational question immediately arose: what is the structure of time in a computational model?

**Linear time** treats the future as a single sequence. At each moment there is one successor.
Non-determinism in a program is resolved by choosing a particular execution path; a temporal
formula is then evaluated along that single path. This gives *Linear Temporal Logic (LTL)*,
developed by Amir Pnueli (1977, Turing Award 2000), who was the first to propose temporal logic
as a framework for specifying and verifying concurrent programs.

**Branching time** treats the future as a *tree*: at each moment, multiple possible successors
may exist, representing the different choices an environment or scheduler could make. A temporal
formula is then evaluated over the entire tree of possibilities, and path quantifiers (∀ paths,
∃ path) become first-class operators. This gives *Computation Tree Logic (CTL)*, developed by
Edmund Clarke and E. Allen Emerson (1981–1982), and the more expressive CTL* by Emerson and
Judy Halpert (1986), which subsumes both LTL and CTL.

The debate between these two views was not merely technical. It concerned what kind of object a
*specification* is and what kind of claim a *property* makes:

- **LTL advocates** argued that a system's behaviour is ultimately characterised by the set of
  execution traces it can produce, and that properties should be properties of individual traces.
  A system is correct if every trace satisfies the specification. On this view, branching
  structure is implementation detail, not specification content.

- **CTL advocates** argued that branching structure is essential. Properties like "the system
  *can always* recover from a fault" (EG-reachability) or "from every state, *all paths*
  eventually reach a safe state" (AG-AF) cannot be expressed in LTL because they quantify
  simultaneously over multiple paths from the same state in a way that linear-time semantics
  cannot capture.

The technical result is that LTL and CTL are *incomparable in expressiveness*: each can express
properties the other cannot. LTL can express the fairness property "infinitely often P" (GF P)
in a form that cannot be mimicked in CTL. CTL can express "there exists an infinite P-path" (EG P)
in a form that has no LTL equivalent. CTL* is strictly more expressive than both. In practice, the
choice is often made on efficiency grounds: CTL model checking is polynomial in both the model
size and the formula size (O(|S| · |φ|)), while LTL model checking requires constructing a product
automaton and is PSPACE-complete in the formula size.



### III. Kripke Structures as Branching-Time Models

The semantic foundation of CTL is the **Kripke structure**, inherited directly from Kripke's
1963 semantics for modal logic (see the parent README for the broader history). In the
computational setting, a Kripke structure is a tuple:

> *M = <S, S₀, R, L>*

where:
- **S** is a finite set of *states*, each representing a snapshot of the system's memory.
- **S₀ ⊆ S** is the set of *initial states*.
- **R ⊆ S × S** is a *total transition relation*: every state has at least one successor.
  (Totality is required so that computation paths are infinite; terminal states are given
  self-loops.)
- **L : S → 2^AP** is a *labeling function* that maps each state to the atomic propositions
  true in that state.

This is a model in the full Tarskian sense: a mathematical structure that interprets a formal
language. The language is CTL; the interpretation is the labeling L. The totality condition on R
ensures that the *computation tree* rooted at any initial state is infinite, which is necessary
for the semantics of globally-quantified formulas like AG and EG to be well-defined.

Conceptually, think of states as rows in a truth table for the system's variables, transitions as
arrows between rows, and the labeling as which propositions are checked-off in each row. The
Kripke structure is then the "meaning" of the system--exactly what Tarski meant by a *model*.



### IV. CTL: Syntax and Semantics

CTL formulas are built from atomic propositions using boolean connectives and a set of *compound
temporal operators*, each consisting of a *path quantifier* paired with a *state operator*.

*Path quantifiers:*
- **A** (*for All paths*): the property must hold on every path from the current state.
- **E** (*there Exists a path*): the property holds on at least one path from the current state.

*State operators:*
- **X** (*neXt*): the property holds in the immediately next state.
- **F** (*Future / eventually*): the property holds at some future state on the path.
- **G** (*Globally / always*): the property holds at every future state on the path.
- **U** (*Until*): the left property holds continuously until the right property becomes true.

In CTL, path quantifiers and state operators must appear in strict pairs: AX, EX, AF, EF, AG, EG,
A[φ U ψ], E[φ U ψ]. This is the syntactic restriction that distinguishes CTL from CTL*, which
allows path quantifiers to scope over arbitrarily nested formulas.

**Semantics.** CTL formulas are evaluated at states in a Kripke structure. Write M, s ⊨ φ to mean
"formula φ holds at state s in structure M." The evaluation rules:

| Formula         | Holds at s iff ...                                  |
|-----------------|-----------------------------------------------------|
| M, s ⊨ p        | p ∈ L(s)                                            |
| M, s ⊨ ¬φ       | not M, s ⊨ φ                                        |
| M, s ⊨ φ ∧ ψ    | M, s ⊨ φ and M, s ⊨ ψ                               |
| M, s ⊨ EX φ     | some successor t of s satisfies φ                   |
| M, s ⊨ AX φ     | every successor t of s satisfies φ                  |
| M, s ⊨ EF φ     | some state on some path from s satisfies φ          |
| M, s ⊨ AF φ     | every path from s reaches a φ-state                 |
| M, s ⊨ EG φ     | some infinite path from s satisfies φ at every step |
| M, s ⊨ AG φ     | every path from s satisfies φ at every step         |
| M, s ⊨ E[φ U ψ] | some path from s has φ holding until ψ is reached   |
| M, s ⊨ A[φ U ψ] | every path from s has φ holding until ψ is reached  |

A full set of expressible properties:

```
AG(safe)                  — invariant: safe holds in every reachable state
EF(goal)                  — reachability: goal is achievable
AG(EF(recover))           — every state can always reach recovery
AG(request → AF(respond)) — every request is eventually responded to
AG(EX true)               — every state has at least one successor (totality)
EG(¬halt)                 — there exists an infinite non-terminating path
```



### V. Fixpoint Semantics and Computability

The power of model checking over finite Kripke structures comes from the *fixpoint
characterisation* of the temporal operators. Every CTL operator can be computed as the limit of an
iterative sequence over the (finite) powerset of states. This is a consequence of the
**Knaster–Tarski fixpoint theorem**: on a complete lattice, every monotone function has a least
fixpoint (lfp) and a greatest fixpoint (gfp), both reachable by iteration.

The state powerset (2^S, ⊆) is a complete lattice. The semantic operators--Pre∃ (existential
predecessor) and Pre∀ (universal predecessor)--are monotone on this lattice. So every temporal
operator has a fixpoint characterisation:

**Least fixpoints** (computed upward from ∅):

```
[[EF φ]]  = lfp Z. [[φ]] ∪ Pre∃(Z)
          — start from φ-states, add any state that can reach Z in one step
          — iterate until stable: this is backward reachability from [[φ]]

[[E[φ U ψ]]]  = lfp Z. [[ψ]] ∪ ([[φ]] ∩ Pre∃(Z))
[[A[φ U ψ]]]  = lfp Z. [[ψ]] ∪ ([[φ]] ∩ Pre∀(Z))
[[AF φ]]  = lfp Z. [[φ]] ∪ Pre∀(Z)   (= A[true U φ])
```

**Greatest fixpoints** (computed downward from S):

```
[[EG φ]]  = gfp Z. [[φ]] ∩ Pre∃(Z)
          — start from φ-states, remove any state with no successor in Z
          — iterate until stable: this is the largest set of φ-states
            from which an infinite φ-path exists

[[AG φ]]  = ¬[[EF ¬φ]]   (derived)
```

For a finite structure with n states, the least fixpoint is reached in at most n iterations (each
iteration adds at least one state or stops). The greatest fixpoint is reached in at most n
iterations (each removes at least one or stops). Hence every CTL formula is computable in
O(|S| · |φ|) time--polynomial.

This fixpoint view connects CTL model checking to the **modal μ-calculus** (Kozen 1983), the most
expressive modal fixpoint logic, in which lfp (μ) and gfp (ν) are explicit binding operators.
Every CTL formula is equivalent to a μ-calculus formula, and the model-checking algorithm for CTL
is essentially the restriction of the μ-calculus algorithm to the operators expressible in CTL.



### VI. Predecessor Computation

Two predecessor operations appear throughout the fixpoint evaluations:

**Pre∃(Z)** — *existential predecessor*: the set of states that have at least one successor in Z.

```
Pre∃(Z) = { s ∈ S | ∃t ∈ Z. (s, t) ∈ R }
```

Used in EX, EU, EG, EF. Intuitively: "which states can *reach* Z in one step along some path?"

**Pre∀(Z)** — *universal predecessor*: the set of states whose *all* successors are in Z.

```
Pre∀(Z) = { s ∈ S | ∀t. (s, t) ∈ R → t ∈ Z }
```

Used in AX, AU, AF. Intuitively: "which states are *forced into* Z in one step along every path?"

The duality of these operators reflects the duality between existential and universal path
quantifiers. Pre∀(Z) = S \ Pre∃(S \ Z): a state is a universal predecessor of Z iff it is not an
existential predecessor of the complement of Z.



### VII. Safety and Liveness

The properties typically verified by model checking fall into two broad categories, a distinction
originating in the work of Lamport (1977) and given a topological characterisation by Alpern and
Schneider (1985):

*Safety properties* say that *something bad never happens*. Formally, a safety property defines
a set of "bad" traces, and the system must produce no trace in that set. In CTL, safety properties
typically take the form AG(¬bad) or AG(p → q). They are *invariants*--they must hold at every
reachable state. If a safety property is violated, there is a *finite* counterexample: the shortest
path to the bad state.

Examples:
- `AG(¬(doors_open ∧ moving))` — the elevator never opens its doors while moving.
- `AG(pc_valid)` — the program counter never goes out of bounds.
- `AG(¬(mutex_a ∧ mutex_b))` — mutual exclusion: the two processes are never both in the
  critical section.

*Liveness properties* say that *something good eventually happens*. They cannot be violated by
any finite prefix of an execution--every finite trace is consistent with the property holding,
because the good thing might still happen later. In CTL, liveness properties typically involve
AF or AG(... → AF ...). If a liveness property is violated, the counterexample is an *infinite*
path (or a cycle) that avoids the good thing forever.

Examples:
- `AF(halted)` — every execution eventually terminates.
- `AG(request_pending → AF(doors_open))` — every request is eventually served.
- `AG(EF(floor3))` — floor 3 is always eventually reachable.

The distinction matters for verification strategy. Safety violations are found by reachability
analysis (has the bad state been visited?). Liveness violations require detecting *trapping
cycles*--strongly connected components of non-halting, non-serving, or otherwise "stuck"
states from which the good event is unreachable.



### VIII. The Python Implementation: `ctlmodel.py`

`ctlmodel.py` implements a complete explicit-state CTL model checker in four layers.

#### Layer 1: Kripke Structure (`KripkeStructure`)

Stores states as strings (easy to read and debug), transitions as a dictionary of sets, and labels
as a dictionary of sets. Key methods:
- `add_state(s, props)` — adds state s and labels it with the given propositions.
- `add_transition(s, t)` — adds the directed edge s → t, checking that both states exist.
- `ensure_total_relation()` — adds self-loops to any state with no outgoing transitions,
  satisfying the totality requirement of CTL semantics.
- `validate()` — checks totality and that all transition endpoints are declared states.
- `get_predecessors(Z)` — Pre∃(Z): states with at least one successor in Z.
- `get_universal_predecessors(Z)` — Pre∀(Z): states whose every successor is in Z.
- `get_strongly_connected_components()` — Tarjan's algorithm, used for structural analysis.

#### Layer 2: CTL Formula AST

Formulas are represented as trees of Python objects:

```
Atom('p')                      — atomic proposition p
Not(φ)                         — ¬φ
And(φ, ψ), Or(φ, ψ)            — φ ∧ ψ, φ ∨ ψ
Implies(φ, ψ)                  — φ → ψ
EX(φ), AX(φ)                   — EX φ, AX φ
EF(φ), AF(φ)                   — EF φ, AF φ
EG(φ), AG(φ)                   — EG φ, AG φ
EU(φ, ψ), AU(φ, ψ)             — E[φ U ψ], A[φ U ψ]
```

All classes share the `CTLFormula` base class; binary operators inherit from `BinaryFormula`,
unary from `UnaryFormula`. Each class implements `validate()` (checking that atomic propositions
exist in the model) and `__str__()` (for display and cache keys).

#### Layer 3: Model Checker (`CTLModelChecker`)

`check_formula(formula)` is the entry point. It:
1. Validates the formula against the model's atomic propositions.
2. Calls `_evaluate_formula()` which looks up the cache or delegates to `_eval_formula_impl()`.
3. Returns a `ModelCheckingResult` dataclass with satisfying states, time, iterations, and
   formula size.

`_eval_formula_impl()` dispatches by formula type. Each case is a direct implementation of the
fixpoint equations from Section V:

```python
# EF φ = lfp Z. [[φ]] ∪ Pre∃(Z)
Z = phi_states
while True:
    new_Z = phi_states | kripke.get_predecessors(Z)
    if new_Z == Z: break
    Z = new_Z

# EG φ = gfp Z. [[φ]] ∩ Pre∃(Z)
Z = phi_states
while True:
    new_Z = phi_states & kripke.get_predecessors(Z)
    if new_Z == Z: break
    Z = new_Z

# E[φ U ψ] = lfp Z. [[ψ]] ∪ ([[φ]] ∩ Pre∃(Z))
Z = psi_states
while True:
    new_Z = psi_states | (phi_states & kripke.get_predecessors(Z))
    if new_Z == Z: break
    Z = new_Z
```

`AX`, `AG`, `AF`, `AU` are implemented via their duals or direct least-fixpoint computations.
Caching (`self.cache`) stores results keyed by `str(formula)`, so shared subformulas (e.g., the
inner formula of a repeated `AG(...)`) are evaluated only once per `check_formula()` call.



### IX. Example 1: Traffic Light

The traffic light model is the simplest non-trivial Kripke structure: four states in a cycle,
each labeled with the propositions true in that state.

```
States and labels:

  red       : {red}
  red_amber : {red, amber}
  green     : {green, safe_to_go}
  amber     : {amber}

Transition relation (deterministic cycle):

  red → red_amber → green → amber → red → ...
```

This is a Kripke structure with a single strongly connected component — every state is reachable
from every other, and the computation tree is an infinite unwinding of the same four-state cycle.

*Properties verified:*

1. `AG(EF(green))` — from every state, green is eventually reachable.
   *Result: HOLDS.* Since the transition relation is a cycle through all four states, every
   state reaches green after at most three steps.

2. `AG(green → AX(amber))` — green is always immediately followed by amber.
   *Result: HOLDS.* The only transition from green leads to amber; AX checks all successors.

3. `AG(red → A[red U green])` — from red, the system stays in red (or passes through red_amber)
   until green is reached; it cannot skip to amber directly.
   *Result: HOLDS.* The only path from red goes red → red_amber → green; there is no path
   from red that reaches amber before green.

4. `AG(safe_to_go → green)` — `safe_to_go` is only labeled in the green state.
   *Result: HOLDS.* A label consistency check; confirms the labeling function is correct.

5. `AG(red → AF(green))` — from red, green is inevitably reached on every path.
   *Result: HOLDS.* Since the model is a deterministic cycle, every path from red reaches
   green within two steps. This is a liveness property.

6. `EG(¬green)` — there exists an infinite path that never visits green.
   *Result: FAILS* (empty set of satisfying states). This is correct: since the only cycle
   passes through green, no infinite path can permanently avoid it. The failure of EG(¬green)
   is the complement of the liveness result: green is not just eventually reachable on some
   path, but unavoidable on every path.

The traffic light illustrates the interplay between safety (property 2: the next state after green
is always amber, no other transition exists) and liveness (property 5: green is always eventually
reached), and shows how the `Until` operator (property 3) can capture ordering constraints that
neither pure safety nor pure liveness expresses on its own.



### X. Example 2: Three-Floor Elevator

The elevator model is a Kripke structure with 17 states and 25 transitions. States encode four
dimensions of the system simultaneously:

```
State name format: <floor>_<direction>_<doors>_<request>

  floor     : 1, 2, 3
  direction : u (moving up), d (moving down), i (idle)
  doors     : o (open), c (closed)
  request   : r (request pending), n (no request)

Example: 2_u_c_r = floor 2, moving up, doors closed, request pending
```

Each dimension corresponds to a set of atomic propositions: `floor1/floor2/floor3`,
`moving_up/moving_down/idle`, `doors_open/doors_closed`, `request_pending/no_request`.

The transition relation models realistic elevator behavior:
- A request can arrive at any idle state (`*_i_c_n → *_i_c_r`).
- An idle elevator with a request serves it by opening its doors (`*_i_c_r → *_i_o_n`).
- An idle elevator can also start moving (`*_i_c_* → *_{u,d}_c_*`).
- A moving elevator arrives at the next floor and becomes idle.
- Doors close after opening.

__Properties verified:__

*Safety — both hold:*

1. `AG((moving_up ∨ moving_down) → doors_closed)` — doors are always closed while moving.
   *Result: HOLDS.* No state in the model has both a direction flag and `doors_open`; the
   labeling function and transitions enforce this invariant.

2. `AG(¬(floor1 ∧ (floor2 ∨ floor3)))` — the elevator cannot be on two floors at once.
   *Result: HOLDS.* Each state is labeled with exactly one floor proposition.

*Liveness — both fail (model gap):*

3. `AG(request_pending → AF(doors_open))` — every request is eventually served.
   *Result: FAILS.* The model is non-deterministic: from a state like `2_i_c_r` (floor 2,
   idle, request pending) the elevator can either serve the request (→ `2_i_o_n`) or start
   moving without serving it (→ `2_u_c_r` or `2_d_c_r`). This creates cycles in which the
   request is perpetually pending and doors never open. AF(doors\_open) requires that *every*
   path from a request-pending state eventually opens the doors, but the cycle via the moving
   states is a counterexample.

   This failure reveals a genuine model deficiency: the specification does not enforce that an
   idle elevator at a floor with a pending request *must* serve it before moving on. In a real
   elevator controller this would be enforced by the control logic; here the model omits that
   constraint. Fixing it would require removing the transitions from `*_i_c_r` to `*_{u,d}_c_r`
   (an idle elevator with a pending request at its current floor cannot choose to leave).

6. `AG((moving ∧ request_pending) → AF(doors_open))` — even while moving, a pending request
   is eventually served. *Result: FAILS* for the same reason as property 3.

__Other properties — both hold:__

4. `AG(EF(floor2)) ∧ AG(EF(floor1)) ∧ AG(EF(floor3))` — every floor is reachable from
   every state. *Result: HOLDS.* The single strongly connected component of the model
   confirms this: any state can reach any other.

5. `AG(floor1 → EF(floor3))` — from any floor 1 state, floor 3 is eventually reachable.
   *Result: HOLDS.* This is a stronger form of reachability than property 4 for one specific
   floor pair; it holds because the elevator can always travel upward.

   (The earlier formula `EF(floor3 ∧ EX(floor1))` was incorrect — it asked whether there is
   a state at floor 3 with a direct one-step transition back to floor 1, which no three-floor
   elevator would have.)

*Structural analysis:*

The strongly connected component (SCC) analysis reports a single SCC containing all 17 states.
This means the model is strongly connected: every state is reachable from every other. This is
consistent with the liveness properties that hold (property 4), but it also means the liveness
properties that fail are genuine failures — the counterexample cycles are real, not artifacts of
unreachable parts of the model.



### XI. What the Failures Teach

The liveness failures in the elevator model are not bugs in the model checker; they are correct
results. The checker has found that the *specification* (the Kripke structure) does not enforce
fair request scheduling, even though we described it as a model of an elevator. This is the
intended use of model checking: to discover gaps between the model and the intended behaviour
*before* building the real system.

In industrial practice, such a result would prompt one of three responses:

1. *Refine the model* to add the missing constraint (remove the non-deterministic choice that
   allows the elevator to leave without serving the request).
2. *Add a fairness assumption*: assert that the system is fair--if a transition is infinitely
   often enabled, it is infinitely often taken. Under a strong fairness assumption, the liveness
   properties can hold even in the non-deterministic model. LTL is better suited to expressing
   fairness assumptions than plain CTL.
3. *Accept the gap*: acknowledge that the model abstracts away the scheduling policy, and verify
   only the properties that hold under *all* schedulers (which are precisely the ones that hold
   here).

The traffic light example holds all its properties because it is a deterministic model: each state
has exactly one successor, so every path is the same path and non-determinism plays no role. Moving
from a deterministic to a non-deterministic model is where the branching structure of CTL becomes
essential--and where model checking earns its keep.



### XII. Running the Code

```bash
# From the ctl/ directory:
python3 ctlmodel.py
```

Output: traffic light analysis first (six properties), then elevator analysis (six properties,
SCC decomposition). All computations complete in milliseconds for these model sizes.

To use the checker interactively or extend it:

```python
from ctlmodel import KripkeStructure, CTLModelChecker
from ctlmodel import Atom, Not, And, Or, Implies, AG, EF, AF, EG, AX, EX, AU, EU

# Build a minimal two-state model
m = KripkeStructure("ping-pong")
m.add_state('A', ['ping'])
m.add_state('B', ['pong'])
m.add_transition('A', 'B')
m.add_transition('B', 'A')
m.ensure_total_relation()

checker = CTLModelChecker(m)

# Does every state infinitely often return to ping?
result = checker.check_formula(AG(EF(Atom('ping'))))
print(result.satisfying_states)   # {'A', 'B'} — holds everywhere

# Is there an infinite path that stays pong forever?
result = checker.check_formula(EG(Atom('pong')))
print(result.satisfying_states)   # set() — fails: pong always leads back to ping
```
