#include "lisp_vm.h"

// Helper to get number arg
static int32_t get_num(lisp_value_t *v) {
    return IS_NUMBER(v) ? v->as.number : 0;
}

// ===== Graphics Built-ins =====

lisp_value_t* lisp_builtin_clear(lisp_vm_t *vm, lisp_value_t *args) {
    uint16_t color = get_num(lisp_car(args));
    
    if (disp_get_framebuffer()) {
        disp_framebuffer_clear(color);
    } else {
        disp_clear(color);
    }
    
    return lisp_nil(vm);
}

lisp_value_t* lisp_builtin_fill_rect(lisp_vm_t *vm, lisp_value_t *args) {
    int16_t x = get_num(lisp_nth(args, 0));
    int16_t y = get_num(lisp_nth(args, 1));
    uint16_t w = get_num(lisp_nth(args, 2));
    uint16_t h = get_num(lisp_nth(args, 3));
    uint16_t color = get_num(lisp_nth(args, 4));
    
    if (disp_get_framebuffer()) {
        disp_framebuffer_fill_rect(x, y, w, h, color);
    } else {
        disp_fill_rect(x, y, w, h, color);
    }
    
    return lisp_nil(vm);
}

lisp_value_t* lisp_builtin_draw_text(lisp_vm_t *vm, lisp_value_t *args) {
    int16_t x = get_num(lisp_nth(args, 0));
    int16_t y = get_num(lisp_nth(args, 1));
    lisp_value_t *text_val = lisp_nth(args, 2);
    uint16_t fg = get_num(lisp_nth(args, 3));
    uint16_t bg = get_num(lisp_nth(args, 4));
    
    const char *text = "";
    if (IS_STRING(text_val)) {
        text = text_val->as.string;
    } else if (IS_SYMBOL(text_val)) {
        text = vm->symbols[text_val->as.symbol_id];
    }
    
    if (disp_get_framebuffer()) {
        disp_framebuffer_draw_text(x, y, text, fg, bg);
    } else {
        disp_draw_text(x, y, text, fg, bg);
    }
    
    return lisp_nil(vm);
}

lisp_value_t* lisp_builtin_draw_sprite(lisp_vm_t *vm, lisp_value_t *args) {
    lisp_value_t *sprite_val = lisp_nth(args, 0);
    int16_t x = get_num(lisp_nth(args, 1));
    int16_t y = get_num(lisp_nth(args, 2));
    
    if (IS_SPRITE(sprite_val)) {
        lisp_draw_sprite(sprite_val->as.sprite, x, y);
    }
    
    return lisp_nil(vm);
}

// ===== Sprite Built-ins =====

lisp_value_t* lisp_builtin_make_sprite(lisp_vm_t *vm, lisp_value_t *args) {
    uint8_t w = get_num(lisp_nth(args, 0));
    uint8_t h = get_num(lisp_nth(args, 1));
    
    lisp_sprite_t *sprite = lisp_create_sprite(vm, w, h, NULL);
    if (!sprite) return lisp_nil(vm);
    
    lisp_value_t *v = lisp_alloc(vm, LISP_SPRITE);
    if (v) v->as.sprite = sprite;
    return v;
}

lisp_value_t* lisp_builtin_sprite_set_pixel(lisp_vm_t *vm, lisp_value_t *args) {
    lisp_value_t *sprite_val = lisp_nth(args, 0);
    uint8_t x = get_num(lisp_nth(args, 1));
    uint8_t y = get_num(lisp_nth(args, 2));
    uint16_t color = get_num(lisp_nth(args, 3));
    
    if (IS_SPRITE(sprite_val)) {
        lisp_sprite_t *sprite = sprite_val->as.sprite;
        if (x < sprite->width && y < sprite->height) {
            sprite->data[y * sprite->width + x] = color;
        }
    }
    
    return sprite_val;
}

// ===== Collision Built-ins =====

lisp_value_t* lisp_builtin_collide(lisp_vm_t *vm, lisp_value_t *args) {
    // (collide? x1 y1 w1 h1 x2 y2 w2 h2)
    lisp_rect_t a = {
        get_num(lisp_nth(args, 0)),
        get_num(lisp_nth(args, 1)),
        get_num(lisp_nth(args, 2)),
        get_num(lisp_nth(args, 3))
    };
    
    lisp_rect_t b = {
        get_num(lisp_nth(args, 4)),
        get_num(lisp_nth(args, 5)),
        get_num(lisp_nth(args, 6)),
        get_num(lisp_nth(args, 7))
    };
    
    bool collides = lisp_rect_collide(&a, &b);
    return lisp_number(vm, collides ? 1 : 0);
}

// ===== Math Built-ins =====

lisp_value_t* lisp_builtin_add(lisp_vm_t *vm, lisp_value_t *args) {
    int32_t sum = 0;
    while (IS_CONS(args)) {
        sum += get_num(lisp_car(args));
        args = lisp_cdr(args);
    }
    return lisp_number(vm, sum);
}

lisp_value_t* lisp_builtin_sub(lisp_vm_t *vm, lisp_value_t *args) {
    if (!IS_CONS(args)) return lisp_number(vm, 0);
    
    int32_t result = get_num(lisp_car(args));
    args = lisp_cdr(args);
    
    if (!IS_CONS(args)) {
        return lisp_number(vm, -result);
    }
    
    while (IS_CONS(args)) {
        result -= get_num(lisp_car(args));
        args = lisp_cdr(args);
    }
    return lisp_number(vm, result);
}

lisp_value_t* lisp_builtin_mul(lisp_vm_t *vm, lisp_value_t *args) {
    int32_t product = 1;
    while (IS_CONS(args)) {
        product *= get_num(lisp_car(args));
        args = lisp_cdr(args);
    }
    return lisp_number(vm, product);
}

lisp_value_t* lisp_builtin_div(lisp_vm_t *vm, lisp_value_t *args) {
    if (!IS_CONS(args)) return lisp_number(vm, 0);
    
    int32_t result = get_num(lisp_car(args));
    args = lisp_cdr(args);
    
    while (IS_CONS(args)) {
        int32_t divisor = get_num(lisp_car(args));
        if (divisor != 0) result /= divisor;
        args = lisp_cdr(args);
    }
    return lisp_number(vm, result);
}

lisp_value_t* lisp_builtin_lt(lisp_vm_t *vm, lisp_value_t *args) {
    int32_t a = get_num(lisp_nth(args, 0));
    int32_t b = get_num(lisp_nth(args, 1));
    return lisp_number(vm, a < b ? 1 : 0);
}

lisp_value_t* lisp_builtin_gt(lisp_vm_t *vm, lisp_value_t *args) {
    int32_t a = get_num(lisp_nth(args, 0));
    int32_t b = get_num(lisp_nth(args, 1));
    return lisp_number(vm, a > b ? 1 : 0);
}

lisp_value_t* lisp_builtin_eq(lisp_vm_t *vm, lisp_value_t *args) {
    int32_t a = get_num(lisp_nth(args, 0));
    int32_t b = get_num(lisp_nth(args, 1));
    return lisp_number(vm, a == b ? 1 : 0);
}

// ===== Control Built-ins =====

lisp_value_t* lisp_builtin_start(lisp_vm_t *vm, lisp_value_t *args) {
    lisp_run_game(vm);
    return lisp_nil(vm);
}

lisp_value_t* lisp_builtin_stop(lisp_vm_t *vm, lisp_value_t *args) {
    lisp_stop_game(vm);
    return lisp_nil(vm);
}

// ===== Utilities =====

const char* lisp_type_name(lisp_type_t type) {
    switch (type) {
        case LISP_NIL: return "nil";
        case LISP_NUMBER: return "number";
        case LISP_SYMBOL: return "symbol";
        case LISP_CONS: return "cons";
        case LISP_BUILTIN: return "builtin";
        case LISP_LAMBDA: return "lambda";
        case LISP_STRING: return "string";
        case LISP_SPRITE: return "sprite";
        default: return "unknown";
    }
}

void lisp_print(lisp_value_t *value) {
    if (!value) {
        printf("NULL");
        return;
    }
    
    switch (value->type) {
        case LISP_NIL:
            printf("nil");
            break;
        case LISP_NUMBER:
            printf("%d", value->as.number);
            break;
        case LISP_SYMBOL:
            printf("'%s", "?");  // Would need VM context
            break;
        case LISP_STRING:
            printf("\"%s\"", value->as.string);
            break;
        case LISP_CONS:
            printf("(");
            while (IS_CONS(value)) {
                lisp_print(lisp_car(value));
                value = lisp_cdr(value);
                if (IS_CONS(value)) printf(" ");
            }
            if (!IS_NIL(value)) {
                printf(" . ");
                lisp_print(value);
            }
            printf(")");
            break;
        case LISP_LAMBDA:
            printf("<lambda>");
            break;
        case LISP_BUILTIN:
            printf("<builtin>");
            break;
        case LISP_SPRITE:
            printf("<sprite %dx%d>", value->as.sprite->width, value->as.sprite->height);
            break;
    }
}