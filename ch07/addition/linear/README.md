
## Linear Logic

Linear logic was invented by *Jean-Yves Girard* in 1987. Girard was studying the semantics
of proofs in classical and intuitionistic logic when he noticed something peculiar:
traditional logic treats hypotheses as *reusable resources*. If you assume A is true,
you can use that assumption as many times as you want in a proof. But what if we took that away?

This wasn't arbitrary cleverness. Girard was working on *proof theory* and the
*geometry of interaction*, trying to understand what proofs *really are* as
computational objects. He discovered that by controlling how many times you can
use assumptions, you could distinguish between different computational behaviours
that classical logic conflates.


### The Core Insight: Resources, Not Truth

Traditional logic is about *truth*. "A ∧ B" means "A is true AND B is true."
You can use this fact repeatedly--truth doesn't get "used up."

Linear logic is about *resources*. "A ⊗ B" means "I have resource A AND resource B."
Once you consume A in a computation, it's gone.
You can't use it again unless you explicitly make a copy.

This makes linear logic naturally suited for reasoning about:
- *Computational resources* (memory, CPU time)
- *Physical resources* (money, materials)
- *Concurrency and processes* (messages, state transitions)
- *Quantum states* (which can't be cloned or measured repeatedly)


### The Connectives: A Whole New Vocabulary

Linear logic doesn't just have "and" and "or"--it distinguishes
between *resource-sensitive* and *resource-insensitive* versions of each connective.

*Multiplicatives* (resources consumed together):
- *A ⊗ B* ("times"): I have A and B simultaneously
- *A ⅋ B* ("par"): I can provide either A or B when demanded
- *A ⊸ B* ("lollipop", linear implication): Consuming A produces B

*Additives* (making choices):
- *A & B* ("with"): I can provide A or B, you choose which
- *A ⊕ B* ("plus"): I provide A or B, I choose which

*Exponentials* (controlled copying):
- *!A* ("of course"): Infinitely many copies of A
- *?A* ("why not"): I may need A arbitrarily many times

The units:
*1* (multiplicative truth),
*⊥* (multiplicative falsity),
*⊤* (additive truth),
*0* (additive falsity)


### Why These Distinctions Matter

In classical logic, "A and B" just means both are true.
But in linear logic:

- *A ⊗ B*: I have one A and one B to spend
  - Example: $5 ⊗ $3 = I have $8 total
  
- *A & B*: I have access to either A or B, your choice
  - Example: At a restaurant, "soup & salad" means you choose one

- *!A*: I have unlimited copies of A
  - Example: !recipe means the recipe doesn't get consumed when you use it

The *lollipop* A ⊸ B is crucial: it's a *one-shot function*.
If you have "apple ⊸ pie" and you give up an apple, you get a pie.
But you can't use that function again unless you have another apple.

Compare to classical implication: "if it rains, the ground is wet"
can be used over and over. But "if you give me $5, I'll give you coffee"
is linear--I don't give you infinitely many coffees.


### Linear Negation: The Incredible Duality

One of the most beautiful features of linear logic is *perfect duality*.
Every connective has a dual:
- (A ⊗ B)⊥ = A⊥ ⅋ B⊥
- (A & B)⊥ = A⊥ ⊕ B⊥
- (!A)⊥ = ?(A⊥)

This isn't just algebraic beauty--it reflects a deep symmetry between
*production and consumption* of resources. If "A ⊗ B" means providing
both A and B, then its negation "A⊥ ⅋ B⊥" means consuming both A and B.

This duality led Girard to discover that *classical logic is self-dual*:
you can flip your entire perspective (producer <--> consumer) and everything still works.


### Sequent Calculus: How Proofs Work

Linear logic proofs are typically done in *sequent calculus*, where a sequent looks like:

*A₁, A₂, ..., Aₙ ⊢ B₁, B₂, ..., Bₘ*

This means: "Consuming resources A₁, A₂, ... produces resources B₁, B₂, ..."

The key rule that makes it "linear" is that every hypothesis must be used *exactly once*
(unless marked with an exponential).

For example, if you have "A, B ⊢ C", you must use both A and B in your proof.
You can't just use A and ignore B, and you can't use A twice.


### Proof Nets: The Geometry of Proofs

Girard also invented *proof nets*, a graphical way to represent linear logic proofs
that exposes their geometric structure. In proof nets, proofs are literally graphs where:
- Formulas are nodes
- Logical inferences are edges
- Valid proofs satisfy certain topological properties

This was revolutionary--it showed that proofs have intrinsic geometric structure
beyond their syntactic derivation trees.


### Applications and Impact

*1. Computational Interpretation*
Linear logic corresponds beautifully to computation:
- A ⊸ B represents a function from A to B
- A ⊗ B represents a pair
- !A represents persistent data
- The proof system corresponds to a type system for programming languages

*2. Concurrency Theory*
Linear logic naturally models concurrent processes where resources
(messages, channels) are created and consumed. The π-calculus and
session types are deeply connected to linear logic.

*3. Game Semantics*
Linear logic has a beautiful interpretation via games where:
- Two players (System and Environment) exchange moves
- Formulas represent games
- Proofs represent winning strategies

*4. Quantum Computing*
Linear logic's "no cloning" property (you can't copy an arbitrary formula)
mirrors quantum mechanics' no-cloning theorem.
There are quantum interpretations of linear logic.

*5. Natural Language Semantics*
Linguists use linear logic to model how words combine in sentences,
since words are "consumed" as you parse (unlike truth values).


### Philosophy

Linear logic challenges our intuitions about logic itself.
It shows that classical logic's notion of truth is just one
possibility--we've been implicitly assuming resources are free and unlimited.

Girard described this as revealing the *"bureaucracy" of logic*--all
the bookkeeping classical logic was doing invisibly. Linear logic makes
it explicit: who owns what resource? When is it produced? When is it consumed?

It also connects logic to *physics and thermodynamics*.
Using a resource costs something. Information isn't free.
This makes linear logic perhaps more "realistic" than classical logic
for modeling actual physical and computational systems.


### The Learning Curve

Linear logic is famously difficult to learn initially because:
1. You must unlearn classical intuitions about "and" and "or"
2. The proliferation of connectives seems overwhelming
3. The accounting discipline (use everything exactly once) is strict

But once it clicks, it provides incredibly precise control over resource
usage and a beautiful unified framework for thinking about computation, concurrency, and proof.



### Example

The program runs on a Raspberry Pi Pico 2 with a 320x240 display and shows two things at once.
The top half has two vendor boxes: VendorA selling Apples and VendorB selling Bananas. Tha
automatically step through a protocol every two seconds: receive a coin, deliver an item, complete.
A cross symbol sits between them representing the tensor product (⊗), meaning both vendors must
complete for the whole session to succeed. When they do, "DONE"appears between the boxes.

The bottom half visualises the proof that justifies this protocol: a tree of circles and lines
representing the formula (A⊗B) (B⊗A) commutativity of tensor. The root node "-o" (lollipop)
branches into two "x" (tensor) nodes, each with two atom leaves A and B. Red dashed lines connect
the matching atoms across the tree: left-A to right-A and left-B to right-B. These are the axiom
links that make the proof valid, showing that the two sides are just the same resources in a different order.


![Tensor Nets](./../../assets/image/tensor.png)

