/*
 * Aspect-Oriented Language - Main Driver
 * Supports: file execution, REPL mode, built-in examples
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

char* read_file(const char* path) {
    FILE* file = fopen(path, "rb");
    if (!file) {
        fprintf(stderr, "Could not open file: %s\n", path);
        return NULL;
    }
    
    fseek(file, 0L, SEEK_END);
    size_t file_size = ftell(file);
    rewind(file);
    
    char* buffer = malloc(file_size + 1);
    if (!buffer) {
        fprintf(stderr, "Not enough memory to read: %s\n", path);
        fclose(file);
        return NULL;
    }
    
    size_t bytes_read = fread(buffer, sizeof(char), file_size, file);
    if (bytes_read < file_size) {
        fprintf(stderr, "Could not read file: %s\n", path);
        free(buffer);
        fclose(file);
        return NULL;
    }
    
    buffer[bytes_read] = '\0';
    fclose(file);
    return buffer;
}

void run_repl() {
    printf("Aspect-Oriented Language REPL\n");
    printf("Type 'exit' or 'quit' to leave, 'help' for commands\n\n");
    
    char line[1024];
    
    while (true) {
        printf("> ");
        
        if (!fgets(line, sizeof(line), stdin)) {
            printf("\n");
            break;
        }
        
        line[strcspn(line, "\n")] = 0;
        
        if (strlen(line) == 0) {
            continue;
        }
        
        if (strcmp(line, "exit") == 0 || strcmp(line, "quit") == 0) {
            break;
        }
        
        if (strcmp(line, "help") == 0) {
            printf("Commands:\n");
            printf("  exit, quit     - Exit REPL\n");
            printf("  help           - Show this help\n");
            printf("  load <file>    - Load and execute file\n");
            printf("  example        - Run built-in example\n");
            printf("\nNote: Full REPL requires complete parser implementation\n");
            printf("Currently shows file execution mode\n");
            continue;
        }
        
        if (strncmp(line, "load ", 5) == 0) {
            char* path = line + 5;
            while (*path == ' ') path++;
            
            printf("Loading file: %s\n", path);
            char* source = read_file(path);
            if (source) {
                printf("File loaded successfully\n");
                printf("Content preview:\n");
                printf("%.200s%s\n", source, strlen(source) > 200 ? "..." : "");
                free(source);
            }
            continue;
        }
        
        if (strcmp(line, "example") == 0) {
            printf("Running built-in example...\n");
            printf("\nNote: This would execute the example if parser was integrated\n");
            continue;
        }
        
        printf("Input: %s\n", line);
        printf("Note: Full compilation requires parser integration\n");
    }
}

void show_usage(const char* program) {
    printf("Aspect-Oriented Language - Main Driver\n\n");
    printf("Usage: %s [options] [file]\n\n", program);
    printf("Options:\n");
    printf("  -h, --help     Show this help message\n");
    printf("  -v, --version  Show version information\n");
    printf("  -i, --repl     Start interactive REPL\n");
    printf("  -c, --check    Check file syntax only\n\n");
    printf("Examples:\n");
    printf("  %s                    Start REPL\n", program);
    printf("  %s script.aop         Run script file\n", program);
    printf("  %s -i                 Start REPL explicitly\n", program);
    printf("  %s -c script.aop      Check syntax\n", program);
}

void show_version() {
    printf("Aspect-Oriented Language v4.0\n\n");
    printf("Features:\n");
    printf("  Pattern matching: *, ?, [abc], [!abc], [a-z]\n");
    printf("  Pointcut types: execution, call, within, cflow\n");
    printf("  Advice types: before, after, after_returning, after_throwing, around\n");
    printf("  Aspect precedence control\n");
    printf("  Memory management with cleanup\n");
}

void check_file(const char* path) {
    printf("Checking syntax: %s\n", path);
    
    char* source = read_file(path);
    if (!source) {
        exit(74);
    }
    
    printf("\nFile structure:\n");
    
    int line_count = 1;
    int aspect_count = 0;
    int function_count = 0;
    
    char* p = source;
    while (*p) {
        if (*p == '\n') line_count++;
        
        if (strncmp(p, "aspect ", 7) == 0) {
            aspect_count++;
            char name[64];
            sscanf(p + 7, "%63s", name);
            printf("  Found aspect: %s\n", name);
        }
        
        if (strncmp(p, "function ", 9) == 0) {
            function_count++;
            char name[64];
            sscanf(p + 9, "%63[^(]", name);
            printf("  Found function: %s\n", name);
        }
        
        p++;
    }
    
    printf("\nStatistics:\n");
    printf("  Lines: %d\n", line_count);
    printf("  Aspects: %d\n", aspect_count);
    printf("  Functions: %d\n", function_count);
    
    free(source);
}

void run_file(const char* path) {
    printf("Executing file: %s\n\n", path);
    
    char* source = read_file(path);
    if (!source) {
        exit(74);
    }
    
    printf("Content:\n");
    printf("%s\n", source);
    
    printf("\nNote: Full execution requires parser integration\n");
    printf("This demonstrates file loading capability\n");
    
    free(source);
}

int main(int argc, char* argv[]) {
    if (argc == 1) {
        run_repl();
        return 0;
    }
    
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0) {
            show_usage(argv[0]);
            return 0;
        }
        
        if (strcmp(argv[i], "-v") == 0 || strcmp(argv[i], "--version") == 0) {
            show_version();
            return 0;
        }
        
        if (strcmp(argv[i], "-i") == 0 || strcmp(argv[i], "--repl") == 0) {
            run_repl();
            return 0;
        }
        
        if (strcmp(argv[i], "-c") == 0 || strcmp(argv[i], "--check") == 0) {
            if (i + 1 >= argc) {
                fprintf(stderr, "Error: -c requires a file argument\n");
                return 64;
            }
            check_file(argv[++i]);
            return 0;
        }
        
        if (argv[i][0] == '-') {
            fprintf(stderr, "Unknown option: %s\n", argv[i]);
            show_usage(argv[0]);
            return 64;
        }
        
        run_file(argv[i]);
        return 0;
    }
    
    return 0;
}
