
## Grand Plan: First Chapter with Dewey-Style Learning

First chapter we try without LLMs directly involved with the learning.

Dewey's principle:
- Students learn by doing, reflecting, and revising.
- Teachers learn by doing with them.
- The environment encourages inquiry, experimentation, and shared construction of knowledge.

The first chapter therefore becomes a cycle of exploration rather than a lecture series:
1. Experience: The teacher and pupils build something concrete immediately.
2. Inquiry: The class asks questions that arise from the experience.
3. Conceptualisation: Foundational ideas (from your three documents) are brought in only when needed.
4. Application: Pupils create variants, extensions, or their own interpretations.
5. Reflection: What did we learn? What new questions arose?


#### Core learning goals
1. Understand fundamental representations (numbers, characters, variables).
2. See programming not abstractly but as a system tied to real structure,
   functions, relations, and automata.
3. Experience that computation is built from concrete human choices.
4. Begin programming with curiosity, not formulas.


#### Pedagogical structure

Three parallel modes, selectable per context:
- Teacher-guided collaborative sessions
- Small-group studio sessions
- Individual self-study track (same content, different pacing)

You can run the class in mixed mode: teacher demonstrates, pupils explore
in groups or individually, then reconvene.



### Synopsis of the First 5–6 Lessons

Each lesson focuses on doing first, explaining second.

The recommended running order is strongly tied to [FOUNDATIONS.md](./advanced/FOUNDATIONS.md)’s
perspectives and to the first sets of exercises and projects.

#### *Lesson 1*

Title: What is computation? Let us build one together.

__Experience__

Teacher and students implement, together, a converter for a very small
part of binary numbers (just converting 0–15 from decimal to binary).

Teacher deliberately makes small "mistakes" or asks, for example:
"What happens if we try 16? What do we need?"
Students discuss bit limits.

__Inquiry__

Why does binary exist? Why 8 bits? Why does it overflow?
Students voice questions; teacher writes them down.

__Conceptualisation__

Introduce: 8-bit systems, limits, signed/unsigned, two's complement.
Use the first block of exercises in [EXERCISES.md](./easy/EXERCISES.md)
(integers) as probing questions, not homework yet.

__Application__

Small group or individual tasks:
- Convert a small set of numbers manually.
- Modify the code to allow 0–255.
- Optional stretch: implement a two's-complement negative number converter.

__Reflection__

"What surprised you about binary?"
"What rules did we implicitly rely on?"
Store questions for Lesson 2.



#### *Lesson 2*

Title: Encoding the world. Numbers, characters, symbols.

__Experience__

Teacher shows a text file opened in a hex editor or prints ASCII codes.
Pupils attempt to write their name in ASCII by hand.
Teacher writes a small program: print binary for each character.

__Inquiry__

Students realise the world is encoded. Questions arise:
Why ASCII? Why uppercase A is 65? Why do non-Latin symbols break?

__Conceptualisation__

Use the Characters/ASCII section of [EXERCISES.md](./easy/EXERCISES.md).
Introduce the idea that binary does not only encode numbers but any structure.
Important!

__Application__

Projects from [PROJECTS.md](./intermediate/PROJECTS.md) that fit here:
- Represent text using binary.
- Convert a word into ASCII and back.
- Bonus: implement a tiny "ASCII art" translator.

__Reflection__

"What limitations do you see in ASCII?"
"Who decides encodings?"
Bridge to UTF-8.



#### *Lesson 3*

Title: Variables as human tools, not just syntactic items.

__Experience__

Teacher demonstrates a simple program with a bug caused by
misunderstanding assignment or mutability.
For example, a Python list aliasing issue.

Students try the program and observe unexpected behaviour.

__Inquiry__

Why did changing b change a?
Why did reassigning x overwrite the old value?
How do different languages treat variables?

__Conceptualisation__

Use the Variables and Memory Management sections in
[EXERCISES.md](./easy/EXERCISES.md).
Explain value vs reference.
Contrast Python vs C memory models.

__Application__

Micro-tasks:
- Trace memory of three or four variable assignments.
- Create an example where immutability prevents a bug.
- If possible: demonstrate C pointer assignments.

__Reflection__

"What surprised you?"
"What does the computer assume when you assign?"
Introduce the idea that variables are abstractions we humans impose.



#### *Lesson 4*

Title: Making programs flow. Control structures and consequences.

__Experience__

Teacher presents a problem: sum all even numbers in a list.
Students propose solutions orally, then implement in groups.

Teacher also shows a recursive version.

__Inquiry__

Why use loops? When is recursion clearer?
Why are nested loops dangerous?

__Conceptualisation__

Draw from Control Structures in [EXERCISES.md](./easy/EXERCISES.md).
Contrast imperative vs functional views (align with
[FOUNDATIONS.md](./advanced/FOUNDATIONS.md) perspectives).
Introduce structural vs functional vs relational viewpoints as lenses.

__Application__

Group challenge:
- Implement the same task in three styles:
- Imperative (loop)
- Functional (map/filter/reduce)
- Structural ADT based (for example, a simple expression tree)

__Reflection__

"What does control flow hide or reveal?"
"What perspective made the task easier?"



#### *Lesson 5*

Title: Functions as units of thought.

__Experience__

Teacher and pupils write a function that is intentionally messy,
with side effects. Then they refactor into pure functions.

__Inquiry__

Why is a function that does many things hard to reason about?
What is a pure function? Why do mathematicians like them?

__Conceptualisation__

Use the Functions section of [EXERCISES.md](./easy/EXERCISES.md).
Introduce higher-order functions.
Relate to functional decomposition in [FOUNDATIONS.md](./advanced/FOUNDATIONS.md).

__Application__

Tasks:
- Write a clean functional pipeline for a small text-processing problem.
- Re-implement part of Lesson 1 (binary converter) using functional style.
- Identify where purity helps and where it does not matter.

__Reflection__

"What changed when we made functions pure?"
"How is programming like composing thoughts?"



#### *Lesson 6*

Title: A first project. Build a number system tool.

This lesson transitions from micro-exercises to the project sequence in
[PROJECTS.md](./intermediate/PROJECTS.md).

__Experience__

Teacher proposes a class-built "Number Representation Toolbox" combining:
- base conversion
- ASCII conversion
- two’s complement
- simple checksum or parity bit

Students propose the design; teacher guides only lightly.

__Inquiry__

What do we need?
What data structures?
What functions?
How to test it?

__Conceptualisation__

Integrate structural, functional, relational, and automata views.
Students begin to see computation as multi-perspective.

__Application__

Group or individual project work following [PROJECTS.md](./intermediate/PROJECTS.md)
items 1–6.

__Reflection__

"What broader understanding did this project unlock?"
"How do representation choices affect everything else?"



#### Teacher Script

Below is a linear text script you can use to run the class.
It is written so you can almost read it aloud or use it as a prep sheet.


__Teacher Script: Lesson 1 (Example)__

Start with a challenge:
"Let us write a program that converts numbers from 0 to 15 into binary.
We do not yet know how binary works, but we will discover it together."

Write a simple function on the board or in the editor.
Run it with a few cases.
Ask pupils to identify patterns.

Shift into inquiry:
"What happens when the number exceeds 15? Try 16. Try 100. What breaks?"
Let pupils experiment.
Collect observations.

Explain only now:
"This is because we implicitly wrote a 4-bit system.
A computer usually uses 8 bits for basic integers.
Let us explore that limit."

Move into conceptualisation by introducing two’s complement.
Use exercises 1–10 from [EXERCISES.md](./easy/EXERCISES.md) as question
prompts during discussion.

Application:
Students in groups modify the program to handle 8 bits.
If they finish early, assign negative numbers.

Reflection:
"What have we discovered about the limits of representation?"


The same structure can be reused for all lessons:
- Pose a concrete task.
- Let the class attempt.
- Let the confusion emerge.
- Use that confusion to introduce theory.
- Close with reflection and optional extension.



#### Self-Study Variant

A motivated learner working alone can follow an identical structure:
 1. Begin each lesson by building the concrete item first.
 2. Write down what you do not understand yet.
 3. Use FOUNDATIONS.md to supply theory filling those gaps.
 4. Use EXERCISES.md to test your understanding.
 5. Use PROJECTS.md to produce a tangible artefact.
 6. End each session with a written reflection:
"What have I learned? What still puzzles me?"



#### Optional: An Even Higher-Level Summary (usable as a syllabus)

Chapter 1: Fundamentals Through Construction
Lesson 1: Binary as lived experience
Lesson 2: Encoding the world (ASCII, UTF-8)
Lesson 3: Variables as abstractions
Lesson 4: Control structures and program shape
Lesson 5: Functions and perspectives
Lesson 6: Integrative project on number representation

Pedagogical mode: Dewey – doing first, reasoning after.
Teacher role: co-builder, co-experimenter.
Student role: active constructor of explanations.
Outputs: working code, diagrams, reflections, insights.

