
## Errors and Warnings

Errors and warnings are vital components of a compiler's interaction with programmers.
They provide feedback about issues in the code, which helps improve both the program's
correctness and the programmer's understanding of the language and tools being used.

Errors and warnings are more than just debugging tools; they are a form of communication
between the compiler and the programmer. When done well, they can reduce frustration,
improve code quality, and even serve as a teaching mechanism. As a compiler developer
or user, appreciating the value of these messages can greatly enhance both the development
process and the final product.


### 1. Why Errors and Warnings Matter

The primary purpose of a compiler is to translate source code into a form that a machine
can execute. However, the process of writing source code is inherently error-prone.
Compilers act as guides, pointing out mistakes and inconsistencies.

1. *Promotes Correctness:*
   Errors ensure that the code adheres to the language's rules, catching syntax errors,
   type mismatches, and other violations before the code is executed.

2. *Improves Code Quality:*
   Warnings highlight potential issues that may not break the program but could lead to
   bugs, inefficiencies, or unintended behaviour.

3. *Enhances Learning:*
   For novice programmers, clear and actionable error messages can teach language rules,
   common pitfalls, and best practices.

4. *Saves Time:*
   A robust error-reporting mechanism helps programmers locate and fix issues quickly,
   reducing debugging time.


### 2. Types of Errors and Warnings

Errors and warnings can be categorised based on their source and severity:

#### Errors

These represent violations of language rules or conditions that prevent the program from
being compiled. Examples include:

- Syntax Errors:
    Invalid syntax, such as a missing semicolon or unmatched parentheses.
    - Example: int x = 10 + ;
	- Message: "Syntax error: unexpected ';' after '+'."
- Type Errors:
    Mismatched types in operations or function calls.
	- Example: int x = "hello";
	- Message: "Type error: cannot assign a string to an integer variable."
- Semantic Errors:
    Code that is syntactically valid but violates logical rules, such as using undefined
    variables or dividing by zero.
	- Example: int result = 10 / 0;
	- Message: "Semantic error: division by zero is undefined."

#### Warnings

Warnings indicate potential issues that do not prevent compilation but might lead to bugs or unexpected behavior.
- Unused Variables:
	- Example: int x = 10; // but x is never used
	- Message: "Warning: variable 'x' is declared but not used."
- Deprecated Features:
    Using features that are outdated and may be removed in future versions.
	- Example: gets(buffer);
	- Message: "Warning: 'gets' is deprecated; consider using 'fgets'."
	- Potential Logical Issues:
- Suspicious constructs that may indicate a bug.
	- Example: if (x = 0) { ... }
	- Message: "Warning: assignment in conditional expression; did you mean '=='?"


### 3. Characteristics of Effective Errors and Warnings

For errors and warnings to be valuable, they must be:

__1. Clear__

The message should precisely describe the issue. Avoid technical jargon that
may confuse programmers, especially beginners.
- Bad: "Parser failed at token 'x'."
- Good: "Syntax error: unexpected token 'x'; expected an operator or semicolon."

__2. Contextual__

Messages should include the line number, column, and surrounding code, making it
easy for programmers to locate and understand the issue.
- Example: "Line 42: expected ';' at the end of the statement. Found: '}'."

__3. Actionable__

Where possible, provide guidance on how to fix the problem.
- Example: "Warning: variable 'y' is used uninitialized. Initialize 'y' before using it."

__4. Non-Intrusive__

Warnings should not overwhelm the programmer with irrelevant or redundant messages. Instead,
they should prioritise issues that are likely to cause problems.

__5. Configurable__

Different projects and programmers have different needs. Allow programmers to suppress or
elevate specific warnings based on their preferences or project guidelines.


### 4. Examples of Helpful Error Messages

Consider the following examples of improving error and warning messages:

__Example 1: Syntax Error__

Original Message:
```
Error: unexpected token ';' on line 5.
```

Improved Message:

```
Line 5: Syntax error: unexpected ';' after '+'. Did you forget an operand?
   4 | int result = 10 +
   5 | ;
       ^
```

__Example 2: Type Error__

Original Message:
```
Error: incompatible types.
```

Improved Message:

```
Line 8: Type error: cannot assign 'string' to 'int'.
   8 | int x = "hello";
           ^^^^^^^^^^
Hint: Did you mean to use a numeric value or change the type of 'x' to 'string'?
```

__Example 3: Warning__

Original Message:
```
Warning: unused variable.
```

Improved Message:

```
Line 12: Warning: variable 'temp' is declared but never used.
   12 | int temp = 42;
Hint: If 'temp' is unnecessary, consider removing it to clean up your code.
```

### 5. Recommendations for Compiler Developers

When implementing error and warning systems in compilers, consider the following best practices:
1. Provide Detailed Feedback:
   Include the error's location, nature, and possible solutions.

2. Categorise Messages:
   Distinguish between errors and warnings and allow programmers to configure their levels of strictness.

3. Use Examples:
   Whenever possible, show examples of both the incorrect and correct usage of a construct.

4. Emphasize Readability:
   Use consistent formatting and avoid overwhelming the programmer with excessively verbose or overly technical messages.



### Practical Applications

__1. Define Return Codes__

Create a set of standardized return codes as an enum to make error handling consistent and readable.

```c
typedef enum {
    SUCCESS = 0,          // Operation successful
    ERR_ALLOCATION = 1,   // Memory allocation error
    ERR_FILE = 2,         // File operation error
    ERR_OVERFLOW = 3,     // Overflow (e.g. unique ID, scope levels)
    ERR_NOT_FOUND = 4,    // Symbol not found
    ERR_INVALID = 5,      // Invalid input or state
} ReturnCode;
```

__2. Modify Functions to Return ReturnCode__

Update the functions to return meaningful error codes instead of exiting or printing directly. Functions
like initSymbolTable, addSymbol, and writeSymbolTableToFile should propagate errors.

Example 1: Handling Allocation Errors

```c
ReturnCode initSymbolTable() {
    symbolTable.entries = malloc(INITIAL_CAPACITY * sizeof(SymbolTableEntry));
    if (!symbolTable.entries) {
        return ERR_ALLOCATION;  // return error code
    }
    symbolTable.capacity = INITIAL_CAPACITY;
    symbolTable.size = 0;
    return SUCCESS;
}
```

__Example 2: Adding a Symbol__

```c
ReturnCode addSymbol(const char *name, Symbol type, int scopeLevel, int dataValueOrAddress, int *outUID) {
    if (symbolTable.size == symbolTable.capacity) {
        void *newEntries = realloc(symbolTable.entries, symbolTable.capacity * 2 * sizeof(SymbolTableEntry));
        if (!newEntries) {
            return ERR_ALLOCATION;  // return error code
        }
        symbolTable.entries = newEntries;
        symbolTable.capacity *= 2;
    }

    int uid = generateUniqueID();
    if (outUID) *outUID = uid;

    symbolTable.entries[symbolTable.size].symbolID = uid;
    symbolTable.entries[symbolTable.size].name = strdup(name);
    if (!symbolTable.entries[symbolTable.size].name) {
        return ERR_ALLOCATION;  // strdup failure
    }
    symbolTable.entries[symbolTable.size].type = type;
    symbolTable.entries[symbolTable.size].scopeLevel = scopeLevel;

    if (type == CONSTSYM) {
        symbolTable.entries[symbolTable.size].data.value = dataValueOrAddress;
    } else {
        symbolTable.entries[symbolTable.size].data.address = dataValueOrAddress;
    }

    symbolTable.size++;
    return SUCCESS;
}
```

__Example 3: Writing to a File__

```c
ReturnCode writeSymbolTableToFile(const char *filename) {
    FILE *file = fopen(filename, "w");
    if (!file) {
        return ERR_FILE;  // file open error
    }

    serializeSymbolTable(file);

    if (fclose(file) != 0) {
        return ERR_FILE;  // file close error
    }
    return SUCCESS;
}
```

__3. Centralized Error Handling__

Create a helper function to interpret and act on return codes,
such as logging errors or performing cleanup.

```c
void handleError(ReturnCode code, const char *context) {
    switch (code) {
        case SUCCESS:
            break;  // no error
        case ERR_ALLOCATION:
            fprintf(stderr, "Error in %s: Memory allocation failed.\n", context);
            break;
        case ERR_FILE:
            fprintf(stderr, "Error in %s: File operation failed.\n", context);
            break;
        case ERR_OVERFLOW:
            fprintf(stderr, "Error in %s: Overflow occurred.\n", context);
            break;
        case ERR_NOT_FOUND:
            fprintf(stderr, "Error in %s: Symbol not found.\n", context);
            break;
        case ERR_INVALID:
            fprintf(stderr, "Error in %s: Invalid input or state.\n", context);
            break;
        default:
            fprintf(stderr, "Error in %s: Unknown error.\n", context);
            break;
    }
}
```

__4. Propagate Errors Consistently__

Update higher-level functions to check for errors from lower-level functions and
propagate them upwards if necessary.

Example: Initializing the Symbol Table and Handling Errors

```c
ReturnCode initializeSystem() {
    ReturnCode rc;

    rc = initSymbolTable();
    if (rc != SUCCESS) {
        handleError(rc, "initSymbolTable");
        return rc;
    }

    resetIDGenerator();
    return SUCCESS;
}
```

__5. Use Return Codes in the Main Logic__

Centralise error handling in the main workflow or key entry points.

```c
int main() {
    ReturnCode rc = initializeSystem();
    if (rc != SUCCESS) {
        handleError(rc, "initializeSystem");
        return rc;
    }

    int uid;
    rc = addSymbol("x", VARSYM, 0, 0, &uid);
    if (rc != SUCCESS) {
        handleError(rc, "addSymbol");
        return rc;
    }

    rc = writeSymbolTableToFile("symbol_table.json");
    if (rc != SUCCESS) {
        handleError(rc, "writeSymbolTableToFile");
        return rc;
    }

    freeSymbolTable();
    return 0;
}
```

__6. Logging and Debugging__

To enhance debugging, you can log errors to a file or provide detailed output during development.

```c
void logErrorToFile(ReturnCode code, const char *context, const char *logFile) {
    FILE *file = fopen(logFile, "a");
    if (!file) {
        perror("Error opening log file");
        return;
    }

    fprintf(file, "Error in %s: %d\n", context, code);
    fclose(file);
}
```

Benefits:
- Consistency: All functions handle errors in a uniform way.
- Readability: Clear and standardised return codes.
- Scalability: Easy to add new error types or improve error handling without changing all functions.
- Debugging: Centralised error logging aids debugging and maintenance.

To get further help: more specific error messages in an excerpt from a [manual](./ERRCODES.md) on PL/0.
