#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>

int is_valid_octal(const char *str) {
    if (*str != '0') return 0;
    str++;
    while (*str) {
        if (*str < '0' || *str > '7') return 0;
        str++;
    }
    return 1;
}

int parse_octal(const char *str) {
    return strtol(str, NULL, 8);
}

void print_result(int result) {
    printf("= %o (%d)\n", result, result);
}

int main() {
    char input[64];
    char a_str[16], b_str[16], op;
    int a, b, res;

    printf("Octal calculator (use C-style octal: e.g. 012 + 007)\n");
    printf("Supports + - * /, Ctrl+C to quit\n\n");

    while (1) {
        printf("> ");
        if (!fgets(input, sizeof(input), stdin)) break;

        if (sscanf(input, "%15s %c %15s", a_str, &op, b_str) != 3) {
            printf("Invalid format. Example: 012 + 007\n");
            continue;
        }

        if (!is_valid_octal(a_str) || !is_valid_octal(b_str)) {
            printf("Invalid octal numbers. Must start with 0 and use digits 0–7 only.\n");
            continue;
        }

        a = parse_octal(a_str);
        b = parse_octal(b_str);

        switch (op) {
            case '+': res = a + b; break;
            case '-': res = a - b; break;
            case '*': res = a * b; break;
            case '/':
                if (b == 0) {
                    printf("Division by zero.\n");
                    continue;
                }
                res = a / b;
                break;
            default:
                printf("Unsupported operator: %c\n", op);
                continue;
        }

        print_result(res);
    }

    return 0;
}
