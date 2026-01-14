
## Null and Alternative Hypotheses

Think of debugging as a scientific experiment.
Your *program is the system*, the *bug is the phenomenon*, and your *hypotheses explain why it happens*.

In statistics:
- *Null hypothesis (H₀)*: "Nothing special is wrong; behavior is as expected."
- *Alternative hypothesis (H₁)*: "Something specific is wrong; this explains the behavior."

In debugging:
- *H₀*: "This part of the code is correct."
- *H₁*: "This part of the code is faulty in this specific way."

You never prove H₁ directly. You try to *reject* H₀ using observations and tests.



### The Scientific Method in Debugging

#### Step 1: Observe and Describe the Failure

Start with facts, not theories.

*Observation must be:*
- Objective and reproducible
- Free from interpretation
- Precisely documented

Write it neutrally:

> "When input X occurs, the program shows behavior Y."

This is your experimental data.



#### Step 2: Define the Global Null Hypothesis

This is your baseline assumption:

*H₀*: The program logic is correct; the failure is caused by invalid input, environment, or misuse.

This protects you from jumping to conclusions and forces rigorous thinking.



#### Step 3: Form the First Alternative Hypothesis

Pick one precise, testable explanation:

*H₁*: The function does not handle [specific edge case].

This must be:
- *Specific* (not "something is broken")
- *Testable* (can design an experiment)
- *Falsifiable* (can be proven wrong)

* *Bad hypothesis*: "Something is wrong somewhere."  
* *Good hypothesis*: "Line 12 performs division without checking for zero."



#### Step 4: Design a Test to Try to Reject H₀

Create a minimal, controlled experiment.

The test should:
- Isolate one variable
- Produce clear pass/fail results
- Be repeatable

This is exactly statistical reasoning: you try to show that H₀ is incompatible with observed data.



#### Step 5: Update Your Belief

Based on test results:

- *If evidence contradicts H₀* -> Reject H₀, provisionally accept H₁
- *If evidence contradicts H₁* -> Reject H₁, maintain H₀
- *If inconclusive* -> Refine the test

You now accept H₁ not as absolute truth, but as the *best explanation so far*.



#### Step 6: Refine the Hypothesis

Go deeper with narrower scope:

*New H₁*: The code lacks an explicit boundary check before the operation.

Test the fix. If the bug disappears, your hypothesis survives another round of falsification.



#### Step 7: Loop the Process (Iterative Refinement)

Every debugging cycle follows this pattern:

1. Observe failure
2. Assume correctness (H₀)
3. Propose specific fault (H₁)
4. Design test
5. Reject either H₀ or H₁
6. Refine hypothesis
7. Repeat

This is *inductive scientific reasoning* applied to software.



### Example 1: Simple Division Bug (Python)

#### Observation

```python
print(divide(10, 0))   ## crashes with ZeroDivisionError
```

*Fact*: Program crashes when divisor is zero.

#### Hypotheses

*H₀*: Function behaves correctly; caller must validate inputs.  
*H₁*: Function must protect against zero divisor internally.

#### Test Design

```python
def test_hypothesis():
    try:
        result = divide(5, 0)
        print("No error raised")
    except ZeroDivisionError:
        print("Division by zero not handled")
```

#### Result

```
Division by zero not handled
```

*Decision*: Reject H₀. The function does not handle the edge case.

#### Fix and Verify

```python
def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
```

Test again. Bug eliminated -> hypothesis survives.



### Example 2: Complex State Management Bug (Python)

#### Observation

```python
class BankAccount:
    def __init__(self, balance=0):
        self.balance = balance
        self.transactions = []
    
    def withdraw(self, amount):
        self.balance -= amount
        self.transactions.append(('withdraw', amount))
        return self.balance

## Bug appears:
account = BankAccount(100)
account.withdraw(50)
account.withdraw(75)  ## Should fail, but balance goes negative
print(account.balance)  ## -25
```

*Fact*: Withdrawal succeeds even when balance is insufficient, resulting in negative balance.



#### Initial Hypotheses

*H₀*: The withdrawal logic is correct; the issue is with how we're calling it.  
*H₁*: The `withdraw` method lacks insufficient-funds validation.



#### First Test

```python
def test_hypothesis_1():
    account = BankAccount(100)
    account.withdraw(150)  ## Try to overdraw immediately
    print(f"Balance: {account.balance}")
    print(f"Expected: Should reject or balance = 100")
```

*Result*: Balance becomes -50.

*Decision*: Reject H₀. The method allows overdrafts unconditionally.



#### Refined Hypothesis

*New H₁*: The method needs to check `if amount > self.balance` before processing.

*Test the fix*:

```python
def withdraw(self, amount):
    if amount > self.balance:
        raise ValueError("Insufficient funds")
    self.balance -= amount
    self.transactions.append(('withdraw', amount))
    return self.balance
```

*Retest*:

```python
account = BankAccount(100)
account.withdraw(50)   ## Works
account.withdraw(75)   ## Raises ValueError
```

*Result*: Exception raised as expected.

*Decision*: H₁ survives this test.



#### But Wait--A New Bug Appears

After deploying the fix, you observe:

```python
account = BankAccount(100)
account.withdraw(100)        # Works
print(account.balance)       #  0
account.withdraw(0)          # Should this work?
print(account.balance)       # Still 0, but transaction logged
print(account.transactions)  # [('withdraw', 100), ('withdraw', 0)]
```

*New Observation*: Zero-amount withdrawals are accepted and logged.



#### Second Hypothesis Cycle

*H₀*: Zero withdrawals are valid business logic.  
*H₁*: Zero-amount transactions should be rejected as meaningless.

*Test*:

```python
def test_zero_withdrawal():
    account = BankAccount(100)
    try:
        account.withdraw(0)
        print("Zero withdrawal accepted")
    except ValueError as e:
        print(f"Zero withdrawal rejected: {e}")
```

*Decision*: This requires domain knowledge. If zero withdrawals are invalid, refine:

```python
def withdraw(self, amount):
    if amount <= 0:
        raise ValueError("Withdrawal amount must be positive")
    if amount > self.balance:
        raise ValueError("Insufficient funds")
    self.balance -= amount
    self.transactions.append(('withdraw', amount))
    return self.balance
```

*Retest all scenarios*:
- Negative amount -> rejected
- Zero amount -> rejected
- Valid amount -> succeeds
- Overdraft -> rejected

Each test is an attempt to *falsify* the current hypothesis.



### How Reasoning Moves Through the Process

| Step | Logical Action | Statistical Analogy |
|------|----------------|---------------------|
| *Observation* | Collect data | Sample measurement |
| *H₀* | Assume correctness | Null hypothesis |
| *H₁* | Propose fault | Alternative hypothesis |
| *Test* | Run experiment | Statistical test |
| *Result* | Accept or reject | Hypothesis decision |
| *Refinement* | Narrow scope | Model improvement |



### Important Debugging Principles

#### You Never Prove Code Is Correct

You only *fail to disprove it*.

Just like science:

> "Not rejected yet" is the strongest possible statement.

#### Each Fix Creates New Test Surface

The bank account example shows this clearly:
1. First bug: no balance check
2. Fix introduced new question: what about zero amounts?
3. Each fix must be tested against new edge cases

#### Hypothesis Quality Matters

*Weak hypothesis*: "The account logic is broken."  
*Strong hypothesis*: "The withdraw method processes transactions before validating balance constraints."

The strong hypothesis tells you *exactly* where to look and what to test.



### Mental Model

*Debugging is not fixing code.*  

*Debugging is running a sequence of falsification experiments on your own beliefs about the code.*

That is exactly null-hypothesis reasoning applied to software. Each test either:
- Eliminates a possibility (rejects H₀ or H₁)
- Increases confidence in current understanding (fails to reject)
- Reveals new questions (triggers new hypothesis cycle)

You move forward by systematically eliminating what
*cannot* be true until only valid explanations remain.






---




### Popper's Falsificationism: The Philosophical Foundation

This entire debugging methodology has many ties to *Karl Popper's philosophy of science*.

* Popper, K. (1959). *The logic of scientific discovery*. London: Hutchinson.
* Popper, K. (1972). Conjectures and refutations: the growth of scientific knowledge. (4. ed., (rev.)). London: Routledge & Kegan Paul.
* Popper, K. & Schilpp, P.A. (1974). The philosophy of Karl Popper. (1. ed.) La Salle, Ill.: Open court.



#### The Core Insight

Popper argued that *scientific knowledge advances through falsification, not verification*.

Key principles:

1. *No amount of confirming evidence proves a theory true*  
   - You can test your code 1,000 times successfully, but you haven't proven it correct
   - The 1,001st test might reveal a bug

2. *A single counterexample can prove a theory false*  
   - One failing test conclusively shows something is wrong
   - This asymmetry is fundamental to the scientific method

3. *Good theories are highly falsifiable*  
   - "Something is broken somewhere" cannot be tested -> bad hypothesis
   - "Line 47 divides without checking for zero" can be tested -> good hypothesis

4. *Science progresses by bold conjectures and attempted refutations*  
   - Propose specific explanations (conjectures)
   - Design harsh tests that could disprove them (refutations)
   - Retain only theories that survive



#### Debugging as Popperian Science

Every debugging session as a *miniature scientific research program*:

| Popper's Philosophy | Debugging Practice |
|---------------------|--------------------|
| Scientific theories must be falsifiable | Hypotheses must predict specific, testable behavior |
| We can never verify, only falsify | Passing tests increase confidence but don't prove correctness |
| Knowledge grows by eliminating error | Each rejected hypothesis narrows the search space |
| Theories survive by resisting falsification | Code gains credibility by surviving adversarial tests |
| Bold conjectures advance science faster | Specific hypotheses lead to faster debugging than vague ones |



#### The Demarcation Problem in Debugging

Popper used falsifiability to distinguish science from non-science. In debugging:

*Non-falsifiable (pseudoscience analogue)*:
- "The code might have issues"
- "Users are confused"
- "Something weird happens sometimes"

*Falsifiable (scientific)*:
- "The function crashes when the input list is empty"
- "The balance becomes negative when withdrawal exceeds available funds"
- "The loop terminates one iteration early when array length is odd"

Only falsifiable hypotheses can be tested. This is why *precision matters* in debugging.



#### Why Popper Matters for Programmers

Popper teaches us that:

1. *Certainty is impossible*  
   We can never prove our code is bug-free, only that we haven't found bugs yet

2. *Aggressive testing is epistemic humility*  
   The more harshly we test, the more we respect the limits of our knowledge

3. *Failure is information*  
   A failing test doesn't mean we failed--it means we successfully eliminated a false belief

4. *Surviving criticism makes theories stronger*  
   Code that survives edge cases, stress tests, and adversarial inputs is more trustworthy

5. *Vagueness protects bad ideas*  
   If you can't state precisely what should happen, you can't test whether it does



#### The Debugging Attitude

Popper's philosophy suggests a specific *epistemic stance* toward your own code:

- *Presume you are wrong* until evidence suggests otherwise
- *Seek disconfirming evidence* more eagerly than confirming evidence  
- *Welcome failed tests* as opportunities to learn
- *Distrust intuition* and demand experimental validation
- *Iterate relentlessly*, knowing each cycle brings you closer to truth

This is why the methodology begins with *H₀: "The code is correct"* and
then tries to *break* that assumption. You're doing science, not defending a belief.



#### The Infinite Regress Problem

Popper recognised a deep issue: even our tests rest on assumptions that could be wrong.

In debugging:
- Your test might have a bug
- Your understanding of correct behavior might be flawed  
- Your test environment might not match production

This means:
- *Always question your tests*, especially when results seem strange
- *Test your tests* with known-good and known-bad cases
- *Validate assumptions* about what "correct" means

There's no absolute foundation. But rigorous falsification gets us progressively closer to truth.



#### Conclusion: Debugging as Applied Epistemology

Popper showed that *all empirical knowledge is provisional and corrigible*--always
subject to revision in light of new evidence.

Debugging embodies this perfectly:
- Every fix is a conjecture
- Every test is an attempted refutation  
- Every surviving hypothesis is tentatively accepted
- The process never ends

You're not just fixing code. You're *practicing the method that all empirical
science is built on*: systematic doubt, bold hypotheses, and relentless testing.

That's why good debuggers think like scientists--because debugging *is* science.





### 1. The Asymmetry of Falsification vs. Verification

*Traditional hypothesis testing*: Seeks to establish confidence in a hypothesis through accumulated confirming evidence (p-values, confidence intervals).

*Popper's addition*: Emphasizes that confirmation is logically weak--no amount of positive instances proves universality. But a single negative instance can definitively refute. This *logical asymmetry* is fundamental, not just methodological.

Example in debugging:
- 1,000 successful test runs don't prove correctness (induction problem)
- 1 crash proves incorrectness (modus tollens--deductively valid)

*Why this matters*: It shifts focus from "gathering support" to "surviving criticism." The goal isn't to confirm your hypothesis but to *fail to falsify it despite your best efforts*.



### 2. Corroboration vs. Confirmation[^1]

*Traditional testing*: Uses probability to quantify belief in hypotheses (Bayesian updating, likelihood ratios).

*Popper's distinction*: Rejects probabilistic confirmation entirely. Instead, theories are *corroborated* by surviving severe tests--but this adds no probability that the theory is true.

*Corroboration* is not:
- A measure of truth
- A degree of belief
- Cumulative evidence for the hypothesis

*Corroboration* is:
- A historical record of test survival
- An indicator of how rigorously challenged the theory has been
- A reason to prefer one theory over another *for now*

In debugging terms:
- Passing 1,000 tests doesn't make your code "99.9% likely to be correct"
- It means your code has survived 1,000 attempts to break it
- The next test could still reveal a fatal flaw

*This is radically different from frequentist or Bayesian confirmation.*

[^1]: One book I found enjoyable in this critique is: Johansson, I. (1975). *A critique of Karl Popper's methodology*. Stockholm: Esselte studium (Akad.-förl.). Currently (2026) apparently he is willing to
send you a PDF: http://ingvarjohansson.se/.


### 3. Bold Conjectures and Severe Tests

*Traditional approach*: Often conservative--test hypotheses close to known results, incrementally extend theories.

*Popper's emphasis*: Science advances fastest through *bold, risky conjectures* that make precise, surprising predictions. The bolder the claim, the more it "sticks its neck out," the better it is--*if it survives*.

In debugging:
- *Weak hypothesis*: "There might be a logic error somewhere in the module."
- *Bold hypothesis*: "The bug occurs because the function assumes the input array is sorted, but the caller doesn't guarantee this, specifically when data comes from the cache layer."

The bold hypothesis:
- Makes specific predictions (fails on unsorted cached data)
- Is easier to test (create that exact scenario)
- Is more informative when it survives (we've ruled out a very specific failure mode)

*Traditional deductive testing doesn't mandate boldness*--Popper does.



### 4. The Demarcation Criterion

*Traditional science*: Doesn't clearly distinguish science from non-science.

*Popper's criterion*: A theory is scientific if and only if it is *falsifiable in principle*. Unfalsifiable claims (astrology, Freudian psychoanalysis, "the code just feels wrong") aren't scientific.

In debugging:
- "The system is unreliable" -> unfalsifiable, useless
- "The system crashes when memory usage exceeds 4GB due to a leak in the connection pool" -> falsifiable, useful

*This adds a meta-level filter*: Before testing a hypothesis, ask "Can this be proven wrong?" If not, it's not a scientific hypothesis.

Traditional hypothesis testing doesn't inherently reject unfalsifiable claims--Popper does.



### 5. All Observation is Theory-Laden

*Traditional empiricism*: Assumes observations are neutral, objective facts.

*Popper's insight*: What we observe depends on what we're looking for. Observation is always interpreted through theoretical frameworks.

In debugging:
- You can't just "look at the data"--you need a theory about what to look for
- The same log file means nothing to someone without domain knowledge
- Your hypothesis determines which variables you monitor, which breakpoints you set

Example:
```python
print(account.balance)  # What are you looking for?
```

- If hypothesis: "balance goes negative," you watch for `balance < 0`
- If hypothesis: "balance overflows," you watch for `balance > MAX_INT`
- Same observation, different theoretical lens

*Traditional testing often assumes observation is theory-neutral*--Popper shows it never is.



### 6. Verisimilitude (Truth-Likeness)

*Traditional approach*: Theories are either true or false.

*Popper's refinement*: Even false theories can be closer to truth than others. Science progresses toward greater *verisimilitude*--truth-likeness.

In debugging:

*Hypothesis 1*: "Something is broken."  
*Hypothesis 2*: "The withdraw function is broken."  
*Hypothesis 3*: "The withdraw function allows negative balances."  
*Hypothesis 4*: "The withdraw function processes the transaction before checking balance >= amount."

Even if H4 is wrong (maybe it's `balance > amount` that's needed, not `>=`), it's *closer to the truth* than H1.

*This explains iterative refinement*: Each hypothesis doesn't have to be correct--it just has to be *better* than the last. Debugging is asymptotic approach to truth.



### 7. Background Knowledge and Auxiliary Hypotheses

*Traditional testing*: Tests one hypothesis in isolation.

*Popper's realism*: Every test actually tests a *whole system of assumptions*:
- The hypothesis itself
- The correctness of the test
- The reliability of the environment
- The validity of background theory

When a test fails, you don't know which assumption was wrong. This is the *Duhem-Quine problem*.

In debugging:

You test: "This function handles empty lists correctly."

But you're also assuming:
- Your test framework works
- The language runtime is correct
- The list implementation is correct
- Your understanding of "correct" is right

If the test fails, *any of these could be wrong*. Experienced debuggers know to question the test itself, the tooling, even the language.

*Traditional deductive testing often ignores this holistic problem*--Popper makes it central.



### 8. The Evolutionary Epistemology Analogy

*Traditional view*: Science accumulates truth through careful reasoning.

*Popper's metaphor*: Science works like biological evolution--through *variation and selection*.

- *Variation*: Propose multiple competing hypotheses (mutations)
- *Selection*: Eliminate those that fail tests (natural selection)
- *Survival*: Retain what hasn't been killed yet (not what's been proven true)

In debugging:

You simultaneously consider:
1. Maybe the input validation is wrong
2. Maybe the state management is wrong  
3. Maybe the concurrency handling is wrong

You run tests to *eliminate* possibilities. What survives isn't "proven"--it just hasn't died yet.

*This is fundamentally different from linear hypothesis testing*--it's competitive, Darwinian, eliminative.



### 9. No Justification, Only Critical Preference

*Traditional epistemology*: Seeks to *justify* belief in theories (rationalism, empiricism, foundationalism).

*Popper's critical rationalism*: Rejects justificationism entirely. We can't justify beliefs, we can only *critically compare* them.

Key shift:
- Don't ask: "Is this theory justified?"
- Ask: "Between competing theories, which has survived stronger criticism?"

In debugging:

You don't prove your fix is correct. You can't.

You show:
- The old code failed test X
- The new code passes test X
- The new code also passes tests Y, Z
- Therefore, prefer the new code--not because it's proven, but because it's survived more criticism

*This is a meta-level philosophical difference that doesn't reduce to standard hypothesis testing.*



### 10. The Openness of Scientific Knowledge

*Traditional view*: Science aims at certain, finished knowledge.

*Popper's view*: All knowledge is provisional, conjectural, and eternally revisable. There is no endpoint.

In debugging:
- Shipping code doesn't mean it's bug-free
- It means you've failed to find bugs *so far*
- New environments, new use cases, new stress levels can always reveal issues

*The attitude this creates*:
- Permanent humility about your code
- Expectation that bugs will emerge
- Design for debuggability, not just correctness
- Continuous testing, monitoring, iteration

*Traditional testing often treats "verified" code as done*--Popper insists nothing is ever done.



### Summary: What Popper Adds Beyond Standard Deductive Testing

| Aspect | Traditional Deductive Testing | Popper's Addition |
|--------|-------------------------------|-------------------|
| *Logic* | Modus ponens (if H then D; D; therefore H plausible) | Modus tollens (if H then D; not-D; therefore not-H) |
| *Goal* | Confirm hypotheses | Falsify hypotheses |
| *Evidence* | Accumulates support | Survives criticism |
| *Success* | Positive results | Failure to fail |
| *Probability* | Uses statistical inference | Rejects probabilistic confirmation |
| *Demarcation* | Doesn't distinguish science/non-science | Falsifiability criterion |
| *Observation* | Theory-neutral | Theory-laden |
| *Progress* | Linear accumulation | Evolutionary elimination |
| *Knowledge* | Justified true belief | Unjustified conjecture that survived |
| *Endpoint* | Certain knowledge | Permanent revisability |



### Philosophical Core

Popper's methodology isn't just "test your hypotheses"--it's a *complete epistemological stance*:

1. *We can't prove, only disprove* (logical asymmetry)
2. *Knowledge grows by error elimination* (not truth accumulation)
3. *All knowledge is conjectural* (fallibilism)
4. *Criticism, not justification* (critical rationalism)
5. *Openness to revision* (permanent uncertainty)

This is why Popper isn't reducible to standard hypothesis testing--he's
proposing a fundamentally different relationship to knowledge itself.

In debugging, this means:
- You're never certain your fix is right
- You're always ready to be wrong again
- You value tests that could break your code, not confirm it
- You see bugs as opportunities to learn, not failures
- You never stop testing, never stop questioning

*That's a philosophical stance, not just a methodology.*

