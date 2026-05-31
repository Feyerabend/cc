
## Project Ideas


#### 1. Enhance List Strategy with Uniqueness Constraints

- *Description*: Extend the existing `ListStrategy` to support generating lists with
  unique elements, optionally enforcing constraints like sorted order or specific
  patterns (e.g., all even numbers). Implement corresponding shrinking logic to maintain
  these constraints.

- *Objectives*: Modify `ListStrategy.generate` to ensure unique elements using a
  set-based approach or rejection sampling, and update `ListStrategy.shrink` to
  preserve uniqueness when removing elements or shrinking values. Test with properties
  like checking if a sorting function preserves uniqueness.

- *Why it's useful*: Many algorithms (e.g., set operations, unique key lists) require
  unique elements, and this enhancement makes the framework more versatile for testing
  such cases.

- *Skills developed*: Working with constraints in random generation, advanced shrinking
  logic, and testing with domain-specific properties.

- *Difficulty*: Intermediate.


#### 2. Create a Custom Reporting Module for Test Results

- *Description*: Develop a reporting module that formats and exports `TestResult` objects
  from `framework.py` into different formats (e.g., JSON, HTML) for better visualisation
  and integration with CI/CD pipelines.

- *Objectives*: Create a `TestReporter` class that processes `TestResult` data, including
  pass/fail status, minimal failing cases, and execution metrics. Support multiple output
  formats and add options for saving reports to files. Test by running existing properties
  (e.g., list reversal) and generating reports.

- *Why it's useful*: Detailed, structured reports improve debugging and make the framework
  more practical for professional testing environments.

- *Skills developed*: Data serialisation, file I/O, and designing extensible reporting systems.

- *Difficulty*: Intermediate.


#### 3. Add Support for Generating and Shrinking Sets

- *Description*: Implement a `SetStrategy` to generate sets of elements from a base strategy
  (e.g., integers or strings) with configurable size bounds, and support shrinking by removing
  elements or simplifying set contents.

- *Objectives*: Create a new `SetStrategy` class that uses a base strategy to generate unique
  elements via `random.choices` and rejection sampling. Implement `shrink` to reduce set size
  or simplify elements while maintaining uniqueness. Test with properties like set union
  commutativity.

- *Why it's useful*: Sets are common in algorithms (e.g., graph algorithms, deduplication),
  and this extends the framework to support such data types.

- *Skills developed*: Handling uniqueness constraints, iterator-based shrinking, and
  property-based testing for collections.

- *Difficulty*: Intermediate.


#### 4. Create a Recursive Strategy for Binary Trees

- *Description*: Design a `TreeStrategy` to generate binary trees with node values from a
  base strategy, controlling depth with the `size` parameter to avoid excessive recursion.
  Implement shrinking to prune subtrees or simplify node values.

- *Objectives*: Define a `Node` class for binary trees and implement `TreeStrategy.generate`
  with depth limits based on `size`. Create `TreeStrategy.shrink` to remove subtrees or shrink
  node values. Test with properties like checking if a tree traversal preserves all nodes.

- *Why it's useful*: Recursive data structures are common in algorithms (e.g., binary search
  trees), and this enables testing of hierarchical data processing.

- *Skills developed*: Recursion, data structure design, and managing complexity in generation
  and shrinking.

- *Difficulty*: Advanced.


#### 5. Integrate with Pytest for Seamless Testing

- *Description*: Adapt the framework to work with the `pytest` testing library by creating a
  plugin or fixture that uses the `@given` decorator to run property-based tests within pytest's
  workflow.

- *Objectives*: Create a pytest fixture that wraps `test_property` or `@given` to generate test
  data and report results in pytest's format. Handle minimal failing cases in pytest's failure
  output. Test with a simple module (e.g., a string manipulator).

- *Why it's useful*: Pytest is widely used, and integration makes the framework accessible to
  developers familiar with standard Python testing tools.

- *Skills developed*: Pytest plugin development, fixture design, and integration with testing
  ecosystems.

- *Difficulty*: Intermediate to Advanced.


#### 6. Optimise Shrinking with Adaptive Strategies

- *Description*: Improve the efficiency of shrinking across strategies by implementing adaptive
  techniques, such as binary search for numeric values or prioritising high-impact shrinks for
  collections (e.g., removing multiple elements at once).

- *Objectives*: Refactor `IntegerStrategy.shrink` to use binary search for faster convergence
  to minimal values. Modify `ListStrategy.shrink` to try removing larger chunks of elements first.
  Benchmark performance using Python's `timeit` module on large inputs.

- *Why it's useful*: Faster shrinking reduces debugging time, especially for complex failing cases,
  making the framework more efficient.

- *Skills developed*: Algorithm optimisation, performance profiling, and advanced iterator manipulation.

- *Difficulty*: Advanced.


#### 7. Test a Real-World Module with Custom Strategies

- *Description*: Apply the framework to test a custom Python module (e.g., a URL parser or matrix
  calculator) by defining properties and creating custom strategies tailored to the module's input
  types.

- *Objectives*: Write a small module, define 3-5 properties (e.g., “parsing a valid URL returns a
  structured object”), and create a custom strategy if needed (e.g., for valid URLs). Use shrinking
  to document bugs and minimal failing cases.

- *Why it's useful*: Demonstrates the framework's practical value in finding edge cases and improves
  debugging skills through minimal counterexamples.

- *Skills developed*: Property definition, custom strategy design, and real-world testing application.

- *Difficulty*: Beginner to Intermediate.


