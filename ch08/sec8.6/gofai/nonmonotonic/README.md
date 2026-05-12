
## Non-Monotonic Reasoning

In 1988 I bought: Ginsberg, M. L. (Ed.). (1987). *Readings in nonmonotonic reasoning*.
Morgan Kaufmann.

*Non-monotonic reasoning* (NMR) was a major topic of interest in artificial intelligence
(AI) in the 1980s. Monotonic reasoning is what classical logic does: adding new premises
never reduces the set of conclusions. In contrast, non-monotonic reasoning allows that
adding new knowledge can invalidate previous conclusions.

Example:
- Premise: "Birds can fly" --> conclude Tweety can fly.
- New information: "Tweety is a penguin" --> retract previous conclusion.

This models human-like reasoning better than classical logic, especially in the presence
of defaults, exceptions, and incomplete knowledge. However it deviates from classical
logic in a way that might rub your skin in the wrong way.

In the late '80s, NMR seemed like a promising direction for AI. At the same time,
*Situation Theory/Semantics* began to gain attention (Jon Barwise & John Perry,
*Situations and Attitudes*, 1983). It emphasised understanding human action and
intention within specific social and practical contexts, rather than relying on abstract
logical formalisms alone. It proposed that reasoning is embedded in situations--structured
by goals, roles, and constraints--and cannot be reduced to rules or formal inference.
As I still was occasionally connected to the Philosophical Institution, we had some
discussions and seminars on this, for us, fresh topic.

This shift also challenged the AI community to think beyond symbolic manipulation.
It suggested that intelligence isn't just about rules or facts, but also about navigating
changing situations, often with incomplete or conflicting information. It was a turn
toward contextual, dynamic reasoning--something NMR had opened the door to, but situational
approaches made explicit.

Both lines of thought pushed AI toward more flexible, realistic models of reasoning.


### Core Formalisms

The 1980s produced several distinct formal systems, each capturing a different intuition
about defaults and exceptions. They share the goal of reasoning under incomplete
information but differ in how they represent and compute extensions of belief.

a. *Default Logic* (Reiter, 1980) introduces *default rules* of the form:

```
  P : M Q
  --------
     R
```

Read: if P is provable and it is *consistent to assume* Q (meaning ¬Q is not derivable),
then derive R. A *normal* default collapses justification and consequence: the common
case is `Bird(x) : M Flies(x) / Flies(x)`. The collection of beliefs closed under
applicable defaults is called an *extension*. A knowledge base may have zero, one, or
several extensions--each a maximally consistent way of applying the available defaults.

b. *Circumscription* (McCarthy, 1980) takes a different approach. Rather than explicit
default rules, it says: *minimise the extension of the abnormality predicate*. Given a
formula φ(P), circumscription asserts that the predicate P is as small as possible while
still satisfying φ. In practice, this means: assume things are *normal* unless forced
otherwise. An elegant variational formulation--but second-order in nature, which made
automated reasoning significantly harder than plain first-order logic.

c. *Autoepistemic Logic* (Moore, 1985) concerns an ideal agent reasoning about its *own
beliefs*. The key modal operator L reads "I believe that." The agent can derive things
like "I don't believe Tweety is a penguin, therefore I'll assume it can fly."
Non-monotonicity arises because the agent's introspective conclusions change when new
information alters what it does or does not believe.

d. *Truth Maintenance Systems* (TMS) (Doyle, 1979) are more procedural than the above.
A TMS maintains a *dependency network* over beliefs, recording which beliefs justify
which others. When a belief is retracted, the TMS traces the dependency graph and
retracts downstream beliefs too. This is the computational side of NMR--belief revision
enacted in data structures and propagation algorithms rather than in proof theory.
Descendant variants, such as the *Assumption-Based TMS* (ATMS), track multiple
consistent contexts simultaneously.


### Closed World vs. Open World Assumption

Underlying much of NMR is a foundational modelling choice: is the world *closed* or *open*?

Under the *Closed World Assumption* (CWA), if something cannot be proved true, it is
assumed false. Relational databases use this: if a flight is not in the database, the
system concludes it does not exist. Prolog's *negation as failure* (`\+ P` succeeds
when P cannot be proved) is the prototypical CWA mechanism--and it is non-monotonic,
because adding a new clause for P can make `\+ P` fail where it previously succeeded.

Under the *Open World Assumption* (OWA), absence of proof is not proof of absence.
OWL ontologies and description logics use OWA: if the ontology doesn't say Tweety is
a non-penguin, that doesn't mean Tweety *is* a penguin--it simply means the system
doesn't know. This is the appropriate stance when the knowledge base is genuinely
incomplete, as most real-world knowledge bases are.

The choice between CWA and OWA is not a matter of correctness but of modelling intent.
It has deep consequences: CWA enables negative inferences that OWA forbids, making
systems under CWA stronger but more committal. NMR largely operates under something
close to CWA--an agent acts on what it knows, and treats unknowns as falsehoods unless
there is reason to believe otherwise.


### Epistemological and Philosophical Context

Non-monotonic reasoning did not emerge from a vacuum. It sits at the intersection of
several philosophical traditions that had long grappled with the problem of defeasible
knowledge--beliefs that are justified, but only provisionally.

a. *Defeasible reasoning in epistemology.* John Pollock developed the most careful
epistemological theory of defeasible reasoning, partly in dialogue with the AI
literature.[^pollock] Pollock distinguished two kinds of defeaters for an inference
from evidence E to conclusion C. A *rebutting defeater* is evidence directly supporting
¬C -- in the Tweety case, knowing Tweety is a penguin directly blocks the flight
inference. An *undercutting defeater* undermines the inferential link itself without
supporting ¬C -- evidence that the lighting conditions made the object look red defeats
the inference from "looks red" to "is red," not by establishing that the object is not
red, but by destroying the warrant for the inference. Default logic has no clean
counterpart to this distinction. Pollock's framework belongs to the epistemological
tradition of reliabilism: asking not just what conclusions follow from given premises,
but under what conditions a belief-forming process is reliably truth-conducive.

[^pollock]: Pollock, J. L. (1987). Defeasible reasoning. *Cognitive Science*, 11(4), 481-518.
His *Cognitive Carpentry* (1995) extends this into a full theory of rational cognition.

b. *The lottery and preface paradoxes.* Henry Kyburg's *lottery paradox* (1961) shows
that rational belief under uncertainty does not satisfy classical conjunction. If a
lottery has 1,000 tickets and exactly one will win, I am individually justified in
believing each ticket will lose (probability 0.999). But by conjunction I should
believe *all* tickets will lose--which contradicts my knowledge that one ticket wins.
The *preface paradox* (Makinson, 1965) is structurally similar: an author is
individually justified in asserting each statement in a book, yet rational enough to
write in the preface "this book probably contains errors." Both paradoxes expose a
tension between local and global consistency that classical logic cannot accommodate.
Non-monotonic reasoning is one proposed resolution: allow that beliefs individually
warranted can be retracted when their aggregate becomes problematic. But the resolution
is incomplete--neither default logic nor circumscription directly addresses graded
confidence, and the paradoxes resurface whenever defaults interact.

c. *Bayesian updating vs. belief revision.* There are two main formal frameworks for
changing beliefs under new evidence, and they embody different philosophical
commitments. *Bayesian updating* maintains a probability distribution over possible
worlds and revises by conditioning: P(H | E) = P(E | H) · P(H) / P(E). This is
monotonic in one sense--no world is ever absolutely excluded, it merely receives lower
probability--and handles graded uncertainty naturally. It is provably optimal under
standard decision-theoretic assumptions, and it requires a prior.
*Belief revision* (the AGM theory, Alchourrón, Gärdenfors, Makinson, 1985) works with
a set of beliefs rather than a probability distribution and allows beliefs to be
outright retracted. NMR is closer in spirit to belief revision: it operates at the
level of what is believed or not, without numerical probabilities. The debate between
these frameworks is not merely technical. It reflects a deeper question about whether
rational belief is fundamentally *graded* or fundamentally *binary*--whether
uncertainty is a matter of degree or of epistemic status. Bayesians often argue their
framework subsumes belief revision (retracting a belief = assigning it probability zero
in the updated distribution). Belief revisionists reply that Bayesian updating
presupposes a rich prior that is rarely available, and that the phenomenon of genuine
revision--where what was previously certain becomes uncertain--does not reduce to
conditioning.

d. *Lakatos and the non-monotonicity of science.* Imre Lakatos's philosophy of science
(*The Methodology of Scientific Research Programmes*, 1978) offers an illuminating
parallel. Scientific theories have a *hard core* of fundamental commitments protected
by a *protective belt* of auxiliary hypotheses. When anomalies arise, scientists revise
the auxiliary belt rather than abandon the core. The same observation that should, by
modus tollens, falsify the core theory is absorbed by revising a peripheral assumption
instead. This is structurally non-monotonic: adding a new observation does not always
add a new conclusion; sometimes it retracts an old one. Lakatos's framework shows that
NMR is not a quirk of AI but a feature of scientific reasoning at the level of research
programmes. The hard core functions like a maximally preferred default; auxiliary
hypotheses are lower-priority ones, subject to revision first.

e. *Popper and falsificationism.* Karl Popper's picture of science--bold conjecture
followed by attempted refutation (*The Logic of Scientific Discovery*, 1935)--is also
non-monotonic: a falsifying instance "retracts" a hypothesis. But Popper's view is
starker than Lakatos's, and NMR theorists found it insufficient: a falsified theory is
discarded wholesale, not revised. Popper describes the endpoint of a reasoning
episode; NMR addresses the internal revision step that Popper largely skipped over.

f. *Defeasibility in legal reasoning.* H.L.A. Hart introduced the term *defeasible*
into formal philosophical discourse (*The Ascription of Responsibilities and Rights*,
1949) in the context of legal concepts: a legal obligation holds unless defeated by
specific conditions -- duress, incapacity, fraud. Legal rules have always been
understood as provisional in this sense: "promise → obligation, unless duress, unless
incapacity, unless fraud ..." The law is a natural domain for NMR, and formal
approaches to legal reasoning--Dung's argumentation frameworks, among others--drew
heavily on NMR concepts. Interestingly, Hart reached the notion of defeasibility
before the AI theorists formalised it, and from a very different direction: not from
the failure of classical logic in AI, but from careful analysis of how legal language
actually works.

g. *Dreyfus's challenge.* Hubert Dreyfus (*What Computers Can't Do*, 1972;
*Being-in-the-World*, 1991) mounted a sustained philosophical critique of GOFAI from
a phenomenological perspective. Drawing on Heidegger and Merleau-Ponty, Dreyfus
argued that human expertise is not rule-following but *skilled coping*--embodied,
contextual, and not decomposable into explicit representations. The frame problem, for
Dreyfus, was not a technical limitation awaiting a better formalism; it was a symptom
of a fundamental misunderstanding of what intelligence is. NMR still operates entirely
within the representationalist paradigm: it tries to encode more defaults, handle more
exceptions, represent more context. Dreyfus would say the problem is not how to
represent defaults better, but that representation is the wrong level of analysis.
Whether or not one accepts this, the challenge is serious: NMR presupposes that
common-sense knowledge *can* be made fully explicit, which is precisely what Dreyfus
denied--and which no NMR system has yet achieved.

h. *Wittgenstein and the rule-following problem.* The rule-following considerations
in Wittgenstein's *Philosophical Investigations* (§201) point in a related direction:
"there is a way of grasping a rule which is not an interpretation." A rule cannot
determine its own application; at some point we simply act, without further explicit
interpretation. NMR, by multiplying defaults and exception-handling rules, may face a
regress that cannot be closed within the formalism. Every default needs to be stated
against a background of practices that the default itself cannot make explicit. This
does not refute NMR as an engineering approach, but it suggests there is a ceiling: no
matter how many defaults are encoded, the system will always be reasoning against a
background of tacit, unencoded understanding. The gap between what can be made explicit
and what must simply be understood is, arguably, where both NMR and GOFAI as a whole
reach their structural limits.


### Why Was It Hot in the 1980s?

Thus in the late '70s and '80s, AI researchers realised that classical logic could not capture
how humans deal with uncertainty, defaults, and change. This led to a surge of interest in:
- Default logic (Reiter, 1980)
- Circumscription (McCarthy)
- Autoepistemic logic (Moore)
- Truth maintenance systems (TMS) (Doyle)
- Non-monotonic modal logics

These formalisms aimed to provide a rigorous foundation for reasoning systems that could:
- Make assumptions by default
- Retract assumptions when contradictory information arises
- Update beliefs in light of new evidence

What happened after the 1980s is not that non-monotonic reasoning disappeared, but that
it evolved and fragmented into several interconnected research directions. Its formal
tools--like the above default logic, circumscription, and autoepistemic logic--were
foundational but often proved difficult to scale or implement efficiently. Instead, more
practical and computationally grounded frameworks emerged, particularly in logic programming
and belief revision. One such outcome is *Answer Set Programming* (ASP), which took shape
in the 1990s and matured into a powerful declarative programming paradigm. ASP retains
the core ideas of non-monotonic reasoning and is widely used today in areas like planning,
diagnosis, and combinatorial search. Meanwhile, the ideas of defeasibility and belief
updating spread into fields like knowledge representation, agent systems, and legal reasoning.
Even now, as AI trends shift toward neural methods, non-monotonic reasoning continues to
inform explainability research and hybrid symbolic-neural models, making its legacy a
persistent undercurrent in the broader AI landscape.


### A Worked Example in Detail

The Tweety example is canonical but easy to underestimate. A careful trace shows where
the non-monotonicity actually occurs and why it matters.

*Setup.* Knowledge base:

```
Bird(Tweety)
Bird(x) : M Flies(x) / Flies(x)      -- normal default: birds fly
```

*Step 1.* The default fires: Bird(Tweety) is known; ¬Flies(Tweety) is not derivable;
so Flies(Tweety) enters the extension. The unique extension is
E₁ = {Bird(Tweety), Flies(Tweety)}.

*Step 2.* Add: Penguin(Tweety) and the hard rule Penguin(x) → ¬Flies(x).

Now ¬Flies(Tweety) is derivable via the hard rule. The default's justification
M Flies(Tweety) is violated: it is no longer *consistent* to assume Flies(Tweety),
because its negation is now provable. The default does not fire. The extension
becomes E₂ = {Bird(Tweety), Penguin(Tweety), ¬Flies(Tweety)}.

Adding Penguin(Tweety) *removed* Flies(Tweety) from the extension. That is the
non-monotonic step. It is perfectly correct behaviour and matches commonsense reasoning;
the unsettling part is that it violates the structural guarantee classical logic offers.

*The multiple extensions problem.* Consider a more symmetric case--the "Nixon diamond":

```
Quaker(Nixon)
Republican(Nixon)
Quaker(x)     : M Pacifist(x)    / Pacifist(x)
Republican(x) : M ¬Pacifist(x)  / ¬Pacifist(x)
```

Nixon is a Quaker (by default, pacifist) and a Republican (by default, non-pacifist).
Two defaults compete, neither overriding the other. Default logic yields *two* equally
valid extensions: one where Nixon is a pacifist and one where he is not. The theory
identifies the ambiguity correctly but provides no principled basis for choosing.
In practice, priority orderings must be supplied externally--which returns the burden
to the knowledge engineer.

This is not an exotic edge case. Priority conflicts arise naturally in legal reasoning,
medical diagnosis, and planning, wherever general rules have exceptions that themselves
have exceptions.


### Code Illustration

The file `nonmonotonic.py` in this directory implements a small defeasible reasoner
following Reiter's default logic. The key structure:

```python
class Reasoner:
    def assert_fact(self, *facts):   ...  # direct knowledge
    def add_rule(self, cond, concl): ...  # hard rule: cond -> concl
    def add_default(self, prereq, justif, conseq): ...
    def extension(self) -> frozenset: ... # computed beliefs
    def query(self, fact) -> bool:   ...
```

A *normal default* uses the same literal for `justif` and `conseq`. The default fires
if `prereq` is believed and `neg(justif)` is not. Negation is represented by the
`not_` prefix convention: `neg("flies_tweety") == "not_flies_tweety"`.

The Tweety example in code:

```python
r = Reasoner()
r.add_default("bird_tweety", "flies_tweety", "flies_tweety")
r.add_rule("penguin_tweety", "not_flies_tweety")

r.assert_fact("bird_tweety")
print(r.query("flies_tweety"))     # True  -- default fires

r.assert_fact("penguin_tweety")
print(r.query("flies_tweety"))     # False -- default blocked
```

The same example in *Answer Set Programming* (ASP), using the Clingo solver, is
even more direct. ASP has non-monotonic negation built into the language:

```prolog
bird(tweety).
penguin(tweety).

flies(X) :- bird(X), not ab(X).
ab(X)    :- penguin(X).

#show flies/1.
```

Running `clingo tweety.lp` yields no model containing `flies(tweety)`. Remove the
`penguin` fact and it appears. The `not ab(X)` is *negation as failure*: ab(X) is
assumed false unless it can be derived. This is the core of non-monotonic logic
programming--and it is the descendant of the 1980s formal work, made practical.

The Nixon diamond reveals the limits of the greedy extension computation:

```python
# Quaker default listed first -> pacifist wins
r1.add_default("quaker_nixon", "pacifist_nixon",     "pacifist_nixon")
r1.add_default("republican_nixon", "not_pacifist_nixon", "not_pacifist_nixon")
# Republican default listed first -> non-pacifist wins
r2.add_default("republican_nixon", "not_pacifist_nixon", "not_pacifist_nixon")
r2.add_default("quaker_nixon", "pacifist_nixon",     "pacifist_nixon")
```

The two reasoners produce opposite conclusions from identical facts. Neither is wrong.
Both represent valid extensions. The implementation makes the order-dependence
explicit--a feature, not a bug: it exposes what the theory leaves unresolved.


### Critique

Non-monotonic reasoning was intellectually exciting and theoretically deep. But it faced
persistent difficulties in practice that are worth examining honestly.

a. *Computational hardness.* Query answering under most NMR formalisms is
Σ₂^P-complete--one level above NP in the polynomial hierarchy. This means deciding
whether a proposition belongs to *some* extension (credulous reasoning) or *all*
extensions (sceptical reasoning) can require searching an exponential space. This is
not merely a theoretical concern: it constrained the practical size of knowledge bases
and drove a cottage industry of research into tractable special cases.

b. *The multiple extensions problem.* As the Nixon diamond shows, a knowledge base can
admit multiple equally valid extensions with no principled basis for preferring one.
Default logic and circumscription identify the problem formally but do not resolve it.
Practical systems had to add priority orderings or preference criteria that came from
outside the formalism--and were often as hard to get right as the original defaults.

c. *Knowledge acquisition.* Like expert systems generally, NMR required someone to encode
the defaults by hand. Getting them right--knowing which exceptions override which
defaults, in which order, for which domains--turned out to be as laborious and
error-prone as encoding the rules in a traditional expert system. The knowledge
acquisition bottleneck did not disappear; it shifted into a more subtle form.

d. *Probabilistic alternatives.* Many of the situations NMR was designed to handle--
uncertain defaults, conflicting evidence, degrees of belief--are handled more naturally
by probabilistic methods. Bayesian networks assign numerical degrees of belief and
update them coherently as evidence arrives, provably optimally under standard assumptions.
They give calibrated uncertainty rather than binary conclusions. By the 1990s, a
substantial portion of the AI community had concluded that probability was the more
appropriate tool for *uncertain* reasoning, leaving NMR at its strongest in domains
where reasoning is genuinely discrete and all-or-nothing.

e. *The frame problem.* One original motivation for NMR was the frame problem: in a
changing world, how do you know what *stays the same* when an action occurs? Default
logic and circumscription offered formal treatments, but practical planning systems
still struggled with it at scale. The problem turned out to be bound up with the
representation and volume of world knowledge, not just the inference mechanism. NMR
reframed it but did not dissolve it.

f. *Neural methods end-run.* Modern machine learning handles many of the tasks that
motivated NMR--language understanding, common-sense reasoning, exception handling--
by learning statistical regularities over large data rather than encoding explicit
defaults. The results are often impressive, though the reasoning is opaque and the
failures are different in character. Whether this counts as solving the problems NMR
addressed, or merely sidestepping them, remains a live and serious question.


### Connections to Other Concepts

a. Logic Programming
- Negation as failure in Prolog is a form of non-monotonic reasoning.
- Led to Answer Set Programming (ASP)--development rooted in stable
  model semantics (Gelfond & Lifschitz).

b. Belief Revision
- The AGM theory (Alchourrón, Gärdenfors, Makinson) formalised how
  agents should revise beliefs.[^agm]
- Closely related to NMR in managing belief updates.

[^agm]: The central insight behind AGM theory is that real-world reasoning isn't static: agents often need to give up beliefs, modify them, or incorporate new ones in light of changing evidence. Traditional logical systems, particularly classical logic, assume that once a belief is held (i.e. derived from axioms), it remains unless a contradiction is encountered. But in practical reasoning, especially under uncertainty or incomplete knowledge, beliefs often have to be revised even in the absence of contradictions. AGM provides a formal structure for doing this in a coherent way.

c. Reasoning about Actions
- Frame problem and qualifications in AI planning required default
  and non-monotonic reasoning.
- Influenced the development of action formalisms (e.g., situation
  calculus, event calculus).

d. Modal and Epistemic Logics
- Autoepistemic logic formalised an agent's introspection (what it
  knows about what it knows), inherently non-monotonic.


### What Happened After the 1980s?

The NMR field did not disappear, but it transformed and was absorbed
into other areas:

a. Answer Set Programming (ASP)
- ASP emerged in the 1990s from the stable model semantics of
  logic programs.
- Today it's used for combinatorial problems, planning,
  bioinformatics, and knowledge representation.

b. Knowledge Representation and Reasoning (KR&R)
- NMR is a core topic in KR.
- Description logics (for ontologies) mostly use monotonic reasoning,
  but extensions have been proposed for non-monotonic variants.

c. Computational Complexity
- Foundational work in the '80s and '90s showed many NMR formalisms
  are computationally hard (often Σ₂^P-complete or worse).
- This pushed focus toward tractable fragments and practical implementations.

d. AI Subfields That Incorporated NMR Ideas
- Common sense reasoning
- Qualitative reasoning
- Legal reasoning
- Cognitive architectures (e.g. SOAR, ACT-R use TMS ideas)


### Is Non-Monotonic Reasoning Still Relevant Today?

Sure, in at least three directions:

a. Logic-Based AI
- ASP is actively used in AI research and competitions.
- Planning, diagnosis, and verification tasks benefit
  from NMR-style reasoning (Non-Monotonic Reasoning).

b. Explainable AI (XAI)
- NMR contributes to explainability via explicit reasoning
  paths, contrastive reasoning, and counterfactuals.

c. Combining Symbolic and Subsymbolic AI
- Hybrid models try to blend deep learning with logic-based
  reasoning.
- NMR principles help in dealing with uncertain or defeasible
  symbolic knowledge.

d. Knowledge Graphs & Ontologies
- Researchers explore default reasoning over graphs, semantic
  web rules, and non-monotonic extensions to OWL.


### Modern Examples and Projects

- DLV system (ASP solver)
- Clingo (modern ASP system combining logic programming with control)
- Common sense KBs like Cyc and ConceptNet, where defaults and defeasibility are key
- AI planning tools like PDDL+, handling default effects


### Suggested Literature for Follow-Up

* Brachman, R. J., & Levesque, H. J. (2022). *Knowledge representation and reasoning* (2nd ed.). MIT Press.
* Brewka, G. (1991). *Nonmonotonic reasoning: Logical foundations of commonsense* (Vol. 12). Cambridge University Press.

* For hands-on practice look into tools like:
  - clingo: https://potassco.org/clingo/
  - DLV: http://www.dlvsystem.com/


### Summary

Non-monotonic reasoning introduced the idea that conclusions can be retracted in the
light of new evidence--crucial for human-like reasoning. While its initial wave was
theoretical and peaked in the 1980s, its principles evolved into more practical systems
(like ASP) and remain relevant in today's logic-based AI and explainable reasoning
efforts. Its limits are real: computational hardness, the multiple extensions problem,
and the persistent challenge of knowledge acquisition all constrained its reach. But
the problems it posed--how to reason from incomplete knowledge, how to handle defaults
and exceptions, how to update beliefs gracefully--remain as live as ever. The field
that tried to solve them formally left tools and concepts that continue to surface
wherever explicit, inspectable reasoning is needed.
