## Syllabus: Course Configurations

This document provides three ways to organise the book's eight chapters into
a course. They differ in pace, depth, and the assumed availability of a teacher.
All three share the same underlying structure: experience before theory,
process alongside product, and increasing LLM engagement as the course progresses.

Regardless of configuration, teachers should read `PEDAGOGY.md` and `RUBRICS.md`
before planning sessions. The chapter-level `PLAN.md` files provide session-by-session
detail. The `d0x/ASSESSMENT.md` files provide specific assessment tasks.

---

### Prerequisites

Students should arrive with:
- Some experience writing programs in at least one language (Python is assumed
  throughout; C is used in several additions).
- Comfort with the command line: navigating directories, running programs,
  reading error messages.
- No assumed background in computer science theory, formal methods, or hardware.

The book builds theory from practice. Prior theoretical knowledge is not required
and is occasionally an obstacle: students who "already know" something are sometimes
less willing to form and test hypotheses than students who do not.

---

### Configuration 1: Full Semester (14 weeks)

Intended for a university course meeting two or three times per week.
Each chapter receives one to two weeks. Chapters 4 and 7 receive extra time
because they involve hardware setup (ch04) and genuinely difficult concepts (ch07).
Chapter 8 receives extra time because it is the most abstract and benefits from
slow, cumulative engagement.

#### Week-by-Week Plan

| Week | Content | Sessions | Assessment due |
|------|---------|----------|---------------|
| 1 | Setup + ch01 intro: binary, prediction tasks | 2–3 | Prediction log (formative) |
| 2 | Ch01: representations, Hamming, floating point | 2–3 | Ch01 project + oral |
| 3 | Ch02: stack VM, bytecode, execution trace | 2–3 | Execution trace (formative) |
| 4 | Ch02: register VM, memory models, Harvard | 2–3 | Ch02 project + oral |
| 5 | Ch03: debugging methodology, hypothesis log | 2–3 | Hypothesis log (formative) |
| 6 | Ch03: testing, mutation testing, TDD | 2–3 | Ch03 project + oral |
| 7 | Ch04: Pico setup, GPIO, state machines | 2–3 | State machine design (formative) |
| 8 | Ch04: protocols, 2FA project (group) | 2–3 | Ch04 project + demo |
| 9 | Ch05: lexing, parsing, AST | 2–3 | Parser draft (formative) |
| 10 | Ch05: evaluator, type checker, full pipeline | 2–3 | Ch05 project + oral |
| 11 | Ch06: craftsmanship, deskilling study | 2–3 | Deskilling reflection (formative) |
| 12 | Ch06: logic audit, GPT-2 study, design defence | 2–3 | Ch06 project + oral |
| 13 | Ch07: concurrency, race conditions, Raft | 2–3 | Failure report (formative) |
| 14 | Ch07 + Ch08: advanced types, Z3, formal proof | 2–3 | Final project + oral |

#### Assessment Schedule

| Assessment | Week | Weight |
|-----------|------|--------|
| Ch01 project + oral | 2 | 8% |
| Ch02 project + oral | 4 | 8% |
| Ch03 project + oral | 6 | 12% |
| Ch04 project + demo | 8 | 12% |
| Ch05 project + oral | 10 | 12% |
| Ch06 project + oral | 12 | 12% |
| Ch07 failure report + oral | 13 | 16% |
| Final project (ch07 or ch08) + oral | 14 | 20% |

#### Notes for 14-Week Format

- Chapters 1 and 2 are foundational. Do not compress them to make time for
  the later chapters. Students who do not build correct intuitions about
  representation and execution in weeks 1–4 struggle increasingly from ch05 onward.

- Chapter 4 requires hardware. Order Picos and Display Packs before week 7.
  If hardware is unavailable, the CEP and TDOS projects can be run in simulation,
  but the hardware experience is valuable and should not be skipped if avoidable.

- Chapter 6 is not a rest week. Students find it unfamiliar because it asks for
  critical thinking and written argument rather than code. Allocate session time
  for discussion and oral defence, not just project work.

- Chapters 7 and 8 can be partially combined at the end of a tight semester.
  If time is short, prioritise ch07 (Raft fault injection, session types) and
  treat ch08 as an extended project for interested students.

#### LLM Policy by Phase

| Weeks | LLM policy |
|-------|-----------|
| 1–4 | No LLM for implementation or exercises. LLM may be used to explain error messages after the student has attempted to understand them independently. |
| 5–8 | LLM permitted for exploring APIs and generating test inputs. All significant uses logged. Not permitted for generating the core implementation. |
| 9–12 | LLM permitted freely. Log required. At least one claim per project corrected with evidence. |
| 13–14 | LLM fully permitted. Every formal claim verified against the tool. Log is assessed. |

---

### Configuration 2: Eight-Week Intensive

Intended for a bootcamp, summer school, or concentrated module. One chapter per week.
Pace is high; coverage is maintained by focusing on the central project in each chapter
and abbreviating the exercise and foundations components.

#### Weekly Plan

| Week | Chapter | Primary activity | Assessment |
|------|---------|-----------------|-----------|
| 1 | Ch01 Representation | Floating-point dissector + Hamming lab | Prediction log + 10-min oral |
| 2 | Ch02 Virtual machines | Build stack VM stages 1–4 | Execution trace + 10-min oral |
| 3 | Ch03 Debugging and testing | Hypothesis lab + mutation testing | Hypothesis log + 10-min oral |
| 4 | Ch04 Embedded | 2FA or ECS game on Pico | Live hardware demo + design question |
| 5 | Ch05 Compilers | Language pipeline stages 1–4 | Parser demo + oral on type checking |
| 6 | Ch06 Craftsmanship | Deskilling study + logic audit | Written reflection + oral defence |
| 7 | Ch07 Advanced | Raft fault injection | Failure report + oral |
| 8 | Ch08 Formal methods | Z3 puzzle progression to verification | Z3 results + Curry-Howard oral |

#### Notes for 8-Week Format

- Each week requires approximately 20–25 hours of student engagement (contact
  hours plus independent work). This is intensive but achievable.

- Skip `easy/EXERCISES.md` as homework. Use exercises only as warm-up prompts
  at the start of sessions. Students at this pace need project time, not exercises.

- Read `advanced/FOUNDATIONS.md` at the end of each week, not before.
  In an intensive format the foundations serve as a weekly consolidation reading.

- Oral examinations are short (10 minutes) but essential. They are the primary
  check that the pace has not outrun the understanding.

- Chapter 4 hardware setup should be done in week 1 or 2 so that hardware is
  ready by week 4. If setting up takes a full session, plan for it explicitly.

- In an 8-week format, chapter 8 is the hardest to do justice to. The Z3
  puzzle progression (Project 1 in `d08/intermediate/PROJECTS.md`) is self-contained
  and produces visible results. Prioritise it over the proof development project
  unless the student group has a formal methods background.

---

### Configuration 3: Self-Study Track

Intended for an individual working alone, without a teacher. There are no fixed
calendar weeks — each unit is time-boxed by the material, not by a schedule.

The self-study track places more responsibility on the student for maintaining
the disciplines that a teacher would otherwise enforce: keeping a log,
writing predictions, re-reading the foundations, and simulating the oral examination.

#### Unit Plan

Each unit corresponds to one chapter. Within a unit, the order is:

1. **Read** the chapter's `README.md` (teaching/learning notes) to orient yourself.
2. **Warm-up:** Work through 5–8 questions from `easy/EXERCISES.md` relevant to
   the first section. Write your answers before looking anything up.
3. **Build:** Work through the primary project from `intermediate/PROJECTS.md`,
   stage by stage. Keep a log. Write predictions before running.
4. **Consolidate:** Read `advanced/FOUNDATIONS.md`. Note which passages connect
   to something you observed during the project.
5. **Assess yourself:** Work through the `ASSESSMENT.md` for this chapter.
   Answer the oral examination questions in writing. For the broken program task,
   attempt it before reading the task description a second time.
6. **Reflect:** Write the "one thing I got wrong" reflection. Write one sentence
   about what question the chapter has opened that you did not have before.

#### Simulating the Oral Examination

Without a teacher, the oral examination must be self-administered.

Method: after completing a project, close the code and explain the project
out loud to an imaginary questioner. Record yourself if possible — the act of
hearing your own explanation is more revealing than reading it.

Then: open the `ASSESSMENT.md` oral questions for this chapter. Write answers
to each one before checking them against the project materials. Note the questions
you could not answer. Do not move to the next chapter until you can answer them.

#### Pacing Guidance

A realistic estimate for a student with some programming background:

| Chapter | Estimated time |
|---------|---------------|
| Ch01 | 8–12 hours |
| Ch02 | 10–14 hours |
| Ch03 | 10–14 hours |
| Ch04 | 12–16 hours (more if hardware is new) |
| Ch05 | 14–18 hours |
| Ch06 | 8–12 hours (different kind of work) |
| Ch07 | 16–20 hours |
| Ch08 | 12–16 hours |

These are approximate. Students with relevant background will move faster in
some chapters; students encountering unfamiliar concepts will move slower.
The right pace is one where the "one thing I got wrong" reflection is specific
and honest. If nothing went wrong, the pace was too fast.

---

### Cross-Chapter Threads

Several conceptual threads run across multiple chapters. Teachers planning
the full semester may want to make these explicit. Students doing self-study
should look for them.

| Thread | Chapters |
|--------|---------|
| Representation → verification | Ch01 (bit patterns) → Ch02 (VM memory model) → Ch08 (Hamming proof in Z3) |
| VM → language → formal semantics | Ch02 (stack VM) → Ch05 (SECD machine) → Ch08 (operational semantics) |
| Testing → formal methods | Ch03 (mutation testing) → Ch06 (logic audit) → Ch08 (Z3, model checking) |
| Embedded → distributed | Ch04 (Pico concurrency, 2FA) → Ch07 (Raft consensus) → Ch08 (CTL model checking) |
| Type systems | Ch05 (simple types, affine) → Ch07 (linear, session) → Ch08 (dependent, Curry-Howard) |
| LLM as tool → LLM as subject | Ch03–05 (use with logging) → Ch06 (study its failures) → Ch08 (verify its claims formally) |

A teacher running the full semester might briefly name the thread at the start
of each chapter: "This week we return to the question of correctness we first
encountered in ch03. This time the tool is different."

---

### Hardware and Software Requirements

#### Software (all chapters)

- Python 3.10+ with standard library
- C compiler (gcc or clang)
- Git
- A text editor or IDE with syntax highlighting

#### Additional by chapter

| Chapter | Additional requirements |
|---------|------------------------|
| Ch02 | None beyond above |
| Ch03 | Python `pytest` or equivalent; `make` |
| Ch04 | MicroPython on Raspberry Pi Pico; Pimoroni Display Pack 2.0; `mpremote` or Thonny |
| Ch05 | None beyond above |
| Ch06 | Python dependencies in `ch06/addition/gpt2/requirements.txt`; Alloy Analyzer (for Project 4) |
| Ch07 | Python `asyncio`; optional: Lean or Agda for session types project |
| Ch08 | Z3 Python bindings (`pip install z3-solver`); Lean 4 or Agda (for proof project) |

#### Ordering hardware

If running the 14-week semester format: order Pico hardware by week 2 at the latest.
If running the 8-week intensive: order before the course starts.

The Pimoroni Display Pack 2.0 is the primary display peripheral used in ch04.
If unavailable, the display-dependent examples can be replaced with serial output,
but the visual feedback of the Display Pack is pedagogically significant for the
state machine and 2FA projects.
