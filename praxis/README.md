## Teaching and Learning Materials

This folder contains supplementary teaching and learning materials for the book
*From Code to Computation: A Modern Guide to Programming and Theory*.

These materials are a companion to the book, not part of it. They are designed
for both classroom use and independent study, and they follow the same chapter
structure as the main repository.

---

### Start Here

**If you are a teacher** setting up a course:
1. Read [`PEDAGOGY.md`](./PEDAGOGY.md) — the educational philosophy, the chapter arc,
   session structure, and how to assess learning in an LLM world.
2. Read [`SYLLABUS.md`](./SYLLABUS.md) — choose a course configuration (14-week semester,
   8-week intensive, or self-study) and adapt the week-by-week plan.
3. Read [`RUBRICS.md`](./RUBRICS.md) — understand the four assessment dimensions
   and how they are weighted per chapter.
4. For each chapter, read `d0x/README.md` and `d0x/PLAN.md` before planning sessions.
   Use `d0x/ASSESSMENT.md` for assessment tasks and oral questions.

**If you are a student** working through the book:
1. Read [`PEDAGOGY.md`](./PEDAGOGY.md) — sections 5 (For the student) and 6 (Assessment)
   will tell you what is expected and how to work effectively.
2. Use [`SELFASSESS.md`](./SELFASSESS.md) before and after each chapter to locate yourself
   in the material and identify gaps.
3. For each chapter, start with `d0x/README.md`, then work through the levels:
   `easy/EXERCISES.md` → `intermediate/PROJECTS.md` → `advanced/FOUNDATIONS.md`.

**If you are working alone** without a teacher:
→ See the self-study track in [`SYLLABUS.md`](./SYLLABUS.md) and the simulation of
   oral examination described in [`PEDAGOGY.md`](./PEDAGOGY.md) section 7.

---

### What Each File Is For

#### Top-level documents

| File | Purpose | Primary audience |
|------|---------|-----------------|
| [`PEDAGOGY.md`](./PEDAGOGY.md) | Educational philosophy, the learning cycle, LLM arc, session structure, assessment framework | Teachers and students |
| [`SYLLABUS.md`](./SYLLABUS.md) | Three course configurations with week-by-week plans, hardware requirements, cross-chapter threads | Teachers |
| [`RUBRICS.md`](./RUBRICS.md) | Four assessment dimensions, three levels each, chapter weightings | Teachers; students wanting to understand expectations |
| [`SELFASSESS.md`](./SELFASSESS.md) | Per-chapter "can I do X?" checklists, reflection prompts, cross-chapter habits | Students |

#### Per-chapter documents

Each `d0x/` folder contains:

| File | Purpose | When to use |
|------|---------|-------------|
| `README.md` | Chapter teaching notes: teacher focus, student tasks, concrete exercise, LLM guidelines | Before planning or starting a chapter |
| `PLAN.md` | Lesson sequences: Experience → Reflection → Conceptualisation → Extension, session-by-session | For structuring classroom sessions or weekly self-study |
| `easy/EXERCISES.md` | Questions for exploration and discussion, organised by topic | Warm-up, homework, pre-session preparation |
| `intermediate/PROJECTS.md` | Concrete buildable projects with stages, constraints, and reflection questions | Primary project work |
| `advanced/FOUNDATIONS.md` | Conceptual essays: history, theory, cross-chapter connections | After projects, for consolidation |
| `ASSESSMENT.md` | Oral questions, assessment task (broken program or transfer task), process artifact requirements | For assessment planning and student self-preparation |

---

### Chapter Overview

| Folder | Topic | Key concept | Central project |
|--------|-------|-------------|----------------|
| `d01/` | Representation | Why `0.1 + 0.2 ≠ 0.3` — and the deeper reason | Floating-point dissector + Hamming codec |
| `d02/` | Virtual machines | The VM as a contract | Stack VM built stage by stage |
| `d03/` | Debugging and testing | Hypothesis before code change | Mutation testing + TDD |
| `d04/` | Embedded systems | Hardware tells the truth | 2FA attack/defend on Pico |
| `d05/` | Compilers and languages | Code before theory, theory to explain code | Language pipeline: lexer → parser → AST → type checker |
| `d06/` | Craftsmanship and AI | Programming is decision-making under constraints | Deskilling study + logic audit |
| `d07/` | Advanced programming | Failure is the curriculum | Raft fault injection + session types |
| `d08/` | Formal methods | The gap between plausible and verified | Z3 verification + CTL model checking |

---

### The Chapter Arc

The pedagogy changes deliberately across the eight chapters.
The most important dimension is the role of LLMs:

```
Ch01  No LLM         ──────────────────────────────────────────────────►
Ch02  Explanation partner
Ch03  Hypothesis generator — verify independently
Ch04  API help — verify on hardware
Ch05  Review after implementation — not before
Ch06  Object of study — document and critique everything
Ch07  Unreliable reviewer — disagree at least once
Ch08  Fully permitted — every formal claim verified against the tool
```

This is not a progression from "LLMs bad" to "LLMs good." It is a progression
from building correct intuitions without a tool, through using a tool critically,
to studying the tool as an object of inquiry. A student who has followed the arc
can use LLMs effectively because they have a calibrated sense of what to trust.

---

### Three Levels of Material

The `easy/`, `intermediate/`, and `advanced/` levels are different modes of
engagement, not a sequence to complete in order.

**Easy / Exercises** — Build mental models. Questions are prompts for investigation,
not recall tests. Use them for warm-ups, discussion starters, or pre-project preparation.

**Intermediate / Projects** — Build things. Each project is staged; the stages matter
as much as the outcome. Keep a log. Write predictions before running. The reflection
questions are not optional.

**Advanced / Foundations** — Understand the context. These are conceptual essays
connecting the chapter to broader ideas. They mean more after the project than before.

---

### How to Use These Materials Without a Teacher

See section 7 of [`PEDAGOGY.md`](./PEDAGOGY.md) for the full self-study guidance.
The key disciplines:

- Write your prediction before running code.
- Keep a log, even if no one will read it.
- Read `FOUNDATIONS.md` after the project, not before.
- Simulate the oral examination by explaining the project aloud before reading
  the oral questions in `ASSESSMENT.md`.
- Do not move to the next chapter until you can answer the oral questions
  in `ASSESSMENT.md` without looking at your notes.

---

### Relation to the Main Repository

The projects in `d0x/intermediate/PROJECTS.md` reference code in `ch0x/addition/`.
Read those files before starting a project — the READMEs in the addition folders
often contain essential context.

The code in the main repository is not always complete or correct. This is intentional.
Part of the work is understanding what you have been given and deciding what to do next.
That process of orientation is a programming skill in itself.

---

### A Note on Difficulty

The easy/intermediate/advanced labelling reflects conceptual depth, not effort.
Some easy exercises take longer to think through carefully than some projects take to implement.
Some foundations essays are harder to engage with than some projects are to complete.

The right entry point is wherever the material connects to something you already know
and extends it. There is no wrong entry point.
