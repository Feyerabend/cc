#include <stdio.h>
#include "stack.h"

// Real-world use case: balanced parentheses checker
int is_balanced(const char* expr) {
    Stack* s = stack_create(256);
    int balanced = 1;
    int val;

    for (int i = 0; expr[i] != '\0'; i++) {
        char c = expr[i];
        if (c == '(' || c == '[' || c == '{') {
            stack_push(s, (int)c);
        } else if (c == ')' || c == ']' || c == '}') {
            if (!stack_pop(s, &val)) { balanced = 0; break; }
            if ((c == ')' && val != '(') ||
                (c == ']' && val != '[') ||
                (c == '}' && val != '{')) {
                balanced = 0;
                break;
            }
        }
    }

    if (!stack_is_empty(s)) balanced = 0;
    stack_destroy(s);
    return balanced;
}

int main(void) {
    const char* exprs[] = {
        "({[a + b] * (c - d)})",
        "({[mismatched)}",
        "((()))",
        "((("
    };

    for (int i = 0; i < 4; i++) {
        printf("%-30s -> %s\n", exprs[i],
               is_balanced(exprs[i]) ? "BALANCED" : "UNBALANCED");
    }
    return 0;
}

