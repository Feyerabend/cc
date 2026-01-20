#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include "ast.h"

ASTNode *createNode(ASTNodeType type, const char *value) {
    ASTNode *node = malloc(sizeof(ASTNode));
    if (!node) {
        printf("Error: Failed to allocate memory for ASTNode\n");
        exit(1);
    }
    node->type = type;
    node->value = value ? strdup(value) : strdup("noname"); // ---
    node->children = NULL;
    node->childCount = 0;
    return node;
}

void addChild(ASTNode *parent, ASTNode *child) {
    if (!parent || !child) return;
    if (parent == NULL || child == NULL) return;
    parent->children = realloc(parent->children, sizeof(ASTNode *) * (parent->childCount + 1));
    if (!parent->children) {
        printf("Error: Failed to allocate memory for children array\n");
        exit(1);
    }
    parent->children[parent->childCount++] = child;
}

void freeNode(ASTNode *node) {
    if (!node) return;
    if (node->value) {
        free(node->value);
    }
    for (int i = 0; i < node->childCount; i++) {
        freeNode(node->children[i]);
    }
    free(node->children);
    free(node);
}

void traverseAST(ASTNode *node, int depth) {
    for (int i = 0; i < depth; i++) {
        printf("  ");
    }
    printf("%s", getASTNodeTypeName(node->type));
    if (node->value) {
        if (strcmp(node->value, "noname") != 0) {
            printf(": %s", node->value);
        }
    }
    printf("\n");
    for (int i = 0; i < node->childCount; i++) {
        traverseAST(node->children[i], depth + 1);
    }
}

// export AST ..
const char *getASTNodeTypeName(ASTNodeType type) {
    size_t tableSize = sizeof(astNodeTypeTable) / sizeof(astNodeTypeTable[0]);
    for (size_t i = 0; i < tableSize; i++) {
        if (astNodeTypeTable[i].type == type) {
            return astNodeTypeTable[i].name;
        }
    }
    return "UNKNOWN";
}

void serializeAST(ASTNode *node, FILE *output) {
    fprintf(output, "{");
    fprintf(output, "\"type\": \"%s\"", getASTNodeTypeName(node->type));
    if (node->value) {
        fprintf(output, ", \"value\": \"%s\"", node->value); // value if present
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

void writeASTToJSON(ASTNode *root, const char *filename) {
    FILE *file = fopen(filename, "w");
    if (!file) {
        perror("Failed to open file");
        return;
    }
    serializeAST(root, file);
    fclose(file);
}
