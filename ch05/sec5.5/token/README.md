
## Tokeniser/Tokenizer or Lexer

A tokeniser or lexer is a essential component of a compiler or interpreter that breaks down the
raw source code into a stream of tokens. Tokens represent the smallest meaningful units in the code
such as keywords, identifiers, operators, and delimiters. While a tokeniser's primary goal is to
recognise and categorise these units, it also plays an essential role in handling simple syntax errors.

Here we use regular expressions, which is easy and very compact way of handling tokens.


### How a Tokeniser Handles Syntax Errors

1. Pattern Matching via Regular Expressions:
 - A tokeniser uses regular expressions to define patterns for valid tokens
   (e.g. identifiers, keywords, numbers).
 - When the tokeniser encounters a substring that doesn't match any of its defined patterns,
   it categorises it as an "unexpected character" or "mismatch."
 - For example:

```python
("MISMATCH", r'.')  # catches anything not matching earlier patterns
```

This rule ensures that any unrecognised input is flagged as an error during tokenisation.

2. Error Reporting:
 - The tokeniser records the location of errors (e.g. line and column numbers).
 - This allows the programmer to trace the issue back to the exact location in the source code
   (as it can be hard otherwise to detect where the error was).

3. Whitespace and Separator Handling:
 - By skipping whitespace and line breaks, the tokeniser focuses only on meaningful elements,
   simplifying error detection for unexpected characters.

4. Context-Agnostic Validation:
 - A tokeniser doesn't understand the program's grammar or structure (that's the job for the parser);
   it merely validates whether individual pieces conform to predefined patterns.
 - For instance, detecting '!!' in 'j !! n;' as invalid is straightforward because '!!' doesn't
   match any defined token pattern.

5. Warnings and Additional Checks:
 - Some tokenisers go beyond just identifying invalid characters. For example:
     - Identifying uppercase identifiers as warnings.
     - Flagging incomplete multi-character tokens, like an assignment operator ':=' missing '='.


### Why a Tokeniser Handles Syntax Errors

1. Early Detection:
 - Catching errors at the tokenisation stage avoids propagating invalid input to later stages like parsing.
 - Early errors are easier to diagnose and fix since they're closer to the source of the problem.

2. Streamlined Parsing:
 - Parsers assume the input is a valid sequence of tokens. If invalid tokens reach the parser, it would
   complicate error handling significantly.
 - By filtering out malformed input at the tokenisation stage, the tokeniser simplifies the parser's job.

3. Improved User Feedback:
 - Highlighting invalid characters or sequences immediately gives the programmer actionable feedback without
   requiring the entire program to be analysed.

4. Maintain Separation of Concerns:
 - The tokeniser focuses on the lexical structure (e.g. recognising valid keywords or identifiers).
 - The parser focuses on syntactic structure (e.g. ensuring statements are well-formed).


### Examples of Syntax Errors a Tokeniser Detects

* Invalid Characters:
    - Input: `j !! n`;
    - Detection: !! is flagged as invalid since it's not a recognised operator or delimiter.

* Unexpected Token Combinations:
    - Input: `j := n \`;
    - Detection: \ is flagged as invalid, as it's not part of a valid token.

* Whitespace-Sensitive Errors:
    - Input: `procedure sub;const k =7`;
    - Detection: Without a space after ;, some tokenisers may not correctly separate tokens, leading to a mismatch.

Why Regular Expressions Work Well
* Simplicity: They provide a concise way to define patterns for each token type.
* Efficiency: Modern regex engines are optimised for pattern matching, making tokenisation fast.
* Extensibility: Adding new token types or error-handling rules is straightforward.
