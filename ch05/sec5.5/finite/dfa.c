#include <stdio.h>
#include <string.h>
#include <stdbool.h>

#define MAX_STATES 100
#define MAX_ALPHABET 26

// DFA Structure
typedef struct {
    int num_states;
    int alphabet_size;
    int transition[MAX_STATES][MAX_ALPHABET];
    int start_state;
    bool is_final[MAX_STATES];
} DFA;

// Init DFA
void init_dfa(DFA *dfa, int num_states, int alphabet_size, int start_state) {
    dfa->num_states = num_states;
    dfa->alphabet_size = alphabet_size;
    dfa->start_state = start_state;
    
    // Init all states as non-final
    for (int i = 0; i < num_states; i++) {
        dfa->is_final[i] = false;
    }
    
    // Init transitions to -1 (undefined)
    for (int i = 0; i < num_states; i++) {
        for (int j = 0; j < alphabet_size; j++) {
            dfa->transition[i][j] = -1;
        }
    }
}

// Add a transition
void add_transition(DFA *dfa, int from, char symbol, int to) {
    int symbol_index = symbol - 'a';
    dfa->transition[from][symbol_index] = to;
}

// Mark a state as final
void mark_final(DFA *dfa, int state) {
    dfa->is_final[state] = true;
}

// Simulate DFA on input string
bool simulate_dfa(DFA *dfa, const char *input) {
    int current_state = dfa->start_state;
    
    for (int i = 0; input[i] != '\0'; i++) {
        char symbol = input[i];
        int symbol_index = symbol - 'a';
        
        // Check if symbol is in alphabet
        if (symbol_index < 0 || symbol_index >= dfa->alphabet_size) {
            printf("Invalid symbol: %c\n", symbol);
            return false;
        }
        
        // Get next state
        int next_state = dfa->transition[current_state][symbol_index];
        
        if (next_state == -1) {
            // Undefined transition - reject
            return false;
        }
        
        printf("State %d --(%c)--> State %d\n", current_state, symbol, next_state);
        current_state = next_state;
    }
    
    // Check if final state
    return dfa->is_final[current_state];
}

// Example 1: DFA for strings ending in "ab"
DFA create_ends_with_ab() {
    DFA dfa;
    init_dfa(&dfa, 3, 2, 0);  // 3 states, 2 symbols (a,b), start at 0
    
    // State 0: Initial state
    add_transition(&dfa, 0, 'a', 1);  // Saw 'a'
    add_transition(&dfa, 0, 'b', 0);  // Stay in initial
    
    // State 1: Just saw 'a'
    add_transition(&dfa, 1, 'a', 1);  // Another 'a'
    add_transition(&dfa, 1, 'b', 2);  // Saw "ab"
    
    // State 2: Just saw "ab" (accepting)
    add_transition(&dfa, 2, 'a', 1);  // Start new pattern
    add_transition(&dfa, 2, 'b', 0);  // Reset
    
    mark_final(&dfa, 2);
    
    return dfa;
}

// Example 2: DFA for even number of a's
DFA create_even_as() {
    DFA dfa;
    init_dfa(&dfa, 2, 2, 0);  // 2 states, 2 symbols (a,b), start at 0
    
    // State 0: Even number of a's (accepting)
    add_transition(&dfa, 0, 'a', 1);  // Odd
    add_transition(&dfa, 0, 'b', 0);  // Stay even
    
    // State 1: Odd number of a's
    add_transition(&dfa, 1, 'a', 0);  // Even again
    add_transition(&dfa, 1, 'b', 1);  // Stay odd
    
    mark_final(&dfa, 0);
    
    return dfa;
}

// Example 3: DFA for binary strings divisible by 3
DFA create_divisible_by_3() {
    DFA dfa;
    init_dfa(&dfa, 3, 2, 0);  // 3 states (remainder 0,1,2)
    
    // Interpret binary string as number, track remainder mod 3
    // State represents current remainder
    
    // State 0: remainder = 0 (accepting)
    add_transition(&dfa, 0, 'a', 1);  // 0*2+0 = 0 mod 3 -> actually 'a'=0, 'b'=1
    add_transition(&dfa, 0, 'b', 1);  // 0*2+1 = 1 mod 3
    
    // State 1: remainder = 1
    add_transition(&dfa, 1, 'a', 2);  // 1*2+0 = 2 mod 3
    add_transition(&dfa, 1, 'b', 0);  // 1*2+1 = 3 mod 3 = 0
    
    // State 2: remainder = 2
    add_transition(&dfa, 2, 'a', 1);  // 2*2+0 = 4 mod 3 = 1
    add_transition(&dfa, 2, 'b', 2);  // 2*2+1 = 5 mod 3 = 2
    
    mark_final(&dfa, 0);
    
    return dfa;
}

void test_dfa(const char *name, DFA dfa, const char *test_cases[], int num_tests) {
    printf("\nTesting: %s\n", name);
    
    for (int i = 0; i < num_tests; i++) {
        printf("\nInput: \"%s\"\n", test_cases[i]);
        bool result = simulate_dfa(&dfa, test_cases[i]);
        printf("Result: %s\n", result ? "ACCEPTED" : "REJECTED");
    }
    printf("\n");
}

int main() {
    printf("DFA in C\n");
    
    // Test 1: Strings ending in "ab"
    DFA dfa1 = create_ends_with_ab();
    const char *test1[] = {"ab", "aab", "bab", "abab", "ba", "aa", "aba"};
    test_dfa("Strings ending in 'ab'", dfa1, test1, 7);
    
    // Test 2: Even number of a's
    DFA dfa2 = create_even_as();
    const char *test2[] = {"", "aa", "aaa", "aaaa", "bbb", "abab", "aba"};
    test_dfa("Even number of 'a's", dfa2, test2, 7);
    
    // Test 3: Binary divisible by 3 (using 'a'=0, 'b'=1)
    DFA dfa3 = create_divisible_by_3();
    const char *test3[] = {"a", "b", "bb", "bbb", "abb", "bab"};
    test_dfa("Binary divisible by 3 (a=0, b=1)", dfa3, test3, 6);
    
    return 0;
}
