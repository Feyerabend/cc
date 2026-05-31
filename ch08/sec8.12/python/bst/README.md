
## Property-Based Testing on BST

To start with cf. a more traditional implementation of BST,
[Binary Search Tree](./../../../../ch07/data/bst.py) in Python.

Property-based testing (PBT) is a testing methodology that focuses on defining
and verifying general properties or invariants that a system must satisfy,
rather than testing specific input-output pairs as in traditional unit testing.
Instead of manually writing test cases with fixed inputs, PBT uses tools to
generate a wide range of inputs automatically, often randomly, to stress-test
the system against its specified properties. This approach helps uncover edge
cases and unexpected behaviours that might be missed in traditional testing.

- *Properties/Invariants*: These are high-level rules or behaviours that the
  system must always uphold, regardless of the input. For example, in a
  binary search tree (BST), the in-order traversal must always produce
  a sorted sequence.

- *Automatic Input Generation*: Tools like Hypothesis (used in the provided
  files) generate diverse inputs, including edge cases like empty lists,
  duplicates, or extreme values.

- *Falsification*: The testing framework tries to find inputs that violate
  the defined properties, helping developers identify bugs.

- *Scalability*: PBT can test a system with thousands of input combinations,
  increasing confidence in its correctness.


### What the Provided Files Illustrate

The files (`bst.py`, `bst_log.py`, `bst_log_pytest.py`, `bst_test_log.jsonl`,
and `bst_log.html`) demonstrate a property-based testing setup for a *Binary
Search Tree* (BST) implementation using Python and the Hypothesis library.

#### 1. *bst.py*
- *Purpose*: This is the core implementation of a simplified BST and its
  property-based tests.
- *Key Features*:
  - Implements a `BinarySearchTree` class that uses a Python `set` to store
    values, *simulating* a BST's behaviour (though not a traditional tree structure).
  - Defines methods: `insert` (adds a value), `inorder_traversal` (returns
    values in sorted order), `contains` (checks if a value exists), and
    `size` (returns the number of unique values).
  - Uses Hypothesis to define a property-based test (`test_bst_invariants`)
    that checks four key invariants of a BST:
    1. *Structural Invariant*: The in-order traversal yields a sorted
       sequence (`is_sorted_ascending`).
    2. *Cardinality Property*: The BST's size equals the number of unique
       inserted values.
    3. *Membership Property*: All inserted values are retrievable via `contains`.
    4. *Completeness Property*: No extra values appear in the traversal.
  - The `@given` decorator with `st.lists(st.integers(), min_size=0, max_size=50)`
    generates random lists of integers (0 to 50 elements) for testing.
- *What It Illustrates*:
  - A clean, minimal example of property-based testing with Hypothesis.
  - How to define and test general invariants of a data structure.
  - The use of random input generation to verify correctness across a
    range of inputs, including edge cases like empty lists or duplicates.

#### 2. *bst_log.py*
- *Purpose*: Extends `bst.py` by adding logging functionality to record
  the test inputs and intermediate states of the BST.
- *Key Features*:
  - Similar to `bst.py`, but logs each test run to a file (`bst_test_log.jsonl`)
    in JSON Lines format.
  - For each test case, it records:
    - The `generated_values` (input list from Hypothesis).
    - The `states` (a list of dictionaries, each capturing the inserted value
      and the current in-order traversal after each insertion).
  - Uses the `@settings(max_examples=10)` decorator to limit Hypothesis
    to 10 test cases for demonstration.
  - The test logic is identical to `bst.py`, ensuring the same invariants are checked.
- *What It Illustrates*:
  - How to augment property-based tests with logging to inspect test execution
    and debug failures.
  - The ability to track the state of the system after each operation, which is
    useful for understanding how the BST evolves during testing.
  - The use of JSON Lines for structured, machine-readable test logs.

#### 3. *bst_log_pytest.py*
- *Purpose*: A variant of `bst_log.py` tailored for use with `pytest`,
  a popular Python testing framework.
- *Key Features*:
  - Nearly identical to `bst_log.py`, but omits the `@settings` decorator
    and the `if __name__ == "__main__":` block, as it’s designed to be
    run by `pytest` rather than as a standalone script.
  - Logs test data to `bst_test_log.jsonl` in the same format as `bst_log.py`.
- *What It Illustrates*:
  - Integration of property-based testing with a testing framework like `pytest`.
  - How Hypothesis tests can be adapted to fit into existing test suites,
    leveraging `pytest`’s features like test discovery and reporting.

#### 4. *bst_test_log.jsonl*
- *Purpose*: Contains the logged output from running `bst_log.py` or `bst_log_pytest.py`.
- *Key Features*:
  - Each line is a JSON object representing one test run, with:
    - `generated_values`: The random list of integers generated by Hypothesis.
    - `states`: A list of states, each with the `inserted` value and the
      `current_traversal` after insertion.
  - Example entries show diverse test cases, including:
    - Empty lists (`[]`).
    - Single-element lists (`[0]`).
    - Lists with small and large integers, both positive and negative (e.g.,
      `[-19374, -9489, 69, 104]`).
    - Lists with extreme values (e.g., `-3656513945143422420`
      or `122848875813976213555377759440973736905`).
- *What It Illustrates*:
  - The diversity of inputs generated by Hypothesis, showcasing its
    ability to test edge cases and extreme values.
  - How logging captures the progression of the BST’s state, making it
    easier to verify that the in-order traversal remains sorted after each insertion.
  - The practical output of property-based testing, which can be analysed
    to understand test coverage or debug issues.

#### 5. *bst_log.html*
- *Purpose*: A functional HTML/JavaScript viewer for the `bst_test_log.jsonl`
  log file, displaying each test case and the step-by-step BST state after
  every insertion.
- *Key Features*:
  - Uses the browser `fetch` API to load `bst_test_log.jsonl` at runtime.
  - Renders each test case as a collapsible block showing the generated values
    and the in-order traversal state after each insertion.
  - Must be served via a local web server (e.g. `python -m http.server`) rather
    than opened as a `file://` URL, because `fetch` is blocked by browser
    same-origin policy for local files.
- *What It Illustrates*:
  - How property-based test logs can be made human-readable with a minimal
    browser-side viewer.
  - The concrete progression of the BST state as values are inserted,
    confirming the sorted-order invariant visually.

#### 6. *chart.html*
- *Purpose*: A standalone Chart.js upload tool that renders any Chart.js-compatible
  JSON config file as an interactive chart.
- *Key Features*:
  - Accepts a `.json` file via a file-picker; no server needed.
  - Destroys and re-renders the chart each time a new file is uploaded.
  - Works directly with the three bundled example configs:
    `test-case.json` (bar chart of test-case sizes),
    `example-chart.json` (line chart of insertion times), and
    `example-insert.json` (bar chart comparing BST implementations).
- *What It Illustrates*:
  - A reusable visualisation tool for the project-idea reports described in
    `PROJECT.md` (Projects 1, 3, and 6).


### Collective Insights
Together, these files illustrate a complete workflow for property-based testing
of a data structure:
- *Implementation and Testing*: `bst.py` shows how to implement a BST and define
  its invariants using PBT.
- *Logging and Debugging*: `bst_log.py` and `bst_log_pytest.py` demonstrate how
  to log test execution for transparency and debugging, with `bst_log_pytest.py`
  showing integration with `pytest`.
- *Test Coverage*: `bst_test_log.jsonl` highlights the variety of inputs generated
  by Hypothesis, including edge cases, which is a key strength of PBT.
- *Visualisation*: `bst_log.html` provides a browser-based log viewer for step-by-step
  inspection; `chart.html` enables chart generation from JSON configs produced by the
  project extensions in `PROJECT.md`.


### Benefits Demonstrated
- *Robustness*: The tests verify that the BST maintains its invariants across
  diverse inputs, catching potential bugs in edge cases.
- *Automation*: Hypothesis automates input generation, reducing the need for
  manually crafted test cases.
- *Debugging Support*: Logging in `bst_log.py` and `bst_log_pytest.py`
  provides detailed insights into test execution, making it easier to diagnose failures.
- *Scalability*: The use of Hypothesis allows testing with a wide range
  of inputs, increasing confidence in the BST’s correctness.


### Limitations Highlighted
- *Simplified BST*: The BST implementation uses a `set`, which avoids the complexity
  of a traditional tree structure. This simplifies the example but doesn’t test
  properties like tree balance or node structure.
- *Visualisation Scope*: The `bst_log.html` viewer displays insertion steps but does
  not yet include aggregate statistics (e.g. distribution of input sizes). `chart.html`
  can fill that gap for the project extensions in `PROJECT.md`.
- *Limited Test Runs*: In `bst_log.py`, the `@settings(max_examples=10)` limits the
  number of test cases, which might not fully exploit Hypothesis’s ability to generate
  thousands of tests (so visualisation must be altered to view this).


### Practical Takeaways

These files serve as an educational example of how to:
- Use Hypothesis for property-based testing in Python.
- Define and verify data structure invariants.
- Log test execution for debugging and analysis.
- Integrate PBT with `pytest` for seamless testing workflows.
- Visualise test results in the browser via `bst_log.html` and `chart.html`.

For someone new to PBT, these files provide a hands-on introduction to setting up,
running, and analysing property-based tests, with a focus on a familiar data structure
like a BST. To extend this project, one (you) could:
- Implement a traditional BST with nodes and test its structural properties.
- Extend `bst_log.html` with aggregate charts (e.g., distribution of input sizes
  or values), using `chart.html` as the Chart.js rendering tool.
- Increase the number of test cases or add more complex properties to test.

