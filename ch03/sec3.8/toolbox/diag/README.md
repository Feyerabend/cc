
## Building Tools: Post-Mortem Diagnostics

Here, we have one of the tools in our toolkit designed for post-mortem analysis. We execute a program on
the structure from our earlier virtual machine, and as a result, we obtain a log detailing what occurs
during the run at specific points.

A shell script provides insights into what is happening:

```shell
#!/bin/sh
clear
python3 dvm.py --input sample.b > log.txt
python3 diag.py < log.txt
```

The virtual machine has been modified with the insertion of logging instructions. The core of the operation,
however, takes place within the diagnostics.

The program 'diag.py' is a diagnostic and analysis tool designed to process the log file containing performance
and error metrics. Its purpose is to parse the log, analyze the data, and present insights into the execution
times, operation frequency, and error probabilities.

It gives you:
1. Insights into performance: By identifying slow operations (developers can optimise the code).
2. Error prioritization: By quantifying error probabilities, resources can be allocated to fixing the most critical issues.
3. Statistical rigor: Bayesian techniques enable principled probabilistic reasoning, accommodating uncertainty and prior knowledge.


### Output

The program organizes its output into diagnostic summaries and analyses:
- Diagnostic Summary: Provides a snapshot of key metrics like operation counts, execution times, and error frequencies.
- Bayesian Analysis of Execution Times: Highlights average execution times and probabilities of slowness for each operation,
  drawing attention to underperforming operations.
- Bayesian Analysis of Error Probabilities: Estimates probabilities for each error type, supporting a data-driven approach
  to error mitigation.

A sample of output on screen:

```shell
====================================
          Diagnostic Summary
====================================

- Operation Counts: Frequency of each
operation encountered during execution,
indicating how central an operation
type is to the code being analyzed.

- Execution Times: Mean execution
time per operation in seconds,
identifying potential performance
bottlenecks.

- Error Counts: Frequency of errors
like division by zero or invalid
operations, offering a measure
of VM stability.


====================================
Bayesian Analysis of Execution Times
====================================

- Mean Time:
Average time (seconds) taken by each
operation, providing a baseline for
performance assessment.

- P(slow):
Probability that an operation's
execution time exceeds the expected
threshold ("slow"). High values
here can point to performance
bottlenecks that may need
optimisation.

=== Bayesian Analysis of Execution Times ===
Operation CALL: Mean time = 0.000008 seconds, P(slow) = 0.8568
Operation EQ: Mean time = 0.000010 seconds, P(slow) = 0.8336
Operation JPZ: Mean time = 0.000015 seconds, P(slow) = 0.7654
Operation LD: Mean time = 0.000066 seconds, P(slow) = 0.0382
Operation LDARG: Mean time = 0.000019 seconds, P(slow) = 0.7012
Operation LOAD: Mean time = 0.000019 seconds, P(slow) = 0.7012
Operation MUL: Mean time = 0.000020 seconds, P(slow) = 0.6840
Operation PRINT: Mean time = 0.000003 seconds, P(slow) = 0.9051
Operation RET: Mean time = 0.000028 seconds, P(slow) = 0.5348
Operation SET: Mean time = 0.000066 seconds, P(slow) = 0.0382
Operation ST: Mean time = 0.000062 seconds, P(slow) = 0.0574
Operation STARG: Mean time = 0.000035 seconds, P(slow) = 0.3993
Operation STORE: Mean time = 0.000034 seconds, P(slow) = 0.4183
Operation SUB: Mean time = 0.000032 seconds, P(slow) = 0.4568

=== Bayesian Analysis of Error Probabilities ===
Error Division By Zero: Estimated Probability = 0.0099
Error Invalid Operation: Estimated Probability = 0.0099
```

In short we have:

- Operation counts: Frequency of specific operations, indicating their usage (or importance).

- Execution times: Average time taken for each operation, useful for identifying performance bottlenecks.

- Error counts: Frequency of specific errors, like "Division By Zero" or "Invalid Operation," offering
  insights into system stability and robustness.


### Analysis of "Execution Times"

Using statistical methods, this component:

1.	Baseline: Computes the average execution time for all operations to establish a performance baseline.

2.	Standard Deviation: Measures the variability of execution times.

3.	Probability of Slowness: For each operation, calculates the probability of being “slow” (execution
    time significantly exceeding the baseline). This is derived using the cumulative distribution function
    (CDF) of a normal distribution, treating the baseline as the *mean* and the standard deviation as *spread*.

This analysis identifies operations that are potential bottlenecks and need optimization, which can be used
for performance tuning.

There are limitations to the static Baseline: It assumes the mean execution time provides a meaningful baseline,
which may not always hold in systems with dynamic workloads.


### Analysis of "Error Probabilities"

The program uses Bayesian methods to estimate error probabilities. It models errors using a *Beta distribution*,
which is well-suited for probabilities because it allows for updating beliefs (posterior probabilities) based
on observed data (error counts) and prior assumptions:

- Prior Parameters: Defaults to Alpha=1 and Beta=99, reflecting an assumption that errors are rare.

- Posterior Parameters: Updates the prior based on observed counts, producing a posterior mean for each error type.

This provides an estimated probability for each error, helping to gauge their relative prevalence and prioritise
mitigation efforts.

There are limitations of the error model: The Beta distribution may not accurately model all
error scenarios, particularly if errors exhibit complex dependencies.

