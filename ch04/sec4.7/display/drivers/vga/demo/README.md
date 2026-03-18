
## Pico 2 VGA Graphics Demo

A double-buffered 2D vector graphics engine for the Raspberry Pi Pico 2,
targeting 320×240 RGB565 output at 60 Hz via `pico_scanvideo_dpi` from pico-extras.
The engine supports Flash-style shapes with solid fills, linear and radial gradients,
stroked outlines, and a depth-sorted scene graph. A sort of basic vector graphics
implementation, which can be extended to e.g., SVG or text rendering.


### Architecture overview

```
Core 0                          Core 1
  │                               │
  ├── demo_update()               ├── vga_core1_main()  (never returns)
  │     ├── physics / animation   │     └── tight scanline loop
  │     └── gfx_render()          │           ├── begin_scanline_generation()
  │           ├── raster_shape()  │           ├── copy row from front buffer
  │           └── raster_stroke() │           └── end_scanline_generation()
  │                               │
  └── vga_swap_buffers()  ─────> picks up new front on next frame
```

The two cores share nothing except two framebuffers and a handful of volatile pointers.
Core 0 owns rasterisation; core 1 owns the scanline state machine.


### VGA output

#### The scanline driver

`vga.c` wraps `pico_scanvideo_dpi`. Core 1 runs `vga_core1_main()` in an infinite loop,
calling `scanvideo_begin_scanline_generation()` for each scanline the hardware needs.
For every line it formats one composable scanline buffer using the `COMPOSABLE_RAW_RUN`
token layout that `pico_scanvideo_dpi` expects:

```
words[0]  lo16 = COMPOSABLE_RAW_RUN token
          hi16 = pixel[0]
words[1]  lo16 = (width - 3)              <-- number of additional pixels
          hi16 = pixel[1]
words[2…] lo/hi16 pairs of remaining pixels
last      COMPOSABLE_EOL_ALIGN
```

Pixels are read from `cur_front`, a snapshot of the front-buffer pointer taken at the
first scanline of each frame. This means the entire frame is always coherent. I.e. a
swap mid-frame cannot corrupt a scanline in progress.

#### Double buffering

```c
static volatile gfx_color_t * volatile vga_front = fb_a;
static volatile gfx_color_t * volatile vga_back  = fb_b;
```

Core 0 always writes to `vga_back`. After finishing a frame it calls `vga_swap_buffers()`,
which atomically promotes back --> front and front --> back. On RP2350 a 32-bit aligned
pointer write is atomic with respect to the other core, so no mutex is needed.
(See [ch07, sec7.4](./../../../../../../ch07/sec7.4/concurrency/) conceptually on the
low-level details.)

`vga_wait_vsync()` then spins on `vga_swap_ack`, a counter that core 1 increments each
time it starts a new frame from the new front buffer. Waiting here eliminates tearing
if core 0 finishes before the display refresh.

#### Frame counter and sync

```c
static volatile uint32_t vga_frames   = 0;
static volatile uint32_t vga_swap_ack = 0;
```

Core 1 copies `scanvideo_frame_number()` into `vga_frames` and mirrors it to `vga_swap_ack`
at the start of every frame. Core 0 reads `vga_frame_count()` for performance measurement
and uses `vga_wait_vsync()` to pace itself.

#### Timing in `main.c`

```c
absolute_time_t prev = get_absolute_time();
while (true) {
    absolute_time_t now = get_absolute_time();
    int64_t us = absolute_time_diff_us(prev, now);
    prev = now;
    float dt = (float)us * 1e-6f;
    if (dt > 0.05f) dt = 0.05f;   /* cap at 50 ms to prevent spiral-of-death */
    ...
}
```

`dt` is derived from wall-clock microseconds, so the animation runs at correct real-time
speed regardless of render load. The 50 ms cap prevents a single slow frame from producing
a huge physics step.



### Graphics stack

Parts of the code have been reimplemented of Flash, originally
developed in Java--likely by Macromedia in the late 1990s. Core concepts
such as gradient rendering and similar techniques are already well established,
but the relatively small codebase (designed for applets) includes a number
of clever optimisations and trade-offs, used here.


#### Coordinate system and matrix (`gfx.h`, `gfx.c`)

Shapes are defined in shape-local pixel space. A 2 x 3 affine matrix maps them to screen space:

```
| a  b  tx |
| c  d  ty |
```

`a`, `b`, `c`, `d` are 16.16 fixed-point; `tx`, `ty` are integer pixels.
The layout follows the Flash/SWF convention. Helper constructors cover the common cases:

```c
gfx_mat_scale(sx, sy)
gfx_mat_rotate(radians)
gfx_mat_translate(tx, ty)
gfx_mat_concat(m1, m2)    /* m1 applied first, then m2 */
gfx_mat_invert(m)
```

#### Shapes and path commands

A `gfx_shape_t` holds up to 16 fill styles, 8 line styles, and 512 path commands.
Commands are one of:

- `GFX_CMD_MOVE` — moves the pen and sets the active fill/line style indices
- `GFX_CMD_LINE` — straight segment to `(x, y)`
- `GFX_CMD_CURVE` — quadratic Bézier to `(x, y)` with control point `(cx, cy)`

Fill and line indices are 1-based; index 0 means "none". The builder functions
(`gfx_shape_add_fill_solid`, `gfx_shape_add_line`, etc.) return these indices
so you can assign them in `gfx_shape_move`.

#### Fill types

```c
GFX_FILL_SOLID    /* single RGB565 color */
GFX_FILL_LINEAR   /* gradient along gradient-space x-axis */
GFX_FILL_RADIAL   /* gradient from origin outward */
```

Gradients carry a `gfx_mat_t` that maps screen space into gradient space.
Scaling it controls the gradient's size and orientation. Up to 8 colour stops
per gradient, each with a `ratio` in [0, 255].

#### Color transform

```c
result = clamp(channel * mul / 256 + add)
```

Applied per-object at render time, allowing per-object brightness, tint,
or saturation changes without rebuilding the shape.

#### Scene graph

`gfx_scene_t` is a painter's-algorithm display list sorted by depth.
`gfx_scene_place()` inserts or replaces an object at a given depth.
Each frame core 0 updates transforms and colour transforms, then
calls `gfx_render()`, which walks the list front-to-back and calls
`raster_shape()` then `raster_stroke()` for each object.

#### Rasteriser (`raster.c`)

The fill rasteriser uses a classic scanline algorithm:
1. Walk path commands, apply the object matrix to each vertex.
2. Bézier curves are adaptively subdivided into line segments
   (De Casteljau at t=0.5, taxicab flatness test, max depth 8).
3. Each line segment emits an `raster_edge_t` into a y-indexed bucket table.
4. For each scanline: pull new edges from the bucket into the
   Active Edge List (AEL), insertion-sort by x, walk AEL pairs
   for even-odd fill, fill horizontal spans, advance each edge's
   x by its fixed-point slope, retire finished edges.

Gradient fills sample the pre-built 256-entry RGB565 ramp at each pixel
using the gradient matrix. Solid fills use 32-bit writes (two pixels at a time) for throughput.

The stroke rasteriser re-walks the path and draws Bresenham lines.
Thick strokes are approximated by drawing multiple offset lines in the normal direction.

The `raster_ctx_t` (~20 KB) and gradient ramps (~8 KB) are declared
`static` inside `raster_shape()` to avoid overflowing the RP2350's 8 KB core stack.



### Demo scene (`demo.c`)

The demo builds three shapes once in `demo_init()` and updates only their transforms
and colour transforms each frame. The background is drawn with immediate-mode horisontal
spans (`gfx_fb_hline`) rather than through the scene graph, saving edge-table overhead
for the full-screen fill.

| Object | Technique |
|--------|-----------|
| Star | 5-point polygon, radial gradient, 1 px stroke, rotation |
| Diamond | 4 quadratic Bézier sides, solid fill, 2 px stroke, box-bounce physics |
| Orbiter | 16-segment Bézier circle, solid fill, elliptical orbit |
| Background | Immediate-mode sine-wave colour bands, per row |



### Extending the project

#### New shapes

Call `gfx_shape_init()`, add fill and line styles, then emit move/line/curve commands.
Shapes are reusable: the same `gfx_shape_t` can be placed at multiple depths with
different matrices. Because `gfx_scene_place()` stores only a pointer to the shape,
memory cost is per-shape, not per-instance.

#### Multiple fill styles on one shape

A single path can carry several fills simultaneously--useful for Flash-style complex
shapes where left-edge and right-edge fills differ. Assign distinct `f0` and `f1`
indices in `gfx_shape_move`. The rasteriser runs one even-odd pass per fill ID in a 
ingle scanline sweep, so additional fills cost very little extra time.

#### Sprites and bitmap fills

`GFX_FILL_LINEAR` and `GFX_FILL_RADIAL` both resolve colour through a gradient matrix
and a ramp lookup. Bitmap fills could slot in as a third type using the same matrix
framework: map screen coordinates into *texel space* via the gradient matrix, then index
into a `uint16_t[]` texture instead of the ramp array.

#### Antialiasing

`raster.c` contains a commented-out Wu line stub (`stroke_line_wu`). Pixel-level antialiasing
for fills would require either a coverage buffer (accumulate alpha per pixel, composite at
end of scanline) or a 2x supersample pass. At 320 x 240 the pixel density is low enough that
even simple coverage counts (1/4 pixel steps) would be visible.

#### Second render thread

At present, `raster_shape()` uses two `static` buffers so it is not re-entrant. To overlap
rasterisation with display on a device that has more than two cores, either make `raster_ctx_t`
and the ramp arrays heap-allocated (or stack-local for a deeper stack) and pass them explicitly,
or partition the scene by depth and rasterise each half on a separate core into the same
framebuffer (no overlap in y is required if objects are known not to intersect).

#### Variable resolution

`GFX_W` and `GFX_H` are compile-time constants used by the rasteriser clipper, the
framebuffer helpers, and the VGA scanline formatter. Changing resolution means updating
those constants and selecting a matching `scanvideo_mode_t`. The `COMPOSABLE_RAW_RUN`
loop in `vga_core1_main()` already reads `GFX_W` dynamically.

#### Frame-rate measurement

`vga_frame_count()` returns the scanvideo frame counter. Sampling it at the start and
end of a fixed wall-clock interval (via `get_absolute_time()`) gives frames per second
without needing a timer interrupt.


### File map

| File                  | Role                                                                      |
|-----------------------|---------------------------------------------------------------------------|
| `vga.h / vga.c`       | Double-buffered scanline driver, core 1 loop                              |
| `gfx.h / gfx.c`       | Matrix math, shape builder, scene graph, framebuffer helpers              |
| `raster.h / raster.c` | Scanline fill rasteriser, stroke rasteriser                               |
| `demo.h / demo.c`     | Animated scene: builds shapes, updates transforms, draws background       |
| `main.c`              | Entry point: initialises VGA, launches core 1, runs render loop on core 0 |


### Dependencies

- [Raspberry Pi Pico SDK](https://github.com/raspberrypi/pico-sdk)
- [pico-extras](https://github.com/raspberrypi/pico-extras)
   which provides `pico_scanvideo_dpi` and the `vga_mode_320x240_60` mode descriptor
