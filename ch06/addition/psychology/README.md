
## Psychology and programming
	
- Kahneman, Daniel (2011). Thinking, fast and slow. 1. ed. New York: Farrar, Straus and Giroux
- Kahneman, D., Sibony, O. & Sunstein, C. R. (2021). Noise: a flaw in human judgment. London: William Collins.

Daniel Kahneman, a psychologist, is best known for his groundbreaking work on decision-making, behavioral
economics, and cognitive biases. His work, particularly in collaboration with Amos Tversky, has had a
profound influence on our understanding of how humans think, make decisions, and solve problems. While his
ideas originate in psychology and behavioral economics, many of them are directly relevant to programming,
software engineering, and software development processes.

This relevance has become even more pronounced with the increasing presence of large language models (LLMs)
in the programmer’s everyday workflow. LLMs amplify intuitive, fast reasoning and lower the cost of producing
plausible solutions, making it more important—not less—to understand the limits of human judgment and the
systematic biases that affect it.

It can be challenging to fully grasp Kahneman’s ideas, and interpretations may deviate from his original
perspective. Nonetheless, exploring fields beyond the confines of strictly programming can be profoundly
enriching and offer valuable insights, particularly when programming is no longer a purely manual activity
but a collaboration between human judgment and automated generation.

*Project: Discuss Kahneman’s ideas and their possible applications to programming.*



#### System 1 and System 2 thinking

One of Kahneman’s most influential ideas is the distinction between two modes of thinking.
- System 1: Fast, automatic, intuitive, and often unconscious. This system relies on heuristics
(mental shortcuts) and is quick to form conclusions, which can lead to systematic errors.
- System 2: Slow, deliberate, effortful, and logical. This system is used for more complex
problem-solving and critical thinking, but it requires attention and cognitive resources.

In the context of LLM-assisted programming, this distinction becomes especially important. LLMs effectively
externalize and automate System 1 thinking: they generate code quickly, fluently, and with high surface
plausibility. They do not, however, replace System 2 thinking, which remains the programmer’s responsibility.

Programming and debugging: When debugging, programmers often rely on System 1 thinking—jumping to
conclusions or making quick assumptions about the cause of a problem. This tendency can be reinforced by
LLMs, which readily propose explanations or fixes that sound reasonable. By deliberately engaging
System 2 thinking, developers can approach problems more methodically, carefully testing assumptions and
investigating behavior step by step.

Example: If a bug occurs, a developer might quickly assume it is a variable initialization issue (System 1),
perhaps reinforced by an LLM-generated suggestion. By stepping through the code, using a debugger, writing
targeted tests, or inspecting invariants, the developer engages System 2 thinking and is more likely to
identify the true root cause.

Code reviews: During code review, it is easy to fall into System 1 thinking, focusing on style issues or
patterns that “look wrong.” With LLM-generated code, this risk increases, as the code may appear idiomatic
and polished. Applying System 2 thinking allows reviewers to critically assess logic, assumptions,
edge cases, and architectural implications rather than surface appearance.



#### Cognitive biases (heuristics)

Kahneman and Tversky identified various cognitive biases that affect human judgment. Many of these biases
directly influence programmers, particularly when making decisions about code, algorithms, tools, or
architectural design. The presence of LLMs does not remove these biases; instead, it often amplifies them by
providing fast, confident suggestions.

##### Relevant to programming
Anchoring bias: The tendency to rely too heavily on the first piece of information (the “anchor”) when
making decisions.

Application: A programmer may overvalue an initial design, implementation, or LLM-generated solution and
refine it incrementally instead of reconsidering the problem from first principles.

Availability heuristic: Making decisions based on easily available information or recent experiences,
rather than all relevant data.

Application: A developer may choose a solution based on recently used libraries, frameworks, or examples
produced by an LLM, rather than conducting a broader evaluation of alternatives.

Confirmation bias: The tendency to search for or interpret information in ways that confirm existing
beliefs or hypotheses.

Application: When debugging, a programmer may selectively attend to evidence that supports their initial
theory of the bug, potentially reinforced by an LLM that provides plausible but incorrect explanations.

Overconfidence bias: Believing one knows more or can do more than is actually the case.

Application: The speed and fluency of LLM-generated code can increase overconfidence, leading developers to
underestimate the effort required for validation, integration, and long-term maintenance.



##### Mitigation strategies

Designing for bias: Awareness of cognitive biases allows programmers to deliberately counteract them.
Practices such as peer reviews, explicit assumption-checking, and structured design discussions become even
more important in an LLM-augmented workflow.

Use of checklists and formal methods: Formal, systematic approaches to design, testing, and verification
help reduce reliance on intuition alone. When code generation is cheap, validation and specification become
the primary safeguards against error.



#### Planning fallacy

The planning fallacy refers to the tendency to underestimate the time and effort required to complete tasks,
even when past experience suggests otherwise.

Time estimation: Developers often underestimate how long features or projects will take, particularly
when early prototypes or LLM-generated code give the impression of rapid progress.

Solution: Kahneman recommends reference class forecasting: basing estimates on data from similar past
projects. In programming, this means accounting for integration, testing, documentation, and validation,
not just initial code generation.

Feature creep: The planning fallacy can also contribute to feature creep, as new functionality appears
cheap to add. Incremental development, explicit scope management, and regular reassessment help counteract
this tendency.



#### Loss aversion and risk aversion

Kahneman’s work on loss aversion shows that people experience losses more strongly than equivalent gains.

Refactoring and changes: Developers may resist refactoring or replacing code—especially code generated
quickly by an LLM—because it feels like discarding something valuable.

Solution: Emphasizing regeneration over preservation can help. When code is viewed as a disposable artifact
derived from specifications and tests, rather than as a handcrafted asset, loss aversion is reduced.

Risk-averse decisions: Programmers may stick to familiar tools or architectures, even when better options
exist.

Solution: Prototyping, experimentation, and a culture that treats failure as information rather than loss
encourage innovation and learning.



#### The halo effect

The halo effect is the tendency for an overall impression to influence specific judgments.

Bias in code reviews: A developer’s reputation, or the perceived authority of an LLM-generated solution,
may bias reviewers toward assuming correctness and overlooking flaws.

Solution: Standardized review processes, explicit criteria, and automated checks help counteract this bias
by shifting evaluation from reputation to evidence.



#### Endowment effect

The endowment effect is the tendency to overvalue what one already owns.

Code ownership: Developers may overvalue their own code—or code they have iteratively refined with an
LLM—and resist changes.

Solution: Encouraging collective ownership and emphasizing specifications, tests, and shared goals over
individual authorship helps detach identity from artifacts. Or, more succinctly: kill your darlings.



### Conclusion: Applying Kahneman’s insights to programming

Kahneman’s insights into human behavior, judgment, and bias offer a powerful lens for improving programming
practice. This is especially true in a landscape where LLMs accelerate intuition, pattern completion, and
surface-level correctness.

By understanding System 1 and System 2 thinking, cognitive biases, and heuristics, programmers can design
workflows that deliberately compensate for these limitations. This leads to better estimation, more robust
debugging, clearer specifications, and more rational design decisions.

LLMs do not eliminate the need for judgment; they sharpen the need for it. Kahneman’s work helps programmers
recognize where human and machine intuition are most likely to fail, and how disciplined methods—testing,
specification, review, and formal reasoning—can turn fast generation into reliable systems.
