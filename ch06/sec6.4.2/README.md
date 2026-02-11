
## Code Reviews from Other Angles

There is a particular pleasure in observing how ideas travel between domains
that are too often kept apart. For years, I have argued for a deliberate
entanglement of the humanities and technology--a conviction so central that
it found its way into my company’s name: Set Lonnert Humanities and Technology.
It is therefore hardly surprising that one of the most fertile meeting grounds
between these worlds emerges--as I perceive it--in a practice as seemingly
technical, and yet profoundly human, as the *code review*.

As *Large Language Models* continue to soften the boundary between natural
language and code, we find ourselves compelled to reconsider how we communicate.
Not only with machines, but with one another. In this shifting landscape, the
humanities offer more than ornament or analogy; they offer intellectual tools
honed over centuries. Traditions of literary critique, scholarly peer review,
and even adversarial discourse provide frameworks for reflection, interpretation,
and judgment that can deepen the way we evaluate software.


### Code Review as Peer Review

Seen from a structural vantage point, code review bears a striking resemblance to
academic peer review. Both are rituals of scrutiny performed before a work is
released into the world, designed to elevate quality, expose blind spots, uphold 
ommunal standards, and cultivate trust. In science, the artefact under examination
is the *research paper* Its claims are woven from theory, evidence, and interpretation,
its weaknesses often lurking in conceptual gaps or methodological frailties.
In software development, the artefact is the *code itself*. The code advance claims
about functionality, performance, and maintainability, with flaws revealing 
as logical fractures, architectural misjudgments, or semantic uncertainties.
Yet in both domains, the reviewer’s task extends beyond the mere verification
of correctness. What is assessed is not simply whether the work functions, but
whether it coheres, with norms, with expectations, with the shared understanding
of a community.

This parallel carries lessons of quiet but considerable importance. Scientific peer
review reminds us that critique is directed toward the artefact rather than the
individual, that the reviewer’s responsibility lies as much in improving the work
as in identifying its deficiencies, and that disagreement is neither aberration
nor failure but an engine of intellectual progress. Clarity and reproducibility
emerge as virtues equal to accuracy, ensuring that knowledge--or code--may endure
beyond its initial creation. The same sensibilities, when carried into programming,
transform the code review from a gatekeeping mechanism into a collaborative act of
refinement. The central questions become disarmingly simple yet deceptively profound:
Is the intent lucid? Could another skilled practitioner extend or reconstruct this work?
Does it resonate with the conventions and practices of its environment?

*Scientific peer review reminds us that:*
- A review is *not* a judgment of the author, but of the artefact
- The reviewer has a responsibility to *improve* the work, not just reject it
- Disagreement is normal and often *productive*
- *Clarity and reproducibility* matter as much as raw correctness

*Good code review should ask:*
- Is the intent clear?
- Could another competent practitioner reproduce or extend this?
- Does this align with accepted practice in this codebase or domain?


### Code Review and Literary Critique

Equally illuminating is the comparison between code review and literary critique.
Code, after all, is a form of text--written primarily for human comprehension,
only secondarily for mechanical execution. No, the machines can handle *machine
code*, and do not bother with code in the sense of language. It is read, interpreted,
and understood within layers of context shaped by history, convention, and audience.
Literary criticism has long concerned itself with precisely these dimensions: structure,
style, voice, assumptions, ambiguity, and the eloquence of what remains unsaid.
Many of the most persistent defects in software do not arise from syntactic missteps
but from failures of interpretation. Intent becomes obscured, abstractions mislead,
meanings multiply, assumptions hide beneath the surface. These are hermeneutic problems,
rooted not in the machinery of code but in the fragile, interpretive space between
writer and reader.

Literary studies provide invaluable lessons for programmers in this regard, encouraging
them to interrogate code with questions like: What does this code claim to accomplish?
What expectations does it establish for those who encounter it? In what ways might a
reasonable reader misinterpret its purpose or behavior? And what metaphors or conceptual
models does it implicitly rely on to convey its logic? For instance, function names
act as rhetorical devices, shaping how developers perceive and interact with the code;
comments serve as narrative frames that guide understanding; and APIs construct overarching
stories about the intended usage and flow of a system.

Ultimately, an effective code review mirrors the practice of close reading in literary
analysis, demanding meticulous attention to subtle details, a keen sensitivity to tone
and clarity, and an acute awareness of how different readers might respond to the text.
This approach elevates code review from a mere checklist of errors to a thoughtful
exploration of communication and intent.

*This is Code as Text*

Code is:
- Written for *humans* first, machines second
- *Interpreted*, not just executed
- Embedded in *context* (history, conventions, audience)

Literary critique examines:
- Structure
- Style
- Voice
- Assumptions
- Ambiguities
- What is left unsaid

Many bugs and maintenance failures arise not from syntax errors, but from:
- Ambiguous intent
- Misleading abstractions
- Overloaded meanings
- Hidden assumptions
- These are *hermeneutic* (interpretation) problems, not technical ones.

From literary studies, programmers can learn to ask:
- What is this code saying it does?
- What expectations does it set for the reader?
- Where might a reader reasonably misinterpret it?
- What metaphors or models does it rely on?

For example:
- Function names are *rhetorical acts*
- Comments are *narrative framing*
- APIs *tell stories* about how a system wants to be used

A good code review resembles close reading:
- *Attention* to small details
- *Sensitivity* to tone and clarity
- *Awareness* of reader response



### Literature Critique vs Adversarial Review Culture

A notable distinction between literary critique and the prevailing culture in code reviews
lies in their tonal approaches. In the humanities, critique tends to be dialogical,
fostering an environment where multiple interpretations can coexist harmoniously,
and disagreements are not only anticipated but actively explored as opportunities for
deeper insight. In contrast, within many engineering cultures, reviews often veer into
an adversarial mode focused primarily on verifying correctness, where the reviewer assumes
an implicit position of authority, and alternative designs are frequently brushed aside
without sufficient consideration.

Humanistic critique, by its nature, prioritises principles such as the charity of
interpretation--approaching the work with an assumption of good faith--alongside a
commitment to contextual understanding and a preference for inquiring "why" something
was done before challenging "why not" pursue a different path. This mindset encourages
empathy and thoroughness in evaluation.

The practical takeaway for code reviewers is to embrace a more humanistic posture,
which involves posing clarifying questions rather than delivering abrupt judgments,
distinguishing between personal lack of comprehension and actual flaws in the work,
and acknowledging that any confusion experienced by the reader constitutes a legitimate
defect in itself--even if the code functions correctly on a technical level. This shift
can transform reviews into more collaborative and constructive exchanges.


*One striking difference is tone.*

In the humanities:
- Critique is often *dialogical*
- Multiple interpretations can *coexist*
- Disagreement is *expected and explored*

In many engineering cultures:
- Reviews drift toward adversarial correctness checking
- The reviewer is implicitly "right"
- Alternative designs are dismissed too quickly

Humanistic critique emphasises:
- Charity of interpretation
- Contextual understanding
- Asking "why" before "why not"

*Practical takeaway:* Adopting a humanistic review posture means:
- Asking clarifying questions instead of issuing verdicts
- Separating "I don't understand" from "this is wrong"
- Recognising that confusion in the reader is itself a defect,
  even if the code is technically correct


### Guidelines

If we integrate lessons from peer review and literary critique, code reviews should:
- Treat code as an argument, not just instructions
- Emphasise clarity, intent, and reader experience
- Encourage dialogue rather than one-sided correction
- Distinguish between:
    - Correctness
    - Quality
    - Style
    - Convention
- Accept that multiple "good" solutions may exist

A strong code review culture looks less like an exam and more like a seminar.
