
## A Simple Compiler


### What is a Compiler?

A compiler is a program that translates code you write into code the
computer can execute. Think of it like a translator that converts English
to French, but instead it converts `x = 5 + 3 * 2;` into instructions
your computer understands.


### The 7 Steps of Compilation

Let's follow what happens to this simple code: `x = 5 + 3 * 2;`



#### 1. Lexical Analysis (Tokenisation)

*What it does:* Breaks the code into individual "words" called tokens.

*Think of it like:* Reading a sentence and identifying each word and punctuation mark.

*Example:*
```
Input:  x = 5 + 3 * 2;

Output: [x] [=] [5] [+] [3] [*] [2] [;]
         ↓   ↓   ↓   ↓   ↓   ↓   ↓   ↓
       name  =  num  +  num  *  num  ;
```

Each piece gets labeled: `x` is an IDENTIFIER, `5`
is a NUMBER, `+` is a PLUS operator, etc.



#### 2. Syntax Analysis (Parsing)

*What it does:* Arranges tokens into a tree structure that shows
their relationships, following grammar rules.

*Think of it like:* Diagramming a sentence to show which words modify which.

*Example:*
```
Input: x = 5 + 3 * 2

Tree structure:
       =
      / \
     x   +
        / \
       5   *
          / \
         3   2
```

Notice how `3 * 2` is grouped together first because multiplication
has higher priority than addition. This tree is called an Abstract Syntax Tree (AST)
(Section 5.6.4).



#### 3. Semantic Analysis

*What it does:* Checks if the code makes sense according to the language rules.

*Think of it like:* A grammar checker that ensures you're using words correctly in context.

*What it checks:*
- Is variable `x` defined before we use it? ✓ (We're defining it here)
- Are we using the right types? ✓ (All numbers)
- Are there any logical errors? ✓ (Looks good)

*Result:* Creates a symbol table:
```
Symbol Table:
x → integer
```



#### 4. Intermediate Code Generation

*What it does:* Converts the tree into simple, step-by-step
instructions that are easier to work with.

*Think of it like:* Converting a recipe into numbered steps.

*Example:*
```
Input: The tree for "5 + 3 * 2"

Intermediate code:
t0 = 5          // Load the number 5
t1 = 3          // Load the number 3
t2 = 2          // Load the number 2
t3 = t1 * t2    // Multiply 3 * 2 (gives 6)
t4 = t0 + t3    // Add 5 + 6 (gives 11)
x = t4          // Store result in x
```

Each line does only ONE simple operation. The `t0`, `t1` ..
etc. are temporary storage locations.



#### 5. Optimisation

*What it does:* Makes the code faster and more efficient by doing
calculations that can be done ahead of time.

*Think of it like:* If a recipe says "add 2 cups of flour plus 3
cups of flour," you'd just write "add 5 cups of flour."

*Example:*
```
Before optimisation:
t1 = 3
t2 = 2
t3 = t1 * t2    // We can calculate this now!

After optimisation:
t3 = 6          // Just use 6 directly!
```

The compiler sees that `3 * 2` will always equal `6`, so it calculates
it once during compilation instead of every time the program runs.

Full optimised code:
```
t0 = 5
t1 = 3
t2 = 2
t3 = 6          // Pre-calculated 3 * 2
t4 = 11         // Pre-calculated 5 + 6
x = t4
```



#### 6. Code Generation

*What it does:* Converts the optimised intermediate
code into actual executable code.

*Think of it like:* Translating the numbered recipe steps
into the actual language you'll cook in.

*Example:*
```
Generated Python code:
t0 = 5
t1 = 3
t2 = 2
t3 = 6
t4 = 11
x = t4
```

This is real Python code that can run on your computer.



#### 7. Linking

*What it does:* Combines your code with any libraries or
other code it needs, then executes it.

*Think of it like:* Putting together all the ingredients
and actually cooking the meal.

*Example:*
```
Execute the code:
x = 11  ✓

Final result: Variable x contains 11
```



### Why So Many Steps?

You might wonder: "Why not just go directly from code to execution?"

Each step has a purpose:

1. *Tokenisation* - Makes it easier to read the code systematically
2. *Parsing* - Ensures proper grammar and creates structure
3. *Semantic Analysis* - Catches errors early (like undefined variables)
4. *Intermediate Code* - Makes it easier to optimise and target different machines
5. *Optimisation* - Makes programs run faster
6. *Code Generation* - Produces the final executable code
7. *Linking* - Puts everything together


### Differences Between A Compiler And An Interpreter

*Interpreter:*
1. Lexical Analysis (Tokenisation)
2. Syntax Analysis (Parsing)
3. Semantic Analysis (Lightweight)
4. Direct Execution

*Compiler:*
1. Lexical Analysis (Tokenisation)
2. Syntax Analysis (Parsing)
3. Semantic Analysis
4. Intermediate Code Generation
5. Optimisation
6. Code Generation
7. Linking & Execution

*Some tradeoffs:*
* Interpreter: Faster startup, slower execution, easier debugging
* Compiler: Slower startup, faster execution, harder debugging

#### Why Interpreters Are Different

The main differences between interpreters and compilers:

*Interpreters:*
- Execute code immediately
- No separate compilation step
- No intermediate code generation
- No optimisation phase
- No code generation phase
- Easier to debug (can stop and inspect at any point)
- Slower execution (repeated interpretation overhead)
- Great for development and scripting

*Compilers:*
- Translate first, execute later
- Generate optimized machine code
- Faster execution (code is pre-optimised)
- Harder to debug (code is transformed)
- Better for production applications


### Summary

Our simple compiler takes `x = 5 + 3 * 2;` and:
- Breaks it into pieces (tokens)
- Organises pieces into a tree (AST)
- Checks for errors (semantic analysis)
- Creates simple instructions (intermediate code)
- Optimises those instructions (calculates `3 * 2 = 6` and `5 + 6 = 11` ahead of time)
- Generates executable code
- Runs it to get `x = 11`

