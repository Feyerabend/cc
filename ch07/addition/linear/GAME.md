
*When I began my studies at the university, I briefly had to choose between
computer science in a particular Swedish form, *systemvetenskap* (roughly
"information systems"), and theoretical philosophy. The division between
practical and theoretical philosophy has been somewhat distinctive in the
Nordic countries. Theoretical philosophy traditionally includes areas such
as logic and epistemology, and its origins may in part be traced back to
the Aristotelian separation of philosophical disciplines.*

*In the end I chose theoretical philosophy, and my professor was Stig Kanger.
I refer to him elsewhere in this repository. He read a preliminary paper,
pre-doctoral thesis, of mine on Occam, Frege, and the notion of assertion,
and he seemed to like it. He suggested that I should go and study to a
close friend of his, Jaakko Hintikka, perhaps because he saw that direction
as closer to my interests than to his own work.*

*At the time I was rather shy and lacked the confidence to follow his
suggestion, although he would certainly have helped me arrange the
opportunity to study with Hintikka. Instead, my interests gradually
shifted toward historical themes. I began reading more in the history
of ideas, the history of science, antiquity, and related subjects.
I never really got back to the ideas I had at the time ..*


## From Game Semantics to Interaction: Hintikka's Legacy in Modern Logic

The connection between Hintikka's work and present-day interaction-based
logics can be understood historically as a gradual shift in how logic
explains meaning. Earlier twentieth-century logic, especially the tradition
following Alfred Tarski, treated meaning in a purely model-theoretic way.
A formula was interpreted relative to a structure, and truth meant that
the formula evaluated to true in that structure under an assignment of
variables. Logical semantics therefore consisted of defining truth conditions.
This perspective dominated formal logic for decades.


### Hintikka's Game-Theoretic Semantics

In the 1960s, Jaakko Hintikka introduced a different way of understanding
semantics. Instead of defining truth as a static relation between formulas
and models, he described the evaluation of formulas as a game between two
players, traditionally called the Verifier (∃loise) and the Falsifier (∀belard). 

Consider the formula ∀x∃y R(x,y). In Hintikka's game:
1. The Falsifier chooses an element a from the domain
2. The Verifier then chooses an element b from the domain
3. The game reduces to evaluating the atomic formula R(a,b)
4. The Verifier wins if R(a,b) holds; otherwise the Falsifier wins

When a formula contains a universal quantifier, the Falsifier chooses the element;
when it contains an existential quantifier, the Verifier chooses.
For logical connectives, the rules are:
- φ ∧ ψ: Falsifier chooses which subformula to evaluate
- φ ∨ ψ: Verifier chooses which subformula to evaluate
- ¬φ: Players swap roles

If the Verifier has a strategy that guarantees victory no matter how the
opponent moves, the formula is considered true in the model. The crucial
conceptual step here is that truth becomes equivalent to the existence of
a winning strategy. Logical meaning is therefore explained through interaction
rather than static evaluation.

Although this reformulation was initially presented as an alternative semantics
for classical logic, it introduced a powerful conceptual shift. The meaning
of a logical expression could now be understood as the set of strategies that
succeed in a structured interaction. In other words, semantics becomes inherently
dynamic. The evaluation of a formula unfolds as a process, and logical structure
determines the rules of that process. This viewpoint influenced several later
developments even when the technical details of Hintikka's original games
were not preserved exactly.


### Game Semantics for Programming Languages

One of the most important directions in which this idea developed was in theoretical
computer science during the 1980s and 1990s. Researchers such as Samson Abramsky,
Martin Hyland, and Luke Ong constructed what is now known as game semantics for
programming languages. In that framework, a type is interpreted as a game between
a program (Player) and its environment (Opponent), and a program itself is interpreted
as a strategy describing how the program responds to environmental inputs.

For example, the function type A → B is interpreted as a game where:
- Opponent provides a value of type A (representing function application)
- Player must respond with a value of type B (representing the function result)

More complex types involve interleaved moves. For the type (A → B) → C:
- Opponent provides a function f : A → B
- Player may query f by providing values of type A
- Opponent responds with values of type B
- Player eventually produces a value of type C

A program of this type is then a strategy specifying Player's responses for all
possible Opponent moves. Computation becomes a play of the game. This approach
solved several long-standing problems in denotational semantics by producing
fully abstract models for languages such as PCF (Programming Computable Functions).
The conceptual similarity to Hintikka's semantics is clear: the meaning of an
expression is given by a strategy in a game governed by logical rules. The difference
is that the game is no longer about verifying the truth of a sentence but about
describing the behaviour of a computation interacting with its context.


### Linear Logic and Ludics

At roughly the same time another line of development emerged from proof theory,
particularly from the work of Jean-Yves Girard. Girard's introduction of Linear
Logic in 1987 emphasised the dynamic aspects of proofs and resource usage. 
inear Logic distinguishes between:
- Multiplicative connectives (A ⊗ B, A ⅋ B) representing parallel composition
- Additive connectives (A & B, A ⊕ B) representing choice
- Exponentials (!A, ?A) allowing controlled reuse of resources

The sequent A ⊢ B is interpreted not just as "B is derivable from A" but as
"A can be consumed to produce B". From this perspective, the process of cut
elimination in proofs resembles an interaction between two proof structures,
where one proof's output matches another proof's input, and the cut elimination
process executes their interaction.

Girard later extended these ideas in the framework called Ludics (introduced
around 2001). In Ludics the starting point is not formulas but interactive
objects called designs. A design is essentially a tree-like structure representing
possible interaction behaviours. When two designs interact, their interaction
either converges (terminates successfully) or diverges. A fundamental relation
called orthogonality (⊥) identifies pairs of designs whose interaction terminates
successfully. Logical structure is reconstructed from these interaction patterns:
a formula becomes a set of designs closed under certain properties.

Although Ludics developed from proof-theoretic motivations rather than directly
from Hintikka's model theory, it shares the same fundamental shift: meaning arises
from interaction processes rather than static truth assignments.


### Independence-Friendly Logic

Another extension of Hintikka's ideas also played a role in this transition.
His work on Independence-Friendly Logic (IF logic), developed with Gabriel Sandu
in 1989, introduced imperfect information into semantic games. In these games
some choices must be made without knowledge of earlier moves.

For example, the formula ∀x∃y/\{x\} R(x,y) means "for all x, there exists y chosen
independently of x such that R(x,y)". The notation /\{x\} indicates that the
Verifier's choice of y cannot depend on the Falsifier's earlier choice of x.
This leads to a richer class of logical phenomena. The formula ∀x∃y/\{x\} (x = y)
is always false (since y cannot track x), while ∀x∃y (x = y) is trivially true.

IF logic has greater expressive power than first-order logic and can express
statements equivalent to existential second-order logic. This notion of restricted
information flow later became significant in areas such as dependence logic
(introduced by Jouko Väänänen in 2007) and the semantics of information
flow in computation.


### The Interactive Turn

These developments together illustrate a broader transformation in modern logic.
Earlier semantics treated meaning as a relation between syntax and structures.
Interaction-based approaches treat meaning as behavior in a structured exchange:
- In Hintikka's semantics the exchange is a verification game for a logical sentence
- In game semantics for programming languages the exchange is between a program and its environment  
- In Ludics the exchange is between proof-like objects whose interaction determines logical compatibility

The underlying conceptual thread is that logical entities can be understood
through the strategies governing their interactions.

The present landscape of logic therefore includes several traditions that can
all be seen as descendants of Hintikka's interactive viewpoint. Game semantics
models programs as strategies. Ludics models proofs as interactive behaviours.
Dependence and independence logics analyse informational constraints through
imperfect-information games. While these frameworks differ in their formal details
and goals, they share the idea that logical meaning is best understood through
the dynamics of interaction rather than through static truth conditions alone.
Hintikka's introduction of semantic games did not merely provide another way
to define truth; it opened a path toward understanding logic itself as a theory
of structured interaction.


### References

Abramsky, S., & McCusker, G. (1999). Game semantics. In H. Schwichtenberg & U. Berger (Eds.), *Computational Logic* (pp. 1-55). Springer.

Girard, J.-Y. (1987). Linear logic. *Theoretical Computer Science*, 50(1), 1-102.

Girard, J.-Y. (2001). Locus solum: From the rules of logic to the logic of rules. *Mathematical Structures in Computer Science*, 11(3), 301-506.

Hintikka, J. (1973). *Logic, Language-Games and Information: Kantian Themes in the Philosophy of Logic*. Clarendon Press.

Hintikka, J., & Sandu, G. (1989). Informational independence as a semantical phenomenon. In J. E. Fenstad et al. (Eds.), *Logic, Methodology and Philosophy of Science VIII* (pp. 571-589). North-Holland.

Hyland, J. M. E., & Ong, C.-H. L. (2000). On full abstraction for PCF: I, II, and III. *Information and Computation*, 163(2), 285-408.

Tarski, A. (1944). The semantic conception of truth and the foundations of semantics. *Philosophy and Phenomenological Research*, 4(3), 341-376.

Väänänen, J. (2007). *Dependence Logic: A New Approach to Independence Friendly Logic*. Cambridge University Press.
