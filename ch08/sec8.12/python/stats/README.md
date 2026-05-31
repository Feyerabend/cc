
## Stats

This Python program implements a custom framework for property-based testing (PBT)
augmented with statistical analysis. At its core, it's a class called `StatisticalTestRunner`
that automates the generation of random test inputs, evaluates a user-defined "property"
(a boolean function asserting some invariant about the code under test), and runs
thousands of iterations to assess whether the property holds reliably. It goes beyond
basic pass/fail by collecting metrics like success rates, confidence intervals, input
distributions, and failure patterns, treating testing as a statistical experiment.

The program includes:
- *Input generation strategies*: Simple classes like `IntegerStrategy` and `ListStrategy`
  to produce random data (e.g., integers or lists of integers) with controllable parameters
  like size or range.
- *Test execution*: Loops over a sample size (default 1000), generates inputs adaptively
  (increasing complexity over iterations), runs the property function, and tracks
  successes/failures.
- *Statistical enhancements*: Analyses input characteristics (e.g., type, length,
  complexity via entropy), computes confidence intervals for success rates, estimates
  statistical power, and identifies patterns in failures.
- *Example usage*: Tests a sorting property (ensuring `sorted(lst)` is ordered and
  preserves elements) on random lists of integers, then prints a summary report.


### Use of Property-Based Testing

Property-based testing here is used to verify general invariants ("properties") of
code through massive random input generation, rather than hand-crafted examples.
The key components are:
- *Property function*: A callable like `sorting_property(lst)` that takes generated
  input and returns `True` if the invariant holds (e.g., sorting a list results in
  an ordered list with the same elements). If it fails or raises an exception,
  it's recorded as a failure.
- *Strategies*: These define how to generate inputs. For instance, `ListStrategy`
  composes with `IntegerStrategy` to create lists of random integers, with adaptive
  sizing (inputs get more complex as tests progress via `_adaptive_sizing`).
- *Runner*: The `run_statistical_test` method orchestrates everything: generates
  inputs, evaluates the property, and analyses results statistically.

In the example, it tests sorting on 500 random lists, expecting 100% success since
Python's `sorted` is reliable for integers. But in real use, this could uncover edge
cases like empty lists, duplicates, or extreme values. The statistical layer adds
rigour: instead of just "passes all tests," you get quantifiable confidence (e.g.,
success rate with a 95% confidence interval) and insights into input distributions
(e.g., average list length, type breakdowns).

This approach shines for testing algorithms or data structures where *exhaustive testing* is
impossible, emphasising "falsification"--trying to disprove the property with diverse inputs.


### No Use of Hypothesis?

The program deliberately avoids Hypothesis to build a lightweight, from-scratch implementation
focused on custom statistical features. This have an *educational purpose*: It demonstrates
core PBT concepts (strategies, generation, properties) without external dependencies, making
it easier to understand internals. Hypothesis abstracts much of this away, which is great for
productivity but less so for learning.

But, other reasons for studying this code includes *customisation for statistics*:
Hypothesis excels at generation and shrinking but doesn't natively provide the deep
statistical analysis here, like input entropy, failure pattern detection, adaptive sizing,
or power estimation. These "experimental science" aspects (e.g., confidence intervals,
distribution analysis) we can do without extending Hypothesis via plugins.

A third reason is *simplicity and control*: Hypothesis requires installing a package and
learning its DSL (e.g., `@given` decorators, built-in strategies). This code uses pure
Python with minimal imports (e.g., `random`, `statistics`, `math`), making it self-contained
and reproducible without pip. It also uses a fixed seed for determinism, which Hypothesis
supports but isn't the default focus.

If Hypothesis were used, the example could be rewritten concisely:

```python
from hypothesis import given
from hypothesis.strategies import lists, integers

@given(lists(integers(min_value=-100, max_value=100)))
def test_sorting_property(lst):
    sorted_lst = sorted(lst)
    assert all(sorted_lst[i] <= sorted_lst[i+1] for i in range(len(sorted_lst)-1))
    assert Counter(lst) == Counter(sorted_lst)  # Preserves elements
```
This runs many tests automatically, with shrinking on failures. But it lacks the
program's statistical reporting--you'd need extra code for that.

Drawbacks of not using Hypothesis: No automatic shrinking (minimising failing examples),
less sophisticated generation (e.g., no recursive strategies), and potential for weaker
randomness or coverage.


### How to Write Property-Based Tests Without Hypothesis

You can implement PBT manually by following a structure like this program:

1. *Define strategies*: Create generator classes or functions that produce random data.
   Use `random` module for randomness, and parameters like `size` for controlling complexity.
   - Example: For strings, `def gen_string(size): return ''.join(random.choice(string.ascii_letters) for _ in range(random.randint(0, size)))`
   - Compose them: e.g., lists of strings via a wrapper that generates lengths then elements.

2. *Write the property*: A function that takes input and returns `bool` (or raises on failure).
   Focus on invariants, not specific cases.
   - Example: For a reversal function, `def prop_reverse(s): return s == s[::-1][::-1]`

3. *Run the tests in a loop*:
   - Set a sample size (e.g., 1000+ for confidence).
   - Seed random for reproducibility.
   - Generate inputs, evaluate property, collect failures.
   - Add adaptive logic: Increase input size over iterations to stress-test.

4. *Handle failures*: Log inputs that fail; optionally implement manual shrinking
   (e.g., binary search on list length to find minimal failing case).
   
5. *Add analysis (optional, like here)*: Track metrics during runs for stats.

Full minimal example without this program's stats:

```python
import random

class StringStrategy:
    def generate(self, rand, size):
        length = rand.randint(0, size)
        return ''.join(rand.choice('abc') for _ in range(length))

def prop_palindrome(s):
    return s == s[::-1] or len(s) < 2  # dummy property: short or palindrome

rand = random.Random(42)
strategy = StringStrategy()
failures = []
for i in range(1000):
    size = i // 40 + 1  # adaptive
    input = strategy.generate(rand, size)
    if not prop_palindrome(input):
        failures.append(input)

if failures:
    print(f"Failures: {failures}")
else:
    print("All tests passed!")
```
This scales easily but requires manual effort for advanced features.


### Properties of Property-Based Testing in This Context

In this program's context, PBT emphasises statistical robustness and empirical validation.

- *Generativity*: Tests aren't fixed; inputs are randomly generated per strategy,
  exploring vast spaces (e.g., lists up to length 50 with integers -100 to 100).
- *Falsifiability*: Aims to disprove hypotheses (e.g., "Sorting always works") via
  counterexamples, with failures analysed for patterns (e.g., common types or sizes
  in failures).
- *Statistical Confidence*: Not just binary pass/fail – success rates with confidence
  intervals (using normal approximation via z-score) quantify reliability. E.g., a 99%
  success rate might have interval (0.98, 1.0), indicating high confidence.
- *Distribution Awareness*: Analyses input characteristics (e.g., mean length 12.5,
  std dev 7.2) to ensure generation isn't biased (e.g., too many empty lists). Uses
  entropy for complexity, helping detect if tests are "diverse enough."
- *Hypothesis-Driven*: Frames tests as experiments (e.g., "Property holds uniformly"),
  with power estimation (simplified here based on sample size) to assess detection strength.
- *Adaptivity*: Inputs evolve (via `_adaptive_sizing`), starting simple and ramping up,
  mimicking real-world stress.
- *Reproducibility and Extensibility*: Seeded random ensures repeatable runs; modular
  for adding strategies or analyses.

In broader PBT terms, this aligns with "QuickCheck-style" testing, but stats make it more
"scientific". Limitations: Assumes properties are pure (no side effects), doesn't handle
non-determinism well, and power calculation is heuristic (real stats might use beta
distributions or simulations).
