## Exercises

### Debugging

#### What Is a Bug?

1. *What is the difference between a syntax error, a runtime error, and a semantic error?*
   - Give one example of each in a language you know. Which is the hardest to find, and why?

2. *A program compiles and runs but produces the wrong answer. What kind of error is this?*
   - Why is this class of error more dangerous than a crash?

3. *What does it mean to say a bug is a "discrepancy between a mental model and reality"?*
   - Whose mental model? Of what reality? Discuss what this framing implies about how to find bugs.

4. *What is a heisenbug?*
   - Why do some bugs disappear when you try to observe them? What does this suggest about the debugging strategy you should use?

5. *Describe three common causes of off-by-one errors.*
   - Why do they occur so frequently? What habits reduce their likelihood?

6. *What is a race condition?*
   - Why is it typically impossible to reproduce a race condition reliably? How would you even begin to investigate one?


#### Debugging Strategies

1. *What is the "scientific method" applied to debugging?*
   - Formulate what a hypothesis, an experiment, and a result look like in the context of a program that produces wrong output.

2. *What is a null hypothesis in debugging?*
   - Give an example of a null hypothesis for a bug you have encountered (or can imagine). How would you test it?

3. *Why is it important to form a hypothesis before modifying code?*
   - What is the risk of changing code without first understanding why it is wrong?

4. *What is delta debugging?*
   - What problem does it solve? What does "minimising the failing input" mean, and why is it useful?

5. *What is a rubber duck? Why is explaining a problem out loud often enough to solve it?*
   - What cognitive process does this trigger?

6. *Describe the difference between a debugger and a print statement.*
   - When is each appropriate? What does a debugger let you do that print statements cannot?

7. *What is a core dump? When is it useful?*
   - How does it differ from an error message? What information can you extract from it?

8. *What does it mean to bisect a bug in version control?*
   - How does `git bisect` work? Under what conditions is it an effective strategy?


### Testing

#### Types of Testing

1. *What is the difference between a unit test and an integration test?*
   - Which is faster to run? Which gives you more confidence that the whole system works?

2. *What is a regression test?*
   - Why would you write a regression test for a bug that has already been fixed?

3. *What does it mean for a test to be deterministic?*
   - Why does non-determinism make a test unreliable? Give two sources of non-determinism in tests.

4. *What is property-based testing?*
   - How does it differ from example-based testing? What is a generator in this context?

5. *What is fuzz testing?*
   - How is it different from property-based testing? What class of bugs does it find well?

6. *What is mutation testing?*
   - What does it mean to "kill a mutant"? What does a surviving mutant tell you about your test suite?

7. *What is test coverage? What does 100% line coverage guarantee?*
   - Does 100% line coverage mean your code is correct? Give a counterexample.

8. *What is test-driven development (TDD)?*
   - What is the "red-green-refactor" cycle? What discipline does TDD impose, and what benefit does it provide?


#### Testing Philosophy

1. *Why is testing a form of knowledge about a program, not just a safety net?*
   - What does a passing test suite tell you? What does a failing test tell you?

2. *Can a program be proven correct by testing alone?*
   - What would it take to test a program completely? Why is that usually impossible?

3. *What is the relationship between a specification and a test?*
   - In what sense is a test an executable specification?

4. *Why do some argue that tests should be written before code?*
   - What does the test-first discipline force you to think about that you might otherwise skip?

5. *What is the cost of not having tests?*
   - Consider both short-term and long-term costs. When might no tests be the right decision?


### Optimisation

#### What Optimisation Is

1. *What does it mean to optimise a program?*
   - Optimise for what? List at least four different things a program might be optimised for.

2. *What is Donald Knuth's warning about optimisation?*
   - What is "premature optimisation"? When is it appropriate to start optimising?

3. *What is the difference between algorithmic complexity and constant-factor performance?*
   - Give an example where a better algorithm is more important than tuning implementation details.

4. *What is a profiler?*
   - What does it tell you that you cannot easily discover by reading the code? What does it not tell you?

5. *What is the difference between latency and throughput?*
   - Can optimising for one hurt the other? Give an example.

6. *What is a cache, and why do cache misses matter for performance?*
   - Describe why accessing elements of an array in order is typically faster than in random order.

7. *What is tail-call optimisation?*
   - What recursion pattern does it apply to? How does it change the program's memory behaviour?

8. *What is dead code elimination?*
   - Can a program have code that never runs but still affects correctness? Explain.

9. *What is loop-invariant code motion?*
   - Give a concrete example of a loop where a computation is unnecessarily repeated.
