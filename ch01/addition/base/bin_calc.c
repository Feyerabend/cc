#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int parse_bin(const char *str) {
    if (strncmp(str, "0b", 2) != 0) return -1;
    int val = 0;
    str += 2;
    while (*str == '0' || *str == '1') {
        val = (val << 1) | (*str - '0');
        str++;
    }
    return val;
}

void print_bin(int val) {
    char buf[64];
    int i = 0;
    for (int b = 31; b >= 0; --b) {
        buf[i++] = ((val >> b) & 1) ? '1' : '0';
    }
    buf[i] = '\0';
    // Trim leading zeros
    char *start = buf;
    while (*start == '0' && *(start + 1)) start++;
    printf("= 0b%s (%d)\n", start, val);
}

int main() {
    char input[64];
    char a_str[32], b_str[32], op;
    int a, b, res;

    printf("Binary calculator (use 0b prefix, e.g., 0b1101 + 0b0011)\n");

    while (1) {
        printf("> ");
        if (!fgets(input, sizeof(input), stdin)) break;

        if (sscanf(input, "%31s %c %31s", a_str, &op, b_str) != 3) {
            printf("Invalid format. Example: 0b1010 + 0b0011\n");
            continue;
        }

        a = parse_bin(a_str);
        b = parse_bin(b_str);
        if (a < 0 || b < 0) {
            printf("Invalid binary format. Use 0b followed by 0/1.\n");
            continue;
        }

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

        print_bin(res);
    }

    return 0;
}