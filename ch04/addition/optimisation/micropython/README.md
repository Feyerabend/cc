
## Optimisations


### 1. Reduce Rectangle Calls

*Problem:* Each `display.rectangle()` has overhead

```python
# SLOW: 50+ rectangle calls per frame
for invader in invaders:
    for y, row in enumerate(pixels):
        for x, pixel in enumerate(row):
            if pixel:
                display.rectangle(...)  # 10-15 calls per invader!
```

*Solution:* Combine rectangles or use simpler shapes

```python
# FAST: 15 rectangle calls per frame
for invader in invaders:
    # Single rectangle for body
    display.rectangle(inv['x'], inv['y'], inv['width'], inv['height'])
    # Two rectangles for eyes
    display.rectangle(...)  # 3 calls per invader total
```

*Impact:* 28 FPS → 40 FPS (+43%)



### 2. Batch Pen Setting

*Problem:* `set_pen()` has overhead

```python
# SLOW: Set pen 15+ times
for invader in invaders:
    display.set_pen(invader['color'])
    draw_invader(invader)
```

*Solution:* Group objects by color

```python
# FAST: Set pen 3-4 times total
display.set_pen(GREEN)
for invader in green_invaders:
    draw_invader(invader)

display.set_pen(RED)
for invader in red_invaders:
    draw_invader(invader)
```

*Impact:* 40 FPS → 43 FPS (+8%)



### 3. Reduce Allocations

*Problem:* Python list operations allocate memory

```python
# SLOW: Creates new list every frame
for i, bullet in enumerate(bullets[:]):  # Copies entire list!
    if bullet['y'] < 0:
        bullets.pop(i)  # Shifts remaining elements
```

*Solution:* Use list comprehensions or reverse iteration

```python
# BETTER: List comprehension (single allocation)
bullets = [b for b in bullets if b['y'] >= 0]

# BEST: Reverse iteration (no allocation)
for i in range(len(bullets) - 1, -1, -1):
    if bullets[i]['y'] < 0:
        bullets.pop(i)
```

*Impact:* 43 FPS → 45 FPS (+5%)




### 4. Cache Calculations

*Problem:* Repeated calculations in loops

```python
# SLOW: Calculates every pixel
pixel_size_x = bunker['width'] / len(bunker['pixels'][0])
pixel_size_y = bunker['height'] / len(bunker['pixels'])
```

*Solution:* Calculate once, store in dict

```python
# FAST: Calculate at init
bunker['pixel_size_x'] = bunker['width'] / 5
bunker['pixel_size_y'] = bunker['height'] / 3
```

*Impact:* 45 FPS → 46 FPS (+2%)



### Optimisation Results Summary

| Optimization | FPS | Improvement | Effort | Worth It? |
|--------------|-----|-------------|--------|-----------|
| Baseline | 28 | - | - | - |
| Reduce rectangles | 40 | +43% | Medium | YES |
| Batch pen setting | 43 | +8% | Easy | YES |
| Reduce allocations | 45 | +5% | Easy | YES |
| Cache calculations | 46 | +2% | Easy | Maybe |
| *Total* | *46* | *+64%* | - | - |




### Premature Optimisation

```python
# DON'T: Precompute everything
PLAYER_SPEED = int(3 * SCALE)  # Impact: 0.001ms
BULLET_SIZE = int(2 * SCALE)   # Impact: 0.001ms
SPACING_X = int(20 * SCALE)    # Impact: 0.001ms
# Total savings: 0.003ms = useless in this case!

# DO: Keep it simple
player_speed = 3 * SCALE  # Computed once anyway
```

### Micro-Optimisations

```python
# DON'T: Use cryptic code for 0.1% speedup
if not any(inv['alive'] for inv in invaders):  # "Optimised"
    
# DO: Use clear code
all_dead = True
for inv in invaders:
    if inv['alive']:
        all_dead = False
        break
# Same performance, much clearer
```




### Baseline (Clean & Fast Enough)

```python
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2, PEN_RGB565
from pimoroni import Button
import time

display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, pen_type=PEN_RGB565)
WIDTH, HEIGHT = display.get_bounds()

# Simple, clear constants
SCALE = 1.5 if WIDTH == 320 else 1.0

# Colors
BLACK = display.create_pen(0, 0, 0)
WHITE = display.create_pen(255, 255, 255)
GREEN = display.create_pen(0, 255, 0)

# Game objects
player = {'x': WIDTH//2, 'y': HEIGHT - 30, 'width': 20, 'height': 10}
invaders = []
bullets = []

def update():
    # Update bullets - use list comprehension (clean & fast)
    bullets[:] = [b for b in bullets if 0 <= b['y'] <= HEIGHT]
    
    for bullet in bullets:
        bullet['y'] -= 5
    
    # .. rest of logic

def draw():
    display.set_pen(BLACK)
    display.clear()
    
    # OPTIMISATION: Batch pen setting
    display.set_pen(WHITE)
    display.rectangle(player['x'], player['y'], 
                     player['width'], player['height'])
    
    # OPTIMISATION: Group by color
    display.set_pen(GREEN)
    for inv in green_invaders:
        # OPTIMISATION: Simple shapes instead of pixel-by-pixel
        display.rectangle(inv['x'], inv['y'], inv['width'], inv['height'])
    
    display.update()

# Main loop
while True:
    update()
    draw()
    time.sleep(0.02)  # ~50 FPS target
```



### How to Profile Code

```python
import time

def profile_frame():
    # Measure game logic
    start = time.ticks_ms()
    update()
    logic_ms = time.ticks_diff(time.ticks_ms(), start)
    
    # Measure rendering
    start = time.ticks_ms()
    draw()
    render_ms = time.ticks_diff(time.ticks_ms(), start)
    
    total_ms = logic_ms + render_ms
    
    print(f"Logic: {logic_ms}ms, Render: {render_ms}ms, Total: {total_ms}ms")
    
# Run every second
frame_count = 0
last_profile = time.ticks_ms()

while True:
    if time.ticks_diff(time.ticks_ms(), last_profile) >= 1000:
        profile_frame()
        last_profile = time.ticks_ms()
    else:
        update()
        draw()
```

*Typical results:*
```
Logic: 3ms, Render: 22ms, Total: 25ms
         ^^^^^^^^^^^^
         This is the bottleneck!
```



### Golden Rules for Pico Optimisation

#### 1. Profile First
Don't guess what's slow - measure it!

#### 2. Fix the Bottleneck
If rendering is 80% of frame time, optimise rendering.  
Don't waste time optimising the 5% game logic.

#### 3. Prefer Clarity
```python
# This is 0.1% faster but 100% harder to read:
bullets = [b for b in bullets if not (b['y'] < 0 or b['y'] > HEIGHT)]

# This is clear and almost as fast:
bullets = [b for b in bullets if 0 <= b['y'] <= HEIGHT]
```

#### 4. Know When to Stop
- 30 FPS = Playable
- 40 FPS = Smooth
- 50+ FPS = Diminishing returns (Pico can't update display faster anyway)


