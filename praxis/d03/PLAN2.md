
## Expanded Project Ideas: Building Custom Tools for Debugging, Optimisation, and Testing

This expanded document builds on the initial set of project ideas, incorporating additional
concepts like static analysis, benchmarking, test-driven development (TDD), documentation
as a debugging aid, and production debugging challenges. These projects encourage you to
deeper exploration of the chapter's themes, such as root cause analysis, concurrent system
debugging, and LLM integration. They can be approached individually for personal skill-building
or in groups for collaborative debugging and iteration. LLMs can provide code suggestions,
bug hypotheses, or test generation, but always verify outputs to maintain craftsmanship.
Each project includes estimated difficulty (beginner, intermediate, advanced), suggested
mode (individual/group), and LLM integration tips.


### 9. Static Analysis Tool for Code Quality
   - *Description*: Create a Python-based static analyzer that scans C or Python code for
     common issues like syntax errors, unused variables, or potential race conditions,
     using libraries like pylint or custom rules. Integrate it with a checklist for
     anti-patterns (inspired by code review sections). Apply it to sample code with
     logical errors.
   - *Learning Outcomes*: Learn about static analysis benefits for catching errors
     pre-runtime and its role in peer debugging (from the chapter's static analysis
     discussion).
   - *Difficulty*: Intermediate.
   - *Mode*: Individual (focus on rule implementation) or group (add support for
     multiple languages and custom checklists).
   - *LLM Assistance*: Prompt an LLM to generate example anti-patterns or suggest
     fixes for detected issues, tying into LLM-assisted debugging.

### 10. Benchmarking Tool for Performance Optimization
   - *Description*: Build a tool in Python that runs benchmarks on code snippets,
     establishing baselines, measuring statistical significance, and detecting
     performance regressions (e.g., using timeit or perf). Test it on optimisation
     scenarios like algorithmic improvements or I/O buffering.
   - *Learning Outcomes*: Understand benchmarking pitfalls and how to measure
     optimisations effectively, including micro-benchmarking (from the benchmarking
     section).
   - *Difficulty*: Intermediate.
   - *Mode*: Group (one handles metrics collection, another visualisation of results
     like graphs).
   - *LLM Assistance*: Use an LLM to interpret benchmark results or propose alternative
     code versions for comparison, enhancing iterative auto-optimisation.

### 11. TDD Workflow Simulator with Debugging Integration
   - *Description*: Develop a script or app that enforces the Red-Green-Refactor
     TDD cycle: generate failing tests, implement code to pass them, and refactor
     while checking for bugs. Include debugging hooks like breakpoints during
     refactoring. Use it on a simple program with evolving requirements.
   - *Learning Outcomes*: Explore how TDD reduces debugging needs and influences
     design (from the TDD cross-references).
   - *Difficulty*: Beginner to Intermediate.
   - *Mode*: Individual (build the core cycle) or group (add features like automated
     refactoring suggestions).
   - *LLM Assistance*: Ask an LLM to generate initial failing tests or refactor code
     snippets, aligning with LLM-assisted testing.

### 12. Documentation Generator as a Debugging Aid
   - *Description*: Create a tool in Python (using libraries like Sphinx or Doxygen)
     that auto-generates API docs from code comments, including design decision
     records. Add features to flag undocumented code sections that could lead to
     integration bugs.
   - *Learning Outcomes*: See how self-documenting code and records aid in understanding
     system behavior and debugging (from the documentation section).
   - *Difficulty*: Beginner.
   - *Mode*: Group (divide into parsing, generation, and validation components).
   - *LLM Assistance*: Leverage an LLM to draft docstrings or explain undocumented code,
     supporting conversational workflows in debugging.

### 13. Live System Debugger for Simulated Production
   - *Description*: Simulate a production environment (e.g., with Docker containers)
     and build a tool for non-disruptive debugging: log analysis, remote inspection,
     and A/B testing for issues. Include metrics for live monitoring.
   - *Learning Outcomes*: Address production challenges like live debugging without
     disruption and log correlation.
   - *Difficulty*: Advanced.
   - *Mode*: Group (collaborate on simulation setup, tool features, and testing scenarios).
   - *LLM Assistance*: Prompt an LLM to analyse simulated logs or suggest A/B test
     hypotheses, extending LLM hypothesis generation.

### 14. Fuzz Testing Tool for Robustness
   - *Description*: Implement a basic fuzzer in Python that generates random inputs
     to test code resilience, focusing on runtime errors or crashes. Integrate with
     property-based testing libraries like Hypothesis and apply to functions with
     potential vulnerabilities.
   - *Learning Outcomes*: Practice fuzz and property-based testing for uncovering
     edge cases (from the testing expansions).
   - *Difficulty*: Intermediate.
   - *Mode*: Individual (core fuzzing logic) or group (add support for different
     input types like networks or files).
   - *LLM Assistance*: Use an LLM to generate diverse fuzz inputs or interpret
     crash reports, boosting automated test generation.

### 15. Hardware Debugging Interface for Embedded Systems
   - *Description*: Create a simple UART-based debugger for a simulated or real
     microcontroller (e.g., Raspberry Pi Pico), including LED toggling for state
     indication and serial logging. Test on embedded code with timing issues.
   - *Learning Outcomes*: Understand hardware debugging challenges and tools like
     serial ports.
   - *Difficulty*: Advanced.
   - *Mode*: Group (one handles hardware setup, another software interface, and
     a third testing).
   - *LLM Assistance*: Ask an LLM for code snippets on UART communication or to
     debug simulated hardware faults.

## Tips for All Projects
- *Evaluation*: In your README, include not just usage and results, but also a
  post-mortem analysis on what went wrong and how you debugged it.
- *Extensions*: Incorporate concurrency (e.g., multithreading in tools) or scale
  to distributed setups. For LLM-heavy projects, track "hallucination" rates
  and mitigation strategies.
- *Ethical Considerations*: When using LLMs, discuss biases in generated code
  or tests. In group work, assign roles for AI verification to ensure balanced
  skill development.
- *Integration Ideas*: Combine projects, e.g., add static analysis to the TDD
  simulator or benchmarking to the production debugger, for a comprehensive toolkit.


