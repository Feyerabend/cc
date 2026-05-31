## Assessment: Chapter 4 — Embedded Systems

### Overview

This chapter is uniquely verifiable: the hardware either works or it does not.
But technical correctness on hardware is not the same as understanding. A student
who copied a working state machine from an example without understanding it will
demonstrate this clearly when asked to modify it under questioning.

Assessment combines a **live hardware demonstration** (can it be shown working?)
with **design questioning** (can the student explain the choices that made it work
and respond to a modification request?).

**Timing:** Assess at the end of the chapter's central project. The live
demonstration is the primary event; oral questions follow immediately.

**Primary dimensions:** Technical correctness (35%), Process quality (25%),
Reasoning and reflection (25%), Critical tool use (15%).

---

### Oral Examination Questions

**Q1.** [During the live demo] Show me your state machine working.
Now: what happens if I press the button while the system is in state X?
- *Follow-up:* Is that the correct behaviour? How did you decide what
  the correct behaviour should be for that case?

**Q2.** Your program uses polling [or interrupts]. Why did you choose that approach?
What would you lose if you switched to the other one?
- *Follow-up:* At what point does polling become unacceptable for a
  real-time system? How would you detect that you had crossed that threshold?

**Q3.** [For 2FA project] Explain the attack that the other team attempted.
Which part of your protocol did it target? Did it succeed? Why or why not?
- *Follow-up:* What is one modification to the attack that would have
  made it more likely to succeed? What would your protocol need to change
  to prevent that?

**Q4.** Explain what debouncing does at the electrical level. Why is a
software delay the right fix for a hardware phenomenon?
- *Follow-up:* You chose a debounce threshold of [X] milliseconds. How
  did you determine that value? What would happen if it were too short?
  Too long?

**Q5.** Your embedded program uses global variables shared between the
main loop and an interrupt handler. What could go wrong? What would the
wrong result look like?
- *Follow-up:* How would you fix this? What does that fix cost in terms
  of complexity or performance?

---

### Assessment Task: State Machine Extension

*This task is done live, during or immediately after the demonstration.
Time allowed: 15–20 minutes.*

The student has demonstrated their working system (traffic light, button lock,
game, or equivalent). The assessor now requests a modification:

**For state machine projects:**
"Add a new state: an 'emergency override' mode that is triggered by
holding both A and B simultaneously for 2 seconds and causes all lights
to flash red. The override is cleared by pressing Y."

**For 2FA/security projects:**
"Add a lockout: after three failed authentication attempts within 60 seconds,
the device refuses all further attempts for 5 minutes."

**For game projects:**
"Add a 'paused' state: pressing X pauses the game (freezes all movement),
and pressing X again resumes it from exactly where it was."

Students do not need to implement the modification in full. They must:
1. Draw the new state machine on paper, showing all new states and transitions.
2. Identify which parts of their existing code would change and which would not.
3. Explain one potential problem with the modification and how they would handle it.

This task tests whether the student understands their own system well enough
to extend it under guidance — which is precisely the skill that distinguishes
genuine understanding from pattern-matching.

---

### Process Artifact Requirements

The process log for this chapter must contain:

1. The state machine diagram drawn *before* implementation, not after.
2. At least one observation of hardware behaviour that contradicted a
   software assumption (e.g. debounce discovering the button bounces,
   timing revealing a delay was needed, an ISR revealing a shared-variable issue).
3. A description of how that contradiction was resolved.

For the 2FA group project: both teams (defending and attacking) must submit
a log. The attacking team's log must document each attack attempted, what
the attack targeted, whether it succeeded, and what the protocol property
was that it was trying to bypass.

---

### Rubric Application Notes

**Technical correctness:** Does the hardware work reliably? Does it handle
edge cases (rapid button presses, power cycle during operation, conflicting
inputs)? Reliability matters more than feature completeness.

**Process quality:** Is the state machine diagram present and pre-implementation?
Does the log show at least one iteration driven by hardware feedback?

**Reasoning and reflection:** The live modification task (assessment task above)
is the primary test. Students who truly understand their state machine can sketch
the modified one in under five minutes. Students who implemented by trial and error
without understanding will struggle.

**Critical tool use:** Was LLM assistance logged? Was any LLM claim about
hardware behaviour (timing, peripheral API, interrupt behaviour) verified on
the actual hardware? Claims about hardware that were only verified in code
(not on the physical device) should be flagged.

**A note on group projects:** For the 2FA exercise, group assessment must
distinguish individual contributions. Each student should be able to answer
questions about the component they implemented and about the system as a whole.
A student who can answer questions about the whole system but not their specific
contribution raises a different concern than one who can answer about their
contribution but not the whole.
