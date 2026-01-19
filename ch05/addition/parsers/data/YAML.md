
## YAML Parser in Python


### 1. Indentation-Sensitive Parsing

This YAML parser exemplifies *indentation-sensitive parsing*, where whitespace
has syntactic meaning beyond mere token separation. The parser maintains an
`indentation_stack` to track nesting levels:
- Each increase in indentation pushes a new level onto the stack
- Decreases in indentation pop levels until the current indent matches
- Misaligned indentation triggers parsing errors

In parsing theory, indentation-sensitive languages (like Python, YAML, and Haskell)
require special handling because they cannot be described by traditional context-free
grammars alone. The indentation stack effectively implements a *context-sensitive*
parsing mechanism.


### 2. Recursive Descent with Indentation Context

The parser uses recursive descent parsing enhanced with indentation awareness:
- `_parse_element()`: Determines element type and delegates to specific parsers
- `_parse_sequence()`: Handles list structures (lines starting with `-`)
- `_parse_mapping()`: Handles key-value pairs (lines containing `:`)
- `_parse_scalar()`: Handles primitive values (strings, numbers, booleans)

Each function respects the current indentation context, making this a *context-aware
recursive descent parser*. The grammar can be informally described as:

```ebnf
element ::= sequence | mapping | scalar
sequence ::= ('-' scalar | '-' mapping) (newline '-' element)*
mapping ::= key ':' (scalar | newline indented_element)
scalar ::= string | number | boolean | null
```

However, the indentation rules add a layer of context-sensitivity that
"pure" EBNF really cannot express.


### 3. Line-Oriented Parsing

Unlike character-stream parsers (like the CSV parser), this YAML parser operates on lines:
```python
self.lines = yaml_str.splitlines()
self.current_line = 0
```

This *line-oriented approach* simplifies indentation tracking since indentation
is inherently a line-level concept. The parser advances through lines using the
`current_line` index, enabling:
- Easy lookahead for indentation comparison
- Simple comment and empty line skipping
- Clear line-by-line error reporting


### 4. Indentation Validation

The `_check_indentation()` function implements strict indentation rules:
```python
def _check_indentation(self, indent_level):
    if indent_level > self.indentation_stack[-1]:
        self.indentation_stack.append(indent_level)  # Deeper nesting
    elif indent_level < self.indentation_stack[-1]:
        while self.indentation_stack and indent_level < self.indentation_stack[-1]:
            self.indentation_stack.pop()  # Return to previous level
        if indent_level != self.indentation_stack[-1]:
            raise ValueError("Improper indentation")  # Misaligned
```

This demonstrates *layout-sensitive parsing*, where the parser enforces that
dedentation must return to a previously established indentation level.
Arbitrary indentation is rejected, maintaining structural integrity.


### 5. Dual Parsing Modes: Inline vs. Block

The parser handles both inline and block-style YAML:

*Inline mapping:*
```yaml
key: value
```

*Block mapping:*
```yaml
key:
  nested_key: nested_value
```

This duality is managed by checking if a value exists after the colon:
```python
if value:  # inline
    mapping[key] = self._parse_scalar(value)
else:  # block (indented child)
    child_element = self._parse_element()
```

This demonstrates *look-ahead parsing*, where the parser examines the
current state to determine which parsing strategy to employ.


### 6. Type Inference in Scalars

The `_parse_scalar()` function implements automatic type inference:
- Quoted strings: `"text"` or `'text'` → string (quotes removed)
- Numbers: `123` → int, `3.14` → float
- Booleans: `true`/`false` → boolean
- Unquoted text: → string

This is a form of *semantic analysis* integrated into parsing, where
syntactic patterns determine data types. The parser prioritizes more
specific patterns (quoted, numeric) before defaulting to generic strings.


### 7. Sequence Parsing Complexity

The `_parse_sequence()` function handles nested structures within sequences:
```python
if ':' in item:  # inline mapping inside sequence
    self.current_line += 1
    sequence.append(self._parse_mapping(indent_level + 1))
else:
    sequence.append(self._parse_scalar(item))
```

This demonstrates *compositional parsing*, where complex structures
(sequences containing mappings) are built from simpler parsing primitives.
The recursion handles arbitrary nesting depth.


### 8. Comment and Whitespace Handling

The parser filters out semantic-free content:
```python
if not line or line.startswith('#'):  # empty lines and comments
    self.current_line += 1
    return self._parse_element()
```

This preprocessing step aligns with the *lexical analysis* phase in traditional
parsers, though integrated into the main parsing logic rather than separated into a distinct lexer.


### 9. Efficiency Analysis

The parser's time complexity is *O(n × d)*, where:
- n = number of lines
- d = maximum indentation depth (for stack operations)

In practice, d is typically small (< 10), making this approximately O(n).
Space complexity is O(d) for the indentation stack plus O(m) for the parsed data structure.


### Potential Improvements

1. *Enhanced Indentation Support*:
   - Validate consistent indentation width (2 spaces vs. 4 spaces)
   - Better error messages showing expected vs. actual indentation
   - Support for explicit indentation indicators (e.g., `>`, `|` for literals)

2. *Full YAML Specification Support*:
   - Anchors and aliases (`&anchor`, `*alias`)
   - Multi-line strings with folding (`>`) and literal (`|`) styles
   - Document separators (`---`, `...`)
   - Tags for explicit type specification (`!!str`, `!!int`)
   - Complex keys (mappings as keys)

3. *Error Recovery and Reporting*:
   - Line and column number tracking for precise error locations
   - Context in error messages (show surrounding lines)
   - Attempt to continue parsing after errors (recover at next valid indentation level)
   - Warnings for ambiguous constructs

4. *Null and Special Value Handling*:
   - Distinguish between `null`, empty string `""`, and absence of value
   - Support YAML null variants: `null`, `~`, empty value
   - Handle special numeric values: `.inf`, `-.inf`, `.nan`

5. *Performance Optimizations*:
   - Cache indentation level calculations
   - Use generators for lazy parsing of large files
   - Optimize string operations (reduce repeated `strip()` calls)

6. *Advanced Features*:
   - Merge keys (`<<:`)
   - Flow collections (inline lists `[1, 2, 3]` and maps `{a: 1, b: 2}`)
   - Binary data support
   - Custom type resolution hooks

7. *Validation and Schema Support*:
   - Validate against YAML schema definitions
   - Ensure sequence items have consistent types
   - Enforce required keys in mappings

*Project/Exercise: Implement anchor and alias support, enabling YAML
references that reduce duplication in configuration files.*


### Comparison with Other Parsers

*vs. JSON Parser:*
- YAML: Indentation-based structure, no explicit delimiters
- JSON: Delimiter-based structure (`{}`, `[]`), no significant whitespace
- YAML allows more implicit structures; JSON requires explicit notation

*vs. XML Parser:*
- YAML: Minimal syntax, human-friendly
- XML: Verbose tags, machine-friendly
- Both support hierarchical data, but YAML emphasizes readability

*vs. CSV Parser:*
- YAML: Complex nested structures, multiple data types
- CSV: Flat tabular data, typically string-based
- CSV uses state machine; YAML uses recursive descent with context


### Summary

This YAML parser demonstrates sophisticated parsing techniques for indentation-sensitive languages.
It combines recursive descent parsing with context-aware indentation tracking, implements automatic
type inference, and handles both inline and block-style syntax. The indentation stack provides the
context-sensitivity needed to properly interpret YAML's significant whitespace, while the line-oriented
approach simplifies structural analysis. Though much simplified compared to full YAML 1.2 parsers,
it captures essential parsing theory concepts including layout-sensitive parsing, compositional
structure building, and semantic type inference. Extensions (your project) toward full specification
compliance would reinforce these concepts while producing a production-grade parser.

