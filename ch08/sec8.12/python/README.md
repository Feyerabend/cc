
> [!IMPORTANT]
> The examples require the *Hypothesis* library (`pip install hypothesis`).
> Several examples also require *pytest* (`pip install pytest`).

## Property-Based Testing

### Introduction

Property-based testing (PBT) occupies a hybrid position between conventional
software testing and fully formal verification.

Like traditional testing, it executes the program on specific inputs to check
whether it behaves as expected. The key difference is that, instead of manually
choosing a handful of representative cases, property-based testing generates a
wide variety of inputs — often randomly or according to systematic rules — to
explore the program's behaviour over a much larger portion of the input space.
This approach still relies on sampling rather than exhaustively covering all
possible cases, so it cannot provide absolute guarantees; at best, it can
*expose faults with high probability*.

At the same time, property-based testing shares important characteristics with
*formal verification*. The process begins by stating general properties or
invariants that the program should satisfy for all valid inputs. This
specification-driven mindset is the same starting point as a formal proof: the
developer expresses requirements in abstract, universal terms rather than as a
list of examples. In fact, in some workflows, property-based testing serves as
a preliminary step before formal verification — allowing developers to validate
that a property is reasonable and that no obvious counterexamples exist before
investing in a proof. When a test fails, the testing framework often produces a
minimal counterexample, much like a proof assistant returning a countermodel.

In practice, this combination makes property-based testing a flexible tool. It
retains the pragmatic immediacy of testing — quick execution and direct feedback
— while nudging developers toward the formal methods mindset of reasoning about
entire domains of inputs. This hybrid nature explains why it is equally at home
in robust traditional QA pipelines and in verification-oriented development
processes.


### Key Concepts

*Properties (invariants)*
A *property* is a predicate that should hold for every valid input, not just for
selected examples. Common patterns include:

| Pattern                    | Example                                         |
|----------------------------|-------------------------------------------------|
| Structural invariant       | Sorted output must be non-decreasing            |
| Round-trip / invertibility | `decode(encode(x)) == x`                        |
| Idempotence                | `sort(sort(x)) == sort(x)`                      |
| Commutativity              | `f(a, b) == f(b, a)`                            |
| Conservation               | `Counter(sort(x)) == Counter(x)`                |
| Metamorphic relation       | `f(transform(x))` relates predictably to `f(x)` |

*Strategies (generators)*
A *strategy* describes how to produce random values of a given type. Strategies
can be composed: `lists(integers(-100, 100))` builds a strategy that generates
lists of bounded integers. The framework starts with small, simple inputs and
gradually scales to larger, more complex ones.

*Shrinking*
When a failing input is found, the framework *shrinks* it: it searches for the
smallest possible input that still triggers the failure. This dramatically
reduces debugging time — a failure originally found in a 47-element list might
shrink to a 2-element list that exposes the root cause directly.

*Falsifiability*
Property-based tests are *falsifiable*: they try to break the property, not to
confirm it. If no counterexample is found after many trials, the test passes —
but this is a probabilistic guarantee, not a proof.

*Why use PBT?*
- Discovers edge cases (empty inputs, duplicates, extreme values, Unicode) that
  manual tests routinely miss.
- Turns the specification into executable documentation.
- The minimal counterexample from shrinking is often more diagnostic than a
  large randomly generated failure.
- Naturally integrates with formal methods: a property that survives thousands
  of generated inputs is a reasonable candidate for a proof attempt.

*When to use PBT?*
PBT shines for *algorithmic code* (sorting, encoding, parsing, data structures,
mathematical functions) and whenever the correct output is hard to state for
specific inputs but easy to state as a general rule. It complements, rather
than replaces, traditional unit tests: use unit tests to nail down known
important cases; use PBT to stress-test the general contract.


### The Hypothesis Library

[Hypothesis](https://hypothesis.readthedocs.io/) is the standard Python
library for property-based testing. Its `@given` decorator wires a strategy to
a test function and handles generation, shrinking, and failure reporting
automatically:

```python
from hypothesis import given, strategies as st
from collections import Counter

@given(st.lists(st.integers()))
def test_sort_preserves_elements(lst):
    result = sorted(lst)
    assert Counter(result) == Counter(lst)
    assert all(result[i] <= result[i+1] for i in range(len(result) - 1))
```

Hypothesis will generate hundreds of lists, shrink any failure to a minimal
case, and replay it on subsequent runs using its built-in example database.


### Interactive Demo

*`DEMO.html`* — open in a browser (no server required).

An interactive JavaScript demo that visualises the four core stages of
property-based testing without requiring Python or Hypothesis:

1. *Test Generation* — generates random arrays and checks the double-reverse
   property `reverse(reverse(x)) == x` live, with pass/fail colouring.
2. *Property Verification* — runs a deliberately buggy sort against three
   selectable properties (sorted order, length preservation, element
   preservation) to show how PBT catches failures in practice.
3. *Shrinking* — steps through the shrinking process on a known failing input,
   showing how the framework reduces a complex counterexample to its minimal form.
4. *Advanced Properties* — tests idempotence (`|x|`), commutativity (÷),
   associativity (−), inverse (√x²), and monotonicity (stable sort), with
   pass/fail results for each generated case.

This demo is a useful first stop for anyone new to PBT concepts before diving
into the Python examples below.


### Examples in This Folder

- [simple](./simple/) — Starting point: the contrast between traditional
  unit testing and property-based testing on a sorting function.
    - `trad_sort.py`: Tests a sorting function with specific unit tests for
      basic functionality, edge cases, duplicates, and negative numbers, using
      Python's `sorted` function.
    - `hyp_sort.py`: Uses Hypothesis for property-based testing, verifying four
      sorting invariants (ordering, permutation, length, idempotence) across
      random integer lists.

- [str](./str/) — Property-based testing on Python strings, checking
  associativity, identity, length additivity, reversal involution, and
  substring preservation with random Unicode inputs. Also provides a
  side-by-side comparison between Hypothesis and classic example-based tests
  for each property. Requires pytest.

- [instr](./instr/) — Property-based testing of a custom function with a
  formal specification. The `instr.py` program implements the BASIC `INSTR`
  function, which finds the 1-based position of a substring within a string
  from a specified start, returning 0 if not found. The file includes unit
  tests for specific scenarios and property-based tests using Hypothesis to
  verify general properties such as substring matching and position
  constraints.

- [bst](./bst/) — A Python Binary Search Tree (BST) implementation (backed by
  a `set` for clarity) tested with Hypothesis against four structural
  invariants: sorted in-order traversal, correct size, membership, and
  completeness. Logging in JSON Lines format captures test inputs and BST
  states for debugging; `bst_log.html` provides a browser-based log viewer;
  `chart.html` is a Chart.js upload tool for the visualisation projects
  described in `PROJECT.md`.

- [stats](./stats/) — A custom property-based testing framework built without
  Hypothesis. `stats.py` implements `StatisticalTestRunner`, which evaluates
  properties with statistical reporting: success rates, confidence intervals,
  and failure-pattern analysis. `shrink.py` extends this with type-aware
  shrinking (integers, floats, lists, strings, dicts) and shrinking
  effectiveness metrics. Demonstrates on a buggy sorting property (fails on
  duplicates) versus a correct one. Educational: shows the internals that
  libraries like Hypothesis handle automatically.

- [mmorph](./mmorph/) — A metamorphic testing framework. Metamorphic testing
  verifies software by checking *relational* properties between transformed
  inputs and outputs, without needing exact expected outputs. Defines
  metamorphic relations for sorting (permutation invariance, element
  preservation, duplication, subset), mathematical functions (√ scaling,
  log addition), and strings (case insensitivity, whitespace normalisation).
  Demonstrates on correct and buggy sorters, showing which relations catch
  which bugs.

- [vm](./vm/) — An Enhanced Virtual Machine (EVM) with a stack-based
  architecture executing a rich opcode set: arithmetic, stack manipulation,
  logical operations, and control flow (jumps, subroutines). The VM is covered
  by both classical `unittest` cases and property-based tests using
  Hypothesis-generated RPN programs, verifying that arbitrary valid programs
  either produce a float result or raise an expected error.

- [conc](./conc/) — Property-based testing for concurrent code. Demonstrates
  three thread-safety patterns — a counter, a bank account, and a bounded
  queue — each in an unsafe (racy) and a safe (lock-protected) variant.
  Properties cover the counter invariant (`n_threads × inc_per_thread`),
  conservation of total money under concurrent transfers, and queue capacity
  bounds. The demo shows the race condition firing live; Hypothesis generates
  diverse thread-count and workload combinations to stress-test the safe
  implementations. Includes a note on Python's GIL and pointers to tools
  for exhaustive interleaving coverage.

- [frame](./frame/) — A full custom property-based testing framework:
  `strategies.py` defines composable generators for integers, floats, strings,
  lists, tuples, dictionaries, and combinators (`one_of`, `map`, `filter`,
  `just`), all with built-in shrinking. `framework.py` implements test
  execution, automatic shrinking with complexity estimation, a `@given`
  decorator, and a `PropertyTestSettings` context manager. Demonstrates both
  passing and deliberately failing properties with detailed result reporting.
