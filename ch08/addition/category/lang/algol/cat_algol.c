#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <assert.h>


// CATEGORY THEORY CORE - Objects

typedef enum {
    OBJ_INT,
    OBJ_BOOL,
    OBJ_UNIT,
    OBJ_PRODUCT,
    OBJ_ARROW,
    OBJ_FUNCTOR_APP
} ObjectType;

typedef struct Object {
    ObjectType type;
    struct Object* left;      // domain for arrows, left for products
    struct Object* right;     // codomain for arrows, right for products
    struct Functor* functor;  // only for OBJ_FUNCTOR_APP: the functor F
    struct Object* arg;       // only for OBJ_FUNCTOR_APP: the argument A in F(A)
} Object;


// FUNCTORS - Structure-preserving maps between categories

typedef enum {
    FUNCTOR_LIST,
    FUNCTOR_MAYBE,
    FUNCTOR_IDENTITY
} FunctorType;

typedef struct Functor {
    FunctorType type;
    char name[64];
    Object* (*map_object)(struct Functor*, Object*);
} Functor;

// Fwd decl
struct AST;
typedef struct AST AST;

// List functor: List(A)
Object* list_map_object(Functor* f, Object* o) {
    Object* result = malloc(sizeof(Object));
    result->type = OBJ_FUNCTOR_APP;
    result->functor = f;
    result->arg = o;
    result->left = NULL;
    result->right = NULL;
    return result;
}

// Maybe functor: Maybe(A)
Object* maybe_map_object(Functor* f, Object* o) {
    Object* result = malloc(sizeof(Object));
    result->type = OBJ_FUNCTOR_APP;
    result->functor = f;
    result->arg = o;
    result->left = NULL;
    result->right = NULL;
    return result;
}

// Identity functor: Id(A) = A
Object* identity_map_object(Functor* f, Object* o) {
    return o;
}

// Helper
int obj_equal(Object* a, Object* b) {
    if (!a || !b) return a == b;
    if (a->type != b->type) return 0;
    
    switch (a->type) {
        case OBJ_INT:
        case OBJ_BOOL:
        case OBJ_UNIT:
            return 1;
        case OBJ_ARROW:
            return obj_equal(a->left, b->left) && obj_equal(a->right, b->right);
        case OBJ_FUNCTOR_APP:
            return a->functor == b->functor && obj_equal(a->arg, b->arg);
        default:
            return 0;
    }
}

Functor* functor_list() {
    Functor* f = malloc(sizeof(Functor));
    f->type = FUNCTOR_LIST;
    strcpy(f->name, "List");
    f->map_object = list_map_object;
    return f;
}

Functor* functor_maybe() {
    Functor* f = malloc(sizeof(Functor));
    f->type = FUNCTOR_MAYBE;
    strcpy(f->name, "Maybe");
    f->map_object = maybe_map_object;
    return f;
}

Functor* functor_identity() {
    Functor* f = malloc(sizeof(Functor));
    f->type = FUNCTOR_IDENTITY;
    strcpy(f->name, "Id");
    f->map_object = identity_map_object;
    return f;
}


// AST - Abstract Syntax Tree

typedef enum {
    AST_INT,
    AST_BOOL,
    AST_VAR,
    AST_LAMBDA,
    AST_APP,
    AST_COMPOSE,
    AST_BINOP,
    AST_LIST,
    AST_MAYBE_JUST,
    AST_MAYBE_NOTHING,
    AST_FMAP
} ASTType;

typedef struct AST {
    ASTType type;
    union {
        int int_val;
        int bool_val;
        struct { char name[64]; } var;
        struct { char param[64]; Object* param_type; struct AST* body; } lambda;
        struct { struct AST* func; struct AST* arg; } app;
        struct { struct AST* f; struct AST* g; } compose;
        struct { char op; struct AST* left; struct AST* right; } binop;
        struct { struct AST** elements; int count; } list;
        struct { struct AST* value; } maybe_just;
        struct { Functor* functor; struct AST* func; struct AST* container; } fmap;
    } data;
    Object* obj_type;
} AST;


// OBJECT CONSTRUCTORS

Object* obj_int() {
    Object* o = malloc(sizeof(Object));
    o->type = OBJ_INT;
    o->left = NULL;
    o->right = NULL;
    o->functor = NULL;
    o->arg = NULL;
    return o;
}

Object* obj_bool() {
    Object* o = malloc(sizeof(Object));
    o->type = OBJ_BOOL;
    o->left = NULL;
    o->right = NULL;
    o->functor = NULL;
    o->arg = NULL;
    return o;
}

Object* obj_arrow(Object* dom, Object* cod) {
    Object* o = malloc(sizeof(Object));
    o->type = OBJ_ARROW;
    o->left = dom;
    o->right = cod;
    o->functor = NULL;
    o->arg = NULL;
    return o;
}

Object* obj_functor_app(Functor* f, Object* arg) {
    return f->map_object(f, arg);
}


// AST CONSTRUCTORS

AST* ast_int(int val) {
    AST* a = malloc(sizeof(AST));
    a->type = AST_INT;
    a->data.int_val = val;
    a->obj_type = obj_int();
    return a;
}

AST* ast_var(const char* name) {
    AST* a = malloc(sizeof(AST));
    a->type = AST_VAR;
    strcpy(a->data.var.name, name);
    a->obj_type = NULL;  // to be inferred
    return a;
}

AST* ast_lambda(const char* param, Object* param_type, AST* body) {
    AST* a = malloc(sizeof(AST));
    a->type = AST_LAMBDA;
    strcpy(a->data.lambda.param, param);
    a->data.lambda.param_type = param_type;
    a->data.lambda.body = body;
    a->obj_type = obj_arrow(param_type, body->obj_type);
    return a;
}

AST* ast_binop(char op, AST* left, AST* right) {
    AST* a = malloc(sizeof(AST));
    a->type = AST_BINOP;
    a->data.binop.op = op;
    a->data.binop.left = left;
    a->data.binop.right = right;
    a->obj_type = obj_int();  // simplified
    return a;
}

AST* ast_compose(AST* f, AST* g) {
    AST* a = malloc(sizeof(AST));
    a->type = AST_COMPOSE;
    a->data.compose.f = f;
    a->data.compose.g = g;
    // f ∘ g : domain(g) → codomain(f)
    a->obj_type = obj_arrow(g->obj_type->left, f->obj_type->right);
    return a;
}

AST* ast_app(AST* func, AST* arg) {
    AST* a = malloc(sizeof(AST));
    a->type = AST_APP;
    a->data.app.func = func;
    a->data.app.arg = arg;
    a->obj_type = func->obj_type->right;
    return a;
}

AST* ast_list(AST** elements, int count) {
    AST* a = malloc(sizeof(AST));
    a->type = AST_LIST;
    a->data.list.elements = elements;
    a->data.list.count = count;
    a->obj_type = obj_functor_app(functor_list(), obj_int());
    return a;
}

AST* ast_maybe_just(AST* value) {
    AST* a = malloc(sizeof(AST));
    a->type = AST_MAYBE_JUST;
    a->data.maybe_just.value = value;
    a->obj_type = obj_functor_app(functor_maybe(), value->obj_type);
    return a;
}

AST* ast_maybe_nothing(Object* inner_type) {
    AST* a = malloc(sizeof(AST));
    a->type = AST_MAYBE_NOTHING;
    a->obj_type = obj_functor_app(functor_maybe(), inner_type);
    return a;
}

AST* ast_fmap(Functor* functor, AST* func, AST* container) {
    AST* a = malloc(sizeof(AST));
    a->type = AST_FMAP;
    a->data.fmap.functor = functor;
    a->data.fmap.func = func;
    a->data.fmap.container = container;
    a->obj_type = obj_functor_app(functor, func->obj_type->right);
    return a;
}


// COMPILER & VM (minimal but functional)

typedef enum {
    OP_PUSH_INT,
    OP_LOAD,
    OP_ADD, OP_SUB, OP_MUL, OP_EQ, OP_LT,
    OP_MAKE_LIST,
    OP_MAKE_JUST,
    OP_MAKE_NOTHING,
    OP_HALT
} OpCode;

typedef struct {
    OpCode op;
    int arg;
} Instruction;

typedef struct {
    Instruction code[1024];
    int ip;
    int stack[256];
    int sp;
    int locals[64];
} VM;

typedef struct {
    int var_count;
    char vars[64][64];
    int var_addrs[64];
} CompileEnv;

void emit(VM* vm, OpCode op, int arg) {
    vm->code[vm->ip].op = op;
    vm->code[vm->ip].arg = arg;
    vm->ip++;
}

int find_var(CompileEnv* env, const char* name) {
    for (int i = 0; i < env->var_count; i++) {
        if (strcmp(env->vars[i], name) == 0) return env->var_addrs[i];
    }
    return -1;
}

void compile_ast(AST* ast, VM* vm, CompileEnv* env) {
    switch (ast->type) {

        case AST_INT:
            emit(vm, OP_PUSH_INT, ast->data.int_val);
            break;

        case AST_VAR: {
            int addr = find_var(env, ast->data.var.name);
            if (addr >= 0) emit(vm, OP_LOAD, addr);
            break;
        }

        case AST_BINOP:
            compile_ast(ast->data.binop.left, vm, env);
            compile_ast(ast->data.binop.right, vm, env);
            switch (ast->data.binop.op) {
                case '+': emit(vm, OP_ADD, 0); break;
                case '-': emit(vm, OP_SUB, 0); break;
                case '*': emit(vm, OP_MUL, 0); break;
                case '=': emit(vm, OP_EQ, 0); break;
                case '<': emit(vm, OP_LT, 0); break;
            }
            break;

        case AST_LIST:
            for (int i = 0; i < ast->data.list.count; i++) {
                compile_ast(ast->data.list.elements[i], vm, env);
            }
            emit(vm, OP_MAKE_LIST, ast->data.list.count);
            break;

        case AST_MAYBE_JUST:
            compile_ast(ast->data.maybe_just.value, vm, env);
            emit(vm, OP_MAKE_JUST, 0);
            break;

        case AST_MAYBE_NOTHING:
            emit(vm, OP_MAKE_NOTHING, 0);
            break;

        default:
            break;
    }
}

void vm_init(VM* vm) {
    memset(vm, 0, sizeof(VM));
    vm->sp = -1;
}

void vm_push(VM* vm, int val) { vm->stack[++vm->sp] = val; }
int vm_pop(VM* vm) { return vm->stack[vm->sp--]; }

void vm_execute(VM* vm) {
    vm->ip = 0;
    while (vm->ip < 1024) {
        Instruction inst = vm->code[vm->ip++];
        switch (inst.op) {
            case OP_PUSH_INT: vm_push(vm, inst.arg); break;
            case OP_LOAD: vm_push(vm, vm->locals[inst.arg]); break;
            case OP_ADD: { int b = vm_pop(vm), a = vm_pop(vm); vm_push(vm, a + b); break; }
            case OP_SUB: { int b = vm_pop(vm), a = vm_pop(vm); vm_push(vm, a - b); break; }
            case OP_MUL: { int b = vm_pop(vm), a = vm_pop(vm); vm_push(vm, a * b); break; }
            case OP_EQ:  { int b = vm_pop(vm), a = vm_pop(vm); vm_push(vm, a == b); break; }
            case OP_LT:  { int b = vm_pop(vm), a = vm_pop(vm); vm_push(vm, a < b); break; }
            case OP_MAKE_NOTHING: vm_push(vm, 0); break;
            case OP_HALT: return;
            default: break;
        }
    }
}


// PRETTY PRINTING & TESTING

int test_count = 0, test_passed = 0;

#define TEST(name) printf("\n[TEST] %s\n", name); test_count++;
#define ASSERT_EQ(a,b,msg) do { if ((a)==(b)) { printf(" ✓ %s\n", msg); test_passed++; } else printf(" ✗ %s (got %d, exp %d)\n", msg, (a), (b)); } while(0)
#define ASSERT_TRUE(c,msg) do { if (c) { printf(" ✓ %s\n", msg); test_passed++; } else printf(" ✗ %s\n", msg); } while(0)

void print_object(Object* o) {
    if (!o) { printf("NULL"); return; }
    switch (o->type) {
        case OBJ_INT: printf("Int"); break;
        case OBJ_BOOL: printf("Bool"); break;
        case OBJ_ARROW: printf("("); print_object(o->left); printf(" → "); print_object(o->right); printf(")"); break;
        case OBJ_FUNCTOR_APP: printf("%s(", o->functor->name); print_object(o->arg); printf(")"); break;
        default: printf("?"); break;
    }
}

void test_functors() {
    TEST("Functor application - List");
    Functor* list_f = functor_list();
    Object* list_int = obj_functor_app(list_f, obj_int());
    printf(" Type: "); print_object(list_int); printf("\n");
    ASSERT_TRUE(list_int->type == OBJ_FUNCTOR_APP && list_int->functor->type == FUNCTOR_LIST, "List(Int) correct");

    TEST("Functor application - Maybe");
    Functor* maybe_f = functor_maybe();
    Object* maybe_int = obj_functor_app(maybe_f, obj_int());
    printf(" Type: "); print_object(maybe_int); printf("\n");
    ASSERT_TRUE(maybe_int->type == OBJ_FUNCTOR_APP && maybe_int->functor->type == FUNCTOR_MAYBE, "Maybe(Int) correct");

    TEST("Identity functor");
    Functor* id_f = functor_identity();
    Object* id_int = obj_functor_app(id_f, obj_int());
    //ASSERT_TRUE(id_int == obj_int(), "Id(Int) ≡ Int");
    ASSERT_TRUE(obj_equal(id_int, obj_int()), "Id(Int) ≡ Int");
}

void test_morphisms() {
    TEST("Lambda creates arrow type");
    AST* body = ast_binop('+', ast_var("x"), ast_int(1));
    AST* lam = ast_lambda("x", obj_int(), body);
    printf(" λx.x+1 : "); print_object(lam->obj_type); printf("\n");
    ASSERT_TRUE(lam->obj_type->type == OBJ_ARROW, "Lambda has arrow type");

    TEST("Simple evaluation");
    VM vm;
    vm_init(&vm);
    CompileEnv env = {0};
    strcpy(env.vars[0], "x");
    env.var_addrs[0] = 0;
    env.var_count = 1;
    vm.locals[0] = 10;

    compile_ast(body, &vm, &env);
    emit(&vm, OP_HALT, 0);
    vm_execute(&vm);
    ASSERT_EQ(vm.stack[vm.sp], 11, "10 + 1 = 11");
}

void test_composition() {
    TEST("Composition type");
    AST* inc = ast_lambda("x", obj_int(), ast_binop('+', ast_var("x"), ast_int(1)));
    AST* dbl = ast_lambda("y", obj_int(), ast_binop('*', ast_var("y"), ast_int(2)));
    AST* comp = ast_compose(inc, dbl);  // inc ∘ dbl

    printf(" dbl       : "); print_object(dbl->obj_type); printf("\n");
    printf(" inc       : "); print_object(inc->obj_type); printf("\n");
    printf(" inc ∘ dbl : "); print_object(comp->obj_type); printf("\n");
    ASSERT_TRUE(comp->obj_type->type == OBJ_ARROW, "Composition is arrow");
}

void test_containers() {
    TEST("List construction");
    AST* elems[3] = { ast_int(5), ast_int(6), ast_int(7) };
    AST* list = ast_list(elems, 3);
    printf(" [5,6,7] : "); print_object(list->obj_type); printf("\n");

    TEST("Maybe Just / Nothing");
    AST* just = ast_maybe_just(ast_int(42));
    AST* nothing = ast_maybe_nothing(obj_int());
    printf(" Just(42)  : "); print_object(just->obj_type); printf("\n");
    printf(" Nothing   : "); print_object(nothing->obj_type); printf("\n");
}




int main() {
    printf("Categorical Programming Prototype\n");
    printf("Functors, Objects, Arrows, and a tiny VM\n\n");

    test_functors();
    test_morphisms();
    test_composition();
    test_containers();

    printf("\nTests passed: %d / %d\n", test_passed, test_count);
    return 0;
}

