#ifndef SYMBOL_TABLE_H
#define SYMBOL_TABLE_H

#include "ast.h"

#define IMMUTABLE 1 // constant
#define MUTABLE 2 // variable

typedef struct Variable {
    int id; // unique ID
    char name[16];
    int type_id; // used for mutable or immutable types
    struct Variable *next;
} Variable;

typedef struct Procedure {
    int id; // unique ID
    char name[16];
    struct Variable *local_vars; // linked list of local variables
    struct Procedure *next;
} Procedure;

extern Variable *global_vars; // linked list of global variables
extern Procedure *procedures; // linked list of (global) procedures

extern void buildSymbolTable(ASTNode *root);
extern void saveSymbolTable(const char *filename);
extern void printSymbolTable();
extern void freeSymbolTable();

#endif  // SYMBOL_TABLE_H
