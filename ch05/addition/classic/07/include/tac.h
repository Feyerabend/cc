#ifndef TAC_H
#define TAC_H

typedef struct TAC {
    char *op;
    char *arg1;
    char *arg2;
    char *result;
    struct TAC *next;
} TAC;

extern char *generateTAC(ASTNode *node, const char *proc_name);
extern void printTAC();
extern void freeTAC();

extern void exportTAC(const char *filename);
extern void printTACtoFile(const char *filename);

extern void parseTAC(const char *filename) ;

#endif  // TAC_H
