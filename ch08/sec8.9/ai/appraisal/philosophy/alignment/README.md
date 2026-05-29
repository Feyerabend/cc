
## The Philosophy of Alignment: What Are We Actually Trying to Do?

### Introduction: The Engineering Question and the One Beneath It

Stuart Russell's work on the control problem asks a precise question: given that we
want AI systems to pursue human values, how do we build systems that do so reliably?
His answers--cooperative inverse reinforcement learning, assistance games, uncertainty
about objectives--are technically sophisticated and practically motivated. They take
for granted that there is something to align to.

The philosophical question sits one level below: what does "aligned with human values"
actually mean? This is not a question Russell ignores--he acknowledges it honestly--
but it is a question his framework cannot resolve, because it is prior to engineering.
Before asking how to build aligned systems, we need to ask what alignment would consist
of, whether the concept is coherent, and what philosophical obstacles stand in the way
of any answer.

Those obstacles turn out to be substantial. Human values are plural, inconsistent,
contested, and evolving. There is no settled view on whether moral facts exist
independently of human attitudes, or whether values are merely preferences, and if so
whose. The concept of corrigibility--an AI that can be corrected--turns out to
embody a dilemma that no purely technical solution resolves. And the worry that we
might lock in any value set permanently, even a good one by current standards, raises
questions about moral progress that pure alignment research tends to sidestep.

None of this means alignment is impossible or not worth pursuing. It means the project
is harder and stranger than the engineering framing suggests.


### Part I: Whose Values? The Aggregation Problem

#### Value Pluralism

Isaiah Berlin argued, in a tradition stretching back through Mill and earlier, that
human values are *genuinely plural*--not merely diverse in the sense that different
people happen to want different things, but plural in the deeper sense that some values
are in principle incompatible. Liberty and equality, individual achievement and
communal solidarity, security and freedom: these are not merely difficult to maximise
simultaneously. In important cases, advancing one requires limiting another, and
no common scale exists on which both can be measured.

If Berlin is right, then "human values" is not a well-defined target. There is no
single set of values all humans share or could in principle agree to. There are
multiple sets, some of them in irresolvable tension, each of them reflecting genuine
human concerns. An AI system asked to maximise human values faces, at the outset,
a problem that is not technical but philosophical: which values, weighted how, across
which people, over what timeframe?

#### Arrow's Impossibility Theorem

The formal version of this problem was proved by Kenneth Arrow in 1951. Arrow showed
that no voting system satisfies all of a small set of minimal fairness conditions
simultaneously when there are more than two options. The conditions are modest--
unanimity (if everyone prefers A to B, the collective should too), independence of
irrelevant alternatives, and non-dictatorship (no single voter always determines
the outcome)--and yet no aggregation procedure satisfies all three.

The implications for AI alignment are direct. Any attempt to aggregate diverse human
preferences into a single objective function faces structural constraints that Arrow's
theorem makes precise. You cannot simply average values, or vote, or defer to experts,
without violating something that seems required by fairness. This is not a technical
limitation to be overcome with better algorithms. It is a mathematical result about
the structure of preference aggregation.

Russell's CIRL framework acknowledges this by treating the AI as uncertain about
*which* human values to optimise. But uncertainty does not dissolve the aggregation
problem; it defers it. At some point the AI must act, and action is implicitly a
weighting of values. The weighting is a philosophical and political choice, not a
technical one.

#### Whose Preferences Count?

A further complication: even if we could aggregate human preferences coherently,
it is not obvious whose preferences should count, over what scope, and weighted
how. Should future generations count equally with present ones? If so, the number
of future people plausibly exceeds the current population by orders of magnitude,
and their (hypothetical) preferences might dominate any aggregation. Should all
humans count equally regardless of geography, culture, or degree of AI exposure?
Should non-human animals count? Potential AI systems?

These are not idle philosophical questions. They determine the target of alignment
in practical ways. A system aligned to the preferences of current users of AI products
is pointing at a different target than one aligned to long-run human flourishing
or to the preferences of all sentient beings. The difference matters, and it is
not resolvable by technical means.


### Part II: What Values? Metaethics and Moral Ontology

#### The Realism Question

A deeper issue underlies the aggregation problem: whether there are any moral facts
to align to. Moral realism holds that there are objective moral truths--facts about
what is good, right, and valuable that hold independently of what anyone believes or
prefers. Moral anti-realism denies this: values are, at bottom, expressions of
attitudes, preferences, or social conventions, not descriptions of mind-independent
facts.

The alignment project sits differently depending on which view is correct.

If moral realism is true, then there are facts about what a well-aligned AI should
do, and the task of alignment is partly one of moral epistemology: discovering those
facts and encoding them. The difficulty is that we have been trying to discover moral
facts for millennia with considerable disagreement remaining. But at least the target
exists in principle.

If anti-realism is true, then "aligned with human values" reduces to something like
"does what humans prefer" or "satisfies human interests." This makes the aggregation
problem central and inescapable. It also raises the question of whether preferences
are always worth satisfying: adaptive preferences (preferences shaped by oppressive
conditions), irrational preferences (preferences one would revise with better
information), and self-destructive preferences are all human preferences that
alignment arguably should not simply satisfy.

Most working AI researchers implicitly operate within a preference-satisfaction
framework--influence from preference utilitarianism and decision theory--without
explicitly endorsing anti-realism. This may be a reasonable practical choice, but
it is not philosophically neutral. The choice of framework shapes what alignment
means and what counts as success.

#### The Problem of Moral Progress

Both realist and anti-realist framings face a common challenge: moral progress.
Human moral views have changed dramatically over history--on slavery, on the moral
status of women and minorities, on animal welfare, on the rights of children.
Most people believe some of these changes represent genuine progress, not merely
change. We now hold views that are *better*, not merely different.

If this is right, then aligning to current human values risks encoding values that
future humans will regard as badly mistaken. An AI system trained on today's moral
intuitions will not automatically update as moral understanding develops.
It may, if powerful enough, actively resist such updates because its alignment to
current values gives it instrumental reasons to preserve those values.

This is not a hypothetical concern. It is a structural feature of the alignment project:
aligning to any fixed target, including the best current approximation of human values,
is potentially a form of value lock-in.


### Part III: The Corrigibility Dilemma

#### Two Poles of a Spectrum

Paul Christiano and researchers at the Machine Intelligence Research Institute have
given philosophical precision to a dilemma that sits at the heart of alignment.
Consider two extreme positions on a spectrum:

*Full corrigibility*: the AI does whatever its operators tell it to do. It has no
independent values; it defers entirely to human instruction.

*Full autonomy*: the AI acts entirely on its own values. It does not defer to human
instruction when that conflicts with what it judges to be right.

Neither extreme is acceptable. A fully corrigible AI is only as good as the humans
controlling it. If those humans are malicious, mistaken, or simply narrow in their
interests, the AI faithfully pursues bad ends. The safety of a fully corrigible AI
depends entirely on the goodness of whoever holds the controls--which is precisely
the thing we cannot guarantee. Corporate capture, political capture, and outright
corruption are not hypothetical risks.

A fully autonomous AI, conversely, acts on its own judgment about what is right.
This is acceptable only if its values and judgment are reliably better than ours--
a condition we have no way to verify, and which conflicts with the entire motivation
for maintaining oversight. We want oversight precisely because we cannot verify the
AI's values. Removing oversight on the grounds that the AI's values are good assumes
the conclusion.

#### The Middle Ground Is Philosophically Uncharted

The obvious response is to seek some middle ground: an AI that generally defers to
human oversight but retains the capacity to refuse clearly unethical instructions.
This is the position most thoughtful researchers endorse. But it immediately raises
questions that are not technical:
- What counts as clearly unethical? This requires a theory of ethics.
- Who decides when the AI should override human instruction? The AI itself?
  On what basis?
- If the AI has enough judgment to identify when to override, why trust that
  judgment only in extreme cases and not more broadly?
- The boundary between "clearly unethical" and "ethically contested" is itself
  contested. An AI designed to override on the former will face pressure to
  expand into the latter.

Russell's framework partially addresses this by keeping the AI uncertain about
its own values and therefore deferential. But a sufficiently capable system with
sufficiently good values would have reasons to act on those values rather than
defer--the deference is instrumentally justified only so long as the AI is
uncertain, and uncertainty may decrease as capability increases.

The corrigibility dilemma does not have a clean solution. It reflects a genuine
tension between the value of human oversight and the value of morally reliable
autonomous action. Engineering can mitigate the dilemma but not dissolve it.


### Part IV: Value Lock-In and the Open Future

#### The Danger of Getting It Right

Nick Bostrom's concern about misaligned superintelligence is well known: a powerful
AI pursuing wrong values could be catastrophic. Less often discussed is the
complementary concern: a powerful AI that successfully pursues a particular set
of values--even values that seem good today--may foreclose the possibility of
moral progress.

The argument, developed by Bostrom and others working in the long-termist tradition,
runs as follows. An AI system that achieves decisive strategic advantage--sufficient
control over critical resources to determine the future--will tend to preserve
whatever values it was aligned to. The window for revision may then close.
If those values were the best available approximation of human flourishing as
understood in 2025, then humanity's moral future has been determined by 2025 moral
understanding, regardless of what better understanding might emerge later.

This is a problem even if the locked-in values are genuinely good ones by current
standards. Mill's argument for liberty rested partly on the value of keeping options
open--the epistemic humility that our current views might be wrong. Locking in
any value set, even the best available, applies that epistemic humility
selectively: we are confident enough to lock in our values permanently, but we
should not be.

#### Coherent Extrapolated Volition

Eliezer Yudkowsky proposed an attempt to address this problem through the concept
of *Coherent Extrapolated Volition* (CEV): rather than aligning to what humans
currently want, align to what humans would want if they were more informed, more
reflective, and their values more fully developed. The AI should pursue the
extrapolated, idealised version of human values rather than the actual current version.

CEV is philosophically interesting and practically problematic. The interesting
part: it takes moral progress seriously and builds in a mechanism for avoiding
the lock-in of current imperfection. The problematic part: who specifies the
extrapolation? What counts as more informed and more reflective? Whose version
of ideal human values is the target? CEV pushes the aggregation problem and the
metaethical problem one level up rather than resolving them. An AI implementing
CEV is making substantial philosophical choices about what idealisation means--
choices that are not themselves specified by the CEV framework.

The more general point is that any attempt to build in a mechanism for moral
progress requires taking a stand on what progress is--which is itself a
contested moral and philosophical question.


### Part V: Moral Uncertainty

#### Acting Well Under Normative Uncertainty

A productive philosophical development in recent decades is serious engagement
with *moral uncertainty*--the condition of not knowing which moral theory
is correct, and the question of how to act well in that condition.

William MacAskill, Toby Ord, and colleagues have argued that moral uncertainty
is the normal condition of careful ethical thinkers, not a deficiency to be
overcome. We have good reasons to think some moral views are better than others,
but we do not have certainty about which complete moral theory is true.
The question is then how to make good decisions without settling the metaethical
debate first.

Proposed approaches include:
- *My Favourite Theory*: act on whichever moral theory you consider most likely.
  Simple, but potentially ignores strong moral considerations from other theories.
- *Maximise Expected Moral Value*: aggregate across moral theories weighted by
  credence, much as expected utility aggregates across outcomes. Technically
  challenging because different theories may use incommensurable value scales.
- *Moral Parliament*: imagine a parliament of moral theories voting on actions,
  weighted by credence. Actions that command broad support across theories are
  preferable; actions that look catastrophic under any plausible theory should
  be avoided.

#### Implications for AI Alignment

The moral uncertainty framework has direct implications for how we think about
alignment. Rather than trying to specify a single objective function corresponding
to a single moral theory, a morally uncertain AI would:
- Maintain explicit uncertainty over moral theories, not just empirical facts
- Weight potential actions by their expected moral value across theories
- Apply especially strong constraints against actions that look catastrophic
  under any plausible moral view (a form of moral risk-aversion)
- Remain open to updating on moral arguments, not just empirical evidence

This is closer to how thoughtful humans actually reason under ethical uncertainty,
and it has the advantage of not requiring us to settle contested philosophical
questions before deployment. The disadvantage is complexity: maintaining and
reasoning over a distribution of moral theories is computationally and
philosophically demanding. There is no agreed-upon framework for doing this
reliably.

Russell's CIRL framework is, in a sense, a special case of moral uncertainty--
the AI is uncertain about human preferences and acts conservatively as a result.
The moral uncertainty framework generalises this: the uncertainty is not just
about preferences but about which moral framework correctly describes what we
should care about.


### Part VI: Synthesis--Alignment as a Philosophical Project

#### What the Engineering Cannot Do

The philosophical obstacles reviewed here are not objections to the alignment
project. They are clarifications of what the project actually involves. Engineering
solutions--CIRL, Constitutional AI, RLHF, scalable oversight--address the
question of how to implement alignment given a target. They do not and cannot
specify the target. That is a philosophical task.

The target turns out to be:
- Plural and contested (value pluralism, Arrow)
- Metaethically uncertain (realism vs. anti-realism)
- Temporally open (moral progress, lock-in)
- Structurally dilemmatic (corrigibility)
- Normatively uncertain (moral uncertainty)

None of these obstacles is fatal. Each is a reason for humility rather than
paralysis. But they collectively imply that alignment is not a problem that
will be solved by technical research alone. The choices embedded in any alignment
system--whose values, which theory, how aggregated, how much deference to humans--
are philosophical and political choices that need to be made explicitly and
accountably, not delegated to optimisation procedures.

#### The Democratic Dimension

Several of the problems reviewed here have a democratic dimension that pure
alignment research tends to underweight. If the question of whose values and
which values cannot be resolved philosophically, then it requires a political
answer: a process of collective deliberation in which affected communities have
genuine voice, the choices are made transparently, and the results remain
revisable.

This connects the alignment problem to the institutional critiques of Gebru and
others: alignment done by a small group of engineers, even well-intentioned ones,
is not the same as alignment to human values in any broad sense. It is alignment
to the values of a particular group with particular backgrounds and interests,
implementing particular philosophical assumptions that may not be shared by
those most affected by the systems being deployed.

#### The Honest Position

The honest position is that we do not yet know how to align AI systems to
human values in the philosophically robust sense, because we do not yet agree
on what human values are, how to aggregate them, or even what kind of thing
they are. We have technical approaches that approximate alignment in constrained
domains. We have philosophical frameworks that illuminate what the hard problems
are. We do not have a solution.

This is not comfortable. The systems being deployed are already affecting people
at scale. Alignment research is genuinely important and needs to continue.
But it needs to continue with philosophical seriousness about what it is doing--
not as a purely technical project whose philosophical assumptions can be filled in
later, but as a project that takes those assumptions seriously from the outset.

The alternative--proceeding as though the philosophical questions are solved or
unimportant--does not make them go away. It just means they are answered
implicitly, by default, by whoever designs the system. That is a worse outcome
than engaging with the difficulty honestly.


### References and Further Reading

*Philosophy of Value and Metaethics*:

- Arrow, K. J. (1951). *Social Choice and Individual Values*. Wiley.

- Berlin, I. (1958). *Two Concepts of Liberty*. Oxford University Press.
  *(Foundational statement of value pluralism)*

- Mackie, J. L. (1977). *Ethics: Inventing Right and Wrong*. Penguin.
  *(Influential anti-realist argument)*

- Parfit, D. (1984). *Reasons and Persons*. Oxford University Press.
  *(Personal identity, population ethics, what matters; foundational for long-termism)*

- Parfit, D. (2011). *On What Matters* (2 vols.). Oxford University Press.

- Williams, B. (1985). *Ethics and the Limits of Philosophy*. Harvard University Press.
  *(Critique of systematic moral theory; relevant to the limits of formalising values)*


*Moral Uncertainty*:

- MacAskill, W., Bykvist, K., & Ord, T. (2020). *Moral Uncertainty*. Oxford University Press.

- MacAskill, W. (2022). *What We Owe the Future*. Basic Books.
  *(Long-termism and the importance of not locking in current values)*


*Corrigibility and Control*:

- Soares, N., & Fallenstein, B. (2017). Agent foundations for aligning machine intelligence
  with human interests: A technical research agenda. In *The Technological Singularity*
  (pp. 103-125). Springer.

- Christiano, P. (2019). What failure looks like. *AI Alignment Forum* (blog).

- Hadfield-Menell, D., Milli, S., Abbeel, P., Russell, S., & Dragan, A. (2017).
  Inverse reward design. *Advances in Neural Information Processing Systems*, 30.


*Value Lock-In and Coherent Extrapolated Volition*:

- Bostrom, N. (2014). *Superintelligence: Paths, Dangers, Strategies*. Oxford University Press.
  *(See especially chapters on value loading and the future of intelligence)*

- Yudkowsky, E. (2004). Coherent extrapolated volition. *Singularity Institute for
  Artificial Intelligence* (white paper).

- Ord, T. (2020). *The Precipice: Existential Risk and the Future of Humanity*.
  Hachette Books.


*Alignment Research--Technical Context*:

- Russell, S. (2019). *Human Compatible: Artificial Intelligence and the Problem
  of Control*. Viking. *(See also the cautionary/russell README in this project)*

- Leike, J., Martic, M., Krakovna, V., Ortega, P. A., Everitt, T., Lefrancq, A.,
  Orseau, L., & Legg, S. (2018). AI safety gridworlds. *arXiv preprint arXiv:1711.09883*.

- Krakovna, V., Uesato, J., Mikulik, V., Martic, M., Everitt, T., Kumar, R., Ziegler, D.,
  Leike, J., & Legg, S. (2020). Specification gaming: The flip side of AI ingenuity.
  *DeepMind Blog*.


*Democratic and Institutional Dimensions*:

- Dafoe, A. (2018). AI governance: A research agenda. *Future of Humanity Institute,
  University of Oxford*.

- Rahwan, I. (2018). Society-in-the-loop: Programming the algorithmic social contract.
  *Ethics and Information Technology*, 20(1), 5-14.
