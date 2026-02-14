
## File Organization

### Original Structure (8 files, ~1500 lines)
```
basic_commands.py         (~1400 lines) - All commands in one file
basic_evaluator.py        (~130 lines)  - Expression evaluation
basic_expressions.py      (~60 lines)   - Expression classes
basic_interpreter.py      (~50 lines)   - Main entry point
basic_parser.py           (~180 lines)  - Parser
basic_shared.py           (~40 lines)   - Shared state/errors
basic_tokenizer.py        (~120 lines)  - Tokenizer
basic_utils.py            (~5 lines)    - Minimal utils
```

### Refactored Structure (15+ files, organised by concern)
```
basic_ii/
├── core/
│   ├── state.py          (~130 lines)  - State management
│   └── exceptions.py     (~35 lines)   - Exception hierarchy
├── expressions/
│   └── ast.py            (~75 lines)   - Expression AST
├── parsing/
│   ├── tokenizer.py      (~190 lines)  - Enhanced tokenizer
│   └── parser.py         (~230 lines)  - Enhanced parser
├── execution/
│   └── evaluator.py      (~230 lines)  - Enhanced evaluator
├── commands/
│   ├── base.py           (~75 lines)   - Command framework
│   ├── io_commands.py    (~180 lines)  - I/O commands
│   ├── data_commands.py  (~190 lines)  - Data commands
│   └── [more modules]
├── utils/
│   └── helpers.py        (~160 lines)  - Utilities
└── interpreter.py        (~195 lines)  - Main engine
```



### 1. Separation of Concerns

*Original:*
- `basic_commands.py` contained ALL commands (PRINT, INPUT, LET, DIM, FOR, WHILE, IF, GOTO, etc.)
- 1400+ lines in a single file
- Difficult to navigate and maintain

*Refactored:*
- Commands split into logical modules:
  - `io_commands.py` - Input/output (PRINT, INPUT, REM)
  - `data_commands.py` - Data manipulation (LET, DIM)
  - `control_flow.py` - Control structures (IF, GOTO, FOR, WHILE)
  - `system_commands.py` - System operations (RUN, LIST, SAVE)
- Each module ~150-200 lines
- Easy to find and modify specific functionality


### 2. State Management

*Original:*
```python
class InterpreterState:
    def __init__(self):
        self.variables = {"#": 0}
        self.arrays = {}
        self.array_dims = {}
        # Direct field access throughout codebase
```

*Refactored:*
```python
class InterpreterState:
    def __init__(self):
        # Same fields, but...
    
    # API methods for controlled access
    def get_variable(self, name, default=0)
    def set_variable(self, name, value)
    def declare_array(self, name, dimensions)
    def get_array_value(self, name, indices, default=0)
    def set_array_value(self, name, indices, value)
    def get_current_line(self)
    def get_next_line(self, current)
```

*Benefits:*
- Encapsulation: Implementation can change without breaking callers
- Validation: Can enforce constraints in one place
- Documentation: Clear API shows what's possible
- Testing: Easy to mock state for unit tests


### 3. Error Handling

*Original:*
```python
class ParserError(Exception):
    pass

class InterpreterError(Exception):
    pass

class ExecutionError(InterpreterError):
    pass
```

*Refactored:*
```python
class BasicError(Exception):
    """Base for all BASIC errors"""

class TokenizationError(BasicError): pass
class ParserError(BasicError): pass
class EvaluationError(BasicError): pass
class ExecutionError(BasicError): pass
class ArrayError(BasicError): pass
class ControlFlowError(BasicError): pass
```

*Benefits:*
- Hierarchical: Can catch all BASIC errors with one handler
- Specific: Can handle different error types differently
- Clear: Error type indicates where problem occurred


### 4. Expression System

*Original:*
- Parser, evaluator, and expression classes tightly coupled
- Limited documentation
- Hard to extend

*Refactored:*
- Clean separation: Tokenizer → Parser → AST → Evaluator
- Each component independently testable
- Well-documented with examples
- Easy to add new expression types or functions


### 5. Code Quality

#### Documentation

*Original:*
```python
def parse_primary(self):
    if self.pos >= self.length:
        return NumberExpression(0)
    # ... 50 lines of code
```

*Refactored:*
```python
def _parse_primary(self) -> Expression:
    """
    Parse primary expressions: numbers, strings, variables, 
    functions, arrays, parentheses.
    """
    # Clear handler dispatch
    handlers = {
        "NUMBER": self._parse_number,
        "STRING": self._parse_string,
        "IDENTIFIER": self._parse_identifier,
        "LPAREN": self._parse_parenthesized
    }
    # ...
```


#### Naming

*Original:*
- Inconsistent naming (parse_term, parse_factor, parse_primary)
- Public methods mixed with private
- No clear interfaces

*Refactored:*
- Consistent naming conventions
- Clear public API (no leading underscore)
- Private helpers (leading underscore)
- Type hints throughout


#### Structure

*Original:*
```python
# 100-line method doing everything
def process(self, args):
    # Parse
    # Validate  
    # Execute
    # Error handling
    # All mixed together
```

*Refactored:*
```python
def process(self, args):
    """Main process - delegates to helpers"""
    declarations = self._split_declarations(args)
    for decl in declarations:
        self._process_single_declaration(decl)

def _split_declarations(self, args):
    """Single responsibility: parsing"""
    # ...

def _process_single_declaration(self, decl):
    """Single responsibility: one declaration"""
    # ...
```


### 6. Testability

*Original:*
- Components tightly coupled
- Hard to test individual pieces
- No dependency injection
- Global state issues

*Refactored:*
- Each component has clear interface
- Dependencies passed in (state, debug flag)
- Can mock dependencies for testing
- Pure functions where possible

Example test scenarios:

```python
# Test tokenizer independently
def test_tokenizer():
    tokenizer = Tokenizer("10 PRINT 'Hello'")
    tokens = tokenizer.tokenize()
    assert tokens[0].type == "NUMBER"
    assert tokens[1].type == "IDENTIFIER"

# Test parser independently  
def test_parser():
    tokens = [Token("NUMBER", "5"), ...]
    parser = ExpressionParser(tokens)
    ast = parser.parse()
    assert isinstance(ast, NumberExpression)

# Test evaluator independently
def test_evaluator():
    state = InterpreterState()
    state.set_variable("X", 10)
    evaluator = ExpressionEvaluator(state)
    result = evaluator.evaluate(VariableExpression("X"))
    assert result == 10

# Test commands independently
def test_print_command():
    state = InterpreterState()
    cmd = PrintCommand(state)
    # Capture output and verify
```


### 7. Extensibility

#### Adding a New Function

*Original:*
1. Find the right place in 130-line evaluator
2. Add to function dict
3. Hope it doesn't break anything

*Refactored:*
1. Add to `ExpressionParser.BUILTIN_FUNCTIONS`
2. Add handler in `ExpressionEvaluator._try_math_function` or `_try_string_function`
3. Function is isolated and documented


#### Adding a New Command

*Original:*
1. Add 100+ lines to 1400-line `basic_commands.py`
2. Add to CommandFactory dict
3. File becomes harder to navigate

*Refactored:*
1. Create new class in appropriate module
2. Register in interpreter
3. Clean separation, easy to find

```python
# New command in its own file or added to relevant module
class MyCommand(ParsedCommand):
    def process(self, args):
        # Implementation

# Register it
interpreter.register_command("mycmd", MyCommand)
```


### 8. Maintenance Benefits

| Aspect | Original | Refactored |
|--------|----------|------------|
| Find a bug | Search 1400-line file | Check specific module |
| Add feature | Modify large file | Add/modify small module |
| Understand code | Read through everything | Read module docs, then code |
| Review changes | Large diffs | Small, focused diffs |
| Onboard new dev | Overwhelming | Progressive learning |
| Reuse code | Copy-paste | Import module |



### Migration Path

The refactored code maintains compatibility:
- Same BASIC language semantics
- Same array indexing (1-based)
- Same command syntax
- Can run existing BASIC programs

*Trade-offs:*
- More files to manage (but better organised)
- Slightly more boilerplate (but more maintainable)
- Need to understand architecture (but well-documented)


