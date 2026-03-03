/**
* Lexical Analyzer State Machine
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <ctype.h>

#define MAX_TOKEN_LENGTH 128

typedef enum {
    TOKEN_KEYWORD, TOKEN_IDENTIFIER, TOKEN_NUMBER,
    TOKEN_STRING, TOKEN_OPERATOR, TOKEN_DELIMITER,
    TOKEN_COMMENT, TOKEN_WHITESPACE, TOKEN_ERROR, TOKEN_EOF
} TokenType;

typedef enum {
    STATE_START, STATE_IDENTIFIER, STATE_NUMBER,
    STATE_NUMBER_DOT, STATE_NUMBER_FLOAT, STATE_STRING,
    STATE_COMMENT_LINE, STATE_COMMENT_BLOCK, STATE_OPERATOR,
    STATE_ERROR
} LexerState;

typedef struct {
    TokenType type;
    char text[MAX_TOKEN_LENGTH];
    int line;
    int column;
} Token;

typedef struct {
    const char *input;
    int position;
    int line;
    int column;
    LexerState state;
    char current;
} Lexer;

const char *keywords[] = {
    "if", "else", "while", "for", "return", "int", "float",
    "char", "void", "struct", "break", "continue", NULL
};

void initLexer(Lexer *lexer, const char *input) {
    lexer->input = input;
    lexer->position = 0;
    lexer->line = 1;
    lexer->column = 1;
    lexer->state = STATE_START;
    lexer->current = input[0];
}

void advanceChar(Lexer *lexer) {
    if (lexer->current == '\0') return;
    
    if (lexer->current == '\n') {
        lexer->line++;
        lexer->column = 1;
    } else {
        lexer->column++;
    }
    
    lexer->position++;
    lexer->current = lexer->input[lexer->position];
}

bool isKeyword(const char *text) {
    for (int i = 0; keywords[i] != NULL; i++) {
        if (strcmp(text, keywords[i]) == 0) return true;
    }
    return false;
}

const char* tokenTypeToString(TokenType type) {
    switch (type) {
        case TOKEN_KEYWORD: return "KEYWORD";
        case TOKEN_IDENTIFIER: return "IDENTIFIER";
        case TOKEN_NUMBER: return "NUMBER";
        case TOKEN_STRING: return "STRING";
        case TOKEN_OPERATOR: return "OPERATOR";
        case TOKEN_DELIMITER: return "DELIMITER";
        case TOKEN_COMMENT: return "COMMENT";
        case TOKEN_WHITESPACE: return "WHITESPACE";
        case TOKEN_ERROR: return "ERROR";
        case TOKEN_EOF: return "EOF";
        default: return "UNKNOWN";
    }
}

Token getNextToken(Lexer *lexer) {
    Token token = {TOKEN_ERROR, "", lexer->line, lexer->column};
    int length = 0;
    bool tokenComplete = false;

    while (!tokenComplete && lexer->current != '\0') {
        if (length >= MAX_TOKEN_LENGTH - 1) {
            strcpy(token.text, "TOO_LONG");
            token.type = TOKEN_ERROR;
            return token;
        }

        switch (lexer->state) {
            case STATE_START:
                if (isspace(lexer->current)) {
                    token.type = TOKEN_WHITESPACE;
                    token.text[length++] = lexer->current;
                    advanceChar(lexer);
                    tokenComplete = true;
                }
                else if (isalpha(lexer->current) || lexer->current == '_') {
                    lexer->state = STATE_IDENTIFIER;
                    token.text[length++] = lexer->current;
                    advanceChar(lexer);
                }
                else if (isdigit(lexer->current)) {
                    lexer->state = STATE_NUMBER;
                    token.text[length++] = lexer->current;
                    advanceChar(lexer);
                }
                else if (lexer->current == '"') {
                    lexer->state = STATE_STRING;
                    token.text[length++] = lexer->current;
                    advanceChar(lexer);
                }
                else if (lexer->current == '/' && lexer->input[lexer->position+1] == '/') {
                    lexer->state = STATE_COMMENT_LINE;
                    token.text[length++] = lexer->current;
                    advanceChar(lexer);
                    token.text[length++] = lexer->current;
                    advanceChar(lexer);
                }
                else if (lexer->current == '/' && lexer->input[lexer->position+1] == '*') {
                    lexer->state = STATE_COMMENT_BLOCK;
                    token.text[length++] = lexer->current;
                    advanceChar(lexer);
                    token.text[length++] = lexer->current;
                    advanceChar(lexer);
                }
                else if (strchr("+-*/=<>!&|%^~?:", lexer->current)) {
                    lexer->state = STATE_OPERATOR;
                    token.text[length++] = lexer->current;
                    advanceChar(lexer);
                }
                else if (strchr(".,;()[]{}", lexer->current)) {
                    token.type = TOKEN_DELIMITER;
                    token.text[length++] = lexer->current;
                    advanceChar(lexer);
                    tokenComplete = true;
                }
                else {
                    lexer->state = STATE_ERROR;
                    token.text[length++] = lexer->current;
                    advanceChar(lexer);
                }
                break;

            case STATE_IDENTIFIER:
                if (isalnum(lexer->current) || lexer->current == '_') {
                    token.text[length++] = lexer->current;
                    advanceChar(lexer);
                } else {
                    token.text[length] = '\0';
                    token.type = isKeyword(token.text) ? TOKEN_KEYWORD : TOKEN_IDENTIFIER;
                    tokenComplete = true;
                    lexer->state = STATE_START;
                }
                break;

            case STATE_NUMBER:
                if (isdigit(lexer->current)) {
                    token.text[length++] = lexer->current;
                    advanceChar(lexer);
                } else if (lexer->current == '.') {
                    token.text[length++] = lexer->current;
                    lexer->state = STATE_NUMBER_DOT;
                    advanceChar(lexer);
                } else {
                    token.text[length] = '\0';
                    token.type = TOKEN_NUMBER;
                    tokenComplete = true;
                    lexer->state = STATE_START;
                }
                break;

            case STATE_NUMBER_DOT:
                if (isdigit(lexer->current)) {
                    token.text[length++] = lexer->current;
                    lexer->state = STATE_NUMBER_FLOAT;
                    advanceChar(lexer);
                } else {
                    lexer->state = STATE_ERROR;
                }
                break;

            case STATE_NUMBER_FLOAT:
                if (isdigit(lexer->current)) {
                    token.text[length++] = lexer->current;
                    advanceChar(lexer);
                } else {
                    token.text[length] = '\0';
                    token.type = TOKEN_NUMBER;
                    tokenComplete = true;
                    lexer->state = STATE_START;
                }
                break;

            case STATE_STRING:
                if (lexer->current == '"') {
                    token.text[length++] = lexer->current;
                    token.type = TOKEN_STRING;
                    tokenComplete = true;
                    advanceChar(lexer);
                    lexer->state = STATE_START;
                } else if (lexer->current == '\0' || lexer->current == '\n') {
                    lexer->state = STATE_ERROR;
                } else {
                    token.text[length++] = lexer->current;
                    advanceChar(lexer);
                }
                break;

            case STATE_COMMENT_LINE:
                if (lexer->current == '\n' || lexer->current == '\0') {
                    token.type = TOKEN_COMMENT;
                    tokenComplete = true;
                    if (lexer->current == '\n') advanceChar(lexer);
                    lexer->state = STATE_START;
                } else {
                    token.text[length++] = lexer->current;
                    advanceChar(lexer);
                }
                break;

            case STATE_COMMENT_BLOCK:
                if (lexer->current == '*' && lexer->input[lexer->position+1] == '/') {
                    token.text[length++] = lexer->current;
                    advanceChar(lexer);
                    token.text[length++] = lexer->current;
                    token.type = TOKEN_COMMENT;
                    tokenComplete = true;
                    advanceChar(lexer);
                    lexer->state = STATE_START;
                } else if (lexer->current == '\0') {
                    lexer->state = STATE_ERROR;
                } else {
                    token.text[length++] = lexer->current;
                    advanceChar(lexer);
                }
                break;

            case STATE_OPERATOR:
                if ((length == 1) && 
                    ((token.text[0] == '+' && lexer->current == '+') ||
                     (token.text[0] == '-' && lexer->current == '-') ||
                     (token.text[0] == '=' && lexer->current == '=') ||
                     (token.text[0] == '!' && lexer->current == '=') ||
                     (token.text[0] == '<' && lexer->current == '=') ||
                     (token.text[0] == '>' && lexer->current == '=') ||
                     (token.text[0] == '&' && lexer->current == '&') ||
                     (token.text[0] == '|' && lexer->current == '|'))) {
                    token.text[length++] = lexer->current;
                    advanceChar(lexer);
                }
                token.text[length] = '\0';
                token.type = TOKEN_OPERATOR;
                tokenComplete = true;
                lexer->state = STATE_START;
                break;

            case STATE_ERROR:
                token.text[length] = '\0';
                token.type = TOKEN_ERROR;
                tokenComplete = true;
                lexer->state = STATE_START;
                break;
        }
    }

    if (lexer->current == '\0' && !tokenComplete) {
        token.type = TOKEN_EOF;
        strcpy(token.text, "EOF");
    }

    token.text[length] = '\0';
    return token;
}

int main() {
    const char *sourceCode = 
        "int main() {\n"
        "    int x = 42;\n"
        "    return x;\n"
        "}\n";
    
    Lexer lexer;
    initLexer(&lexer, sourceCode);
    
    printf("Tokens:\n");
    printf("%-15s %-25s %-10s %-10s\n", "TYPE", "TEXT", "LINE", "COLUMN");
    printf("---------------------------------------------------------------\n");
    
    Token token;
    do {
        token = getNextToken(&lexer);
        if (token.type != TOKEN_WHITESPACE) {
            printf("%-15s %-25s %-10d %-10d\n",
                tokenTypeToString(token.type),
                token.text,
                token.line,
                token.column);
        }
    } while (token.type != TOKEN_EOF);
    
    return 0;
}