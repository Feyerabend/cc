#include <stdio.h>
#include <stdbool.h>
#include <string.h>

#define MAX_STACK 1000

typedef struct {
    char stack[MAX_STACK];
    int top;
} PDA;

void init_pda(PDA *pda) {
    pda->top = -1;
}

bool is_empty(PDA *pda) {
    return pda->top == -1;
}

void push(PDA *pda, char c) {
    if (pda->top < MAX_STACK - 1) {
        pda->stack[++pda->top] = c;
    }
}

char pop(PDA *pda) {
    if (!is_empty(pda)) {
        return pda->stack[pda->top--];
    }
    return '\0';
}

char peek(PDA *pda) {
    if (!is_empty(pda)) {
        return pda->stack[pda->top];
    }
    return '\0';
}

bool check_balanced(const char *input) {
    PDA pda;
    init_pda(&pda);
    
    for (int i = 0; input[i] != '\0'; i++) {
        char c = input[i];
        
        // Opening brackets - push to stack
        if (c == '(' || c == '[' || c == '{') {
            push(&pda, c);
        }
        // Closing brackets - check matching
        else if (c == ')' || c == ']' || c == '}') {
            if (is_empty(&pda)) {
                return false; // No matching opening bracket
            }
            
            char top = pop(&pda);
            
            // Check if brackets match
            if ((c == ')' && top != '(') ||
                (c == ']' && top != '[') ||
                (c == '}' && top != '{')) {
                return false;
            }
        }
    }
    
    // Stack should be empty for balanced input
    return is_empty(&pda);
}

int main() {
    const char *tests[] = {
        "(())",
        "({[]})",
        "(()",
        "([)]",
        "{[()]}",
        "((())",
        ""
    };
    
    int num_tests = sizeof(tests) / sizeof(tests[0]);
    
    printf("Testing PDA for balanced parentheses\n");
    
    for (int i = 0; i < num_tests; i++) {
        bool result = check_balanced(tests[i]);
        printf("Input: \"%s\"\n", tests[i]);
        printf("Result: %s\n\n", result ? "ACCEPTED" : "REJECTED");
    }
    
    return 0;
}
