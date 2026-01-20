
## Abstract Syntax Trees (AST)

An Abstract Syntax Tree (AST) is a hierarchical, tree-like representation
of the structure of source code. Each node in the tree represents a construct
occurring in the source code, such as an expression, statement, or variable
declaration. Unlike raw text or token streams, an AST abstracts away low-level
syntactical details and organises the code into a form that is easier for a
compiler or interpreter to analyse and process.

- Nodes: Each node in an AST represents a syntactic construct, such as a variable,
  function call, or operator (cf. the grammar).
- Edges: The edges define parent-child relationships between nodes, representing
  the nesting of constructs (e.g. a function contains a block, which contains statements).
- Attributes: Nodes may have associated attributes, such as names, types, or literal values.
- Traversal: ASTs can be traversed for tasks like semantic analysis, code generation,
  optimisation, or interpretation.

ASTs are central to compilers and interpreters because they enable structured
and systematic processing of code.


### The Code

The code 'AST.c' in the following folders defines an implementation of an AST for a
simple programming language or data model: PL/E.

__1. Creating Nodes (createNode)__

```c
ASTNode *createNode(ASTNodeType type, const char *value) {
    ASTNode *node = malloc(sizeof(ASTNode));
    if (!node) {
        printf("Error: Failed to allocate memory for ASTNode\n");
        exit(1);
    }
    node->type = type;
    node->value = value ? strdup(value) : strdup("noname");
    node->children = NULL;
    node->childCount = 0;
    return node;
}
```

Purpose: Creates and initialises an AST node.
Key Points:
- Allocates memory for the node dynamically using malloc.
- The type field specifies what kind of AST construct this node represents.
- The value field stores additional information, like a variable name or
  literal value. If no value is provided, it defaults to "noname".
- Initialises the children array to hold child nodes, but starts empty
  (NULL and childCount = 0).

__2. Adding Child Nodes (addChild)__

```c
void addChild(ASTNode *parent, ASTNode *child) {
    if (!parent || !child) return;
    parent->children = realloc(parent->children, sizeof(ASTNode *) * (parent->childCount + 1));
    if (!parent->children) {
        printf("Error: Failed to allocate memory for children array\n");
        exit(1);
    }
    parent->children[parent->childCount++] = child;
}
```

Purpose: Links a child node to a parent node in the AST.
Key Points:
- Uses realloc to dynamically expand the children array as new child nodes are added.
- Updates the childCount field to reflect the current number of children.
- Ensures safety by checking for NULL inputs.


__3. Freeing Nodes (freeNode)__

```c
void freeNode(ASTNode *node) {
    if (node->value) {
        free(node->value);
    }
    for (int i = 0; i < node->childCount; i++) {
        freeNode(node->children[i]);
    }
    free(node->children);
    free(node);
}
```

Purpose: Recursively deallocates memory used by the node and its children.
Key Points:
- Recursively frees all child nodes before freeing the current node.
- Frees dynamically allocated memory for the value and children array.


__4. Traversing the AST (traverseAST)__

```c
void traverseAST(ASTNode *node, int depth) {
    for (int i = 0; i < depth; i++) {
        printf("  ");
    }
    printf("%s", getASTNodeTypeName(node->type));
    if (node->value && strcmp(node->value, "noname") != 0) {
        printf(": %s", node->value);
    }
    printf("\n");
    for (int i = 0; i < node->childCount; i++) {
        traverseAST(node->children[i], depth + 1);
    }
}
```

Purpose: Performs a depth-first traversal of the AST, printing each node and its depth.
Key Points:
- Indents output based on the depth parameter to visually represent the tree structure.
- Prints the node's type (retrieved using getASTNodeTypeName) and its value if it exists.


__5. Exporting the AST as JSON__

Serialisation (serializeAST)

```c
void serializeAST(ASTNode *node, FILE *output) {
    fprintf(output, "{");
    fprintf(output, "\"type\": \"%s\"", getASTNodeTypeName(node->type));
    if (node->value) {
        fprintf(output, ", \"value\": \"%s\"", node->value);
    }
    if (node->childCount > 0) {
        fprintf(output, ", \"children\": [");
        for (int i = 0; i < node->childCount; i++) {
            serializeAST(node->children[i], output);
            if (i < node->childCount - 1) {
                fprintf(output, ", ");
            }
        }
        fprintf(output, "]");
    }
    fprintf(output, "}");
}
```

Purpose: Serialises the AST into a JSON-like format, making it easier to analyse or use in external tools.
Key Points:
- Encodes each node's type, value, and children into JSON.
- Recursively serialises child nodes.
- Handles arrays of children efficiently using commas to separate entries.

