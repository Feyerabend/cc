// main.c
#include "css_parser.h"
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    const char *css;
    
    if (argc > 1) {
        // Read from file
        FILE *f = fopen(argv[1], "r");
        if (!f) {
            fprintf(stderr, "Error: Could not open file %s\n", argv[1]);
            return 1;
        }
        
        fseek(f, 0, SEEK_END);
        long size = ftell(f);
        fseek(f, 0, SEEK_SET);
        
        char *buffer = malloc(size + 1);
        fread(buffer, 1, size, f);
        buffer[size] = '\0';
        fclose(f);
        
        css = buffer;
    } else {
        // Use example CSS
        css = 
            "body { "
            "  background-color: white; "
            "  margin: 0px; "
            "  font-family: Arial; "
            "} "
            "/* Navigation styles */ "
            ".header { "
            "  color: blue; "
            "  font-size: 24px; "
            "  padding: 10px; "
            "} "
            ".nav { "
            "  display: flex; "
            "  background: #333; "
            "}";
    }
    
    printf("Parsing CSS...\n\n");
    
    Arena *arena = arena_create();
    Lexer *lexer = lexer_create(css, arena);
    CSSStylesheet *sheet = stylesheet_create(arena);
    
    parse_stylesheet(lexer, sheet);
    stylesheet_print(sheet);
    
    printf("Memory used: %zu bytes\n", arena->current->used);
    
    arena_free(arena);
    
    if (argc > 1) {
        free((void*)css);
    }
    
    return 0;
}
