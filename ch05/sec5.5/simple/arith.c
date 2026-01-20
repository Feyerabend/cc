#include <stdio.h>
#include <ctype.h>
#include <string.h>
#include <stdlib.h>

// globals
const char *input;
int pos = 0;

// fwd decl.
void parse_E();
void parse_E_prime();
void parse_T();
void parse_T_prime();
void parse_F();
double parse_number();
char current_token();
void consume(char expected);
void skip_whitespace();

char current_token() {
    skip_whitespace();
    return input[pos];
}

void consume(char expected) {
    skip_whitespace();
    if (current_token() == expected) {
        pos++;
    } else {
        printf("Error: Expected '%c' but found '%c'\n", expected, current_token());
        exit(1);
    }
}

void skip_whitespace() {
    while (isspace(input[pos])) {
        pos++;
    }
}

// integers and floating-point values
double parse_number() {
    int start = pos;
    while (isdigit(current_token())) {
        pos++;
    }
    if (current_token() == '.') {
        pos++; // consume dot
        if (!isdigit(current_token())) {
            printf("Error: Malformed number at position %d\n", pos);
            exit(1);
        }
        while (isdigit(current_token())) {
            pos++;
        }
    }
    char buffer[64];
    strncpy(buffer, &input[start], pos - start);
    buffer[pos - start] = '\0'; // null-terminate
    return atof(buffer); // convert to a floating-point number
}

// recursive descent
void parse_E() {
    parse_T();
    parse_E_prime();
}

void parse_E_prime() {
    if (current_token() == '+') {
        consume('+');
        parse_T();
        parse_E_prime();
    } else if (current_token() == '-') {
        consume('-');
        parse_T();
        parse_E_prime();
    }
}

void parse_T() {
    parse_F();
    parse_T_prime();
}

void parse_T_prime() {
    if (current_token() == '*') {
        consume('*');
        parse_F();
        parse_T_prime();
    } else if (current_token() == '/') {
        consume('/');
        parse_F();
        parse_T_prime();
    }
}

void parse_F() {
    if (current_token() == '(') {
        consume('(');
        parse_E();
        consume(')');
    } else if (isdigit(current_token())) {
        double number = parse_number();
        printf("Parsed number: %f\n", number);
    } else {
        printf("Error: Unexpected token '%c'\n", current_token());
        exit(1);
    }
}

int main() {
    input = "3.14 + (2 * 4) - 5 / 1.5";
    printf("Input: %s\n", input);
    parse_E();
    if (input[pos] == '\0') {
        printf("Parsing successful!\n");
    } else {
        printf("Error: Unexpected input at position %d: '%c'\n", pos, current_token());
    }
    return 0;
}
