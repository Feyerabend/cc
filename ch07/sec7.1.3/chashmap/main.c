#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include "hashmap.h"

void to_lower(char* str) {
    for (int i = 0; str[i]; i++) str[i] = tolower(str[i]);
}

void count_word_frequencies() {
    printf("-- Word Frequency Counter (HashMap ADT) --\n\n");
    
    const char* text = "the quick brown fox jumps over the lazy dog "
                       "the fox was quick and the dog was lazy";
    
    HashMap* freq_map = hashmap_create(16);
    
    // Tokenize and count
    char text_copy[256];
    strncpy(text_copy, text, sizeof(text_copy));
    
    char* token = strtok(text_copy, " ");
    while (token) {
        to_lower(token);
        int count = 0;
        if (hashmap_get(freq_map, token, &count)) {
            hashmap_put(freq_map, token, count + 1);
        } else {
            hashmap_put(freq_map, token, 1);
        }
        token = strtok(NULL, " ");
    }
    
    // Display results
    printf("Text: \"%s\"\n\n", text);
    printf("Word frequencies:\n");
    
    const char* words[] = {"the", "fox", "dog", "quick", "lazy", "was"};
    for (int i = 0; i < 6; i++) {
        int count;
        if (hashmap_get(freq_map, words[i], &count)) {
            printf("  %-10s : %d\n", words[i], count);
        }
    }
    
    printf("\nTotal unique words: %d\n", hashmap_size(freq_map));
    
    hashmap_destroy(freq_map);
}

int main(void) {
    count_word_frequencies();
    return 0;
}
