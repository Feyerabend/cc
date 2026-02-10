
## Code Reviews from Other Angles

I have long advocated for the integration of the humanities and technology;
in fact, it’s right there in my company name: *Set Lonnert Humanities and Technology*.
It likely comes as no surprise, then, that one way to bridge these two worlds
is through *code reviews*. Here are a few angles to explore.

As *Large Language Models* (LLMs) blur the boundaries between natural language
and code, we could/should look to the humanities for better ways to communicate with
both machines and humans. We can draw from long-standing traditions of literary
critique, peer review, and adversarial discourse to bring a deeper level of
reflection to the way we review code.


### Code Review as Peer Review

At a structural level, code review functions much like peer review in academia.
Both processes share fundamental purposes: they seek to enhance the quality of
work before it is published or merged, uncover errors that the original creator
might overlook, uphold community standards, facilitate the sharing of unspoken
knowledge, and build legitimacy and trust among participants. In the scientific
realm, the core artefact under scrutiny is a research paper, where the key claims
revolve around theoretical or empirical insights, and potential flaws often stem
from conceptual gaps, methodological weaknesses, or interpretive missteps. By
contrast, in software development, the artefact is the code itself, with claims
centered on functionality, performance, or maintainability, and errors typically
manifesting as logical inconsistencies, architectural flaws, or semantic ambiguities.
Ultimately, in both domains, reviewers go beyond mere verification of accuracy;
they assess how well the work fits within an established framework of norms
and expectations.

This parallel offers valuable lessons for programmers drawing from scientific peer
review. It underscores that a review should target the artefact rather than serve
as a personal judgment of its author. Reviewers bear a duty not only to identify
issues but also to contribute constructively toward improving the work, rather
than simply dismissing it. Disagreements are a natural and often fruitful part
of the process, fostering deeper understanding. Moreover, clarity and reproducibility
are just as crucial as outright correctness, ensuring the work's long-term value.
In practice, effective code reviews should probe essential questions: Is the
underlying intent transparent? Could another skilled practitioner reliably reproduce
or build upon this code? And does it conform to the prevailing practices in the
relevant codebase or field?

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

Code review shares a profound, yet often overlooked, analogy with literary critique,
offering a powerful lens for understanding software development. At its core, code
functions as a form of text--primarily written for human comprehension, with execution
by machines as a secondary concern. It is interpreted within layers of context,
including historical precedents, established conventions, and the expectations of its
audience. In much the same way, literary critique delves into elements such as structure,
style, voice, underlying assumptions, ambiguities, and even what remains unspoken or implied.

Many of the bugs and long-term maintenance challenges in software do not stem from
straightforward syntax errors but from deeper interpretive issues: ambiguous intent
that confuses readers, misleading abstractions that obscure true functionality,
overloaded meanings that lead to misuse, and hidden assumptions that only surface
under specific conditions. These are fundamentally hermeneutic problems--matters of
interpretation and meaning--rather than purely technical glitches.

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


