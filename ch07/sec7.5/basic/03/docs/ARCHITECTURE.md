
## Component Flow

```
┌-------------------------------------------------------------┐
│                         User Input                          │
│                   (BASIC source code)                       │
└----------------------------┬--------------------------------┘
                             │
                             v
┌-------------------------------------------------------------┐
│                   INTERPRETER ENGINE                        │
│                    (interpreter.py)                         │
│  - Program loading/saving                                   │
│  - Command dispatch                                         │
│  - Execution control                                        │
└---┬------------------------------------------------------┬--┘
    │                                                      │
    │ Line Execution                         State Access  │
    │                                                      │
    v                                                      v
┌----------------------┐               ┌----------------------┐
│  UTILS               │               │   CORE STATE         │
│  (utils/helpers.py)  │               │   (core/state.py)    │
│  - split_statements  │               │  - Variables         │
│  - parse_line_number │               │  - Arrays            │
│  - helpers           │               │  - Code storage      │
└----------------------┘               │  - Control flow      │
    │                                  └----------------------┘
    │
    │ Statement
    │
    v
┌-------------------------------------------------------------┐
│                   COMMAND DISPATCHER                        │
│                 (commands/base.py + registry)               │
└---┬-----------------------------------------------------┬---┘
    │                                                     │
    │ Command Creation                        Command Execution
    │                                                     │
    v                                                     v
┌----------------------┐                    ┌---------------------┐
│  COMMAND MODULES     │                    │ EXPRESSION PARSING  │
│                      │                    │                     │
│  io_commands.py      │                    │  ┌--------------┐   │
│  - PrintCommand      │◄---needs----┐      │  │ TOKENIZER    │   │
│  - InputCommand      │             │      │  │ tokenizer.py │   │
│                      │             │      │  │ text->tokens │   │
│  control_flow.py     │             │      │  └------┬-------┘   │
│  - IfCommand         │             │      │         │           │
│  - GotoCommand       │             │      │         v           │
│  - ForCommand        │             │      │  ┌--------------┐   │
│  - WhileCommand      │             │      │  │ PARSER       │   │
│                      │             │      │  │ parser.py    │   │
│  data_commands.py    │             │      │  │ tokens->AST  │   │
│  - LetCommand        │             │      │  └------┬-------┘   │
│  - DimCommand        │             │      │         │           │
│                      │             │      │         v           │
│  system_commands.py  │             │      │  ┌--------------┐   │
│  - RunCommand        │             │      │  │ AST NODES    │   │
│  - ListCommand       │             │      │  │ ast.py       │   │
│  - SaveCommand       │             └------+->│ Expression   │   │
│  - LoadCommand       │                    │  │ tree         │   │
└----------------------┘                    │  └------┬-------┘   │
                                            │         │           │
                                            │         v           │
                                            │  ┌--------------┐   │
                                            │  │ EVALUATOR    │   │
                                            │  │ evaluator.py │   │
                                            │  │ AST->values  │   │
                                            │  └--------------┘   │
                                            └---------------------┘

┌-----------------------------------┐
│       EXCEPTION HIERARCHY         │
│       (core/exceptions.py)        │
│                                   │
│  BasicError                       │
│  ├-- TokenizationError            │
│  ├-- ParserError                  │
│  ├-- EvaluationError              │
│  ├-- ExecutionError               │
│  ├-- ArrayError                   │
│  └-- ControlFlowError             │
└-----------------------------------┘
```

## Data Flow for Expression Evaluation

```
Source: "X = SIN(3.14) + 5"
   │
   v
[TOKENIZER]
   │
   ├-> Token(IDENTIFIER, "X")
   ├-> Token(OPERATOR, "=")
   ├-> Token(IDENTIFIER, "SIN")
   ├-> Token(LPAREN, "(")
   ├-> Token(NUMBER, "3.14")
   ├-> Token(RPAREN, ")")
   ├-> Token(OPERATOR, "+")
   └-> Token(NUMBER, "5")
   │
   v
[PARSER]
   │
   └-> BinaryExpression(
         left: VariableExpression("X"),
         op: "=",
         right: BinaryExpression(
           left: FunctionExpression("SIN", [NumberExpression(3.14)]),
           op: "+",
           right: NumberExpression(5)
         )
       )
   │
   v
[EVALUATOR]
   │
   ├-> Evaluate right side:
   │   ├-> FunctionExpression("SIN", [...]) -> sin(3.14) ≈ 0.00159
   │   └-> BinaryExpression(0.00159, "+", 5) -> 5.00159
   │
   └-> Assign to variable X: 5.00159
```

## Command Execution Flow

```
User: "10 PRINT X + 5"
   │
   v
[Interpreter.load_program or execute_line]
   │
   ├-> Parse line number (10)
   ├-> Store in state.code[10] = "PRINT X + 5"
   │
   v
[Interpreter.run]
   │
   ├-> Get state.code[10]
   ├-> split_statements("PRINT X + 5") -> ["PRINT X + 5"]
   │
   v
[Command Dispatcher]
   │
   ├-> Parse "PRINT" as command
   ├-> Create PrintCommand(state)
   ├-> Call execute("X + 5")
   │
   v
[PrintCommand.execute]
   │
   ├-> Parse expression "X + 5"
   │   ├-> Tokenize
   │   ├-> Parse to AST
   │   └-> Evaluate
   │
   └-> Output result
```

## Module Dependencies

```
interpreter.py
    ├--> core/state.py
    ├--> core/exceptions.py
    ├--> commands/base.py
    ├--> commands/* (all command modules)
    └--> utils/helpers.py

commands/base.py
    ├--> core/state.py
    ├--> core/exceptions.py
    ├--> parsing/tokenizer.py
    ├--> parsing/parser.py
    └--> execution/evaluator.py

parsing/parser.py
    ├--> parsing/tokenizer.py
    ├--> expressions/ast.py
    └--> core/exceptions.py

execution/evaluator.py
    ├--> expressions/ast.py
    ├--> core/state.py
    └--> core/exceptions.py

commands/* (specific commands)
    └--> commands/base.py
```

## Design Principles

1. *Layered Architecture*: Clear separation between layers
2. *Single Responsibility*: Each module does one thing well
3. *Dependency Inversion*: Depend on abstractions, not concretions
4. *Open/Closed*: Open for extension, closed for modification
5. *DRY*: Don't Repeat Yourself - common code in base classes

