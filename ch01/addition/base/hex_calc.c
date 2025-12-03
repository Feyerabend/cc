#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main() {
    char input[64];
    char a_str[16], b_str[16], op;
    int a, b, res;

    printf("Hexadecimal calculator (use 0x prefix, e.g., 0x1A + 0x0F)\n");

    while (1) {
        printf("> ");
        if (!fgets(input, sizeof(input), stdin)) break;

        if (sscanf(input, "%15s %c %15s", a_str, &op, b_str) != 3) {
            printf("Invalid format. Example: 0x1A + 0x0F\n");
            continue;
        }

        a = strtol(a_str, NULL, 0);
        b = strtol(b_str, NULL, 0);

        switch (op) {
            case '+': res = a + b; break;
            case '-': res = a - b; break;
            case '*': res = a * b; break;
            case '/':
                if (b == 0) { printf("Division by zero.\n"); continue; }
                res = a / b; break;
            default:
                printf("Unsupported operator: %c\n", op); continue;
        }

        printf("= 0x%X (%d)\n", res, res);
    }

    return 0;
}