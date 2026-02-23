/*
 * ps_parser.c
 *
 * A packrat (PEG) parser for PostScript source files.
 *
 * Packrat parsing memoises every (rule, position) pair so each rule is
 * evaluated at each input position at most once, giving guaranteed O(n)
 * parse time at the cost of O(n) memory for the memo table.
 *
 * -- Grammar (PEG notation) 
 *
 *   Program    ←  WS* Token* EOF
 *   Token      ←  Comment | Procedure | Array | String | HexString
 *               |  Number  | Name     | Operator
 *
 *   Comment    ←  '%'  (¬EOL .)*  EOL?
 *   Procedure  ←  '{'  WS* Token* '}'
 *   Array      ←  '['  WS* Token* ']'
 *   String     ←  '('  BalancedString  ')'
 *   HexString  ←  '<'  [0-9A-Fa-f \t\n\r ]*  '>'   (not '<<')
 *   Number     ←  Float | Integer
 *   Float      ←  [+-]? [0-9]* '.' [0-9]*  ( [eE] [+-]? [0-9]+ )?
 *   Integer    ←  [+-]? [0-9]+             (must be followed by delimiter)
 *   Name       ←  '/'  [A-Za-z_] [A-Za-z0-9_.]*    (literal name)
 *   Operator   ←  (any non-delimiter, non-whitespace run)
 *
 * -- Architecture 
 *
 *   Memory     Arena allocator.  All AST nodes are bump-allocated; there
 *              are no individual frees.  arena_free_all() reclaims
 *              everything at once.  This also eliminates double-free bugs
 *              that arise naturally when memoised entries share Node*.
 *
 *   Memo table Open-addressed hash table, MEMO_CAPACITY slots, linear
 *              probe of depth 8.  Key = (rule_id, byte_position).
 *              Value = (end_position, Node*).  Special sentinels:
 *                MEMO_EMPTY  — slot has never been written
 *                MEMO_FAIL   — rule failed at this position
 *
 * -- Build 
 *
 *   gcc -O2 -Wall -Wextra -o ps_parser ps_parser.c
 *
 * -- Usage 
 *
 *   ./ps_parser [-q] file.ps [file2.ps ...]
 *
 *     -q  quiet mode: suppress AST output, show only pass/fail + stats
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdint.h>
#include <stdbool.h>
#include <limits.h>


/* 
 * §1  Arena allocator
 * 
 *
 * A linked list of fixed-size chunks.  Allocations are bump-pointer within
 * the current chunk; a new chunk is appended when the current one is full.
 * Freeing individual objects is not supported — call arena_free_all() to
 * release every chunk at once.
 */

#define ARENA_CHUNK_SIZE  (1 << 20)   /* 1 MiB per chunk */

typedef struct ArenaChunk {
    struct ArenaChunk *next;
    size_t             used;
    char               data[];        /* flexible array — actual storage */
} ArenaChunk;

static struct {
    ArenaChunk *head;
} g_arena;


static void * arena_alloc(size_t size) {
    /* Round up to 8-byte alignment so all allocations are naturally aligned. */
    size = (size + 7u) & ~7u;

    ArenaChunk *chunk = g_arena.head;

    if (!chunk || chunk->used + size > ARENA_CHUNK_SIZE) {
        size_t capacity = size > ARENA_CHUNK_SIZE ? size : ARENA_CHUNK_SIZE;
        chunk           = malloc(sizeof(ArenaChunk) + capacity);
        chunk->used     = 0;
        chunk->next     = g_arena.head;
        g_arena.head    = chunk;
    }

    void *ptr    = chunk->data + chunk->used;
    chunk->used += size;
    return ptr;
}


static char * arena_copy_string(const char *src, int length) {
    char *dst = arena_alloc(length + 1);
    memcpy(dst, src, length);
    dst[length] = '\0';
    return dst;
}


void arena_free_all(void) {
    ArenaChunk *chunk = g_arena.head;
    while (chunk) {
        ArenaChunk *next = chunk->next;
        free(chunk);
        chunk = next;
    }
    g_arena.head = NULL;
}


/* 
 * §2  AST node
 * 
 *
 * Every token in the PostScript source becomes one Node.  Compound tokens
 * (PROGRAM, PROCEDURE, ARRAY) own an array of child Node pointers.
 */

#include "ps_ast.h"

static const char *const NODE_KIND_LABELS[] = {
    "PROGRAM", "INTEGER", "FLOAT",   "STRING", "HEXSTRING",
    "NAME",    "OPERATOR","PROCEDURE","ARRAY",  "COMMENT",
};


static Node * node_new(NodeKind kind, int source_pos) {
    Node *node        = arena_alloc(sizeof(Node));
    memset(node, 0, sizeof(Node));
    node->kind        = kind;
    node->source_pos  = source_pos;
    return node;
}


static void node_append_child(Node *parent, Node *child) {
    if (parent->child_count == parent->child_capacity) {
        int    new_cap  = parent->child_capacity ? parent->child_capacity * 2 : 4;
        Node **new_arr  = arena_alloc(new_cap * sizeof(Node *));

        if (parent->children)
            memcpy(new_arr, parent->children, parent->child_count * sizeof(Node *));

        parent->children      = new_arr;
        parent->child_capacity = new_cap;
    }

    parent->children[parent->child_count++] = child;
}


/* 
 * §3  Memo table
 * 
 *
 * Open-addressed hash table.  Each slot stores one memoised parse result.
 * We use linear probing with a small probe depth (8) — collisions beyond
 * that silently fall through to re-parsing (correctness unaffected, just a
 * minor performance miss for very large files).
 */

typedef enum {
    RULE_TOKEN     = 0,
    RULE_COMMENT,
    RULE_PROCEDURE,
    RULE_ARRAY,
    RULE_STRING,
    RULE_HEXSTRING,
    RULE_NUMBER,
    RULE_INTEGER,
    RULE_FLOAT,
    RULE_NAME,
    RULE_OPERATOR,
    RULE__COUNT,
} RuleID;

/*
 * MEMO_CAPACITY must be a power of two.  For typical PS files (< 100 KB)
 * 1 M slots comfortably fits RULE__COUNT × source_length entries.
 */
#define MEMO_CAPACITY    (1 << 20)
#define MEMO_INDEX_MASK  (MEMO_CAPACITY - 1)
#define MEMO_PROBE_DEPTH 8

#define MEMO_SLOT_EMPTY  INT_MIN   /* slot has never been written */
#define MEMO_PARSE_FAIL  (-1)      /* rule failed at this position */

typedef struct {
    int32_t rule;      /* which grammar rule              */
    int32_t pos;       /* byte position in source         */
    int32_t end_pos;   /* result: MEMO_SLOT_EMPTY / MEMO_PARSE_FAIL / ≥0 */
    Node   *node;      /* result node (NULL on failure)   */
} MemoSlot;

static MemoSlot g_memo[MEMO_CAPACITY];


static void memo_reset(void) {
    for (int i = 0; i < MEMO_CAPACITY; i++)
        g_memo[i].end_pos = MEMO_SLOT_EMPTY;
}


static uint32_t memo_hash(int rule, int pos) {
    /*
     * Combine rule and position with two different multiplicative constants
     * to spread keys evenly across the table.
     */
    uint32_t h = (uint32_t)rule * 2654435761u ^ (uint32_t)pos * 40503u;
    return h & MEMO_INDEX_MASK;
}


/*
 * memo_lookup — look up a memoised result.
 *
 * Returns true and fills *out_end / *out_node if the key is present.
 * Returns false if the slot was never written (re-parse needed).
 */
static bool memo_lookup(RuleID rule, int pos, int *out_end, Node **out_node) {
    uint32_t base = memo_hash(rule, pos);

    for (int probe = 0; probe < MEMO_PROBE_DEPTH; probe++) {
        MemoSlot *slot = &g_memo[(base + probe) & MEMO_INDEX_MASK];

        if (slot->end_pos == MEMO_SLOT_EMPTY)
            return false;   /* empty slot — key is definitely absent */

        if (slot->rule == (int32_t)rule && slot->pos == (int32_t)pos) {
            *out_end  = slot->end_pos;
            *out_node = slot->node;
            return true;
        }
    }

    return false;   /* probe depth exhausted — treat as absent */
}


static void memo_store(RuleID rule, int pos, int end_pos, Node *node) {
    uint32_t base = memo_hash(rule, pos);

    for (int probe = 0; probe < MEMO_PROBE_DEPTH; probe++) {
        MemoSlot *slot = &g_memo[(base + probe) & MEMO_INDEX_MASK];

        bool is_empty    = (slot->end_pos == MEMO_SLOT_EMPTY);
        bool is_same_key = (slot->rule == (int32_t)rule && slot->pos == (int32_t)pos);

        if (is_empty || is_same_key) {
            slot->rule    = (int32_t)rule;
            slot->pos     = (int32_t)pos;
            slot->end_pos = end_pos;
            slot->node    = node;
            return;
        }
    }
    /* Table full at this probe chain — silently skip (harmless miss). */
}


/*  Convenience macros used inside every parse function  */

/*
 * MEMO_CHECK  — if a memoised result exists, return it immediately.
 * MEMO_RETURN — store a successful result and return the end position.
 * MEMO_FAIL   — store a failure result and return MEMO_PARSE_FAIL.
 */
#define MEMO_CHECK(rule, pos, out_node)                             \
    do {                                                            \
        int   _end;                                                 \
        Node *_node;                                                \
        if (memo_lookup((rule), (pos), &_end, &_node)) {           \
            *(out_node) = _node;                                    \
            return _end;                                            \
        }                                                           \
    } while (0)

#define MEMO_RETURN(rule, start, end, node)                         \
    do {                                                            \
        memo_store((rule), (start), (end), (node));                 \
        *(out) = (node);                                            \
        return (end);                                               \
    } while (0)

#define MEMO_FAIL(rule, start)                                      \
    do {                                                            \
        memo_store((rule), (start), MEMO_PARSE_FAIL, NULL);         \
        *out = NULL;                                                 \
        return MEMO_PARSE_FAIL;                                      \
    } while (0)


/* 
 * §4  Source helpers
 * 
 */

typedef struct {
    const char *src;
    int         len;
} Source;


/* A character is a "delimiter" if it terminates an unquoted token. */
static bool is_delimiter(char c) {
    return !c
        || isspace((unsigned char)c)
        || c == '(' || c == ')' || c == '{' || c == '}'
        || c == '[' || c == ']' || c == '<' || c == '>'
        || c == '/' || c == '%';
}


static int skip_whitespace(const Source *src, int pos) {
    while (pos < src->len && isspace((unsigned char)src->src[pos]))
        pos++;
    return pos;
}


/* 
 * §5  Forward declarations
 * 
 *
 * Every parse function has the same signature:
 *
 *   int parse_XXX(Source *src, int pos, Node **out);
 *
 * Returns the position immediately after the matched text on success,
 * or MEMO_PARSE_FAIL (-1) on failure.  *out is set to the parsed Node
 * on success, NULL on failure.
 */

static int parse_token     (Source *, int, Node **);
static int parse_comment   (Source *, int, Node **);
static int parse_procedure (Source *, int, Node **);
static int parse_array     (Source *, int, Node **);
static int parse_string    (Source *, int, Node **);
static int parse_hexstring (Source *, int, Node **);
static int parse_number    (Source *, int, Node **);
static int parse_integer   (Source *, int, Node **);
static int parse_float     (Source *, int, Node **);
static int parse_name      (Source *, int, Node **);
static int parse_operator  (Source *, int, Node **);


/* 
 * §6  Parse functions
 * 
 */

/* §6.1  Comment 
 *
 *   Comment ← '%' (¬EOL .)* EOL?
 */
static int parse_comment(Source *src, int pos, Node **out) {
    MEMO_CHECK(RULE_COMMENT, pos, out);

    if (pos >= src->len || src->src[pos] != '%')
        MEMO_FAIL(RULE_COMMENT, pos);

    int start = pos++;

    /* Consume everything up to (but not including) the line ending. */
    while (pos < src->len && src->src[pos] != '\n' && src->src[pos] != '\r')
        pos++;

    /* Consume the line ending itself (CR, LF, or CR+LF). */
    if (pos < src->len && src->src[pos] == '\r') pos++;
    if (pos < src->len && src->src[pos] == '\n') pos++;

    Node *node  = node_new(NODE_COMMENT, start);
    node->sval  = arena_copy_string(src->src + start, pos - start);

    MEMO_RETURN(RULE_COMMENT, start, pos, node);
}


/*  §6.2  Integer 
 *
 *   Integer ← [+-]? [0-9]+   (must be followed by a delimiter)
 *
 * The delimiter requirement prevents "42abc" from matching as integer "42".
 */
static int parse_integer(Source *src, int pos, Node **out) {
    MEMO_CHECK(RULE_INTEGER, pos, out);

    int start = pos;

    /* Optional sign. */
    if (pos < src->len && (src->src[pos] == '+' || src->src[pos] == '-'))
        pos++;

    /* At least one digit required. */
    if (pos >= src->len || !isdigit((unsigned char)src->src[pos]))
        MEMO_FAIL(RULE_INTEGER, start);

    while (pos < src->len && isdigit((unsigned char)src->src[pos]))
        pos++;

    /* Must be followed by a delimiter, otherwise this is part of an operator. */
    if (pos < src->len && !is_delimiter(src->src[pos]))
        MEMO_FAIL(RULE_INTEGER, start);

    char buf[32];
    int  len = (pos - start < 31) ? pos - start : 31;
    memcpy(buf, src->src + start, len);
    buf[len] = '\0';

    Node *node  = node_new(NODE_INTEGER, start);
    node->ival  = atol(buf);

    MEMO_RETURN(RULE_INTEGER, start, pos, node);
}


/*  §6.3  Float 
 *
 *   Float ← [+-]? [0-9]* '.' [0-9]*  ( [eE] [+-]? [0-9]+ )?
 *
 * Both "3." and ".5" are valid; "." alone is not.
 * Tried before Integer so that "3.14" is not partially matched as "3".
 */
static int parse_float(Source *src, int pos, Node **out) {
    MEMO_CHECK(RULE_FLOAT, pos, out);

    int start = pos;

    /* Optional sign. */
    if (pos < src->len && (src->src[pos] == '+' || src->src[pos] == '-'))
        pos++;

    /* Digits before the decimal point (may be absent: ".5"). */
    int digits_before = 0;
    while (pos < src->len && isdigit((unsigned char)src->src[pos])) {
        pos++;
        digits_before++;
    }

    /* The decimal point is mandatory. */
    if (pos >= src->len || src->src[pos] != '.')
        MEMO_FAIL(RULE_FLOAT, start);
    pos++;

    /* Digits after the decimal point (may be absent: "3."). */
    int digits_after = 0;
    while (pos < src->len && isdigit((unsigned char)src->src[pos])) {
        pos++;
        digits_after++;
    }

    /* At least one digit total required. */
    if (digits_before == 0 && digits_after == 0)
        MEMO_FAIL(RULE_FLOAT, start);

    /* Optional exponent part. */
    if (pos < src->len && (src->src[pos] == 'e' || src->src[pos] == 'E')) {
        pos++;

        if (pos < src->len && (src->src[pos] == '+' || src->src[pos] == '-'))
            pos++;

        /* Exponent must contain at least one digit. */
        if (pos >= src->len || !isdigit((unsigned char)src->src[pos]))
            MEMO_FAIL(RULE_FLOAT, start);

        while (pos < src->len && isdigit((unsigned char)src->src[pos]))
            pos++;
    }

    /* Must be followed by a delimiter. */
    if (pos < src->len && !is_delimiter(src->src[pos]))
        MEMO_FAIL(RULE_FLOAT, start);

    char buf[48];
    int  len = (pos - start < 47) ? pos - start : 47;
    memcpy(buf, src->src + start, len);
    buf[len] = '\0';

    Node *node  = node_new(NODE_FLOAT, start);
    node->fval  = atof(buf);

    MEMO_RETURN(RULE_FLOAT, start, pos, node);
}


/*  §6.4  Number 
 *
 *   Number ← Float | Integer
 *
 * Float is tried first (ordered PEG choice) so "3.14" matches as a float
 * rather than integer "3" followed by operator ".14".
 */
static int parse_number(Source *src, int pos, Node **out) {
    MEMO_CHECK(RULE_NUMBER, pos, out);

    int   end  = MEMO_PARSE_FAIL;
    Node *node = NULL;

    end = parse_float(src, pos, &node);
    if (end != MEMO_PARSE_FAIL)
        MEMO_RETURN(RULE_NUMBER, pos, end, node);

    end = parse_integer(src, pos, &node);
    if (end != MEMO_PARSE_FAIL)
        MEMO_RETURN(RULE_NUMBER, pos, end, node);

    MEMO_FAIL(RULE_NUMBER, pos);
}


/* §6.5  Name (literal name) 
 *
 *   Name ← '/' [A-Za-z_] [A-Za-z0-9_.]*
 *
 * In PostScript, a name preceded by '/' is a literal (unevaluated) name,
 * e.g. /Helvetica, /x, /myProc.
 */
static int parse_name(Source *src, int pos, Node **out) {
    MEMO_CHECK(RULE_NAME, pos, out);

    int start = pos;

    if (pos >= src->len || src->src[pos] != '/')
        MEMO_FAIL(RULE_NAME, start);
    pos++;

    /* First character of the name body: letter or underscore. */
    if (pos >= src->len
     || (!isalpha((unsigned char)src->src[pos]) && src->src[pos] != '_'))
        MEMO_FAIL(RULE_NAME, start);

    while (pos < src->len
        && (isalnum((unsigned char)src->src[pos])
            || src->src[pos] == '_'
            || src->src[pos] == '.'))
        pos++;

    Node *node  = node_new(NODE_NAME, start);
    node->sval  = arena_copy_string(src->src + start, pos - start);

    MEMO_RETURN(RULE_NAME, start, pos, node);
}


/* §6.6  Operator (executable name)
 *
 *   Operator ← (any run of non-delimiter characters)
 *
 * This is the catch-all rule.  It matches both built-in operators (add,
 * moveto, gsave …) and user-defined procedure names.
 */
static int parse_operator(Source *src, int pos, Node **out) {
    MEMO_CHECK(RULE_OPERATOR, pos, out);

    int start = pos;

    if (pos >= src->len || is_delimiter(src->src[pos]))
        MEMO_FAIL(RULE_OPERATOR, start);

    while (pos < src->len && !is_delimiter(src->src[pos]))
        pos++;

    Node *node  = node_new(NODE_OPERATOR, start);
    node->sval  = arena_copy_string(src->src + start, pos - start);

    MEMO_RETURN(RULE_OPERATOR, start, pos, node);
}


/* §6.7  String
 *
 *   String ← '(' BalancedString ')'
 *
 * Parentheses nest inside strings: (a (b) c) is valid and contains
 * "a (b) c".  Backslash escape sequences are decoded on the fly.
 * We accumulate decoded bytes into a temporary heap buffer, then copy
 * the result into the arena.
 */
static int parse_string(Source *src, int pos, Node **out) {
    MEMO_CHECK(RULE_STRING, pos, out);

    int start = pos;

    if (pos >= src->len || src->src[pos] != '(')
        MEMO_FAIL(RULE_STRING, start);
    pos++;

    /* Temporary buffer for the decoded string content. */
    int   buf_capacity = 64;
    int   buf_length   = 0;
    char *buf          = malloc(buf_capacity);

#define BUF_APPEND(ch)                                              \
    do {                                                            \
        if (buf_length == buf_capacity) {                           \
            buf_capacity *= 2;                                      \
            buf = realloc(buf, buf_capacity);                       \
        }                                                           \
        buf[buf_length++] = (char)(ch);                             \
    } while (0)

    int depth = 1;   /* tracks nesting of parentheses */

    while (pos < src->len && depth > 0) {
        char ch = src->src[pos++];

        if (ch == '\\' && pos < src->len) {
            /* Backslash escape sequence. */
            char escaped = src->src[pos++];
            switch (escaped) {
                case 'n':  BUF_APPEND('\n'); break;
                case 'r':  BUF_APPEND('\r'); break;
                case 't':  BUF_APPEND('\t'); break;
                case 'b':  BUF_APPEND('\b'); break;
                case 'f':  BUF_APPEND('\f'); break;
                case '\\': BUF_APPEND('\\'); break;
                case '(':  BUF_APPEND('(');  break;
                case ')':  BUF_APPEND(')');  break;
                default:   BUF_APPEND(escaped); break;
            }
        } else if (ch == '(') {
            depth++;
            BUF_APPEND(ch);
        } else if (ch == ')') {
            depth--;
            if (depth > 0)   /* the outermost ')' is the closing delimiter */
                BUF_APPEND(ch);
        } else {
            BUF_APPEND(ch);
        }
    }

#undef BUF_APPEND

    if (depth != 0) {
        /* Unterminated string — unbalanced parentheses. */
        free(buf);
        MEMO_FAIL(RULE_STRING, start);
    }

    Node *node  = node_new(NODE_STRING, start);
    node->sval  = arena_copy_string(buf, buf_length);
    free(buf);

    MEMO_RETURN(RULE_STRING, start, pos, node);
}


/* §6.8  Hex string 
 *
 *   HexString ← '<' [0-9A-Fa-f \t\n\r ]* '>'
 *
 * Note: '<<' is the PostScript dictionary-open operator and is not a hex
 * string.  We detect and reject that case first.
 */
static int parse_hexstring(Source *src, int pos, Node **out) {
    MEMO_CHECK(RULE_HEXSTRING, pos, out);

    int start = pos;

    if (pos >= src->len || src->src[pos] != '<')
        MEMO_FAIL(RULE_HEXSTRING, start);

    /* Reject '<<' (dictionary operator). */
    if (pos + 1 < src->len && src->src[pos + 1] == '<')
        MEMO_FAIL(RULE_HEXSTRING, start);

    pos++;   /* consume '<' */

    int raw_start = pos;

    while (pos < src->len && src->src[pos] != '>') {
        char ch = src->src[pos];

        if (!isxdigit((unsigned char)ch) && !isspace((unsigned char)ch)) {
            /* Invalid character inside hex string. */
            MEMO_FAIL(RULE_HEXSTRING, start);
        }
        pos++;
    }

    if (pos >= src->len)
        MEMO_FAIL(RULE_HEXSTRING, start);   /* missing closing '>' */

    Node *node  = node_new(NODE_HEXSTRING, start);
    node->sval  = arena_copy_string(src->src + raw_start, pos - raw_start);

    pos++;   /* consume '>' */

    MEMO_RETURN(RULE_HEXSTRING, start, pos, node);
}


/* §6.9  Procedure
 *
 *   Procedure ← '{' WS* Token* '}'
 *
 * Procedures are anonymous code objects.  They may nest arbitrarily.
 */
static int parse_procedure(Source *src, int pos, Node **out) {
    MEMO_CHECK(RULE_PROCEDURE, pos, out);

    int start = pos;

    if (pos >= src->len || src->src[pos] != '{')
        MEMO_FAIL(RULE_PROCEDURE, start);
    pos++;

    Node *node = node_new(NODE_PROCEDURE, start);

    pos = skip_whitespace(src, pos);

    while (pos < src->len && src->src[pos] != '}') {
        Node *child = NULL;
        int   end   = parse_token(src, pos, &child);

        if (end == MEMO_PARSE_FAIL)
            MEMO_FAIL(RULE_PROCEDURE, start);

        if (child)
            node_append_child(node, child);

        int next = skip_whitespace(src, end);
        pos = (next > pos) ? next : pos + 1;   /* guard against infinite loop */
    }

    if (pos >= src->len)
        MEMO_FAIL(RULE_PROCEDURE, start);   /* missing closing '}' */

    pos++;   /* consume '}' */

    MEMO_RETURN(RULE_PROCEDURE, start, pos, node);
}


/* §6.10  Array
 *
 *   Array ← '[' WS* Token* ']'
 *
 * Array literals contain arbitrary tokens (including nested arrays and
 * procedures).
 */
static int parse_array(Source *src, int pos, Node **out) {
    MEMO_CHECK(RULE_ARRAY, pos, out);

    int start = pos;

    if (pos >= src->len || src->src[pos] != '[')
        MEMO_FAIL(RULE_ARRAY, start);
    pos++;

    Node *node = node_new(NODE_ARRAY, start);

    pos = skip_whitespace(src, pos);

    while (pos < src->len && src->src[pos] != ']') {
        Node *child = NULL;
        int   end   = parse_token(src, pos, &child);

        if (end == MEMO_PARSE_FAIL)
            MEMO_FAIL(RULE_ARRAY, start);

        if (child)
            node_append_child(node, child);

        int next = skip_whitespace(src, end);
        pos = (next > pos) ? next : pos + 1;
    }

    if (pos >= src->len)
        MEMO_FAIL(RULE_ARRAY, start);   /* missing closing ']' */

    pos++;   /* consume ']' */

    MEMO_RETURN(RULE_ARRAY, start, pos, node);
}


/* §6.11  Token (dispatch)
 *
 *   Token ← Comment | Procedure | Array | String | HexString
 *           | Number  | Name     | Operator
 *
 * Ordered PEG choice: the first alternative that succeeds wins.
 * Whitespace is assumed to have been consumed by the caller.
 */
static int parse_token(Source *src, int pos, Node **out) {
    MEMO_CHECK(RULE_TOKEN, pos, out);

    if (pos >= src->len) {
        /* EOF is not an error — return success with a NULL node. */
        *out = NULL;
        memo_store(RULE_TOKEN, pos, pos, NULL);
        return pos;
    }

    Node *node = NULL;
    int   end  = MEMO_PARSE_FAIL;

    /* Try each alternative in order. */
    end = parse_comment(src, pos, &node);   if (end != MEMO_PARSE_FAIL) goto success;
    end = parse_procedure(src, pos, &node); if (end != MEMO_PARSE_FAIL) goto success;
    end = parse_array(src, pos, &node);     if (end != MEMO_PARSE_FAIL) goto success;
    end = parse_string(src, pos, &node);    if (end != MEMO_PARSE_FAIL) goto success;
    end = parse_hexstring(src, pos, &node); if (end != MEMO_PARSE_FAIL) goto success;
    end = parse_number(src, pos, &node);    if (end != MEMO_PARSE_FAIL) goto success;
    end = parse_name(src, pos, &node);      if (end != MEMO_PARSE_FAIL) goto success;
    end = parse_operator(src, pos, &node);  if (end != MEMO_PARSE_FAIL) goto success;

    MEMO_FAIL(RULE_TOKEN, pos);

success:
    MEMO_RETURN(RULE_TOKEN, pos, end, node);
}


/*
 * §7  Top-level parse entry point
 *
 */

Node * ps_parse(const char *text, int length) {
    memo_reset();

    Source  src  = { text, length };
    Node   *root = node_new(NODE_PROGRAM, 0);
    int     pos  = 0;

    while (pos < length) {
        int ws_end = skip_whitespace(&src, pos);
        if (ws_end >= length)
            break;

        Node *token = NULL;
        int   end   = parse_token(&src, ws_end, &token);

        if (end == MEMO_PARSE_FAIL) {
            fprintf(stderr,
                    "parse error at byte %d  near: \"%.40s\"\n",
                    ws_end, text + ws_end);
            return NULL;
        }

        if (token)
            node_append_child(root, token);

        /* Advance past the token; guard against infinite loop at EOF. */
        pos = (end > ws_end) ? end : ws_end + 1;
    }

    return root;
}


/*
 * §8  AST printer
 *
 */

static int count_nodes(const Node *node) {
    if (!node) return 0;

    int total = 1;
    for (int i = 0; i < node->child_count; i++)
        total += count_nodes(node->children[i]);

    return total;
}


static void print_ast(const Node *node, int depth) {
    if (!node) return;

    /* Indent by two spaces per level. */
    for (int i = 0; i < depth * 2; i++)
        putchar(' ');

    printf("(%s @%d", NODE_KIND_LABELS[node->kind], node->source_pos);

    switch (node->kind) {
        case NODE_INTEGER:
            printf("  %ld", node->ival);
            break;
        case NODE_FLOAT:
            printf("  %g", node->fval);
            break;
        case NODE_STRING:
            printf("  \"%s\"", node->sval);
            break;
        case NODE_HEXSTRING:
            printf("  <%s>", node->sval);
            break;
        case NODE_NAME:
        case NODE_OPERATOR:
        case NODE_COMMENT:
            printf("  %s", node->sval);
            break;
        default:
            break;
    }

    if (node->child_count == 0) {
        printf(")\n");
        return;
    }

    printf("\n");
    for (int i = 0; i < node->child_count; i++)
        print_ast(node->children[i], depth + 1);

    for (int i = 0; i < depth * 2; i++)
        putchar(' ');
    printf(")\n");
}


/* 
 * §9  File I/O
 * 
 */

static char * read_file(const char *path, int *out_length) {
    FILE *file = fopen(path, "rb");
    if (!file) {
        perror(path);
        return NULL;
    }

    fseek(file, 0, SEEK_END);
    long size = ftell(file);
    rewind(file);

    char *buf = malloc(size + 1);
    size      = (long)fread(buf, 1, size, file);
    buf[size] = '\0';

    fclose(file);
    *out_length = (int)size;
    return buf;
}


/* 
 * §10  main
 * 
 */

static void print_usage(const char *program_name) {
    fprintf(stderr,
        "Usage: %s [-q] <file.ps> [file2.ps ...]\n"
        "\n"
        "  Parse one or more PostScript source files and print their ASTs.\n"
        "\n"
        "  -q   Quiet mode: suppress AST output, print only pass/fail + stats.\n"
        "\n"
        "Exit status: 0 if all files parsed successfully, 1 otherwise.\n",
        program_name);
}


#ifndef PS_PARSER_LIB_MODE
int main(int argc, char **argv) {
    if (argc < 2) {
        print_usage(argv[0]);
        return 1;
    }

    bool quiet      = false;
    int  first_file = 1;

    if (strcmp(argv[1], "-q") == 0) {
        quiet      = true;
        first_file = 2;
    }

    if (first_file >= argc) {
        print_usage(argv[0]);
        return 1;
    }

    int files_total  = 0;
    int files_passed = 0;
    int exit_status  = 0;

    for (int i = first_file; i < argc; i++) {
        const char *path = argv[i];
        int         len  = 0;
        char       *src  = read_file(path, &len);

        if (!src) {
            fprintf(stderr, "FAIL  %s  (cannot open)\n", path);
            exit_status = 1;
            files_total++;
            continue;
        }

        if (!quiet)
            printf("=== %s  (%d bytes) ===\n", path, len);

        Node *ast = ps_parse(src, len);
        files_total++;

        if (!ast) {
            fprintf(stderr, "FAIL  %s\n", path);
            exit_status = 1;
        } else {
            if (!quiet) {
                print_ast(ast, 0);
                putchar('\n');
            }
            printf("PASS  top=%-3d  nodes=%-4d  %s\n",
                   ast->child_count, count_nodes(ast), path);
            files_passed++;
        }

        free(src);
        arena_free_all();
        memo_reset();
    }

    if (files_total > 1)
        printf("\n%d / %d files parsed successfully.\n", files_passed, files_total);

    return exit_status;
}
#endif /* PS_PARSER_LIB_MODE */
