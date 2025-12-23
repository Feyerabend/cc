
### Project 1: Add Comprehensive Documentation and Comments

*Description:* The current code lacks detailed comments and explanations,
making it harder for others (or future you) to understand and maintain.
You can document the entire codebase, including inline comments, a README,
and possibly generated docs.

*Goals:*
- Make the code more readable and explainable.
- Cover key components like the parser, compiler, code generator, and CLI.

*Suggested Steps:*
1. Go through each major section (e.g., PARSER, COMPILER, CCodeGen class)
   and add inline comments explaining what each function or class does,
   its inputs/outputs, and any assumptions.
2. Add docstrings to classes and methods, using a format like Google or
   NumPy style for consistency.
3. Create a README.md file that includes: an overview of Ferrite, how to
   use the compiler, example Ferrite code snippets, and a high-level
   architecture diagram (you can use tools like Draw.io for this).
4. Optionally, use a tool like Sphinx or pdoc to generate HTML documentation
   from the code.
5. Test by sharing the documented code with someone unfamiliar
   and getting feedback on clarity.

*Potential Challenges:*
- Balancing brevity with detail--avoid over-commenting obvious code.
- Ensuring documentation stays in sync with future changes
  (consider using a git hook for reminders).


### Project 2: Implement Unit and Integration Tests

*Description:* The compiler doesn't have any tests, so you can't easily
verify if it works correctly or catch regressions. You can add tests to
check parsing, compilation, and output C code behavior.

*Goals:*
- Ensure the compiler does what it's supposed to (e.g., correct parsing
  of S-expressions, ownership handling, C code generation).
- Cover edge cases like invalid input, moved values, or complex structs.

*Suggested Steps:*
1. Use Python's unittest or pytest framework--install pytest if needed
   (though the code execution tool notes no pip installs, you can assume
   a local setup for this project).
2. Write unit tests for individual functions: e.g., test `parse_program`
   with valid/invalid Ferrite code strings, asserting expected AST output
   or ParseError raises.
3. Add integration tests: Compile sample Ferrite files to C, then use
   subprocess to compile the C with gcc and run it, checking stdout/stderr
   against expected results.
4. Test specific features like borrowing (e.g., ensure errors for using
   moved values) and pattern matching in `match`.
5. Aim for 70-80% code coverage using a tool like coverage.py.
6. Bonus: Set up CI with GitHub Actions to run tests automatically.

*Potential Challenges:*
- Creating diverse test cases for ownership rules without overcomplicating the test suite.


### Project 3: Extend the Language with New Built-in Types and Operators

*Description:* Ferrite currently supports basic types like i32 and structs,
but you can add more features like strings, booleans, or floating-point
numbers to make it more versatile.

*Goals:*
- Enhance the language's expressiveness while maintaining Rust-like ownership semantics.
- Update the parser, type system, and code generator accordingly.

*Suggested Steps:*
1. Add a new type, e.g., "f64" for doubles: Modify `parse_type` to recognise it,
   update `Type.to_c()` to map to "double", and handle it in expressions like arithmetic ops.
2. Introduce boolean support: Add "bool" type, parse true/false literals,
   and support logical operators (&&, ||, !) in the compiler's ops dict.
3. For strings, add a "str" type (map to char* in C), with literals like "hello",
   and ops like concatenation.
4. Update `compile_expr` to handle these in binary ops, if statements, etc.
5. Write example Ferrite programs using the new features and compile/test them.
6. Ensure ownership works (e.g., borrowing strings without copying).

*Potential Challenges:*
- Managing memory for new types like strings (e.g., avoiding leaks in generated C,
  in many ways the thing we want to avoid).
- Backwards compatibility--test that existing features don't break.


### Project 4: Improve Static Checking for Ownership and Lifetimes

*Description:* The current ownership system is basic (tracks moved values, borrowing),
but you can strengthen it with more robust static checks, like preventing use-after-move
or enforcing lifetime rules more strictly.

*Goals:*
- Make the compiler catch more errors at compile time, aligning with the purpose of static checking for safety.
- Explore and implement alternatives to the current enum-based Ownership model.

*Suggested Steps:*
1. Enhance the existing system: In `compile_expr`, add more checks for moved
   variables (e.g., flag errors if a borrowed ref outlives its owner).
2. Introduce basic lifetime analysis: Track lifetimes in scopes and error if
   a ref's lifetime doesn't match its use.
3. As an alternative approach, experiment with a different static checking
   method--e.g., use a graph-based analysis (build a dependency graph of
   variables and check for cycles or invalid paths) instead of the current Scope/Var lookup.
4. Compare alternatives: Implement a prototype using a library like networkx
   (available in the code execution env) to model variable lifetimes as nodes/edges,
   then validate against the current method.
5. Add error reporting: Instead of just appending to self.errors, pretty-print
   them with line numbers from the source.
6. Test with programs that intentionally violate rules and ensure errors are caught.

*Potential Challenges:*
- Avoiding false positives in lifetime checks.
- Performance for complex programs (keep analysis linear time if possible).


### Project 5: Add Advanced Language Features Like Loops or Generics

*Description:* Ferrite lacks control flow beyond if/match, so you can extend
it with loops (while/for) or basic generics for reusable structs/functions.

*Goals:*
- Make the language more practical for real programs.
- Handle new syntax in parsing and compilation while preserving safety.

*Suggested Steps:*
1. Add a "while" loop: Update `parse_sexp` to recognize (while cond body),
   then in `compile_expr`, generate C while loops with cond evaluation and body compilation.
2. For generics, allow type parameters in defstruct/defn, e.g., (defstruct List<T> (head T)
   (tail &List<T>)). Modify `parse_type` to handle params, and instantiate them during compilation.
3. Update codegen to produce templated C (using macros or duplicated code for simplicity).
4. Add pattern matching for loops if needed (e.g., for iterating lists).
5. Write sample programs, like a list summation loop, and verify the generated C runs correctly.
6. Document the new syntax in a language spec file.

*Potential Challenges:*
- Parsing nested generics without ambiguity.
- Ensuring generics don't complicate ownership (e.g., borrowed generic types).


### Project 6: Explore Alternatives to the Current Static Checking Approach

*Description:* Beyond improving the existing system, you can research and
prototype entirely different ways to achieve similar safety goals
(e.g., ownership without borrowing).

*Goals:*
- Understand trade-offs in compiler design.
- Implement a small alternative and compare it to Ferrite's approach.

*Suggested Steps:*
1. Research alternatives: Look into garbage collection (e.g., via Boehm GC in C)
   as a runtime alternative to static ownership, or affine types (use-once variables) instead of borrow/own.
2. Prototype one: Fork the compiler and replace Ownership with affine
   tracking--mark variables as "consumed" after use, error on reuse.
3. Use the browse_page or web_search tools (if needed) to find resources
   on "affine types in compilers" or "alternatives to Rust ownership."
4. Compare: Write the same Ferrite program in both versions, measure generated
   C size/runtime, and note pros/cons (e.g., affine might simplify code but limit expressiveness).
5. Document findings in a report, including code snippets.

*Potential Challenges:*
- Integrating runtime alternatives without bloating the generated C.
- Balancing safety with usability in the alternative system.

These projects build progressively on the Ferrite code, starting from low-risk
(documentation/testing) to high-impact (language extensions).

