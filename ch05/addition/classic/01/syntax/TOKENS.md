
## PL/E and Tokenisation

Tokenisation is the process of breaking the source code into meaningful units called tokens. In PL/E,
tokens correspond to:
	
1. Keywords: Reserved words such as const, var, procedure, begin, if, while, etc.
2. Identifiers: Names for variables, constants, and procedures.
3. Operators and Symbols: Includes arithmetic (+, -, *, /), relational (=, #, <, <=, >, >=), and
   assignment (:=) operators, as well as structural symbols like `;`, `,`, `.`.
4. Literals: Numeric values (such as '100').
5. Special Tokens: Markers such as ENDOFLINE and ENDOFFILE.

The list of tokens defined for PL/E is as follows:

```python
    NOP,
    IDENT,
    NUMBER,
    LPAREN,     // (
    RPAREN,     // )
    TIMES,      // *
    SLASH,      // /
    PLUS,       // +
    MINUS,      // -
    EQL,        // =
    NEQ,        // #
    LSS,        // <
    LEQ,        // <=
    GTR,        // >
    GEQ,        // >=
    CALLSYM,    // call
    BEGINSYM,   // begin
    SEMICOLON,  // ;
    ENDSYM,     // end
    IFSYM,      // if
    WHILESYM,   // while
    BECOMES,    // :=
    THENSYM,    // then
    DOSYM,      // do
    CONSTSYM,   // const
    COMMA,      // ,
    VARSYM,     // var
    PROCSYM,    // proc
    PERIOD,     // .
    ENDOFLINE,
    ENDOFFILE
```

Each token is associated with its type (such as NUMBER, IDENT) and may have a value (max, 100, etc.).


### Summary

The tokenisation process converts the above PL/E program into tokens like CONSTSYM, IDENT, BECOMES, etc.,
which are then parsed according to the EBNF grammar rules. This leads to the construction of an Abstract
Syntax Tree (AST), forming the backbone of the compilation process.
