// Game built-ins: drawing, sprites, collision, buttons and the frame loop.
// All drawing goes to the framebuffer, which is sent to the display once
// per frame by lisp_game_frame.

#include "lisp_game.h"
#include "display.h"
#include <stdio.h>

static void check_args(lisp_vm_t *vm, lisp_value_t *args, size_t n, const char *name) {
    if (lisp_length(args) != n) {
        lisp_fail(vm, "%s: expects %u arguments", name, (unsigned) n);
    }
}

static int32_t arg_int(lisp_vm_t *vm, lisp_value_t *args, size_t n) {
    return lisp_to_int(vm, lisp_nth(vm, args, n));
}

static uint16_t arg_color(lisp_vm_t *vm, lisp_value_t *args, size_t n) {
    return (uint16_t) arg_int(vm, args, n);
}

static lisp_sprite_t *arg_sprite(lisp_vm_t *vm, lisp_value_t *args, size_t n) {
    lisp_value_t *v = lisp_nth(vm, args, n);
    if (!IS_SPRITE(v)) lisp_fail(vm, "Expected a sprite");
    return v->as.sprite;
}

// Clips a rectangle to the screen. Returns false if nothing is left.
static bool clip(int32_t *x, int32_t *y, int32_t *w, int32_t *h) {
    if (*x < 0) {
        *w += *x;
        *x = 0;
    }
    if (*y < 0) {
        *h += *y;
        *y = 0;
    }
    if (*x + *w > DISPLAY_WIDTH) *w = DISPLAY_WIDTH - *x;
    if (*y + *h > DISPLAY_HEIGHT) *h = DISPLAY_HEIGHT - *y;
    return *w > 0 && *h > 0;
}

// Drawing

static lisp_value_t *bi_clear(lisp_vm_t *vm, lisp_value_t *args) {
    // (clear color)
    check_args(vm, args, 1, "clear");
    disp_framebuffer_clear(arg_color(vm, args, 0));
    return lisp_nil(vm);
}

static lisp_value_t *bi_fill_rect(lisp_vm_t *vm, lisp_value_t *args) {
    // (fill-rect x y w h color)
    check_args(vm, args, 5, "fill-rect");
    int32_t x = arg_int(vm, args, 0);
    int32_t y = arg_int(vm, args, 1);
    int32_t w = arg_int(vm, args, 2);
    int32_t h = arg_int(vm, args, 3);
    if (clip(&x, &y, &w, &h)) {
        disp_framebuffer_fill_rect((uint16_t) x, (uint16_t) y, (uint16_t) w, (uint16_t) h,
                                   arg_color(vm, args, 4));
    }
    return lisp_nil(vm);
}

static lisp_value_t *bi_draw_text(lisp_vm_t *vm, lisp_value_t *args) {
    // (draw-text x y text fg bg), where text is a string or a number.
    // Characters are 6 pixels wide and 8 high.
    check_args(vm, args, 5, "draw-text");
    int32_t x = arg_int(vm, args, 0);
    int32_t y = arg_int(vm, args, 1);
    lisp_value_t *text = lisp_nth(vm, args, 2);
    uint16_t fg = arg_color(vm, args, 3);
    uint16_t bg = arg_color(vm, args, 4);

    const char *s;
    char buf[12];
    if (IS_STRING(text)) {
        s = text->as.string.text;
    } else if (IS_NUMBER(text)) {
        snprintf(buf, sizeof(buf), "%ld", (long) text->as.number);
        s = buf;
    } else if (IS_SYMBOL(text)) {
        s = text->as.symbol.name;
    } else {
        lisp_fail(vm, "draw-text: expected a string or a number");
        return NULL;
    }

    // Skip characters left of the screen, then let the display clip the rest
    while (*s && x < 0) {
        s++;
        x += 6;
    }
    if (*s && y >= 0 && y + 8 <= DISPLAY_HEIGHT && x < DISPLAY_WIDTH) {
        disp_framebuffer_draw_text((uint16_t) x, (uint16_t) y, s, fg, bg);
    }
    return lisp_nil(vm);
}

// Sprites

static lisp_value_t *bi_make_sprite(lisp_vm_t *vm, lisp_value_t *args) {
    // (make-sprite w h) makes a fully transparent sprite
    check_args(vm, args, 2, "make-sprite");
    return lisp_make_sprite(vm, arg_int(vm, args, 0), arg_int(vm, args, 1));
}

static lisp_value_t *bi_sprite_set_pixel(lisp_vm_t *vm, lisp_value_t *args) {
    // (sprite-set-pixel sprite x y color)
    check_args(vm, args, 4, "sprite-set-pixel");
    lisp_sprite_t *s = arg_sprite(vm, args, 0);
    int32_t x = arg_int(vm, args, 1);
    int32_t y = arg_int(vm, args, 2);
    if (x >= 0 && y >= 0 && x < s->width && y < s->height) {
        s->data[y * s->width + x] = arg_color(vm, args, 3);
    }
    return lisp_car(vm, args);
}

static lisp_value_t *bi_sprite_fill(lisp_vm_t *vm, lisp_value_t *args) {
    // (sprite-fill sprite x y w h color)
    check_args(vm, args, 6, "sprite-fill");
    lisp_sprite_t *s = arg_sprite(vm, args, 0);
    int32_t x0 = arg_int(vm, args, 1);
    int32_t y0 = arg_int(vm, args, 2);
    int32_t w = arg_int(vm, args, 3);
    int32_t h = arg_int(vm, args, 4);
    uint16_t color = arg_color(vm, args, 5);
    for (int32_t y = y0; y < y0 + h; y++) {
        for (int32_t x = x0; x < x0 + w; x++) {
            if (x >= 0 && y >= 0 && x < s->width && y < s->height) {
                s->data[y * s->width + x] = color;
            }
        }
    }
    return lisp_car(vm, args);
}

static lisp_value_t *bi_draw_sprite(lisp_vm_t *vm, lisp_value_t *args) {
    // (draw-sprite sprite x y). Transparent (magenta) pixels are skipped.
    check_args(vm, args, 3, "draw-sprite");
    lisp_sprite_t *s = arg_sprite(vm, args, 0);
    int32_t x0 = arg_int(vm, args, 1);
    int32_t y0 = arg_int(vm, args, 2);
    for (int32_t sy = 0; sy < s->height; sy++) {
        int32_t y = y0 + sy;
        if (y < 0 || y >= DISPLAY_HEIGHT) continue;
        for (int32_t sx = 0; sx < s->width; sx++) {
            int32_t x = x0 + sx;
            uint16_t color = s->data[sy * s->width + sx];
            if (x >= 0 && x < DISPLAY_WIDTH && color != LISP_TRANSPARENT) {
                disp_framebuffer_set_pixel((uint16_t) x, (uint16_t) y, color);
            }
        }
    }
    return lisp_nil(vm);
}

// Collision

static lisp_value_t *bi_collide(lisp_vm_t *vm, lisp_value_t *args) {
    // (collide? x1 y1 w1 h1 x2 y2 w2 h2): do the rectangles overlap?
    check_args(vm, args, 8, "collide?");
    int32_t ax = arg_int(vm, args, 0), ay = arg_int(vm, args, 1);
    int32_t aw = arg_int(vm, args, 2), ah = arg_int(vm, args, 3);
    int32_t bx = arg_int(vm, args, 4), by = arg_int(vm, args, 5);
    int32_t bw = arg_int(vm, args, 6), bh = arg_int(vm, args, 7);
    return lisp_bool(vm, ax < bx + bw && bx < ax + aw && ay < by + bh && by < ay + ah);
}

// Buttons and the game loop

static lisp_value_t *bi_button(lisp_vm_t *vm, lisp_value_t *args) {
    // (button? n) is true while button n is held down.
    // Use the constants button-a, button-b, button-x and button-y.
    check_args(vm, args, 1, "button?");
    int32_t b = arg_int(vm, args, 0);
    if (b < 0 || b >= BUTTON_COUNT) lisp_fail(vm, "button?: no such button");
    return lisp_bool(vm, button_pressed((button_t) b));
}

static lisp_value_t *set_callback(lisp_vm_t *vm, lisp_value_t *args, lisp_value_t **slot, const char *name) {
    check_args(vm, args, 1, name);
    lisp_value_t *fn = lisp_car(vm, args);
    if (!IS_LAMBDA(fn) && !IS_BUILTIN(fn) && !IS_NIL(fn)) {
        lisp_fail(vm, "%s: expected a function", name);
    }
    *slot = IS_NIL(fn) ? NULL : fn;
    return fn;
}

static lisp_value_t *bi_on_update(lisp_vm_t *vm, lisp_value_t *args) {
    return set_callback(vm, args, &vm->on_update, "on-update");
}

static lisp_value_t *bi_on_button_a(lisp_vm_t *vm, lisp_value_t *args) {
    return set_callback(vm, args, &vm->on_button[BUTTON_A], "on-button-a");
}

static lisp_value_t *bi_on_button_b(lisp_vm_t *vm, lisp_value_t *args) {
    return set_callback(vm, args, &vm->on_button[BUTTON_B], "on-button-b");
}

static lisp_value_t *bi_on_button_x(lisp_vm_t *vm, lisp_value_t *args) {
    return set_callback(vm, args, &vm->on_button[BUTTON_X], "on-button-x");
}

static lisp_value_t *bi_on_button_y(lisp_vm_t *vm, lisp_value_t *args) {
    return set_callback(vm, args, &vm->on_button[BUTTON_Y], "on-button-y");
}

static lisp_value_t *bi_start(lisp_vm_t *vm, lisp_value_t *args) {
    check_args(vm, args, 0, "start");
    vm->running = true;
    return lisp_bool(vm, true);
}

static lisp_value_t *bi_stop(lisp_vm_t *vm, lisp_value_t *args) {
    check_args(vm, args, 0, "stop");
    vm->running = false;
    return lisp_bool(vm, false);
}

void lisp_game_init(lisp_vm_t *vm) {
    lisp_define_builtin(vm, "clear", bi_clear);
    lisp_define_builtin(vm, "fill-rect", bi_fill_rect);
    lisp_define_builtin(vm, "draw-text", bi_draw_text);

    lisp_define_builtin(vm, "make-sprite", bi_make_sprite);
    lisp_define_builtin(vm, "sprite-set-pixel", bi_sprite_set_pixel);
    lisp_define_builtin(vm, "sprite-fill", bi_sprite_fill);
    lisp_define_builtin(vm, "draw-sprite", bi_draw_sprite);

    lisp_define_builtin(vm, "collide?", bi_collide);

    lisp_define_builtin(vm, "button?", bi_button);
    lisp_define_builtin(vm, "on-update", bi_on_update);
    lisp_define_builtin(vm, "on-button-a", bi_on_button_a);
    lisp_define_builtin(vm, "on-button-b", bi_on_button_b);
    lisp_define_builtin(vm, "on-button-x", bi_on_button_x);
    lisp_define_builtin(vm, "on-button-y", bi_on_button_y);
    lisp_define_builtin(vm, "start", bi_start);
    lisp_define_builtin(vm, "stop", bi_stop);

    lisp_define(vm, "screen-width", lisp_number(vm, DISPLAY_WIDTH));
    lisp_define(vm, "screen-height", lisp_number(vm, DISPLAY_HEIGHT));
    lisp_define(vm, "button-a", lisp_number(vm, BUTTON_A));
    lisp_define(vm, "button-b", lisp_number(vm, BUTTON_B));
    lisp_define(vm, "button-x", lisp_number(vm, BUTTON_X));
    lisp_define(vm, "button-y", lisp_number(vm, BUTTON_Y));
}

bool lisp_game_frame(lisp_vm_t *vm) {
    buttons_update();

    for (int i = 0; i < BUTTON_COUNT; i++) {
        if (vm->on_button[i] != NULL && button_just_pressed((button_t) i)) {
            if (lisp_call(vm, vm->on_button[i]) == NULL) return false;
        }
    }
    if (vm->on_update != NULL) {
        if (lisp_call(vm, vm->on_update) == NULL) return false;
    }

    disp_framebuffer_flush();
    return true;
}
