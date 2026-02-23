/*
 * ps_codegen.c
 *
 * PostScript --> SVG code generator.
 *
 * -- Imaging model mapping 
 *
 *   PostScript concept          SVG equivalent
 *   --------------------------- ------------------------------------
 *   gsave / grestore               <g style="..."> ... </g>
 *   newpath / moveto / ...         <path d="M x y L x y C ... Z" />
 *   stroke / fill / eofill         stroke="..." / fill="..." attributes
 *   setlinewidth                   stroke-width="..."
 *   setlinecap                     stroke-linecap="butt|round|square"
 *   setlinejoin                    stroke-linejoin="miter|round|bevel"
 *   setdash                        stroke-dasharray="..."
 *   setmiterlimit                  stroke-miterlimit="..."
 *   setgray / setrgbcolor / ...    rgb(r,g,b) colour strings
 *   translate / rotate / scale     <g transform="translate(...)"> ...
 *   setfont + show                 <text font-family="..." ...>...</text>
 *   showpage                       (no-op - SVG has no pages)
 *
 * -- Coordinate system --
 *
 *   PostScript: origin bottom-left, y increases upward.
 *   SVG:        origin top-left,    y increases downward.
 *
 * A single top-level transform on the root group handles this globally:
 *
 *   <g transform="scale(1,-1) translate(0,-HEIGHT)">
 *
 * All generated coordinates are emitted verbatim - no per-point arithmetic.
 *
 * -- Graphics state stack --
 *
 * Each gsave opens a <g> element whose style attributes (colour, line width,
 * dash, font) are inherited by children - idiomatic, minimal SVG.
 *
 * translate / rotate / scale each open their own inner <g transform="...">.
 * The count of these inner groups is tracked per GS level so grestore knows
 * how many to close before closing the main gsave <g>.
 *
 * -- Build --
 *
 *   See Makefile.  The canonical build command is:
 *
 *     make          - builds ./ps2svg
 *     make check    - builds and runs the test suite
 */

#define _GNU_SOURCE
#include "ps_codegen.h"
#include "ps_ast.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdbool.h>
#include <stdarg.h>
#include <ctype.h>
#ifndef M_PI
#  define M_PI 3.14159265358979323846
#endif


/*
 * 1  Dynamic string buffer
 */

typedef struct {
    char  *data;
    size_t length;
    size_t capacity;
} StrBuf;


static StrBuf * strbuf_new(void) {
    StrBuf *b   = malloc(sizeof(StrBuf));
    b->capacity = 4096;
    b->length   = 0;
    b->data     = malloc(b->capacity);
    b->data[0]  = '\0';
    return b;
}


static void strbuf_free(StrBuf *b) {
    free(b->data);
    free(b);
}


static void strbuf_ensure(StrBuf *b, size_t extra) {
    while (b->length + extra + 1 > b->capacity)
        b->capacity *= 2;
    b->data = realloc(b->data, b->capacity);
}


static void strbuf_append(StrBuf *b, const char *str) {
    size_t len = strlen(str);
    strbuf_ensure(b, len);
    memcpy(b->data + b->length, str, len + 1);
    b->length += len;
}


static void strbuf_appendf(StrBuf *b, const char *fmt, ...) {
    /* Try with a stack buffer first; fall back to heap for long strings. */
    char stack_buf[256];
    va_list ap;

    va_start(ap, fmt);
    int n = vsnprintf(stack_buf, sizeof(stack_buf), fmt, ap);
    va_end(ap);

    if (n < (int)sizeof(stack_buf)) {
        strbuf_append(b, stack_buf);
    } else {
        char *heap_buf = malloc(n + 1);
        va_start(ap, fmt);
        vsnprintf(heap_buf, n + 1, fmt, ap);
        va_end(ap);
        strbuf_append(b, heap_buf);
        free(heap_buf);
    }
}


static void strbuf_reset(StrBuf *b) {
    b->length  = 0;
    b->data[0] = '\0';
}


/* 
 * 2  Colour
 */

typedef struct {
    double r, g, b;   /* all clamped to [0.0, 1.0] */
} Colour;


static double clamp01(double v) {
    return v < 0.0 ? 0.0 : v > 1.0 ? 1.0 : v;
}

static Colour colour_gray(double gray) {
    double g = clamp01(gray);
    return (Colour){ g, g, g };
}

static Colour colour_rgb(double r, double g, double b) {
    return (Colour){ clamp01(r), clamp01(g), clamp01(b) };
}

/*
 * CMYK --> RGB:  R = (1-C)(1-K),  G = (1-M)(1-K),  B = (1-Y)(1-K)
 */
static Colour colour_cmyk(double c, double m, double y, double k) {
    return (Colour){
        clamp01((1.0 - c) * (1.0 - k)),
        clamp01((1.0 - m) * (1.0 - k)),
        clamp01((1.0 - y) * (1.0 - k)),
    };
}

/* Write "rgb(R,G,B)" into buf (must be ≥ 24 bytes). */
static void colour_fmt(const Colour *c, char *buf, size_t size) {
    snprintf(buf, size, "rgb(%d,%d,%d)",
             (int)(c->r * 255.0 + 0.5),
             (int)(c->g * 255.0 + 0.5),
             (int)(c->b * 255.0 + 0.5));
}


/* 
 * 3  Line dash pattern
 */

#define DASH_MAX 16

typedef struct {
    double values[DASH_MAX];
    int count;
    double offset;
} DashPattern;


static DashPattern dash_solid(void) {
    DashPattern d;
    d.count  = 0;
    d.offset = 0.0;
    return d;
}

/*
 * Format the SVG stroke-dasharray attribute value into buf.
 * Returns an empty string for a solid line.
 */
static void dash_fmt(const DashPattern *d, char *buf, size_t size) {
    if (d->count == 0) {
        buf[0] = '\0';
        return;
    }

    int pos = 0;
    for (int i = 0; i < d->count && pos < (int)size - 16; i++) {
        if (i > 0) buf[pos++] = ' ';
        pos += snprintf(buf + pos, size - pos, "%.4g", d->values[i]);
    }
}


/* 
 * 4  Graphics state
 */

#define FONT_NAME_MAX 64

/*
 * line_cap / line_join use the PostScript integer encoding:
 *   cap:   0=butt  1=round  2=square
 *   join:  0=miter 1=round  2=bevel
 */
typedef struct {
    /* Colour */
    Colour stroke_colour;
    Colour fill_colour;

    /* Line geometry */
    double line_width;
    int line_cap;       /* 0 butt | 1 round | 2 projecting/square */
    int line_join;      /* 0 miter | 1 round | 2 bevel */
    double miter_limit;
    DashPattern dash;

    /* Text */
    char font_name[FONT_NAME_MAX];
    double font_size;
} GraphicsState;


static GraphicsState gs_default(void) {
    GraphicsState g;
    g.stroke_colour = colour_gray(0.0);
    g.fill_colour   = colour_gray(0.0);
    g.line_width    = 1.0;
    g.line_cap      = 0;
    g.line_join     = 0;
    g.miter_limit   = 10.0;
    g.dash          = dash_solid();
    strncpy(g.font_name, "sans-serif", FONT_NAME_MAX - 1);
    g.font_size     = 12.0;
    return g;
}

static const char * linecap_name(int cap) {
    switch (cap) {
        case 1:  return "round";
        case 2:  return "square";
        default: return "butt";
    }
}

static const char * linejoin_name(int join) {
    switch (join) {
        case 1:  return "round";
        case 2:  return "bevel";
        default: return "miter";
    }
}


/* 
 * 5  Graphics state stack
 */

#define GS_STACK_MAX 64

typedef struct {
    GraphicsState levels[GS_STACK_MAX];
    int transform_groups[GS_STACK_MAX]; /* extra <g>s per level */
    int top;
} GsStack;


static void gs_init(GsStack *s) {
    s->top                  = 1;
    s->levels[0]            = gs_default();
    s->transform_groups[0]  = 0;
}

static GraphicsState * gs_top(GsStack *s) {
    return &s->levels[s->top - 1];
}

static bool gs_push(GsStack *s) {
    if (s->top >= GS_STACK_MAX) {
        fprintf(stderr, "warning: graphics state stack overflow\n");
        return false;
    }
    s->levels[s->top] = s->levels[s->top - 1];
    s->transform_groups[s->top] = 0;
    s->top++;
    return true;
}

static bool gs_pop(GsStack *s) {
    if (s->top <= 1) {
        fprintf(stderr, "warning: graphics state stack underflow\n");
        return false;
    }
    s->top--;
    return true;
}


/* 
 * 6  Current path
 */

typedef struct {
    StrBuf *data;
    double  cur_x;
    double  cur_y;
    double  start_x;   /* start of current sub-path, for closepath */
    double  start_y;
    bool  has_point;
} Path;


static Path * path_new(void) {
    Path *p     = malloc(sizeof(Path));
    p->data     = strbuf_new();
    p->cur_x    = 0.0;
    p->cur_y    = 0.0;
    p->start_x  = 0.0;
    p->start_y  = 0.0;
    p->has_point = false;
    return p;
}

static void path_free(Path *p) {
    strbuf_free(p->data);
    free(p);
}

static void path_reset(Path *p) {
    strbuf_reset(p->data);
    p->has_point = false;
}

static bool path_is_empty(const Path *p) {
    return p->data->length == 0;
}


/* 
 * 7  Operand stack
 */

typedef enum {
    OP_NUMBER,
    OP_STRING,
    OP_NODE,
} OperandKind;

typedef struct {
    OperandKind  kind;
    union {
        double number;
        char *string; /* heap-owned */
        const Node *node;
    };
} Operand;

#define OP_STACK_MAX 512

typedef struct {
    Operand items[OP_STACK_MAX];
    int top;
} OpStack;


static void ops_init(OpStack *s) {
    s->top = 0;
}

static void operand_free(Operand *op) {
    if (op->kind == OP_STRING)
        free(op->string);
}

static bool ops_push_number(OpStack *s, double v) {
    if (s->top >= OP_STACK_MAX) {
        fprintf(stderr, "warning: operand stack overflow\n");
        return false;
    }
    s->items[s->top].kind   = OP_NUMBER;
    s->items[s->top].number = v;
    s->top++;
    return true;
}

static bool ops_push_string(OpStack *s, const char *str) {
    if (s->top >= OP_STACK_MAX) {
        fprintf(stderr, "warning: operand stack overflow\n");
        return false;
    }
    s->items[s->top].kind   = OP_STRING;
    s->items[s->top].string = strdup(str);
    s->top++;
    return true;
}

static bool ops_push_node(OpStack *s, const Node *node) {
    if (s->top >= OP_STACK_MAX) {
        fprintf(stderr, "warning: operand stack overflow\n");
        return false;
    }
    s->items[s->top].kind = OP_NODE;
    s->items[s->top].node = node;
    s->top++;
    return true;
}

static bool ops_pop(OpStack *s, Operand *out) {
    if (s->top <= 0) {
        fprintf(stderr, "warning: operand stack underflow\n");
        return false;
    }
    *out = s->items[--s->top];
    return true;
}

static bool ops_pop_number(OpStack *s, double *out) {
    Operand op;
    if (!ops_pop(s, &op)) return false;
    if (op.kind == OP_NUMBER) { *out = op.number; return true; }
    operand_free(&op);
    fprintf(stderr, "warning: expected number on operand stack\n");
    return false;
}

/*
 * Pop N numbers in reverse (deepest first) so callers can assign naturally.
 *
 * E.g. for "r g b setrgbcolor" the stack (top-->bottom) is b g r.
 * ops_pop_n(s, arr, 3) gives arr[0]=r arr[1]=g arr[2]=b.
 */
static bool ops_pop_n(OpStack *s, double *arr, int n) {
    /* Pop into a temp array top-first, then reverse. */
    double tmp[16];
    if (n > 16) return false;
    for (int i = 0; i < n; i++)
        if (!ops_pop_number(s, &tmp[i])) return false;
    for (int i = 0; i < n; i++)
        arr[i] = tmp[n - 1 - i];
    return true;
}


/* 
 * 8  Canvas  (the opaque type declared in ps_codegen.h)
 */

struct SvgCanvas {
    double  width;
    double  height;

    StrBuf  *svg;        /* accumulated SVG element output */
    GsStack  gs;         /* graphics state stack */
    OpStack  ops;        /* PostScript operand stack */
    Path    *path;       /* path currently being constructed */

    /* Text cursor - updated by moveto and rmoveto. */
    double  text_x;
    double  text_y;
};


SvgCanvas * svg_canvas_new(double width, double height) {
    SvgCanvas *c = malloc(sizeof(SvgCanvas));
    c->width     = width;
    c->height    = height;
    c->svg       = strbuf_new();
    c->path      = path_new();
    c->text_x    = 0.0;
    c->text_y    = 0.0;
    gs_init(&c->gs);
    ops_init(&c->ops);
    return c;
}

void svg_canvas_free(SvgCanvas *c) {
    strbuf_free(c->svg);
    path_free(c->path);
    free(c);
}


/* -- Emit helpers -- */

static void emit(SvgCanvas *c, const char *fmt, ...) {
    char    buf[512];
    va_list ap;
    va_start(ap, fmt);
    int n = vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);

    if (n < (int)sizeof(buf)) {
        strbuf_append(c->svg, buf);
    } else {
        char *big = malloc(n + 1);
        va_start(ap, fmt);
        vsnprintf(big, n + 1, fmt, ap);
        va_end(ap);
        strbuf_append(c->svg, big);
        free(big);
    }
}

/* Escape characters that are special in SVG text content. */
static void emit_text_escaped(SvgCanvas *c, const char *text) {
    for (const char *p = text; *p; p++) {
        switch (*p) {
            case '<':  strbuf_append(c->svg, "&lt;");  break;
            case '>':  strbuf_append(c->svg, "&gt;");  break;
            case '&':  strbuf_append(c->svg, "&amp;"); break;
            case '"':  strbuf_append(c->svg, "&quot;");break;
            default:   strbuf_ensure(c->svg, 1);
                       c->svg->data[c->svg->length++] = *p;
                       c->svg->data[c->svg->length]   = '\0';
                       break;
        }
    }
}


/* 
 * 9  Path --> SVG <path> emission
 */

/*
 * Build the style attribute string for a <path> element.
 * Both stroke and fill can be "none" or a colour.
 */
static void build_path_style(SvgCanvas *c, bool do_stroke, bool do_fill, char *buf, size_t size) {
    GraphicsState *gs = gs_top(&c->gs);

    char stroke_col[24], fill_col[24], dash_str[128];
    colour_fmt(&gs->stroke_colour, stroke_col, sizeof(stroke_col));
    colour_fmt(&gs->fill_colour,   fill_col,   sizeof(fill_col));
    dash_fmt(&gs->dash, dash_str, sizeof(dash_str));

    int pos = 0;

    pos += snprintf(buf + pos, size - pos,
                    "stroke=\"%s\" ",
                    do_stroke ? stroke_col : "none");

    if (do_stroke) {
        pos += snprintf(buf + pos, size - pos,
                        "stroke-width=\"%.4g\" "
                        "stroke-linecap=\"%s\" "
                        "stroke-linejoin=\"%s\" "
                        "stroke-miterlimit=\"%.4g\" ",
                        gs->line_width,
                        linecap_name(gs->line_cap),
                        linejoin_name(gs->line_join),
                        gs->miter_limit);

        if (dash_str[0])
            pos += snprintf(buf + pos, size - pos,
                            "stroke-dasharray=\"%s\" "
                            "stroke-dashoffset=\"%.4g\" ",
                            dash_str, gs->dash.offset);
    }

    snprintf(buf + pos, size - pos,
             "fill=\"%s\"",
             do_fill ? fill_col : "none");
}


static void emit_path(SvgCanvas *c, bool do_stroke, bool do_fill) {
    if (path_is_empty(c->path)) return;

    char style[512];
    build_path_style(c, do_stroke, do_fill, style, sizeof(style));

    emit(c, "    <path d=\"%s\"\n"
             "          %s />\n",
         c->path->data->data, style);

    path_reset(c->path);
}


/* 
 * 10  Font name mapping  (PostScript --> CSS font-family)
 */

static void map_font_name(const char *ps_name, char *out, size_t size) {
    /* Strip leading slash if present (e.g. /Helvetica). */
    if (ps_name[0] == '/')
        ps_name++;

    /* Map common PostScript font families to CSS equivalents. */
    if      (strstr(ps_name, "Helvetica") || strstr(ps_name, "Arial"))
        strncpy(out, "sans-serif",  size - 1);
    else if (strstr(ps_name, "Times"))
        strncpy(out, "serif",       size - 1);
    else if (strstr(ps_name, "Courier"))
        strncpy(out, "monospace",   size - 1);
    else if (strstr(ps_name, "Palatino"))
        strncpy(out, "Palatino, serif", size - 1);
    else if (strstr(ps_name, "Bookman"))
        strncpy(out, "Bookman, serif",  size - 1);
    else if (strstr(ps_name, "Symbol"))
        strncpy(out, "Symbol, serif",   size - 1);
    else
        strncpy(out, ps_name, size - 1);

    out[size - 1] = '\0';
}


/* 
 * 11  Operator handlers
 * 
 *
 * Every handler has signature:  bool op_NAME(SvgCanvas *c)
 * Returns false on stack underflow or invalid argument; the caller logs a
 * warning and continues - the SVG remains well-formed even on errors.
 */

/* -- 11.1  Graphics state -- */

static bool op_gsave(SvgCanvas *c) {
    if (!gs_push(&c->gs)) return false;

    GraphicsState *gs = gs_top(&c->gs);
    char sc[24], fc[24];
    colour_fmt(&gs->stroke_colour, sc, sizeof(sc));
    colour_fmt(&gs->fill_colour,   fc, sizeof(fc));

    emit(c,
         "  <g stroke=\"%s\" stroke-width=\"%.4g\""
         " stroke-linecap=\"%s\" stroke-linejoin=\"%s\""
         " stroke-miterlimit=\"%.4g\""
         " fill=\"%s\""
         " font-family=\"%s\" font-size=\"%.4g\">\n",
         sc, gs->line_width,
         linecap_name(gs->line_cap), linejoin_name(gs->line_join),
         gs->miter_limit,
         fc,
         gs->font_name, gs->font_size);

    return true;
}

static bool op_grestore(SvgCanvas *c) {
    /* Close any inner transform groups opened at this GS level. */
    int n_transforms = c->gs.transform_groups[c->gs.top - 1];
    for (int i = 0; i < n_transforms; i++)
        emit(c, "  </g> <!-- transform -->\n");

    if (!gs_pop(&c->gs)) return false;

    emit(c, "  </g> <!-- gsave -->\n");
    return true;
}

static bool op_setlinewidth(SvgCanvas *c) {
    double w;
    if (!ops_pop_number(&c->ops, &w)) return false;
    gs_top(&c->gs)->line_width = w;
    return true;
}

static bool op_setlinecap(SvgCanvas *c) {
    double cap;
    if (!ops_pop_number(&c->ops, &cap)) return false;
    gs_top(&c->gs)->line_cap = (int)cap;
    return true;
}

static bool op_setlinejoin(SvgCanvas *c) {
    double join;
    if (!ops_pop_number(&c->ops, &join)) return false;
    gs_top(&c->gs)->line_join = (int)join;
    return true;
}

static bool op_setmiterlimit(SvgCanvas *c) {
    double ml;
    if (!ops_pop_number(&c->ops, &ml)) return false;
    gs_top(&c->gs)->miter_limit = ml;
    return true;
}

static bool op_setdash(SvgCanvas *c) {
    /*
     * PostScript: [d1 d2 ...] offset setdash
     *
     * The array is on the stack as a NODE_ARRAY node; offset is above it.
     */
    double  offset;
    Operand arr_op;

    if (!ops_pop_number(&c->ops, &offset)) return false;
    if (!ops_pop(&c->ops, &arr_op))        return false;

    DashPattern d;
    d.offset = offset;
    d.count  = 0;

    if (arr_op.kind == OP_NODE
     && arr_op.node
     && arr_op.node->kind == NODE_ARRAY) {

        const Node *arr = arr_op.node;
        int n = arr->child_count < DASH_MAX ? arr->child_count : DASH_MAX;

        for (int i = 0; i < n; i++) {
            const Node *child = arr->children[i];
            if (child->kind == NODE_INTEGER)
                d.values[d.count++] = (double)child->ival;
            else if (child->kind == NODE_FLOAT)
                d.values[d.count++] = child->fval;
        }
    }

    gs_top(&c->gs)->dash = d;
    return true;
}


/* -- 11.2  Colour -- */

static bool op_setgray(SvgCanvas *c) {
    double gray;
    if (!ops_pop_number(&c->ops, &gray)) return false;
    GraphicsState *gs = gs_top(&c->gs);
    gs->stroke_colour = colour_gray(gray);
    gs->fill_colour   = colour_gray(gray);
    return true;
}

static bool op_setrgbcolor(SvgCanvas *c) {
    double vals[3];   /* r g b, deepest first after ops_pop_n */
    if (!ops_pop_n(&c->ops, vals, 3)) return false;
    GraphicsState *gs = gs_top(&c->gs);
    gs->stroke_colour = colour_rgb(vals[0], vals[1], vals[2]);
    gs->fill_colour   = colour_rgb(vals[0], vals[1], vals[2]);
    return true;
}

static bool op_setcmykcolor(SvgCanvas *c) {
    double vals[4];   /* c m y k */
    if (!ops_pop_n(&c->ops, vals, 4)) return false;
    GraphicsState *gs = gs_top(&c->gs);
    Colour col = colour_cmyk(vals[0], vals[1], vals[2], vals[3]);
    gs->stroke_colour = col;
    gs->fill_colour   = col;
    return true;
}

/*
 * setstrokecolor / setfillcolor - non-standard but common in generated PS.
 * Treat them as separate stroke/fill colour setters.
 */
static bool op_setstrokecolor(SvgCanvas *c) {
    double vals[3];
    if (!ops_pop_n(&c->ops, vals, 3)) return false;
    gs_top(&c->gs)->stroke_colour = colour_rgb(vals[0], vals[1], vals[2]);
    return true;
}

static bool op_setfillcolor(SvgCanvas *c) {
    double vals[3];
    if (!ops_pop_n(&c->ops, vals, 3)) return false;
    gs_top(&c->gs)->fill_colour = colour_rgb(vals[0], vals[1], vals[2]);
    return true;
}


/* -- 11.3  Path construction -- */

static bool op_newpath(SvgCanvas *c) {
    path_reset(c->path);
    return true;
}

static bool op_moveto(SvgCanvas *c) {
    double vals[2];   /* x y */
    if (!ops_pop_n(&c->ops, vals, 2)) return false;

    double x = vals[0], y = vals[1];
    strbuf_appendf(c->path->data, "M %.6g %.6g ", x, y);

    c->path->cur_x   = x;  c->path->cur_y   = y;
    c->path->start_x = x;  c->path->start_y = y;
    c->path->has_point = true;
    c->text_x = x;  c->text_y = y;
    return true;
}

static bool op_rmoveto(SvgCanvas *c) {
    double vals[2];   /* dx dy */
    if (!ops_pop_n(&c->ops, vals, 2)) return false;

    double x = c->path->cur_x + vals[0];
    double y = c->path->cur_y + vals[1];
    strbuf_appendf(c->path->data, "M %.6g %.6g ", x, y);

    c->path->cur_x   = x;  c->path->cur_y   = y;
    c->path->start_x = x;  c->path->start_y = y;
    c->path->has_point = true;
    c->text_x = x;  c->text_y = y;
    return true;
}

static bool op_lineto(SvgCanvas *c) {
    double vals[2];
    if (!ops_pop_n(&c->ops, vals, 2)) return false;

    double x = vals[0], y = vals[1];
    strbuf_appendf(c->path->data, "L %.6g %.6g ", x, y);
    c->path->cur_x = x;  c->path->cur_y = y;
    return true;
}

static bool op_rlineto(SvgCanvas *c) {
    double vals[2];
    if (!ops_pop_n(&c->ops, vals, 2)) return false;

    double x = c->path->cur_x + vals[0];
    double y = c->path->cur_y + vals[1];
    strbuf_appendf(c->path->data, "L %.6g %.6g ", x, y);
    c->path->cur_x = x;  c->path->cur_y = y;
    return true;
}

/*
 * curveto - cubic Bézier.
 * PostScript: x1 y1 x2 y2 x3 y3 curveto
 * SVG path:   C x1 y1  x2 y2  x3 y3
 */
static bool op_curveto(SvgCanvas *c) {
    double v[6];   /* x1 y1 x2 y2 x3 y3 */
    if (!ops_pop_n(&c->ops, v, 6)) return false;

    strbuf_appendf(c->path->data,
                   "C %.6g %.6g  %.6g %.6g  %.6g %.6g ",
                   v[0], v[1], v[2], v[3], v[4], v[5]);
    c->path->cur_x = v[4];  c->path->cur_y = v[5];
    return true;
}

/*
 * rcurveto - relative cubic Bézier.
 * PostScript: dx1 dy1 dx2 dy2 dx3 dy3 rcurveto
 */
static bool op_rcurveto(SvgCanvas *c) {
    double v[6];
    if (!ops_pop_n(&c->ops, v, 6)) return false;

    double cx = c->path->cur_x, cy = c->path->cur_y;
    double x1 = cx + v[0], y1 = cy + v[1];
    double x2 = cx + v[2], y2 = cy + v[3];
    double x3 = cx + v[4], y3 = cy + v[5];

    strbuf_appendf(c->path->data,
                   "C %.6g %.6g  %.6g %.6g  %.6g %.6g ",
                   x1, y1, x2, y2, x3, y3);
    c->path->cur_x = x3;  c->path->cur_y = y3;
    return true;
}

/*
 * arc - counter-clockwise arc.
 * PostScript: cx cy r angle1 angle2 arc
 *
 * SVG has no native "centre + angles" arc.  We convert to SVG's endpoint
 * parametrisation.  A full circle requires two arcs to avoid the degenerate
 * case where start == end.
 */
static bool op_arc(SvgCanvas *c) {
    double v[5];   /* cx cy r a1 a2 */
    if (!ops_pop_n(&c->ops, v, 5)) return false;

    double cx = v[0], cy = v[1], r = v[2];
    double a1 = v[3], a2 = v[4];

    /* Normalise: PS arcs are CCW; ensure a2 >= a1. */
    while (a2 < a1) a2 += 360.0;

    double r1 = a1 * M_PI / 180.0;
    double r2 = a2 * M_PI / 180.0;
    double x1 = cx + r * cos(r1),  y1 = cy + r * sin(r1);
    double x2 = cx + r * cos(r2),  y2 = cy + r * sin(r2);

    /* Connect current point to arc start with a line (PS semantics). */
    if (!c->path->has_point) {
        strbuf_appendf(c->path->data, "M %.6g %.6g ", x1, y1);
        c->path->start_x = x1;  c->path->start_y = y1;
    } else {
        strbuf_appendf(c->path->data, "L %.6g %.6g ", x1, y1);
    }
    c->path->has_point = true;

    bool full_circle = (fabs(a2 - a1) >= 360.0);
    int  large_arc   = ((a2 - a1) > 180.0) ? 1 : 0;

    if (full_circle) {
        /* Split into two semicircles. */
        double xm = cx + r * cos(r1 + M_PI);
        double ym = cy + r * sin(r1 + M_PI);
        strbuf_appendf(c->path->data,
                       "A %.6g %.6g 0 0 1 %.6g %.6g "
                       "A %.6g %.6g 0 0 1 %.6g %.6g ",
                       r, r, xm, ym, r, r, x1, y1);
    } else {
        strbuf_appendf(c->path->data,
                       "A %.6g %.6g 0 %d 1 %.6g %.6g ",
                       r, r, large_arc, x2, y2);
    }

    c->path->cur_x = x2;  c->path->cur_y = y2;
    return true;
}

/*
 * arcn - clockwise arc (arc-negative).
 * PostScript: cx cy r angle1 angle2 arcn
 */
static bool op_arcn(SvgCanvas *c) {
    double v[5];
    if (!ops_pop_n(&c->ops, v, 5)) return false;

    double cx = v[0], cy = v[1], r = v[2];
    double a1 = v[3], a2 = v[4];

    /* Normalise: arcn is CW; ensure a2 <= a1. */
    while (a2 > a1) a2 -= 360.0;

    double r1 = a1 * M_PI / 180.0;
    double r2 = a2 * M_PI / 180.0;
    double x1 = cx + r * cos(r1),  y1 = cy + r * sin(r1);
    double x2 = cx + r * cos(r2),  y2 = cy + r * sin(r2);

    if (!c->path->has_point) {
        strbuf_appendf(c->path->data, "M %.6g %.6g ", x1, y1);
        c->path->start_x = x1;  c->path->start_y = y1;
    } else {
        strbuf_appendf(c->path->data, "L %.6g %.6g ", x1, y1);
    }
    c->path->has_point = true;

    bool full_circle = (fabs(a1 - a2) >= 360.0);
    int  large_arc   = ((a1 - a2) > 180.0) ? 1 : 0;

    if (full_circle) {
        double xm = cx + r * cos(r1 + M_PI);
        double ym = cy + r * sin(r1 + M_PI);
        strbuf_appendf(c->path->data,
                       "A %.6g %.6g 0 0 0 %.6g %.6g "
                       "A %.6g %.6g 0 0 0 %.6g %.6g ",
                       r, r, xm, ym, r, r, x1, y1);
    } else {
        strbuf_appendf(c->path->data,
                       "A %.6g %.6g 0 %d 0 %.6g %.6g ",
                       r, r, large_arc, x2, y2);
    }

    c->path->cur_x = x2;  c->path->cur_y = y2;
    return true;
}

static bool op_closepath(SvgCanvas *c) {
    strbuf_append(c->path->data, "Z ");
    c->path->cur_x = c->path->start_x;
    c->path->cur_y = c->path->start_y;
    return true;
}


/* -- 11.4  Painting ---- */

static bool op_stroke(SvgCanvas *c) {
    emit_path(c, true, false);
    return true;
}

static bool op_fill(SvgCanvas *c) {
    emit_path(c, false, true);
    return true;
}

static bool op_eofill(SvgCanvas *c) {
    /*
     * Even-odd fill rule.  SVG supports this via fill-rule="evenodd".
     * We emit the path with an extra attribute.
     */
    if (path_is_empty(c->path)) return true;

    GraphicsState *gs = gs_top(&c->gs);
    char fc[24];
    colour_fmt(&gs->fill_colour, fc, sizeof(fc));

    emit(c, "    <path d=\"%s\"\n"
             "          fill=\"%s\" fill-rule=\"evenodd\""
             " stroke=\"none\" />\n",
         c->path->data->data, fc);

    path_reset(c->path);
    return true;
}

static bool op_strokeandfill(SvgCanvas *c) {
    emit_path(c, true, true);
    return true;
}

/*
 * rectfill - x y w h rectfill
 * Emits a <rect> directly; more efficient than building a path.
 */
static bool op_rectfill(SvgCanvas *c) {
    double v[4];   /* x y w h */
    if (!ops_pop_n(&c->ops, v, 4)) return false;

    GraphicsState *gs = gs_top(&c->gs);
    char fc[24];
    colour_fmt(&gs->fill_colour, fc, sizeof(fc));

    emit(c, "    <rect x=\"%.6g\" y=\"%.6g\""
             " width=\"%.6g\" height=\"%.6g\""
             " fill=\"%s\" stroke=\"none\" />\n",
         v[0], v[1], v[2], v[3], fc);

    return true;
}

/*
 * rectstroke - x y w h rectstroke
 */
static bool op_rectstroke(SvgCanvas *c) {
    double v[4];
    if (!ops_pop_n(&c->ops, v, 4)) return false;

    GraphicsState *gs = gs_top(&c->gs);
    char sc[24];
    colour_fmt(&gs->stroke_colour, sc, sizeof(sc));

    emit(c, "    <rect x=\"%.6g\" y=\"%.6g\""
             " width=\"%.6g\" height=\"%.6g\""
             " stroke=\"%s\" stroke-width=\"%.4g\" fill=\"none\" />\n",
         v[0], v[1], v[2], v[3], sc, gs->line_width);

    return true;
}

/*
 * image / imagemask - placeholder.
 * Real PS image data is complex (binary encoded, various filters).
 * We emit an SVG comment so the output is still valid.
 */
static bool op_image(SvgCanvas *c) {
    /* image takes several parameters - pop what we can. */
    (void)c;
    emit(c, "    <!-- image: not yet implemented -->\n");
    return true;
}


/* -- 11.5  Transforms -- */

/*
 * Transforms emit their own <g transform="..."> WITHOUT pushing a new GS
 * level.  Instead, we increment the transform-group counter for the current
 * GS level so grestore knows how many to close.
 */

static void open_transform_group(SvgCanvas *c, const char *transform) {
    emit(c, "  <g transform=\"%s\">\n", transform);
    c->gs.transform_groups[c->gs.top - 1]++;
}

static bool op_translate(SvgCanvas *c) {
    double v[2];   /* tx ty */
    if (!ops_pop_n(&c->ops, v, 2)) return false;

    char t[64];
    snprintf(t, sizeof(t), "translate(%.6g,%.6g)", v[0], v[1]);
    open_transform_group(c, t);
    return true;
}

static bool op_rotate(SvgCanvas *c) {
    double angle;
    if (!ops_pop_number(&c->ops, &angle)) return false;

    char t[32];
    snprintf(t, sizeof(t), "rotate(%.6g)", angle);
    open_transform_group(c, t);
    return true;
}

static bool op_scale(SvgCanvas *c) {
    double v[2];   /* sx sy */
    if (!ops_pop_n(&c->ops, v, 2)) return false;

    char t[64];
    snprintf(t, sizeof(t), "scale(%.6g,%.6g)", v[0], v[1]);
    open_transform_group(c, t);
    return true;
}


/* -- 11.6  Text -- */

static bool op_setfont(SvgCanvas *c) {
    /*
     * PostScript: /FontName size setfont
     * Stack (top-->bottom): size  /FontName
     */
    double  size;
    Operand name_op;

    if (!ops_pop_number(&c->ops, &size)) return false;
    if (!ops_pop(&c->ops, &name_op))     return false;

    const char *raw = "";
    if      (name_op.kind == OP_STRING) raw = name_op.string;
    else if (name_op.kind == OP_NODE && name_op.node && name_op.node->sval)
        raw = name_op.node->sval;

    GraphicsState *gs = gs_top(&c->gs);
    gs->font_size = size;
    map_font_name(raw, gs->font_name, FONT_NAME_MAX);

    if (name_op.kind == OP_STRING) free(name_op.string);
    return true;
}

static bool op_selectfont(SvgCanvas *c) {
    /* selectfont has same stack layout as setfont */
    return op_setfont(c);
}

static bool op_show(SvgCanvas *c) {
    Operand op;
    if (!ops_pop(&c->ops, &op)) return false;

    const char *text = (op.kind == OP_STRING) ? op.string : "";

    GraphicsState *gs = gs_top(&c->gs);
    char fc[24];
    colour_fmt(&gs->fill_colour, fc, sizeof(fc));

    /*
     * Counter-flip text so it reads left-to-right and right-way-up.
     *
     * The root SVG group applies scale(1,-1) to map PostScript's
     * bottom-left origin to SVG's top-left origin.  That same transform
     * flips every <text> element, mirroring it vertically and reversing
     * the baseline direction.
     *
     * Fix: apply another scale(1,-1) on the element itself, pivoting
     * around the text's own anchor point (text_x, text_y):
     *
     *   transform="scale(1,-1) translate(0, -2*y)"
     *
     * The two vertical flips cancel out, leaving the text upright and
     * correctly positioned.
     */
    emit(c, "    <text x=\"%.6g\" y=\"%.6g\""
             " transform=\"scale(1,-1) translate(0,%.6g)\""
             " font-family=\"%s\" font-size=\"%.4g\""
             " fill=\"%s\">",
         c->text_x, c->text_y,
         -2.0 * c->text_y,
         gs->font_name, gs->font_size, fc);

    emit_text_escaped(c, text);
    emit(c, "</text>\n");

    if (op.kind == OP_STRING) free(op.string);
    return true;
}

/*
 * ashow - like show but also adjusts spacing.
 * PostScript: ax ay string ashow
 * We ignore the spacing adjustments and just show the string.
 */
static bool op_ashow(SvgCanvas *c) {
    Operand str_op;
    double  ax, ay;

    if (!ops_pop(&c->ops, &str_op))   return false;
    if (!ops_pop_number(&c->ops, &ay)) { operand_free(&str_op); return false; }
    if (!ops_pop_number(&c->ops, &ax)) { operand_free(&str_op); return false; }
    (void)ax; (void)ay;

    /* Re-push string and delegate to show. */
    if (str_op.kind == OP_STRING)
        ops_push_string(&c->ops, str_op.string);
    else
        ops_push_node(&c->ops, str_op.node);

    bool ok = op_show(c);
    operand_free(&str_op);
    return ok;
}

/*
 * stringwidth - pushes the width and height of a string.
 * We push 0 0 as a placeholder (we don't have a font metric engine).
 */
static bool op_stringwidth(SvgCanvas *c) {
    Operand op;
    if (!ops_pop(&c->ops, &op)) return false;
    operand_free(&op);
    ops_push_number(&c->ops, 0.0);   /* wx */
    ops_push_number(&c->ops, 0.0);   /* wy */
    return true;
}


/* -- 11.7  Stack / arithmetic (for operands used by drawing ops) -- */

static bool op_pop(SvgCanvas *c) {
    Operand op;
    if (!ops_pop(&c->ops, &op)) return false;
    operand_free(&op);
    return true;
}

static bool op_dup(SvgCanvas *c) {
    if (c->ops.top < 1) return false;
    Operand *top = &c->ops.items[c->ops.top - 1];
    if (top->kind == OP_STRING)
        ops_push_string(&c->ops, top->string);
    else if (top->kind == OP_NUMBER)
        ops_push_number(&c->ops, top->number);
    else
        ops_push_node(&c->ops, top->node);
    return true;
}

static bool op_exch(SvgCanvas *c) {
    if (c->ops.top < 2) return false;
    Operand tmp                    = c->ops.items[c->ops.top - 1];
    c->ops.items[c->ops.top - 1]  = c->ops.items[c->ops.top - 2];
    c->ops.items[c->ops.top - 2]  = tmp;
    return true;
}

static bool op_add(SvgCanvas *c) {
    double a, b;
    if (!ops_pop_number(&c->ops, &b)) return false;
    if (!ops_pop_number(&c->ops, &a)) return false;
    return ops_push_number(&c->ops, a + b);
}

static bool op_sub(SvgCanvas *c) {
    double a, b;
    if (!ops_pop_number(&c->ops, &b)) return false;
    if (!ops_pop_number(&c->ops, &a)) return false;
    return ops_push_number(&c->ops, a - b);
}

static bool op_mul(SvgCanvas *c) {
    double a, b;
    if (!ops_pop_number(&c->ops, &b)) return false;
    if (!ops_pop_number(&c->ops, &a)) return false;
    return ops_push_number(&c->ops, a * b);
}

static bool op_div(SvgCanvas *c) {
    double a, b;
    if (!ops_pop_number(&c->ops, &b)) return false;
    if (!ops_pop_number(&c->ops, &a)) return false;
    if (b == 0.0) {
        fprintf(stderr, "warning: division by zero\n");
        return ops_push_number(&c->ops, 0.0);
    }
    return ops_push_number(&c->ops, a / b);
}

static bool op_neg(SvgCanvas *c) {
    double a;
    if (!ops_pop_number(&c->ops, &a)) return false;
    return ops_push_number(&c->ops, -a);
}

static bool op_abs(SvgCanvas *c) {
    double a;
    if (!ops_pop_number(&c->ops, &a)) return false;
    return ops_push_number(&c->ops, fabs(a));
}

static bool op_sqrt(SvgCanvas *c) {
    double a;
    if (!ops_pop_number(&c->ops, &a)) return false;
    return ops_push_number(&c->ops, sqrt(a));
}

static bool op_sin(SvgCanvas *c) {
    double a;
    if (!ops_pop_number(&c->ops, &a)) return false;
    return ops_push_number(&c->ops, sin(a * M_PI / 180.0));
}

static bool op_cos(SvgCanvas *c) {
    double a;
    if (!ops_pop_number(&c->ops, &a)) return false;
    return ops_push_number(&c->ops, cos(a * M_PI / 180.0));
}

static bool op_def(SvgCanvas *c) {
    /* We don't maintain a PS dict - just discard both operands. */
    Operand a, b;
    if (!ops_pop(&c->ops, &b)) return false;
    if (!ops_pop(&c->ops, &a)) return false;
    operand_free(&a);  operand_free(&b);
    return true;
}

static bool op_showpage(SvgCanvas *c) {
    /* No-op in SVG; a page boundary has no meaning here. */
    (void)c;
    emit(c, "  <!-- showpage -->\n");
    return true;
}


/* 
 * 12  Operator dispatch table
 * 
 *
 * Keep entries alphabetically sorted within each group for readability.
 * Adding a new operator = one line here + one handler function above.
 */

typedef bool (*OpFn)(SvgCanvas *);

typedef struct {
    const char *name;
    OpFn        fn;
} OpEntry;

static const OpEntry OPERATORS[] = {
    /* Arithmetic & stack */
    { "abs",            op_abs            },
    { "add",            op_add            },
    { "cos",            op_cos            },
    { "def",            op_def            },
    { "div",            op_div            },
    { "dup",            op_dup            },
    { "exch",           op_exch           },
    { "mul",            op_mul            },
    { "neg",            op_neg            },
    { "pop",            op_pop            },
    { "sin",            op_sin            },
    { "sqrt",           op_sqrt           },
    { "sub",            op_sub            },

    /* Graphics state */
    { "grestore",       op_grestore       },
    { "gsave",          op_gsave          },
    { "setcmykcolor",   op_setcmykcolor   },
    { "setdash",        op_setdash        },
    { "setfillcolor",   op_setfillcolor   },
    { "setgray",        op_setgray        },
    { "setlinecap",     op_setlinecap     },
    { "setlinejoin",    op_setlinejoin    },
    { "setlinewidth",   op_setlinewidth   },
    { "setmiterlimit",  op_setmiterlimit  },
    { "setrgbcolor",    op_setrgbcolor    },
    { "setstrokecolor", op_setstrokecolor },

    /* Path construction */
    { "arc",            op_arc            },
    { "arcn",           op_arcn           },
    { "closepath",      op_closepath      },
    { "curveto",        op_curveto        },
    { "lineto",         op_lineto         },
    { "moveto",         op_moveto         },
    { "newpath",        op_newpath        },
    { "rcurveto",       op_rcurveto       },
    { "rlineto",        op_rlineto        },
    { "rmoveto",        op_rmoveto        },

    /* Painting */
    { "eofill",         op_eofill         },
    { "fill",           op_fill           },
    { "fillstroke",     op_strokeandfill  },
    { "image",          op_image          },
    { "imagemask",      op_image          },
    { "rectfill",       op_rectfill       },
    { "rectstroke",     op_rectstroke     },
    { "stroke",         op_stroke         },

    /* Transforms */
    { "rotate",         op_rotate         },
    { "scale",          op_scale          },
    { "translate",      op_translate      },

    /* Text */
    { "ashow",          op_ashow          },
    { "selectfont",     op_selectfont     },
    { "setfont",        op_setfont        },
    { "show",           op_show           },
    { "showpage",       op_showpage       },
    { "stringwidth",    op_stringwidth    },

    { NULL, NULL },   /* sentinel */
};


static OpFn find_op(const char *name) {
    for (int i = 0; OPERATORS[i].name; i++)
        if (strcmp(OPERATORS[i].name, name) == 0)
            return OPERATORS[i].fn;
    return NULL;
}


/* 
 * 13  AST walker
 */

static void walk(SvgCanvas *c, const Node *node);

static void walk_children(SvgCanvas *c, const Node *parent) {
    for (int i = 0; i < parent->child_count; i++)
        walk(c, parent->children[i]);
}

static void walk(SvgCanvas *c, const Node *node) {
    if (!node) return;

    switch (node->kind) {

        /* -- Literals --> push onto operand stack -- */

        case NODE_INTEGER:
            ops_push_number(&c->ops, (double)node->ival);
            break;

        case NODE_FLOAT:
            ops_push_number(&c->ops, node->fval);
            break;

        case NODE_STRING:
            ops_push_string(&c->ops, node->sval ? node->sval : "");
            break;

        case NODE_NAME:
            /* /LiteralName - push as a node (consumed by setfont etc.) */
            ops_push_node(&c->ops, node);
            break;

        case NODE_PROCEDURE:
        case NODE_ARRAY:
            /* Push the compound node; operators like setdash consume it. */
            ops_push_node(&c->ops, node);
            break;

        /* -- Operators --> dispatch -- */

        case NODE_OPERATOR: {
            const char *name = node->sval;
            OpFn        fn   = find_op(name);

            if (fn) {
                if (!fn(c)) {
                    fprintf(stderr,
                            "warning: '%s' (byte %d) failed\n",
                            name, node->source_pos);
                }
            }
            /* Unknown operators are silently ignored - they may be user
               procedures or PS idioms that don't affect rendering. */
            break;
        }

        /* -- Structural nodes --> recurse -- */

        case NODE_PROGRAM:
            walk_children(c, node);
            break;

        case NODE_COMMENT:
        case NODE_HEXSTRING:
            /* Comments produce no SVG output. */
            break;
    }
}


/* 
 * 14  Public API
 */

bool svg_generate(SvgCanvas *c, const Node *ast) {
    if (!ast) return false;
    walk(c, ast);
    return true;
}

void svg_canvas_write(const SvgCanvas *c, FILE *out) {
    fprintf(out,
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
            "<svg xmlns=\"http://www.w3.org/2000/svg\"\n"
            "     width=\"%.6g\" height=\"%.6g\"\n"
            "     viewBox=\"0 0 %.6g %.6g\">\n"
            "\n"
            "  <!--\n"
            "    Generated by ps2svg.\n"
            "    Coordinate system: PostScript (origin bottom-left) flipped\n"
            "    to SVG (origin top-left) via the transform on the root group.\n"
            "  -->\n"
            "\n"
            "  <g transform=\"scale(1,-1) translate(0,-%.6g)\">\n"
            "\n",
            c->width, c->height,
            c->width, c->height,
            c->height);

    fputs(c->svg->data, out);

    fprintf(out,
            "\n"
            "  </g> <!-- coordinate flip -->\n"
            "\n"
            "</svg>\n");
}
