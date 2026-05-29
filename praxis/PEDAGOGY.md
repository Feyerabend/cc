## Pedagogy: How to Teach and Learn With This Book

This document describes the educational philosophy behind *From Code to Computation*
and its companion materials. It is addressed to both teachers and students.

It is not a summary of what the chapters contain. It is a guide to *how to work with them*:
how to structure sessions, how to approach projects, how to use LLMs responsibly at each
stage, and above all, how to assess learning in a world where the traditional forms of
assessment are no longer reliable.

Read it before you begin. Return to it when the approach feels unclear.


---

### 1. The Underlying Philosophy

This book follows a tradition of education associated with John Dewey: learning happens
through active inquiry, concrete problem-solving, and structured reflection — not through
passive reception of facts. A student who has built something, been surprised by its
behaviour, and revised their understanding based on that surprise has learned something
different in kind from a student who has read a correct description of the same phenomenon.

The specific claim this book makes, which goes beyond Dewey, is that programming education
must reckon with large language models — not as a threat to be managed, but as a condition
to be understood. LLMs change what is easy, what is difficult, and what it means to learn.
An educational approach that ignores this is not neutral; it is obsolete.

The response here is not to ban LLMs, nor to embrace them uncritically. It is to integrate
them deliberately, to study them as objects of inquiry alongside using them as tools, and
to build the habits of mind that remain valuable regardless of what the tools can do.
These habits are: forming hypotheses and testing them; reading code carefully; stating
what you believe and checking whether you are right; explaining your reasoning to another person.

None of these are new. All of them become more important as tools become more capable.


---

### 2. The Learning Cycle

Each chapter is structured around a version of the same cycle. The cycle has five phases.
They do not always occur in strict sequence, and they can operate at the level of a single
session, a whole project, or an entire chapter.

**Experience** — Begin with something concrete and immediate. Build it, run it, or observe it.
Do not explain it first. The point is to generate genuine questions from genuine engagement.
A student who has tried to parse an expression and failed has a different relationship
to parsing theory than one who has only read about it.

**Inquiry** — Surface the questions that the experience raised. These questions are the
entry points for conceptual learning. A question that comes from experience is anchored;
a question presented in the abstract floats free.

**Conceptualisation** — Introduce theory, vocabulary, and formal frameworks *in response*
to the questions raised by inquiry. The theory is not the starting point; it is the
explanation. A grammar is not a definition to memorise; it is an answer to "why does
my parser fail on this input?"

**Application** — Return to the concrete. Extend the original experience using the new
concepts. This is where understanding consolidates: not in reading the theory, but in
finding that the theory actually helps.

**Reflection** — Name what changed. What do you now understand that you did not before?
What new questions have opened up? What would you do differently? This phase is
frequently skipped under time pressure. It should not be. Reflection is what transforms
an experience into a lesson that transfers to the next problem.


---

### 3. The Chapter Arc

The pedagogy changes deliberately across the eight chapters. This is not arbitrary.
It reflects the book's arc from mechanical certainty (representation, virtual machines)
toward adaptive reasoning (formal methods, AI tools).

| Chapter | Topic | LLM role | Primary mode |
|---------|-------|----------|--------------|
| 01 | Representation | None | Teacher-led discovery |
| 02 | Virtual machines | Explanation partner | Guided construction |
| 03 | Debugging and testing | Hypothesis generator — verify independently | Systematic investigation |
| 04 | Embedded systems | API help — verify on hardware | Hardware experiment |
| 05 | Compilers and languages | Review after implementation — not before | Individual construction |
| 06 | Craftsmanship and AI | Object of study and active tool — log everything | Critical reflection |
| 07 | Advanced programming | Unreliable reviewer — disagree with it at least once | Structured failure |
| 08 | Formal methods | Fully permitted — every claim must be verified | Tool-driven proof |

**Chapters 1–2** are taught with minimal or no LLM involvement. The goal is to build correct
intuitions about representation and execution. These intuitions are the foundation everything
else rests on. A student who learns them with LLM assistance often learns a description of the
intuition rather than the intuition itself.

**Chapters 3–5** introduce LLMs as tools for exploration: generating test cases, suggesting
alternatives, explaining APIs. But the core work — forming the hypothesis, writing the parser,
deciding the design — must come from the student. The LLM assists; it does not replace.

**Chapters 6–8** use LLMs freely, but with increasing critical scrutiny. Chapter 6 studies
the LLM as an object: what does it produce, what does that reveal about its limitations?
Chapter 7 treats the LLM as an unreliable reviewer of correctness claims. Chapter 8 requires
that every LLM claim about a formal system be verified against the actual tool.

The arc is from *no tool* to *tool with critical distance*. A student who has followed
the arc can use LLMs effectively precisely because they know what to check.


---

### 4. For the Teacher

#### Role

The teacher in this framework is not primarily a lecturer. The teacher designs experiences,
surfaces questions, introduces theory at the moment it is needed, and manages the reflection
that consolidates learning. This is a different kind of work from delivering a prepared
presentation, and it is harder to plan in advance.

The practical implication: prepare less content to deliver, and more situations to create.
A broken program that the class debugs together is more valuable than a correct explanation
of the same bug. A student who predicts the wrong output and then sees the right one has
been taught something that a lecture cannot teach.

#### Session Structure

A productive session follows the cycle at the session level:

1. **Warm-up (5–10 minutes):** A short prediction task or a question from `easy/EXERCISES.md`.
   Students write their answer before any discussion. The written answer is important:
   it commits the student to a position that can be confirmed or revised.

2. **Construction (25–40 minutes):** Students work on a project stage, individually or in
   small groups. The teacher circulates, asks questions, and resists giving answers.
   The right question is usually: "What do you expect to happen?" followed by: "Run it.
   What actually happened?"

3. **Surfacing (10 minutes):** One or two students share what they found. The teacher
   draws out the conceptual point that the experience illustrates. This is the
   conceptualisation phase at the session level.

4. **Reflection (5 minutes):** Each student writes one sentence: what changed in their
   understanding today? This takes five minutes. It is not optional.

#### What to Demo, What to Leave

As a rule: demo the setup and the failure; leave the explanation and the fix to the students.

Show the program that produces the wrong output. Ask what they expected. Do not explain why
it is wrong. Give them time to form hypotheses. The explanation they produce after a genuine
attempt will stick in a way that your explanation cannot.

The exception: when students are genuinely stuck at the level of missing prerequisite knowledge
— not confused about what is happening, but lacking a tool to think with — provide the concept
directly and briefly, then return to the experience.

#### Creating Failure Conditions

In chapters 7 and 8 especially, bugs do not arise naturally in the time available.
The teacher must create them deliberately.

- For concurrency (ch07): provide a program with a race condition seeded at a known location.
  Ask students to reproduce the failure, not to find it.
- For distributed systems (ch07/Raft): provide a working Raft cluster and a test harness
  that can kill nodes. The teacher kills nodes; students observe and document.
- For formal verification (ch08): provide a program with a property claim that is slightly
  wrong. The model checker will find the counterexample. Study it together.

Failure created under controlled conditions is not cheating. It is the best way to study
phenomena that are rare in the wild.

#### The Three Levels

The `easy/`, `intermediate/`, and `advanced/` levels are not a sequence to complete in order.
They are different modes of engagement:

- `easy/EXERCISES.md` is for building vocabulary and surfacing questions. Use it for warm-ups,
  discussion prompts, or homework that prepares for the next session.
- `intermediate/PROJECTS.md` is the primary work of the chapter. Most class time should
  be spent here.
- `advanced/FOUNDATIONS.md` is for contextualisation and consolidation. It is not a prerequisite;
  it is a reward. It means more after the project than before it.


---

### 5. For the Student

#### How to Approach Exercises

The questions in `easy/EXERCISES.md` are not comprehension checks. They do not have single
correct answers that you look up and write down. Each question has a sub-prompt pointing
toward a dimension to *investigate*. The expected response is not an answer but an inquiry:
something you tried, something you found, something you are still uncertain about.

If a question can be answered in one sentence without thinking, you have answered the wrong
question. Probe further.

#### How to Approach Projects

Each project in `intermediate/PROJECTS.md` has stages. The stages matter as much as the
final result. Do not skip ahead to make the project work. Work through each stage and stop
at the end of each one to answer the questions provided. The questions are not decoration;
they are the learning.

Before starting any project: write down what you expect to happen. After finishing each stage:
compare what happened with what you expected. When there is a discrepancy, *that is the most
important moment of the project*. Do not move on without naming the discrepancy and explaining it.

Keep a log. Not a tidy document to hand in — a rough record of what you tried, what failed,
what surprised you, and what you changed as a result. The log is not assessed directly,
but it is the raw material for the reflections that are.

#### How to Approach Foundations

`advanced/FOUNDATIONS.md` can be read at any point, but it has a different quality depending
on when you read it.

Before the project: it provides orientation. You will understand some of it and find the rest
abstract. That is expected.

After the project: it provides explanation. The concepts it introduces are now answers to
questions you have actually encountered. Sentences that seemed abstract will connect directly
to something you observed.

Read it twice if you have time. The second reading is the one that consolidates.

#### How to Use LLMs

The LLM guidance differs by chapter — see the arc in section 3 above, and the chapter-level
README files for specifics. These principles apply throughout:

- **Use LLMs to generate questions, not answers.** "What edge cases might this function
  miss?" is a better prompt than "Fix my function." The first extends your thinking;
  the second replaces it.
- **Verify every significant claim.** Run the code. Check the output. Consult the specification.
  An LLM's confidence is not correlated with its accuracy.
- **Log your interactions when required.** In chapters 6–8, LLM interaction logs are part
  of the deliverable. A log of what you asked, what the LLM produced, and what you decided
  to do with the output is evidence of genuine engagement.
- **If you could not explain the LLM's solution to another person, you do not own it.**
  Do not submit, deploy, or build on code you cannot explain.


---

### 6. Assessment

This section addresses the hardest question in teaching programming with LLMs:
*how do you know whether the student learned anything?*

Traditional assessments — take-home programming tasks, written essays about code, multiple-choice
questions about syntax — are now trivially answerable with LLM assistance. A student who submits
correct code generated entirely by an LLM has demonstrated the ability to prompt an LLM.
This is a skill, but it is not the skill being assessed.

The response is not to ban LLMs from assessments. That is unenforceable and sends the wrong
message about how these tools should be used. The response is to design assessments that
reveal understanding regardless of whether the student used an LLM to help.


#### What Works

**Process artifacts**

A process artifact documents how something was done, not just what was produced. Examples:
the hypothesis log from d03/Project 1, the prediction-before-running record from d01,
the TDD order log from d03/Project 6, the LLM interaction log from d06.

Process artifacts are difficult to fake convincingly because they require a record of genuine
engagement over time. An LLM can produce a plausible-looking log, but the plausibility is
exactly the wrong kind: it will be too clean, too linear, too free of the specific
wrong turns that real learning produces. A genuine log has surprises. A generated log has
a narrative arc.

Assign process artifacts for the most important projects. Tell students in advance that the
log will be assessed. The discipline of keeping a log changes how students work, even before
it is evaluated.

**Oral examination**

Ask the student to explain their work, answer one question they have not seen before,
and modify something in their implementation in real time. Five minutes per student reveals
more than five hours of take-home work.

The oral examination is the most LLM-resistant assessment form that exists, and it is
also the most valuable: it reveals the actual state of the student's understanding with
high precision. A student who has genuinely engaged with a project can explain it.
A student who has submitted LLM-generated work cannot explain the choices that were made.

Oral examination need not be high-stakes or formal. A brief conversation during project
work time — "walk me through what you did here" — is an informal oral examination.
The habit of asking students to explain their work in conversation is itself a teaching practice.

**Prediction before observation**

Ask students to write their prediction before running the code. The written prediction
is assessed: not on whether it was correct, but on whether it reflects a genuine model
of the system. A wrong prediction with clear reasoning is more valuable than a correct
prediction with no reasoning.

This form of assessment is built into the project structure throughout the book.
Making it explicit — telling students that their prediction will be read and considered —
changes the quality of the predictions.

**Intentional failure analysis**

Provide deliberately broken code that compiles and runs but produces wrong output
in at least one case. Students must find the bug using the systematic debugging approach
from ch03 — not by inspecting the code at random or asking an LLM, but by forming and
testing hypotheses.

The deliverable is the hypothesis log: what they expected, what experiments they ran,
what each experiment revealed, and what conclusion they reached.

This assessment cannot be outsourced to an LLM, because the LLM does not have access to
the specific bug that was introduced. It may suggest plausible bugs; the student must
verify which one is actually present.

**The "one thing I got wrong" reflection**

After each significant project, students write a short piece — a paragraph is enough —
about one thing they got wrong during the project, how they found it, and what it reveals
about their prior understanding.

This reflection is almost impossible to write convincingly without having actually done
the work. It requires a specific wrong turn, a specific moment of discovery, and a
specific revision of a prior belief. LLMs can produce text that resembles this form,
but it will be generic. Genuine reflections are specific.

**Live demonstration**

Students demonstrate their project working on hardware or in a running environment.
They are then asked one question about a design decision and one question about what
they would change. These questions are not prepared in advance.

This format is especially valuable for ch04 (embedded systems) and ch07 (distributed
systems), where the system's behaviour under failure conditions is part of what is assessed.

**Peer explanation**

Students explain a concept or a piece of their own work to another student.
The listener is asked: did the explanation make sense? Where was it unclear?
The quality of the explanation is assessed, not just whether the concept is correct.

This is valuable both as assessment and as learning: the act of explaining reveals gaps
that neither running tests nor writing code will surface.


#### A Practical Assessment Scheme

The following combination works across the chapter structure of this book:

| Component | Weight | Assessed by |
|-----------|--------|-------------|
| Process log (hypothesis, TDD, or LLM interaction) | 30% | Written record |
| Live demonstration with design question | 30% | Oral, 5–10 minutes |
| Final reflection ("one thing I got wrong") | 20% | Written, 1–3 paragraphs |
| Peer explanation of one concept | 20% | Observed conversation |

None of these components can be satisfactorily completed without genuine engagement.
All of them reward understanding over performance. The combination is more resilient to
LLM-assisted shortcuts than any single component would be alone.

For self-study contexts without a teacher present, the oral and peer components can be
replaced by more demanding written reflections: a structured account of three decisions
made during the project, with alternatives considered and rejected.


#### What Not To Do

Avoid assessment forms that primarily test recall of syntax, API names, or library signatures.
These were not the most valuable things to test before LLMs; they are the least valuable
things to test now. A student who cannot recall the exact signature of a function but can
explain what it does, when to use it, and what could go wrong is more capable than one
who memorised the signature.

Avoid take-home coding tasks without a process component. A submitted program that passes
all tests says nothing about who wrote it or what understanding produced it. Add a process
log requirement, or add a demonstration component, and the assessment recovers its value.

Avoid penalising wrong predictions or documented failures. The goal is to create an
environment in which being wrong is information, not a liability. A student who documents
their wrong predictions and explains them has shown more understanding than one who only
shows the correct result.


---

### 7. The Hybrid Model

This book is designed to work in multiple configurations, and the pedagogy adapts to each.

**Classroom with a teacher**

The full cycle applies. Teacher designs experiences, facilitates inquiry, introduces theory
at the right moment, manages group and individual work, and conducts oral assessment.
The PLAN.md files in each chapter folder provide session-by-session structure.

The three modes — teacher-guided collaborative sessions, small-group studio sessions,
and individual self-study — can be mixed within a course. Early chapters (1–3) benefit
from more teacher-guided work; later chapters (5–8) benefit from more individual
and self-directed work, with the teacher as a resource rather than a guide.

**Independent self-study**

A learner without a teacher follows the self-study path described in each PLAN.md file.
The key disciplines are:

- Always write the prediction before running.
- Always keep a log, even if no one will read it.
- Read FOUNDATIONS after the project, not before.
- When stuck, use the LLM as a Socratic partner: "Ask me questions that help me figure out
  what I am missing" rather than "Tell me the answer."
- Simulate the oral examination by explaining the project to a rubber duck, a friend,
  or a recording of yourself. The act of explaining aloud reveals gaps that silent
  reading does not.

**Mixed group (classroom + independent)**

Some students will have more background than others. The three-level structure (easy,
intermediate, advanced) is designed for this: students who need more grounding use the
exercises; students who are ready for more challenge engage with the foundations.
The teacher's role is to hold the room together at the project level while allowing
individual paths at the exercise and foundations level.

**Assessment in a hybrid context**

The process log and final reflection work in all configurations. The oral examination
requires a teacher or a peer. In fully self-directed contexts, the peer explanation
component can be replaced by a written dialogue: the student writes the questions
they expect to be asked and answers them, then writes one question they could not answer.


---

### 8. What This Approach Asks of Everyone

Of the teacher: patience with open-endedness, willingness to not have all the answers
in advance, and trust that the struggle is the learning. A session that ends with more
questions than it started with has been successful.

Of the student: willingness to be wrong in public, to keep a log of mistakes, to explain
what you do not fully understand. These are uncomfortable habits to build. They are the
most important ones.

Of the LLM: it is a tool. A very capable, often surprising, frequently wrong, never
accountable tool. Use it as you would use a brilliant but unreliable colleague:
with appreciation for what it offers and scepticism about what it claims.

The goal throughout is not to produce students who have completed the projects.
It is to produce students who have been changed by working through them —
who reason differently about computation, who read code critically, who know
what they do not know, and who can learn what they need next.

That is what this book is for.
