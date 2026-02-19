// mol_lexer.c
#include "mol.h"

static void skip_ws_comments(Lexer *lex) {
    while (1) {
        while (lex->input[lex->pos] && isspace(lex->input[lex->pos])) {
            if (lex->input[lex->pos] == '\n') lex->line++;
            lex->pos++;
        }
        if (lex->input[lex->pos] == '/' && lex->input[lex->pos+1] == '/') {
            lex->pos += 2;
            while (lex->input[lex->pos] && lex->input[lex->pos] != '\n') lex->pos++;
        } else if (lex->input[lex->pos] == '/' && lex->input[lex->pos+1] == '*') {
            lex->pos += 2;
            while (lex->input[lex->pos] && !(lex->input[lex->pos]=='*' && lex->input[lex->pos+1]=='/')) {
                if (lex->input[lex->pos] == '\n') lex->line++;
                lex->pos++;
            }
            if (lex->input[lex->pos]) lex->pos += 2;
        } else break;
    }
}

static void set_tok(Lexer *lex, TokenType t, const char *text) {
    free(lex->current.text);
    lex->current.type = t;
    lex->current.text = strdup(text);
    lex->current.line = lex->line;
}

void next_token(Lexer *lex) {
    skip_ws_comments(lex);
    free(lex->current.text);
    lex->current.text = NULL;
    lex->current.line = lex->line;

    if (!lex->input[lex->pos]) {
        lex->current.type = TOK_EOF; return;
    }

    char ch = lex->input[lex->pos];

    /* integers */
    if (isdigit(ch)) {
        int start = lex->pos;
        int64_t val = 0;
        while (isdigit(lex->input[lex->pos])) {
            val = val * 10 + (lex->input[lex->pos] - '0');
            lex->pos++;
        }
        int len = lex->pos - start;
        lex->current.type    = TOK_INT;
        lex->current.int_val = val;
        lex->current.text = malloc(len + 1);
        strncpy(lex->current.text, lex->input + start, len);
        lex->current.text[len] = '\0';
        return;
    }

    /* string literals */
    if (ch == '"') {
        lex->pos++;
        char buf[4096]; int n = 0;
        while (lex->input[lex->pos] && lex->input[lex->pos] != '"') {
            if (lex->input[lex->pos] == '\\') {
                lex->pos++;
                switch (lex->input[lex->pos]) {
                    case 'n':  buf[n++] = '\n'; break;
                    case 't':  buf[n++] = '\t'; break;
                    case '"':  buf[n++] = '"';  break;
                    case '\\': buf[n++] = '\\'; break;
                    default:   buf[n++] = lex->input[lex->pos]; break;
                }
            } else {
                buf[n++] = lex->input[lex->pos];
            }
            lex->pos++;
        }
        if (lex->input[lex->pos] == '"') lex->pos++;
        buf[n] = '\0';
        lex->current.type = TOK_STRING;
        lex->current.text = strdup(buf);
        return;
    }

    /* identifiers and keywords */
    if (isalpha(ch) || ch == '_') {
        int start = lex->pos;
        while (isalnum(lex->input[lex->pos]) || lex->input[lex->pos] == '_'
               || lex->input[lex->pos] == '?') {
            lex->pos++;
        }
        int len = lex->pos - start;
        char *text = malloc(len + 1);
        strncpy(text, lex->input + start, len); text[len] = '\0';
        lex->current.text = text;

        if      (strcmp(text, "let")    == 0) lex->current.type = TOK_LET;
        else if (strcmp(text, "letrec") == 0) lex->current.type = TOK_LETREC;
        else if (strcmp(text, "fn")     == 0) lex->current.type = TOK_FN;
        else if (strcmp(text, "null")   == 0) lex->current.type = TOK_NULL;
        else if (strcmp(text, "true")   == 0) lex->current.type = TOK_TRUE;
        else if (strcmp(text, "false")  == 0) lex->current.type = TOK_FALSE;
        else if (strcmp(text, "if")     == 0) lex->current.type = TOK_IF;
        else if (strcmp(text, "else")   == 0) lex->current.type = TOK_ELSE;
        else if (strcmp(text, "and")    == 0) lex->current.type = TOK_AND;
        else if (strcmp(text, "or")     == 0) lex->current.type = TOK_OR;
        else if (strcmp(text, "not")    == 0) lex->current.type = TOK_NOT;
        else                                  lex->current.type = TOK_ID;
        return;
    }

    /* multi-char operators */
#define TWO(a,b,tok,txt) \
    if (ch == a && lex->input[lex->pos+1] == b) { lex->pos += 2; set_tok(lex, tok, txt); return; }
    TWO('=','=', TOK_EQEQ, "==")
    TWO('!','=', TOK_NEQ,  "!=")
    TWO('<','=', TOK_LTE,  "<=")
    TWO('>','=', TOK_GTE,  ">=")
    TWO('.','.',TOK_DOTDOT,"..")
    TWO('+','+', TOK_PLUS, "++")   /* string/list concat */
#undef TWO

    /* single char */
    lex->pos++;
    char tmp[2] = {ch, '\0'};
    set_tok(lex, TOK_EOF, tmp); /* will override below */
    switch (ch) {
        case '(': lex->current.type = TOK_LPAREN;  break;
        case ')': lex->current.type = TOK_RPAREN;  break;
        case '{': lex->current.type = TOK_LBRACE;  break;
        case '}': lex->current.type = TOK_RBRACE;  break;
        case '[': lex->current.type = TOK_LBRACK;  break;
        case ']': lex->current.type = TOK_RBRACK;  break;
        case ',': lex->current.type = TOK_COMMA;   break;
        case '.': lex->current.type = TOK_DOT;     break;
        case ';': lex->current.type = TOK_SEMI;    break;
        case ':': lex->current.type = TOK_COLON;   break;
        case '+': lex->current.type = TOK_PLUS;    break;
        case '-': lex->current.type = TOK_MINUS;   break;
        case '*': lex->current.type = TOK_STAR;    break;
        case '/': lex->current.type = TOK_SLASH;   break;
        case '%': lex->current.type = TOK_PERCENT; break;
        case '=': lex->current.type = TOK_EQ;      break;
        case '<': lex->current.type = TOK_LT;      break;
        case '>': lex->current.type = TOK_GT;      break;
        case '!': lex->current.type = TOK_BANG;    break;
        default:
            fprintf(stderr, "Line %d: unknown character '%c'\n", lex->line, ch);
            exit(1);
    }
}

Lexer *make_lexer(const char *input) {
    Lexer *lex = calloc(1, sizeof(Lexer));
    lex->input = input;
    lex->line  = 1;
    next_token(lex);
    return lex;
}

int match(Lexer *lex, TokenType type) {
    return lex->current.type == type;
}

void expect(Lexer *lex, TokenType type) {
    if (!match(lex, type)) {
        fprintf(stderr, "Line %d: parse error: unexpected token '%s'\n",
                lex->current.line,
                lex->current.text ? lex->current.text : "(none)");
        exit(1);
    }
    next_token(lex);
}

char *expect_id(Lexer *lex) {
    if (!match(lex, TOK_ID)) {
        fprintf(stderr, "Line %d: expected identifier, got '%s'\n",
                lex->current.line,
                lex->current.text ? lex->current.text : "(none)");
        exit(1);
    }
    char *name = strdup(lex->current.text);
    next_token(lex);
    return name;
}
