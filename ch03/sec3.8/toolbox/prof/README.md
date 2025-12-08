
## Project

*Make your own profiler, and here is where to start.
We use the previous VM2 as the starting point.*


### Overview

The profiler is designed to monitor and report various aspects of the VM's execution.

1. *Execution time*: It measures the total time taken for the VM to execute its
instructions, as well as the execution time for individual opcodes. This helps identify
which operations consume the most time.

2. *Memory usage*:

- Current memory: It tracks the amount of memory currently allocated for the VM's stack
  and variable storage.

- Peak memory: It records the *maximum* memory usage during the execution, providing insights
  into how memory consumption varies with different workloads.

3. *Execution statistics*:

- Count: The number of times each opcode is executed.

- Time: The cumulative time spent on each opcode, allowing for performance
  optimization by identifying bottlenecks in specific operations.

4. *Stack depth tracking*:

- Current stack depth: It measures the current depth of the stack, reflecting how many
  elements are present at any given time.

- Peak stack depth: It records the maximum depth reached during execution, which can be
  useful for understanding memory usage patterns and optimizing stack operations.


### Details

1. *Data structure*:

- The profiler uses a Profiler struct that holds various fields to track execution time,
  memory usage, opcode statistics, and stack depth.

- Fields include arrays for tracking the start time of opcode executions, cumulative
  execution times, and counts of how many times each opcode has been executed.

2. *Functions*:

- Start and Stop: Functions to start and stop profiling, capturing the start
  and end times.

- Opcode Profiling: Functions to mark the beginning and end of opcode executions,
  updating time and count metrics accordingly.

- Memory Tracking: Functions to track memory allocations and deallocations,
  updating current and peak memory usage.

- Stack Depth: A function to update the current and peak stack depth based on
  the stack pointer (sp).

3. *Integration with VM Operations*:

- The profiler is integrated with VM operations such as push and pop to update stack
  depth dynamically.

- Memory tracking is incorporated within the VM's memory allocation and deallocation
  functions, allowing for accurate tracking of memory usage related to the stack and
  variable storage.

4. *Output Reporting*:

- A print function that summarizes the profiling results, displaying total execution
  time, peak memory usage, peak stack depth, and a detailed breakdown of opcode performance.


### Benefits

- *Performance*: By identifying slow opcodes and memory-intensive operations,
  developers can focus on optimising critical sections of the code.

- *Memory management*: Understanding memory usage patterns helps ensure that the
  VM operates efficiently and can handle larger workloads without running into memory issues.

- *Debugging*: The profiler provides valuable metrics that can assist in debugging
  performance-related issues, enabling developers to identify and rectify inefficiencies in
  the VM's operation.


### P1, P2, P3

The instrumentation of code introduces overhead that affects absolute timing, as observed
in versions `p1`, `p2`, and `p3`. Due to this added overhead, it's essential to focus on
*relative measurements* and analyse percentage differences rather than relying on absolute
timing values for comparison. This approach allows for a more accurate assessment of performance
variations without interference from the overhead introduced by instrumentation.


### Conclusion

This profiler enhances the VM's capabilities by providing detailed performance insights,
making it easier to optimise both execution speed and memory usage. It serves as a powerful
tool for developers looking to refine their virtual machine implementation and ensure it
operates efficiently under various conditions.
