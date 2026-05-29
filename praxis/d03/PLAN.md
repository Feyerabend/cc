
## Project Ideas: Building Custom Tools for Debugging, Optimisation, and Testing

This document outlines project ideas inspired by the concepts in Chapter 3 of the book,
focusing on debugging, optimisation, testing, error handling, and the role of LLMs. These
projects allow exploration of foundational programming skills while building practical
tools. They can be tackled individually for focused learning or in groups for collaborative
problem-solving. LLMs (like Grok, Claude, or GitHub Copilot) can assist by generating
code snippets, suggesting hypotheses for bugs, or automating test cases--encouraging a
balance between AI augmentation and hands-on craftsmanship. Each project includes estimated
difficulty (beginner, intermediate, advanced), suggested mode (individual/group),
and LLM integration tips.


### 1. Custom Print Debugger with Logging Enhancements
   - *Description*: Develop a simple debugging tool in C or Python that extends basic
     print statements into a structured logger. Include features like timestamping,
     severity levels (e.g., DEBUG, INFO, ERROR), and file output, drawing from the logging
     techniques in the section on tools. Test it on a sample program with syntax,
     logical, and runtime errors (as described on debugging).
   - *Learning Outcomes*: Understand error types and how logging aids in root cause
     analysis.
   - *Difficulty*: Beginner.
   - *Mode*: Individual (for quick prototyping) or group (to divide features like UI
     for log viewing).
   - *LLM Assistance*: Use an LLM to generate initial code templates or suggest ways
     to handle thread-safe logging for concurrent systems.

### 2. Root Cause Analysis Tool Using Five Whys and Fishbone Diagrams
   - *Description*: Create a Python script or web app that guides users through root
     cause analysis. Input a bug description, and the tool prompts for "Five Whys"
     iterations or generates a visual fishbone diagram (using libraries like Matplotlib
     or Graphviz). Apply it to debug a provided code snippet with a race condition or
     deadlock.
   - *Learning Outcomes*: Practice systematic debugging processes and visualise causes
     for complex bugs.
   - *Difficulty*: Intermediate.
   - *Mode*: Group (one member handles input parsing, another visualisation, and a third
     integration with code examples).
   - *LLM Assistance*: Prompt an LLM to brainstorm potential causes for a given symptom
     or generate diagram structures based on common software issues.

### 3. Basic Profiler for Optimization
   - *Description*: Build a lightweight profiler in C or Python that measures execution
     time and memory usage for functions in a sample program. Include features like
     identifying bottlenecks (e.g., slow loops) and suggesting optimisations such as
     loop unrolling or memory pooling. Test on algorithms like sorting or dynamic
     programming examples.
   - *Learning Outcomes*: Explore optimisation types (compiler, algorithmic, memory)
     and tools like profilers.
   - *Difficulty*: Intermediate.
   - *Mode*: Individual (focus on core metrics) or group (add advanced features like
     GPU acceleration integration).
   - *LLM Assistance*: Ask an LLM to suggest optimized code variants or explain
     profiling results, aligning with LLM-assisted optimisation.

### 4. Automated Unit Testing Framework with Coverage Analysis
   - *Description*: Design a simple testing tool in Python that generates and runs
     unit tests for given functions, incorporating property-based testing or fuzzing
     (mentioned in the chapter's testing section). Include coverage reports and
     integrate with a Makefile for automation. Use it to test error-handling code.
   - *Learning Outcomes*: Master test types (unit, regression) and automation in CI pipelines.
   - *Difficulty*: Intermediate.
   - *Mode*: Group (divide tasks: test generation, execution, and reporting).
   - *LLM Assistance*: Leverage an LLM to auto-generate test cases from function
     descriptions, as highlighted in LLM-assisted testing.

### 5. Distributed System Debugger Simulator
   - *Description*: Simulate a distributed system (e.g., multiple threads or processes
     mimicking microservices) and build a tool to detect race conditions or deadlocks
     using techniques like thread sanitizers or logging correlation. Visualise traces
     with a simple dashboard.
   - *Learning Outcomes*: Tackle challenges in concurrent debugging and observability.
   - *Difficulty*: Advanced.
   - *Mode*: Group (collaborate on simulation, detection algorithms, and visualisation).
   - *LLM Assistance*: Use an LLM for generating example code with intentional bugs
     or suggesting fixes based on simulated error logs.

### 6. Error Handling and Resilience Toolkit
   - *Description*: Create a library in C or Python for defensive programming, including
     input validation, bounds checking, and exception patterns. Add assertions and contracts,
     then test it on a program prone to runtime errors like division by zero.
   - *Learning Outcomes*: Implement preventive debugging through structured error handling.
   - *Difficulty*: Beginner to Intermediate.
   - *Mode*: Individual (build core functions) or group (extend to production features
     like circuit breakers[^cb]).
   - *LLM Assistance*: Prompt an LLM to suggest edge cases or generate contract examples,
     enhancing resilience design.

[^cb]: A circuit breaker is a protective electrical device designed to automatically interrupt current flow when a fault occurs, such as an overload or short circuit. By opening the circuit at the moment unsafe conditions arise, it prevents damage to equipment, reduces fire risk, and protects wiring and connected loads. After the fault is cleared, most circuit breakers can be manually reset, unlike fuses, which must be replaced once blown.

### 7. LLM-Augmented Debugging Chatbot
   - *Description*: Build a simple chatbot (using Python and use a LLM API) that
     takes code snippets, error messages, or stack traces as input and provides
     debugging suggestions, hypotheses, or fixes. Integrate it with a basic IDE
     plugin or command-line tool, drawing from the LLM impact discussion.
   - *Learning Outcomes*: Explore AI literacy, prompt engineering, and balancing
     LLM assistance with manual verification.
   - *Difficulty*: Advanced.
   - *Mode*: Group (one handles API integration, another user interface, and a
     third validation of suggestions).
   - *LLM Assistance*: Ironically, use an LLM to bootstrap the chatbot's logic
     or test its accuracy on sample bugs.

### 8. Production Debugging Dashboard
   - *Description*: Develop a web-based dashboard that aggregates logs, metrics,
     and traces from a simulated production environment (e.g., using Flask or
     Django). Include features for post-mortem analysis like core dump inspection
     or log correlation.
   - *Learning Outcomes*: Understand observability pillars and remote debugging
     techniques.
   - *Difficulty*: Advanced.
   - *Mode*: Group (divide into backend data collection, frontend visualisation,
     and analysis features).
   - *LLM Assistance*: Use an LLM to analyze simulated logs for patterns or
     generate incident response reports.

### Tips for All Projects
- *Evaluation*: For each project, include a README with usage instructions,
  test results, and reflections on challenges (e.g., how LLMs helped or hindered).
- *Extensions*: Scale projects by adding hardware elements (e.g., Raspberry Pi
  Pico debugging) or integrating with version control.
- *Ethical Considerations*: When using LLMs, verify outputs to avoid hallucinations,
  and discuss privacy implications in group reflections.

