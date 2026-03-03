#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <ctype.h>

#define MAX_TAPE 1000
#define BLANK '_'

/*
 * MINIMAL ALU TURING MACHINE
 * 
 * Operations: ADD, AND, NOT
 * 
 * Tape format:
 *   ADD|<binary_a>|<binary_b>|   -> Computes a + b
 *   AND|<binary_a>|<binary_b>|   -> Computes a & b  
 *   NOT|<binary>|                -> Computes ~binary
 * 
 * The machine processes bits from right to left,
 * marks them as used (with 'X'), and writes results
 * after the final pipe separator.
 */

typedef struct {
    char tape[MAX_TAPE];
    int head;
    int steps;
    char carry; // For ADD
    char bit_a, bit_b; // Temporary storage
    char operation[10]; // Store the operation type
} TuringMachine;

void tm_init(TuringMachine *tm, const char *input) {
    memset(tm->tape, '\0', MAX_TAPE);  // Use null termination instead of BLANK
    strncpy(tm->tape, input, strlen(input));
    tm->head = 0;
    tm->steps = 0;
    tm->carry = '0';
    tm->bit_a = '0';
    tm->bit_b = '0';
    
    // Extract operation
    int i = 0;
    while (input[i] && input[i] != '|') {
        tm->operation[i] = input[i];
        i++;
    }
    tm->operation[i] = '\0';
}

void tm_print_tape(TuringMachine *tm, int context) {
    int start = (tm->head > context) ? tm->head - context : 0;
    int end = tm->head + context;
    if (end >= MAX_TAPE) end = MAX_TAPE - 1;
    
    printf("  Tape: ");
    for (int i = start; i <= end && tm->tape[i] != BLANK; i++) {
        printf("%c", tm->tape[i]);
    }
    printf("\n  Head: ");
    for (int i = start; i < tm->head; i++) {
        printf(" ");
    }
    printf("^\n");
}

// Simulate ADD operation in a Turing-like manner
void tm_add(TuringMachine *tm, bool verbose) {
    if (verbose) printf("\n* Simulating ADD Operation *\n");
    
    // Find the operands
    int pipe1 = -1, pipe2 = -1;
    for (int i = 0; i < MAX_TAPE; i++) {
        if (tm->tape[i] == '|') {
            if (pipe1 == -1) pipe1 = i;
            else if (pipe2 == -1) { pipe2 = i; break; }
        }
    }
    
    int pos_a = pipe2 - 1; // Rightmost bit of A
    int pos_b = strlen(tm->tape) - 2; // Rightmost bit of B (before final pipe)
    int write_pos = strlen(tm->tape); // Where to write result
    
    tm->carry = '0';
    
    // Process from right to left
    while (pos_a > pipe1 || pos_b > pipe2 || tm->carry == '1') {
        tm->steps++;
        
        // Read bit from A (or use 0 if exhausted)
        char bit_a = (pos_a > pipe1 && tm->tape[pos_a] != '|') ? tm->tape[pos_a] : '0';
        
        // Read bit from B (or use 0 if exhausted)
        char bit_b = (pos_b > pipe2 && tm->tape[pos_b] != '|') ? tm->tape[pos_b] : '0';
        
        // Compute sum
        int sum = (bit_a - '0') + (bit_b - '0') + (tm->carry - '0');
        char result_bit = (sum % 2) + '0';
        tm->carry = (sum >= 2) ? '1' : '0';
        
        if (verbose) {
            printf("  Step %d: %c + %c + carry(%c) = %c (new carry: %c)\n", 
                   tm->steps, bit_a, bit_b, (tm->carry == '1') ? (char)(sum - 2 + '0') : '0',
                   result_bit, tm->carry);
        }
        
        // Write result (we'll reverse it later)
        tm->tape[write_pos++] = result_bit;
        
        pos_a--;
        pos_b--;
    }
    
    tm->tape[write_pos] = '\0';
}

// Simulate AND operation
void tm_and(TuringMachine *tm, bool verbose) {
    if (verbose) printf("\n* Simulating AND Operation *\n");
    
    int pipe1 = -1, pipe2 = -1;
    for (int i = 0; i < MAX_TAPE; i++) {
        if (tm->tape[i] == '|') {
            if (pipe1 == -1) pipe1 = i;
            else if (pipe2 == -1) { pipe2 = i; break; }
        }
    }
    
    int pos_a = pipe2 - 1;
    int pos_b = strlen(tm->tape) - 2;
    int write_pos = strlen(tm->tape);
    
    while (pos_a > pipe1 || pos_b > pipe2) {
        tm->steps++;
        
        char bit_a = (pos_a > pipe1 && tm->tape[pos_a] != '|') ? tm->tape[pos_a] : '0';
        char bit_b = (pos_b > pipe2 && tm->tape[pos_b] != '|') ? tm->tape[pos_b] : '0';
        
        char result_bit = ((bit_a == '1') && (bit_b == '1')) ? '1' : '0';
        
        if (verbose) {
            printf("  Step %d: %c AND %c = %c\n", tm->steps, bit_a, bit_b, result_bit);
        }
        
        tm->tape[write_pos++] = result_bit;
        
        pos_a--;
        pos_b--;
    }
    
    tm->tape[write_pos] = '\0';
}

// Simulate NOT operation
void tm_not(TuringMachine *tm, bool verbose) {
    if (verbose) printf("\n* Simulating NOT Operation *\n");
    
    int pipe1 = -1;
    for (int i = 0; i < MAX_TAPE; i++) {
        if (tm->tape[i] == '|') {
            if (pipe1 == -1) pipe1 = i;
            else break;
        }
    }
    
    int pos = strlen(tm->tape) - 2; // Before final pipe
    int write_pos = strlen(tm->tape);
    
    while (pos > pipe1) {
        tm->steps++;
        
        char bit = tm->tape[pos];
        if (bit == '|') {
            pos--;
            continue;
        }
        
        char result_bit = (bit == '1') ? '0' : '1';
        
        if (verbose) {
            printf("  Step %d: NOT %c = %c\n", tm->steps, bit, result_bit);
        }
        
        tm->tape[write_pos++] = result_bit;
        pos--;
    }
    
    tm->tape[write_pos] = '\0';
}

void tm_run(TuringMachine *tm, bool verbose) {
    if (strcmp(tm->operation, "ADD") == 0) {
        tm_add(tm, verbose);
    } else if (strcmp(tm->operation, "AND") == 0) {
        tm_and(tm, verbose);
    } else if (strcmp(tm->operation, "NOT") == 0) {
        tm_not(tm, verbose);
    } else {
        printf("ERROR: Unknown operation\n");
        return;
    }
    
    if (verbose) {
        printf("\n  Completed in %d steps\n", tm->steps);
    }
}

void tm_get_result(TuringMachine *tm, char *result) {
    // Find last pipe
    int last_pipe = -1;
    for (int i = 0; i < MAX_TAPE && tm->tape[i] != BLANK && tm->tape[i] != '\0'; i++) {
        if (tm->tape[i] == '|') {
            last_pipe = i;
        }
    }
    
    if (last_pipe == -1) {
        strcpy(result, "ERROR");
        return;
    }
    
    // Copy and reverse result
    int j = 0;
    for (int i = last_pipe + 1; i < MAX_TAPE && tm->tape[i] != BLANK && tm->tape[i] != '\0'; i++) {
        result[j++] = tm->tape[i];
    }
    result[j] = '\0';
    
    // Reverse
    int len = strlen(result);
    for (int i = 0; i < len / 2; i++) {
        char temp = result[i];
        result[i] = result[len - 1 - i];
        result[len - 1 - i] = temp;
    }
    
    // Remove leading zeros (but keep at least one digit)
    // DON'T remove leading zeros for NOT operation (preserve bit width)
    if (strcmp(tm->operation, "NOT") != 0) {
        char *p = result;
        while (*p == '0' && *(p+1) != '\0') p++;
        if (p != result) {
            memmove(result, p, strlen(p) + 1);
        }
    }
    
    // Handle empty result
    if (result[0] == '\0') {
        strcpy(result, "0");
    }
}

int main(int argc, char *argv[]) {
    printf("   A very minimal ALU Turing Machine\n");
    printf("   Operations: ADD, AND, NOT\n");
    
    bool verbose = false;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-v") == 0 || strcmp(argv[i], "--verbose") == 0) {
            verbose = true;
        }
    }
    
    // Test cases
    struct {
        const char *input;
        const char *description;
        const char *expected;
    } tests[] = {
        {"ADD|1011|110|", "ADD: 1011 + 110 (11 + 6)", "10001"},   // = 17
        {"ADD|1111|1|", "ADD: 1111 + 1 (15 + 1)", "10000"},       // = 16
        {"ADD|101|11|", "ADD: 101 + 11 (5 + 3)", "1000"},         // = 8
        {"ADD|1|1|", "ADD: 1 + 1", "10"},                         // = 2
        {"AND|1101|1011|", "AND: 1101 & 1011", "1001"},           // = 9
        {"AND|1111|0000|", "AND: 1111 & 0000", "0"},              // = 0
        {"AND|1010|0101|", "AND: 1010 & 0101", "0"},              // = 0
        {"AND|1111|1111|", "AND: 1111 & 1111", "1111"},           // = 15
        {"NOT|1010|", "NOT: ~1010", "0101"},
        {"NOT|0000|", "NOT: ~0000", "1111"},
        {"NOT|1111|", "NOT: ~1111", "0000"},
        {"NOT|1|", "NOT: ~1", "0"},
    };
    
    int num_tests = sizeof(tests) / sizeof(tests[0]);
    int passed = 0;
    
    for (int i = 0; i < num_tests; i++) {
        printf("> Test %d: %s\n", i + 1, tests[i].description);
        
        if (verbose) {
            printf("  Input: %s\n", tests[i].input);
        }
        
        TuringMachine tm;
        tm_init(&tm, tests[i].input);
        tm_run(&tm, verbose);
        
        char result[100];
        tm_get_result(&tm, result);
        
        bool test_passed = (strcmp(result, tests[i].expected) == 0);
        printf("  Result: %s ", result);
        
        if (test_passed) {
            printf("(+)\n");
            passed++;
        } else {
            printf("(-) (expected: %s)\n", tests[i].expected);
        }
        
        if (!verbose) {
            printf("  Steps: %d\n", tm.steps);
        }
        printf("  ----------------------------------------\n");
    }
    
    printf("\n Tests passed: %d/%d\n\n", passed, num_tests);
    printf(" Usage: %s [-v|--verbose]\n", argv[0]);
    printf("        -v, --verbose: Show step-by-step execution\n\n");
    
    return (passed == num_tests) ? 0 : 1;
}
