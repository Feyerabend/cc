import re
import numpy as np
from scipy.stats import norm, beta

def parse_log(file_path):
    counts = {}
    times = {}
    errors = {'Division By Zero': 0, 'Invalid Operation': 0}
    
    with open(file_path, 'r') as file:
        lines = file.readlines()
        reading_times = False
        for line in lines:
            # Parse operation counts
            if line.startswith('Operation Counts:'):
                reading_times = False
                continue
            if line.startswith('Execution Times:'):
                reading_times = True
                continue
            if line.startswith('Error Counts:'):
                break  # Errors are at the end

            if not reading_times:
                match = re.match(r"(\w+): (\d+)", line)
                if match:
                    operation, count = match.groups()
                    counts[operation] = int(count)
            else:
                match = re.match(r"(\w+): ([0-9.]+) seconds", line)
                if match:
                    operation, time = match.groups()
                    times[operation] = float(time)

        # Parse error counts
        for line in lines[-2:]:
            match = re.match(r"(.+): (\d+)", line)
            if match:
                error_type, count = match.groups()
                errors[error_type] = int(count)
    
    return counts, times, errors

def analyze_execution_times(times):
    baseline_time = np.mean(list(times.values()))
    std_dev = np.std(list(times.values()))

    results = {}
    for op, time in times.items():
        prob_slow = 1 - norm.cdf(time, baseline_time, std_dev)
        results[op] = {
            'mean_time': time,
            'prob_slow': prob_slow
        }
    return results

# estimate probability of errors using beta distribution
def analyze_error_probabilities(errors, prior_alpha=1, prior_beta=99):
    posteriors = {}
    for error_type, count in errors.items():
        alpha = prior_alpha + count
        beta_val = prior_beta + (1 - count)
        posteriors[error_type] = beta(alpha, beta_val).mean()
    return posteriors

def main(log_file="log.txt"):
    counts, times, errors = parse_log(log_file)
    header_diag()
    header_analysis()
    print("=== Bayesian Analysis of Execution Times ===")
    execution_analysis = analyze_execution_times(times)
    for op, data in execution_analysis.items():
        print(f"Operation {op}: Mean time = {data['mean_time']:.6f} seconds, P(slow) = {data['prob_slow']:.4f}")
    
    print("\n=== Bayesian Analysis of Error Probabilities ===")
    error_analysis = analyze_error_probabilities(errors)
    for error_type, prob in error_analysis.items():
        print(f"Error {error_type}: Estimated Probability = {prob:.4f}")

def header_analysis():
        # Print description header for the analysis output
    print("""
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
""")

def header_diag():

    print("""
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
""")

if __name__ == "__main__":
    main()