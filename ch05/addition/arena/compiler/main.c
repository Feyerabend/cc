#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <getopt.h>
#include <errno.h>

#include "compiler.h"


/* COMMAND LINE OPTIONS */

typedef struct {
    const char *input_file;
    const char *output_dir;
    bool emit_tokens;
    bool emit_ast;
    bool emit_symtab;
    bool emit_tac;
    bool verbose;
    bool debug;
    bool print_ast;
    bool print_tac;
} CompilerOptions;


/* USE */

static void print_usage(const char *program_name) {
    printf("Usage: %s [OPTIONS] <source-file>\n\n", program_name);
    printf("Compile a PL/0 source file to three-address code.\n\n");
    printf("Options:\n");
    printf("  -o, --output DIR       Output directory (default: current directory)\n");
    printf("  -t, --tokens           Emit tokenized output (.tokens)\n");
    printf("  -a, --ast              Emit abstract syntax tree (.ast.json)\n");
    printf("  -s, --symtab           Emit symbol table (.symtab)\n");
    printf("  -c, --tac              Emit three-address code (.tac)\n");
    printf("  -A, --all              Emit all intermediate outputs\n");
    printf("  -v, --verbose          Verbose output\n");
    printf("  -d, --debug            Enable debug mode\n");
    printf("      --print-ast        Print AST to stdout\n");
    printf("      --print-tac        Print TAC to stdout\n");
    printf("  -h, --help             Display this help message\n");
    printf("  -V, --version          Display version information\n");
    printf("\n");
    printf("Examples:\n");
    printf("  %s program.pl0                    # Compile with defaults\n", program_name);
    printf("  %s -A program.pl0                 # Emit all outputs\n", program_name);
    printf("  %s -o build -tac program.pl0      # TAC to build/ directory\n", program_name);
    printf("  %s --print-ast --print-tac prog.pl0  # Print to stdout\n", program_name);
    printf("\n");
}

static void print_version(void) {
    printf("PL/0 Compiler v2.0 (Refactored)\n");
    printf("Built with improved memory management and error handling.\n");
}


/* PATH UTILITIES */

static char *get_basename(const char *path) {
    const char *last_slash = strrchr(path, '/');
    const char *last_backslash = strrchr(path, '\\');
    const char *basename = path;
    
    if (last_slash && last_slash > basename) basename = last_slash + 1;
    if (last_backslash && last_backslash > basename) basename = last_backslash + 1;
    
    return strdup(basename);
}

static char *remove_extension(const char *filename) {
    char *result = strdup(filename);
    char *dot = strrchr(result, '.');
    if (dot && dot > result) {
        *dot = '\0';
    }
    return result;
}

static char *build_output_path(const char *output_dir, const char *basename, const char *ext) {
    size_t dir_len = strlen(output_dir);
    size_t base_len = strlen(basename);
    size_t ext_len = strlen(ext);
    
    // +2 for possible slash and null terminator
    char *path = malloc(dir_len + base_len + ext_len + 2);
    if (!path) return NULL;
    
    strcpy(path, output_dir);
    
    // Add slash if directory doesn't end with one
    if (dir_len > 0 && output_dir[dir_len - 1] != '/' && output_dir[dir_len - 1] != '\\') {
        strcat(path, "/");
    }
    
    strcat(path, basename);
    strcat(path, ext);
    
    return path;
}


/* FILE OUTPUT */

static bool write_tokens(CompilerContext *ctx, const char *filename) {
    FILE *f = fopen(filename, "w");
    if (!f) {
        fprintf(stderr, "Error: Cannot open %s for writing: %s\n", 
                filename, strerror(errno));
        return false;
    }
    
    fprintf(f, "# Token Stream\n");
    fprintf(f, "# Format: TYPE VALUE (line:column)\n\n");
    
    for (size_t i = 0; i < ctx->tokens->count; i++) {
        Token *tok = &ctx->tokens->tokens[i];
        if (tok->value) {
            fprintf(f, "%-15s %-20s (%d:%d)\n", 
                    token_type_name(tok->type), tok->value, tok->line, tok->column);
        } else {
            fprintf(f, "%-15s %-20s (%d:%d)\n", 
                    token_type_name(tok->type), "", tok->line, tok->column);
        }
    }
    
    fclose(f);
    return true;
}

static bool write_ast_json(CompilerContext *ctx, const char *filename) {
    FILE *f = fopen(filename, "w");
    if (!f) {
        fprintf(stderr, "Error: Cannot open %s for writing: %s\n", 
                filename, strerror(errno));
        return false;
    }
    
    ast_serialize_json(ctx->ast, f);
    fclose(f);
    return true;
}

static bool write_symbol_table(CompilerContext *ctx, const char *filename) {
    FILE *f = fopen(filename, "w");
    if (!f) {
        fprintf(stderr, "Error: Cannot open %s for writing: %s\n", 
                filename, strerror(errno));
        return false;
    }
    
    symbol_table_print(ctx->symtab, f);
    fclose(f);
    return true;
}

static bool write_tac(CompilerContext *ctx, const char *filename) {
    FILE *f = fopen(filename, "w");
    if (!f) {
        fprintf(stderr, "Error: Cannot open %s for writing: %s\n", 
                filename, strerror(errno));
        return false;
    }
    
    tac_print(ctx->tac, f);
    fclose(f);
    return true;
}


/* ERROR REPORTING */

static void print_error(const CompilerError *error) {
    const char *error_type;
    switch (error->code) {
        case ERR_MEMORY:      error_type = "Memory Error"; break;
        case ERR_FILE_IO:     error_type = "I/O Error"; break;
        case ERR_SYNTAX:      error_type = "Syntax Error"; break;
        case ERR_SEMANTIC:    error_type = "Semantic Error"; break;
        case ERR_UNDEFINED_SYMBOL: error_type = "Undefined Symbol"; break;
        case ERR_TYPE_MISMATCH: error_type = "Type Mismatch"; break;
        default:              error_type = "Error"; break;
    }
    
    if (error->line > 0) {
        fprintf(stderr, "%s at line %d, column %d: %s\n", 
                error_type, error->line, error->column, error->message);
    } else {
        fprintf(stderr, "%s: %s\n", error_type, error->message);
    }
}

static void print_compilation_errors(CompilerContext *ctx) {
    if (ctx->error_count == 0) return;
    
    fprintf(stderr, "\nCompilation failed with %zu error%s:\n\n", 
            ctx->error_count, ctx->error_count == 1 ? "" : "s");
    
    for (size_t i = 0; i < ctx->error_count; i++) {
        fprintf(stderr, "[%zu] ", i + 1);
        print_error(&ctx->errors[i]);
    }
    fprintf(stderr, "\n");
}


/* COMPILATION PIPELINE */

static int compile_file(const char *input_file, const CompilerOptions *opts) {
    int exit_code = EXIT_SUCCESS;
    
    // Validate input file exists
    FILE *test = fopen(input_file, "r");
    if (!test) {
        fprintf(stderr, "Error: Cannot open input file '%s': %s\n", 
                input_file, strerror(errno));
        return EXIT_FAILURE;
    }
    fclose(test);
    
    if (opts->verbose) {
        printf("Compiling: %s\n", input_file);
    }
    
    // Create compiler context
    CompilerContext *ctx = compiler_context_create();
    if (!ctx) {
        fprintf(stderr, "Error: Failed to create compiler context\n");
        return EXIT_FAILURE;
    }
    
    // Compile
    Result result = compiler_compile_file(ctx, input_file);
    
    if (result.has_error) {
        print_error(&result.error);
        print_compilation_errors(ctx);
        exit_code = EXIT_FAILURE;
        goto cleanup;
    }
    
    if (opts->verbose) {
        printf("✓ Lexical analysis complete (%zu tokens)\n", ctx->tokens->count);
        printf("✓ Parsing complete\n");
        printf("✓ Semantic analysis complete\n");
        printf("✓ Code generation complete (%d instructions)\n", 
               tac_instruction_count(ctx->tac));
    }
    
    // Print to stdout if requested
    if (opts->print_ast) {
        printf("\n=== Abstract Syntax Tree ===\n");
        ast_print_tree(ctx->ast, stdout, 0);
        printf("\n");
    }
    
    if (opts->print_tac) {
        printf("\n=== Three-Address Code ===\n");
        tac_print(ctx->tac, stdout);
        printf("\n");
    }
    
    // Generate output files
    char *base = get_basename(input_file);
    char *base_noext = remove_extension(base);
    
    if (opts->emit_tokens) {
        char *path = build_output_path(opts->output_dir, base_noext, ".tokens");
        if (opts->verbose) printf("Writing tokens to: %s\n", path);
        if (!write_tokens(ctx, path)) {
            exit_code = EXIT_FAILURE;
        }
        free(path);
    }
    
    if (opts->emit_ast) {
        char *path = build_output_path(opts->output_dir, base_noext, ".ast.json");
        if (opts->verbose) printf("Writing AST to: %s\n", path);
        if (!write_ast_json(ctx, path)) {
            exit_code = EXIT_FAILURE;
        }
        free(path);
    }
    
    if (opts->emit_symtab) {
        char *path = build_output_path(opts->output_dir, base_noext, ".symtab");
        if (opts->verbose) printf("Writing symbol table to: %s\n", path);
        if (!write_symbol_table(ctx, path)) {
            exit_code = EXIT_FAILURE;
        }
        free(path);
    }
    
    if (opts->emit_tac) {
        char *path = build_output_path(opts->output_dir, base_noext, ".tac");
        if (opts->verbose) printf("Writing TAC to: %s\n", path);
        if (!write_tac(ctx, path)) {
            exit_code = EXIT_FAILURE;
        }
        free(path);
    }
    
    if (opts->verbose && exit_code == EXIT_SUCCESS) {
        printf("\n✓ Compilation successful!\n");
    }
    
    free(base);
    free(base_noext);
    
cleanup:
    compiler_context_destroy(ctx);
    return exit_code;
}




int main(int argc, char **argv) {
    CompilerOptions opts = {
        .input_file = NULL,
        .output_dir = ".",
        .emit_tokens = false,
        .emit_ast = false,
        .emit_symtab = false,
        .emit_tac = false,
        .verbose = false,
        .debug = false,
        .print_ast = false,
        .print_tac = false
    };
    
    // Long options
    static struct option long_options[] = {
        {"output",    required_argument, 0, 'o'},
        {"tokens",    no_argument,       0, 't'},
        {"ast",       no_argument,       0, 'a'},
        {"symtab",    no_argument,       0, 's'},
        {"tac",       no_argument,       0, 'c'},
        {"all",       no_argument,       0, 'A'},
        {"verbose",   no_argument,       0, 'v'},
        {"debug",     no_argument,       0, 'd'},
        {"print-ast", no_argument,       0, 256},
        {"print-tac", no_argument,       0, 257},
        {"help",      no_argument,       0, 'h'},
        {"version",   no_argument,       0, 'V'},
        {0, 0, 0, 0}
    };
    
    // Parse command line arguments
    int option_index = 0;
    int c;
    
    while ((c = getopt_long(argc, argv, "o:tascAvdhV", long_options, &option_index)) != -1) {
        switch (c) {
            case 'o':
                opts.output_dir = optarg;
                break;
            case 't':
                opts.emit_tokens = true;
                break;
            case 'a':
                opts.emit_ast = true;
                break;
            case 's':
                opts.emit_symtab = true;
                break;
            case 'c':
                opts.emit_tac = true;
                break;
            case 'A':
                opts.emit_tokens = true;
                opts.emit_ast = true;
                opts.emit_symtab = true;
                opts.emit_tac = true;
                break;
            case 'v':
                opts.verbose = true;
                break;
            case 'd':
                opts.debug = true;
                opts.verbose = true;
                break;
            case 256:  // --print-ast
                opts.print_ast = true;
                break;
            case 257:  // --print-tac
                opts.print_tac = true;
                break;
            case 'h':
                print_usage(argv[0]);
                return EXIT_SUCCESS;
            case 'V':
                print_version();
                return EXIT_SUCCESS;
            case '?':
                // getopt_long already printed an error message
                fprintf(stderr, "Try '%s --help' for more information.\n", argv[0]);
                return EXIT_FAILURE;
            default:
                abort();
        }
    }
    
    // Get input file
    if (optind >= argc) {
        fprintf(stderr, "Error: No input file specified\n");
        fprintf(stderr, "Try '%s --help' for more information.\n", argv[0]);
        return EXIT_FAILURE;
    }
    
    opts.input_file = argv[optind];
    
    // Warn about extra arguments
    if (optind + 1 < argc) {
        fprintf(stderr, "Warning: Ignoring extra arguments:");
        for (int i = optind + 1; i < argc; i++) {
            fprintf(stderr, " %s", argv[i]);
        }
        fprintf(stderr, "\n");
    }
    
    // If no output options specified, emit TAC by default
    if (!opts.emit_tokens && !opts.emit_ast && 
        !opts.emit_symtab && !opts.emit_tac &&
        !opts.print_ast && !opts.print_tac) {
        opts.emit_tac = true;
    }
    
    // Run compilation
    return compile_file(opts.input_file, &opts);
}

