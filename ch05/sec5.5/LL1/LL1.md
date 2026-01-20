
## LL(1) Parsing

Arriving at the grammar is an essential step in designing a parser. The grammar is
typically derived from the language specification or requirements you want to parse.
The grammar for LL(1) and its use of a parsing table, can be a bit odd to understand.


#### 1. Understand the Structure of the Language

Start by identifying the key constructs of the language. For arithmetic expressions,
this includes:
- Numbers (integers or floating-point).
- Arithmetic operators like `+`, `-`, `*`, `/`.
- Parentheses for grouping.

From this, we know the language involves expressions, which combine numbers and operators.


#### 2. Establish Precedence and Associativity

Operators often have precedence:
- `*` and `/` have higher precedence than `+` and `-`.
- Parentheses `()` override precedence.
- Associativity governs how operators of the same precedence are evaluated:
- Most arithmetic operators are left-associative (e.g., 3 - 2 - 1 is (3 - 2) - 1).

This informs how we design the grammar rules.


#### 3. Write Informal Rules

Break the expression into its hierarchical components:
1. *Expression (E)*: The top-level construct, allowing addition and subtraction.
2. *Term (T)*: A sub-part of an expression, handling multiplication and division.
3. *Factor (F)*: The smallest unit, such as a number or a parenthesized expression.

Informally:
- An expression is one or more terms combined by + or -.
- A term is one or more factors combined by * or /.
- A factor is a number or a grouped expression in parentheses.


#### 4. Write the Grammar

Translate the informal rules into a formal grammar:

__1. Start with the highest-level construct:__
$E \rightarrow T \ E{\prime}$

Here, $E$ is an *expression*, which consists of a *term* ($T$) followed by $E{\prime}$,
which accounts for additional terms connected by + or -.

__2. Define $E{\prime}$ for additions and subtractions:__
$E{\prime} \rightarrow + \ T \ E{\prime} \ | \ - \ T \ E{\prime} \ | \ \epsilon$

$E{\prime}$ recursively handles additional terms or ends the expression $( \epsilon )$.

__3. Define $T$ for multiplication and division:__
$T \rightarrow F \ T{\prime}$

$T$ consists of a *factor* ($F$) followed by $T{\prime}$, which handles repeated factors connected by * or /.

__4. Define $T{\prime}$:__
$T{\prime} \rightarrow * \ F \ T{\prime} \ | \ / \ F \ T{\prime} \ | \ \epsilon$

$T{\prime}$ handles multiplication and division or ends the term $( \epsilon )$.

__5. Define $F$ for numbers and parentheses:__
$F \rightarrow \text{num} \ | \ ( E )$


### Grammar (EBNF)

Here's is the final grammar with support for numbers, floating points, and operators:

```ebnf
    E  → T E'
    E' → + T E' | - T E' | ε
    T  → F T'
    T' → * F T' | / F T' | % F T' | ε
    F  → ( E ) | num | num ^ F
```

- num represents an integer or floating-point number.
- ε is the empty production (i.e. nothing).


### Parsing Table

And here is parsing table that results from the reasoning above:


|NT	|num	|(	|+	|-	|*	|/	|%	|)	|$	|^|
|-|-|-|-|-|-|-|-|-|-|-|
|E	|T E'	|T E'	|	|	|	|	|	|	|	|   |
|E'	|		|   |+ T E'	|- T E'	|ε	|ε	|ε	|ε	|ε	|   |
|T	|F T'	|F T'	|	|	|	|	|	|	|	|   |
|T'	|		|   |ε	|ε	|* F T'	|/ F T'	|% F T'	|ε	|ε	|   |
|F	|num	|( E )	|	|	|	|	|	|	|	|num ^ F    |


Legend:
- NT is Non-terminal
- $ is the end-of-input marker.
- Cells contain the production to apply or are empty if the input is invalid for that non-terminal.

Steps to Use the Table (what the program does):
1. Start with the initial non-terminal (e.g. E).
2. Look at the current token (lookahead) in the input.
3. Find the intersection of the *row* (non-terminal) and *column* (lookahead):
	- If the cell contains a production (e.g. E → T E'), apply it.
	- If the cell contains ε, perform an epsilon transition (nothing is added to the stack).
	- If the cell contains error, the input cannot be parsed.
	- If the cell is empty, it is an implicit error.
4. Replace the non-terminal on the top of the stack with the symbols from the production rule.
5. Repeat until the input is parsed (stack is empty and input is consumed).


### Code

Here's how we integrate the parsing table into the parser:

```python
import re

class LL1Parser:
    def __init__(self, input):
        self.tokens = self.tokenize(input)
        self.tokens.append('$')  # end-of-input marker
        self.pos = 0
        self.stack = ['$', 'E']  # parsing stack starts with $ and the start symbol

        # parsing table
        self.table = {
            'E': {
                'num': ['T', 'E\''],
                '(': ['T', 'E\'']
            },
            'E\'': {
                '+': ['+', 'T', 'E\''],
                '-': ['-', 'T', 'E\''],
                ')': [],
                '$': []
            },
            'T': {
                'num': ['F', 'T\''],
                '(': ['F', 'T\'']
            },
            'T\'': {
                '+': [],
                '-': [],
                '*': ['*', 'F', 'T\''],
                '/': ['/', 'F', 'T\''],
                '%': ['%', 'F', 'T\''],
                ')': [],
                '$': []
            },
            'F': {
                'num': ['num'],
                '(': ['(', 'E', ')']
            }
        }

    def tokenize(self, input):
        token_pattern = r'\d+\.\d+|\d+|[+\-*/%^()]'
        tokens = re.findall(token_pattern, input)
        print(f"Tokens: {tokens}")
        return tokens

    def lookahead(self): # one item look ahead
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def parse(self):
        while self.stack:
            top = self.stack.pop()
            token = self.lookahead()

            if top in self.table:  # non-terminal
                if token in self.table[top]:
                    production = self.table[top][token]
                    print(f"Applying production {top} → {' '.join(production)}")
                    self.stack.extend(reversed(production))  # push production onto stack
                else:
                    raise Exception(f"Error: Unexpected token {token} for {top}")

            elif top == token:  # terminal matches input
                print(f"Consuming: {token}")
                self.pos += 1

            elif top == 'num' and self.is_number(token):  # match number
                print(f"Consuming number: {token}")
                self.pos += 1

            else:
                raise Exception(f"Error: Unexpected token {token}. Expected {top}")

        if self.lookahead() == '$': # end parsing
            print("Input parsed successfully!")
        else:
            raise Exception(f"Error: Unexpected input at end. Found {self.lookahead()}")

    def is_number(self, token):
        """Check if the token is a valid number (integer or floating-point)."""
        return re.match(r'^\d+(\.\d+)?$', token)



input_string = "3 + 2 * 4"
parser = LL1Parser(input_string)
parser.parse()

input_string2 = "3.14 * ( 2 + 5.6 )"
parser2 = LL1Parser(input_string2)
parser2.parse()

input_string3 = "5 + 3.5 ^ 2"
parser3 = LL1Parser(input_string3)
parser3.parse()

input_string4 = "2 * (3 + 2.5)"
parser4 = LL1Parser(input_string4)
parser4.parse()

input_string5 = "1.5 + 2.5 * 3"
parser5 = LL1Parser(input_string5)
parser5.parse()
```

#### Explanation

1. Parsing Table:
	- Explicitly constructed for each non-terminal and terminal.
	- Guides the parser on which production to apply.

2. Stack:
	- The stack holds the current symbols (terminals and non-terminals) the parser is processing.

3. Table Lookup:
	- The parser uses the table to decide which production to apply based on the top of the stack and the lookahead token.

4. Error Handling:
	- If no production exists for a (non-terminal, token) pair, an error is raised.

5. Number Handling:
	- Matches integers and floating-point numbers.


#### Output

For the input 3 + 2 * 4:

```text
Tokens: ['3', '+', '2', '*', '4']
Applying production E → T E'
Applying production T → F T'
Applying production F → num
Consuming number: 3
Applying production T' → ε
Applying production E' → + T E'
Consuming: +
Applying production T → F T'
Applying production F → num
Consuming number: 2
Applying production T' → * F T'
Consuming: *
Applying production F → num
Consuming number: 4
Applying production T' → ε
Applying production E' → ε
Input parsed successfully!
```

This approach is systematic and extendable, ideal for learning and implementing larger grammars.
