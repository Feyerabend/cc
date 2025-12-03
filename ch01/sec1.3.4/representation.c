#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/* null terminalted strings vs length-prefixed strings in C */


// null terminated strings
void print_null_terminated(const char *str) {
    printf("Null-terminated: \"");
    // Iterate until we hit '\0'
    for (int i = 0; str[i] != '\0'; i++) {
        putchar(str[i]);
    }
    printf("\"\n");
}

int null_terminated_length(const char *str) {
    int len = 0;
    while (str[len] != '\0') {
        len++;
    }
    return len;
}


// length-prefixed strings

// Structure: [length_byte][char][char][char]...
// First byte stores length, followed by string data
typedef struct {
    unsigned char *data; // Points to the full array (length + string)
} LengthPrefixedString;

LengthPrefixedString create_length_prefixed(const char *str) {
    LengthPrefixedString lps;
    size_t len = strlen(str);
    
    // Allocate: 1 byte for length + len bytes for string
    lps.data = (unsigned char *)malloc(1 + len);
    
    // Store length in first byte (max 255 characters)
    lps.data[0] = (unsigned char)len;
    
    // Copy string data starting at index 1
    for (size_t i = 0; i < len; i++) {
        lps.data[1 + i] = str[i];
    }
    
    return lps;
}

void print_length_prefixed(LengthPrefixedString lps) {
    unsigned char len = lps.data[0]; // Read length from first byte
    printf("Length-prefixed (len=%d): \"", len);
    
    // Print exactly 'len' characters, starting from index 1
    for (int i = 0; i < len; i++) {
        putchar(lps.data[1 + i]);
    }
    printf("\"\n");
}

int get_length_prefixed_length(LengthPrefixedString lps) {
    return lps.data[0]; // O(1) - just read the first byte!
}

void free_length_prefixed(LengthPrefixedString lps) {
    free(lps.data);
}


// demo

void demonstrate_memory_layout() {
    printf("\n-- Memory layouts --\n\n");
    
    const char *text = "Hello";
    
    // Null-terminated
    char null_term[6] = {'H', 'e', 'l', 'l', 'o', '\0'};
    printf("Null-terminated array:\n");
    printf("Index:  [0]  [1]  [2]  [3]  [4]  [5]\n");
    printf("Value:  ");
    for (int i = 0; i < 6; i++) {
        if (null_term[i] == '\0') {
            printf(" \\0  ");
        } else {
            printf(" '%c' ", null_term[i]);
        }
    }
    printf("\n");
    printf("Bytes:  ");
    for (int i = 0; i < 6; i++) {
        printf(" %3d ", null_term[i]);
    }
    printf("\n\n");
    
    // Length-prefixed
    LengthPrefixedString lps = create_length_prefixed(text);
    printf("Length-prefixed array:\n");
    printf("Index:  [0]  [1]  [2]  [3]  [4]  [5]\n");
    printf("Value:  ");
    printf(" %2d  ", lps.data[0]); // Length byte
    for (int i = 1; i <= 5; i++) {
        printf(" '%c' ", lps.data[i]);
    }
    printf("\n");
    printf("Bytes:  ");
    for (int i = 0; i < 6; i++) {
        printf(" %3d ", lps.data[i]);
    }
    printf("\n");
    printf("        ^--- length stored here\n");
    
    free_length_prefixed(lps);
}

void demonstrate_operations() {
    printf("\n-- Operation comparation --\n\n");
    
    const char *text = "Programming";
    
    // Null-terminated version
    char null_term_str[20];
    strcpy(null_term_str, text);
    
    printf("Null-Terminated Operations:\n");
    print_null_terminated(null_term_str);
    printf("Length calculation: O(n) - must scan until \\0\n");
    printf("Length: %d\n\n", null_terminated_length(null_term_str));
    
    // Length-prefixed version
    LengthPrefixedString lps = create_length_prefixed(text);
    
    printf("Length-Prefixed Operations:\n");
    print_length_prefixed(lps);
    printf("Length calculation: O(1) - read first byte\n");
    printf("Length: %d\n\n", get_length_prefixed_length(lps));
    
    free_length_prefixed(lps);
}

void demonstrate_advantages() {
    printf("\n-- Differences --\n\n");
    
    printf("NULL-TERMINATED (C Standard):\n");
    printf("  + Standard in C, compatible everywhere\n");
    printf("  + Works with all C string functions (strlen, strcpy, etc.)\n");
    printf("  + No length limit (except memory)\n");
    printf("  - Length requires O(n) scan\n");
    printf("  - Cannot contain null bytes in the middle\n");
    printf("  - Vulnerable to missing terminators (buffer overflows)\n\n");
    
    printf("LENGTH-PREFIXED:\n");
    printf("  + O(1) length access\n");
    printf("  + Can contain null bytes in string data\n");
    printf("  + Bounds known immediately\n");
    printf("  - Length limited by prefix size (255 with 1 byte)\n");
    printf("  - Not compatible with standard C string functions\n");
    printf("  - Requires custom functions for manipulation\n\n");
    
    printf("Used in:\n");
    printf("  * Null-terminated: C, UNIX, POSIX APIs\n");
    printf("  * Length-prefixed: Pascal strings, network protocols,\n");
    printf("    some binary formats, embedded systems\n");
}

int main() {
    printf("C stringstorage methods\n");
    printf("-----------------------\n");
    
    demonstrate_memory_layout();
    demonstrate_operations();
    demonstrate_advantages();
    
    return 0;
}
