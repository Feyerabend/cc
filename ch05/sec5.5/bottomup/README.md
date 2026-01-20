
## Bottom-Up Parsing

Bottom-up parsing is a type of syntactic analysis technique used to recognise a language by starting with the input symbols (the "leaves") and progressively reducing them to the start symbol of the grammar. Unlike top-down parsing (which begins with the start symbol and works its way down to the leaves), bottom-up parsing works by attempting to find the deepest derivations first and then reducing the string to match the start symbol.

1. Shift and Reduce Operations:
- Shift: This operation moves the next input symbol onto the stack. The stack initially starts empty, and the shift operation gradually builds up the structure of the input.
- Reduce: Once the parser has built up enough symbols in the stack, it checks if a sequence of symbols matches a right-hand side of a production rule in the grammar. If a match is found, the parser "reduces" this sequence of symbols to the corresponding non-terminal (left-hand side) of the rule.

2. Handles and Handles Recognition:
A handle is a substring of the input that matches the right-hand side of a production rule in the grammar. The idea behind bottom-up parsing is that the parser attempts to identify and reduce these handles until the start symbol is derived.

3. Shift-Reduce Conflicts:
Sometimes, a bottom-up parser might face situations where it's unclear whether to shift or reduce. This is called a shift-reduce conflict. In practical implementations (like in certain parser generators), this can be resolved by prioritising one action over the other.

4. Final Goal:
The goal of bottom-up parsing is to reduce the entire input string to the start symbol. If successful, this means the input string is a valid sentence in the language defined by the grammar.


### Process

Bottom-up parsing works by applying reductions and shifts in the following steps:
- Start with the input symbols (tokens) from left to right.
- Shift the tokens onto the stack. This means pushing the tokens from the input onto the stack one by one.
- After each shift, check the top of the stack to see if it matches the right-hand side of any production rule in the grammar. If a match is found, perform a reduce operation, which involves replacing the matched symbols with the left-hand side (non-terminal) of the rule.
- Repeat the process: Shift tokens and reduce as possible. The process continues until the stack contains only the start symbol of the grammar.


#### Why?
- Efficient for LR Parsers: Bottom-up parsing is often used in LR parsers, which are efficient for a wide range of programming languages and grammars. These parsers can handle context-free grammars (CFG) with relatively simple deterministic strategies.
- Handles Complex Expressions: This approach naturally handles complex expressions in programming languages, such as arithmetic operations, control structures (like if-else or loops), and others.


### Example: Nested Brackets

This program implements a *bottom-up parser* using a *shift-reduce parsing* approach to
process a simplified grammar for input commands. It includes two main components:
a tokenizer and a parser.

#### Tokenizer

The tokenizer converts the raw input string into a sequence of tokens using predefined
patterns (regular expressions). Each token represents a syntactic unit, such as a bracket,
value, or whitespace.

Purpose of the Tokenizer
- Breaks down the input into manageable, discrete units.
- Removes unnecessary elements, like whitespace.
- Classifies each unit with a type (e.g., LBRACKET, RBRACKET, VALUE).

Given:

```python
[ "value" [ "value" "value" ] ]
```

Produces:

```python
[
    ('LBRACKET', '['),
    ('VALUE', '"value"'),
    ('LBRACKET', '['),
    ('VALUE', '"value"'),
    ('VALUE', '"value"'),
    ('RBRACKET', ']'),
    ('RBRACKET', ']')
]
```

#### Parser

The ShiftReduceParser processes tokens using the shift-reduce strategy.

Phases:
- Shift: Pushes the next token from the input onto a stack.
- Reduce: Applies production rules when the top elements of the stack match a rule’s right-hand side.

Production Rules
* Rule 1: $\` E \rightarrow [ E ] \`$ (an LBRACKET, an E, and an RBRACKET are reduced to E).
* Rule 2: $\` E \rightarrow EE \`$ (two E elements are reduced to a single E).
* Rule 3: $\` E \rightarrow \text{VALUE} \`$ (a single VALUE is reduced to E).

Example Workflow

For the input tokens:

```python
[
    ('LBRACKET', '['),
    ('VALUE', '"value"'),
    ('LBRACKET', '['),
    ('VALUE', '"value"'),
    ('VALUE', '"value"'),
    ('RBRACKET', ']'),
    ('RBRACKET', ']')
]
```

1. Shifting and Initial Reduction:
    - The parser shifts ('VALUE', '"value"') and applies Rule 3 to reduce it to E.
	- This results in:
```python
[('E', [('VALUE', '"value"')])]
```

2. Processing Nested Structure:
	- The parser shifts ('LBRACKET', '[') and ('VALUE', '"value"'), then applies Rule 1 to reduce [ E ] to E.
	- This results in:
```python
[('E', [('RBRACKET', ']'), ('E', [('VALUE', '"value"')]), ('LBRACKET', '[')])]
```

3. Combining Sequential Expressions:
	- The parser reduces the two E elements using Rule 2.
	- This results in:
```python
[('E', [('E', [('VALUE', '"value"')]), ('E', [('VALUE', '"value"')])])]
```

4. Final Reduction:
	- The parser reduces the entire nested structure [ "value" [ "value" "value" ] ] using Rule 1.
	- This results in:
```python
[('E', [
    ('RBRACKET', ']'),
    ('E', [
        ('E', [('VALUE', '"value"')]),
        ('E', [('VALUE', '"value"')])
    ]),
    ('LBRACKET', '[')
])]
```

Parse Tree

The final parse tree reflects the nested structure of the input:
```python
[
    ('E', [
        ('RBRACKET', ']'),
        ('E', [
            ('E', [('VALUE', '"value"')]),
            ('E', [('VALUE', '"value"')])
        ]),
        ('LBRACKET', '[')
    ])
]
```
This hierarchical representation demonstrates how the grammar rules decompose the input
into its structural components, showcasing the capabilities of bottom-up parsing.
