/**
 * TYPE SYSTEMS IN C
 * 
 * This C implementation demonstrates type system concepts at a lower level,
 * showing how types work in compiled languages and how type checking happens
 * during compilation.
 * 
 * Topics:
 * 1. Static typing in C
 * 2. Implicit type conversions (coercion)
 * 3. Type safety and undefined behavior
 * 4. Runtime type information (basic implementation)
 * 
 * Compile: gcc -Wall -Wextra -std=c11 -o type_demo type_systems.c -lm
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <math.h>

// For strdup on some systems
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif


// PART 1: TYPE SYSTEM FOUNDATIONS

/**
 * Enum representing the different type kinds we support.
 * This is our runtime type information (RTTI).
 */
typedef enum {
    TYPE_INT,
    TYPE_FLOAT,
    TYPE_BOOL,
    TYPE_CHAR,
    TYPE_STRING,
    TYPE_VOID,
    TYPE_UNKNOWN
} TypeKind;

/**
 * Get string representation of a type.
 */
const char* type_to_string(TypeKind type) {
    switch (type) {
        case TYPE_INT:     return "int";
        case TYPE_FLOAT:   return "float";
        case TYPE_BOOL:    return "bool";
        case TYPE_CHAR:    return "char";
        case TYPE_STRING:  return "string";
        case TYPE_VOID:    return "void";
        case TYPE_UNKNOWN: return "unknown";
        default:           return "error";
    }
}

/**
 * Tagged union for storing values of different types.
 * This is similar to Python's dynamic typing but implemented manually.
 */
typedef struct {
    TypeKind type;
    union {
        int int_val;
        double float_val;
        bool bool_val;
        char char_val;
        char* string_val;
    } data;
} Value;

/**
 * Create a new Value of a specific type.
 */
Value value_int(int val) {
    Value v = {.type = TYPE_INT, .data.int_val = val};
    return v;
}

Value value_float(double val) {
    Value v = {.type = TYPE_FLOAT, .data.float_val = val};
    return v;
}

Value value_bool(bool val) {
    Value v = {.type = TYPE_BOOL, .data.bool_val = val};
    return v;
}

Value value_char(char val) {
    Value v = {.type = TYPE_CHAR, .data.char_val = val};
    return v;
}

Value value_string(const char* val) {
    Value v = {.type = TYPE_STRING};
    // Manually allocate and copy for portability
    size_t len = strlen(val);
    v.data.string_val = (char*)malloc(len + 1);
    if (v.data.string_val != NULL) {
        strcpy(v.data.string_val, val);
    }
    return v;
}

/**
 * Print a Value.
 */
void value_print(const Value* v) {
    switch (v->type) {
        case TYPE_INT:
            printf("%d", v->data.int_val);
            break;
        case TYPE_FLOAT:
            printf("%f", v->data.float_val);
            break;
        case TYPE_BOOL:
            printf("%s", v->data.bool_val ? "true" : "false");
            break;
        case TYPE_CHAR:
            printf("'%c'", v->data.char_val);
            break;
        case TYPE_STRING:
            printf("\"%s\"", v->data.string_val);
            break;
        default:
            printf("<unknown>");
    }
}

/**
 * Free memory associated with a Value.
 */
void value_free(Value* v) {
    if (v->type == TYPE_STRING && v->data.string_val != NULL) {
        free(v->data.string_val);
        v->data.string_val = NULL;
    }
}


// PART 2: TYPE COERCION AND PROMOTION

/**
 * Type ranks for determining promotion order.
 * Higher rank = "wider" type.
 */
int type_rank(TypeKind type) {
    switch (type) {
        case TYPE_BOOL:   return 1;
        case TYPE_CHAR:   return 2;
        case TYPE_INT:    return 3;
        case TYPE_FLOAT:  return 4;
        default:          return 0;
    }
}

/**
 * Check if type t1 can be coerced to type t2.
 */
bool can_coerce(TypeKind t1, TypeKind t2) {
    // Same type - trivially true
    if (t1 == t2) return true;
    
    // Can only coerce to higher-ranked types
    return type_rank(t1) < type_rank(t2);
}

/**
 * Coerce a value from one type to another.
 * Returns a new Value with the target type.
 */
Value coerce_value(const Value* v, TypeKind target_type) {
    // No coercion needed
    if (v->type == target_type) {
        // Deep copy for strings
        if (v->type == TYPE_STRING) {
            return value_string(v->data.string_val);
        }
        return *v;
    }
    
    // Coercion logic
    switch (target_type) {
        case TYPE_INT:
            switch (v->type) {
                case TYPE_BOOL:  return value_int(v->data.bool_val ? 1 : 0);
                case TYPE_CHAR:  return value_int((int)v->data.char_val);
                case TYPE_FLOAT: return value_int((int)v->data.float_val);
                default: break;
            }
            break;
            
        case TYPE_FLOAT:
            switch (v->type) {
                case TYPE_BOOL:  return value_float(v->data.bool_val ? 1.0 : 0.0);
                case TYPE_CHAR:  return value_float((double)v->data.char_val);
                case TYPE_INT:   return value_float((double)v->data.int_val);
                default: break;
            }
            break;
            
        case TYPE_BOOL:
            switch (v->type) {
                case TYPE_INT:   return value_bool(v->data.int_val != 0);
                case TYPE_FLOAT: return value_bool(v->data.float_val != 0.0);
                case TYPE_CHAR:  return value_bool(v->data.char_val != '\0');
                default: break;
            }
            break;
            
        default:
            break;
    }
    
    // Coercion failed
    fprintf(stderr, "Error: Cannot coerce %s to %s\n",
            type_to_string(v->type), type_to_string(target_type));
    exit(1);
}

/**
 * Determine the common type for binary operations.
 * Uses C's standard arithmetic conversion rules.
 */
TypeKind common_type(TypeKind t1, TypeKind t2) {
    // If either is float, result is float
    if (t1 == TYPE_FLOAT || t2 == TYPE_FLOAT) {
        return TYPE_FLOAT;
    }
    
    // If either is int, result is int
    if (t1 == TYPE_INT || t2 == TYPE_INT) {
        return TYPE_INT;
    }
    
    // Both are smaller types, promote to int
    return TYPE_INT;
}


// PART 3: ARITHMETIC OPERATIONS WITH TYPE COERCION

/**
 * Add two values with automatic type coercion.
 * Demonstrates C's usual arithmetic conversions.
 */
Value value_add(const Value* left, const Value* right, bool verbose) {
    TypeKind result_type = common_type(left->type, right->type);
    
    if (verbose) {
        printf("  [Coercion] ");
        if (left->type != result_type) {
            printf("%s->%s ", type_to_string(left->type), type_to_string(result_type));
        }
        if (right->type != result_type) {
            printf("%s->%s ", type_to_string(right->type), type_to_string(result_type));
        }
        printf("for addition\n");
    }
    
    // Coerce both operands to the common type
    Value left_coerced = coerce_value(left, result_type);
    Value right_coerced = coerce_value(right, result_type);
    
    // Perform the operation
    Value result;
    switch (result_type) {
        case TYPE_INT:
            result = value_int(left_coerced.data.int_val + right_coerced.data.int_val);
            break;
        case TYPE_FLOAT:
            result = value_float(left_coerced.data.float_val + right_coerced.data.float_val);
            break;
        default:
            fprintf(stderr, "Error: Cannot add types %s and %s\n",
                    type_to_string(left->type), type_to_string(right->type));
            exit(1);
    }
    
    value_free(&left_coerced);
    value_free(&right_coerced);
    
    return result;
}

/**
 * Multiply two values with automatic type coercion.
 */
Value value_multiply(const Value* left, const Value* right, bool verbose) {
    TypeKind result_type = common_type(left->type, right->type);
    
    if (verbose) {
        printf("  [Coercion] ");
        if (left->type != result_type) {
            printf("%s->%s ", type_to_string(left->type), type_to_string(result_type));
        }
        if (right->type != result_type) {
            printf("%s->%s ", type_to_string(right->type), type_to_string(result_type));
        }
        printf("for multiplication\n");
    }
    
    Value left_coerced = coerce_value(left, result_type);
    Value right_coerced = coerce_value(right, result_type);
    
    Value result;
    switch (result_type) {
        case TYPE_INT:
            result = value_int(left_coerced.data.int_val * right_coerced.data.int_val);
            break;
        case TYPE_FLOAT:
            result = value_float(left_coerced.data.float_val * right_coerced.data.float_val);
            break;
        default:
            fprintf(stderr, "Error: Cannot multiply types %s and %s\n",
                    type_to_string(left->type), type_to_string(right->type));
            exit(1);
    }
    
    value_free(&left_coerced);
    value_free(&right_coerced);
    
    return result;
}


// PART 4: SYMBOL TABLE

#define MAX_SYMBOLS 100

typedef struct {
    char name[64];
    Value value;
    bool is_constant;
} Symbol;

typedef struct {
    Symbol symbols[MAX_SYMBOLS];
    int count;
} SymbolTable;

/**
 * Initialize a symbol table.
 */
void symtab_init(SymbolTable* table) {
    table->count = 0;
}

/**
 * Declare a new symbol.
 */
void symtab_declare(SymbolTable* table, const char* name, Value value, bool is_const) {
    if (table->count >= MAX_SYMBOLS) {
        fprintf(stderr, "Error: Symbol table full\n");
        exit(1);
    }
    
    // Check for redeclaration
    for (int i = 0; i < table->count; i++) {
        if (strcmp(table->symbols[i].name, name) == 0) {
            fprintf(stderr, "Error: Symbol '%s' already declared\n", name);
            exit(1);
        }
    }
    
    Symbol* sym = &table->symbols[table->count++];
    strncpy(sym->name, name, sizeof(sym->name) - 1);
    sym->value = value;
    sym->is_constant = is_const;
}

/**
 * Look up a symbol by name.
 */
Symbol* symtab_lookup(SymbolTable* table, const char* name) {
    for (int i = 0; i < table->count; i++) {
        if (strcmp(table->symbols[i].name, name) == 0) {
            return &table->symbols[i];
        }
    }
    return NULL;
}

/**
 * Update a symbol's value.
 */
void symtab_update(SymbolTable* table, const char* name, Value new_value) {
    Symbol* sym = symtab_lookup(table, name);
    if (!sym) {
        fprintf(stderr, "Error: Undefined symbol '%s'\n", name);
        exit(1);
    }
    
    if (sym->is_constant) {
        fprintf(stderr, "Error: Cannot modify constant '%s'\n", name);
        exit(1);
    }
    
    value_free(&sym->value);
    sym->value = new_value;
}

/**
 * Print all symbols in the table.
 */
void symtab_print(const SymbolTable* table) {
    printf("\nSymbol Table:\n");
    printf("%-15s %-10s %s\n", "Name", "Type", "Value");
    printf("--------------------------------------\n");
    
    for (int i = 0; i < table->count; i++) {
        printf("%-15s %-10s ", 
               table->symbols[i].name,
               type_to_string(table->symbols[i].value.type));
        value_print(&table->symbols[i].value);
        if (table->symbols[i].is_constant) {
            printf(" (const)");
        }
        printf("\n");
    }
}

/**
 * Free all memory in symbol table.
 */
void symtab_free(SymbolTable* table) {
    for (int i = 0; i < table->count; i++) {
        value_free(&table->symbols[i].value);
    }
    table->count = 0;
}


// DEMOS

void print_section(const char* title) {
    printf("\n");
    printf("      %s\n", title);
    printf("\n\n");
}

/**
 * Demonstrate basic type coercion in arithmetic.
 */
void demo_type_coercion() {
    print_section("TYPE COERCION IN C");
    
    printf("Demonstrating C's implicit type conversions:\n\n");
    
    // Integer arithmetic
    printf("1. Integer arithmetic:\n");
    Value x = value_int(10);
    Value y = value_int(3);
    Value result1 = value_add(&x, &y, true);
    printf("   int(10) + int(3) = ");
    value_print(&result1);
    printf(" : %s\n", type_to_string(result1.type));
    value_free(&result1);
    
    // Mixed int and float
    printf("\n2. Mixed integer and float:\n");
    Value z = value_float(3.14);
    Value result2 = value_add(&x, &z, true);
    printf("   int(10) + float(3.14) = ");
    value_print(&result2);
    printf(" : %s\n", type_to_string(result2.type));
    value_free(&result2);
    
    // Character promotion
    printf("\n3. Character to integer promotion:\n");
    Value c = value_char('A');
    Value result3 = value_add(&c, &y, true);
    printf("   char('A') + int(3) = ");
    value_print(&result3);
    printf(" : %s (ASCII: %d)\n", 
           type_to_string(result3.type), result3.data.int_val);
    value_free(&result3);
    
    // Boolean to int
    printf("\n4. Boolean to integer coercion:\n");
    Value b = value_bool(true);
    Value result4 = value_add(&b, &x, true);
    printf("   bool(true) + int(10) = ");
    value_print(&result4);
    printf(" : %s\n", type_to_string(result4.type));
    value_free(&result4);
    
    value_free(&x);
    value_free(&y);
    value_free(&z);
    value_free(&c);
    value_free(&b);
}

/**
 * Demonstrate type safety and checking.
 */
void demo_type_safety() {
    print_section("TYPE SAFETY");
    
    printf("C provides static type checking at compile time.\n");
    printf("Here we simulate runtime type checking:\n\n");
    
    SymbolTable table;
    symtab_init(&table);
    
    // Declare variables
    printf("Declaring variables:\n");
    symtab_declare(&table, "x", value_int(42), false);
    printf("  int x = 42\n");
    
    symtab_declare(&table, "pi", value_float(3.14159), true);
    printf("  const float pi = 3.14159\n");
    
    symtab_declare(&table, "message", value_string("Hello"), false);
    printf("  string message = \"Hello\"\n");
    
    // Try to modify constant (will fail)
    printf("\nTrying to modify constant 'pi':\n");
    printf("  This will produce an error:\n");
    // Uncomment to see error:
    // symtab_update(&table, "pi", value_float(3.0));
    printf("  (Error: Cannot modify constant 'pi')\n");
    
    // Valid modification
    printf("\nModifying non-constant variable 'x':\n");
    symtab_update(&table, "x", value_int(100));
    printf("  x = 100 (OK)\n");
    
    symtab_print(&table);
    symtab_free(&table);
}

/**
 * Demonstrate how C handles different type combinations.
 */
void demo_type_combinations() {
    print_section("TYPE COMBINATIONS AND PROMOTIONS");
    
    printf("Showing how different type combinations are handled:\n\n");
    
    SymbolTable table;
    symtab_init(&table);
    
    // Create test values
    Value v_bool = value_bool(true);
    Value v_char = value_char('X');
    Value v_int = value_int(42);
    Value v_float = value_float(2.5);
    
    symtab_declare(&table, "b", v_bool, false);
    symtab_declare(&table, "c", v_char, false);
    symtab_declare(&table, "i", v_int, false);
    symtab_declare(&table, "f", v_float, false);
    
    printf("Variables:\n");
    printf("  bool b = true\n");
    printf("  char c = 'X'\n");
    printf("  int i = 42\n");
    printf("  float f = 2.5\n\n");
    
    // Perform various operations
    printf("Operations:\n\n");
    
    printf("1. bool + int:\n");
    Value r1 = value_add(&v_bool, &v_int, true);
    printf("   b + i = ");
    value_print(&r1);
    printf(" : %s\n\n", type_to_string(r1.type));
    
    printf("2. char * int:\n");
    Value r2 = value_multiply(&v_char, &v_int, true);
    printf("   c * i = ");
    value_print(&r2);
    printf(" : %s\n\n", type_to_string(r2.type));
    
    printf("3. int + float:\n");
    Value r3 = value_add(&v_int, &v_float, true);
    printf("   i + f = ");
    value_print(&r3);
    printf(" : %s\n\n", type_to_string(r3.type));
    
    printf("4. (bool + char) * float:\n");
    Value temp = value_add(&v_bool, &v_char, true);
    Value r4 = value_multiply(&temp, &v_float, true);
    printf("   (b + c) * f = ");
    value_print(&r4);
    printf(" : %s\n\n", type_to_string(r4.type));
    
    // Cleanup
    value_free(&r1);
    value_free(&r2);
    value_free(&r3);
    value_free(&temp);
    value_free(&r4);
    symtab_free(&table);
}

/**
 * Compare C's static typing with dynamic behavior simulation.
 */
void demo_static_vs_dynamic() {
    print_section("STATIC VS DYNAMIC TYPING");
    
    printf("C is statically typed - types are fixed at compile time.\n");
    printf("Here's a comparison:\n\n");
    
    printf("Static typing (C's normal behavior):\n");
    printf("  int x = 10;        // x is int forever\n");
    printf("  x = 20;            // OK: still int\n");
    printf("  x = 3.14;          // Compile error or implicit conversion\n\n");
    
    printf("Dynamic typing (simulated with tagged unions):\n");
    SymbolTable table;
    symtab_init(&table);
    
    Value v1 = value_int(10);
    symtab_declare(&table, "x", v1, false);
    printf("  x = 10             // x is int\n");
    
    symtab_update(&table, "x", value_float(3.14));
    printf("  x = 3.14           // x is now float (allowed in dynamic)\n");
    
    symtab_update(&table, "x", value_string("hello"));
    printf("  x = \"hello\"        // x is now string (allowed in dynamic)\n");
    
    symtab_print(&table);
    
    printf("\nKey differences:\n");
    printf("  _ Static: Type checking at compile time, no runtime overhead\n");
    printf("  _ Dynamic: Type checking at runtime, more flexible but slower\n");
    printf("  _ Static: Cannot change variable type after declaration\n");
    printf("  _ Dynamic: Variables can hold any type at any time\n");
    
    symtab_free(&table);
}

/**
 * Demonstrate undefined behavior from type misuse.
 */
void demo_undefined_behavior() {
    print_section("TYPE SAFETY AND UNDEFINED BEHAVIOR");
    
    printf("Without proper type checking, C can exhibit undefined behavior.\n");
    printf("Our Value system prevents many of these issues:\n\n");
    
    printf("Safe version (with type checking):\n");
    Value x = value_int(42);
    printf("  Value x = int(42)\n");
    printf("  Accessing as int: %d ✓\n", x.data.int_val);
    printf("  Type is tracked: %s ✓\n\n", type_to_string(x.type));
    
    printf("Unsafe version (raw C without checks):\n");
    printf("  int x = 42;\n");
    printf("  float* p = (float*)&x;  // Type pun\n");
    printf("  *p;  // Undefined behavior! ✗\n\n");
    
    printf("Our tagged union approach provides:\n");
    printf("    Runtime type information\n");
    printf("    Type safety checks\n");
    printf("    Prevention of type confusion\n");
    printf("    Explicit coercion rules\n");
    
    value_free(&x);
}




int main(void) {
    printf("\n");
    printf("    TYPE SYSTEMS IN C\n\n");
    printf("    Demonstrating type system\n");
    printf("    concepts at the systems level:\n");
    printf("     _ Static typing\n");
    printf("     _ Type coercion and promotion\n");
    printf("     _ Type safety\n");
    printf("     _ Tagged unions for dynamic behaviour\n");
    printf("\n\n");
    
    demo_type_coercion();
    demo_type_safety();
    demo_type_combinations();
    demo_static_vs_dynamic();
    demo_undefined_behavior();
    
    return 0;
}
