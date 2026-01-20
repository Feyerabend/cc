#ifndef LEXER_H
#define LEXER_H


extern int readTokensFromFile(const char *tokenFilename);
extern void printTokens();
extern int saveTokensToJson(const char *filename);

#endif  // LEXER_H



