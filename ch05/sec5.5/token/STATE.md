
### State Machine Tokeniser

This tokeniser recognises identifiers, numbers, and operators from a simple input string.

```python
class StateMachineTokenizer:
    def __init__(self):
        self.tokens = []
        self.state = "START"

    def tokenize(self, input_string):
        self.tokens = []
        self.state = "START"
        buffer = ""
        i = 0

        while i < len(input_string):
            char = input_string[i]

            if self.state == "START":
                if char.isalpha():  # start of an identifier
                    self.state = "IDENTIFIER"
                    buffer += char
                elif char.isdigit():  # start of a number
                    self.state = "NUMBER"
                    buffer += char
                elif char in "+-*/=":  # operators, including '='
                    self.tokens.append(("OPERATOR", char))
                elif char.isspace():
                    pass  # ignore spaces
                else:
                    raise ValueError(f"Unexpected character: {char}")

            elif self.state == "IDENTIFIER":
                if char.isalnum():  # continue identifier
                    buffer += char
                else:  # identifier ends
                    self.tokens.append(("IDENTIFIER", buffer))
                    buffer = ""
                    self.state = "START"
                    continue  # skip the current character and reprocess it in the next loop

            elif self.state == "NUMBER":
                if char.isdigit():  # continue number
                    buffer += char
                else:  # number ends
                    self.tokens.append(("NUMBER", buffer))
                    buffer = ""
                    self.state = "START"
                    continue  # skip the current character and reprocess it in the next loop

            i += 1

        # Flush remaining buffer
        if buffer:
            if self.state == "IDENTIFIER":
                self.tokens.append(("IDENTIFIER", buffer))
            elif self.state == "NUMBER":
                self.tokens.append(("NUMBER", buffer))

        return self.tokens


# test
tokenizer = StateMachineTokenizer()
print(tokenizer.tokenize("x = 42 + y * 5"))
# output: [
#   ('IDENTIFIER', 'x'),
#   ('OPERATOR', '='),
#   ('NUMBER', '42'),
#   ('OPERATOR', '+'),
#   ('IDENTIFIER', 'y'),
#   ('OPERATOR', '*'),
#   ('NUMBER', '5')
# ]
```

### What is a State Machine Tokeniser?

A state machine tokeniser uses a finite automaton to break an input string into meaningful
components, called tokens. Tokens are categorised elements, such as identifiers, keywords,
numbers, operators, etc., often used in programming languages.


#### Components of a State Machine Tokeniser

1. States:
   Each state represents a specific part of the tokenisation process
   (e.g. reading an identifier, reading a number, handling whitespace).

2. Transitions:
   Define how the tokeniser moves from one state to another based on
   the next input character.

3. Input Alphabet:
   The set of characters the tokeniser can process.

4. Start State:
   The initial state before processing begins.

5. Accepting States:
   States where a token is completed and can be emitted.


#### How Does a State Machine Tokeniser Work?

1. Initialisation:
 - Start in the initial state.
 - Define transitions between states based on input.

2. Processing:
 - Read the input character by character.
 - Transition between states according to the defined rules.

3. Token Emission:
 - When reaching an accepting state, emit the corresponding token.
 - Return to the initial state to continue processing.


#### Where is a State Machine Tokeniser Used?

* Lexical Analysis in Compilers: Breaking source code into tokens like keywords, operators, literals, and identifiers.
* Data Parsing: Tokenising structured data like CSV files or simple text formats.
* Natural Language Processing: Splitting text into words, punctuation, etc.
* Command-Line Interfaces: Tokenising user input into commands and arguments.


#### Example of Tokeniser in Use

A simple tokeniser for mathematical expressions like `x = 3 + y * 2`:

1. States:
 - START: Initial state.
 - IDENTIFIER: Reading variable names.
 - NUMBER: Reading numeric values.

2. Transitions:
 - Alphabetic characters --> IDENTIFIER.
 - Digits --> NUMBER.
 - Operators or whitespace --> Emit the current token and return to START.

The tokeniser processes the input string and generates a sequence of tokens, such as
`[("IDENTIFIER", "x"), ("OPERATOR", "="), ("NUMBER", "3"), ...]`.
