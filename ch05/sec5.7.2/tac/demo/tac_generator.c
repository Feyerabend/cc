/*
 * Three-Address Code (TAC) Generator in C
 * ========================================
 *
 * This program converts arithmetic expressions into Three-Address Code (TAC),
 * an intermediate representation used in compilers.
 *
 * Key Features:
 * - Tokenization of input expressions
 * - Handling of operator precedence
 * - Support for parentheses
 * - Stack-based parsing algorithm
 * - Detailed debugging output
 *
 * Author: Educational Implementation
 * Purpose: Demonstrate TAC generation from infix expressions
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdbool.h>

/* Configuration Constants */
#define MAX_TOKENS 100
#define MAX_TOKEN_LEN 20
#define MAX_TAC 100
#define MAX_EXPR_LEN 200

/* Global flags */
bool verbose = true;

/* Structure to hold a TAC instruction */
typedef struct {
    char instruction[100];
} TACInstruction;

/* Structure for the TAC generator state */
typedef struct {
    TACInstruction tac[MAX_TAC];
    int tac_count;
    int temp_count;
} TACGenerator;

/*
 * Initialize the TAC generator
 */
void init_generator(TACGenerator *gen) {
    gen->tac_count = 0;
    gen->temp_count = 0;
}

/*
 * Generate a unique temporary variable name
 * 
 * Parameters:
 *   temp_var - output buffer for the temporary variable name
 *   temp_count - counter for temporary variables
 */
void generate_temp_var(char *temp_var, int temp_count) {
    sprintf(temp_var, "t%d", temp_count);
}

/*
 * Determine operator precedence
 * 
 * Parameters:
 *   op - operator character
 * 
 * Returns:
 *   precedence level (higher number = higher precedence)
 */
int precedence(char op) {
    switch (op) {
        case '+':
        case '-':
            return 1;
        case '*':
        case '/':
            return 2;
        default:
            return 0;
    }
}

/*
 * Check if a character is an operator
 */
bool is_operator(char c) {
    return (c == '+' || c == '-' || c == '*' || c == '/');
}

/*
 * Print a separator line
 */
void print_separator(char c, int length) {
    for (int i = 0; i < length; i++) {
        putchar(c);
    }
    putchar('\n');
}

/*
 * Print the current stack state (for debugging)
 */
void print_stack(char stack[MAX_TOKENS][MAX_TOKEN_LEN], int stack_top) {
    printf("  Stack: [");
    for (int i = 0; i <= stack_top; i++) {
        printf("%s", stack[i]);
        if (i < stack_top) printf(", ");
    }
    printf("]\n");
}

/*
 * Tokenize the input expression
 * 
 * Parameters:
 *   expr - input expression string
 *   tokens - output array of tokens
 * 
 * Returns:
 *   number of tokens found
 */
int tokenize(const char *expr, char tokens[MAX_TOKENS][MAX_TOKEN_LEN]) {
    int token_index = 0;
    int i = 0;
    int j;
    
    if (verbose) {
        printf("\nTokenizing: '%s'\n", expr);
    }
    
    while (expr[i] != '\0') {
        /* Skip whitespace */
        if (isspace(expr[i])) {
            i++;
            continue;
        }
        
        /* Handle numbers and variable names */
        if (isdigit(expr[i]) || isalpha(expr[i]) || expr[i] == '_') {
            j = 0;
            while ((isdigit(expr[i]) || isalpha(expr[i]) || expr[i] == '_') && 
                   j < MAX_TOKEN_LEN - 1) {
                tokens[token_index][j++] = expr[i++];
            }
            tokens[token_index][j] = '\0';
            token_index++;
        }
        /* Handle operators and parentheses */
        else if (strchr("()+-*/", expr[i])) {
            tokens[token_index][0] = expr[i++];
            tokens[token_index][1] = '\0';
            token_index++;
        }
        /* Invalid character */
        else {
            fprintf(stderr, "Error: Invalid character in expression: '%c'\n", expr[i]);
            exit(EXIT_FAILURE);
        }
    }
    
    if (verbose) {
        printf("Tokens: ");
        for (int k = 0; k < token_index; k++) {
            printf("%s ", tokens[k]);
        }
        printf("\n");
    }
    
    return token_index;
}

/*
 * Generate TAC from tokenized expression
 * 
 * This function implements a stack-based algorithm to convert
 * infix expressions to Three-Address Code, respecting operator
 * precedence and parentheses.
 * 
 * Parameters:
 *   tokens - array of tokens
 *   token_count - number of tokens
 *   gen - TAC generator state
 */
void parse_to_tac(char tokens[MAX_TOKENS][MAX_TOKEN_LEN], 
                  int token_count, 
                  TACGenerator *gen) {
    
    char stack[MAX_TOKENS][MAX_TOKEN_LEN];
    int stack_top = -1;
    int step = 0;
    
    if (verbose) {
        print_separator('=', 60);
        printf("PARSING TOKENS TO TAC\n");
        print_separator('=', 60);
    }
    
    for (int i = 0; i < token_count; i++) {
        char *token = tokens[i];
        step++;
        
        if (verbose) {
            printf("\n[Step %d] Processing token: '%s'\n", step, token);
        }
        
        /* Handle operands (numbers and variables) */
        if (isdigit(token[0]) || isalpha(token[0])) {
            strcpy(stack[++stack_top], token);
            if (verbose) {
                printf("  Action: Pushed operand to stack\n");
                print_stack(stack, stack_top);
            }
        }
        
        /* Handle left parenthesis */
        else if (token[0] == '(') {
            strcpy(stack[++stack_top], token);
            if (verbose) {
                printf("  Action: Pushed '(' to stack\n");
                print_stack(stack, stack_top);
            }
        }
        
        /* Handle right parenthesis */
        else if (token[0] == ')') {
            if (verbose) {
                printf("  Action: Processing expression in parentheses\n");
                printf("  Stack before: ");
                print_stack(stack, stack_top);
            }
            
            /* Collect operands until we find '(' */
            char operands[MAX_TOKENS][MAX_TOKEN_LEN];
            int op_count = 0;
            
            while (stack_top >= 0 && stack[stack_top][0] != '(') {
                strcpy(operands[op_count++], stack[stack_top--]);
            }
            
            if (stack_top < 0 || stack[stack_top][0] != '(') {
                fprintf(stderr, "Error: Mismatched parentheses\n");
                exit(EXIT_FAILURE);
            }
            
            stack_top--;  /* Remove '(' */
            
            /* Process operands (they're in reverse order) */
            for (int j = op_count - 1; j >= 2; j -= 2) {
                char temp_var[MAX_TOKEN_LEN];
                generate_temp_var(temp_var, gen->temp_count++);
                
                sprintf(gen->tac[gen->tac_count].instruction,
                        "%s = %s %s %s",
                        temp_var, operands[j-2], operands[j-1], operands[j]);
                
                if (verbose) {
                    printf("  Generated: %s\n", gen->tac[gen->tac_count].instruction);
                }
                
                gen->tac_count++;
                strcpy(operands[j-2], temp_var);
            }
            
            /* Push result back to stack */
            strcpy(stack[++stack_top], operands[0]);
            
            if (verbose) {
                printf("  Stack after: ");
                print_stack(stack, stack_top);
            }
        }
        
        /* Handle operators */
        else if (is_operator(token[0])) {
            if (verbose) {
                printf("  Action: Processing operator '%s'\n", token);
                printf("  Stack before: ");
                print_stack(stack, stack_top);
            }
            
            /* Pop operators with higher or equal precedence */
            while (stack_top >= 2 && 
                   is_operator(stack[stack_top-1][0]) &&
                   precedence(stack[stack_top-1][0]) >= precedence(token[0])) {
                
                char temp_var[MAX_TOKEN_LEN];
                generate_temp_var(temp_var, gen->temp_count++);
                
                sprintf(gen->tac[gen->tac_count].instruction,
                        "%s = %s %s %s",
                        temp_var, stack[stack_top-2], stack[stack_top-1], stack[stack_top]);
                
                if (verbose) {
                    printf("  Generated: %s\n", gen->tac[gen->tac_count].instruction);
                }
                
                gen->tac_count++;
                stack_top -= 2;
                strcpy(stack[stack_top], temp_var);
                
                if (verbose) {
                    printf("  Stack now: ");
                    print_stack(stack, stack_top);
                }
            }
            
            strcpy(stack[++stack_top], token);
            
            if (verbose) {
                printf("  Pushed operator to stack\n");
                printf("  Stack after: ");
                print_stack(stack, stack_top);
            }
        }
    }
    
    /* Process remaining items on stack */
    if (verbose) {
        printf("\n[Final] Processing remaining stack\n");
        print_stack(stack, stack_top);
    }
    
    while (stack_top >= 2) {
        char temp_var[MAX_TOKEN_LEN];
        generate_temp_var(temp_var, gen->temp_count++);
        
        sprintf(gen->tac[gen->tac_count].instruction,
                "%s = %s %s %s",
                temp_var, stack[stack_top-2], stack[stack_top-1], stack[stack_top]);
        
        if (verbose) {
            printf("  Generated: %s\n", gen->tac[gen->tac_count].instruction);
        }
        
        gen->tac_count++;
        stack_top -= 2;
        strcpy(stack[stack_top], temp_var);
    }
}

/*
 * Print the generated TAC instructions
 */
void print_tac(TACGenerator *gen) {
    printf("\n");
    print_separator('=', 60);
    printf("GENERATED THREE-ADDRESS CODE\n");
    print_separator('=', 60);
    
    for (int i = 0; i < gen->tac_count; i++) {
        printf("%d. %s\n", i+1, gen->tac[i].instruction);
    }
    
    print_separator('=', 60);
}

/*
 * Demonstrate TAC generation with an example
 */
void demonstrate_example(const char *expr) {
    printf("\n\n");
    print_separator('#', 60);
    printf("# EXAMPLE: %s\n", expr);
    print_separator('#', 60);
    
    char tokens[MAX_TOKENS][MAX_TOKEN_LEN];
    TACGenerator gen;
    
    init_generator(&gen);
    int token_count = tokenize(expr, tokens);
    parse_to_tac(tokens, token_count, &gen);
    print_tac(&gen);
}

/*
 * Main function
 */
int main(void) {
    print_separator('=', 60);
    printf("THREE-ADDRESS CODE GENERATOR (C Implementation)\n");
    print_separator('=', 60);
    printf("\nThis program converts arithmetic expressions to TAC.\n\n");
    
    /* Array of example expressions */
    const char *examples[] = {
        "a + (b * c) / 5 - 8",
        "x + y * z",
        "(a + b) * (c - d)",
        "a * b + c * d",
        "((a + b) * c) - d"
    };
    int num_examples = sizeof(examples) / sizeof(examples[0]);
    
    /* Run demonstrations */
    for (int i = 0; i < num_examples; i++) {
        demonstrate_example(examples[i]);
        
        if (i < num_examples - 1) {
            printf("\nPress Enter to continue to next example...\n");
            getchar();
        }
    }
    
    printf("\n\nAll examples completed!\n");
    
    return EXIT_SUCCESS;
}
