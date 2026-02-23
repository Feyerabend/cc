/*
 * ps2svg.c
 *
 * Driver: read a PostScript file, parse it, generate SVG, write output.
 * PS Ref: https://www.adobe.com/jp/print/postscript/pdfs/PLRM.pdf
 * Build:
 *   gcc -O2 -Wall -Wextra -lm \
 *       -o ps2svg ps2svg.c ps_parser.c ps_codegen.c
 *
 * Usage:
 *   ./ps2svg input.ps              # writes input.svg
 *   ./ps2svg input.ps output.svg   # explicit output path
 *   ./ps2svg input.ps -            # write SVG to stdout
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

#include "ps_ast.h"
#include "ps_codegen.h"


/* File I/O */

static char * read_file(const char *path, int *out_length) {
    FILE *f = fopen(path, "rb");
    if (!f) { perror(path); return NULL; }

    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    rewind(f);

    char *buf = malloc(size + 1);
    size      = (long)fread(buf, 1, size, f);
    buf[size] = '\0';

    fclose(f);
    *out_length = (int)size;
    return buf;
}


/* Output path derivation */

/*
 * Given "path/to/file.ps", return "path/to/file.svg".
 * Caller must free() the result.
 */
static char * derive_svg_path(const char *ps_path) {
    size_t len = strlen(ps_path);
    char  *out = malloc(len + 5);   /* +5: room for ".svg\0" */
    memcpy(out, ps_path, len + 1);

    /* Replace trailing .ps extension, or append .svg if absent. */
    if (len >= 3 && strcmp(out + len - 3, ".ps") == 0)
        strcpy(out + len - 3, ".svg");
    else
        strcat(out, ".svg");

    return out;
}


/* Usage */

static void print_usage(const char *program) {
    fprintf(stderr,
        "Usage: %s <input.ps> [output.svg | -]\n"
        "\n"
        "  Transpile a PostScript file to SVG.\n"
        "\n"
        "  output.svg   write SVG to this file  (default: input.svg)\n"
        "  -            write SVG to stdout\n",
        program);
}



int main(int argc, char **argv) {
    if (argc < 2) {
        print_usage(argv[0]);
        return 1;
    }

    const char *input_path  = argv[1];
    const char *output_path = (argc >= 3) ? argv[2] : NULL;

    /* Read source */

    int   source_len = 0;
    char *source     = read_file(input_path, &source_len);
    if (!source) return 1;

    fprintf(stderr, "Parsing  %s  (%d bytes) ...\n", input_path, source_len);

    /* Parse */

    Node *ast = ps_parse(source, source_len);
    if (!ast) {
        fprintf(stderr, "error: parse failed.\n");
        free(source);
        return 1;
    }

    fprintf(stderr, "Parsed OK.  Generating SVG ...\n");

    /* Generate */

    /*
     * Default canvas size: A4 in PostScript points (1pt = 1/72 inch).
     * 595 × 842 pt ≈ 210 × 297 mm.
     */
    SvgCanvas *canvas = svg_canvas_new(595.0, 842.0);
    svg_generate(canvas, ast);

    /* Write output */

    FILE *out_file = NULL;
    bool  close_out = false;
    char *derived   = NULL;

    if (output_path && strcmp(output_path, "-") == 0) {
        out_file = stdout;
    } else {
        if (!output_path) {
            derived     = derive_svg_path(input_path);
            output_path = derived;
        }
        out_file  = fopen(output_path, "w");
        close_out = true;
        if (!out_file) {
            perror(output_path);
            svg_canvas_free(canvas);
            free(source);
            free(derived);
            return 1;
        }
    }

    svg_canvas_write(canvas, out_file);

    if (close_out) {
        fclose(out_file);
        fprintf(stderr, "Wrote    %s\n", output_path);
    }

    /* Cleanup */

    svg_canvas_free(canvas);
    free(source);
    free(derived);

    return 0;
}
