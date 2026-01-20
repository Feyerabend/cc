
## Simple Semantics


### Sample no 1. (simple_semantics.py)

#### Symbol Table Management
- Tracks variables with name, type, scope, and memory location
- Detects redeclarations in the same scope
- Manages multiple scopes (global and local)

#### Type Checking
- Validates binary operations (arithmetic, comparison)
- Ensures type compatibility in assignments
- Allows safe type promotions (int -> float)

#### Scope Checking
- Detects undefined variables
- Verifies variables are used in accessible scopes
- Implements scope hierarchy (local -> global lookup)

#### Sample Programs
- `+` Valid program
- `-` Redeclaration error
- `-` Type mismatch error
- `-` Undefined variable error
- `+` Scope example

The program uses a simple dictionary-based representation where each statement is
a dict with a "type" field. The analyser processes statements sequentially, building
the symbol table and checking for semantic errors.


### Sample no 2. (simple_semantics2.py)

#### Function Verification
- Function declarations and definitions
- Parameter count checking
- Parameter type checking
- Return type tracking
- Preventing duplicate function names

#### Control Flow Analysis
- Unreachable code detection (code after return)
- All-paths-return verification
- Break/continue outside loops detection
- Infinite loop warnings
- If-else branch analysis

#### Sample Programs
- `+` Valid function with correct call
- `-` Wrong argument types
- `-` Missing return on some paths
- `-` Unreachable code warning
- `-` Break outside loop
- `+` All paths return correctly


The program shows function verification: wrong types, wrong number of args.
Further more control flow: unreachable code, missing returns. We also iterate
some scope checking: break/continue only in loops.

