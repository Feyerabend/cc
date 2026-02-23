/*
 * ps_codegen.h
 *
 * Public interface for the PostScript --> SVG code generator.
 *
 * The generator walks the AST produced by ps_parse() and emits an SVG
 * document.  It models a subset of the PostScript imaging model:
 *
 *   . Graphics state stack  (gsave / grestore --> <g> groups)
 *   . Current path          (moveto, lineto, curveto, arc, closepath)
 *   . Paint operators       (stroke, fill, rectfill)
 *   . Colour                (setgray, setrgbcolor, setcmykcolor)
 *   . Line style            (setlinewidth)
 *   . Coordinate transforms (translate, rotate, scale)
 *   . Text                  (setfont, show)
 *
 * Usage:
 *
 *   #include "ps_codegen.h"
 *
 *   Node       *ast = ps_parse(src, len);
 *   SvgCanvas  *canvas = svg_canvas_new(595.0, 842.0);   // A4 points
 *   svg_generate(canvas, ast);
 *   svg_canvas_write(canvas, stdout);
 *   svg_canvas_free(canvas);
 */

#ifndef PS_CODEGEN_H
#define PS_CODEGEN_H

#include <stdio.h>
#include <stdbool.h>

/* Forward-declare Node so callers don't need to include the full parser. */
typedef struct Node Node;


/* -- SvgCanvas
 *
 * Opaque handle representing the in-progress SVG document.
 * Allocate with svg_canvas_new(), release with svg_canvas_free().
 */
typedef struct SvgCanvas SvgCanvas;


/* svg_canvas_new - create a new canvas of the given dimensions (in pt/px). */
SvgCanvas *svg_canvas_new(double width, double height);

/* svg_canvas_free - release all memory owned by the canvas. */
void       svg_canvas_free(SvgCanvas *canvas);


/* -- Code generation
 *
 * svg_generate - walk *ast* and emit drawing commands into *canvas*.
 *
 * Returns true on success.  On failure (unknown operator, stack underflow,
 * etc.) a warning is printed to stderr and generation continues - the
 * resulting SVG may be incomplete but is always well-formed XML.
 */
bool svg_generate(SvgCanvas *canvas, const Node *ast);


/* -- Output
 *
 * svg_canvas_write - serialise the finished SVG document to *out*.
 */
void svg_canvas_write(const SvgCanvas *canvas, FILE *out);


#endif /* PS_CODEGEN_H */
