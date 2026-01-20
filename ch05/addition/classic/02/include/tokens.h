#ifndef TOKENS_H
#define TOKENS_H

typedef enum {
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
} Symbol;

extern int fromSourceToTokens(const char *sourceFilename, const char *tokenFilename);

#endif  // TOKENS_H