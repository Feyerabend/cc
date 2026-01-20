
## ISSUES!!

* Memory Management: Inconsistent use of strdup, manual tracking of temporaries,
  potential memory leaks
* Error Handling: Uses exit() throughout instead of proper error propagation
* Global State: Heavy reliance on global variables (tokens array, TAC lists, symbol tables)
* Code Duplication: Lots of repeated patterns (token handling, AST traversal)
* Separation of Concerns: Parser and AST generation are tightly coupled
* Type Safety: No structured error types, magic numbers for type IDs
* Testing: Hard to unit test due to global state and side effects

