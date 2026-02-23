
## DSL Exmple: `ps2svg`

These files collectively implement a lightweight transpiler (compiler/translator).
It converts PostScript (PS) source code--a stack-based, domain-specific language
(DSL) for describing vector graphics and page layouts--into Scalable Vector Graphics
(SVG), an XML-based format for web-compatible vector images. PostScript, originally
designed by Adobe for printers (e.g., in PDF internals), is a classic DSL example,
focusing on concise, programmatic drawing commands like paths, strokes, and transforms.

The project is written in C for efficiency and portability. It supports a subset of PS
(e.g., paths, strokes/fills, colors, text, and basic transforms) but not full PS (e.g.,
no arbitrary procedures or fonts beyond basics). Here's a breakdown of the files:


- *ps_ast.h*: Defines the Abstract Syntax Tree (AST) structure. This is the intermediate
  representation of parsed PS code, with node types like integers, strings, operators
  (e.g., `moveto`, `stroke`), procedures `{...}`, arrays `[...]`, and comments.
  It's shared between parsing and code generation.

- *ps_parser.c*: The parser. It uses a packrat (PEG) parsing algorithm for efficient,
  linear-time parsing of PS source. It reads the input as a string, skips whitespace/comments,
  and builds the AST. Includes memoization to avoid recomputing sub-parses.
  (Also has a standalone main for testing.)

- *ps_codegen.h*: Header for the code generator. Declares `SvgCanvas` (an opaque handle
  for building SVG) and functions like `svg_generate()` to walk the AST and emit SVG.

- *ps_codegen.c*: The core generator. It models PS's graphics state (e.g., colors, line styles, paths)
  and transpiles AST nodes to SVG elements (e.g., PS `moveto/lineto` become `<path d="M x y L x y"/>`;
  `gsave/grestore` become nested `<g>` groups). Handles coordinate flips (PS origin is bottom-left;
  SVG is top-left). Uses a string buffer for output and supports operators like
  `setrgbcolor`, `fill`, and `show` (text).

- *ps2svg.c*: The main driver/entry point. Reads a PS file (e.g., `input.ps`), parses it to AST,
  generates SVG on a canvas (default A4 size), and writes to `input.svg` or stdout.
  Usage: `./ps2svg input.ps [output.svg]`.

To build and run (on Unix-like systems): `gcc -O2 -Wall -lm -o ps2svg *.c` then `./ps2svg example.ps`.
Limitations: Partial PS support (e.g., no images beyond basics, no full font embedding);
errors are warnings, producing partial SVG.


