#ifndef LEXER_H
#define LEXER_H

#include "tokens.h"

#define MAX_TOKENS 1000
#define MAX_SYM_LEN 128

typedef struct {
    Symbol type;
    char value[MAX_SYM_LEN];  // store the value of the token (such as identifier or number) < 128
    int line;                 // line number where the token was found
    int column;               // column number where the token was found
} Token;

Token tokens[MAX_TOKENS];

extern void resetTokens();
extern Token nextToken();

extern int readTokensFromFile(const char *tokenFilename);
extern void printTokens();
extern int saveTokensToJson(const char *filename);

#endif  // LEXER_H



