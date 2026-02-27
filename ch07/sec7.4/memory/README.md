
### Memory & State Management

| Mechanism | Description | Use Cases | Related Pattern(s) |
|-----------|-------------|-----------|--------------------|
| [Checkpoint](./checkpoint/) | Save program state to resume from that point | Backtracking, recovery systems, interpreters | Memento, Recovery |
| [Stack Frame](./frame/) | Local storage for function calls | Recursion, coroutines, nested procedures | Call stack convention |
| [Backtracking](./backtrack/) | Reverting to previous states on failure | Logic programming, constraint solving | Search tree, trail stack |

Memory mechanisms like backtracking, checkpoints, and stack frames are fundamental
concepts that help manage program execution flow and state.

Backtracking is an algorithmic technique that builds solutions incrementally by trying
options, abandoning them ("backtracking") when they fail, and trying alternatives. When
reaching a dead end in solving a problem, the algorithm undoes recent decisions and
explores different paths. Its core principle is essentially "try, fail, undo, try something else."
From a memory perspective, this requires keeping track of decision points and unexplored
alternatives. You can see backtracking at work in solving puzzles like Sudoku, maze navigation,
and constraint satisfaction problems.

Checkpoints save a program's complete state at specific points in execution. They work by
capturing all relevant state information, including variable values and execution position,
at strategic points throughout program execution. The core purpose of checkpoints is to
enable returning to a known good state if errors occur later in the program flow. The memory
aspect involves storing a snapshot of program state that can be restored when needed. Common
examples include database transactions, game save points, and system restore points in
operating systems.

Stack frames organise program execution in memory, particularly for function and procedure
calls. Each time a function is called, the system creates a dedicated memory region for that
function call. This stack frame contains the function's local variables, the return address
to jump back to when the function completes, parameter values passed to the function, and
saved register values. The core purpose of stack frames is to maintain separate execution
contexts for nested function calls. From a memory perspective, stack frames organise the
program's call hierarchy in memory. Every programming language with function or procedure
calls uses stack frames in some form.

These mechanisms work together to create robust program flow. Stack frames naturally enable
a form of backtracking because the call stack records the path of execution, making it possible
to "unwind" to previous decision points. When function call history isn't enough, checkpoints
supplement stack frames by providing complete state capture that can be restored.

Many algorithms combine these mechanisms in hybrid approaches. They use stack frames for
normal function calls, create explicit checkpoints at critical decision points, and implement
backtracking logic to explore alternative paths when solutions aren't immediately found.

Exception handling in modern programming languages uses stack unwinding, which is a form
of backtracking, when errors occur. The system traces back through the stack frames to find
appropriate error handling code. Database systems employ transactions with checkpoints and
rollback mechanisms to ensure data integrity. Recursive algorithms rely heavily on stack
frames to track nested function calls and maintain the correct state at each level of recursion.

Game development utilises checkpoints for save points and often employs backtracking algorithms
for AI pathfinding. Debugging tools leverage stack frames to show call history and use checkpoints
for state inspection, allowing developers to understand how a program reached a particular state.

These memory mechanisms form the backbone of how programs manage execution flow, handle errors
gracefully, and explore complex solution spaces efficiently. While they serve different primary
purposes, their underlying connection is the management of program state and execution context,
allowing programs to navigate complex paths of execution while maintaining appropriate context.
