
## JSON Parser in C

### 1. Recursive Descent Parsing

This parser exemplifies recursive descent parsing, where each non-terminal in the JSON
grammar corresponds to a dedicated parsing function:
- `json_parse_object` handles JSON objects.
- `json_parse_array` handles arrays.
- `json_parse_string` handles strings.
- And so on for numbers, booleans, and null values.

In parsing theory, recursive descent parsers are a top-down approach to parsing, starting
from the root of the grammar (in this case, a JSON value) and decomposing it into its components.


### 2. Handling Context-Free Grammars

JSON can be described with a context-free grammar (CFG). The parser aligns with the grammar as follows:

```ebnf
    value ::= object | array | string | number | "true" | "false" | "null"
    object ::= "{" (string ":" value ("," string ":" value)*)? "}"
    array ::= "[" (value ("," value)*)? "]"
    string ::= "\"" .* "\""
    number ::= [+-]?([0-9]+(.[0-9]+)?) ([eE][+-]?[0-9]+)?
```

The parser implements this grammar through its structure, functions, and control flow. For instance:
- Objects and arrays use loops to handle their repetitive constructs (e.g. key-value pairs or array items).
- Terminal symbols like "true", "null", or "\"" are directly matched and processed.


### 3. Lexical Analysis and Tokenization

Unlike parsers that separate tokenization and syntax analysis, this JSON parser processes characters directly
within parsing functions. Examples:
- Strings are parsed by identifying delimiters (").
- Numbers are parsed by recognizing numeric sequences and using sscanf for conversion.
- Whitespace is skipped using the skip_whitespace function, akin to ignoring insignificant tokens in lexical analysis.

While not explicitly tokenized, this approach is equivalent to on-the-fly lexical analysis, which simplifies
the implementation but couples lexical and syntactic concerns.


### 4. Abstract Syntax Tree (AST) Construction

The JsonValue structure serves as an Abstract Syntax Tree (AST), representing the parsed JSON data:
- Objects are stored as arrays of key-value pairs.
- Arrays are represented as lists of JSON values.
- Primitives (e.g. strings, numbers) are directly stored.

In parsing theory, the construction of an AST is a standard step after parsing to represent the hierarchical
structure of the input data.


### 5. Error Detection

The parser incorporates basic error detection:
- If an unexpected character appears (such as a missing ':' in an object), the parser returns NULL.
- Functions like `expect_char` ensure that mandatory characters (e.g. ',' or '}') are present.

This approach is a practical application of error handling in parsing theory, though it lacks advanced error
recovery strategies (e.g. skipping malformed sections).


### 6. Efficiency

Parsing is performed in a single pass with recursive calls, resulting in linear time complexity relative
to the size of the JSON input ($\`O(n)\`$), assuming well-formed JSON. Parsing theory often considers such
efficiency for practical applications.

#### Potential Improvements

1. *Lexer Integration*:
   Introducing a lexer to tokenize JSON into recognizable units (STRING, NUMBER, COMMA, etc.)
   would decouple lexical and syntactic concerns, improving modularity.

2. *Grammar Validation*:
   The parser assumes JSON input adheres to the grammar. Incorporating grammar validation would
   help ensure all constructs are properly formed.

3. *Error Recovery*:
   Current error handling stops parsing upon encountering an invalid structure. Implementing
   strategies like synchronizing at the next valid token (e.g. '}' or ']') would enhance robustness.

4. *Advanced Tree Representation*:
   Enhance the AST to include line/column information for each node, useful for debugging
   and error reporting.

*Project/Exercise: Amend the parser with one or several of these suggestions.*


### Summary

This JSON parser is a practical embodiment of parsing theory concepts, particularly *recursive descent parsing*.
It adheres to the JSON grammar, constructs an AST-like structure, and demonstrates efficient parsing with basic
error handling. Enhancements informed by theoretical principles could make it more robust and extensible,
bridging the gap between theory and practical implementation.

