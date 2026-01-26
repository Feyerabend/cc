
## Compiler Error Reporting System

This compiler implements a comprehensive error reporting system that provides clear,
actionable feedback throughout all compilation phases. The system is designed to
help developers quickly identify and fix issues by collecting multiple errors,
providing context, and suggesting fixes.


#### Core Components

1. *ErrorReporter* (`error_reporter.py`)
   - Central error collection and reporting system
   - Categorises errors by severity and type
   - Provides formatted output with suggestions

2. *Error Categories*
   - *Lexical*: Token-level errors (invalid characters, unterminated strings)
   - *Syntax*: Grammar-level errors (missing semicolons, unmatched braces)
   - *Semantic*: Meaning-level errors (undeclared variables, type mismatches)
   - *Runtime*: Execution-time errors (division by zero, undefined operations)

3. *Error Severities*
   - *Warning*: Non-fatal issues that should be addressed
   - *Error*: Problems that prevent successful compilation
   - *Fatal*: Critical errors that stop compilation immediately


### Features

#### 1. Multi-Phase Error Collection

The compiler can collect errors from multiple phases before reporting:

```python
# By default, collects all errors
compile_and_run(source_code)

# Stop at first error phase
compile_and_run(source_code, stop_on_error=True)
```

*Advantages:*
- See all problems at once instead of fixing one error at a time
- Better understanding of the overall code quality
- Faster development cycle

*Trade-offs:*
- Later phases may report spurious errors due to earlier issues
- More complex error recovery logic required


#### 2. Contextual Error Messages

Each error includes:
- *Location*: Line and column numbers
- *Context*: The actual source code line
- *Visual pointer*: Caret (^) pointing to the error location
- *Category*: Type of error (Lexical/Syntax/Semantic/Runtime)
- *Suggestion*: Actionable advice for fixing the issue

Example output:
```
[Error] Line 3, Column 15 (Syntax) Expected SEMICOLON, got IDENTIFIER
  Context: let x = 42
           ^
  Suggestion: Did you forget a semicolon ';' before this?
```

### 3. Error Recovery

The parser implements panic-mode recovery to continue parsing after errors:

```python
def synchronize(self):
    """Synchronise to the next statement after an error"""
    while self.current() is not None:
        if self.current().kind == "SEMICOLON":
            self.consume()
            return
        if self.current().kind in ("LET", "PRINT", "INPUT", "IF", "WHILE"):
            return
        self.pos += 1
```

This allows finding multiple syntax errors in one pass.


#### 4. Helpful Suggestions

The system includes a database of common error patterns and suggestions:

```python
ERROR_SUGGESTIONS = {
    "undeclared_variable": "Did you forget to declare this variable with 'let'?",
    "redeclared_variable": "This variable was already declared. Use '=' for assignment.",
    "missing_semicolon": "Add a semicolon ';' at the end of the statement.",
    "missing_brace": "Check that all '{' braces have matching '}' braces.",
    # .. more
}
```


#### 5. Warning System

Non-fatal issues are reported as warnings:
- Unused variables
- Potential division by zero (with literals)
- Case sensitivity issues in keywords
- Variables used before initialization

Warnings surely don't prevent compilation but highlight potential problems.


### Usage

#### Basic Usage

```python
from compiler import compile_and_run

# Simple compilation
success = compile_and_run(source_code)

# Verbose mode (show all phases)
success = compile_and_run(source_code, verbose=True)

# Stop on first error phase
success = compile_and_run(source_code, stop_on_error=True)
```

#### Command Line

```bash
# Basic compilation
python compiler.py program.txt

# Verbose output
python compiler.py program.txt --verbose

# Stop at first error
python compiler.py program.txt --stop-on-error

# Show help
python compiler.py --help
```

#### Programmatic Error Handling

```python
from error_reporter import ErrorReporter, ErrorSeverity, ErrorCategory

# Create reporter
reporter = ErrorReporter(source_code)

# Report an error
reporter.report(
    ErrorSeverity.ERROR,
    ErrorCategory.SYNTAX,
    "Expected semicolon",
    line=5,
    column=12,
    suggestion="Add ';' at the end of the statement"
)

# Check for errors
if reporter.has_errors():
    reporter.print_report()
```


### Error Reporting Strategy

#### Two Modes of Operation

__1. Collect All Errors (Default)__
- Continues through all compilation phases
- Reports all errors at the end
- Best for: Development, when you want to see all issues

*Pros:*
- See complete picture of all problems
- Fix multiple issues at once
- More efficient development cycle

*Cons:*
- Some errors may be cascading effects
- May report false positives from earlier errors

__2. Stop on Error__
- Stops at first phase with errors
- Reports only errors from that phase
- Best for: Learning, understanding error progression

*Pros:*
- Focus on one type of error at a time
- Fewer false positives
- Clearer error isolation

*Cons:*
- Must fix and recompile multiple times
- Slower development cycle


#### Error Limits

To prevent overwhelming output, the compiler stops after 50 errors:

```python
self.max_errors = 50  # Configurable in ErrorReporter
```


### Examples

#### Example 1: Lexical Errors

*Input:*
```
Let x = 42;
let y = "unterminated;
```

*Output:*
```
[Warning] Line 1, Column 1 (Lexical) Keyword 'let' should be lowercase
  Context: Let x = 42;
           ^
  Suggestion: Use 'let' instead of 'Let'

[Error] Line 2, Column 9 (Lexical) Unterminated string literal
  Context: let y = "unterminated;
                   ^
  Suggestion: Strings must end with a closing quote (").
```

#### Example 2: Semantic Errors

*Input:*
```
let x = 42;
y = 10;
print(x + z);
```

*Output:*
```
[Error] Line 2 (Semantic) Variable 'y' is not declared
  Suggestion: Did you forget to declare this variable with 'let'?

[Error] Line 3 (Semantic) Variable 'z' is not declared
  Suggestion: Did you forget to declare this variable with 'let'?
```

#### Example 3: Multiple Phases

The system collects errors from all phases:

*Input:*
```
Let x = 42
y = 10;
print(z);
```

*Output:*
```
[Warning] Line 1 (Lexical) Keyword 'let' should be lowercase
[Error] Line 1 (Syntax) Expected SEMICOLON, got IDENTIFIER
[Error] Line 2 (Semantic) Variable 'y' is not declared
[Error] Line 3 (Semantic) Variable 'z' is not declared
```


### Best Practices

#### For Users

1. *Read errors top-to-bottom*: Earlier errors often cause later ones
2. *Pay attention to suggestions*: They're tailored to common mistakes
3. *Use verbose mode*: Helps understand what the compiler is doing
4. *Check line numbers*: Errors are usually on or near the reported line

#### For Developers

1. *Be specific*: Include exact location and context
2. *Provide suggestions*: Help users fix the problem
3. *Categorize correctly*: Use appropriate severity and category
4. *Recover gracefully*: Continue parsing when possible
5. *Limit error counts*: Prevent overwhelming output


### Implementation Details

### Error Reporter Class

```python
class ErrorReporter:
    def __init__(self, source_code: str = ""):
        self.errors: List[CompilerError] = []
        self.warnings: List[CompilerError] = []
        self.source_lines = source_code.split('\n')
        self.max_errors = 50
```

#### CompilerError Dataclass

```python
@dataclass
class CompilerError:
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    context: Optional[str] = None
    suggestion: Optional[str] = None
```

#### Integration with Compiler Phases

Each phase receives the error reporter:

```python
# Lexer
tokens = tokenize(source_code, reporter)

# Parser
parser = Parser(tokens, reporter)
ast = parser.parse()

# Semantic Analyzer
analyzer = SemanticAnalyzer(ast, reporter)
analyzer.analyze()
```

### Future Enhancements

Potential improvements to the error reporting system:

1. *Color-coded output*: Use ANSI colors for better readability
2. *Error codes*: Assign unique codes to error types
3. *Quick fixes*: Automated suggestions for simple errors
4. *IDE integration*: Export errors in LSP format
5. *Error statistics*: Track common error patterns
6. *Severity levels*: More granular control (info, hint, warning, error, fatal)
7. *Suppression*: Allow users to suppress specific warnings
8. *Context expansion*: Show multiple lines of context
9. *Error grouping*: Group related errors together
10. *Fix preview*: Show what code would look like after fix


### Conclusion

This error reporting system demonstrates best practices in compiler design:
- Clear, actionable feedback
- Error recovery for better user experience
- Separation of concerns (error reporting is separate from compilation logic)
- Configurable behaviour for different use cases
- Comprehensive coverage of all compilation phases

