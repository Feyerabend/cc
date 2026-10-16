#include "lisp_vm.h"
#include <ctype.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Type tag for cells that sit on the free list
#define LISP_FREE 0xFF

static lisp_value_t *nil(lisp_vm_t *vm) {
    return &vm->nil;
}

lisp_value_t *lisp_nil(lisp_vm_t *vm) {
    return &vm->nil;
}

// Errors

void lisp_fail(lisp_vm_t *vm, const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(vm->error, sizeof(vm->error), fmt, ap);
    va_end(ap);

    if (vm->error_jmp == NULL) {
        // No top-level call is active, so there is nobody to report to
        fprintf(stderr, "lisp: %s\n", vm->error);
        abort();
    }
    longjmp(*vm->error_jmp, 1);
}

const char *lisp_error(lisp_vm_t *vm) {
    return vm->error;
}

// Garbage collection

static void mark(lisp_value_t *v) {
    // Loops instead of recursing on the last child, so long lists
    // and environment chains do not use up the C stack.
    while (v != NULL && !v->marked) {
        v->marked = 1;
        switch (v->type) {
            case LISP_CONS:
                mark(v->as.cons.car);
                v = v->as.cons.cdr;
                break;
            case LISP_SYMBOL:
                v = v->as.symbol.value;
                break;
            case LISP_LAMBDA:
                mark(v->as.lambda.params);
                mark(v->as.lambda.body);
                v = v->as.lambda.env;
                break;
            default:
                return;
        }
    }
}

// Values that C code holds in local variables during evaluation are not
// reachable from the VM's own roots. They are found by scanning the C stack
// conservatively: every word that points into the heap keeps that cell
// alive. Callee-saved registers are first forced onto the stack.
#if defined(__GNUC__)
__attribute__((noinline, no_sanitize_address))
#endif
static void mark_stack(lisp_vm_t *vm) {
    if (vm->stack_base == NULL) return;

    jmp_buf regs;
#if defined(__GNUC__)
    __builtin_unwind_init();
#endif
    setjmp(regs);

    volatile uintptr_t here = 0;
    uintptr_t lo = (uintptr_t) &here;
    uintptr_t hi = (uintptr_t) vm->stack_base;
    if (lo > hi) {
        uintptr_t t = lo;
        lo = hi;
        hi = t;
    }
    lo &= ~(uintptr_t) (sizeof(void *) - 1);

    uintptr_t heap_lo = (uintptr_t) &vm->heap[0];
    uintptr_t heap_hi = (uintptr_t) &vm->heap[LISP_HEAP_SIZE];

    for (uintptr_t p = lo; p < hi; p += sizeof(void *)) {
        uintptr_t word = *(volatile uintptr_t *) p;
        if (word >= heap_lo && word < heap_hi) {
            lisp_value_t *cell = &vm->heap[(word - heap_lo) / sizeof(lisp_value_t)];
            if (cell->type != LISP_FREE) {
                mark(cell);
            }
        }
    }
}

void lisp_gc(lisp_vm_t *vm) {
    for (size_t i = 0; i < LISP_HEAP_SIZE; i++) {
        vm->heap[i].marked = 0;
    }

    // Roots: all symbols (and through them every global), the callbacks,
    // and whatever is referenced from the C stack.
    for (size_t i = 0; i < vm->symbol_count; i++) {
        mark(vm->symbols[i]);
    }
    mark(vm->on_update);
    for (int i = 0; i < 4; i++) {
        mark(vm->on_button[i]);
    }
    mark_stack(vm);

    // Sweep: unmarked cells go back on the free list. Cells never move,
    // so pointers held anywhere stay valid.
    vm->free_list = NULL;
    vm->cells_used = 0;
    for (size_t i = LISP_HEAP_SIZE; i-- > 0; ) {
        lisp_value_t *v = &vm->heap[i];
        if (v->marked) {
            vm->cells_used++;
            continue;
        }
        if (v->type == LISP_STRING && v->as.string.slot >= 0) {
            vm->string_slot_used[v->as.string.slot] = false;
        } else if (v->type == LISP_SPRITE && v->as.sprite != NULL) {
            v->as.sprite->in_use = false;
        }
#ifdef LISP_GC_STRESS
        // Make use of a freed cell easy to detect in tests
        memset(v, 0xA5, sizeof(*v));
        v->marked = 0;
#endif
        v->type = LISP_FREE;
        v->as.next_free = vm->free_list;
        vm->free_list = v;
    }
    vm->gc_count++;
}

static lisp_value_t *alloc(lisp_vm_t *vm, lisp_type_t type) {
#ifdef LISP_GC_STRESS
    // Testing aid: collect before every allocation
    if (vm->stack_base != NULL) lisp_gc(vm);
#endif
    if (vm->free_list == NULL) {
        lisp_gc(vm);
        if (vm->free_list == NULL) {
            lisp_fail(vm, "Out of memory (%d cells)", LISP_HEAP_SIZE);
        }
    }
    lisp_value_t *v = vm->free_list;
    vm->free_list = v->as.next_free;
    vm->cells_used++;
    memset(v, 0, sizeof(*v));
    v->type = type;
    return v;
}

// Construction

lisp_value_t *lisp_number(lisp_vm_t *vm, int32_t n) {
    lisp_value_t *v = alloc(vm, LISP_NUMBER);
    v->as.number = n;
    return v;
}

lisp_value_t *lisp_bool(lisp_vm_t *vm, bool b) {
    return lisp_number(vm, b ? 1 : 0);
}

lisp_value_t *lisp_cons(lisp_vm_t *vm, lisp_value_t *car, lisp_value_t *cdr) {
    lisp_value_t *v = alloc(vm, LISP_CONS);
    v->as.cons.car = car;
    v->as.cons.cdr = cdr;
    return v;
}

lisp_value_t *lisp_symbol(lisp_vm_t *vm, const char *name, size_t len) {
    for (size_t i = 0; i < vm->symbol_count; i++) {
        const char *s = vm->symbols[i]->as.symbol.name;
        if (strlen(s) == len && memcmp(s, name, len) == 0) {
            return vm->symbols[i];
        }
    }

    if (vm->symbol_count >= LISP_MAX_SYMBOLS) {
        lisp_fail(vm, "Too many symbols");
    }
    if (vm->name_pool_used + len + 1 > LISP_NAME_POOL_SIZE) {
        lisp_fail(vm, "Out of space for symbol names");
    }

    lisp_value_t *v = alloc(vm, LISP_SYMBOL);
    char *copy = &vm->name_pool[vm->name_pool_used];
    memcpy(copy, name, len);
    copy[len] = '\0';
    vm->name_pool_used += len + 1;

    v->as.symbol.name = copy;
    v->as.symbol.value = NULL;
    vm->symbols[vm->symbol_count++] = v;
    return v;
}

static lisp_value_t *intern(lisp_vm_t *vm, const char *name) {
    return lisp_symbol(vm, name, strlen(name));
}

static int free_string_slot(lisp_vm_t *vm) {
    for (int i = 0; i < LISP_STRING_SLOTS; i++) {
        if (!vm->string_slot_used[i]) return i;
    }
    return -1;
}

// A string made at run time. It gets a slot that is freed by the collector.
lisp_value_t *lisp_string(lisp_vm_t *vm, const char *text) {
    if (free_string_slot(vm) < 0) {
        lisp_gc(vm);
    }
    int slot = free_string_slot(vm);
    if (slot < 0) {
        lisp_fail(vm, "Out of string slots (max %d)", LISP_STRING_SLOTS);
    }

    lisp_value_t *v = alloc(vm, LISP_STRING);
    vm->string_slot_used[slot] = true;
    snprintf(vm->string_slots[slot], LISP_STRING_SLOT_SIZE, "%s", text);
    v->as.string.text = vm->string_slots[slot];
    v->as.string.slot = (int16_t) slot;
    return v;
}

static lisp_sprite_t *free_sprite(lisp_vm_t *vm) {
    for (int i = 0; i < LISP_MAX_SPRITES; i++) {
        if (!vm->sprites[i].in_use) return &vm->sprites[i];
    }
    return NULL;
}

static lisp_sprite_t *sprite_alloc(lisp_vm_t *vm, int32_t w, int32_t h) {
    if (w < 1 || h < 1 || w > LISP_SPRITE_MAX_SIZE || h > LISP_SPRITE_MAX_SIZE) {
        lisp_fail(vm, "Sprite size must be 1..%d", LISP_SPRITE_MAX_SIZE);
    }
    if (free_sprite(vm) == NULL) {
        lisp_gc(vm);
    }
    lisp_sprite_t *s = free_sprite(vm);
    if (s == NULL) {
        lisp_fail(vm, "Too many sprites (max %d)", LISP_MAX_SPRITES);
    }

    s->in_use = true;
    s->width = (uint8_t) w;
    s->height = (uint8_t) h;
    for (int p = 0; p < w * h; p++) {
        s->data[p] = LISP_TRANSPARENT;
    }
    return s;
}

// A new sprite with all pixels transparent
lisp_value_t *lisp_make_sprite(lisp_vm_t *vm, int32_t w, int32_t h) {
    // The cell comes first, so a failed allocation cannot leave a slot
    // marked in use with no cell to free it.
    lisp_value_t *v = alloc(vm, LISP_SPRITE);
    v->as.sprite = sprite_alloc(vm, w, h);
    return v;
}

void lisp_define_builtin(lisp_vm_t *vm, const char *name, lisp_builtin_fn fn) {
    lisp_value_t *sym = intern(vm, name);
    lisp_value_t *v = alloc(vm, LISP_BUILTIN);
    v->as.builtin.name = sym->as.symbol.name;
    v->as.builtin.fn = fn;
    sym->as.symbol.value = v;
}

void lisp_define(lisp_vm_t *vm, const char *name, lisp_value_t *value) {
    intern(vm, name)->as.symbol.value = value;
}

// Access

lisp_value_t *lisp_car(lisp_vm_t *vm, lisp_value_t *v) {
    if (IS_NIL(v)) return v;
    if (!IS_CONS(v)) lisp_fail(vm, "car: not a list");
    return v->as.cons.car;
}

lisp_value_t *lisp_cdr(lisp_vm_t *vm, lisp_value_t *v) {
    if (IS_NIL(v)) return v;
    if (!IS_CONS(v)) lisp_fail(vm, "cdr: not a list");
    return v->as.cons.cdr;
}

lisp_value_t *lisp_nth(lisp_vm_t *vm, lisp_value_t *list, size_t n) {
    while (n-- > 0) {
        list = lisp_cdr(vm, list);
    }
    return lisp_car(vm, list);
}

size_t lisp_length(lisp_value_t *list) {
    size_t len = 0;
    while (IS_CONS(list)) {
        len++;
        list = list->as.cons.cdr;
    }
    return len;
}

int32_t lisp_to_int(lisp_vm_t *vm, lisp_value_t *v) {
    if (!IS_NUMBER(v)) lisp_fail(vm, "Expected a number");
    return v->as.number;
}

// nil and 0 are false, everything else is true
bool lisp_truthy(lisp_value_t *v) {
    return !(IS_NIL(v) || (IS_NUMBER(v) && v->as.number == 0));
}

// Parsing

static void skip_space(const char **src) {
    for (;;) {
        while (isspace((unsigned char) **src)) (*src)++;
        if (**src != ';') return;
        while (**src && **src != '\n') (*src)++;
    }
}

static bool is_delimiter(char c) {
    return c == '\0' || isspace((unsigned char) c) || c == '(' || c == ')' ||
           c == '\'' || c == '"' || c == ';';
}

static bool parse_number(const char *tok, size_t len, int32_t *out) {
    char buf[24];
    if (len == 0 || len >= sizeof(buf)) return false;
    memcpy(buf, tok, len);
    buf[len] = '\0';

    const char *p = buf;
    if (*p == '-' || *p == '+') p++;
    if (!isdigit((unsigned char) *p)) return false;

    int base = (p[0] == '0' && (p[1] == 'x' || p[1] == 'X')) ? 16 : 10;
    char *end;
    long n = strtol(buf, &end, base);
    if (*end != '\0') return false;
    *out = (int32_t) n;
    return true;
}

static lisp_value_t *parse_string(lisp_vm_t *vm, const char **src) {
    (*src)++;  // Opening quote
    char *start = &vm->text_pool[vm->text_pool_used];
    size_t n = 0;

    while (**src != '"') {
        char c = **src;
        if (c == '\0') lisp_fail(vm, "Missing closing \"");
        if (c == '\\') {
            (*src)++;
            c = **src;
            if (c == 'n') c = '\n';
            else if (c == 't') c = '\t';
            else if (c == '\0') lisp_fail(vm, "Missing closing \"");
        }
        if (vm->text_pool_used + n + 1 >= LISP_TEXT_POOL_SIZE) {
            lisp_fail(vm, "Out of space for string literals");
        }
        start[n++] = c;
        (*src)++;
    }
    (*src)++;  // Closing quote

    lisp_value_t *v = alloc(vm, LISP_STRING);
    start[n] = '\0';
    vm->text_pool_used += n + 1;
    v->as.string.text = start;
    v->as.string.slot = -1;
    return v;
}

// Parses one expression. Returns NULL at end of input.
static lisp_value_t *parse(lisp_vm_t *vm, const char **src) {
    skip_space(src);
    char c = **src;

    if (c == '\0') return NULL;

    if (c == ')') lisp_fail(vm, "Unexpected )");

    if (c == '(') {
        (*src)++;
        lisp_value_t *head = nil(vm);
        lisp_value_t *tail = NULL;
        for (;;) {
            skip_space(src);
            if (**src == ')') {
                (*src)++;
                return head;
            }
            if (**src == '\0') lisp_fail(vm, "Missing )");

            lisp_value_t *cell = lisp_cons(vm, parse(vm, src), nil(vm));
            if (tail == NULL) {
                head = cell;
            } else {
                tail->as.cons.cdr = cell;
            }
            tail = cell;
        }
    }

    if (c == '\'') {
        (*src)++;
        lisp_value_t *quoted = parse(vm, src);
        if (quoted == NULL) lisp_fail(vm, "Nothing after '");
        return lisp_cons(vm, vm->s_quote, lisp_cons(vm, quoted, nil(vm)));
    }

    if (c == '"') return parse_string(vm, src);

    const char *start = *src;
    while (!is_delimiter(**src)) (*src)++;
    size_t len = (size_t) (*src - start);

    int32_t n;
    if (parse_number(start, len, &n)) {
        return lisp_number(vm, n);
    }
    if (len == 3 && memcmp(start, "nil", 3) == 0) {
        return nil(vm);
    }
    return lisp_symbol(vm, start, len);
}

// Evaluation

static lisp_value_t *lookup(lisp_vm_t *vm, lisp_value_t *sym, lisp_value_t *env) {
    for (lisp_value_t *e = env; IS_CONS(e); e = e->as.cons.cdr) {
        lisp_value_t *binding = e->as.cons.car;
        if (binding->as.cons.car == sym) {
            return binding->as.cons.cdr;
        }
    }
    if (sym->as.symbol.value == NULL) {
        lisp_fail(vm, "Undefined: %s", sym->as.symbol.name);
    }
    return sym->as.symbol.value;
}

static void assign(lisp_vm_t *vm, lisp_value_t *sym, lisp_value_t *value, lisp_value_t *env) {
    for (lisp_value_t *e = env; IS_CONS(e); e = e->as.cons.cdr) {
        lisp_value_t *binding = e->as.cons.car;
        if (binding->as.cons.car == sym) {
            binding->as.cons.cdr = value;
            return;
        }
    }
    if (sym->as.symbol.value == NULL) {
        lisp_fail(vm, "set!: undefined: %s", sym->as.symbol.name);
    }
    sym->as.symbol.value = value;
}

static lisp_value_t *expect_symbol(lisp_vm_t *vm, lisp_value_t *v, const char *form) {
    if (!IS_SYMBOL(v)) lisp_fail(vm, "%s: expected a name", form);
    return v;
}

static lisp_value_t *make_lambda(lisp_vm_t *vm, lisp_value_t *params, lisp_value_t *body, lisp_value_t *env) {
    for (lisp_value_t *p = params; !IS_NIL(p); p = lisp_cdr(vm, p)) {
        expect_symbol(vm, lisp_car(vm, p), "lambda");
    }
    lisp_value_t *v = alloc(vm, LISP_LAMBDA);
    v->as.lambda.params = params;
    v->as.lambda.body = body;
    v->as.lambda.env = env;
    return v;
}

// Evaluates all expressions in body except the last, which is returned
// so the caller can evaluate it in tail position. Returns NULL for an
// empty body.
static lisp_value_t *eval_body(lisp_vm_t *vm, lisp_value_t *body, lisp_value_t *env) {
    if (IS_NIL(body)) return NULL;
    while (!IS_NIL(lisp_cdr(vm, body))) {
        lisp_eval(vm, lisp_car(vm, body), env);
        body = lisp_cdr(vm, body);
    }
    return lisp_car(vm, body);
}

static lisp_value_t *eval_list(lisp_vm_t *vm, lisp_value_t *list, lisp_value_t *env) {
    lisp_value_t *head = nil(vm);
    lisp_value_t *tail = NULL;
    for (; !IS_NIL(list); list = lisp_cdr(vm, list)) {
        lisp_value_t *cell = lisp_cons(vm, lisp_eval(vm, lisp_car(vm, list), env), nil(vm));
        if (tail == NULL) {
            head = cell;
        } else {
            tail->as.cons.cdr = cell;
        }
        tail = cell;
    }
    return head;
}

static lisp_value_t *bind_params(lisp_vm_t *vm, lisp_value_t *fn, lisp_value_t *args) {
    lisp_value_t *env = fn->as.lambda.env;
    lisp_value_t *params = fn->as.lambda.params;
    size_t expected = lisp_length(params);
    size_t given = lisp_length(args);

    if (expected != given) {
        lisp_fail(vm, "Wrong number of arguments: expected %u, got %u",
                  (unsigned) expected, (unsigned) given);
    }
    while (!IS_NIL(params)) {
        env = lisp_cons(vm, lisp_cons(vm, params->as.cons.car, args->as.cons.car), env);
        params = params->as.cons.cdr;
        args = args->as.cons.cdr;
    }
    return env;
}

// Expressions in tail position (the branches of if, the last expression
// of a body, and so on) are evaluated by looping instead of recursing.
// A game can therefore loop by recursion without using up the C stack.
lisp_value_t *lisp_eval(lisp_vm_t *vm, lisp_value_t *expr, lisp_value_t *env) {
    if (++vm->depth > LISP_MAX_DEPTH) {
        lisp_fail(vm, "Nested too deeply (max %d)", LISP_MAX_DEPTH);
    }

    lisp_value_t *result;
    for (;;) {
        if (IS_SYMBOL(expr)) {
            result = lookup(vm, expr, env);
            break;
        }
        if (!IS_CONS(expr)) {
            result = expr;  // Numbers, strings, nil and so on evaluate to themselves
            break;
        }

        lisp_value_t *op = expr->as.cons.car;
        lisp_value_t *args = expr->as.cons.cdr;

        if (op == vm->s_quote) {
            result = lisp_car(vm, args);
            break;
        }

        if (op == vm->s_if) {
            if (lisp_truthy(lisp_eval(vm, lisp_nth(vm, args, 0), env))) {
                expr = lisp_nth(vm, args, 1);
            } else {
                expr = lisp_nth(vm, args, 2);  // nil when there is no else branch
            }
            continue;
        }

        if (op == vm->s_cond) {
            // (cond (test expr ...) ... (else expr ...))
            lisp_value_t *next = NULL;
            result = nil(vm);
            for (lisp_value_t *c = args; !IS_NIL(c); c = lisp_cdr(vm, c)) {
                lisp_value_t *clause = lisp_car(vm, c);
                lisp_value_t *test = lisp_car(vm, clause);
                lisp_value_t *value = (test == vm->s_else) ? test : lisp_eval(vm, test, env);
                if (lisp_truthy(value)) {
                    next = eval_body(vm, lisp_cdr(vm, clause), env);
                    if (next == NULL) result = value;
                    break;
                }
            }
            if (next == NULL) break;
            expr = next;
            continue;
        }

        if (op == vm->s_when) {
            // (when test expr ...)
            result = nil(vm);
            if (!lisp_truthy(lisp_eval(vm, lisp_car(vm, args), env))) break;
            expr = eval_body(vm, lisp_cdr(vm, args), env);
            if (expr == NULL) break;
            continue;
        }

        if (op == vm->s_and || op == vm->s_or) {
            // Returns the value that decided the result
            bool is_and = (op == vm->s_and);
            bool decided = false;
            result = lisp_bool(vm, is_and);
            if (IS_NIL(args)) break;
            while (!IS_NIL(lisp_cdr(vm, args))) {
                lisp_value_t *value = lisp_eval(vm, lisp_car(vm, args), env);
                if (lisp_truthy(value) != is_and) {
                    result = value;
                    decided = true;
                    break;
                }
                args = lisp_cdr(vm, args);
            }
            if (decided) break;
            expr = lisp_car(vm, args);
            continue;
        }

        if (op == vm->s_begin) {
            expr = eval_body(vm, args, env);
            if (expr == NULL) {
                result = nil(vm);
                break;
            }
            continue;
        }

        if (op == vm->s_let) {
            // (let ((name value) ...) expr ...)
            lisp_value_t *local = env;
            for (lisp_value_t *b = lisp_car(vm, args); !IS_NIL(b); b = lisp_cdr(vm, b)) {
                lisp_value_t *binding = lisp_car(vm, b);
                lisp_value_t *name = expect_symbol(vm, lisp_car(vm, binding), "let");
                lisp_value_t *value = lisp_eval(vm, lisp_nth(vm, binding, 1), env);
                local = lisp_cons(vm, lisp_cons(vm, name, value), local);
            }
            env = local;
            expr = eval_body(vm, lisp_cdr(vm, args), env);
            if (expr == NULL) {
                result = nil(vm);
                break;
            }
            continue;
        }

        if (op == vm->s_define) {
            // (define name value) or (define (name param ...) expr ...)
            // Definitions are always global.
            lisp_value_t *target = lisp_car(vm, args);
            lisp_value_t *name;
            lisp_value_t *value;
            if (IS_CONS(target)) {
                name = expect_symbol(vm, lisp_car(vm, target), "define");
                value = make_lambda(vm, lisp_cdr(vm, target), lisp_cdr(vm, args), env);
            } else {
                name = expect_symbol(vm, target, "define");
                value = lisp_eval(vm, lisp_nth(vm, args, 1), env);
            }
            name->as.symbol.value = value;
            result = name;
            break;
        }

        if (op == vm->s_set) {
            lisp_value_t *name = expect_symbol(vm, lisp_car(vm, args), "set!");
            result = lisp_eval(vm, lisp_nth(vm, args, 1), env);
            assign(vm, name, result, env);
            break;
        }

        if (op == vm->s_lambda) {
            result = make_lambda(vm, lisp_car(vm, args), lisp_cdr(vm, args), env);
            break;
        }

        if (op == vm->s_while) {
            // (while test expr ...)
            lisp_value_t *test = lisp_car(vm, args);
            while (lisp_truthy(lisp_eval(vm, test, env))) {
                for (lisp_value_t *b = lisp_cdr(vm, args); !IS_NIL(b); b = lisp_cdr(vm, b)) {
                    lisp_eval(vm, lisp_car(vm, b), env);
                }
            }
            result = nil(vm);
            break;
        }

        // Function call
        lisp_value_t *fn = lisp_eval(vm, op, env);
        lisp_value_t *values = eval_list(vm, args, env);

        if (IS_BUILTIN(fn)) {
            result = fn->as.builtin.fn(vm, values);
            break;
        }
        if (!IS_LAMBDA(fn)) {
            if (IS_SYMBOL(op)) {
                lisp_fail(vm, "Not a function: %s", op->as.symbol.name);
            }
            lisp_fail(vm, "Not a function");
        }

        env = bind_params(vm, fn, values);
        expr = eval_body(vm, fn->as.lambda.body, env);
        if (expr == NULL) {
            result = nil(vm);
            break;
        }
    }

    vm->depth--;
    return result;
}

lisp_value_t *lisp_apply(lisp_vm_t *vm, lisp_value_t *fn, lisp_value_t *args) {
    if (IS_BUILTIN(fn)) {
        return fn->as.builtin.fn(vm, args);
    }
    if (!IS_LAMBDA(fn)) {
        lisp_fail(vm, "Not a function");
    }

    lisp_value_t *env = bind_params(vm, fn, args);
    lisp_value_t *result = nil(vm);
    for (lisp_value_t *b = fn->as.lambda.body; !IS_NIL(b); b = lisp_cdr(vm, b)) {
        result = lisp_eval(vm, lisp_car(vm, b), env);
    }
    return result;
}

// Top level

lisp_value_t *lisp_run(lisp_vm_t *vm, const char *source) {
    jmp_buf here;
    jmp_buf *outer = vm->error_jmp;
    void *outer_base = vm->stack_base;
    // Changed after setjmp, so they must be volatile to survive a longjmp
    lisp_value_t *volatile result = nil(vm);
    const char *volatile pos = source;

    vm->error_jmp = &here;
    if (outer_base == NULL) vm->stack_base = &here;
    if (setjmp(here) != 0) {
        vm->error_jmp = outer;
        vm->stack_base = outer_base;
        return NULL;
    }

    for (;;) {
        vm->depth = 0;
        const char *p = pos;
        lisp_value_t *expr = parse(vm, &p);
        pos = p;
        if (expr == NULL) break;
        result = lisp_eval(vm, expr, nil(vm));
    }

    vm->error_jmp = outer;
    vm->stack_base = outer_base;
    vm->error[0] = '\0';
    return result;
}

lisp_value_t *lisp_call(lisp_vm_t *vm, lisp_value_t *fn) {
    jmp_buf here;
    jmp_buf *outer = vm->error_jmp;
    void *outer_base = vm->stack_base;

    vm->error_jmp = &here;
    if (outer_base == NULL) vm->stack_base = &here;
    if (setjmp(here) != 0) {
        vm->error_jmp = outer;
        vm->stack_base = outer_base;
        return NULL;
    }

    vm->depth = 0;
    lisp_value_t *result = lisp_apply(vm, fn, nil(vm));

    vm->error_jmp = outer;
    vm->stack_base = outer_base;
    vm->error[0] = '\0';
    return result;
}

// Printing

void lisp_print(lisp_value_t *v) {
    switch (v->type) {
        case LISP_NIL:
            printf("()");
            break;
        case LISP_NUMBER:
            printf("%ld", (long) v->as.number);
            break;
        case LISP_SYMBOL:
            printf("%s", v->as.symbol.name);
            break;
        case LISP_STRING:
            printf("%s", v->as.string.text);
            break;
        case LISP_CONS:
            printf("(");
            for (;;) {
                lisp_print(v->as.cons.car);
                v = v->as.cons.cdr;
                if (!IS_CONS(v)) break;
                printf(" ");
            }
            if (!IS_NIL(v)) {
                printf(" . ");
                lisp_print(v);
            }
            printf(")");
            break;
        case LISP_BUILTIN:
            printf("<builtin %s>", v->as.builtin.name);
            break;
        case LISP_LAMBDA:
            printf("<lambda>");
            break;
        case LISP_SPRITE:
            printf("<sprite %dx%d>", v->as.sprite->width, v->as.sprite->height);
            break;
        default:
            printf("<?>");
            break;
    }
}

// Setup

void lisp_init(lisp_vm_t *vm) {
    memset(vm, 0, sizeof(*vm));
    vm->nil.type = LISP_NIL;

    for (size_t i = LISP_HEAP_SIZE; i-- > 0; ) {
        vm->heap[i].type = LISP_FREE;
        vm->heap[i].as.next_free = vm->free_list;
        vm->free_list = &vm->heap[i];
    }

    vm->s_quote  = intern(vm, "quote");
    vm->s_if     = intern(vm, "if");
    vm->s_cond   = intern(vm, "cond");
    vm->s_else   = intern(vm, "else");
    vm->s_when   = intern(vm, "when");
    vm->s_and    = intern(vm, "and");
    vm->s_or     = intern(vm, "or");
    vm->s_begin  = intern(vm, "begin");
    vm->s_let    = intern(vm, "let");
    vm->s_define = intern(vm, "define");
    vm->s_set    = intern(vm, "set!");
    vm->s_lambda = intern(vm, "lambda");
    vm->s_while  = intern(vm, "while");

    lisp_register_builtins(vm);
}
