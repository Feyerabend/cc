
## CSV Parser in Python


### 1. Finite-State Machine (FSM) Approach

This CSV parser exemplifies a finite-state machine approach to parsing,
where the parser transitions between distinct states based on input characters:
- *Normal state*: Processing regular field content
- *Quoted state*: Inside a quoted field (triggered by `quote_char`)
- *Field boundary*: Encountering delimiters outside quotes
- *Row boundary*: Encountering newlines outside quotes

In parsing theory, FSMs are particularly well-suited for regular languages and
simple context-free constructs. The parser maintains state through the `in_quotes`
boolean flag, which determines how to interpret each character.


### 2. Character-by-Character Streaming

Unlike parsers that require full tokenization upfront,
this CSV parser processes input as a character stream:
- Each character is examined exactly once (single-pass parsing)
- The `buffer` accumulates characters for the current field
- State transitions occur based on delimiter and quote characters

This streaming approach demonstrates *online parsing*, where decisions are made
incrementally without needing to see the entire input first.
This is efficient for large CSV files that might not fit entirely in memory.


### 3. Context-Sensitivity in Quoted Fields

CSV parsing presents an interesting challenge in parsing theory
due to context-dependent interpretation:

```
Regular field: delimiter ends field
Quoted field: delimiter is literal content
```

The grammar can be informally described as:

```ebnf
csv ::= row (newline row)*
row ::= field (delimiter field)*
field ::= quoted_field | unquoted_field
quoted_field ::= quote_char (any_char_except_quote | escaped_quote)* quote_char
unquoted_field ::= (any_char_except_delimiter_or_newline)*
```

The parser handles this context-sensitivity through the `in_quotes` state variable,
which changes the interpretation of delimiters and newlines.


### 4. Escape Sequence Handling

The parser implements a simple quote-toggling mechanism:
- Each `quote_char` toggles the `in_quotes` state
- This handles the CSV convention where `""` within quoted fields represents a literal quote

While functional for basic cases, this approach has limitations with more
complex escaping scenarios, which would require additional state tracking.


### 5. Whitespace and Line Ending Normalization

The parser treats both `\r` (carriage return) and `\n` (newline) as row terminators:
```python
elif char in "\r\n" and not in_quotes:
```

This demonstrates *input normalization*, handling different line ending conventions
(Unix `\n`, Windows `\r\n`, old Mac `\r`) uniformly. In parsing theory, this
preprocessing step simplifies the main parsing logic.


### 6. Delimiter Parameterization

The parser accepts configurable `delimiter` and `quote_char` parameters,
making it adaptable to CSV variants:
- Standard CSV: `delimiter=","`, `quote_char='"'`
- TSV (Tab-Separated Values): `delimiter="\t"`
- Semicolon-delimited: `delimiter=";"`

This parameterization demonstrates the *parser generator* concept,
where a single parsing framework handles multiple related formats.


### 7. Efficiency Considerations

The parser achieves *O(n)* time complexity, where n is the number of characters:
- Single pass through the input
- Constant-time state transitions
- String concatenation in Python is amortized O(1) for the += operator

Space complexity is O(m), where m is the total size of parsed data,
which is optimal since the output itself requires this space.

### Potential Improvements

1. *Enhanced Escape Handling*:
   - Support for `\"` style escaping in addition to `""` doubling
   - Handle escaped newlines and other special characters
   - Align with RFC 4180 CSV specification more closely

2. *Error Detection and Recovery*:
   - Detect unclosed quoted fields (e.g., missing closing quote)
   - Report line/column numbers for malformed input
   - Implement error recovery strategies (skip to next row, insert missing quotes)

3. *Type Inference*:
   - Automatically detect and convert numeric fields to int/float
   - Parse boolean values (true/false, yes/no)
   - Handle NULL/empty value distinction

4. *Performance Optimization*:
   - Use list accumulation instead of string concatenation for large fields
   - Implement lazy parsing (generator-based) for memory-efficient processing
   - Add support for parallel parsing of large files

5. *Standards Compliance*:
   - Full RFC 4180 compliance validation
   - Support for header row detection
   - Handle byte order marks (BOM) in UTF-8 files

6. *Advanced Features*:
   - Column count validation (ensure consistent field count per row)
   - Comment line support (e.g., lines starting with `#`)
   - Multi-line field support with proper quoting

*Project/Exercise: Extend the parser to implement RFC 4180
compliance with proper error reporting and type inference.*


### Summary

This CSV parser demonstrates practical application of finite-state
machine concepts to parsing. It efficiently handles the context-dependent
nature of CSV through state tracking, processes input in a single
streaming pass, and provides flexibility through parameterization.
While simplified compared to production CSV parsers, it captures the
essential parsing theory concepts and provides a solid foundation for
understanding delimiter-separated value formats. Enhancements toward
standards compliance and robust error handling would make it suitable
for production use while reinforcing theoretical parsing principles.


