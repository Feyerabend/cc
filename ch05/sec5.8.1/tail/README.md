
## Tail Recursion

Tail recursion is a form of recursion where the recursive call is the last operation
in a function before returning a result. This means that once the recursive call is
made, there is no need to retain any previous state, as there are no pending operations
to perform. Because of this property, some programming languages and compilers can optimise
tail-recursive functions by reusing the same stack frame instead of creating a new one
for each recursive call. This optimisation, known as tail call optimisation (TCO), allows
tail-recursive functions to execute with constant memory usage, making them as efficient
as loops in terms of space complexity. Tail recursion is particularly useful in cases
where deep recursion would otherwise lead to stack overflow, and it encourages an iterative
approach within a recursive structure by passing accumulated results through function parameters.

