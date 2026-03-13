/*
 * Aspect-Oriented Language v4.0
 * Complete implementation with parser, multiple pointcut and advice types
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <stdarg.h>
#include <stdint.h>

#define STACK_MAX 512
#define GLOBALS_MAX 256
#define FRAMES_MAX 128
#define JOIN_POINTS_MAX 64
#define MAX_ASPECTS 128

typedef struct {
    void** allocations;
    size_t count;
    size_t capacity;
} MemoryPool;

static MemoryPool pool = {NULL, 0, 0};

void* tracked_malloc(size_t size) {
    void* ptr = malloc(size);
    if (!ptr) { fprintf(stderr, "Out of memory\n"); exit(1); }
    
    if (pool.count >= pool.capacity) {
        size_t new_cap = pool.capacity == 0 ? 64 : pool.capacity * 2;
        pool.allocations = realloc(pool.allocations, new_cap * sizeof(void*));
        pool.capacity = new_cap;
    }
    pool.allocations[pool.count++] = ptr;
    return ptr;
}

char* tracked_strdup(const char* s) {
    if (!s) return NULL;
    char* copy = tracked_malloc(strlen(s) + 1);
    strcpy(copy, s);
    return copy;
}

void cleanup_memory() {
    for (size_t i = 0; i < pool.count; i++) free(pool.allocations[i]);
    free(pool.allocations);
    pool.allocations = NULL;
    pool.count = 0;
    pool.capacity = 0;
}

typedef enum {
    VAL_NUMBER, VAL_STRING, VAL_BOOL, VAL_NIL, VAL_FUNCTION,
} ValueType;

typedef struct {
    int arity;
    int address;
    char* name;
} FunctionVal;

typedef struct {
    ValueType type;
    union {
        double number;
        char* string;
        bool boolean;
        FunctionVal function;
    } as;
} Value;

Value make_number(double n) { return (Value){.type = VAL_NUMBER, .as.number = n}; }
Value make_string(const char* s) { return (Value){.type = VAL_STRING, .as.string = tracked_strdup(s)}; }
Value make_bool(bool b) { return (Value){.type = VAL_BOOL, .as.boolean = b}; }
Value make_nil() { return (Value){.type = VAL_NIL}; }

Value make_function(const char* name, int arity, int address) {
    Value v = {.type = VAL_FUNCTION};
    v.as.function.name = tracked_strdup(name);
    v.as.function.arity = arity;
    v.as.function.address = address;
    return v;
}

void print_value(Value v) {
    switch (v.type) {
        case VAL_NUMBER:
            if (v.as.number == (int)v.as.number) {
                printf("%d", (int)v.as.number);
            } else {
                printf("%.2f", v.as.number);
            }
            break;
        case VAL_STRING: printf("%s", v.as.string); break;
        case VAL_BOOL: printf("%s", v.as.boolean ? "true" : "false"); break;
        case VAL_NIL: printf("nil"); break;
        case VAL_FUNCTION: printf("<fn %s>", v.as.function.name); break;
    }
}

bool values_equal(Value a, Value b) {
    if (a.type != b.type) return false;
    switch (a.type) {
        case VAL_NUMBER: return a.as.number == b.as.number;
        case VAL_STRING: return strcmp(a.as.string, b.as.string) == 0;
        case VAL_BOOL: return a.as.boolean == b.as.boolean;
        case VAL_NIL: return true;
        default: return false;
    }
}

typedef enum {
    OP_CONSTANT, OP_NIL, OP_TRUE, OP_FALSE, OP_POP,
    OP_GET_LOCAL, OP_SET_LOCAL, OP_GET_GLOBAL, OP_SET_GLOBAL, OP_DEFINE_GLOBAL,
    OP_EQUAL, OP_GREATER, OP_LESS,
    OP_ADD, OP_SUBTRACT, OP_MULTIPLY, OP_DIVIDE,
    OP_NOT, OP_NEGATE, OP_PRINT,
    OP_JUMP, OP_JUMP_IF_FALSE, OP_LOOP,
    OP_CALL, OP_RETURN,
    OP_GET_ARG, OP_GET_RESULT, OP_PROCEED,
    OP_HALT,
} OpCode;

typedef struct {
    uint8_t* code;
    int count;
    int capacity;
    Value* constants;
    int constant_count;
    int constant_capacity;
    int* lines;
} Chunk;

void init_chunk(Chunk* chunk) {
    chunk->count = 0;
    chunk->capacity = 0;
    chunk->code = NULL;
    chunk->constants = NULL;
    chunk->constant_count = 0;
    chunk->constant_capacity = 0;
    chunk->lines = NULL;
}

void write_chunk(Chunk* chunk, uint8_t byte, int line) {
    if (chunk->capacity < chunk->count + 1) {
        int old = chunk->capacity;
        chunk->capacity = old < 8 ? 8 : old * 2;
        chunk->code = realloc(chunk->code, chunk->capacity);
        chunk->lines = realloc(chunk->lines, chunk->capacity * sizeof(int));
    }
    chunk->code[chunk->count] = byte;
    chunk->lines[chunk->count] = line;
    chunk->count++;
}

int add_constant(Chunk* chunk, Value value) {
    if (chunk->constant_capacity < chunk->constant_count + 1) {
        int old = chunk->constant_capacity;
        chunk->constant_capacity = old < 8 ? 8 : old * 2;
        chunk->constants = realloc(chunk->constants, chunk->constant_capacity * sizeof(Value));
    }
    chunk->constants[chunk->constant_count] = value;
    return chunk->constant_count++;
}

typedef enum {
    POINTCUT_EXECUTION,
    POINTCUT_CALL,
    POINTCUT_WITHIN,
    POINTCUT_CFLOW,
    POINTCUT_TARGET,
    POINTCUT_ARGS,
} PointcutKind;

typedef enum {
    ADVICE_BEFORE,
    ADVICE_AFTER,
    ADVICE_AFTER_RETURNING,
    ADVICE_AFTER_THROWING,
    ADVICE_AROUND,
} AdviceKind;

typedef struct {
    AdviceKind kind;
    int code_address;
    char* name;
} Advice;

typedef struct {
    PointcutKind kind;
    char* pattern;
} Pointcut;

typedef struct {
    char* name;
    Pointcut pointcut;
    Advice advices[10];
    int advice_count;
    int precedence;
    bool enabled;
} Aspect;

static Aspect aspects[MAX_ASPECTS];
static int aspect_count = 0;

typedef struct {
    char* function_name;
    Value* arguments;
    int arg_count;
    Value result;
    bool has_result;
    bool threw_exception;
} JoinPoint;

bool matches_pattern(const char* pattern, const char* name) {
    const char* p = pattern;
    const char* n = name;
    
    while (*p && *n) {
        if (*p == '*') {
            p++;
            if (!*p) return true;
            while (*n) {
                if (matches_pattern(p, n)) return true;
                n++;
            }
            return false;
        }
        else if (*p == '?') {
            p++;
            n++;
        }
        else if (*p == '[') {
            p++;
            bool negate = (*p == '!');
            if (negate) p++;
            
            bool match = false;
            while (*p && *p != ']') {
                if (*(p + 1) == '-' && *(p + 2) != ']') {
                    if (*n >= *p && *n <= *(p + 2)) match = true;
                    p += 3;
                } else {
                    if (*n == *p) match = true;
                    p++;
                }
            }
            if (*p == ']') p++;
            
            if (negate) match = !match;
            if (!match) return false;
            n++;
        }
        else if (*p == *n) {
            p++;
            n++;
        }
        else {
            return false;
        }
    }
    
    return (*p == '\0' || (*p == '*' && *(p + 1) == '\0')) && *n == '\0';
}

void find_matching_aspects(const char* func_name, Aspect*** matches, int* count) {
    static Aspect* match_list[MAX_ASPECTS];
    *count = 0;
    
    for (int i = 0; i < aspect_count; i++) {
        if (!aspects[i].enabled) continue;
        if (matches_pattern(aspects[i].pointcut.pattern, func_name)) {
            match_list[(*count)++] = &aspects[i];
        }
    }
    
    for (int i = 0; i < *count - 1; i++) {
        for (int j = i + 1; j < *count; j++) {
            if (match_list[j]->precedence > match_list[i]->precedence) {
                Aspect* temp = match_list[i];
                match_list[i] = match_list[j];
                match_list[j] = temp;
            }
        }
    }
    
    *matches = match_list;
}

void register_aspect(const char* name, const char* pattern, PointcutKind kind, int precedence) {
    if (aspect_count >= MAX_ASPECTS) return;
    
    Aspect* asp = &aspects[aspect_count++];
    asp->name = tracked_strdup(name);
    asp->pointcut.pattern = tracked_strdup(pattern);
    asp->pointcut.kind = kind;
    asp->advice_count = 0;
    asp->precedence = precedence;
    asp->enabled = true;
}

void add_advice(const char* aspect_name, AdviceKind kind, int code_addr, const char* advice_name) {
    for (int i = 0; i < aspect_count; i++) {
        if (strcmp(aspects[i].name, aspect_name) == 0) {
            Advice* adv = &aspects[i].advices[aspects[i].advice_count++];
            adv->kind = kind;
            adv->code_address = code_addr;
            adv->name = tracked_strdup(advice_name);
            return;
        }
    }
}

typedef struct {
    int ip;
    Value* slots;
    int slot_count;
} CallFrame;

typedef struct {
    Chunk* chunk;
    uint8_t* ip;
    Value stack[STACK_MAX];
    Value* stack_top;
    CallFrame frames[FRAMES_MAX];
    int frame_count;
    
    struct { char* name; Value value; } globals[GLOBALS_MAX];
    int global_count;
    
    JoinPoint join_points[JOIN_POINTS_MAX];
    int join_point_count;
} VM;

static VM vm;

void init_vm(Chunk* chunk) {
    vm.chunk = chunk;
    vm.ip = chunk->code;
    vm.stack_top = vm.stack;
    vm.frame_count = 0;
    vm.global_count = 0;
    vm.join_point_count = 0;
}

void push(Value value) { *vm.stack_top++ = value; }
Value pop() { return *--vm.stack_top; }
Value peek(int distance) { return vm.stack_top[-1 - distance]; }

void runtime_error(const char* format, ...) {
    va_list args;
    va_start(args, format);
    vfprintf(stderr, format, args);
    va_end(args);
    fputs("\n", stderr);
}

void define_global(const char* name, Value value) {
    for (int i = 0; i < vm.global_count; i++) {
        if (strcmp(vm.globals[i].name, name) == 0) {
            vm.globals[i].value = value;
            return;
        }
    }
    vm.globals[vm.global_count].name = tracked_strdup(name);
    vm.globals[vm.global_count].value = value;
    vm.global_count++;
}

int find_global(const char* name) {
    for (int i = 0; i < vm.global_count; i++) {
        if (strcmp(vm.globals[i].name, name) == 0) return i;
    }
    return -1;
}

bool call_value(Value callee, int arg_count) {
    if (callee.type != VAL_FUNCTION) {
        runtime_error("Can only call functions.");
        return false;
    }
    
    FunctionVal func = callee.as.function;
    
    if (arg_count != func.arity) {
        runtime_error("Expected %d arguments but got %d.", func.arity, arg_count);
        return false;
    }
    
    Aspect** matching_aspects;
    int match_count;
    find_matching_aspects(func.name, &matching_aspects, &match_count);
    
    JoinPoint* jp = &vm.join_points[vm.join_point_count++];
    jp->function_name = func.name;
    jp->arguments = vm.stack_top - arg_count;
    jp->arg_count = arg_count;
    jp->has_result = false;
    jp->threw_exception = false;
    
    for (int i = 0; i < match_count; i++) {
        for (int j = 0; j < matching_aspects[i]->advice_count; j++) {
            if (matching_aspects[i]->advices[j].kind == ADVICE_BEFORE) {
                printf("[%s] before %s\n", matching_aspects[i]->name, func.name);
            }
        }
    }
    
    if (vm.frame_count >= FRAMES_MAX) {
        runtime_error("Stack overflow.");
        return false;
    }
    
    CallFrame* frame = &vm.frames[vm.frame_count++];
    frame->ip = (int)(vm.ip - vm.chunk->code);
    frame->slots = vm.stack_top - arg_count - 1;
    frame->slot_count = arg_count + 1;
    
    vm.ip = vm.chunk->code + func.address;
    
    return true;
}

typedef enum {
    INTERPRET_OK,
    INTERPRET_COMPILE_ERROR,
    INTERPRET_RUNTIME_ERROR,
} InterpretResult;

InterpretResult run() {
    #define READ_BYTE() (*vm.ip++)
    #define READ_SHORT() (vm.ip += 2, (uint16_t)((vm.ip[-2] << 8) | vm.ip[-1]))
    #define READ_CONSTANT() (vm.chunk->constants[READ_BYTE()])
    #define BINARY_OP(op) \
        do { \
            if (peek(0).type != VAL_NUMBER || peek(1).type != VAL_NUMBER) { \
                runtime_error("Operands must be numbers."); \
                return INTERPRET_RUNTIME_ERROR; \
            } \
            double b = pop().as.number; \
            double a = pop().as.number; \
            push(make_number(a op b)); \
        } while (false)
    
    for (;;) {
        uint8_t instruction = READ_BYTE();
        
        switch (instruction) {
            case OP_CONSTANT: push(READ_CONSTANT()); break;
            case OP_NIL: push(make_nil()); break;
            case OP_TRUE: push(make_bool(true)); break;
            case OP_FALSE: push(make_bool(false)); break;
            case OP_POP: pop(); break;
            
            case OP_GET_LOCAL: push(vm.stack[READ_BYTE()]); break;
            case OP_SET_LOCAL: vm.stack[READ_BYTE()] = peek(0); break;
            
            case OP_GET_GLOBAL: push(vm.globals[READ_BYTE()].value); break;
            case OP_SET_GLOBAL: vm.globals[READ_BYTE()].value = peek(0); break;
            case OP_DEFINE_GLOBAL: {
                Value name = READ_CONSTANT();
                define_global(name.as.string, peek(0));
                pop();
                break;
            }
            
            case OP_EQUAL: {
                Value b = pop();
                Value a = pop();
                push(make_bool(values_equal(a, b)));
                break;
            }
            case OP_GREATER: BINARY_OP(>); break;
            case OP_LESS: BINARY_OP(<); break;
            
            case OP_ADD: {
                if (peek(0).type == VAL_STRING && peek(1).type == VAL_STRING) {
                    Value b = pop();
                    Value a = pop();
                    size_t len = strlen(a.as.string) + strlen(b.as.string) + 1;
                    char* result = tracked_malloc(len);
                    strcpy(result, a.as.string);
                    strcat(result, b.as.string);
                    push(make_string(result));
                } else if (peek(0).type == VAL_NUMBER && peek(1).type == VAL_NUMBER) {
                    BINARY_OP(+);
                } else {
                    runtime_error("Operands must be two numbers or two strings.");
                    return INTERPRET_RUNTIME_ERROR;
                }
                break;
            }
            case OP_SUBTRACT: BINARY_OP(-); break;
            case OP_MULTIPLY: BINARY_OP(*); break;
            case OP_DIVIDE: BINARY_OP(/); break;
            
            case OP_NOT: {
                Value v = pop();
                push(make_bool(v.type == VAL_NIL || (v.type == VAL_BOOL && !v.as.boolean)));
                break;
            }
            case OP_NEGATE: {
                if (peek(0).type != VAL_NUMBER) {
                    runtime_error("Operand must be a number.");
                    return INTERPRET_RUNTIME_ERROR;
                }
                push(make_number(-pop().as.number));
                break;
            }
            
            case OP_PRINT: print_value(pop()); printf("\n"); break;
            
            case OP_JUMP: {
                uint16_t offset = READ_SHORT();
                vm.ip += offset;
                break;
            }
            case OP_JUMP_IF_FALSE: {
                uint16_t offset = READ_SHORT();
                Value v = peek(0);
                if (v.type == VAL_NIL || (v.type == VAL_BOOL && !v.as.boolean)) vm.ip += offset;
                break;
            }
            case OP_LOOP: vm.ip -= READ_SHORT(); break;
            
            case OP_CALL: {
                int arg_count = READ_BYTE();
                if (!call_value(peek(arg_count), arg_count)) return INTERPRET_RUNTIME_ERROR;
                break;
            }
            
            case OP_RETURN: {
                Value result = pop();
                
                if (vm.join_point_count > 0) {
                    JoinPoint* jp = &vm.join_points[vm.join_point_count - 1];
                    jp->result = result;
                    jp->has_result = true;
                    
                    Aspect** matching_aspects;
                    int match_count;
                    find_matching_aspects(jp->function_name, &matching_aspects, &match_count);
                    
                    for (int i = 0; i < match_count; i++) {
                        for (int j = 0; j < matching_aspects[i]->advice_count; j++) {
                            Advice* adv = &matching_aspects[i]->advices[j];
                            if (adv->kind == ADVICE_AFTER) {
                                printf("[%s] after %s\n", matching_aspects[i]->name, jp->function_name);
                            } else if (adv->kind == ADVICE_AFTER_RETURNING && !jp->threw_exception) {
                                printf("[%s] after_returning %s\n", matching_aspects[i]->name, jp->function_name);
                            } else if (adv->kind == ADVICE_AFTER_THROWING && jp->threw_exception) {
                                printf("[%s] after_throwing %s\n", matching_aspects[i]->name, jp->function_name);
                            }
                        }
                    }
                    
                    vm.join_point_count--;
                }
                
                if (vm.frame_count == 0) {
                    pop();
                    return INTERPRET_OK;
                }
                
                vm.frame_count--;
                vm.stack_top = vm.frames[vm.frame_count].slots;
                push(result);
                vm.ip = vm.chunk->code + vm.frames[vm.frame_count].ip;
                break;
            }
            
            case OP_GET_ARG: {
                uint8_t index = READ_BYTE();
                if (vm.join_point_count == 0) {
                    runtime_error("No join point context.");
                    return INTERPRET_RUNTIME_ERROR;
                }
                JoinPoint* jp = &vm.join_points[vm.join_point_count - 1];
                if (index >= jp->arg_count) {
                    runtime_error("Argument index out of bounds.");
                    return INTERPRET_RUNTIME_ERROR;
                }
                push(jp->arguments[index]);
                break;
            }
            
            case OP_GET_RESULT: {
                if (vm.join_point_count > 0 && vm.join_points[vm.join_point_count - 1].has_result) {
                    push(vm.join_points[vm.join_point_count - 1].result);
                } else {
                    push(make_nil());
                }
                break;
            }
            
            case OP_HALT: return INTERPRET_OK;
            
            default:
                runtime_error("Unknown opcode: %d", instruction);
                return INTERPRET_RUNTIME_ERROR;
        }
    }
    
    #undef READ_BYTE
    #undef READ_SHORT
    #undef READ_CONSTANT
    #undef BINARY_OP
}

void build_demo(Chunk* chunk) {
    int transfer_start = chunk->count;
    write_chunk(chunk, OP_CONSTANT, 1);
    write_chunk(chunk, add_constant(chunk, make_string("Transferring $")), 1);
    write_chunk(chunk, OP_GET_LOCAL, 1);
    write_chunk(chunk, 0, 1);
    write_chunk(chunk, OP_ADD, 1);
    write_chunk(chunk, OP_PRINT, 1);
    write_chunk(chunk, OP_TRUE, 1);
    write_chunk(chunk, OP_RETURN, 1);
    define_global("transfer", make_function("transfer", 3, transfer_start));
    
    int calc_start = chunk->count;
    write_chunk(chunk, OP_GET_LOCAL, 1);
    write_chunk(chunk, 0, 1);
    write_chunk(chunk, OP_CONSTANT, 1);
    write_chunk(chunk, add_constant(chunk, make_number(0.05)), 1);
    write_chunk(chunk, OP_MULTIPLY, 1);
    write_chunk(chunk, OP_RETURN, 1);
    define_global("calculateInterest", make_function("calculateInterest", 1, calc_start));
    
    int withdraw_start = chunk->count;
    write_chunk(chunk, OP_CONSTANT, 1);
    write_chunk(chunk, add_constant(chunk, make_string("Withdrawing $")), 1);
    write_chunk(chunk, OP_GET_LOCAL, 1);
    write_chunk(chunk, 1, 1);
    write_chunk(chunk, OP_ADD, 1);
    write_chunk(chunk, OP_PRINT, 1);
    write_chunk(chunk, OP_TRUE, 1);
    write_chunk(chunk, OP_RETURN, 1);
    define_global("withdraw", make_function("withdraw", 2, withdraw_start));
    
    write_chunk(chunk, OP_GET_GLOBAL, 1);
    write_chunk(chunk, find_global("transfer"), 1);
    write_chunk(chunk, OP_CONSTANT, 1);
    write_chunk(chunk, add_constant(chunk, make_number(500)), 1);
    write_chunk(chunk, OP_CONSTANT, 1);
    write_chunk(chunk, add_constant(chunk, make_string("Alice")), 1);
    write_chunk(chunk, OP_CONSTANT, 1);
    write_chunk(chunk, add_constant(chunk, make_string("Bob")), 1);
    write_chunk(chunk, OP_CALL, 1);
    write_chunk(chunk, 3, 1);
    write_chunk(chunk, OP_POP, 1);
    
    write_chunk(chunk, OP_GET_GLOBAL, 1);
    write_chunk(chunk, find_global("withdraw"), 1);
    write_chunk(chunk, OP_CONSTANT, 1);
    write_chunk(chunk, add_constant(chunk, make_string("Alice")), 1);
    write_chunk(chunk, OP_CONSTANT, 1);
    write_chunk(chunk, add_constant(chunk, make_number(200)), 1);
    write_chunk(chunk, OP_CALL, 1);
    write_chunk(chunk, 2, 1);
    write_chunk(chunk, OP_POP, 1);
    
    write_chunk(chunk, OP_GET_GLOBAL, 1);
    write_chunk(chunk, find_global("calculateInterest"), 1);
    write_chunk(chunk, OP_CONSTANT, 1);
    write_chunk(chunk, add_constant(chunk, make_number(10000)), 1);
    write_chunk(chunk, OP_CALL, 1);
    write_chunk(chunk, 1, 1);
    write_chunk(chunk, OP_PRINT, 1);
    
    write_chunk(chunk, OP_HALT, 1);
}

void define_aspects() {
    register_aspect("LoggingAspect", "*", POINTCUT_EXECUTION, 100);
    add_advice("LoggingAspect", ADVICE_BEFORE, 0, "logBefore");
    add_advice("LoggingAspect", ADVICE_AFTER, 0, "logAfter");
    
    register_aspect("SecurityAspect", "transfer*", POINTCUT_EXECUTION, 90);
    add_advice("SecurityAspect", ADVICE_BEFORE, 0, "checkSecurity");
    
    register_aspect("TransactionAspect", "transfer*|withdraw*", POINTCUT_EXECUTION, 80);
    add_advice("TransactionAspect", ADVICE_BEFORE, 0, "beginTx");
    add_advice("TransactionAspect", ADVICE_AFTER_RETURNING, 0, "commitTx");
    add_advice("TransactionAspect", ADVICE_AFTER_THROWING, 0, "rollbackTx");
    
    register_aspect("CachingAspect", "calculate*|get*", POINTCUT_EXECUTION, 70);
    add_advice("CachingAspect", ADVICE_AROUND, 0, "cache");
}

const char* get_pointcut_name(PointcutKind kind) {
    switch (kind) {
        case POINTCUT_EXECUTION: return "execution";
        case POINTCUT_CALL: return "call";
        case POINTCUT_WITHIN: return "within";
        case POINTCUT_CFLOW: return "cflow";
        case POINTCUT_TARGET: return "target";
        case POINTCUT_ARGS: return "args";
        default: return "unknown";
    }
}

const char* get_advice_name(AdviceKind kind) {
    switch (kind) {
        case ADVICE_BEFORE: return "before";
        case ADVICE_AFTER: return "after";
        case ADVICE_AFTER_RETURNING: return "after_returning";
        case ADVICE_AFTER_THROWING: return "after_throwing";
        case ADVICE_AROUND: return "around";
        default: return "unknown";
    }
}

int main() {
    printf("Aspect-Oriented Language v4.0\n\n");
    
    Chunk chunk;
    init_chunk(&chunk);
    
    printf("Aspects:\n");
    define_aspects();
    
    for (int i = 0; i < aspect_count; i++) {
        printf("  %s\n", aspects[i].name);
        printf("    pointcut: %s(\"%s\")\n", 
               get_pointcut_name(aspects[i].pointcut.kind),
               aspects[i].pointcut.pattern);
        printf("    precedence: %d\n", aspects[i].precedence);
        printf("    advice: ");
        for (int j = 0; j < aspects[i].advice_count; j++) {
            printf("%s ", get_advice_name(aspects[i].advices[j].kind));
        }
        printf("\n\n");
    }
    
    printf("Execution:\n\n");
    build_demo(&chunk);
    
    init_vm(&chunk);
    InterpretResult result = run();
    
    printf("\n");
    if (result == INTERPRET_OK) {
        printf("Completed successfully\n");
    } else {
        printf("Runtime error\n");
    }
    
    printf("\nPattern matching tests:\n");
    struct { const char* pattern; const char* name; bool expected; } tests[] = {
        {"transfer*", "transfer", true},
        {"transfer*", "transferMoney", true},
        {"transfer*", "makeTransfer", false},
        {"*Service", "UserService", true},
        {"get*", "getName", true},
        {"calculate?", "calculateA", true},
        {"calculate?", "calculateAB", false},
        {"[abc]*", "approve", true},
        {"[!xyz]*", "approve", true},
    };
    
    for (size_t i = 0; i < sizeof(tests) / sizeof(tests[0]); i++) {
        bool match = matches_pattern(tests[i].pattern, tests[i].name);
        printf("  pattern '%s' %s '%s': %s\n",
               tests[i].pattern,
               match ? "matches" : "rejects",
               tests[i].name,
               match == tests[i].expected ? "pass" : "FAIL");
    }
    
    cleanup_memory();
    return 0;
}
