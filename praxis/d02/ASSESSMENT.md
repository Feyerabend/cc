## Assessment: Chapter 2 — Virtual Machines

### Overview

This chapter is about execution models: what actually happens when a program runs.
The risk is that students implement a working VM by following examples without
understanding the mechanism — the VM passes the projects but the student cannot
explain why a CALL instruction needs to save the return address.

Assessment focuses on **execution tracing** (can the student run a program
mentally, step by step?) and **design reasoning** (can the student explain
*why* the VM is built the way it is, not just *how*?).

**Timing:** Assess after completing at least Projects 1–4 from PROJECTS.md.

**Primary dimensions:** Technical correctness (40%), Process quality (30%),
Reasoning and reflection (30%).

---

### Oral Examination Questions

**Q1.** Here is a bytecode program for your VM:
`PUSH 3 / PUSH 4 / ADD / PUSH 2 / MUL / PRINT / HALT`
Trace the stack state after each instruction. What does the program compute?
- *Follow-up:* If I remove the HALT instruction, what happens in your implementation?

**Q2.** Your VM supports function calls. What information must be saved when
`CALL` executes? Where is it saved? When is it restored?
- *Follow-up:* What happens if a recursive function never reaches its base case
  in your VM? Show me in terms of the stack.

**Q3.** You implemented a register VM as well as a stack VM. For the same program,
which produced more instructions? Which was easier to write bytecode for by hand?
- *Follow-up:* Which would be easier to optimise? Why?

**Q4.** Explain the difference between the Harvard and von Neumann architectures
in terms of your VM. What attack is possible in a von Neumann VM that is not
possible in a Harvard one?
- *Follow-up:* In your Harvard VM implementation, what specifically prevents
  a program from writing to the instruction array?

**Q5.** I have a program that allocates a lot of small objects quickly and frees
them all at once at the end. Which memory allocator should I use, and why?
- *Follow-up:* What would happen if I used that allocator for objects with different
  lifetimes, where some live much longer than others?

---

### Assessment Task: The Broken VM

*Time allowed: 30–45 minutes. No LLM assistance.*

The following stack VM implementation has a bug. The bug is not a syntax error.
The VM runs without crashing on many programs. On some programs it produces
wrong results.

```python
class VM:
    def __init__(self, code):
        self.code = code
        self.stack = []
        self.pc = 0

    def run(self):
        while self.pc < len(self.code):
            op = self.code[self.pc]
            self.pc += 1
            if op == 'PUSH':
                self.stack.append(self.code[self.pc])
                self.pc += 1
            elif op == 'ADD':
                a = self.stack.pop()
                b = self.stack.pop()
                self.stack.append(a + b)
            elif op == 'SUB':
                a = self.stack.pop()
                b = self.stack.pop()
                self.stack.append(a - b)
            elif op == 'PRINT':
                print(self.stack[-1])
            elif op == 'HALT':
                return

program = ['PUSH', 5, 'PUSH', 3, 'SUB', 'PRINT', 'HALT']
VM(program).run()   # Should print 2
```

**Part A:** Run the program. Is the output correct?

**Part B:** Construct a second program using `SUB` where the output is *wrong*.
Write it down before running it. Run it. Is your prediction confirmed?

**Part C:** Explain why the bug occurs. What property of subtraction (and division,
if implemented) does the implementation violate?

**Part D:** Fix the bug with the minimal change. Write a test program that
distinguishes the buggy version from the fixed version.

---

### Process Artifact Requirements

The execution trace log for this chapter must contain:
- A hand-written trace of at least one bytecode program (at least 8 instructions),
  showing the stack state after every instruction.
- The trace must be written *before* running the program, not after.
- A note comparing the hand-trace to the actual VM output.

The purpose of the hand-trace is to force engagement with the execution model
at the instruction level. A trace written after running the program does not serve
this purpose and should be flagged.

---

### Rubric Application Notes

**Technical correctness:** Does the VM correctly execute arithmetic, variables,
control flow, and function calls? Does it handle stack underflow gracefully?

**Process quality:** Is the hand-trace present and pre-execution? Is there
evidence that the student worked through each project stage rather than
jumping to the final implementation?

**Reasoning and reflection:** The oral Q1 (bytecode trace) is the clearest
test. A student who can trace bytecode mentally, with correct stack states,
has understood the execution model. A student who needs to run the code to
check the trace has not.

**Common failure mode:** Students often implement function calls by adding
a `CALL` instruction that jumps correctly but do not implement the return
address save/restore. The VM appears to work for non-recursive programs and
fails mysteriously for recursive ones. Q2 probes for this specifically.
