#ifndef UTIL_H
#define UTIL_H

extern int isReserved(const char *word);
extern const char* symbolToString(int symbol);
extern void printsymbol(Symbol s, char *buf);

#endif  // UTIL_H
