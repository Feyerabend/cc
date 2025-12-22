#include "lisp_vm.h"
#include <string.h>
#include <stdio.h>
#include <ctype.h>

// ===== Helper Macros =====
#define IS_NIL(v) ((v)->type == LISP_NIL)
#define IS_NUMBER(v) ((v)->type == LISP_NUMBER)
#define IS_SYMBOL(v) ((v)->type == LISP_SYMBOL)
#define IS_CONS(v) ((v)->type == LISP_CONS)
#define IS_LAMBDA(v) ((v)->type == LISP_LAMBDA)
#define IS_SPRITE(v) ((v)->type == LISP_SPRITE)

// ===== Static Globals =====
static lisp_vm_t *g_vm = NULL;  // Current VM for callbacks

// ===== Memory Management =====

void lisp_init(lisp_vm_t *vm) {
    memset(vm, 0, sizeof(lisp_vm_t));
    g_vm = vm;
    
    // Create global environment
    vm->global_env = lisp_nil(vm);
    
    // Register built-ins
    #define REGISTER(name, fn) \
        lisp_env_define(vm, vm->global_env, \
            lisp_symbol(vm, name), \
            lisp_builtin(vm, (lisp_builtin_fn)fn))
    
    // Graphics
    REGISTER("clear", lisp_builtin_clear);
    REGISTER("fill-rect", lisp_builtin_fill_rect);
    REGISTER("draw-text", lisp_builtin_draw_text);
    REGISTER("draw-sprite", lisp_builtin_draw_sprite);
    
    // Sprites
    REGISTER("make-sprite", lisp_builtin_make_sprite);
    REGISTER("sprite-set-pixel", lisp_builtin_sprite_set_pixel);
    
    // Collision
    REGISTER("collide?", lisp_builtin_collide);
    
    // Math
    REGISTER("+", lisp_builtin_add);
    REGISTER("-", lisp_builtin_sub);
    REGISTER("*", lisp_builtin_mul);
    REGISTER("/", lisp_builtin_div);
    REGISTER("<", lisp_builtin_lt);
    REGISTER(">", lisp_builtin_gt);
    REGISTER("=", lisp_builtin_eq);
    
    // Control
    REGISTER("start", lisp_builtin_start);
    REGISTER("stop", lisp_builtin_stop);
    
    #undef REGISTER
}

void lisp_deinit(lisp_vm_t *vm) {
    // Nothing to free - all memory is stack-allocated
    g_vm = NULL;
}

lisp_value_t* lisp_alloc(lisp_vm_t *vm, lisp_type_t type) {
    if (vm->heap_used >= LISP_HEAP_SIZE) {
        lisp_gc(vm);
        if (vm->heap_used >= LISP_HEAP_SIZE) {
            vm->error_msg = "Out of memory";
            return NULL;
        }
    }
    
    lisp_value_t *val = &vm->heap[vm->heap_used++];
    memset(val, 0, sizeof(lisp_value_t));
    val->type = type;
    return val;
}

void lisp_gc(lisp_vm_t *vm) {
    // Simple mark-sweep GC
    
    // Mark phase - mark all reachable values
    for (size_t i = 0; i < vm->heap_used; i++) {
        vm->heap[i].marked = 0;
    }
    
    // Mark from roots
    void mark(lisp_value_t *v) {
        if (!v || v->marked) return;
        v->marked = 1;
        
        if (v->type == LISP_CONS) {
            mark(v->as.cons.car);
            mark(v->as.cons.cdr);
        } else if (v->type == LISP_LAMBDA) {
            mark(v->as.lambda.params);
            mark(v->as.lambda.body);
            mark(v->as.lambda.env);
        }
    }
    
    mark(vm->global_env);
    mark(vm->on_update);
    for (int i = 0; i < 4; i++) {
        mark(vm->on_button_callbacks[i]);
    }
    for (size_t i = 0; i < vm->stack_ptr; i++) {
        mark(vm->stack[i]);
    }
    
    // Sweep phase - compact heap
    size_t write = 0;
    for (size_t read = 0; read < vm->heap_used; read++) {
        if (vm->heap[read].marked) {
            if (write != read) {
                vm->heap[write] = vm->heap[read];
            }
            write++;
        }
    }
    
    printf("GC: %zu -> %zu cells\n", vm->heap_used, write);
    vm->heap_used = write;
}

// ===== Constructors =====

lisp_value_t* lisp_nil(lisp_vm_t *vm) {
    lisp_value_t *v = lisp_alloc(vm, LISP_NIL);
    return v;
}

lisp_value_t* lisp_number(lisp_vm_t *vm, int32_t n) {
    lisp_value_t *v = lisp_alloc(vm, LISP_NUMBER);
    if (v) v->as.number = n;
    return v;
}

lisp_value_t* lisp_symbol(lisp_vm_t *vm, const char *name) {
    // Intern symbol
    for (size_t i = 0; i < vm->symbol_count; i++) {
        if (strcmp(vm->symbols[i], name) == 0) {
            lisp_value_t *v = lisp_alloc(vm, LISP_SYMBOL);
            if (v) v->as.symbol_id = i;
            return v;
        }
    }
    
    if (vm->symbol_count >= LISP_SYMBOL_TABLE_SIZE) {
        vm->error_msg = "Symbol table full";
        return NULL;
    }
    
    vm->symbols[vm->symbol_count] = name;
    lisp_value_t *v = lisp_alloc(vm, LISP_SYMBOL);
    if (v) v->as.symbol_id = vm->symbol_count++;
    return v;
}

lisp_value_t* lisp_cons(lisp_vm_t *vm, lisp_value_t *car, lisp_value_t *cdr) {
    lisp_value_t *v = lisp_alloc(vm, LISP_CONS);
    if (v) {
        v->as.cons.car = car;
        v->as.cons.cdr = cdr;
    }
    return v;
}

lisp_value_t* lisp_string(lisp_vm_t *vm, const char *str) {
    lisp_value_t *v = lisp_alloc(vm, LISP_STRING);
    if (v) v->as.string = str;
    return v;
}

lisp_value_t* lisp_builtin(lisp_vm_t *vm, lisp_builtin_fn fn) {
    lisp_value_t *v = lisp_alloc(vm, LISP_BUILTIN);
    if (v) v->as.builtin = fn;
    return v;
}

// ===== List Operations =====

lisp_value_t* lisp_car(lisp_value_t *cons) {
    return IS_CONS(cons) ? cons->as.cons.car : NULL;
}

lisp_value_t* lisp_cdr(lisp_value_t *cons) {
    return IS_CONS(cons) ? cons->as.cons.cdr : NULL;
}

size_t lisp_length(lisp_value_t *list) {
    size_t len = 0;
    while (IS_CONS(list)) {
        len++;
        list = lisp_cdr(list);
    }
    return len;
}

lisp_value_t* lisp_nth(lisp_value_t *list, size_t n) {
    while (n-- > 0 && IS_CONS(list)) {
        list = lisp_cdr(list);
    }
    return IS_CONS(list) ? lisp_car(list) : NULL;
}

// ===== Parsing =====

static void skip_whitespace(const char **code) {
    while (**code && isspace(**code)) (*code)++;
    
    // Skip comments
    if (**code == ';') {
        while (**code && **code != '\n') (*code)++;
        skip_whitespace(code);
    }
}

lisp_value_t* lisp_parse(lisp_vm_t *vm, const char **code) {
    skip_whitespace(code);
    
    if (**code == '\0') return NULL;
    
    // List
    if (**code == '(') {
        (*code)++;
        skip_whitespace(code);
        
        if (**code == ')') {
            (*code)++;
            return lisp_nil(vm);
        }
        
        lisp_value_t *list = NULL;
        lisp_value_t **tail = &list;
        
        while (**code && **code != ')') {
            lisp_value_t *elem = lisp_parse(vm, code);
            if (!elem) break;
            
            *tail = lisp_cons(vm, elem, lisp_nil(vm));
            tail = &(*tail)->as.cons.cdr;
            skip_whitespace(code);
        }
        
        if (**code == ')') (*code)++;
        return list;
    }
    
    // Number (including hex)
    if (isdigit(**code) || (**code == '-' && isdigit((*code)[1])) ||
        (**code == '0' && (*code)[1] == 'x')) {
        
        char *end;
        int32_t num;
        
        if (**code == '0' && (*code)[1] == 'x') {
            num = strtol(*code, &end, 16);
        } else {
            num = strtol(*code, &end, 10);
        }
        
        *code = end;
        return lisp_number(vm, num);
    }
    
    // Symbol
    const char *start = *code;
    while (**code && !isspace(**code) && **code != '(' && **code != ')') {
        (*code)++;
    }
    
    size_t len = *code - start;
    char *sym = (char*)malloc(len + 1);
    strncpy(sym, start, len);
    sym[len] = '\0';
    
    return lisp_symbol(vm, sym);
}

// ===== Environment =====

lisp_value_t* lisp_env_lookup(lisp_vm_t *vm, lisp_value_t *env, lisp_value_t *symbol) {
    if (!IS_SYMBOL(symbol)) return NULL;
    
    while (IS_CONS(env)) {
        lisp_value_t *binding = lisp_car(env);
        if (IS_CONS(binding)) {
            lisp_value_t *key = lisp_car(binding);
            if (IS_SYMBOL(key) && key->as.symbol_id == symbol->as.symbol_id) {
                return lisp_cdr(binding);
            }
        }
        env = lisp_cdr(env);
    }
    
    return NULL;
}

lisp_value_t* lisp_env_define(lisp_vm_t *vm, lisp_value_t *env, lisp_value_t *symbol, lisp_value_t *value) {
    lisp_value_t *binding = lisp_cons(vm, symbol, value);
    vm->global_env = lisp_cons(vm, binding, vm->global_env);
    return value;
}

lisp_value_t* lisp_env_set(lisp_vm_t *vm, lisp_value_t *env, lisp_value_t *symbol, lisp_value_t *value) {
    if (!IS_SYMBOL(symbol)) return NULL;
    
    lisp_value_t *orig = env;
    while (IS_CONS(env)) {
        lisp_value_t *binding = lisp_car(env);
        if (IS_CONS(binding)) {
            lisp_value_t *key = lisp_car(binding);
            if (IS_SYMBOL(key) && key->as.symbol_id == symbol->as.symbol_id) {
                binding->as.cons.cdr = value;
                return value;
            }
        }
        env = lisp_cdr(env);
    }
    
    vm->error_msg = "Undefined variable";
    return NULL;
}

// ===== Evaluation =====

lisp_value_t* lisp_eval(lisp_vm_t *vm, lisp_value_t *expr, lisp_value_t *env) {
    if (!expr) return lisp_nil(vm);
    
    // Self-evaluating
    if (IS_NUMBER(expr) || IS_STRING(expr) || IS_SPRITE(expr)) {
        return expr;
    }
    
    // Variable lookup
    if (IS_SYMBOL(expr)) {
        lisp_value_t *val = lisp_env_lookup(vm, env, expr);
        if (!val) {
            printf("Undefined: %s\n", vm->symbols[expr->as.symbol_id]);
            return lisp_nil(vm);
        }
        return val;
    }
    
    // List evaluation
    if (IS_CONS(expr)) {
        lisp_value_t *op = lisp_car(expr);
        lisp_value_t *args = lisp_cdr(expr);
        
        // Special forms
        if (IS_SYMBOL(op)) {
            const char *name = vm->symbols[op->as.symbol_id];
            
            if (strcmp(name, "define") == 0) {
                lisp_value_t *sym = lisp_nth(args, 0);
                lisp_value_t *val = lisp_eval(vm, lisp_nth(args, 1), env);
                return lisp_env_define(vm, env, sym, val);
            }
            
            if (strcmp(name, "set!") == 0) {
                lisp_value_t *sym = lisp_nth(args, 0);
                lisp_value_t *val = lisp_eval(vm, lisp_nth(args, 1), env);
                return lisp_env_set(vm, env, sym, val);
            }
            
            if (strcmp(name, "if") == 0) {
                lisp_value_t *test = lisp_eval(vm, lisp_nth(args, 0), env);
                bool cond = !(IS_NIL(test) || (IS_NUMBER(test) && test->as.number == 0));
                return lisp_eval(vm, lisp_nth(args, cond ? 1 : 2), env);
            }
            
            if (strcmp(name, "lambda") == 0) {
                lisp_value_t *lam = lisp_alloc(vm, LISP_LAMBDA);
                lam->as.lambda.params = lisp_nth(args, 0);
                lam->as.lambda.body = lisp_nth(args, 1);
                lam->as.lambda.env = env;
                return lam;
            }
            
            if (strcmp(name, "on-update") == 0) {
                vm->on_update = lisp_eval(vm, lisp_nth(args, 0), env);
                return vm->on_update;
            }
            
            if (strcmp(name, "on-button-a") == 0) {
                vm->on_button_callbacks[0] = lisp_eval(vm, lisp_nth(args, 0), env);
                return vm->on_button_callbacks[0];
            }
            
            if (strcmp(name, "on-button-b") == 0) {
                vm->on_button_callbacks[1] = lisp_eval(vm, lisp_nth(args, 0), env);
                return vm->on_button_callbacks[1];
            }
            
            if (strcmp(name, "on-button-x") == 0) {
                vm->on_button_callbacks[2] = lisp_eval(vm, lisp_nth(args, 0), env);
                return vm->on_button_callbacks[2];
            }
            
            if (strcmp(name, "on-button-y") == 0) {
                vm->on_button_callbacks[3] = lisp_eval(vm, lisp_nth(args, 0), env);
                return vm->on_button_callbacks[3];
            }
        }
        
        // Function call - evaluate all arguments
        lisp_value_t *fn = lisp_eval(vm, op, env);
        
        // Build evaluated args list
        lisp_value_t *eval_args = NULL;
        lisp_value_t **tail = &eval_args;
        while (IS_CONS(args)) {
            lisp_value_t *arg = lisp_eval(vm, lisp_car(args), env);
            *tail = lisp_cons(vm, arg, lisp_nil(vm));
            tail = &(*tail)->as.cons.cdr;
            args = lisp_cdr(args);
        }
        
        return lisp_apply(vm, fn, eval_args, env);
    }
    
    return lisp_nil(vm);
}

lisp_value_t* lisp_apply(lisp_vm_t *vm, lisp_value_t *fn, lisp_value_t *args, lisp_value_t *env) {
    if (!fn) return lisp_nil(vm);
    
    // Built-in function
    if (fn->type == LISP_BUILTIN) {
        return fn->as.builtin(vm, args);
    }
    
    // Lambda
    if (IS_LAMBDA(fn)) {
        // Create new environment with lambda's closure
        lisp_value_t *new_env = fn->as.lambda.env;
        
        // Bind parameters
        lisp_value_t *params = fn->as.lambda.params;
        while (IS_CONS(params) && IS_CONS(args)) {
            lisp_value_t *param = lisp_car(params);
            lisp_value_t *arg = lisp_car(args);
            lisp_value_t *binding = lisp_cons(vm, param, arg);
            new_env = lisp_cons(vm, binding, new_env);
            params = lisp_cdr(params);
            args = lisp_cdr(args);
        }
        
        return lisp_eval(vm, fn->as.lambda.body, new_env);
    }
    
    return lisp_nil(vm);
}

// ===== Sprites =====

lisp_sprite_t* lisp_create_sprite(lisp_vm_t *vm, uint8_t w, uint8_t h, const uint16_t *data) {
    if (vm->sprite_count >= LISP_MAX_SPRITES) return NULL;
    if (w > LISP_SPRITE_MAX_SIZE || h > LISP_SPRITE_MAX_SIZE) return NULL;
    
    lisp_sprite_t *sprite = &vm->sprites[vm->sprite_count++];
    sprite->width = w;
    sprite->height = h;
    
    if (data) {
        memcpy(sprite->data, data, w * h * sizeof(uint16_t));
    } else {
        memset(sprite->data, 0, w * h * sizeof(uint16_t));
    }
    
    return sprite;
}

void lisp_draw_sprite(lisp_sprite_t *sprite, int16_t x, int16_t y) {
    if (!sprite) return;
    
    // Use framebuffer for smooth rendering
    uint16_t *fb = disp_get_framebuffer();
    if (!fb) {
        // Fallback to direct drawing
        disp_blit(x, y, sprite->width, sprite->height, sprite->data);
        return;
    }
    
    for (uint8_t sy = 0; sy < sprite->height; sy++) {
        for (uint8_t sx = 0; sx < sprite->width; sx++) {
            int16_t px = x + sx;
            int16_t py = y + sy;
            
            if (px >= 0 && px < DISPLAY_WIDTH && py >= 0 && py < DISPLAY_HEIGHT) {
                uint16_t color = sprite->data[sy * sprite->width + sx];
                // Skip transparent pixels (color 0xF81F = magenta = transparent)
                if (color != 0xF81F) {
                    fb[py * DISPLAY_WIDTH + px] = color;
                }
            }
        }
    }
}

// ===== Collision Detection =====

bool lisp_rect_collide(lisp_rect_t *a, lisp_rect_t *b) {
    return !(a->x + a->w < b->x || b->x + b->w < a->x ||
             a->y + a->h < b->y || b->y + b->h < a->y);
}

bool lisp_point_in_rect(int16_t px, int16_t py, lisp_rect_t *rect) {
    return px >= rect->x && px < rect->x + rect->w &&
           py >= rect->y && py < rect->y + rect->h;
}

// ===== Game Loop =====

void lisp_run_game(lisp_vm_t *vm) {
    vm->running = true;
}

void lisp_stop_game(lisp_vm_t *vm) {
    vm->running = false;
}

void lisp_update(lisp_vm_t *vm) {
    if (!vm->running) return;
    
    // Update buttons
    buttons_update();
    
    // Check button callbacks
    for (int i = 0; i < 4; i++) {
        if (button_just_pressed((button_t)i) && vm->on_button_callbacks[i]) {
            lisp_apply(vm, vm->on_button_callbacks[i], lisp_nil(vm), vm->global_env);
        }
    }
    
    // Call update callback
    if (vm->on_update) {
        lisp_apply(vm, vm->on_update, lisp_nil(vm), vm->global_env);
    }
    
    // Flush framebuffer if used
    if (disp_get_framebuffer()) {
        disp_framebuffer_flush();
    }
}

// Continues in next message...