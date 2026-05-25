
## Property-Based Testing Projects for Learning

Below are three project ideas that build on the provided `stats.py` and `shrink.py` code.
Each project asks you to extend the framework, test new properties, or analyse results in
creative ways. You'll work with Python, explore testing concepts, and apply statistical
thinking. Pick a project that excites you, and use the steps to guide your work. Each project
includes optional extensions to dive deeper.


## Project 1: Testing a String Manipulation Function (Beginner-Friendly)

*Goal*: Create a new strategy to generate random strings and test a string manipulation
function using the `StatisticalTestRunner`. Learn how to define properties, generate test
data, and interpret statistical results.

*Why It's Cool*: You'll test a real-world string function (like `str.replace`) and see how
property-based testing can catch edge cases, like empty strings or special characters. The
stats will show you patterns in what makes the function fail or succeed.

*Steps*:
1. *Create a String Strategy*:
   - In `stats.py` or `shrink.py`, add a new `StringStrategy` class that inherits from `Strategy`.
   - Implement the `generate` method to produce random strings using `random.choice` from
     a character set (e.g., `string.ascii_letters` or a custom set like `'abc123'`).
   - Add a parameter for maximum length (e.g., `max_length=50`) and use the `size` parameter
     to control string length dynamically.
   - Example: Generate strings of length 0 to `min(size, max_length)` with random characters.

2. *Define a Property*:
   - Write a property function to test a string method, like `str.replace`. For example:
     ```python
     def prop_replace(s):
         result = s.replace('a', 'b')
         return 'a' not in result  # Property: all 'a's are replaced
     ```
   - Alternatively, test that `s.lower().upper() == s.upper()` (case conversion preserves content).

3. *Run the Test*:
   - In the `if __name__ == "__main__":` block, create a `StatisticalTestRunner` instance and
     call `run_statistical_test` with your `StringStrategy` and property.
   - Use a sample size of 500 and a clear hypothesis, like "Replacing 'a' with 'b' removes all 'a's."
   - Print the results: success rate, confidence interval, and failure patterns.

4. *Analyse Results*:
   - Look at the `distribution_analysis` output. What’s the average string length? Are failures
     linked to specific lengths or characters?
   - If you find failures (e.g., due to a buggy implementation), explain what input caused them.

*Extensions*:
- Add special characters (e.g., `string.punctuation`) to your strategy and see if it reveals new failures.
- Test a custom string function, like one that reverses words in a sentence, and define a property for it.
- Add a new analysis to `_analyze_input` to count specific characters (e.g., how many spaces or digits appear).

*Learning Outcomes*:
- Understand how to create a strategy for random data generation.
- Learn to write properties that capture function behaviour.
- Interpret statistical outputs like confidence intervals and failure patterns.



## Project 2: Adding a Dictionary Strategy and Testing a Data Structure (Intermediate)

*Goal*: Extend the framework to generate random dictionaries and test a dictionary-based
data structure, like a simple key-value cache. Use the shrinking capabilities in `shrink.py`
to minimise failing cases.

*Why It's Cool*: Dictionaries are common in real-world applications, and testing them with
random key-value pairs can uncover bugs in edge cases (e.g., duplicate keys, empty dictionaries).
Shrinking will help you find the smallest input that causes a failure, making debugging easier.

*Steps*:
1. *Create a Dictionary Strategy*:
   - In `stats.py` or `shrink.py`, add a `DictStrategy` class that inherits from `Strategy`.
   - Make it generate dictionaries with random keys (e.g., strings or integers) and values
     (e.g., using `IntegerStrategy` or `StringStrategy`).
   - Use parameters like `max_size` for the number of key-value pairs and compose with other
     strategies for values.
   - Example: Generate a dictionary with 0 to `min(size, max_size)` pairs, where keys are
     strings and values are integers.

2. *Define a Cache Property*:
   - Create a simple cache class with `put(key, value)` and `get(key)` methods. For example:
     ```python
     class SimpleCache:
         def __init__(self):
             self.data = {}
         def put(self, key, value):
             self.data[key] = value
         def get(self, key):
             return self.data.get(key)
     ```
   - Write a property to test the cache, like:
     ```python
     def prop_cache_consistency(d):
         cache = SimpleCache()
         for k, v in d.items():
             cache.put(k, v)
         return all(cache.get(k) == v for k, v in d.items())
     ```

3. *Test with Shrinking*:
   - Update `shrink.py` to ensure `DictShrinker` works with your strategy’s key-value types.
   - Run `StatisticalTestRunner` with your `DictStrategy` and property, using a sample size of 1000.
   - Introduce a deliberate bug in the cache (e.g., `put` sometimes skips updates) to trigger shrinking.
   - Check the `shrunk_counterexamples` in the results to see how the framework minimises failing inputs.

4. *Analyse and Improve*:
   - Look at `shrinking_analysis` to see how many steps it took to shrink failures.
   - Add a new shrinking rule to `DictShrinker` (e.g., try replacing all values with a single value).
   - Check `failure_patterns` to see if failures correlate with dictionary size or key types.

*Extensions*:
- Add support for nested dictionaries in `DictStrategy` and `DictShrinker`.
- Test a more complex data structure, like a priority queue implemented with a dictionary.
- Enhance `_analyze_input` to track key-value type combinations in the distribution analysis.

*Learning Outcomes*:
- Learn to compose strategies for complex data types like dictionaries.
- Understand how shrinking simplifies debugging by finding minimal counterexamples.
- Gain experience with statistical analysis of test inputs and failures.



## Project 3: Statistical Analysis Dashboard with Visualisations (Advanced)

*Goal*: Build a web-based dashboard using Python (with Flask or a simple HTML+JS setup) to
visualise the statistical results from `StatisticalTestRunner`. Display charts for success
rates, input distributions, and shrinking effectiveness.

*Why It's Cool*: You’ll turn raw statistical data into interactive visualisations, making
it easier to understand test results. This combines backend testing with frontend skills,
simulating a real-world testing dashboard.

*Steps*:
1. *Collect Test Data*:
   - Run `StatisticalTestRunner` on the `buggy_sorting_property` from `shrink.py` with
     a sample size of 1000.
   - Save the results (e.g., success rate, confidence interval, distribution analysis,
     shrinking analysis) to a JSON file.
   - Example:
     ```python
     import json
     results = runner.run_statistical_test(buggy_sorting_property, ListStrategy(IntegerStrategy(-10, 10)), 1000)
     with open('test_results.json', 'w') as f:
         json.dump(results, f)
     ```

2. *Create a Web App*:
   - Use Flask (or a simple HTML file with JavaScript) to create a web page.
   - Load the JSON results and display:
     - A bar chart for `type_distribution` (e.g., how many sequences vs. other types).
     - A line chart for success rate with confidence interval bounds.
     - A table summarising `shrinking_analysis` (e.g., average shrink steps, success rate).
   - Use a library like Chart.js (via CDN) for visualisations. Example HTML:
     ```html
     <!DOCTYPE html>
     <html>
     <head>
         <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
     </head>
     <body>
         <canvas id="typeChart"></canvas>
         <script>
             fetch('test_results.json')
                 .then(response => response.json())
                 .then(data => {
                     new Chart(document.getElementById('typeChart'), {
                         type: 'bar',
                         data: {
                             labels: Object.keys(data.distribution_analysis.type_distribution),
                             datasets: [{
                                 label: 'Input Type Distribution',
                                 data: Object.values(data.distribution_analysis.type_distribution)
                             }]
                         }
                     });
                 });
         </script>
     </body>
     </html>
     ```

3. *Enhance Visualisations*:
   - Add a histogram for `size_statistics` (e.g., distribution of list lengths).
   - Show a scatter plot of shrink steps vs. input complexity (from `_estimate_complexity`).
   - Add interactivity, like tooltips showing exact values or filters for failure patterns.

4. *Analyse and Reflect*:
   - Run tests with different properties or strategies and compare visualisations.
   - Write a short report (in Markdown) explaining which visualisations reveal the
     most about test quality (e.g., biased input distributions or ineffective shrinking).

*Extensions*:
- Add real-time test running: Modify the app to run `StatisticalTestRunner` on demand
  via a Flask endpoint.
- Support multiple test runs in the dashboard, comparing their stats side by side.
- Add a visualisation for failure patterns, like a heatmap of failure types vs. input sizes.

*Learning Outcomes*:
- Learn to integrate Python backend testing with web-based visualisations.
- Understand how to present statistical data effectively using charts.
- Gain experience with JSON, web development, and data analysis.



## Tips for Success

- *Start Small*: If you’re new to PBT, begin with Project 1 to get comfortable with
  strategies and properties.
- *Use the Existing Code*: Modify `stats.py` or `shrink.py` directly, but keep backups
  to avoid breaking things.
- *Experiment with Bugs*: Introduce deliberate bugs in your properties or functions
  to see how the framework catches and shrinks them.
- *Ask for Help*: If you’re stuck, share your code and results to get feedback (you can ask me!).
- *Document Your Work*: Add comments or a README section explaining your changes
  and what you learned.

Each project builds on the framework’s strengths--randomised testing, statistical analysis,
and shrinking--while letting you explore Python, testing, and data visualisation.

