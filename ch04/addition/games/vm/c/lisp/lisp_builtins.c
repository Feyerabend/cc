// Language built-ins: arithmetic, comparison, lists and printing.
// The game built-ins (graphics, sprites, buttons) are in lisp_game.c.

#include "lisp_vm.h"
#include <stdio.h>
#include <stdlib.h>

static void check_args(lisp_vm_t *vm, lisp_value_t *args, size_t min, size_t max, const char *name) {
    size_t n = lisp_length(args);
    if (n < min || n > max) {
        if (min == max) {
            lisp_fail(vm, "%s: expects %u arguments", name, (unsigned) min);
        }
        lisp_fail(vm, "%s: expects %u to %u arguments", name, (unsigned) min, (unsigned) max);
    }
}

static int32_t arg_int(lisp_vm_t *vm, lisp_value_t *args, size_t n) {
    return lisp_to_int(vm, lisp_nth(vm, args, n));
}

// Arithmetic wraps around on overflow, like the 32-bit hardware does.
// Doing it in unsigned arithmetic avoids undefined behaviour in C.
static int32_t wrap_add(int32_t a, int32_t b) { return (int32_t) ((uint32_t) a + (uint32_t) b); }
static int32_t wrap_sub(int32_t a, int32_t b) { return (int32_t) ((uint32_t) a - (uint32_t) b); }
static int32_t wrap_mul(int32_t a, int32_t b) { return (int32_t) ((uint32_t) a * (uint32_t) b); }

// Arithmetic

static lisp_value_t *bi_add(lisp_vm_t *vm, lisp_value_t *args) {
    int32_t sum = 0;
    for (; IS_CONS(args); args = args->as.cons.cdr) {
        sum = wrap_add(sum, lisp_to_int(vm, args->as.cons.car));
    }
    return lisp_number(vm, sum);
}

static lisp_value_t *bi_mul(lisp_vm_t *vm, lisp_value_t *args) {
    int32_t product = 1;
    for (; IS_CONS(args); args = args->as.cons.cdr) {
        product = wrap_mul(product, lisp_to_int(vm, args->as.cons.car));
    }
    return lisp_number(vm, product);
}

static lisp_value_t *bi_sub(lisp_vm_t *vm, lisp_value_t *args) {
    check_args(vm, args, 1, LISP_HEAP_SIZE, "-");
    int32_t result = arg_int(vm, args, 0);
    args = args->as.cons.cdr;
    if (IS_NIL(args)) {
        return lisp_number(vm, wrap_sub(0, result));
    }
    for (; IS_CONS(args); args = args->as.cons.cdr) {
        result = wrap_sub(result, lisp_to_int(vm, args->as.cons.car));
    }
    return lisp_number(vm, result);
}

static lisp_value_t *bi_div(lisp_vm_t *vm, lisp_value_t *args) {
    check_args(vm, args, 2, 2, "/");
    int32_t d = arg_int(vm, args, 1);
    int32_t n = arg_int(vm, args, 0);
    if (d == 0) lisp_fail(vm, "/: division by zero");
    if (d == -1) return lisp_number(vm, wrap_sub(0, n));  // INT32_MIN / -1 would trap
    return lisp_number(vm, n / d);
}

static lisp_value_t *bi_mod(lisp_vm_t *vm, lisp_value_t *args) {
    check_args(vm, args, 2, 2, "mod");
    int32_t a = arg_int(vm, args, 0);
    int32_t b = arg_int(vm, args, 1);
    if (b == 0) lisp_fail(vm, "mod: division by zero");
    if (b == -1) return lisp_number(vm, 0);
    int32_t r = a % b;
    // Result has the sign of the divisor, so (mod -1 10) is 9
    if (r != 0 && ((r < 0) != (b < 0))) r += b;
    return lisp_number(vm, r);
}

static lisp_value_t *bi_abs(lisp_vm_t *vm, lisp_value_t *args) {
    check_args(vm, args, 1, 1, "abs");
    int32_t n = arg_int(vm, args, 0);
    return lisp_number(vm, n < 0 ? wrap_sub(0, n) : n);
}

static lisp_value_t *bi_min(lisp_vm_t *vm, lisp_value_t *args) {
    check_args(vm, args, 1, LISP_HEAP_SIZE, "min");
    int32_t m = arg_int(vm, args, 0);
    for (args = args->as.cons.cdr; IS_CONS(args); args = args->as.cons.cdr) {
        int32_t n = lisp_to_int(vm, args->as.cons.car);
        if (n < m) m = n;
    }
    return lisp_number(vm, m);
}

static lisp_value_t *bi_max(lisp_vm_t *vm, lisp_value_t *args) {
    check_args(vm, args, 1, LISP_HEAP_SIZE, "max");
    int32_t m = arg_int(vm, args, 0);
    for (args = args->as.cons.cdr; IS_CONS(args); args = args->as.cons.cdr) {
        int32_t n = lisp_to_int(vm, args->as.cons.car);
        if (n > m) m = n;
    }
    return lisp_number(vm, m);
}

static lisp_value_t *bi_random(lisp_vm_t *vm, lisp_value_t *args) {
    // (random n) gives 0 .. n-1
    check_args(vm, args, 1, 1, "random");
    int32_t n = arg_int(vm, args, 0);
    if (n <= 0) lisp_fail(vm, "random: limit must be positive");
    return lisp_number(vm, rand() % n);
}

// Comparison. (< a b c) means a < b < c.

typedef enum { CMP_EQ, CMP_LT, CMP_GT, CMP_LE, CMP_GE } cmp_t;

static lisp_value_t *compare(lisp_vm_t *vm, lisp_value_t *args, cmp_t op, const char *name) {
    check_args(vm, args, 2, LISP_HEAP_SIZE, name);
    int32_t a = arg_int(vm, args, 0);
    for (args = args->as.cons.cdr; IS_CONS(args); args = args->as.cons.cdr) {
        int32_t b = lisp_to_int(vm, args->as.cons.car);
        bool ok = false;
        switch (op) {
            case CMP_EQ: ok = (a == b); break;
            case CMP_LT: ok = (a < b); break;
            case CMP_GT: ok = (a > b); break;
            case CMP_LE: ok = (a <= b); break;
            case CMP_GE: ok = (a >= b); break;
        }
        if (!ok) return lisp_bool(vm, false);
        a = b;
    }
    return lisp_bool(vm, true);
}

static lisp_value_t *bi_eq(lisp_vm_t *vm, lisp_value_t *args) { return compare(vm, args, CMP_EQ, "="); }
static lisp_value_t *bi_lt(lisp_vm_t *vm, lisp_value_t *args) { return compare(vm, args, CMP_LT, "<"); }
static lisp_value_t *bi_gt(lisp_vm_t *vm, lisp_value_t *args) { return compare(vm, args, CMP_GT, ">"); }
static lisp_value_t *bi_le(lisp_vm_t *vm, lisp_value_t *args) { return compare(vm, args, CMP_LE, "<="); }
static lisp_value_t *bi_ge(lisp_vm_t *vm, lisp_value_t *args) { return compare(vm, args, CMP_GE, ">="); }

static lisp_value_t *bi_not(lisp_vm_t *vm, lisp_value_t *args) {
    check_args(vm, args, 1, 1, "not");
    return lisp_bool(vm, !lisp_truthy(lisp_car(vm, args)));
}

static lisp_value_t *bi_eqp(lisp_vm_t *vm, lisp_value_t *args) {
    // Same object, or equal numbers
    check_args(vm, args, 2, 2, "eq?");
    lisp_value_t *a = lisp_nth(vm, args, 0);
    lisp_value_t *b = lisp_nth(vm, args, 1);
    if (IS_NUMBER(a) && IS_NUMBER(b)) {
        return lisp_bool(vm, a->as.number == b->as.number);
    }
    return lisp_bool(vm, a == b);
}

// Lists

static lisp_value_t *bi_cons(lisp_vm_t *vm, lisp_value_t *args) {
    check_args(vm, args, 2, 2, "cons");
    return lisp_cons(vm, lisp_nth(vm, args, 0), lisp_nth(vm, args, 1));
}

static lisp_value_t *bi_car(lisp_vm_t *vm, lisp_value_t *args) {
    check_args(vm, args, 1, 1, "car");
    return lisp_car(vm, lisp_car(vm, args));
}

static lisp_value_t *bi_cdr(lisp_vm_t *vm, lisp_value_t *args) {
    check_args(vm, args, 1, 1, "cdr");
    return lisp_cdr(vm, lisp_car(vm, args));
}

static lisp_value_t *bi_list(lisp_vm_t *vm, lisp_value_t *args) {
    // The argument list is freshly built for each call, so it can be returned as is
    (void) vm;
    return args;
}

static lisp_value_t *bi_reverse(lisp_vm_t *vm, lisp_value_t *args) {
    check_args(vm, args, 1, 1, "reverse");
    lisp_value_t *result = lisp_nil(vm);
    for (lisp_value_t *l = lisp_car(vm, args); !IS_NIL(l); l = lisp_cdr(vm, l)) {
        result = lisp_cons(vm, lisp_car(vm, l), result);
    }
    return result;
}

static lisp_value_t *bi_length(lisp_vm_t *vm, lisp_value_t *args) {
    check_args(vm, args, 1, 1, "length");
    return lisp_number(vm, (int32_t) lisp_length(lisp_car(vm, args)));
}

static lisp_value_t *bi_nth(lisp_vm_t *vm, lisp_value_t *args) {
    // (nth n list), counting from 0
    check_args(vm, args, 2, 2, "nth");
    int32_t n = arg_int(vm, args, 0);
    if (n < 0) lisp_fail(vm, "nth: negative index");
    return lisp_nth(vm, lisp_nth(vm, args, 1), (size_t) n);
}

static lisp_value_t *bi_nullp(lisp_vm_t *vm, lisp_value_t *args) {
    check_args(vm, args, 1, 1, "null?");
    return lisp_bool(vm, IS_NIL(lisp_car(vm, args)));
}

static lisp_value_t *bi_pairp(lisp_vm_t *vm, lisp_value_t *args) {
    check_args(vm, args, 1, 1, "pair?");
    return lisp_bool(vm, IS_CONS(lisp_car(vm, args)));
}

static lisp_value_t *bi_numberp(lisp_vm_t *vm, lisp_value_t *args) {
    check_args(vm, args, 1, 1, "number?");
    return lisp_bool(vm, IS_NUMBER(lisp_car(vm, args)));
}

// Strings and output

static lisp_value_t *bi_number_to_string(lisp_vm_t *vm, lisp_value_t *args) {
    check_args(vm, args, 1, 1, "number->string");
    char buf[LISP_STRING_SLOT_SIZE];
    snprintf(buf, sizeof(buf), "%ld", (long) arg_int(vm, args, 0));
    return lisp_string(vm, buf);
}

static lisp_value_t *bi_print(lisp_vm_t *vm, lisp_value_t *args) {
    // (print a b ...) writes the values separated by spaces, then a newline
    for (lisp_value_t *a = args; IS_CONS(a); a = a->as.cons.cdr) {
        lisp_print(a->as.cons.car);
        if (IS_CONS(a->as.cons.cdr)) printf(" ");
    }
    printf("\n");
    return IS_CONS(args) ? lisp_car(vm, args) : args;
}

void lisp_register_builtins(lisp_vm_t *vm) {
    lisp_define_builtin(vm, "+", bi_add);
    lisp_define_builtin(vm, "-", bi_sub);
    lisp_define_builtin(vm, "*", bi_mul);
    lisp_define_builtin(vm, "/", bi_div);
    lisp_define_builtin(vm, "mod", bi_mod);
    lisp_define_builtin(vm, "abs", bi_abs);
    lisp_define_builtin(vm, "min", bi_min);
    lisp_define_builtin(vm, "max", bi_max);
    lisp_define_builtin(vm, "random", bi_random);

    lisp_define_builtin(vm, "=", bi_eq);
    lisp_define_builtin(vm, "<", bi_lt);
    lisp_define_builtin(vm, ">", bi_gt);
    lisp_define_builtin(vm, "<=", bi_le);
    lisp_define_builtin(vm, ">=", bi_ge);
    lisp_define_builtin(vm, "not", bi_not);
    lisp_define_builtin(vm, "eq?", bi_eqp);

    lisp_define_builtin(vm, "cons", bi_cons);
    lisp_define_builtin(vm, "car", bi_car);
    lisp_define_builtin(vm, "cdr", bi_cdr);
    lisp_define_builtin(vm, "list", bi_list);
    lisp_define_builtin(vm, "length", bi_length);
    lisp_define_builtin(vm, "reverse", bi_reverse);
    lisp_define_builtin(vm, "nth", bi_nth);
    lisp_define_builtin(vm, "null?", bi_nullp);
    lisp_define_builtin(vm, "pair?", bi_pairp);
    lisp_define_builtin(vm, "number?", bi_numberp);

    lisp_define_builtin(vm, "number->string", bi_number_to_string);
    lisp_define_builtin(vm, "print", bi_print);
}
