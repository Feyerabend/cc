
## Syntax: Tokeniser, or Tokenizer, Lexer ..

__Build__

```shell
make clean
make
make samples
```

This system tokenises input files from the samples directory and reads the tokenised output to display it.
Although the grammar isn't applied yet, the system makes a best-effort guess to identify reserved words,
which are prohibited from being used as anything else.

This code implements a simple tokeniser (lexer) for a programming language similar to PL/0 (some adjustments
have been made). The tokeniser reads a source file containing code, identifies individual tokens based on
language grammar, and writes these tokens to an output file.

__View__

In the directory of 'tools' you'll find a HTML-file: tokens.html. Open the file locally, and search
for the tokenised representation in the 'tokens' folder.



### Overview

The tokeniser breaks down the input program into tokens, which are the smallest units of meaning in the
language (e.g. keywords, identifiers, numbers, operators). The tokens are written to an output file in
a readable format.

__nextChar()__

- Advances to the next character in the input string (sourceCode) and updates currentChar.
- Maintains the state of the tokeniser as it processes the input.

__skipWhitespace()__

- Skips over whitespace characters (' ', '\t', '\n', etc.).
- If a newline ('\n') is encountered, it writes an "ENDOFLINE" token to the output file, which is useful
  for handling line-sensitive constructs (e.g. error reporting indicating where the error can be found).

__handleIdentifier()__

- Processes identifiers and keywords.
- Reads a sequence of alphanumeric characters and underscores (_).
- Checks if the read string matches a keyword (e.g. call, begin) and emits the corresponding token. If not,
  it is treated as an identifier.

__handleNumber()__

- Handles numeric literals.
- Reads a sequence of digits and emits a "NUMBER" token with its value.

__tokeniser()__

- The main function that orchestrates tokenization.
- Iterates through the input string (sourceCode), categorizing each character or sequence of characters into tokens.
- Handles:
    - Identifiers and keywords using handleIdentifier.
	- Numbers using handleNumber.
	- Symbols and operators directly ('(', ')', '+', '-', etc.).
	- Multi-character operators like '<=' and ':='.
	- Writes tokens to the output file in a readable format.

__cleanup()__

- Closes the input and output files and frees dynamically allocated memory to avoid resource leaks.

__fromSourceToTokens()__

- Reads the source file into memory.
- Sets up the tokeniser and output file.
- Calls tokeniser() to perform the actual tokenization.
- Cleans up resources after tokenization.


### Notes

1. Keywords vs. Identifiers:
- Keywords are reserved words (such as 'if', 'while') that have special meanings in the language.
- Identifiers are user-defined names (such as variable or procedure names).
- handleIdentifier() differentiates these by comparing the read string to a list of known keywords.

2. Operators and Symbols:
- Single-character symbols (e.g. '+', '-', '*', '(', ')') are directly tokenised.
- Multi-character operators (e.g. '<=', ':=') are handled by checking the next character after encountering the first one.

3. Error Handling:
- If an unexpected character is encountered, an "ERROR" token is emitted, and the tokeniser moves to the next character.

4. End of Input:
- The input ends when currentChar is '\0' (null terminator).
- An "ENDOFFILE" token is emitted to signify the end of the program.


### Example

Input:

```pascal
var sum;

begin
    sum := 4 + 2;
end.
```

Output:

```
VARSYM IDENT sum SEMICOLON ENDOFLINE
ENDOFLINE
BEGINSYM ENDOFLINE
IDENT sum BECOMES NUMBER 4 PLUS NUMBER 2 SEMICOLON ENDOFLINE
ENDSYM PERIOD ENDOFFILE
```

1. Input Processing:
- The input file is read into memory as a single string (sourceCode).
- The tokeniser processes the input one character at a time using nextChar().

2. Token Identification:
- Each character is categorized:
- Letters (a-z, A-Z, _) start identifiers or keywords.
- Digits (0-9) start numeric literals.
- Symbols (+, -, *, etc.) are matched directly.
- Multi-character tokens (<=, :=) are handled by peeking at the next character.

3. Output:
- Tokens are written to the output file in a readable format.


This tokeniser is a simple implementation for a small programming language. It efficiently
classifies input characters into tokens while handling common constructs like identifiers,
keywords, numbers, and operators. It produces a tokenized representation of the input code,
which is an essential step before parsing and compiling.


### Exercise

Thus far, we have primarily focused on scenarios where parsing is successful. However, as you
are likely aware, parsing frequently encounters failures, leading to the generation of error
messages. During tokenisation, there is a possibility that reserved or expected keywords do
not align with the input. Consider implementing a Python script or a C program to handle these
errors, which may be represented as replacement tokens.

Reflect on the following:
- Can the program recover from such errors and continue parsing effectively?
- Or are the errors (likely) too severe, requiring the parsing process to terminate?

Explore mechanisms for error recovery and determine whether the parser can proceed or if the
input requires correction before resuming.



### .. with annotations

Tokens are *annotated* with approximate locations in the source code. Although the grammar isn't applied yet,
the system makes a best-effort guess to identify reserved words, which are prohibited from being used as
anything else.

This code implements a simple tokeniser (lexer) for a programming language similar to PL/0 (some adjustments
have been made). The tokeniser reads a source file containing code, identifies individual tokens based on
language grammar, and writes these tokens to an output file.

### Project

The aim of this project is to build a flexible and robust tokeniser for a simple programming language. The tokeniser will:

1. *Identify Tokens*: Recognise identifiers, numbers, keywords, operators, delimiters, and other syntactic components.

2. *Annotate Locations*: Attach precise location metadata (e.g., line and column numbers) to each token to facilitate debugging.

3. *Handle Errors*: Detect invalid tokens, highlight their location, and provide meaningful annotations to help the user
   understand and correct mistakes.

4. *Suggest Corrections*: For errors such as misspelled keywords or invalid identifiers, the system will offer suggestions
   or guesses for what might have been intended.


#### Features

1. Token Analysis:
	- Reserved keywords are checked and validated.
	- Identifiers and constants are recognised according to lexical rules.
	- Errors are marked when tokens deviate from expectations.
2. Error Detection and Annotation:
	- Invalid tokens are flagged with precise locations.
	- Error messages describe the issue and possible causes.
	- The system attempts to suggest corrections for misspellings or unintended usage.
3. Suggestions:
	- For misspelled keywords, the system provides likely matches using string similarity measures.
	- For misplaced tokens, suggestions are made based on contextual rules.
4. Extensibility:
	- Built with modularity to allow integration with parsers.
	- Easily adjustable for other PL/0-like languages or entirely new grammars.


#### Workflow

1. Input Source File: A '.pas' file containing source code is provided as input.

2. Tokenisation:
	- The tokeniser scans the input line by line.
	- Tokens are extracted based on regular expressions and language rules.

3. Error Handling:
	- If a token cannot be matched, it is marked as an error.
	- Annotations include the token’s location and a descriptive error message.

4. Output:
	- The tokenised output is saved to a file, with errors and suggestions highlighted for easy debugging.


#### Challenges and Solutions

1. Handling Ambiguities:
	- Challenge: Similar-looking tokens or partial matches may cause confusion.
	- Solution: Use greedy matching and backtracking to ensure the longest valid token is selected.

2.	Providing Useful Suggestions:
	- Challenge: Generating accurate guesses for misspelled keywords.
	- Solution: Implement a string similarity algorithm (e.g. Levenshtein distance).

3.	Annotating Errors Precisely:
	- Challenge: Maintaining accurate line and column counts during tokenisation.
	- Solution: Include metadata updates for every scanned character.

__Roadmap__

1: Implement the basic tokeniser with annotation support. DONE.

2: Add error detection and basic correction suggestions.

3: Extend to handle more complex language features and integrate with a parser.

4: Optimise for performance and release a production-ready version.

__Implementation Languages__

- *Python*: Ideal for rapid development, string manipulation, and prototyping error-detection features.
- *JavaScript*: Suitable for browser-based tokenisation tools, illustrating process or integrating into web development workflows.
- *C*: Provides performance benefits for large-scale or production-grade systems, especially in embedded environments.
