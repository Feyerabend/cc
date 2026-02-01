#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#define MAX_TOKENS 100
#define MAX_TOKEN_LEN 10
#define MAX_TAC 100

void generate_temp_var(char *temp_var, int temp_count) {
    sprintf(temp_var, "t%d", temp_count);
}

int tokenize(const char *expr, char tokens[MAX_TOKENS][MAX_TOKEN_LEN]) {
    int token_index = 0, i = 0, j = 0;
    while (expr[i] != '\0') {
        if (isspace(expr[i])) {
            i++;
            continue;
        }
        if (isdigit(expr[i]) || isalpha(expr[i])) {
            j = 0;
            while (isdigit(expr[i]) || isalpha(expr[i])) {
                tokens[token_index][j++] = expr[i++];
            }
            tokens[token_index++][j] = '\0';
        } else if (strchr("()+-*/", expr[i])) {
            tokens[token_index][0] = expr[i++];
            tokens[token_index++][1] = '\0';
        } else {
            fprintf(stderr, "Invalid character in expression: %c\n", expr[i]);
            exit(1);
        }
    }
    return token_index;
}

int precedence(char op) {
    if (op == '+' || op == '-') return 1;
    if (op == '*' || op == '/') return 2;
    return 0;
}

void parse_to_tac(char tokens[MAX_TOKENS][MAX_TOKEN_LEN], int token_count) {
    char tac[MAX_TAC][50];
    int temp_count = 0, tac_index = 0;
    char stack[MAX_TOKENS][MAX_TOKEN_LEN];
    int stack_top = -1;

    for (int i = 0; i < token_count; i++) {
        char *token = tokens[i];
        printf("\nProcessing token: %s\n", token);

        if (isdigit(token[0]) || isalpha(token[0])) {
            strcpy(stack[++stack_top], token);
            printf("Stack after operand '%s': ", token);
            for (int j = 0; j <= stack_top; j++) printf("%s ", stack[j]);
            printf("\n");

        } else if (token[0] == '(') {
            strcpy(stack[++stack_top], token);
            printf("Stack after '(': ");
            for (int j = 0; j <= stack_top; j++) printf("%s ", stack[j]);
            printf("\n");

        } else if (token[0] == ')') {
            printf("Processing ')', Stack before popping: ");
            for (int j = 0; j <= stack_top; j++) printf("%s ", stack[j]);
            printf("\n");

            char operands[MAX_TOKENS][MAX_TOKEN_LEN];
            int op_count = 0;
            while (stack_top >= 0 && stack[stack_top][0] != '(') {
                strcpy(operands[op_count++], stack[stack_top--]);
            }
            if (stack_top < 0 || stack[stack_top][0] != '(') {
                fprintf(stderr, "Mismatched parentheses. Stack state invalid.\n");
                exit(1);
            }
            stack_top--;

            for (int j = op_count - 1; j >= 2; j -= 2) {
                char temp_var[MAX_TOKEN_LEN];
                generate_temp_var(temp_var, temp_count++);
                sprintf(tac[tac_index++], "%s = %s %s %s", temp_var, operands[j - 2], operands[j - 1], operands[j]);
                strcpy(operands[j - 2], temp_var);
            }
            strcpy(stack[++stack_top], operands[0]);
            printf("Stack after ')': ");
            for (int j = 0; j <= stack_top; j++) printf("%s ", stack[j]);
            printf("\n");

        } else if (strchr("+-*/", token[0])) {
            printf("Processing operator: %s, Stack before checking precedence: ", token);
            for (int j = 0; j <= stack_top; j++) printf("%s ", stack[j]);
            printf("\n");

            while (stack_top >= 2 && precedence(stack[stack_top - 1][0]) >= precedence(token[0])) {
                char temp_var[MAX_TOKEN_LEN];
                generate_temp_var(temp_var, temp_count++);
                sprintf(tac[tac_index++], "%s = %s %s %s", temp_var, stack[stack_top - 2], stack[stack_top - 1], stack[stack_top]);
                stack_top -= 2;
                strcpy(stack[stack_top], temp_var);
            }
            strcpy(stack[++stack_top], token);
            printf("Stack after adding operator '%s': ", token);
            for (int j = 0; j <= stack_top; j++) printf("%s ", stack[j]);
            printf("\n");
        }
    }


    printf("\nStack before final processing: ");
    for (int i = 0; i <= stack_top; i++) printf("%s ", stack[i]);
    printf("\n");

    while (stack_top >= 2) {
        char temp_var[MAX_TOKEN_LEN];
        generate_temp_var(temp_var, temp_count++);
        sprintf(tac[tac_index++], "%s = %s %s %s", temp_var, stack[stack_top - 2], stack[stack_top - 1], stack[stack_top]);
        stack_top -= 2;
        strcpy(stack[stack_top], temp_var);
    }

    printf("\nGenerated Three-Address Code:\n");
    for (int i = 0; i < tac_index; i++) {
        printf("%s\n", tac[i]);
    }
}


int main() {
    const char *expr = "a + (b * c) / 5 - 8";
    char tokens[MAX_TOKENS][MAX_TOKEN_LEN];
    int token_count;

    printf("Input:\n%s\n", expr);

    token_count = tokenize(expr, tokens);
    printf("Tokens: ");
    for (int i = 0; i < token_count; i++) {
        printf("%s ", tokens[i]);
    }
    printf("\n");

    parse_to_tac(tokens, token_count);

    return 0;
}