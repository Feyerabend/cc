/*
 * ps_ast.h
 *
 * Shared AST node types used by both ps_parser.c and ps_codegen.c.
 *
 * Including this header in both translation units guarantees a single,
 * consistent definition of NodeKind and Node without duplication.
 */

#ifndef PS_AST_H
#define PS_AST_H


typedef enum {
    NODE_PROGRAM,      /* root - holds all top-level tokens     */
    NODE_INTEGER,      /* signed integer literal                */
    NODE_FLOAT,        /* floating-point literal                */
    NODE_STRING,       /* ( ... ) literal, escapes decoded      */
    NODE_HEXSTRING,    /* < hex digits >                        */
    NODE_NAME,         /* /LiteralName                          */
    NODE_OPERATOR,     /* bare word / executable name           */
    NODE_PROCEDURE,    /* { ... }                               */
    NODE_ARRAY,        /* [ ... ]                               */
    NODE_COMMENT,      /* % ... <EOL>                           */
} NodeKind;


typedef struct Node Node;

struct Node {
    NodeKind  kind;
    int       source_pos;  /* byte offset of this token in the source */

    union {
        long   ival;    /* NODE_INTEGER */
        double fval;    /* NODE_FLOAT */
        char  *sval;    /* NODE_STRING, HEXSTRING, NAME, OPERATOR, COMMENT */
    };

    Node **children;
    int    child_count;
    int    child_capacity;
};


/*
 * ps_parse - parse *length* bytes of PostScript source text.
 *
 * Returns the root NODE_PROGRAM node on success, NULL on parse error.
 * All nodes are arena-allocated; call arena_free_all() to release them.
 */
Node *ps_parse(const char *text, int length);
void  arena_free_all(void);


#endif /* PS_AST_H */
