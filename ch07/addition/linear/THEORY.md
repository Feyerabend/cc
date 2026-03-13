
## Linear Logic: Theory


### The Problem with Classical Logic

Classical logic has *structural rules* that create problems for computational interpretation:

#### Weakening
```
   Γ ⊢ Δ
─────────
Γ, A ⊢ Δ
```
"If you can prove Δ from Γ, you can still prove it even if I give you extra assumption A."

*Problem*: In computation, this means unused variables are OK. But in reality,
if I give you a file handle and you don't close it, that's a *resource leak*.

#### Contraction
```
Γ, A, A ⊢ Δ
────────────
  Γ, A ⊢ Δ
```
"Two copies of assumption A can be replaced by one."

*Problem*: In computation, this means variables can be used multiple times.
But what if A is a *unique resource* like a lock or a network packet? You can't duplicate it!

#### The Fix: LINEAR LOGIC

Linear logic *removes weakening and contraction* by default,
making them explicit through the exponential modalities `!` and `?`.

This creates a logic where:
- Resources must be used (no waste)
- Resources can't be copied arbitrarily (no magic duplication)
- Computation is explicit (no hidden bookkeeping)

### Sequent Calculus

Linear logic is presented in *sequent calculus*, where sequents have the form:

```
A₁, A₂, ..., Aₙ ⊢ B₁, B₂, ..., Bₘ
```

Read as: "Consuming resources A₁, ..., Aₙ produces resources B₁, ..., Bₘ"

#### Key Rules

*Identity:*
```
─────
A ⊢ A
```
"Resource A can become resource A (obviously)"

*Cut:*
```
Γ ⊢ A, Δ      Σ, A ⊢ Π
────────────────────────
     Γ, Σ ⊢ Δ, Π
```
"If Γ produces A and A can be consumed to get Π, eliminate the intermediate A"

*Tensor (⊗) rules:*
```
Γ ⊢ A     Δ ⊢ B
──────────────── ⊗R
  Γ, Δ ⊢ A ⊗ B

 Γ, A, B ⊢ Δ
────────────── ⊗L
Γ, A ⊗ B ⊢ Δ
```

*Par (⅋) rules:*
```
Γ ⊢ A, B, Δ
────────────── ⅋R
Γ ⊢ A ⅋ B, Δ

Σ, A ⊢ Π    Ω, B ⊢ Λ
───────────────────── ⅋L
  Σ, Ω, A ⅋ B ⊢ Π, Λ
```

*Bang (!) rules:*
```
!Γ ⊢ A
─────── !R
!Γ ⊢ !A

Γ, A ⊢ Δ
───────── !L (dereliction)
Γ, !A ⊢ Δ

Γ ⊢ Δ
──────── !W (weakening)
Γ, !A ⊢ Δ

Γ, !A, !A ⊢ Δ
────────────── !C (contraction)
  Γ, !A ⊢ Δ
```

The exponentials restore classical behavior *on demand*.

### The Linear Logic Connectives

#### Multiplicatives (Resources consumed together)

*Tensor (⊗)*: "I have both A and B"
- Both resources exist simultaneously
- Both must be consumed together
- `A ⊗ B` can be decomposed into A and B
- Unit: 1 (the empty tensor, "nothing needed")

*Par (⅋)*: "I will provide either A or B (or both) when demanded"
- Dual of tensor
- You choose which to take
- `A ⅋ B` must be consumed as A and B
- Unit: ⊥ (the empty par, "I can provide nothing")

*Why are they different from AND/OR?*

In classical logic, `A ∧ B` means "A is true AND B is true".
The "and" is about *truth values*.

In linear logic, `A ⊗ B` means "I have resource A AND resource B".
The "and" is about *simultaneous availability*.

Similarly, `A ⅋ B` is NOT classical OR. It's "You can demand both
A and B from me (though I may only provide one or the other)".

#### Additives (Making choices)

*With (&)*: "I can provide A or B, you choose"
- Environment picks which one
- The unchosen branch is discarded
- `A & B` means system must be prepared for either request
- Unit: ⊤ (top, "I can provide anything you don't want")

*Plus (⊕)*: "I will provide A or B, I choose"
- System picks which one
- The unchosen branch disappears
- `A ⊕ B` means system commits to one path
- Unit: 0 (zero, "I provide nothing", uninhabited)

*Example:*
```
Menu: (Soup & Salad)
```
Restaurant can provide either, customer chooses.

```
Desert: (Cake ⊕ Pie)
```
Restaurant decides what to serve today.

#### Implication

*Lollipop (⊸)*: "Give me A, I'll give you B"
- One-shot function
- Consumes the argument
- `A ⊸ B ≡ A⊥ ⅋ B`
- Not reusable unless wrapped in !

Compare to classical implication:
```
Classical: A → B
  "If A is true, B is true"
  Can be used infinitely many times
  
Linear: A ⊸ B
  "Consuming A produces B"
  Can be used exactly once
```

#### Exponentials (Controlled copying)

*Bang (!)*: "Unlimited copies of A"
- Persistent resource
- Can be copied (contraction)
- Can be discarded (weakening)
- `!A ⊸ B ⊸ C` is a normal function (can use A many times)

*Why Not (?)*: "May need A multiple times"
- Dual of !
- On the consumer side
- `!(A ⊸ B) ≡ !A ⊸ !B` (functions can be used many times if input is unlimited)

#### Negation

Linear negation is *involutive* and *complete*:

```
(A ⊗ B)⊥ = A⊥ ⅋ B⊥
(A ⅋ B)⊥ = A⊥ ⊗ B⊥
(A & B)⊥ = A⊥ ⊕ B⊥
(A ⊕ B)⊥ = A⊥ & B⊥
   (!A)⊥ = ?(A⊥)
   (?A)⊥ = !(A⊥)
   (A⊥)⊥ = A
```

This perfect duality is the *De Morgan laws on steroids*.



### Proof Nets

Proof nets are *graphs* representing proofs, exposing their geometric structure.

#### Why Proof Nets?

Sequent calculus proofs have *bureaucracy*: the same logical content
can have different derivation trees based on rule application order.

Proof nets *quotient out* this bureaucracy, giving a *canonical representation*.

#### Structure

A proof net is a graph where:
- *Vertices* are formula occurrences
- *Edges* represent logical connectives
- *Links* connect formulas according to typing rules

#### Correctness Criterion

Not every graph is a valid proof net!

*Danos-Regnier criterion*: A graph is a proof net if:
1. Every switching (choosing one premise from each & node)
2. Yields a tree
3. When you contract all &/⊕ nodes

This is a *polynomial-time* check, while finding proofs in sequent calculus is exponential!

#### Example: (A ⊗ B) ⊸ (B ⊗ A)

```
    A────┐
         ⊗────┐
    B────┘    │
              ⊸────(result)
    B────┐    │
         ⊗────┘
    A────┘
```

The proof net shows the *wiring*: A from the left goes to the right,
B from the left goes to the right, but they swap positions.

#### Cut Elimination in Proof Nets

Cuts in proof nets are *graph rewrites*:

*Tensor/Par cut:*
```
Before:
  ⊗─────Cut─────⅋
  
After:
  (two new cuts connecting components)
```

*Plus/With cut:*
```
Before:
  ⊕─────Cut─────&
  
After:
  (one cut on chosen branch, other branch deleted)
```

This is *graph rewriting*, and it's the computational content!


### Game Semantics

Game semantics interprets formulas as *two-player games*.

#### Players

- *Proponent (P, System, ∀)*: Tries to prove the formula
- *Opponent (O, Environment, ∃)*: Tries to refute it

#### Games

A game has:
- *Positions*: States of play
- *Moves*: P-moves and O-moves
- *Rules*: Who can move when

#### Strategy

A *strategy* for P is a function:
```
O-move sequence → P-move
```

A *winning strategy* is one where P always wins if they follow it.

*A proof is a winning strategy.*

#### Connectives as Game Operations

*A ⊗ B*:
- P must defend both A and B simultaneously
- O can attack either (or both)
- P wins if they win both subgames

*A ⅋ B*:
- O must attack at least one
- P can respond in either (or both)
- P wins if they win any subgame

*A & B*:
- O chooses which game to play
- P must be ready for either
- P wins if they win the chosen game

*A ⊕ B*:
- P chooses which game to play
- O must accept P's choice
- P wins if they win their chosen game

*A ⊸ B*:
- O plays A (provides input)
- Then P must play B (provide output)
- P wins if they can respond to any O-move with a B-move

*!A*:
- O can request A multiple times
- P must provide it every time
- Persistent resource

#### Example: Vendning Machine

Formula: `!Coin ⊸ (Snack ⊕ Refund)`

Game:
1. O provides unlimited coins (!Coin)
2. For each coin, P must choose Snack or Refund (⊕)
3. P wins if they always respond appropriately

This is exactly a vending machine protocol!

### Session Types

Session types are *behavioral types* for communication channels,
based on linear logic.

#### Basic Session Types

```
   !T   "Send a message of type T (can send many)"
   ?T   "Receive a message of type T (can receive many)"
T ⊗ S   "Session T and session S in parallel"
T ⊕ S   "Offer choice between T and S (internal choice)"
T & S   "Accept choice between T and S (external choice)"
end     "Session closes"
```

#### Example: ATM Protocol

```
ATM = !Pin . (
  (CorrectPin ⊕ IncorrectPin)
)

CorrectPin = ?(Amount . (!Cash . end))
             &
             !Balance . end

IncorrectPin = end
```

Reading:
1. Send PIN
2. System chooses: correct or incorrect
3. If correct: 
   - External choice: withdraw or check balance
   - Withdraw: receive amount, send cash
   - Balance: send balance
4. If incorrect: end

#### Duality

Session types have *duality*: if one endpoint has type S, the other has type S⊥.

```
   (!T)⊥ = ?T⊥
   (?T)⊥ = !T⊥
(S ⊗ T)⊥ = S⊥ ⅋ T⊥
(S ⊕ T)⊥ = S⊥ & T⊥
```

This ensures *protocol compatibility*: the two ends fit together perfectly.

#### Type Safety

If both ends follow their session types, the system *cannot deadlock*!

This is guaranteed by linear logic:
- No message is sent without a receiver
- No receive happens without a sender
- Resources are balanced

### Categorical Semantics {#categorical-semantics}

Linear logic has a beautiful categorical semantics in *∗-autonomous categories*.

#### Basic Structure

A ∗-autonomous category has:
- Monoidal structure `(⊗, 1)` for tensor
- Dual monoidal `(⅋, ⊥)` for par
- Linear negation `(−)⊥` satisfying `A⊥⊥ = A`
- Natural isomorphism `A ⊗ B → (A⊥ ⅋ B⊥)⊥`

#### Exponentials

The exponentials are modeled by a *comonad* `!` and dual monad `?`:
```
!: C → C  is a comonad with:
   ε: !A → A      (counit, dereliction)
   δ: !A → !!A    (comultiplication, contraction)

? is the dual monad
```

#### Models

Important models include:
- *Coherence spaces*: Sets with coherence relation
- *Phase semantics*: Subsets of a monoid
- *Geometry of interaction*: Operators on a Hilbert space
- *Ludics*: Game semantics construction

#### Why Category Theory?

Category theory shows that linear logic is *canonical*:
- It's the *free ∗-autonomous category* on a set of atoms
- Proof nets are *morphisms* in this category
- Cut elimination is *composition* of morphisms

### Conclusion

Linear logic is profound because it:
1. *Refines classical logic*: Makes resource usage explicit
2. *Has computational content*: Proofs are programs
3. *Has geometric structure*: Proof nets are graphs
4. *Has game semantics*: Proofs are strategies
5. *Types communication*: Session types prevent errors
6. *Has categorical semantics*: Everything is compositional
