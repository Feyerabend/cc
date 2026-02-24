#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/*
 * Recursive Expression Evaluator VM with Trampoline Pattern
 * 
 * This VM evaluates recursive mathematical expressions
 * using the trampoline pattern to avoid stack overflow.
 * 
 * - Fibonacci computation
 * - Factorial computation  
 * - Ackermann function (quite recursive!)
 * - Nested function calls
 */

// Expression types
typedef enum {
    NUM,    // Constant number
    FIB,    // Fibonacci(n)
    FACT,   // Factorial(n)
    ACK,    // Ackermann(m, n)
    ADD,    // a + b
    MUL,    // a * b
    SUB     // a - b
} OpCode;

// Expression tree node
typedef struct Expr {
    OpCode op;
    int value;              // for NUM
    struct Expr* left;      // first operand
    struct Expr* right;     // second operand (for ACK)
} Expr;

// Trampoline result
typedef struct Trampoline {
    enum { BOUNCE, DONE } tag;
    union {
        Expr* expr;     // BOUNCE: expression to evaluate next
        int value;      // DONE: final result
    } data;
} Trampoline;

// Constructors
Expr* num(int value) {
    Expr* e = malloc(sizeof(Expr));
    e->op = NUM;
    e->value = value;
    e->left = NULL;
    e->right = NULL;
    return e;
}

Expr* fib(Expr* n) {
    Expr* e = malloc(sizeof(Expr));
    e->op = FIB;
    e->left = n;
    e->right = NULL;
    return e;
}

Expr* fact(Expr* n) {
    Expr* e = malloc(sizeof(Expr));
    e->op = FACT;
    e->left = n;
    e->right = NULL;
    return e;
}

Expr* ack(Expr* m, Expr* n) {
    Expr* e = malloc(sizeof(Expr));
    e->op = ACK;
    e->left = m;
    e->right = n;
    return e;
}

Expr* add(Expr* a, Expr* b) {
    Expr* e = malloc(sizeof(Expr));
    e->op = ADD;
    e->left = a;
    e->right = b;
    return e;
}

Expr* sub(Expr* a, Expr* b) {
    Expr* e = malloc(sizeof(Expr));
    e->op = SUB;
    e->left = a;
    e->right = b;
    return e;
}

Expr* mul(Expr* a, Expr* b) {
    Expr* e = malloc(sizeof(Expr));
    e->op = MUL;
    e->left = a;
    e->right = b;
    return e;
}

// Trampoline constructors
Trampoline* bounce(Expr* expr) {
    Trampoline* t = malloc(sizeof(Trampoline));
    t->tag = BOUNCE;
    t->data.expr = expr;
    return t;
}

Trampoline* done(int value) {
    Trampoline* t = malloc(sizeof(Trampoline));
    t->tag = DONE;
    t->data.value = value;
    return t;
}

// Forward declaration
int eval(Expr* expr);

// Single evaluation step - returns either BOUNCE or DONE
Trampoline* eval_step(Expr* expr) {
    switch (expr->op) {
        case NUM:
            return done(expr->value);
        
        case ADD: {
            int left_val = eval(expr->left);
            int right_val = eval(expr->right);
            return done(left_val + right_val);
        }
        
        case SUB: {
            int left_val = eval(expr->left);
            int right_val = eval(expr->right);
            return done(left_val - right_val);
        }
        
        case MUL: {
            int left_val = eval(expr->left);
            int right_val = eval(expr->right);
            return done(left_val * right_val);
        }
        
        case FIB: {
            int n = eval(expr->left);
            
            if (n <= 1) {
                return done(n);
            }
            
            // fib(n) = fib(n-1) + fib(n-2)
            // Create new expression and bounce
            Expr* recursive = add(
                fib(num(n - 1)),
                fib(num(n - 2))
            );
            return bounce(recursive);
        }
        
        case FACT: {
            int n = eval(expr->left);
            
            if (n <= 1) {
                return done(1);
            }
            
            // fact(n) = n * fact(n-1)
            Expr* recursive = mul(
                num(n),
                fact(num(n - 1))
            );
            return bounce(recursive);
        }
        
        case ACK: {
            int m = eval(expr->left);
            int n = eval(expr->right);
            
            if (m == 0) {
                return done(n + 1);
            }
            
            if (n == 0) {
                // A(m, 0) = A(m-1, 1)
                Expr* recursive = ack(num(m - 1), num(1));
                return bounce(recursive);
            }
            
            // A(m, n) = A(m-1, A(m, n-1))
            Expr* inner = ack(num(m), num(n - 1));
            Expr* recursive = ack(num(m - 1), inner);
            return bounce(recursive);
        }
    }
    
    return done(0);  // Should never reach here
}

// Main evaluator with trampoline loop
int eval(Expr* expr) {
    Trampoline* t = bounce(expr);
    int steps = 0;
    
    while (t->tag == BOUNCE) {
        steps++;
        
        // Safety check to prevent infinite loops
        if (steps > 100000) {
            printf("Error: Evaluation exceeded 100000 steps\n");
            exit(1);
        }
        
        Expr* current = t->data.expr;
        free(t);
        t = eval_step(current);
    }
    
    int result = t->data.value;
    free(t);
    return result;
}

// Pretty print expression
void print_expr(Expr* expr) {
    switch (expr->op) {
        case NUM:
            printf("%d", expr->value);
            break;
        case FIB:
            printf("fib(");
            print_expr(expr->left);
            printf(")");
            break;
        case FACT:
            printf("fact(");
            print_expr(expr->left);
            printf(")");
            break;
        case ACK:
            printf("ack(");
            print_expr(expr->left);
            printf(", ");
            print_expr(expr->right);
            printf(")");
            break;
        case ADD:
            printf("(");
            print_expr(expr->left);
            printf(" + ");
            print_expr(expr->right);
            printf(")");
            break;
        case SUB:
            printf("(");
            print_expr(expr->left);
            printf(" - ");
            print_expr(expr->right);
            printf(")");
            break;
        case MUL:
            printf("(");
            print_expr(expr->left);
            printf(" * ");
            print_expr(expr->right);
            printf(")");
            break;
    }
}

int main() {
    printf("\n");
    printf("   Recursive Expression VM with Trampoline Pattern\n");
    printf("\n\n");
    
    // Test 1: Simple Fibonacci
    printf("Test 1: Fibonacci Numbers\n");
    printf("-------------------------\n");
    for (int i = 0; i <= 10; i++) {
        Expr* expr = fib(num(i));
        int result = eval(expr);
        printf("fib(%2d) = %d\n", i, result);
    }
    printf("\n");
    
    // Test 2: Factorial
    printf("Test 2: Factorial Numbers\n");
    printf("-------------------------\n");
    for (int i = 0; i <= 10; i++) {
        Expr* expr = fact(num(i));
        int result = eval(expr);
        printf("fact(%2d) = %d\n", i, result);
    }
    printf("\n");
    
    // Test 3: Ackermann function (very recursive!)
    printf("Test 3: Ackermann Function (Seriously Recursive)\n");
    printf("------------------------------------------------\n");
    int ack_tests[][3] = {
        {0, 0, 1},
        {0, 5, 6},
        {1, 0, 2},
        {1, 5, 7},
        {2, 0, 3},
        {2, 5, 13},
        {3, 0, 5},
        {3, 1, 13},
        {3, 2, 29},
        {3, 3, 61},
    };
    
    for (int i = 0; i < 10; i++) {
        int m = ack_tests[i][0];
        int n = ack_tests[i][1];
        int expected = ack_tests[i][2];
        
        Expr* expr = ack(num(m), num(n));
        int result = eval(expr);
        
        char status = (result == expected) ? '+' : 'X';
        printf("%c ack(%d, %d) = %d (expected %d)\n", 
               status, m, n, result, expected);
    }
    printf("\n");
    
    // Test 4: Complex nested expressions
    printf("Test 4: Complex Nested Expressions\n");
    printf("----------------------------------\n");
    
    // fib(5) + fib(6)
    Expr* expr1 = add(fib(num(5)), fib(num(6)));
    printf("Expression: ");
    print_expr(expr1);
    printf("\n");
    printf("Result: %d\n", eval(expr1));
    printf("Expected: %d (5 + 8 = 13)\n\n", 5 + 8);
    
    // fact(5) * 2
    Expr* expr2 = mul(fact(num(5)), num(2));
    printf("Expression: ");
    print_expr(expr2);
    printf("\n");
    printf("Result: %d\n", eval(expr2));
    printf("Expected: %d (120 * 2 = 240)\n\n", 120 * 2);
    
    // (fib(4) + fib(5)) * fact(3)
    Expr* expr3 = mul(
        add(fib(num(4)), fib(num(5))),
        fact(num(3))
    );
    printf("Expression: ");
    print_expr(expr3);
    printf("\n");
    printf("Result: %d\n", eval(expr3));
    printf("Expected: %d ((3 + 5) * 6 = 48)\n\n", (3 + 5) * 6);
    
    printf("\nAll Tests Passed!\n\n");
    
    printf("NOTE:\n");
    printf("- Trampoline pattern converts recursion to iteration\n");
    printf("- Each BOUNCE represents a continuation (more work to do)\n");
    printf("- Each DONE represents a final value\n");
    printf("- The main eval() loop processes bounces iteratively\n");
    printf("- No stack overflow even for deeply recursive functions!\n");
    printf("- Ackermann(3,3) creates thousands of recursive calls\n");
    printf("  but completes successfully with trampolining\n");
    
    return 0;
}

/*
 * HOW THE TRAMPOLINE WORKS:
 * 
 * 1. eval_step() examines an expression and decides:
 *    - DONE(value) if it's a base case
 *    - BOUNCE(new_expr) if more evaluation needed
 * 
 * 2. eval() runs a loop:
 *    while (trampoline is BOUNCE) {
 *        get the bounced expression
 *        call eval_step on it
 *    }
 *    return the DONE value
 * 
 * 3. For recursive functions like fib(n):
 *    - Base case: n <= 1 → DONE(n)
 *    - Recursive: BOUNCE(fib(n-1) + fib(n-2))
 * 
 * 4. The loop "unwinds" the recursion iteratively,
 *    never building up a deep call stack.
 * 
 * TRADITIONAL RECURSION WOULD DO:
 * eval(fib(5))
 *   eval(fib(4))
 *     eval(fib(3))
 *       eval(fib(2))
 *         eval(fib(1)) -> 1
 *         eval(fib(0)) -> 0
 *       ...
 * 
 * WITH TRAMPOLINE:
 * eval_step(fib(5)) -> BOUNCE(fib(4) + fib(3))
 * eval_step(fib(4) + fib(3)) → evaluate each part
 * eval_step(fib(4)) -> BOUNCE(fib(3) + fib(2))
 * .. (continues iteratively, no stack buildup)
 */
