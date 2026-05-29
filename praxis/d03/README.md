
## Teaching / Learning

This chapter introduces the core practices of debugging, testing, optimisation, error handling,
and the use of development tools. These topics invite both *individual* reflection and *collaborative*
work, since understanding code quality benefits from multiple perspectives. In a future where
large language models may reliably generate code, the act of checking and validating that code
may become even more important. Code that appears correct can still contain hidden faults, and
such faults may remain unnoticed for a long time after the code has been written. Subtle errors
are often the most difficult to detect, and they can resist careful investigation unless systematic
techniques are applied. Testing can come in many forms, be done in many ways. These topics and
many more are explored in the chapter.

Ideas on projects can be found in [PLAN.md](./PLAN.md) and [PLAN2.md](PLAN2.md).

You should now also be able to make your own planning, with the help of LLMs.

*Tools are part of the system, not accessories.*

Teacher focus:
- Compilers, debuggers, build tools
- Observability over convenience

Student tasks:
- Use debugger before printing
- Capture traces and explain them


### Concrete exercise

Provide a broken program that:
- compiles
- runs
- produces wrong output

Students must:
- Debug without changing code
- Produce a causal explanation

LLM use:
- Allowed for hypotheses
- Disallowed for direct fixes


### Example: Hypothesis and Debugging

Debugging is often taught as a search for mistakes, but this framing does not scale.
When programs grow, failures are rarely obvious errors; they are mismatches between
assumptions and reality. A more accurate way to teach debugging is as hypothesis testing.

At the start of a debugging session, nothing is known. The student has an observation:
the program behaves differently from what was expected. The first task is *not* to change
the code, but to form a *hypothesis* about why the behaviour occurs. This hypothesis
should be falsifiable. For example: "This variable has the wrong value at this point,"
or "This function is not being called."

Students rarely do this naturally. They tend to make changes immediately, guided by intuition.
This leads to random walks rather than understanding. Teaching debugging as hypothesis
testing forces students to slow down and reason.

A powerful teaching tool here is the *null hypothesis*. The null hypothesis states that
the suspected cause is not responsible for the observed behaviour. For example:
"The compiler is not miscompiling this code," or "The debugger is showing the correct value."
Students are encouraged to assume the null hypothesis is true unless evidence proves
otherwise. This prevents premature blame of tools and encourages disciplined
investigation.

A concrete classroom exercise begins with a small program that produces incorrect output
only under certain conditions, such as in a release build or when run with specific input.
The teacher asks students to write down two hypotheses before touching the code. One must
be a null hypothesis. For example: "The logic in function X is incorrect," and
"The build configuration is correct and not influencing behaviour."

Students then design experiments to test these hypotheses. They may add logging, inspect
intermediate values, or change a single build flag. The key rule is that each experiment
must test exactly one hypothesis. If the result contradicts the hypothesis, it is rejected.
If it does not, the hypothesis remains viable but not proven.

The teacher models this process explicitly. Instead of saying "let's check this variable,"
the teacher says "our hypothesis is that this value changes here; this print statement tests that."
Language matters. It trains students to associate debugging actions with reasoning, not instinct.

An important moment comes when the null hypothesis is rejected. For example, a change in
compiler optimisation alters behaviour. This teaches students that tools and environments
are not neutral, but it also teaches restraint: they are blamed only when evidence supports it.

The exercise ends not when the bug is fixed, but when the *causal chain* is understood.
Students must explain which assumption was wrong, how the experiment disproved it, and
what new hypothesis replaced it. Fixing the code is secondary to explaining the failure.

Teaching debugging this way turns into a lesson about *scientific reasoning*. Students
learn that debugging is not about cleverness or experience alone, but about forming models,
testing them, and revising them based on *evidence*. This habit generalises to larger systems,
unfamiliar tools, and even to evaluating confident explanations from automated systems.



