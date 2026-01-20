#ifndef AST_H
#define AST_H

// -- AST nodes --

typedef enum {
    NODE_PROGRAM,
    NODE_BLOCK,
    NODE_CONST_DECL,
    NODE_VAR_DECL,
    NODE_PROC_DECL,
    NODE_ASSIGNMENT,
    NODE_CALL,
    NODE_BEGIN,
    NODE_IF,
    NODE_WHILE,
    NODE_CONDITION,
    NODE_EXPRESSION,
    NODE_TERM,
    NODE_FACTOR,
    NODE_OPERATOR,
    NODE_IDENTIFIER,
    NODE_NUMBER
} ASTNodeType;

typedef struct ASTNode {
    ASTNodeType type;
    char *value;               // identifiers, numbers, or operators
    int symbolID;
    struct ASTNode **children; // array of child nodes
    int childCount;            // number of children
} ASTNode;

// -- text representation of nodes --

typedef struct {
    ASTNodeType type;
    const char *name;
} ASTNodeTypeMapping;

static const ASTNodeTypeMapping astNodeTypeTable[] = {
    {NODE_PROGRAM, "PROGRAM"},
    {NODE_BLOCK, "BLOCK"},
    {NODE_CONST_DECL, "CONST_DECL"},
    {NODE_VAR_DECL, "VAR_DECL"},
    {NODE_PROC_DECL, "PROC_DECL"},
    {NODE_ASSIGNMENT, "ASSIGNMENT"},
    {NODE_CALL, "CALL"},
    {NODE_BEGIN, "BEGIN"},
    {NODE_IF, "IF"},
    {NODE_WHILE, "WHILE"},
    {NODE_CONDITION, "CONDITION"},
    {NODE_EXPRESSION, "EXPRESSION"},
    {NODE_TERM, "TERM"},
    {NODE_FACTOR, "FACTOR"},
    {NODE_OPERATOR, "OPERATOR"},
    {NODE_IDENTIFIER, "IDENTIFIER"},
    {NODE_NUMBER, "NUMBER"}
};

extern const char *getASTNodeTypeName(ASTNodeType type);
extern void writeASTToJSON(ASTNode *root, const char *filename);
extern void traverseAST(ASTNode *node, int depth);
extern void freeNode(ASTNode *node);
extern ASTNode *createNode(ASTNodeType type, const char *value);
extern void addChild(ASTNode *parent, ASTNode *child);
extern void prettyPrintAST(ASTNode *node, int depth);

#endif  // AST_H
