
## Arena Allocators for Compiler Construction

As is evident from our example of a compiler implemented in the classical style,
memory management quickly becomes fragile and difficult to maintain. Repeated
patterns of ad-hoc allocation and deallocation tend to produce brittle code,
increase fragmentation, and significantly raise the risk of memory leaks,
use-after-free errors, and subtle lifetime bugs. When memory ownership is spread
across many small components, such as individual parsing stages or syntax tree
constructors, it becomes harder to reason about which part of the system is
responsible for releasing which resources, and when.

Rather than allocating and freeing memory in a scattered and opportunistic way,
for example after each separate parsing step, we can adopt a more structured and
robust strategy. One such approach is *arena allocation*. With arena allocation,
memory is obtained in larger contiguous blocks, called arenas, and individual
objects are carved out of these blocks as needed. The entire arena is then released
in one operation when it is no longer required. This shifts memory management
from fine-grained, error-prone bookkeeping to coarse-grained, predictable lifetimes.

#### Compilers

In the context of a compiler, arenas naturally align with the lifetimes of major
phases such as parsing, semantic analysis, and code generation. For instance,
all abstract syntax tree nodes created during parsing can be allocated from a
single arena that is discarded once parsing is complete. This eliminates the
need to explicitly deallocate each node, reduces fragmentation, and ensures that
memory usage follows clear and well-defined phase boundaries.

Beyond improving safety, arena allocation also simplifies reasoning about program
behaviour. Object lifetimes become implicit in the lifetime of the arena, which
makes ownership relationships easier to understand and document. The resulting
code is typically shorter, more readable, and less cluttered with defensive memory
management logic. Performance often improves as well, since arena allocation usually
involves simple pointer arithmetic rather than expensive general-purpose allocation
routines.

In summary, instead of relying on scattered allocate/deallocate patterns that are
fragile and difficult to scale, arena allocation provides a disciplined memory management
model. It reduces complexity, minimises errors, improves performance, and aligns naturally
with the phase-oriented structure of a compiler, making it a particularly suitable
choice for systems built in a classical, low-level style.


### The Memory Problem in Compilers

Compilers create thousands of short-lived objects during compilation:

```
Source Code (100 lines)
->
Tokens (300-500 objects)
->
AST Nodes (200-400 objects)
->
Symbol Table Entries (50-100 objects)
->
TAC Instructions (500-1000 objects)
->
All discarded after compilation!
```


#### The Brittle Traditional Approach

```c
// parser.c - Classic brittle construction
ASTNode *createNode(ASTNodeType type, const char *value) {
    ASTNode *node = malloc(sizeof(ASTNode));
    if (!node) {
        fprintf(stderr, "Out of memory!\n");
        exit(1);  // Catastrophic failure
    }
    
    node->value = strdup(value);  // Another allocation
    if (!node->value) {
        free(node);  // Must remember to free
        exit(1);
    }
    
    node->children = NULL;
    node->childCount = 0;
    return node;
}

// Later.. (if you remember!)
void freeNode(ASTNode *node) {
    if (!node) return;
    
    free(node->value);  // Must free in correct order
    
    for (int i = 0; i < node->childCount; i++) {
        freeNode(node->children[i]);  // Recursive - stack overflow risk
    }
    
    free(node->children);
    free(node);
}
```

#### Problems with This Brittle Approach

1. *Memory Leaks Everywhere*
   - Forget to free? Leak.
   - Error path without cleanup? Leak.
   - Early return? Leak.

2. *Fragmentation*
   - Small allocations scattered across heap
   - Poor cache locality
   - Slower access times

3. *Bookkeeping Overhead*
   - Each `malloc` has 8-16 bytes overhead
   - For a 24-byte AST node, that's 33-66% waste!

4. *Brittle Error Handling*
   ```c
   ASTNode *node = malloc(sizeof(ASTNode));
   node->value = strdup(value);   // What if malloc succeeded but strdup failed?
   node->children = malloc(...);  // Now we have 2 allocations to track
   // Error here? Must free node and node->value
   ```

5. *Complex Cleanup*
   ```c
   // At the end of compilation:
   freeNode(ast);           // Free AST
   freeSymbolTable(symtab); // Free symbols
   freeTAC(tac);            // Free TAC
   freeTokens(tokens);      // Free tokens
   // Did we free them all?
   ```



### What is an Arena Allocator?

An arena (also called region, zone, or bump allocator)
is a memory management pattern that:

1. Allocates from a large contiguous block
2. Doesn't free individual allocations
3. Frees everything at once when done

#### Core Concept

```
┌──────────────────────────────────────────────────┐
│                  Arena (64KB Block)              │
├────────┬────────┬────────┬───────────────────────┤
│ Node 1 │ Node 2 │ Node 3 │      Free Space       │
│ 24 B   │ 24 B   │ 24 B   │                       │
└────────┴────────┴────────┴───────────────────────┘
                           |
               Current pointer (bumps forward)
```

#### Basic API

```c
Arena *arena_create(size_t block_size);
void *arena_alloc(Arena *arena, size_t size);
void arena_destroy(Arena *arena);  // Frees everything!
```

That's it. No `arena_free()` for individual objects.



### Why Compilers Need Arenas

#### 1. *Uniform Lifetime*

All compiler data structures have the same lifetime:

```
Program Start
    ↓
Create tokens    ─┐
Create AST       ─┤ All live together
Create symbols   ─┤
Create TAC       ─┘
    ↓
Use for analysis
    ↓
Destroy all      ← One operation!
    ↓
Program End
```

#### 2. *Predictable Allocation Pattern*

Compilers allocate in phases:

```c
// Phase 1: Lexing
for each character {
    token = arena_alloc(arena, sizeof(Token));
}

// Phase 2: Parsing  
for each token {
    node = arena_alloc(arena, sizeof(ASTNode));
}

// Phase 3: Code generation
for each node {
    instr = arena_alloc(arena, sizeof(TACInstr));
}

// After all phases:
arena_destroy(arena);  // Done!
```

#### 3. *Elimination of Cleanup Code*

Traditional:
```c
if (error) {
    freeNode(node);
    freeSymbols(symtab);
    freeTAC(tac);
    return ERROR;
}
```

With arena:
```c
if (error) {
    return ERROR;  // Arena cleanup happens automatically
}
```

#### 4. *Speed*

```c
// malloc: ~50-100 CPU cycles
void *malloc(size_t size) {
    // Search free lists
    // Split blocks
    // Update metadata
    // ...
}

// arena_alloc: ~5-10 CPU cycles
void *arena_alloc(Arena *a, size_t size) {
    void *ptr = a->current + a->used;
    a->used += size;
    return ptr;
}
```

*Result:* 10-100x faster allocation for typical compiler workloads.



### Memory Issues in Traditional Compilers

#### Issue 1: String Duplication Hell

```c
// Traditional parsing
Token *createToken(const char *value) {
    Token *tok = malloc(sizeof(Token));
    tok->value = strdup(value);  // Allocation #1
    return tok;
}

ASTNode *createIdentifier(Token *tok) {
    ASTNode *node = malloc(sizeof(ASTNode));  // Allocation #2
    node->value = strdup(tok->value);         // Allocation #3 (duplicate!)
    return node;
}

// For identifier "count", we now have 3 copies:
// - Original in source
// - Copy in token
// - Copy in AST node
```

*Problem:* For a 1000-line program with 500 identifiers,
that's 1500+ string allocations to track and free!

#### Issue 2: Parent-Child Ownership

```c
ASTNode *parent = createNode(...);
ASTNode *child = createNode(...);
addChild(parent, child);

// Later:
freeNode(parent);  // Does this free child?

// If yes: What if child is shared?
// If no: Now we have a leak!
```

*Problem:* Unclear ownership leads to either double-frees or leaks.

#### Issue 3: Error Path Memory Leaks

```c
ASTNode *parseExpression() {
    Token *tok = nextToken();           // Alloc #1
    ASTNode *left = parseTerm();        // Alloc #2
    
    if (tok->type != PLUS) {
        error("Expected +");
        return NULL;  // Leaked tok and left!
    }
    
    ASTNode *right = parseTerm();       // Alloc #3
    ASTNode *result = createBinOp(...); // Alloc #4
    
    // What if createBinOp fails?
    // Must free left and right!
}
```

*Problem:* Every error path needs manual cleanup. Miss one = leak.

#### Issue 4: Temporary Allocations

```c
char *generateTempName() {
    static int counter = 0;
    char *name = malloc(16);
    sprintf(name, "t%d", counter++);
    return name;  // Who owns this? When to free?
}

// Usage:
char *temp = generateTempName();
addInstruction("MOV", temp, ...);
// Should I free temp now? Later? Never?
```

*Problem:* Unclear ownership of temporary strings.

#### Issue 5: Fragment Fragmentation

```c
// Allocating thousands of small objects
for (int i = 0; i < 10000; i++) {
    nodes[i] = malloc(24);  // Small allocations
}

// Result:
┌──┬──┬─┬──┬─┬──┬──┬─┬──┬─┬──┐  - Fragmented heap
│24│24│ │24│ │24│24│ │24│ │24│  - Poor cache locality
└──┴──┴─┴──┴─┴──┴──┴─┴──┴─┴──┘  - Wasted space
```

*Problem:* Poor performance, cache misses, memory waste.



### String Handling in Parsing

Strings are particularly problematic in compilers because:
1. *Frequent duplication* - Same identifier appears many times
2. *Varied lifetimes* - Some needed until end, some temporary
3. *Ownership unclear* - Who's responsible for freeing?

#### The Traditional String Problem

```c
// Source: "var count, total;"

// Lexer creates tokens:
Token t1 = { .value = strdup("count") };     // Alloc #1
Token t2 = { .value = strdup("total") };     // Alloc #2

// Parser creates AST:
ASTNode *var1 = { .name = strdup("count") }; // Alloc #3
ASTNode *var2 = { .name = strdup("total") }; // Alloc #4

// Symbol table:
Symbol *s1 = { .name = strdup("count") };    // Alloc #5
Symbol *s2 = { .name = strdup("total") };    // Alloc #6

// TAC generation:
TAC *i1 = { .result = strdup("count") };     // Alloc #7
TAC *i2 = { .result = strdup("total") };     // Alloc #8

// For 2 identifiers: 8 allocations, 8 frees needed!
```

#### Arena Solution: String Interning

```c
// All strings allocated in arena
char *arena_strdup(Arena *arena, const char *str) {
    size_t len = strlen(str) + 1;
    char *copy = arena_alloc(arena, len);
    memcpy(copy, str, len);
    return copy;
}

// Usage in lexer:
Token createToken(Arena *arena, const char *value) {
    Token tok;
    tok.value = arena_strdup(arena, value);  // Owned by arena
    return tok;
}

// Usage in parser:
ASTNode *createIdentifier(Arena *arena, const char *name) {
    ASTNode *node = arena_alloc(arena, sizeof(ASTNode));
    node->value = arena_strdup(arena, name);  // Owned by arena
    return node;
}

// No manual freeing needed anywhere!
```

#### Advanced: String Interning with Hash Table

For even better performance, intern strings so each unique string exists only once:

```c
typedef struct StringInterner {
    Arena *arena;
    StringEntry *table[256];  // Hash table
} StringInterner;

const char *intern(StringInterner *i, const char *str) {
    unsigned hash = hash_string(str) % 256;
    
    // Check if already interned
    for (StringEntry *e = i->table[hash]; e; e = e->next) {
        if (strcmp(e->str, str) == 0) {
            return e->str;  // Return existing copy
        }
    }
    
    // Add new entry
    StringEntry *entry = arena_alloc(i->arena, sizeof(StringEntry));
    entry->str = arena_strdup(i->arena, str);
    entry->next = i->table[hash];
    i->table[hash] = entry;
    
    return entry->str;
}

// Now you can compare strings with pointer equality!
const char *s1 = intern(interner, "count");
const char *s2 = intern(interner, "count");
assert(s1 == s2);  // Same pointer!

// Fast comparison:
if (node->name == s1) { ... }  // No strcmp needed!
```

*Benefits:*
- Each unique string stored once
- Pointer equality for comparisons (O(1) instead of O(n))
- Still arena-managed (no manual freeing)



### AST Construction with Arenas

#### Traditional Brittle AST

```c
typedef struct ASTNode {
    ASTNodeType type;
    char *value;              // Owned? Shared?
    struct ASTNode *children; // Dynamic array
    int childCount;
} ASTNode;

ASTNode *createNode(ASTNodeType type, const char *value) {
    ASTNode *node = malloc(sizeof(ASTNode));   // Alloc #1
    node->value = strdup(value);               // Alloc #2
    node->children = NULL;
    node->childCount = 0;
    return node;
}

void addChild(ASTNode *parent, ASTNode *child) {
    parent->children = realloc(parent->children,   // Alloc #3+
                              (parent->childCount + 1) * sizeof(ASTNode*));
    parent->children[parent->childCount++] = child;
}

// Cleanup nightmare:
void freeNode(ASTNode *node) {
    free(node->value);                  // Free #1
    for (int i = 0; i < node->childCount; i++) {
        freeNode(node->children[i]);    // Free #2+ (recursive)
    }
    free(node->children);               // Free #N
    free(node);                         // Free #N+1
}
```

#### Arena-Based AST

```c
typedef struct ASTNode {
    ASTNodeType type;
    char *value;              // Arena-owned
    struct ASTNode *children; // Arena-owned
    int childCount;
    int childCapacity;
} ASTNode;

ASTNode *ast_create(Arena *arena, ASTNodeType type, const char *value) {
    ASTNode *node = arena_alloc(arena, sizeof(ASTNode));
    node->type = type;
    node->value = value ? arena_strdup(arena, value) : NULL;
    node->children = NULL;
    node->childCount = 0;
    node->childCapacity = 0;
    return node;
}

void ast_add_child(Arena *arena, ASTNode *parent, ASTNode *child) {
    if (parent->childCount >= parent->childCapacity) {
        int new_cap = parent->childCapacity == 0 ? 4 : parent->childCapacity * 2;
        ASTNode *new_children = arena_alloc(arena, new_cap * sizeof(ASTNode*));
        
        // Copy existing children
        if (parent->children) {
            memcpy(new_children, parent->children, 
                   parent->childCount * sizeof(ASTNode*));
        }
        
        parent->children = new_children;
        parent->childCapacity = new_cap;
    }
    
    parent->children[parent->childCount++] = child;
}

// No cleanup function needed!
// arena_destroy(arena) frees everything
```

#### Building a Parse Tree

```c
// Traditional (error-prone):
ASTNode *parseExpression() {
    ASTNode *left = parseTerm();
    if (!left) return NULL;  // No cleanup needed yet
    
    if (token == PLUS) {
        ASTNode *op = createNode(AST_ADD, "+");
        if (!op) {
            freeNode(left);   // Must remember to free
            return NULL;
        }
        
        ASTNode *right = parseTerm();
        if (!right) {
            freeNode(left);   // Must free both
            freeNode(op);
            return NULL;
        }
        
        addChild(op, left);   // Ownership transfer
        addChild(op, right);
        return op;
    }
    
    return left;
}

// With arena (clean):
ASTNode *parseExpression(Arena *arena) {
    ASTNode *left = parseTerm(arena);
    if (!left) return NULL;  // No cleanup needed
    
    if (token == PLUS) {
        ASTNode *op = ast_create(arena, AST_ADD, "+");
        ASTNode *right = parseTerm(arena);
        if (!right) return NULL;  // Still no cleanup!
        
        ast_add_child(arena, op, left);
        ast_add_child(arena, op, right);
        return op;
    }
    
    return left;
}
```

*Key Insight:* Error handling becomes trivial because the arena owns everything.



### Symbol Tables and Scopes

Symbol tables in compilers often have hierarchical scopes:

```
Global Scope
    ├── var x
    ├── var y
    └── Procedure foo
            ├── var local1
            ├── var local2
            └── Procedure nested
                    └── var inner
```

#### Traditional Approach

```c
typedef struct Symbol {
    char *name;              // Alloc #1
    SymbolKind kind;
    struct Symbol *next;     // Linked list
} Symbol;

typedef struct Scope {
    char *name;              // Alloc #2
    Symbol *symbols;         // Must free all
    struct Scope *parent;
    struct Scope *children;  // More allocations
} Scope;

Symbol *addSymbol(Scope *scope, const char *name) {
    Symbol *sym = malloc(sizeof(Symbol));      // Alloc
    sym->name = strdup(name);                  // Alloc
    sym->next = scope->symbols;
    scope->symbols = sym;
    return sym;
}

// Cleanup:
void freeScope(Scope *scope) {
    Symbol *sym = scope->symbols;
    while (sym) {
        Symbol *next = sym->next;
        free(sym->name);    // Must free each string
        free(sym);          // Must free each symbol
        sym = next;
    }
    free(scope->name);      // Free scope name
    free(scope);            // Free scope itself
}
```

#### Arena Approach

```c
typedef struct Symbol {
    char *name;              // Arena-owned
    SymbolKind kind;
    struct Symbol *next;
} Symbol;

typedef struct Scope {
    char *name;              // Arena-owned
    Symbol *symbols;
    struct Scope *parent;
} Scope;

Scope *scope_create(Arena *arena, const char *name, Scope *parent) {
    Scope *scope = arena_alloc(arena, sizeof(Scope));
    scope->name = arena_strdup(arena, name);
    scope->symbols = NULL;
    scope->parent = parent;
    return scope;
}

Symbol *scope_add_symbol(Arena *arena, Scope *scope, const char *name) {
    Symbol *sym = arena_alloc(arena, sizeof(Symbol));
    sym->name = arena_strdup(arena, name);
    sym->next = scope->symbols;
    scope->symbols = sym;
    return sym;
}

// No cleanup needed!
```

#### Nested Scopes Example

```c
void buildSymbolTable(Arena *arena, ASTNode *root) {
    Scope *global = scope_create(arena, "global", NULL);
    
    // Process global variables
    for (each var_decl in root) {
        scope_add_symbol(arena, global, var_decl->name);
    }
    
    // Process procedures
    for (each proc_decl in root) {
        Scope *proc_scope = scope_create(arena, proc_decl->name, global);
        
        // Add local variables
        for (each local_var in proc_decl) {
            scope_add_symbol(arena, proc_scope, local_var->name);
        }
        
        // Nested procedures
        for (each nested_proc in proc_decl) {
            Scope *nested = scope_create(arena, nested_proc->name, proc_scope);
            // ...
        }
    }
    
    // All scopes and symbols freed with arena_destroy(arena)
}
```



### Intermediate Representations

TAC (Three-Address Code) generation creates many small instructions:

#### Traditional TAC

```c
typedef struct TAC {
    char *op;        // strdup("ADD")
    char *arg1;      // strdup("t0")
    char *arg2;      // strdup("t1")
    char *result;    // strdup("t2")
    struct TAC *next;
} TAC;

TAC *emitTAC(const char *op, const char *arg1, 
             const char *arg2, const char *result) {
    TAC *instr = malloc(sizeof(TAC));               // Alloc #1
    instr->op = strdup(op);                         // Alloc #2
    instr->arg1 = arg1 ? strdup(arg1) : NULL;       // Alloc #3
    instr->arg2 = arg2 ? strdup(arg2) : NULL;       // Alloc #4
    instr->result = result ? strdup(result) : NULL; // Alloc #5
    return instr;
}

// For 1000 instructions: 5000+ allocations!
```

#### Arena TAC

```c
typedef struct TAC {
    char *op;        // Arena-owned
    char *arg1;
    char *arg2;
    char *result;
    struct TAC *next;
} TAC;

TAC *emitTAC(Arena *arena, const char *op, const char *arg1,
             const char *arg2, const char *result) {
    TAC *instr = arena_alloc(arena, sizeof(TAC));
    instr->op = arena_strdup(arena, op);
    instr->arg1 = arg1 ? arena_strdup(arena, arg1) : NULL;
    instr->arg2 = arg2 ? arena_strdup(arena, arg2) : NULL;
    instr->result = result ? arena_strdup(arena, result) : NULL;
    return instr;
}

// Better: Intern common strings
const char *ADD = intern(interner, "ADD");
const char *SUB = intern(interner, "SUB");

TAC *instr = arena_alloc(arena, sizeof(TAC));
instr->op = ADD;  // Shared pointer, no allocation!
```

#### Temporary Variable Generation

```c
// Traditional (leaked strings):
char *newTemp() {
    static int counter = 0;
    char *name = malloc(16);
    sprintf(name, "t%d", counter++);
    return name;  // Who frees this?
}

// Arena version:
char *newTemp(Arena *arena) {
    static int counter = 0;
    char buf[16];
    snprintf(buf, 16, "t%d", counter++);
    return arena_strdup(arena, buf);  // Arena-owned
}

// Even better with arena_sprintf:
char *newTemp(Arena *arena) {
    static int counter = 0;
    return arena_sprintf(arena, "t%d", counter++);
}
```



### Complete Implementation Pattern

#### Compiler Structure with Arena

```c
typedef struct CompilerContext {
    Arena *arena;           // The main arena
    
    TokenStream *tokens;    // All tokens here
    ASTNode *ast;           // Entire AST here
    SymbolTable *symtab;    // All symbols here
    TACGenerator *tac;      // All instructions here
    
    StringInterner *intern; // String interning
    
    ErrorList *errors;      // Even errors!
} CompilerContext;
```

#### Full Compilation Pipeline

```c
CompilerContext *compiler_create() {
    CompilerContext *ctx = malloc(sizeof(CompilerContext));
    
    // Create arena (64KB blocks is a good default)
    ctx->arena = arena_create(64 * 1024);
    
    // Initialize string interner
    ctx->intern = interner_create(ctx->arena);
    
    // Initialize components (all use arena)
    ctx->tokens = NULL;
    ctx->ast = NULL;
    ctx->symtab = symbol_table_create(ctx->arena);
    ctx->tac = tac_create(ctx->arena);
    ctx->errors = error_list_create(ctx->arena);
    
    return ctx;
}

Result compiler_compile(CompilerContext *ctx, const char *filename) {
    // Phase 1: Lexing
    ctx->tokens = lex_file(ctx->arena, filename);
    if (!ctx->tokens) {
        return ERROR("Lexing failed");
    }
    
    // Phase 2: Parsing
    ctx->ast = parse_tokens(ctx->arena, ctx->tokens);
    if (!ctx->ast) {
        return ERROR("Parsing failed");
    }
    
    // Phase 3: Semantic Analysis
    if (!analyze_semantics(ctx->arena, ctx->ast, ctx->symtab)) {
        return ERROR("Semantic analysis failed");
    }
    
    // Phase 4: Code Generation
    if (!generate_tac(ctx->arena, ctx->ast, ctx->tac)) {
        return ERROR("Code generation failed");
    }
    
    return OK;
}

void compiler_destroy(CompilerContext *ctx) {
    // This is the beautiful part:
    arena_destroy(ctx->arena);  // Frees EVERYTHING
    free(ctx);                  // Just the context itself
}
```

#### Usage Example

```c
int main(int argc, char *argv) {
    CompilerContext *ctx = compiler_create();
    
    Result result = compiler_compile(ctx, argv[1]);
    
    if (result.has_error) {
        fprintf(stderr, "Compilation failed: %s\n", result.error.message);
        compiler_destroy(ctx);
        return 1;
    }
    
    // Use the results
    tac_print(ctx->tac, stdout);
    
    // Cleanup (one line!)
    compiler_destroy(ctx);
    
    return 0;
}
```



### Common Pitfalls and Solutions

#### Pitfall 1: Mixing Arena and malloc

```c
// BAD: Mixing allocation strategies
ASTNode *node = arena_alloc(arena, sizeof(ASTNode));
node->value = strdup(value);  // malloc'd string in arena object

// Later:
arena_destroy(arena);  // Frees node but not node->value → LEAK
```

*Solution:* Use arena consistently:
```c
// GOOD: All arena
ASTNode *node = arena_alloc(arena, sizeof(ASTNode));
node->value = arena_strdup(arena, value);

// Later:
arena_destroy(arena);  // Frees everything
```

#### Pitfall 2: Returning Pointers After Arena Destroyed

```c
// BAD: Dangling pointer
char *compile_and_get_output(const char *input) {
    Arena *arena = arena_create(4096);
    // .. compilation ..
    char *output = arena_sprintf(arena, "Result: %d", value);
    arena_destroy(arena);
    return output;  // Dangling pointer!
}
```

*Solution:* Return before destroying, or use a different arena:
```c
// GOOD: Caller provides arena
char *compile_and_get_output(Arena *arena, const char *input) {
    // ... compilation ...
    return arena_sprintf(arena, "Result: %d", value);
}

// Or copy to heap if needed:
char *compile_and_get_output(const char *input) {
    Arena *arena = arena_create(4096);
    // ... compilation ...
    char *output = arena_sprintf(arena, "Result: %d", value);
    char *heap_copy = strdup(output);  // Copy before destroying
    arena_destroy(arena);
    return heap_copy;  // Caller must free
}
```

#### Pitfall 3: Growing Arrays Wastefully

```c
// BAD: Old arrays wasted in arena
void add_element(Arena *arena, Array *arr, int value) {
    if (arr->count >= arr->capacity) {
        arr->capacity *= 2;
        int *new_data = arena_alloc(arena, arr->capacity * sizeof(int));
        memcpy(new_data, arr->data, arr->count * sizeof(int));
        arr->data = new_data;  // Old array stays in arena (wasted)
    }
    arr->data[arr->count++] = value;
}
```

*Solution:* Over-allocate initially, or use linked structures:
```c
// GOOD: Pre-allocate
Array *array_create(Arena *arena, size_t initial_capacity) {
    Array *arr = arena_alloc(arena, sizeof(Array));
    arr->capacity = initial_capacity * 2;  // Extra space
    arr->data = arena_alloc(arena, arr->capacity * sizeof(int));
    arr->count = 0;
    return arr;
}

// Or use linked list (no reallocation):
typedef struct Node {
    int value;
    struct Node *next;
} Node;

void add_element(Arena *arena, Node **head, int value) {
    Node *node = arena_alloc(arena, sizeof(Node));
    node->value = value;
    node->next = *head;
    *head = node;
}
```


#### Pitfall 4: Not Aligning Allocations

```c
// BAD: Misaligned pointers (can crash on ARM/MIPS)
void *arena_alloc(Arena *arena, size_t size) {
    void *ptr = arena->memory + arena->used;
    arena->used += size;  // No alignment
    return ptr;
}
```

*Solution:* Always align to 8 bytes:
```c
// GOOD: Aligned allocations
void *arena_alloc(Arena *arena, size_t size) {
    size_t aligned = (size + 7) & ~7;  // Round up to multiple of 8
    void *ptr = arena->memory + arena->used;
    arena->used += aligned;
    return ptr;
}
```


#### Pitfall 5: Forgetting to Check for NULL

```c
// BAD: No error checking
ASTNode *node = arena_alloc(arena, sizeof(ASTNode));
node->value = ..;  // Crash if allocation failed
```

**Solution:** Always check (or use assertions in debug builds):
```c
// GOOD: Check allocations
ASTNode *node = arena_alloc(arena, sizeof(ASTNode));
if (!node) {
    return ERROR("Out of memory");
}

// Or in debug builds:
#ifdef DEBUG
    #define ARENA_ALLOC(arena, size) \
        ({ void *p = arena_alloc(arena, size); assert(p); p; })
#else
    #define ARENA_ALLOC arena_alloc
#endif
```



### Performance Characteristics

#### Speed Comparison

```
Operation          malloc/free    Arena       Speedup
─────────────────────────────────────────────────────
Single alloc       ~100 cycles    ~5 cycles   20x
1000 allocs        ~100K cycles   ~5K cycles  20x
Cleanup            ~100K cycles   ~10 cycles  10,000x
Total (typical)    ~200K cycles   ~5K cycles  40x
```

#### Memory Usage

For a typical 1000-line program:

*Traditional:*
```
AST nodes:        500 × 24 bytes = 12,000 bytes
  + malloc overhead: 500 × 16 bytes = 8,000 bytes
Symbols:          100 × 32 bytes = 3,200 bytes
  + malloc overhead: 100 × 16 bytes = 1,600 bytes
TAC instructions: 800 × 40 bytes = 32,000 bytes
  + malloc overhead: 800 × 16 bytes = 12,800 bytes
Strings (dupes):  ~200 strings × 3 copies × 12 bytes avg = 7,200 bytes
  + malloc overhead: 600 × 16 bytes = 9,600 bytes
-------------------------------------------------
Total: 86,400 bytes
Actual memory used: ~47,200 bytes
Wasted overhead: 39,200 bytes (45% waste!)
```

*Arena:*
```
Single arena:     64 KB = 65,536 bytes
Actual used:      ~47,200 bytes
Wasted:           ~18,336 bytes (28% waste)
-------------------------------------------------
Total: 65,536 bytes
Savings: 20,864 bytes (24% less memory)
```


#### Cache Performance

*Traditional (fragmented):*
```
Node A [heap addr 0x1000]
Node B [heap addr 0x5000]  <- Far apart
Node C [heap addr 0x2000]  <- Cache miss
```

*Arena (contiguous):*
```
Node A [arena addr 0x1000]
Node B [arena addr 0x1018]  <- Same cache line
Node C [arena addr 0x1030]  <- Cache hit!
```

Result: ~2-3x fewer cache misses on AST traversal.



### Memory Alignment

We have touched on memory alignment early in the book. But it can be worth
reflecting on this in relation to arena memory management. Memory alignment
refers to the way data is arranged and accessed in computer memory, ensuring
that data objects are stored at memory addresses that are *multiples* of
their *size* or a *specific boundary* (e.g., 2 bytes, 4 bytes, 8 bytes).
This is a fundamental concept in low-level programming, hardware interaction,
and memory management, as seen in allocators like the arena allocator.

#### Why Memory Alignment Matters

1. *Hardware Requirements*: Many CPU architectures (e.g., x86, ARM)
   require or prefer that certain data types be aligned to specific
   boundaries. For example:
   - A 4-byte integer should start at an address that's a multiple of 4.
   - An 8-byte double or 64-bit pointer should start at a multiple of 8.
     If data is misaligned (e.g., a 4-byte int at address 0x03 instead
     of 0x04), the CPU might:
     - Generate a hardware exception or bus error (crashing the program
       on strict architectures like older ARM or SPARC).
     - Handle it automatically but with a performance penalty (e.g., on
       x86, it might split the access into multiple slower operations).

2. *Performance Optimization*:
   - Aligned access is faster because the CPU can fetch data in a single
     cycle from cache lines or memory buses, which are typically aligned
     to powers of 2 (e.g., 64-byte cache lines on modern CPUs).
   - Misaligned access can cause cache misses, extra bus cycles, or even
     page faults, slowing down your program significantly—up to 10x or
     more in extreme cases.
   - In vectorized operations (e.g., SIMD instructions like SSE/AVX),
     alignment is often mandatory for efficiency.

3. *Portability*: Alignment rules vary by platform. Aligning conservatively
   (e.g., to 8 bytes) makes code more portable across 32-bit and
   64-bit systems.

4. *Struct Padding and Packing*: In C/C++, structs may include implicit
   padding bytes to align members. For example:
   ```c
   struct Example {
       char a;    // 1 byte
       int b;     // 4 bytes, but may start at offset 4 due to 4-byte alignment
   };
   ```
   - sizeof(Example) might be 8 bytes (not 5) due to padding after 'a'.
   - Compilers handle this automatically, but manual memory management
     (like in the included arena) must respect it.

5. *Atomic Operations and Thread Safety*: Misaligned data can break atomic
   reads/writes in multithreaded code, leading to torn reads or undefined behavior.

#### How Alignment Works in the Arena Allocator Code
In the `arena_alloc` function, you see this:
```c
size_t aligned_size = (size + 7) & ~7;
```
- This aligns the requested `size` to the next multiple of 8 bytes.
- *Breakdown*:
  - Adding 7: If `size` is already a multiple of 8, it stays the same
    after the operation. Otherwise, it "rounds up" (e.g., size=5 -> 5+7=12).
  - Bitwise AND with ~7: ~7 is binary ..11111000 (all 1s except the
    last 3 bits), which clears the lowest 3 bits, effectively
    rounding up to a multiple of 8 (2^3).
- Why 8 bytes? It's a common default for 64-bit systems (aligns pointers,
  doubles, etc.). For 32-bit, 4 bytes might suffice,
  but 8 is safer and more future-proof.
- The allocator then bumps the pointer forward by `aligned_size`,
  ensuring the next allocation starts aligned too.
- This prevents fragmentation or misalignment in the arena's contiguous blocks.

If you didn't align, allocations could start at odd offsets, causing issues
when storing aligned types (e.g., via `arena_alloc_type(arena, ASTNode)`, if
ASTNode has an int, it needs 4-byte alignment at minimum).

#### Calculating Alignment in Code
- To check alignment: `if ((uintptr_t)ptr % alignment == 0) // aligned`.
- General rounding up: `aligned_size = ((size + (alignment - 1)) / alignment) * alignment;`.
- Your bitwise method is faster for power-of-2 alignments (like 8=2^3).

#### Potential Issues and Best Practices
- *Over-Alignment*: Wastes memory (e.g., aligning small 1-byte chars to
  8 bytes), but in arenas, it's a trade-off for simplicity and speed.
- *Under-Alignment*: Crashes or slowdowns. Use `alignof(type)` in C11+
  to get a type's required alignment dynamically.
- *In Custom Allocators*: Always align to at least the maximum of
  `sizeof(void*)` or the platform's word size.
- *Debugging*: Tools like Valgrind or AddressSanitizer can detect
  misalignment issues.
- *When to Ignore*: For byte arrays or untyped data, alignment
  might not matter, but it's good hygiene.




### Concrete Example

Let's compile this PL/0 program:

```pascal
var x, sum;

procedure addToSum;
var temp;
begin
  temp := x;
  sum := sum + temp
end;

begin
  x := 5;
  sum := 0;
  while (x > 0) do
  begin
    call addToSum;
    x := x - 1
  end
end.
```

### Memory Allocations Needed

*Phase 1 - Lexing:* 45 tokens
```
Token("var")    -> 16 bytes
Token("x")      -> 16 bytes
Token(",")      -> 16 bytes
... (42 more)
---------------------------
Total: 720 bytes
```

*Phase 2 - Parsing:* 28 AST nodes
```
NODE_PROGRAM        -> 40 bytes
NODE_BLOCK          -> 40 bytes
NODE_VAR_DECL("x")  -> 40 bytes + 2 bytes (string)
NODE_VAR_DECL("sum")-> 40 bytes + 4 bytes (string)
... (24 more nodes)
--------------------------------------------------
Total: ~1,500 bytes
```

*Phase 3 - Symbols:* 6 symbols
```
Global: x           -> 32 bytes
Global: sum         -> 32 bytes
Procedure: addToSum -> 48 bytes
  Local: temp       -> 32 bytes
-------------------------------
Total: 144 bytes
```

*Phase 4 - TAC:* 23 instructions
```
LABEL main          -> 40 bytes
t0 = LOAD 5         -> 40 bytes
x = t0              -> 40 bytes
.. (20 more)
-------------------------------
Total: 920 bytes
```

#### Traditional Approach

```c
// 102 separate malloc calls
// 102 separate free calls
// Fragmented across heap
// Easy to leak if error occurs

Total operations: ~204
Total time: ~20,400 cycles
Risk of leaks: HIGH / VERY HIGH
```

#### Arena Approach

```c
Arena *arena = arena_create(4096);  // One 4KB block

// All allocations from this block
// Total used: ~3,284 bytes
// Waste: ~812 bytes (20%)

arena_destroy(arena);  // One operation frees all

Total operations: ~2
Total time: ~500 cycles  
Risk of leaks: ZERO
```

#### Implementation

```c
#include <stdio.h>
#include "arena.h"
#include "compiler.h"

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <source.pl0>\n", argv[0]);
        return 1;
    }
    
    // Create compiler context with arena
    CompilerContext *ctx = compiler_create();
    
    // Compile
    Result result = compiler_compile(ctx, argv[1]);
    
    if (result.has_error) {
        fprintf(stderr, "Error: %s\n", result.error.message);
        compiler_destroy(ctx);  // Clean exit
        return 1;
    }
    
    // Print results
    printf("-- TAC Output --\n");
    tac_print(ctx->tac, stdout);
    
    printf("\n-- Statistics --\n");
    printf("Tokens:       %zu\n", ctx->tokens->count);
    printf("AST nodes:    %d\n", ast_node_count(ctx->ast));
    printf("Symbols:      %d\n", symbol_table_size(ctx->symtab));
    printf("Instructions: %d\n", tac_instruction_count(ctx->tac));
    
    arena_stats(ctx->arena);
    
    // Cleanup (one line!)
    compiler_destroy(ctx);
    
    return 0;
}
```

*Output:*
```
-- TAC Output --
main:
  t0 = LOAD 5
  x = t0
  t1 = LOAD 0
  sum = t1
L0:
  t2 = LOAD x
  t3 = LOAD 0
  t4 = > t2 t3
  IF_NOT t4 GOTO L1
  CALL addToSum
  t5 = LOAD x
  t6 = LOAD 1
  t7 = - t5 t6
  x = t7
  GOTO L0
L1:

-- Statistics --
Tokens:       45
AST nodes:    28
Symbols:      6
Instructions: 23

Arena Statistics:
  Total allocated: 4,096 bytes
  Total used:      3,284 bytes
  Waste:           812 bytes (19.8%)
  Blocks:          1

  Compilation successful!
```



### Summary

__The Core Problem:__
Compilers create thousands of short-lived, interconnected objects
with uniform lifetime. Traditional malloc/free is:
- *Slow* (100x slower than arena)
- *Fragmented* (poor cache performance)
- *Error-prone* (easy to leak)
- *Complex* (unclear ownership)

__The Arena Solution:__
One allocator for the entire compilation:
- *Fast* (pointer bump allocation)
- *Simple* (no individual frees)
- *Safe* (impossible to leak)
- *Clean* (one-line cleanup)

__Principles:__
1. *Allocate from arena:* Everything uses `arena_alloc()`
2. *No individual frees:* Trust the arena
3. *Destroy once:* `arena_destroy()` at the end
4. *Consistent strategy:* Don't mix malloc and arena


#### When to Use Arena in Compilers

*Suitable for:*
- AST nodes
- Tokens
- Symbol table entries
- Temporary strings
- Intermediate code
- Error messages
- Any tree/graph structure

*Not suitable for:*
- Long-lived caches across compilations (temporary files might do better)
- Interactive REPL state
- Persistent data structures

