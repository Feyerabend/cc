
### Metamorphic Testing

The provided Python script (`mmorph.py`) implements a *Metamorphic Testing Framework* in Python.
Metamorphic testing is an advanced software testing technique that *doesn't* rely on predefined
"oracle" outputs (i.e., exact expected results for every input). Instead, it defines
*metamorphic relations*—properties or relationships that should hold true between multiple
executions of a function on related (transformed) inputs. If these relations are violated,
it indicates a potential bug in the function under test.

This framework is particularly useful for testing complex systems where:
- Computing the correct output independently is difficult or impossible
  (e.g., machine learning models, optimisation algorithms, or non-deterministic functions).
- Traditional unit tests with fixed input-output pairs are insufficient or hard to create.
- You want to automate property-based testing that explores a wide range of inputs.

The code is structured modularly, with base classes for data generation strategies,
metamorphic relations, and a test suite. It includes examples demonstrating its application
to sorting algorithms, mathematical functions (like square root and logarithm), and
string processing.

#### 1. *Data Generation Strategies (Strategy Classes)*
   These are used to create random test inputs of varying complexity. They support gradual
   scaling of input size/complexity during testing.
   - `Strategy`: Base abstract class.
   - `IntegerStrategy`: Generates random integers in a range (e.g., -50 to 50).
   - `FloatStrategy`: Generates random floats in a range (e.g., 0.1 to 100.0).
   - `ListStrategy`: Generates lists of elements using another strategy, with optional min/max sizes.
   - `TupleStrategy`: Generates tuples with elements from multiple strategies.
   - Custom example: `StringStrategy` (in the main block) for generating random strings.

   These strategies use Python's `random` module (seeded for reproducibility) and can
   generate increasingly complex inputs (e.g., longer lists as tests progress).

#### 2. *MetamorphicRelation Class*
   This core class defines a single metamorphic property:
   - *Input Transform*: A function that modifies the original input (e.g., shuffling a
     list or scaling a number).
   - *Output Relation*: A checker that verifies if the function's outputs on the original
     and transformed inputs satisfy the expected relationship (e.g., sorted outputs should
     be equal for permutations).
   - `test` Method: Runs the function on both inputs and checks the relation. It catches
     exceptions as failures.

   Some relations are subclassed for custom testing logic (e.g., `SqrtScalingRelation`
   and `LogAdditionRelation` handle multi-input scenarios).

#### 3. *MetamorphicTestSuite Class*
   Manages a collection of `MetamorphicRelation` objects and runs tests:
   - `add_relation`: Adds a relation to the suite.
   - `test_function`: Tests a given function using a provided strategy for input generation.
     - Runs a specified number of tests (default: 100).
     - Tracks success rates, failures, and sample failing inputs.
     - Prints progress and failures during execution.
   - Returns a dictionary of results per relation (e.g., success rate, total tests, number
     of failures, sample failures).

#### 4. *Predefined Test Suites (Factory Functions)*
   These create ready-to-use suites for specific domains:
   - `create_sorting_metamorphic_suite`: For sorting functions. Relations include:
     - Permutation Invariance: Sorting any shuffle of a list yields the same result.
     - Same Elements Property: Sorted output has the same elements as input.
     - Duplication Property: Sorting a duplicated list yields a correctly duplicated sorted list.
     - Subset Property: Adding elements preserves the original sorted elements as a subset.
   - `create_mathematical_metamorphic_suite`: For math functions like sqrt and log.
     - Square Root Scaling: `sqrt(k² * x) ≈ k * sqrt(x)` for positive k.
     - Logarithm Addition: `log(a) + log(b) ≈ log(a * b)`.
   - `create_string_metamorphic_suite`: For string functions.
     - Case Insensitive Property: Case-swapping input shouldn't affect lowercase-normalized output.
     - Whitespace Normalization: Adding whitespace shouldn't affect stripped output.

#### 5. *Example Test Functions*
   - `correct_sort`: A correct implementation using Python's `sorted`.
   - `buggy_sort`: A flawed implementation that mishandles duplicates (uses `remove` which
     only removes the first occurrence).
   - `safe_sqrt` and `safe_log`: Handle negative inputs gracefully using `abs` and small offsets.
   - `simple_upper`: Converts input to uppercase.

#### 6. *Main Demonstration Block*
   - Runs tests on the correct and buggy sorters, showing how the framework detects bugs
     (e.g., low success rates for buggy sort on duplication).
   - Tests math and string functions.
   - Prints formatted results, including success rates and failure examples.
   - Ends with a summary highlighting the framework's strengths.

The code also includes a comment block at the end explaining metamorphic testing conceptually.


### Use Cases and How to Use It

This framework is designed for *automated bug detection* in software development, especially
for algorithms where absolute correctness is hard to verify. It's an extension of property-based
testing (like Hypothesis in Python) but focuses on relational properties.

#### Basic Usage Steps

1. *Define a Strategy*: Choose or create one to generate inputs for your function (e.g.,
   `ListStrategy(IntegerStrategy(-10, 10))` for lists of integers).

2. *Create or Use a Suite*: Use a factory like `create_sorting_metamorphic_suite()` or
   build your own by adding custom `MetamorphicRelation` objects.

3. *Run Tests*: Call `suite.test_function(your_function, strategy, num_tests=50)`.

4. *Analyze Results*: Check the returned dict for success rates. Low rates or failures
   indicate bugs—inspect sample failing inputs for debugging.

5. *Extend It*: Add new relations for your domain (e.g., for a search algorithm:
   "Adding irrelevant items shouldn't change top results for a query").


#### Example from the Code
```python
sorting_suite = create_sorting_metamorphic_suite()
results = sorting_suite.test_function(buggy_sort, ListStrategy(IntegerStrategy(-10, 10)), num_tests=30)
# Results will show failures in "Duplication Property" due to the bug.
```

#### Benefits
- *No Oracle Needed*: Tests rely on relative properties, not absolute outputs.
- *Scalable*: Handles increasing input complexity and random generation for broad coverage.
- *Detects Subtle Bugs*: As shown, it catches issues like duplicate handling in sorting.
- *Versatile*: Applicable to various domains (sorting, math, strings, and extensible to
  others like ML models or databases).
- *Reproducible*: Uses a fixed random seed (42) for consistent results.

#### Limitations (Project Ideas)
- Relies on well-defined relations; poor ones may miss bugs or produce false positives.
- Exceptions are treated as failures, which might mask non-bug issues.
- Input generation is capped for practicality (e.g., list size up to 20).
- Not thread-safe or optimised for very large-scale testing.

