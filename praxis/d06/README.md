
## Teaching / Learning

This chapter differs significantly from the others. Rather than focusing on tools
or techniques alone, it introduces a perspective — a philosophy and methodology
that, until very recently, shaped how we understood programming and software
development. It serves as a conceptual backdrop: a framework against which we can
question, reflect, and construct new ideas. At the centre of this exploration lies
the notion of *craftsmanship* in programming.

Programming has long been described not only as a technical discipline, but as a
craft. The term suggests care, skill, judgment, and a sense of responsibility for
the quality of one's work. Craftsmanship implies more than simply producing
functioning code; it involves clarity, maintainability, elegance, and an awareness
of how decisions affect others who will read, use, or extend the system. It also
carries ethical dimensions: pride in work, respect for users, and attention to
long-term consequences.

Historically, this view has influenced various movements and methodologies.
Agile practices emphasised collaboration, adaptability, and iterative improvement.
Software engineering traditions stressed structure, reliability, and systematic
thinking. Open-source communities highlighted shared ownership and collective
refinement. Each of these approaches reflects assumptions about what it means
to "do good work."

The emergence of LLMs introduces a profound shift in this landscape. Tasks once
considered central to programming — writing boilerplate code, generating
documentation, even designing components — can now be partially automated.
This development raises important questions. If machines can produce code,
what becomes of the programmer's role? Does craftsmanship lose its meaning,
or does it acquire new significance? How should we evaluate skill, creativity,
and understanding in an era of AI-assisted development?

These questions are not merely technical; they are philosophical and practical.
They concern how we learn, how we collaborate, how we judge quality, and how we
define expertise. They challenge assumptions about authorship, originality, and
responsibility. Most importantly, they invite reflection on what remains uniquely
human in programming.

This chapter is therefore an invitation: to think critically, to debate, and to
reconsider familiar concepts. Rather than offering definitive answers, it provides
a starting point for discussion. What does craftsmanship mean today? How should
programmers adapt? What values should guide us as technologies evolve?
What alternatives exist? How should we think anew about programming?

*Programming is decision-making under constraints.*


### Teacher Focus

- **No single right answer.** This chapter is about trade-offs, not best practices.
  Resist the urge to resolve debates. The goal is for students to develop and defend
  positions, not to discover the correct position.
- **Code as an object of critical reading.** Present code not just as something to
  run and debug, but as something to evaluate. What values does this code express?
  What did the author prioritise? What did they sacrifice?
- **LLM output as evidence.** Use LLM-generated code or explanations as material
  for the logic audit exercise. Ask: does this code do what it claims? What assumptions
  does it make? Who is responsible if those assumptions are wrong?
- **The deskilling question is genuine.** Do not dismiss concerns about LLM deskilling
  as either alarmism or technophobia. Engage with the evidence students bring from
  their own experience in the deskilling study. Their observations are data.
- **Oral defence is essential.** Written design rationales can be drafted with LLM
  assistance. Oral defence cannot. Every significant design decision in this chapter
  should be defended in conversation, not just in writing.


### Student Tasks

- Perform the deskilling study: the same task twice, with and without LLM assistance.
  Write the reflection immediately after, while the experience is fresh.
- Conduct a logic audit on a function from an earlier chapter. Document findings
  by severity: critical, warning, informational.
- Given a deliberately ambiguous specification, implement it, then write a short
  document naming every assumption you made that was not stated in the specification.
- Run the GPT-2 pipeline. Find three factual errors, three logical errors, and
  three errors in code generation. Write a one-paragraph analysis of each category.
- For every project in this chapter: document each LLM interaction — what you asked,
  what it produced, whether you accepted or modified the output, and why.


### Concrete Exercise: Two Designs

Present students with an ambiguous requirement:
"Build a component that stores user preferences and makes them available to other parts
of the system. It should be easy to test."

Ask each student to:
1. Propose two different designs. They may be as different as possible.
2. For each design, explicitly list: the assumptions it makes, the risks it introduces,
   and the trade-offs it embodies.
3. Choose one. Write a one-paragraph justification for the choice.
4. Compare with a classmate's choice. Where do you agree? Where do you disagree?
   Can you identify the difference in values or priorities that explains the disagreement?

LLM use: Students may ask an LLM to generate alternative designs.
They must evaluate those designs using the same criteria and explain why they
accepted, rejected, or modified each suggestion.

The point is not to find the best design. It is to practise making design decisions
explicitly and defending them against alternatives. A student who can articulate
*why* they made a choice — and who can engage with a challenge to that choice —
has learned more than one who produced a correct implementation.


### Example: The Logic Audit in Practice

A logic audit is a systematic check of claims made about code against the code itself.
It is a form of critical reading applied to software.

A teacher takes a short function — say, a cache with an expiry mechanism — and
reads it aloud with the class. For each comment, the class asks:

- Is this comment accurate? Does the code do what it says?
- Is this invariant maintained? Show me where.
- Is this precondition checked? What happens if it is not?
- Is this error path handled? What does the caller do if it receives an error here?

Most functions, even well-written ones, have at least one comment that is slightly
wrong, one invariant that is assumed but not checked, and one error path that is
handled less carefully than the happy path.

This is not a criticism of the author. It is a demonstration of what careful reading
reveals. The audit is not about finding blame; it is about building a habit of asking
"how do I know this is true?"

When the same audit is applied to LLM-generated code, the results are instructive.
LLM-generated code often has comments that are fluent and confident and wrong.
The discrepancy between the authoritative tone and the actual content is a concrete
demonstration of the difference between plausible and verified — a theme that runs
from this chapter all the way to ch08.


### LLM Use

LLM use is explicitly part of the subject matter in this chapter, not just a tool.

Guidelines:
- All significant LLM interactions must be logged: the prompt, the output, whether
  it was accepted, modified, or rejected, and the reason.
- LLMs may be used to generate designs, explain concepts, critique code, and produce
  alternative implementations. This is encouraged.
- The deskilling study requires one run *without* LLM assistance. That constraint
  is not optional.
- In the GPT-2 study, the analysis of failure is the deliverable. Running the
  pipeline and accepting the output without critique is not completing the project.

The underlying question this chapter asks about LLMs is the same question it asks
about all tools: *what does using this tool cost, and who pays that cost?*
Students who have worked through this chapter should be able to answer that question
with evidence from their own experience, not just from theory.
