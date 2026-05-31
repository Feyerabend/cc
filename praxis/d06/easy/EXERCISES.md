## Exercises

### Craftsmanship, Quality, and the Question of Judgment

#### What Is Good Code?

1. *What does it mean for code to be "readable"?*
   - Readable to whom? Under what conditions? Does readable code always mean short code?

2. *What is technical debt?*
   - How does it accumulate? Is all technical debt bad? When might you deliberately incur it?

3. *What is the difference between code that "works" and code that is "correct"?*
   - Can code work in all tested cases and still be incorrect? Give an example.

4. *What is the relationship between simplicity and correctness?*
   - Is simpler code always easier to reason about? What is accidental complexity?

5. *What does it mean to say that code has "high cohesion" and "low coupling"?*
   - Give an example of code that has low cohesion. Why is it harder to maintain?

6. *What is a code smell?*
   - Name three common code smells. Why are they called smells rather than bugs?

7. *What is refactoring? How does it differ from rewriting?*
   - What invariant does refactoring preserve? Why is a test suite necessary for safe refactoring?


#### Design and Decision-Making

1. *What does it mean to make a design decision "under uncertainty"?*
   - Give a concrete example of a design decision in software where the right answer depends
     on information you do not have yet.

2. *What is the YAGNI principle ("You Aren't Gonna Need It")?*
   - What does it caution against? When is it appropriate to build for anticipated future needs?

3. *What is the DRY principle ("Don't Repeat Yourself")?*
   - Is all code duplication bad? When might duplication be preferable to abstraction?

4. *What is the principle of least surprise?*
   - Whose surprise are we worried about? Give an example of an API that violates this principle.

5. *What is a design pattern? Give two examples.*
   - Is a design pattern a solution or a template? What is the risk of over-applying patterns?

6. *What is the difference between interface and implementation in software design?*
   - Why is it valuable to program to an interface rather than to a specific implementation?

7. *What is the cost of "over-engineering"? Give an example.*
   - How do you know, in the moment, whether you are over-engineering or being appropriately prudent?


#### Programming Methodology

1. *What is agile software development? What is its central claim about planning?*
   - What does agile say about specifications written before any code is written?

2. *What is continuous integration? What problem does it solve?*
   - How does it change the relationship between individual programmers and the shared codebase?

3. *What is a code review? What kinds of problems does it reliably find? What does it not find well?*
   - When is a code review a waste of time? When is it essential?

4. *What is the relationship between documentation and code?*
   - Who is documentation for? Can code be self-documenting? When is a comment necessary?

5. *What does it mean to say that a programming practice has "emerged from the community"?*
   - Give an example of a widely adopted practice. Was it always considered good? Has it changed?

6. *What is the open-source model of software development? What does it assume about motivation?*
   - What problems of the open-source model have become apparent over the last decade?


#### Large Language Models and Programming

1. *What is a Large Language Model? What does it predict?*
   - It predicts the next token. Why does this make LLMs useful for code generation?
     Why does it also make them unreliable?

2. *What is "hallucination" in the context of LLMs?*
   - Give an example of a plausible-sounding output that is factually wrong.
     Why is this dangerous in a code generation context?

3. *What does it mean for an LLM to "understand" code?*
   - Does the LLM have a model of what the program does, or does it have a model of what
     code looks like? Is there a meaningful difference?

4. *What is "deskilling"? How might the use of LLMs for code generation cause it?*
   - What skills might a programmer lose if they routinely accept generated code without
     understanding it?

5. *What kinds of programming tasks are LLMs most useful for? Least useful for?*
   - Think about the difference between code that is mostly pattern and code that requires
     genuine problem-specific reasoning.

6. *What is the programmer's responsibility when they use LLM-generated code?*
   - Who is accountable if LLM-generated code contains a security vulnerability?
     Does it matter whether the programmer understood the code?

7. *How should the existence of LLMs change how programming is taught?*
   - What skills become more important? What becomes less important? What stays the same?
