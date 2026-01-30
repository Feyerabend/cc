
## Teaching / Learning

This chapter is designed primarily for independent study, with extensive and deliberate
use of LLMs as a learning tool rather than a shortcut. At this point in the book/repository,
you should be capable of formulating and carrying out your own projects, either on your own
or in collaboration with a teacher.

Before starting a project, clearly define a *goal*. The goal should not only describe what
you want to build, but also what you want to understand better. Ask yourself what concepts,
techniques, or theoretical ideas you want to explore. A good project is one where the final
result matters, but where the learning process matters even more.

Decide early what *success* looks like. What properties should your solution have? How will
you know that it is correct, elegant, efficient, or well-structured? These criteria guide
your design decisions and help you avoid drifting into unfocused experimentation.

Use *LLMs* actively and critically. Treat them as a sparring partner: ask for explanations,
alternative formulations, edge cases, and theoretical background. Let them help you generate
ideas, clarify concepts, and test your understanding. Do not let them replace your reasoning.
The goal is not to obtain answers quickly, but to deepen your comprehension and sharpen your
ability to think independently.

Try to make each project slightly *uncomfortable*. Choose problems that force you to confront
something you do not yet fully understand: recursion, abstraction, formal reasoning,
computational complexity, logic, or program correctness. Learning happens most effectively
at the *boundary of your current knowledge*.

Finally, reflect on what you learned after completing a project. What assumptions turned out
to be wrong? What concepts became clearer? What would you do differently next time? This
reflection transforms isolated exercises into long-term understanding and helps you grow
from a user of tools into a thinker in programming and theory.


### Example: From Code to Syntax as Learning by Construction

The section on syntax has been intentionally reduced in comparison to other parts of
the compilation process. This is not an omission, but a *methodological* choice. Instead
of beginning with formal theory and abstract models, the approach starts from concrete
code and moves gradually toward abstraction. Syntax is therefore introduced as something
that is discovered through practice rather than imposed through definitions.

The idea is that understanding syntax becomes stronger when it grows out of direct interaction
with real programs and real parsers. By working with code first, syntax stops being a
collection of rules and symbols and becomes an observable structure that explains why
programs behave the way they do. Theory is not removed, but postponed until the reader
has something tangible to connect it to.

For this reason, a relatively rich set of different parsers is provided early on.
They serve several purposes at once. They allow you to skim through code and get an
intuitive feel for how parsing works. They show that there is not just one correct way
to parse a language, but many, each with its own strengths, weaknesses, and underlying 
assumptions. They also function as stepping stones toward the theoretical models that
later formalise what these parsers are doing.

Learning proceeds by iteration:
* First, you read and modify existing code.
* Then, you observe patterns and recurring structures.
* After that, you introduce theoretical concepts that explain those patterns.
* Finally, you refine your understanding by relating it back to specifications and formal definitions.

This *reverses* the usual order found in textbooks, where theory comes first and code
is merely an application. Here, code is the primary source of insight, and theory is
a tool for clarification and generalisation.

Building your own parser is therefore not treated as an optional exercise, but as a
central learning activity. Writing a seemingly simple parser forces you to confront
fundamental questions:
* What is a token?
* Where does syntax end and semantics begin?
* How do ambiguity and precedence arise?
* What does it mean for a grammar to be "correct" or "complete"?

These questions are difficult to appreciate in the abstract, but become unavoidable
when you implement even a small parser by hand.

The working process can be summarised as a loop:

__1. Build code:__  Implement something concrete, even if it is naive or incomplete.

__2. Check against theory:__ Compare what you built with known parsing techniques
such as recursive descent, LL, LR, PEG, or combinator-based approaches.
Identify similarities and deviations.

__3. Check against specifications:__
Compare your parser with the formal specification of the language you are targeting.
Notice what is missing, what is oversimplified, and what is surprisingly difficult to model.

__4. Refine in steps.__
Improve structure, correctness, and expressiveness incrementally. Each refinement should
be motivated by something you observed in practice.

Over time, this creates a natural progression:
* From ad-hoc parsing logic
* To structured parsing strategies
* To formal grammars
* To precise language specifications

Syntax is then no longer a detached theoretical "thing," but a living part of the system
that evolves together with your understanding of the language and its implementation.

