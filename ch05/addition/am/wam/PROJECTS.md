
## Projects on WAM

Here are a few project ideas for working with the Warren Abstract Machine (WAM) that you can try.
These projects will help you explore various aspects of Prolog execution, optimisation,
and enhancement of WAM, as well as deepen your understanding of logic programming.

#### 1. Build a Simple WAM Debugger
- *Goal:* Extend the current WAM with an interactive debugger that provides step-by-step execution.
- *Description:* You can modify the existing 'fetch_execute()' function to allow you to pause the
  execution at any given step. The debugger could display the values of registers, the stack, heap,
  and choice points after each instruction. You could also allow stepping over or skipping instructions,
  which would enable you to track how the interpreter is processing the logic.

#### 2. Implement Tail-Call Optimisation (TCO)
- *Goal:* Add tail-call optimisation to the WAM to avoid excessive memory consumption due to the growth
  of the call stack.
- *Description:* In Prolog, recursive predicates can consume a lot of memory due to the growing call
  stack. Implement a mechanism in WAM that detects tail-recursive calls and reuses the current frame
  in the call stack, effectively eliminating the need for additional memory allocation in the case of
  tail calls.

#### 3. Support for Negation as Failure
- *Goal:* Modify the WAM to handle negation as failure (\+) as in traditional Prolog systems.
- *Description:* Negation as failure is a fundamental part of logic programming. Modify the WAM execution
  model to support this concept, where if a goal fails to unify with any fact or rule, it is considered
  false. Implement a mechanism to backtrack and check for the negation of the goal.

#### 4. Introduce Non-Deterministic Execution (Choice Points)
- *Goal:* Extend the WAM to explicitly manage choice points in non-deterministic predicates.
- *Description:* Non-deterministic predicates allow Prolog programs to explore multiple possibilities.
  Extend the current WAM to handle choice points more efficiently, where each time a predicate fails
  and backtracking occurs, it can "jump" back to the most recent choice point and try an alternative solution.

#### 5. Optimising the WAM for Memory Efficiency
- *Goal:* Modify the WAM to make more efficient use of memory, especially with large programs.
- *Description:* You can focus on optimising the heap and stack management in the WAM. This might involve
  techniques like garbage collection to clean up unused variables, improving stack size management,
  and compressing terms in the heap.

#### 6. Implement a Garbage Collector for the Heap
- *Goal:* Introduce a basic garbage collection system to automatically reclaim memory used by dead
  terms or unreferenced variables.
- *Description:* This project will require you to analyse how terms are stored in the heap and how you
  can detect when certain terms are no longer needed. After identifying unused terms, you can reclaim
  that memory space and defragment the heap to optimise space usage.

#### 7. Implement Type Checking/Inference in WAM
- *Goal:* Add type checking or type inference in the WAM execution model.
- *Description:* In this project, you will enhance the WAM by introducing support for types of terms.
  Each term (constant, variable, or structure) can be assigned a type, and the WAM would enforce that
  the types of terms being unified or operated on are compatible.

#### 8. Add Constraint Logic Programming (CLP) Support
- *Goal:* Extend the WAM to support Constraint Logic Programming (CLP).
- *Description:* CLP extends traditional logic programming by allowing the use of constraints, which are
  logical relations that restrict the values variables can take. In this project, you would implement
  constraints like arithmetic constraints (X + Y = s), logical constraints, and even domain-specific
  constraints in WAM.

#### 9. Create a WAM-Based Query Processor
- *Goal:* Design and implement a simple query processor using WAM.
- *Description:* This project will involve writing an engine that can take a query from a user, translate
  it into WAM code, and then use the WAM interpreter to execute the query and return results. This could
  be a text-based or web-based query interface.

#### 10. Experiment with Memory Models (Heap vs Stack Usage)
- *Goal:* Experiment with the role of the heap and stack in the WAM model and propose optimisations.
- *Description:* In Prolog's execution model, the heap and stack serve different roles in managing
  execution. You can conduct experiments comparing performance and memory usage when using different
  models for storing terms (e.g. deeper usage of the heap versus the stack). You can then analyse
  how Prolog's performance is affected and suggest potential optimisations.

#### 11. Implement Parallel Execution in WAM
- *Goal:* Investigate and implement a parallel execution model for WAM.
- *Description:* This project would explore how WAM can be modified to allow parallel execution of
  independent goals, utilising multiple CPU cores. You would implement a system for managing parallel
  backtracking and independent goals, improving the speed of execution for programs with multiple
  independent goals.

#### 12. Build an Interactive WAM Simulator with GUI
- *Goal:* Create a graphical user interface (GUI) that simulates the execution of WAM.
- *Description:* You could build an interactive tool that visualises the operation of the WAM, showing
  the state of the registers, stack, heap, and call stack in real time as the program runs. The GUI
  could allow users to input Prolog programs, execute them, and observe how the WAM interprets and
  processes them.


### Getting Started

To help you get started, you could break down these ideas into smaller tasks or modules and
try to implement one or more of them gradually. These projects would allow you to explore
various features of Prolog, enhance the WAM model, and add optimisations or extensions to the
existing architecture.

For example, you could begin by adding trace support in the fetch_execute method to track execution
and progress, which would be useful for debugging. Once that's done, you could move on to tail-call
optimisation, which would improve the efficiency of recursive predicates. These projects will als
involve working with the internals of Prolog's backtracking mechanism, heap, and stack management,
giving you a deeper understanding of the language.
