
### Baseline: Naive Implementation

```c
// Version 0: Naive approach - 12 FPS
void render_v0() {
    for (every pixel on screen) {
        draw_pixel_to_display();  // Each pixel = SPI transaction
    }
}
```

*Performance:* ~12 FPS, severe tearing, sluggish
*Why slow:* 76,800 individual SPI transactions per frame


### Optimisation 1: Batched Writes (+150% FPS)

```c
// Version 1: Batch writes - 30 FPS
void render_v1() {
    for (each rectangle) {
        set_window(x, y, w, h);
        write_pixels(buffer, w*h);  // One SPI transaction per rectangle
    }
}
```

*Performance:* ~30 FPS, still some tearing
*Improvement:* 150% faster (12 → 30 FPS)
*Why faster:* ~50 SPI transactions instead of 76,800



### Optimisation 2: Framebuffer (+200% FPS)

```c
// Version 2: Framebuffer - 60 FPS
uint16_t framebuffer[320*240];

void render_v2() {
    clear_framebuffer();           // Fast memory write
    draw_to_framebuffer();         // All drawing in RAM
    flush_framebuffer_via_dma();   // ONE SPI transfer
}
```

*Performance:* ~60 FPS, smooth, no tearing
*Improvement:* 200% faster than v1 (30 → 60 FPS), 400% faster than v0
*Why faster:* 
- All drawing happens in fast RAM
- Single DMA transfer (no CPU overhead)
- No tearing (complete frames only)

*Memory cost:* 150KB (320×240×2 bytes)



### Optimisation 3: Dirty Rectangles (Same FPS, Less Power)

```c
// Version 3: Dirty regions - 60 FPS, 70% power savings
void render_v3() {
    track_changed_regions();
    
    if (small_changes) {
        // Only update changed rectangles
        for (each dirty_rect) {
            blit_region(rect);
        }
    } else {
        // Full frame if many changes
        flush_framebuffer();
    }
}
```

*Performance:* ~60 FPS (same), but ~70% less data transferred
*When useful:* Menu screens, HUD updates, minimal movement
*Not useful:* Fast-moving games like Space Invaders (everything moves)



### Optimisation 4: Fixed-Point Math (+5% FPS)

```c
// Version 4: Fixed-point - 63 FPS
// Replace float with fixed-point integer math

// Before (slow)
float x = 10.5f;
x += 0.3f * delta_time;

// After (fast)
int32_t x = 10 << 8;  // 10.0 in 24.8 fixed-point
x += (77 * delta_time) >> 8;  // 0.3 * delta_time
```

*Performance:* ~63 FPS
*Improvement:* Minor (60 → 63 FPS), but consistent
*Why faster:* No floating-point emulation on Cortex-M0+



### Optimisation 5: Spatial Partitioning (Only for Many Objects)

```c
// Version 5: Spatial grid - useful for 100+ objects
#define GRID_SIZE 8
Cell grid[GRID_SIZE][GRID_SIZE];

void check_collisions_v5() {
    // Only check objects in same/adjacent cells
    for (each bullet) {
        Cell* cell = get_cell(bullet.x, bullet.y);
        check_adjacent_cells(cell);  // 9 cells max
    }
}
```

*When useful:* 100+ objects (bullets, particles, enemies)
*Our case:* 15 invaders, 5 bullets = *waste of time*
*Break-even point:* ~50+ dynamic objects



### Performance Summary

| Version | FPS | Frame Time | Key Technique | Complexity |
|---------|-----|------------|---------------|------------|
| 0. Naive | 12 | 83ms | Pixel-by-pixel | Very Simple |
| 1. Batched | 30 | 33ms | Rectangle writes | Simple |
| 2. Framebuffer | 60 | 16ms | DMA + RAM | *Sweet spot* |
| 3. Dirty rects | 60 | 10ms* | Update tracking | Complex |
| 4. Fixed-point | 63 | 15ms | Integer math | Medium |
| 5. Spatial | 60 | 16ms | Grid partition | Very Complex |

*Less data transferred, not necessarily faster rendering



### When to Use

#### Always Use:
- *Batched writes* - Free performance, no downside
- *Framebuffer* - Mandatory for smooth gameplay
- *Fixed-point* - Small effort, consistent benefit

#### Dependent/Situational:
- *Dirty rectangles* - Only for static/slow-moving content
- *Spatial partitioning* - Only for 50+ dynamic objects
- *Object pooling* - Only if creating/destroying many objects

#### Avoid:
- *Premature optimization* - Profile first!
- *Micro-optimizations* - Focus on algorithmic improvements
- *Over-engineering* - Simple code is maintainable code



### Real-World Example: When Spatial Grid Helps

```c
// BAD: Checking 1,000 bullets vs 1,000 enemies = 1,000,000 checks
for (each of 1000 bullets) {
    for (each of 1000 enemies) {
        check_collision();  // 1,000,000 iterations!
    }
}

// GOOD: With spatial grid = ~9,000 checks (99% reduction)
for (each of 1000 bullets) {
    Cell* cells = get_adjacent_cells(bullet);  // 9 cells
    for (each enemy in cells) {  // ~9 enemies per cell
        check_collision();  // 1,000 × 9 = 9,000 iterations
    }
}
```

*Savings:* 1,000,000 → 9,000 checks (111× faster)



### Golden Rule

> *Optimise what matters, measure everything*

1. *Profile first* - Don't guess what's slow
2. *Target bottlenecks* - 80% of time in 20% of code
3. *Measure improvements* - Numbers don't lie
4. *Keep it simple* - Readable code is debuggable code

For a game with 15 invaders and 20 projectiles:
-  Use framebuffer (mandatory)
-  Use fixed-point math (easy win)
-  Skip spatial grids (overkill)
-  Skip dirty rectangles (everything moves)



### Memory vs Speed Trade-offs

| Technique | RAM Cost | Speed Gain | Worth It? |
|-----------|----------|------------|-----------|
| Framebuffer | 150KB | 400% | ✅ Always |
| Pre-computed sprites | 1-5KB | 20% | ✅ Yes |
| Spatial grid | <1KB | -5%* | ❌ Not for small games |
| Dirty tracking | <1KB | 0%* | ⚠️ Situational |

*Negative for games with few objects (overhead > benefit)  
*No FPS gain, but reduces power/heat



### Code Example: Proper Profiling

```c
// Measure what actually matters
typedef struct {
    uint32_t game_logic_us;
    uint32_t render_us;
    uint32_t total_us;
    uint32_t fps;
} perf_stats_t;

void profile_frame() {
    uint32_t start = time_us_32();
    
    uint32_t logic_start = time_us_32();
    update_game();
    uint32_t logic_end = time_us_32();
    
    uint32_t render_start = time_us_32();
    render_game();
    uint32_t render_end = time_us_32();
    
    stats.game_logic_us = logic_end - logic_start;
    stats.render_us = render_end - render_start;
    stats.total_us = time_us_32() - start;
    
    // Now you KNOW where the time goes!
    printf("Logic: %lu us, Render: %lu us\n", 
           stats.game_logic_us, stats.render_us);
}
```



### Conclusion

*For the Space Invaders game:*

```c
// This is all you need:
int main() {
    disp_framebuffer_alloc();  // ONE optimization that matters
    
    while (1) {
        update_game();           // Simple logic
        render_to_framebuffer(); // Draw in RAM
        disp_framebuffer_flush(); // DMA to display
    }
}
```

Simple, fast (60 FPS), maintainable. Done.

*Don't add complexity unless measurements prove it's needed!*
