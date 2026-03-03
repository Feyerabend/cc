/*
 * lexer.c - table-driven finite-state lexer
 *
 * Tokenises a C-expression-like language.
 * Features beyond a minimal lexer:
 *
 *   * string literals  "hello \"world\""
 *   * line comments    // until newline
 *   * compound ops     == != <= >= && ||
 *   * hex integers     0x1A3F
 *   * source line tracking
 *
 * The entire machine is one 2-D table T[state][input_class].
 * The hot loop never branches on token type - it just indexes
 * the table and follows edges.
 */

#include <stdio.h>
#include <ctype.h>
#include <string.h>


/* TOKEN KINDS */

typedef enum {
    TOK_INT,        /* 42  0x2A                            */
    TOK_FLOAT,      /* 3.14                                */
    TOK_IDENT,      /* foo  _bar  x123                     */
    TOK_STRING,     /* "hello"                             */
    TOK_OP,         /* +  -  *  /  =  <  >  !  ...         */
    TOK_OP2,        /* ==  !=  <=  >=  &&  ||              */
    TOK_LPAREN,     /* (                                   */
    TOK_RPAREN,     /* )                                   */
    TOK_COMMENT,    /* // ...                              */
    TOK_EOF,        /* end of input                        */
    TOK_ERROR,      /* unexpected character                */
    TOK__COUNT
} TokKind;

static const char *TOK_NAME[TOK__COUNT] = {
    "INT", "FLOAT", "IDENT", "STRING",
    "OP", "OP2", "LPAREN", "RPAREN",
    "COMMENT", "EOF", "ERROR"
};


/* TOKEN  (result type) */

typedef struct {
    TokKind kind;
    const char *start;   /* pointer into original source  */
    int len;             /* byte length of lexeme */
    int line;            /* 1-based source line */
} Token;



/*  LEXER STATES */

typedef enum {
    S_START,    /* initial / between tokens                */
    S_INT,      /* consuming decimal digits                */
    S_HEX,      /* consuming hex digits after 0x           */
    S_ZERO,     /* just saw '0' - hex prefix or plain int? */
    S_FLOAT,    /* consuming digits after decimal point    */
    S_IDENT,    /* consuming [a-zA-Z0-9_]+                 */
    S_STRING,   /* inside "..."                            */
    S_STR_ESC,  /* just saw backslash inside a string      */
    S_OP1,      /* saw one op char - single or compound?   */
    S_COMMENT,  /* consuming // comment body to newline    */
    S_DONE,     /* terminal: emit token                    */
    S_ERROR,    /* terminal: emit error                    */
    S__COUNT
} State;


/* 
 *  INPUT CHARACTER CLASSES
 *
 *  Collapse 256 chars into a small alphabet so the table
 *  stays manageable.  The classifier runs once per char.
 */

typedef enum {
    C_SPACE,    /* ' '  '\t'  '\r'                         */
    C_NEWLINE,  /* '\n'  - tracked for line numbers        */
    C_DIGIT,    /* '1'-'9'                                 */
    C_ZERO,     /* '0'  - special: might start 0x...       */
    C_XSPEC,    /* 'x' or 'X'  - hex prefix after zero     */
    C_HEX,      /* 'a'-'f'  'A'-'F'                        */
    C_ALPHA,    /* other letters + '_'                     */
    C_DOT,      /* '.'                                     */
    C_DQUOTE,   /* '"'                                     */
    C_BACKSL,   /* '\'                                     */
    C_SLASH,    /* '/'                                     */
    C_OPCHAR,   /* + - * = < > ! & | ^ % ~                 */
    C_LPAREN,   /* '('                                     */
    C_RPAREN,   /* ')'                                     */
    C_NUL,      /* '\0'  - end of input                    */
    C_OTHER,    /* anything not listed above               */
    C__COUNT
} Class;

static Class classify(char c)
{
    if (c == ' ' || c == '\t' || c == '\r')    return C_SPACE;
    if (c == '\n')                             return C_NEWLINE;
    if (c == '0')                              return C_ZERO;
    if (isdigit((unsigned char)c))             return C_DIGIT;
    if (c == 'x' || c == 'X')                  return C_XSPEC;
    if ((c >= 'a' && c <= 'f') ||
        (c >= 'A' && c <= 'F'))                return C_HEX;
    if (isalpha((unsigned char)c) || c == '_') return C_ALPHA;
    if (c == '.')                              return C_DOT;
    if (c == '"')                              return C_DQUOTE;
    if (c == '\\')                             return C_BACKSL;
    if (c == '/')                              return C_SLASH;
    if (c && strchr("+-*=<>!&|^%~", c))        return C_OPCHAR;
    if (c == '(')                              return C_LPAREN;
    if (c == ')')                              return C_RPAREN;
    if (c == '\0')                             return C_NUL;
    return C_OTHER;
}


/* 
 *  TRANSITION TABLE
 *
 *  Each cell is an Edge: { next_state, emit, advance }
 *
 *    next_state  - where to go after this character
 *    emit        - which token kind this edge produces
 *                  (TOK_ERROR here means "keep going, no
 *                  emission yet" - only terminal edges carry
 *                  a real kind)
 *    advance     - 1: consume the char  0: leave it for the
 *                  next call (boundary: char triggered stop)
 *
 *  Column order matches the Class enum exactly.
 */

typedef struct {
    State   next;
    TokKind emit;
    int     advance;
} Edge;

/* Shorthand macros - undefed after the table */
#define NX            TOK_ERROR           /* Not eXiting: no emission yet */
#define GO(s)         { s,       NX,  1 } /* advance + transition         */
#define STAY(s)       { s,       NX,  1 } /* same state, advance          */
#define EMIT(t)       { S_DONE,  t,   1 } /* consume char, emit token     */
#define EMIT_BACK(t)  { S_DONE,  t,   0 } /* leave char, emit token       */
#define ERR           { S_ERROR, NX,  1 } /* consume char, emit error     */

/*
 * Column order:
 *   SPC   NL    DIG   ZER   XSP   HEX   ALP   DOT
 *   DQ    BSL   SLS   OPC   LP    RP    NUL   OTH
 */
static const Edge T[S__COUNT][C__COUNT] = {

/* -- S_START
   Skip whitespace; route first char to the correct sub-machine.        */
[S_START] = {
    STAY(S_START),       /* C_SPACE   skip                              */
    STAY(S_START),       /* C_NEWLINE skip  (line++ handled in loop)    */
    GO(S_INT),           /* C_DIGIT   start decimal int                 */
    GO(S_ZERO),          /* C_ZERO    '0': might be 0x... or just 0     */
    GO(S_IDENT),         /* C_XSPEC   'x'/'X' as ident start            */
    GO(S_IDENT),         /* C_HEX     a-f as ident start                */
    GO(S_IDENT),         /* C_ALPHA   normal identifier                 */
    ERR,                 /* C_DOT     bare '.' not valid here           */
    GO(S_STRING),        /* C_DQUOTE  open string literal               */
    ERR,                 /* C_BACKSL  bare backslash: error             */
    GO(S_OP1),           /* C_SLASH   '/' - could be '//'               */
    GO(S_OP1),           /* C_OPCHAR  single or compound op             */
    EMIT(TOK_LPAREN),    /* C_LPAREN                                    */
    EMIT(TOK_RPAREN),    /* C_RPAREN                                    */
    EMIT(TOK_EOF),       /* C_NUL     end of input                      */
    ERR,                 /* C_OTHER   unknown character                 */
},

/* -- S_ZERO
   Just consumed '0'.  Wait to see if 'x'/'X' follows for hex mode.     */
[S_ZERO] = {
    EMIT_BACK(TOK_INT),  /* C_SPACE   lone zero done                    */
    EMIT_BACK(TOK_INT),  /* C_NEWLINE                                   */
    GO(S_INT),           /* C_DIGIT   '00...' - treat as decimal        */
    GO(S_INT),           /* C_ZERO    '00'                              */
    GO(S_HEX),           /* C_XSPEC   '0x' --> enter hex mode           */
    EMIT_BACK(TOK_INT),  /* C_HEX     '0a' - boundary                   */
    EMIT_BACK(TOK_INT),  /* C_ALPHA   '0z' - boundary                   */
    GO(S_FLOAT),         /* C_DOT     '0.' --> float                    */
    EMIT_BACK(TOK_INT),  /* C_DQUOTE  0 before string                   */
    EMIT_BACK(TOK_INT),  /* C_BACKSL                                    */
    EMIT_BACK(TOK_INT),  /* C_SLASH                                     */
    EMIT_BACK(TOK_INT),  /* C_OPCHAR                                    */
    EMIT_BACK(TOK_INT),  /* C_LPAREN                                    */
    EMIT_BACK(TOK_INT),  /* C_RPAREN                                    */
    EMIT_BACK(TOK_INT),  /* C_NUL                                       */
    ERR,                 /* C_OTHER                                     */
},

/* -- S_INT
   Consuming decimal digits.                                            */
[S_INT] = {
    EMIT_BACK(TOK_INT),  /* C_SPACE   boundary                          */
    EMIT_BACK(TOK_INT),  /* C_NEWLINE boundary                          */
    STAY(S_INT),         /* C_DIGIT   keep going                        */
    STAY(S_INT),         /* C_ZERO    keep going                        */
    EMIT_BACK(TOK_INT),  /* C_XSPEC   '42x' - boundary                  */
    EMIT_BACK(TOK_INT),  /* C_HEX     '42a' - boundary                  */
    EMIT_BACK(TOK_INT),  /* C_ALPHA   boundary                          */
    GO(S_FLOAT),         /* C_DOT     '3.' --> float                    */
    EMIT_BACK(TOK_INT),  /* C_DQUOTE                                    */
    EMIT_BACK(TOK_INT),  /* C_BACKSL                                    */
    EMIT_BACK(TOK_INT),  /* C_SLASH                                     */
    EMIT_BACK(TOK_INT),  /* C_OPCHAR                                    */
    EMIT_BACK(TOK_INT),  /* C_LPAREN                                    */
    EMIT_BACK(TOK_INT),  /* C_RPAREN                                    */
    EMIT_BACK(TOK_INT),  /* C_NUL                                       */
    ERR,                 /* C_OTHER                                     */
},

/* -- S_HEX
   Consuming hex digits after '0x'.                                     */
[S_HEX] = {
    EMIT_BACK(TOK_INT),  /* C_SPACE                                     */
    EMIT_BACK(TOK_INT),  /* C_NEWLINE                                   */
    STAY(S_HEX),         /* C_DIGIT   0-9 valid in hex                  */
    STAY(S_HEX),         /* C_ZERO    '0' valid in hex                  */
    EMIT_BACK(TOK_INT),  /* C_XSPEC   '0x1x' - boundary                 */
    STAY(S_HEX),         /* C_HEX     a-f A-F                           */
    EMIT_BACK(TOK_INT),  /* C_ALPHA   '0x1z' - boundary                 */
    EMIT_BACK(TOK_INT),  /* C_DOT     no hex floats                     */
    EMIT_BACK(TOK_INT),  /* C_DQUOTE                                    */
    EMIT_BACK(TOK_INT),  /* C_BACKSL                                    */
    EMIT_BACK(TOK_INT),  /* C_SLASH                                     */
    EMIT_BACK(TOK_INT),  /* C_OPCHAR                                    */
    EMIT_BACK(TOK_INT),  /* C_LPAREN                                    */
    EMIT_BACK(TOK_INT),  /* C_RPAREN                                    */
    EMIT_BACK(TOK_INT),  /* C_NUL                                       */
    ERR,                 /* C_OTHER                                     */
},

/* -- S_FLOAT
   Consuming digits after the decimal point.                            */
[S_FLOAT] = {
    EMIT_BACK(TOK_FLOAT),/* C_SPACE                                     */
    EMIT_BACK(TOK_FLOAT),/* C_NEWLINE                                   */
    STAY(S_FLOAT),       /* C_DIGIT   keep going                        */
    STAY(S_FLOAT),       /* C_ZERO    keep going                        */
    EMIT_BACK(TOK_FLOAT),/* C_XSPEC                                     */
    EMIT_BACK(TOK_FLOAT),/* C_HEX                                       */
    EMIT_BACK(TOK_FLOAT),/* C_ALPHA                                     */
    EMIT_BACK(TOK_FLOAT),/* C_DOT     second dot - boundary             */
    EMIT_BACK(TOK_FLOAT),/* C_DQUOTE                                    */
    EMIT_BACK(TOK_FLOAT),/* C_BACKSL                                    */
    EMIT_BACK(TOK_FLOAT),/* C_SLASH                                     */
    EMIT_BACK(TOK_FLOAT),/* C_OPCHAR                                    */
    EMIT_BACK(TOK_FLOAT),/* C_LPAREN                                    */
    EMIT_BACK(TOK_FLOAT),/* C_RPAREN                                    */
    EMIT_BACK(TOK_FLOAT),/* C_NUL                                       */
    ERR,                 /* C_OTHER                                     */
},

/* -- S_IDENT
   Consuming [a-zA-Z0-9_]+ identifier characters.                       */
[S_IDENT] = {
    EMIT_BACK(TOK_IDENT),/* C_SPACE                                     */
    EMIT_BACK(TOK_IDENT),/* C_NEWLINE                                   */
    STAY(S_IDENT),       /* C_DIGIT   digits valid mid-ident            */
    STAY(S_IDENT),       /* C_ZERO                                      */
    STAY(S_IDENT),       /* C_XSPEC   'x'/'X' valid in ident            */
    STAY(S_IDENT),       /* C_HEX     a-f valid in ident                */
    STAY(S_IDENT),       /* C_ALPHA                                     */
    EMIT_BACK(TOK_IDENT),/* C_DOT                                       */
    EMIT_BACK(TOK_IDENT),/* C_DQUOTE                                    */
    EMIT_BACK(TOK_IDENT),/* C_BACKSL                                    */
    EMIT_BACK(TOK_IDENT),/* C_SLASH                                     */
    EMIT_BACK(TOK_IDENT),/* C_OPCHAR                                    */
    EMIT_BACK(TOK_IDENT),/* C_LPAREN                                    */
    EMIT_BACK(TOK_IDENT),/* C_RPAREN                                    */
    EMIT_BACK(TOK_IDENT),/* C_NUL                                       */
    ERR,                 /* C_OTHER                                     */
},

/* -- S_STRING
   Inside "...": accumulate everything; backslash escapes into S_STR_ESC.  */
[S_STRING] = {
    STAY(S_STRING),      /* C_SPACE                                     */
    STAY(S_STRING),      /* C_NEWLINE  multi-line string (warn later)   */
    STAY(S_STRING),      /* C_DIGIT                                     */
    STAY(S_STRING),      /* C_ZERO                                      */
    STAY(S_STRING),      /* C_XSPEC                                     */
    STAY(S_STRING),      /* C_HEX                                       */
    STAY(S_STRING),      /* C_ALPHA                                     */
    STAY(S_STRING),      /* C_DOT                                       */
    EMIT(TOK_STRING),    /* C_DQUOTE  closing '"' - done, include it    */
    GO(S_STR_ESC),       /* C_BACKSL  escape sequence                   */
    STAY(S_STRING),      /* C_SLASH                                     */
    STAY(S_STRING),      /* C_OPCHAR                                    */
    STAY(S_STRING),      /* C_LPAREN                                    */
    STAY(S_STRING),      /* C_RPAREN                                    */
    ERR,                 /* C_NUL     unterminated string               */
    STAY(S_STRING),      /* C_OTHER                                     */
},

/* -- S_STR_ESC
   The character immediately after a backslash inside a string.
   Whatever it is, consume it and go back to S_STRING.                   */
[S_STR_ESC] = {
    GO(S_STRING),        /* C_SPACE                                     */
    GO(S_STRING),        /* C_NEWLINE  line continuation                */
    GO(S_STRING),        /* C_DIGIT    \0 \n \t etc.                    */
    GO(S_STRING),        /* C_ZERO     \0                               */
    GO(S_STRING),        /* C_XSPEC    \x hex escape                    */
    GO(S_STRING),        /* C_HEX                                       */
    GO(S_STRING),        /* C_ALPHA    \n \t \r etc.                    */
    GO(S_STRING),        /* C_DOT                                       */
    GO(S_STRING),        /* C_DQUOTE   \"                               */
    GO(S_STRING),        /* C_BACKSL   \\                               */
    GO(S_STRING),        /* C_SLASH                                     */
    GO(S_STRING),        /* C_OPCHAR                                    */
    GO(S_STRING),        /* C_LPAREN                                    */
    GO(S_STRING),        /* C_RPAREN                                    */
    ERR,                 /* C_NUL      backslash at end of input        */
    GO(S_STRING),        /* C_OTHER                                     */
},

/* -- S_OP1
   We just consumed one operator character.  A second op-char extends it
   to a compound operator (==, !=, <=, >=, &&, ||...).
   A second '/' means we're starting a line comment.
   Anything else closes the single-char operator.                         */
[S_OP1] = {
    EMIT_BACK(TOK_OP),   /* C_SPACE   single op done                    */
    EMIT_BACK(TOK_OP),   /* C_NEWLINE                                   */
    EMIT_BACK(TOK_OP),   /* C_DIGIT                                     */
    EMIT_BACK(TOK_OP),   /* C_ZERO                                      */
    EMIT_BACK(TOK_OP),   /* C_XSPEC                                     */
    EMIT_BACK(TOK_OP),   /* C_HEX                                       */
    EMIT_BACK(TOK_OP),   /* C_ALPHA                                     */
    EMIT_BACK(TOK_OP),   /* C_DOT                                       */
    EMIT_BACK(TOK_OP),   /* C_DQUOTE                                    */
    EMIT_BACK(TOK_OP),   /* C_BACKSL                                    */
    GO(S_COMMENT),       /* C_SLASH   '//' --> consume comment body     */
    EMIT(TOK_OP2),       /* C_OPCHAR  '==' '!=' '<=' '>=' '&&' '||'     */
    EMIT_BACK(TOK_OP),   /* C_LPAREN                                    */
    EMIT_BACK(TOK_OP),   /* C_RPAREN                                    */
    EMIT_BACK(TOK_OP),   /* C_NUL                                       */
    EMIT_BACK(TOK_OP),   /* C_OTHER                                     */
},

/* -- S_COMMENT
   Consuming the body of a // comment.  Stop at newline or EOF.          */
[S_COMMENT] = {
    STAY(S_COMMENT),         /* C_SPACE                                 */
    EMIT_BACK(TOK_COMMENT),  /* C_NEWLINE  newline ends the comment     */
    STAY(S_COMMENT),         /* C_DIGIT                                 */
    STAY(S_COMMENT),         /* C_ZERO                                  */
    STAY(S_COMMENT),         /* C_XSPEC                                 */
    STAY(S_COMMENT),         /* C_HEX                                   */
    STAY(S_COMMENT),         /* C_ALPHA                                 */
    STAY(S_COMMENT),         /* C_DOT                                   */
    STAY(S_COMMENT),         /* C_DQUOTE                                */
    STAY(S_COMMENT),         /* C_BACKSL                                */
    STAY(S_COMMENT),         /* C_SLASH                                 */
    STAY(S_COMMENT),         /* C_OPCHAR                                */
    STAY(S_COMMENT),         /* C_LPAREN                                */
    STAY(S_COMMENT),         /* C_RPAREN                                */
    EMIT_BACK(TOK_COMMENT),  /* C_NUL     EOF ends comment too          */
    STAY(S_COMMENT),         /* C_OTHER                                 */
},

/* S_DONE and S_ERROR are terminal - never looked up */
};

#undef NX
#undef GO
#undef STAY
#undef EMIT
#undef EMIT_BACK
#undef ERR


/* LEXER CONTEXT */

typedef struct {
    const char *src;    /* current read position     */
    int         line;   /* current 1-based line no.  */
} Lexer;

static Lexer lexer_new(const char *source) {
    return (Lexer){ .src = source, .line = 1 };
}


/* THE "HOT LOOP"  - pure table walk, no token-kind branching */

Token next_token(Lexer *lx) {
    const char *p         = lx->src;
    const char *tok_start = p;
    State       state     = S_START;
    TokKind     last_emit = TOK_ERROR;

    while (state < S_DONE) {
        Class       cl = classify(*p);
        const Edge *e  = &T[state][cl];

        /* track source line numbers */
        if (cl == C_NEWLINE)
            lx->line++;

        /* slide the token-start pointer past whitespace */
        if (state == S_START && e->next == S_START)
            tok_start = p + 1;

        last_emit = e->emit;
        if (e->advance) ++p;
        state = e->next;
    }

    lx->src = p;
    return (Token){
        .kind  = (state == S_DONE) ? last_emit : TOK_ERROR,
        .start = tok_start,
        .len   = (int)(p - tok_start),
        .line  = lx->line,
    };
}


/* DRIVER */

static const char SOURCE[] =
    "// compute discriminant\n"
    "disc = (b * b) - (4 * a * c)\n"
    "flag = (disc >= 0) && (a != 0)\n"
    "label = \"result: \\\"ok\\\"\"\n"
    "addr  = 0xFF3C + base\n"
    "ratio = 2.718 / scale\n";

int main(void) {
    Lexer lx = lexer_new(SOURCE);
    Token t;

    printf("LINE  %-8s  LEXEME\n", "KIND");
    printf("----  --------  ------\n");

    do {
        t = next_token(&lx);
        if (t.kind == TOK_COMMENT) continue;
        printf("%4d  %-8s  %.*s\n",
               t.line, TOK_NAME[t.kind], t.len, t.start);
    } while (t.kind != TOK_EOF && t.kind != TOK_ERROR);

    return 0;
}
