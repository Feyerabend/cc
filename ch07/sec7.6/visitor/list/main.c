#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct Node Node;
typedef struct NodeVisitor NodeVisitor;

typedef enum {
    EMPTY_NODE,
    NEXT_NODE
} NodeType;

struct Node {
    NodeType type;
    void* data;
    Node* next;

    void* (*accept)(Node*, NodeVisitor*);
};

struct NodeVisitor {
    void* (*for_empty_node)(NodeVisitor*, Node*);
    void* (*for_next_node)(NodeVisitor*, Node*);
    void* context; // holding visitor-specific data
};

void* empty_node_accept(Node* node, NodeVisitor* visitor) {
    return visitor->for_empty_node(visitor, node);
}

void* next_node_accept(Node* node, NodeVisitor* visitor) {
    return visitor->for_next_node(visitor, node);
}

Node* create_empty_node() {
    Node* node = malloc(sizeof(Node));
    node->type = EMPTY_NODE;
    node->data = NULL;
    node->next = NULL;
    node->accept = empty_node_accept;
    return node;
}

Node* create_next_node(void* data, Node* next) {
    Node* node = malloc(sizeof(Node));
    node->type = NEXT_NODE;
    node->data = data;
    node->next = next;
    node->accept = next_node_accept;
    return node;
}

// remove visitor
typedef struct {
    void* o; // object to remove
} RemoveContext;

void* remove_for_empty_node(NodeVisitor* visitor, Node* node) {
    return create_empty_node();
}

void* remove_for_next_node(NodeVisitor* visitor, Node* node) {
    RemoveContext* ctx = (RemoveContext*)visitor->context;
    
    if (strcmp((char*)ctx->o, (char*)node->data) == 0) {
        void* result = node->next->accept(node->next, visitor);
        free(node);
        return result;
    } else {
        Node* next_result = node->next->accept(node->next, visitor);
        node->next = next_result;
        return node;
    }
}

NodeVisitor* create_remove_visitor(void* o) {
    NodeVisitor* visitor = malloc(sizeof(NodeVisitor));
    RemoveContext* ctx = malloc(sizeof(RemoveContext));
    ctx->o = o;
    visitor->for_empty_node = remove_for_empty_node;
    visitor->for_next_node = remove_for_next_node;
    visitor->context = ctx;
    return visitor;
}

// insert visitor
typedef struct {
    void* o; // object to insert
} InsertContext;

void* insert_for_empty_node(NodeVisitor* visitor, Node* node) {
    InsertContext* ctx = (InsertContext*)visitor->context;
    return create_next_node(ctx->o, create_empty_node());
}

void* insert_for_next_node(NodeVisitor* visitor, Node* node) {
    Node* next_result = node->next->accept(node->next, visitor);
    node->next = next_result;
    return node;
}

NodeVisitor* create_insert_visitor(void* o) {
    NodeVisitor* visitor = malloc(sizeof(NodeVisitor));
    InsertContext* ctx = malloc(sizeof(InsertContext));
    ctx->o = o;
    visitor->for_empty_node = insert_for_empty_node;
    visitor->for_next_node = insert_for_next_node;
    visitor->context = ctx;
    return visitor;
}

// replace visitor
typedef struct {
    void* r; // replacement object
    void* o; // object to replace
} ReplaceContext;

void* replace_for_empty_node(NodeVisitor* visitor, Node* node) {
    return create_empty_node();
}

void* replace_for_next_node(NodeVisitor* visitor, Node* node) {
    ReplaceContext* ctx = (ReplaceContext*)visitor->context;
    
    if (strcmp((char*)ctx->o, (char*)node->data) == 0) {
        Node* next_result = node->next->accept(node->next, visitor);
        node->data = ctx->r;
        node->next = next_result;
        return node;
    } else {
        Node* next_result = node->next->accept(node->next, visitor);
        node->next = next_result;
        return node;
    }
}

NodeVisitor* create_replace_visitor(void* r, void* o) {
    NodeVisitor* visitor = malloc(sizeof(NodeVisitor));
    ReplaceContext* ctx = malloc(sizeof(ReplaceContext));
    ctx->r = r;
    ctx->o = o;
    visitor->for_empty_node = replace_for_empty_node;
    visitor->for_next_node = replace_for_next_node;
    visitor->context = ctx;
    return visitor;
}

void* print_for_empty_node(NodeVisitor* visitor, Node* node) {
    printf("\n");
    return NULL;
}

void* print_for_next_node(NodeVisitor* visitor, Node* node) {
    printf("%s\n", (char*)node->data);
    node->next->accept(node->next, visitor);
    return node->data;
}

NodeVisitor* create_print_visitor() {
    NodeVisitor* visitor = malloc(sizeof(NodeVisitor));
    visitor->for_empty_node = print_for_empty_node;
    visitor->for_next_node = print_for_next_node;
    visitor->context = NULL;
    return visitor;
}

// free visitor to clean up memory
void* free_for_empty_node(NodeVisitor* visitor, Node* node) {
    free(node);
    return NULL;
}

void* free_for_next_node(NodeVisitor* visitor, Node* node) {
    node->next->accept(node->next, visitor);
    free(node);
    return NULL;
}

NodeVisitor* create_free_visitor() {
    NodeVisitor* visitor = malloc(sizeof(NodeVisitor));
    visitor->for_empty_node = free_for_empty_node;
    visitor->for_next_node = free_for_next_node;
    visitor->context = NULL;
    return visitor;
}

// gardener impl
typedef struct {
    Node* t;
} Gardener;

Gardener* create_gardener() {
    Gardener* g = malloc(sizeof(Gardener));
    g->t = create_empty_node();
    return g;
}

void gardener_add(Gardener* g, void* o) {
    g->t = create_next_node(o, g->t);
}

void gardener_insert(Gardener* g, void* o) {
    NodeVisitor* visitor = create_insert_visitor(o);
    g->t = g->t->accept(g->t, visitor);
    free(visitor->context);
    free(visitor);
}

void gardener_remove(Gardener* g, void* o) {
    NodeVisitor* visitor = create_remove_visitor(o);
    g->t = g->t->accept(g->t, visitor);
    free(visitor->context);
    free(visitor);
}

void gardener_replace(Gardener* g, void* o, void* p) {
    NodeVisitor* visitor = create_replace_visitor(o, p);
    g->t = g->t->accept(g->t, visitor);
    free(visitor->context);
    free(visitor);
}

void* gardener_print_all_elements(Gardener* g) {
    NodeVisitor* visitor = create_print_visitor();
    void* result = g->t->accept(g->t, visitor);
    free(visitor);
    return result;
}

void gardener_free(Gardener* g) {
    NodeVisitor* visitor = create_free_visitor();
    g->t->accept(g->t, visitor);
    free(visitor);
    free(g);
}

// string duplication helper (strdup may not be available on all systems)
char* string_dup(const char* s) {
    char* d = malloc(strlen(s) + 1);
    if (d) {
        strcpy(d, s);
    }
    return d;
}

int main() {
    Gardener* g = create_gardener();
    gardener_add(g, string_dup("1"));
    gardener_add(g, string_dup("2"));
    gardener_add(g, string_dup("3"));
    gardener_add(g, string_dup("4"));
    gardener_add(g, string_dup("5"));
    gardener_add(g, string_dup("6"));
    gardener_insert(g, string_dup("7"));
    gardener_insert(g, string_dup("8"));
    gardener_add(g, string_dup("9"));
    gardener_print_all_elements(g);
    gardener_replace(g, string_dup("0"), string_dup("1"));
    gardener_print_all_elements(g);
    gardener_replace(g, string_dup("0"), string_dup("1"));
    gardener_free(g); // free memory
    return 0;
}
