
## Tiny C Compiler with CFG-Based Optimisation

A complete, small C compiler that demonstrates Control Flow Graph (CFG)
construction and optimisation techniques. The compiler translates a subset
of C into optimised C code (self-hosting approach).


#### Language Features
- Integer variables and arithmetic (`+`, `-`, `*`, `/`)
- Comparisons (`<`, `<=`, `>`, `>=`, `==`, `!=`)
- Control flow: `if/else`, `while` loops
- Functions with parameters and return values
- Comments (`//`)

#### Compiler Pipeline
1. *Lexical Analysis* - Tokenizes source code
2. *Parsing* - Builds Abstract Syntax Tree (implicit)
3. *IR Generation* - Generates three-address code
4. *CFG Construction* - Builds Control Flow Graph with basic blocks
5. *Optimisation* - Multiple optimisation passes
6. *Code Generation* - Emits C code

#### Optimisations Implemented So Far

1. Constant Folding
Evaluates constant expressions at compile time:
```c
int x = 5 + 3;  // Becomes: int x = 8;
```

2. Dead Code Elimination
Removes unreachable blocks and unused computations:
```c
int dead_var = 5 + 3;  // Removed if never used
if (0) { ... }         // Unreachable block removed
```

3. Liveness Analysis
Preserves variable assignments across basic blocks
while eliminating unnecessary temporary computations.


### 1. Build the Compiler
```bash
make tcc
## or
gcc -o tcc tiny_c_compiler.c
```

### 2. Write Your Code
Create a file like `myprogram.c`:
```c
int sum(int n) {
    int result = 0;
    int i = 0;
    while (i < n) {
        result = result + i;
        i = i + 1;
    }
    return result;
}

int main() {
    int x = sum(10);
    return x;
}
```

### 3. Compile It
```bash
./tcc < myprogram.c > myprogram_out.c
gcc myprogram_out.c -o myprogram
./myprogram
echo $?  ## Shows return value
```

### 4. Run All Tests
```bash
make all-tests
```

### Language

Variables:
```c
int x;              // Declaration
int y = 5;          // Declaration with initialization
x = 10;             // Assignment
```

Arithmetic:
```c
int a = 2 + 3 * 4;  // Operator precedence respected
int b = (2 + 3) * 4;
```

Control Flow:
```c
if (x < 10) {
    y = 1;
} else {
    y = 2;
}

while (x > 0) {
    x = x - 1;
}
```

Functions:
```c
int add(int a, int b) {
    return a + b;
}

int main() {
    int result = add(5, 3);
    return result;
}
```


### Optimisation

Before:
```c
int demo() {
    int x = 5 + 3;      // Computed at runtime
    int y = 10 * 2;     // Computed at runtime
    int unused = 100;   // Never used
    return x + y;
}
```

After:
```c
int demo() {
    int x;
    int y;
    int unused;
    int t[5] = {0};
    
L0:
    t[0] = 8;           // Constant folding: 5+3
    x = t[0];
    t[1] = 20;          // Constant folding: 10*2
    y = t[1];
    t[2] = 100;
    unused = t[2];      // Kept (conservative)
    t[3] = x;
    t[4] = y;
    t[5] = t[3] + t[4];
    return t[5];
}
```

### Troubleshooting

1. *"Expected token type X"*
   - Missing semicolon
   - Mismatched braces
   - Invalid syntax

2. *"Too many basic blocks"*
   - Program too complex
   - Try breaking into smaller functions

3. *Wrong return value*
   - Check your algorithm
   - Try adding intermediate prints in generated code

#### Tips

1. *Look at generated code*:
   ```bash
   ./tcc < myprogram.c > output.c
   cat output.c  # Inspect the generated C code
   ```

2. *Add debug print output*:
   ```c
   // Modify generated code temporarily
   printf("x = %d\n", x);
   ```

3. *Check optimisation*:
   - Compare with/without optimisation
   - Look for constant-folded values


### Performance Notes

This compiler generates *unoptimised* C code.
For improvements:
- Generated code uses many temporaries
- No register allocation
- No advanced optimisations
- C compiler (gcc) does final optimisation

The value here is in *learning how compilers work*,
not really performance in itself.

### Next Steps

1. Try writing your own test programs
2. Modify the compiler to add new features:
   - Add modulo operator `%`
   - Add `for` loops
   - Add boolean type
   - Improve optimisations
   - Add more dead code elimination
   - Add common subexpression elimination
3. Study the CFG more carefully by adding debug output
4. Implement additional optimisation passes


### Files
```
tiny_c_compiler.c   - Main compiler source
README.md           - Comprehensive documentation
Makefile            - Build automation
test1_factorial.c   - Factorial example
test2_fibonacci.c   - Fibonacci example
test3_complex.c     - Complex control flow
test4_demo.c        - Optimization demo
```



### Examples

#### Test 1: Factorial (test1_factorial.c)
Demonstrates:
- While loops
- Variable assignments
- Constant folding (`5 + 3` → `8`, `2 * 3` → `6`)
- Dead code elimination (unused variables removed)
- Return value: 120 (5! = 120)

```c
int factorial(int n) {
    int result = 1;
    int dead_var = 5 + 3;  // Dead code - eliminated
    int x = 2 * 3;         // Constant folding: becomes 6
    
    while (n > 1) {
        result = result * n;
        n = n - 1;
    }
    
    return result;
}
```

#### Test 2: Fibonacci (test2_fibonacci.c)
Demonstrates:
- Recursive function calls
- If/else branching
- Return value: 55 (fib(10) = 55)

#### Test 3: Complex nested control flow (test3_complex.c)
Demonstrates:
- Nested if/while constructs
- Multiple variables
- Constant folding in declarations
- Return value: 80



### Implementation Details

#### Three-Address Code (TAC)
The compiler uses the intermediate representation
where each instruction has at most three operands (TAC):
```
t1 = a + b
t2 = t1 * c
result = t2
```

#### Control Flow Graph (CFG)
Basic blocks are connected with edges representing:
- Sequential flow
- Conditional branches (true/false paths)
- Loop back-edges
- Function calls

#### Variable Management
- Variables (index < 1000): Actual program variables
- Temporaries (index >= 1000): Intermediate computation results

#### Optimisation Strategy
1. *Constant Folding*: Single pass through each basic block
2. *Dead Code Elimination*: 
   - Mark reachable blocks via BFS
   - Remove instructions writing to unused temporaries
   - Preserve all variable assignments (may be used across blocks)


### Architecture

```
Input C Code ->
[Lexer]          Tokens ->
[Parser]         AST (implicit) ->
[IR Generator]   Three-Address Code ->
[CFG Builder]    Control Flow Graph ->
[Optimizer]      Optimised CFG ->
[Code Generator] Output C Code
```

### Future Enhancements

Possible extensions:
- Common subexpression elimination
- Loop-invariant code motion
- Register allocation
- More data types (float, char, arrays)
- Pointers and arrays
- Code generation to assembly or bytecode
- More sophisticated liveness analysis
- SSA form
- Interprocedural optimization
