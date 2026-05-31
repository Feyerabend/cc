## Learning Blueprint: Judgment, Craft, and the Critical Use of Tools

This chapter is structurally different from the others. It does not introduce
a new programming technique or a new computational model. It asks students to
step back from what they have been building and ask: *how should this be done?
What does it mean to do it well? And how does that change when a machine can do
much of it for you?*

The primary mode is critical reflection, not construction. Students still write
code — the projects are technically substantive — but the deliverables are
as much written analysis and argument as working programs.

This chapter works best when students have completed at least ch03 (testing)
and ch05 (compilers). The questions it asks about software quality, design
decisions, and the role of LLMs are grounded most naturally in work students
have already done. The chapter asks: *looking back at what you built, was it good?
How would you know? How should you have built it?*

LLMs are used extensively in this chapter — and also analysed as objects of study.
Students use them, document that use, and then critique both the outputs and their
own process of using them.


### Pedagogical Principles

__1. Judgment cannot be specified, only exercised__

Craftsmanship involves decisions that cannot be fully reduced to rules.
This chapter deliberately presents situations with no single correct answer
and asks students to defend their choices. The goal is to develop judgment,
not to identify the "right" practice.

__2. Critical reading is as important as critical writing__

Students read code they did not write and form an opinion about it. They read
LLM output and form an opinion about it. They read their own earlier code and
form an opinion about it. These three kinds of reading are all in play.

__3. Documentation is a form of argument__

Every project in this chapter requires written documentation of decisions and
reasoning. This is not supplementary to the technical work. In this chapter,
the written argument is often the primary deliverable.

__4. LLM use must be auditable__

For this chapter specifically, every significant LLM interaction must be logged:
the prompt, the output, whether it was accepted, modified, or rejected, and why.
This log is part of the assessment. A student who cannot explain their LLM
interactions has not engaged with the chapter's core questions.


### Structure of the Chapter

#### Sequence 1: What Does Good Code Look Like?

*Experience*

Students are shown two implementations of the same function: one from
`ch06/addition/tidy/working/` (functional but messy) and one from
`ch06/addition/tidy/clean/` (refactored). Both pass the same tests.

Without explanation, students are asked: which is better? Write down your reasons.

*Reflection*

"What criteria did you use? Where do those criteria come from? Are they universal,
or do they depend on context?"

After discussion: present a third version that is cleaner but significantly slower.
Ask the same question again.

LLM-assisted task: "Here are two implementations. Which is better? Give me the
strongest argument for each one. Then tell me what additional information would
change your answer."

*Conceptualisation*

Introduce the vocabulary of software quality: cohesion, coupling, readability,
maintainability, testability, performance. The key insight: these are different
dimensions, and optimising for one often degrades another. Good code is good
*in a context*.

*Extension*

Students take a piece of their own code from an earlier chapter and refactor it
according to one of the quality criteria they found most compelling. They write
a short note explaining what they changed and why.


#### Sequence 2: The Deskilling Question

*Experience*

Students perform the deskilling study from [PROJECTS.md](./intermediate/PROJECTS.md):
the same task twice, once without LLM assistance and once with.

This is not a race. The goal is observation, not efficiency.

*Reflection*

"What was different about your experience of the two runs? Not the output —
your experience. What did you notice about your own thinking?"

This reflection should be written immediately after completing both runs,
while the experience is fresh. It is the central document for this sequence.

LLM-assisted task (meta): After completing both runs, ask an LLM: "What skills
does a programmer need that cannot be developed through LLM-assisted coding?
Now argue against your own answer."

*Conceptualisation*

Introduce the concept of deskilling from labour sociology. Apply it to programming:
what is the difference between using a tool and depending on a tool? What skills
are at risk? What new skills are required?

Connect to `ch06/addition/deskilling/README.md` and `future/DEBT.md`.

*Extension*

Students identify one specific programming skill they believe is at risk of
being deskilled by LLM use. They write a short argument for why that skill
still matters and how it could be preserved in education.


#### Sequence 3: The Logic Audit

*Experience*

Students perform a logic audit on a piece of code they did not write.
See [PROJECTS.md](./intermediate/PROJECTS.md), Project 3.

The audit begins with a simple question: "Does this comment accurately describe
this code?" Students go line by line through a short function.

*Reflection*

"How many comments were inaccurate? Were the inaccuracies deliberate lies,
honest mistakes, or descriptions that were once correct but became wrong?
What does each kind of inaccuracy tell you about the code's history?"

LLM-assisted task: "Here is a function and its documentation. Identify every
place where the documentation and the code are inconsistent. Categorise each
inconsistency by severity."

*Conceptualisation*

Introduce the idea of documentation as a claim about code. Documentation can be
wrong in the same way that code can be wrong. The logic audit is a systematic
technique for checking those claims.

Connect to testing: a unit test is also a claim about code. The relationship
between tests, comments, and specifications as different levels of claim.

*Extension*

Students audit a piece of LLM-generated code using the same methodology.
How does the character of the inaccuracies differ from those in human-written code?


#### Sequence 4: Design Under Pressure

*Experience*

Students are given a specification with deliberate ambiguities and asked to
implement it. They have 30 minutes. No clarifying questions allowed.

After implementation, the "real" requirements are revealed. There are always
two or three points where the revealed requirement differs from what students
assumed.

*Reflection*

"Which of your assumptions turned out to be wrong? Were they reasonable assumptions
given the information available? What would you have done differently if you had
had more time?"

LLM-assisted task: "Here is an ambiguous specification. List every ambiguity
you find. For each, describe the two most different implementations that would
satisfy the letter of the specification. Do not resolve the ambiguity — just name it."

*Conceptualisation*

Introduce the concept of requirements and the problem of specification.
The relationship between agile methods and specification ambiguity.
The difference between a decision made because it is right and a decision made
because you ran out of time.

*Extension*

Students write a clearer specification for the original task. They swap
specifications with another student and implement each other's version.
They compare: did their specification prevent the ambiguities they encountered?


#### Sequence 5: The GPT-2 Study

*Experience*

Students run the GPT-2 pipeline from `ch06/addition/gpt2/`.
See [PROJECTS.md](./intermediate/PROJECTS.md), Project 1.

*Reflection*

"What would a student who did not know GPT-2 was a language model think
about its outputs? What would they assume it understood? Where would they
be wrong, and why?"

This reflection should be written from the perspective of a naive user,
not a technical one. The goal is to develop empathy for non-technical users
who encounter LLM outputs.

*Conceptualisation*

Introduce the distinction between generating plausible text and understanding.
Connect to `ch06/addition/psychology/README.md`: why do humans attribute
understanding to LLM outputs? What cognitive tendencies does this exploit?

Connect forward to ch08: formal methods are one response to the unreliability
of plausible reasoning.

*Extension*

Students ask GPT-2 to explain a concept from an earlier chapter.
They grade the explanation against the chapter's own materials.
They write a one-paragraph correction for the worst error they find.


#### Self-Study Path

A learner working alone follows this order:
1. Perform the deskilling study. Write the reflection immediately.
2. Read `easy/EXERCISES.md` on code quality, design, and LLMs.
3. Perform a logic audit on one function from an earlier chapter's code.
4. Run the GPT-2 study and write the failure analysis.
5. Read `advanced/FOUNDATIONS.md`.
6. Choose one further project from PROJECTS.md and complete it with full LLM logging.

*Outcome:*

By the end of this chapter the learner will:
- Have a vocabulary for discussing software quality across multiple dimensions.
- Have experienced and reflected on the deskilling effect of LLM-assisted coding.
- Be able to conduct a logic audit on unfamiliar code.
- Have generated, analysed, and critiqued LLM output systematically.
- Understand that design decisions require judgment that cannot be automated.
