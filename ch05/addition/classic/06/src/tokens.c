#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#include "tokens.h"

FILE *outputFile = NULL;
FILE *sourceFile = NULL;

char currentChar;
int currentIndex = 0;
char *sourceCode;

void nextChar() {
    currentChar = sourceCode[currentIndex++];
}

void skipWhitespace() {
    while (isspace(currentChar)) {
        if (currentChar == '\n') {
            fprintf(outputFile, "ENDOFLINE ");
        }
        nextChar();
    }
}

// string literals for identifiers or keywords
void handleIdentifier(char *buffer) {
    int i = 0;
    while (isalnum(currentChar) || currentChar == '_') {
        buffer[i++] = currentChar;
        nextChar();
    }
    buffer[i] = '\0';

    // keyword
    if (strcmp(buffer, "call") == 0) {
        fprintf(outputFile, "CALLSYM ");
    } else if (strcmp(buffer, "begin") == 0) {
        fprintf(outputFile, "BEGINSYM ");
    } else if (strcmp(buffer, "end") == 0) {
        fprintf(outputFile, "ENDSYM ");
    } else if (strcmp(buffer, "if") == 0) {
        fprintf(outputFile, "IFSYM ");
    } else if (strcmp(buffer, "while") == 0) {
        fprintf(outputFile, "WHILESYM ");
    } else if (strcmp(buffer, "then") == 0) {
        fprintf(outputFile, "THENSYM ");
    } else if (strcmp(buffer, "do") == 0) {
        fprintf(outputFile, "DOSYM ");
    } else if (strcmp(buffer, "const") == 0) {
        fprintf(outputFile, "CONSTSYM ");
    } else if (strcmp(buffer, "var") == 0) {
        fprintf(outputFile, "VARSYM ");
    } else if (strcmp(buffer, "procedure") == 0) {
        fprintf(outputFile, "PROCSYM ");
    } else {
        fprintf(outputFile, "IDENT %s ", buffer);
    }
}

// number literals
void handleNumber() {
    char buffer[32];
    int i = 0;
    while (isdigit(currentChar)) {
        buffer[i++] = currentChar;
        nextChar();
    }
    buffer[i] = '\0';
    fprintf(outputFile, "NUMBER %s ", buffer);
}

// scan and tokenise input
void tokenizer() {
    char buffer[128];
    skipWhitespace();

    while (currentChar != '\0') {
        if (isalpha(currentChar) || currentChar == '_') {
            // identifiers and keywords
            handleIdentifier(buffer);
        } else if (isdigit(currentChar)) {
            // numbers
            handleNumber();
        } else if (currentChar == '(') {
            fprintf(outputFile, "LPAREN ");
            nextChar();
        } else if (currentChar == ')') {
            fprintf(outputFile, "RPAREN ");
            nextChar();
        } else if (currentChar == '*') {
            fprintf(outputFile, "TIMES ");
            nextChar();
        } else if (currentChar == '/') {
            fprintf(outputFile, "SLASH ");
            nextChar();
        } else if (currentChar == '+') {
            fprintf(outputFile, "PLUS ");
            nextChar();
        } else if (currentChar == '-') {
            fprintf(outputFile, "MINUS ");
            nextChar();
        } else if (currentChar == '=') {
            fprintf(outputFile, "EQL ");
            nextChar();
        } else if (currentChar == '#') {
            fprintf(outputFile, "NEQ ");
            nextChar();
        } else if (currentChar == '<') {
            nextChar();
            if (currentChar == '=') {
                fprintf(outputFile, "LEQ ");
                nextChar();
            } else {
                fprintf(outputFile, "LSS ");
            }
        } else if (currentChar == '>') {
            nextChar();
            if (currentChar == '=') {
                fprintf(outputFile, "GEQ ");
                nextChar();
            } else {
                fprintf(outputFile, "GTR ");
            }
        } else if (currentChar == ':') {
            nextChar();
            if (currentChar == '=') {
                fprintf(outputFile, "BECOMES ");
                nextChar();
            } else {
                fprintf(outputFile, "ERROR ");
            }
        } else if (currentChar == ';') {
            fprintf(outputFile, "SEMICOLON ");
            nextChar();
        } else if (currentChar == ',') {
            fprintf(outputFile, "COMMA ");
            nextChar();
        } else if (currentChar == '.') {
            fprintf(outputFile, "PERIOD ");
            nextChar();
        } else {
            fprintf(outputFile, "ERROR ");
            nextChar();
        }
        skipWhitespace();
    }
    fprintf(outputFile, "ENDOFFILE\n");
}

void cleanup() {
    if (sourceFile) fclose(sourceFile);
    if (outputFile) fclose(outputFile);
    if (sourceCode) free(sourceCode);
}

// main entry point
int fromSourceToTokens(const char *sourceFilename, const char *tokenFilename) {
    sourceCode = NULL;

    // input source file
    sourceFile = fopen(sourceFilename, "r");
    if (!sourceFile) {
        printf("Error opening file %s\n", sourceFilename);
        return EXIT_FAILURE;
    }

    // read entire source code into a string
    fseek(sourceFile, 0, SEEK_END);
    long fileSize = ftell(sourceFile);
    fseek(sourceFile, 0, SEEK_SET);
    sourceCode = (char *) malloc(fileSize + 1);
    if (!sourceCode) {
        printf("Memory allocation failed\n");
        cleanup();
        return EXIT_FAILURE;
    }
    fread(sourceCode, 1, fileSize, sourceFile);
    sourceCode[fileSize] = '\0'; // null-terminate string

    // output file for tokenized results
    outputFile = fopen(tokenFilename, "w");
    if (!outputFile) {
        printf("Error opening output file %s\n", tokenFilename);
        cleanup();
        return EXIT_FAILURE;
    }

    // lexing ..
    currentIndex = 0;
    nextChar(); // first char ..
    tokenizer();

    // clean up
    cleanup();

    return 0;
}
