
## Excerpt from a User Manual for PL/0

See further:
https://raw.github.com/adamdunson/pl0-compiler/master/doc/PL0%20User%27s%20Manual.pdf


| Error Number | Error Message                                          | Comments/Suggestions                                                                                   |
|--------------|--------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| 0            | No errors, program is syntactically correct.           | N/A                                                                                                    |
| 1            | Use = instead of :=.                                   | You tried to assign a value to a variable                                                              |
| 2            | = must be followed by a number.                        | Syntax error near constant declarations or in a conditional expression.                               |
| 3            | Identifier must be followed by =.                      | Syntax error near constant declarations.                                                               |
| 4            | const, int, procedure must be followed by identifier.  | Syntax error near constant, variable, or procedure declarations.                                       |
| 5            | Semicolon or comma missing.                            | You missed a semicolon or a comma somewhere. Also check that you aren't adding extra semicolons to if-then-else and while-do’s. |
| 6            | Incorrect symbol after procedure declaration.          | Not currently used.                                                                                   |
| 7            | Statement expected.                                    | Not currently used.                                                                                   |
| 8            | Incorrect symbol after statement part in block.       | Not currently used.                                                                                   |
| 9            | Period expected.                                       | Missed a period at the end of the program.                                                             |
| 10           | Semicolon between statements missing.                  | Except for the last one in a block, every statement needs to end with a semicolon.                     |
| 11           | Undeclared identifier.                                 | You tried to use an undeclared constant, variable, or procedure, or you tried to access something that is outside of your scope. |
| 12           | Assignment to constant or procedure is not allowed.    | You tried to assign a value to a constant or a procedure. Check your variable names.                   |
| 13           | Assignment operator expected.                          | You began a statement with an identifier, but it wasn't followed by an assignment operator (:=).        |
| 14           | call must be followed by an identifier.                | You used call, but you didn't include the procedure name.                                               |
| 15           | Call of a constant or variable is meaningless.         | You tried to call a constant or a variable, which is meaningless.                                      |
| 16           | then expected.                                          | if [condition] must be followed by then [statement].                                                   |
| 17           | Semicolon or end expected.                             | Not currently used.                                                                                   |
| 18           | do expected.                                           | while [condition] must be followed by do [statement].                                                  |
| 19           | Incorrect symbol following statement.                  | Not currently used.                                                                                   |
| 20           | Relational operator expected.                          | In a conditional expression, you are missing a relational operator.                                    |
| 21           | Expression must not contain a procedure identifier.    | You cannot use procedures in expressions (since they do not return or represent values).               |
| 22           | Right parenthesis missing.                             | Missing the right parenthesis at the end of a factor.                                                  |
| 23           | The preceding factor cannot begin with this symbol.    | There is something wrong with a factor used in an expression.                                          |
| 24           | An expression cannot begin with this symbol.           | Not currently used.                                                                                   |
| 25           | This number is too large.                              | Code generator exceeded the maximum number of lines of code.                                           |
| 26           | out must be followed by an expression.                 | You used out, but didn't specify anything to output.                                                   |
| 27           | in must be followed by an identifier.                  | You used in, but you didn't specify what variable to assign it to.                                      |
| 28           | Cannot reuse this symbol here.                         | Not currently used.                                                                                   |
| 29           | Cannot redefine constants.                             | Constants cannot be redefined.                                                                         |