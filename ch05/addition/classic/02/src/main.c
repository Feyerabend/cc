#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "tokens.h"
#include "lexer.h"


void processFile(const char* sourceFilename, const char* tokenFilename, const char* annotatedTokenFilename) {
    printf("\nparsing file: %s ..\n", sourceFilename);

    printf("tokenizing input ..\n");
    int flag = fromSourceToTokens(sourceFilename, tokenFilename);
    if (flag) {
        printf("failed saving tokens to file %s.\n", tokenFilename);
    }
    printf("tokens written to %s.\n", tokenFilename);

    printf("read tokens from %s.\n", tokenFilename);
    flag = readTokensFromFile(tokenFilename);
    if (flag) {
        printf("failed reading tokens from file %s.\n", tokenFilename);
    }
    printTokens(); // DEBUG

    flag = saveTokensToJson(annotatedTokenFilename);
    if (flag) {
        printf("failed to save annotated tokens to file %s.\n", annotatedTokenFilename);
    }
    printf("annotated tokens saved to %s\n", annotatedTokenFilename);

    printf("done.\n");
}

int main(int argc, char* argv[]) {
    if (argc != 6) {
        fprintf(stderr, "Usage: %s <source-file> <token-output-file> <token-annotated-output-file> .. (%d)\n", argv[0], argc);
        return EXIT_FAILURE;
    }

    const char* sourceFile = argv[1];
    const char* tokenFile = argv[2];
    const char* annTokenFile = argv[3];

    processFile(sourceFile, tokenFile, annTokenFile);

    return EXIT_SUCCESS;
}
