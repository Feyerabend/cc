
## Game Programming Projects

### Key Enhancements:
1. *Procedural Map Generation* - Creates rooms and corridors instead of random walls
2. *Better AI* - Line-of-sight detection, memory of last seen position
3. *Game Systems* - Score, health, collectibles, HUD
4. *Performance* - Optimized rendering, bot updates every other frame
5. *Color Palette* - Organized color management
6. *Collision Response* - Proper damage and pushback mechanics



### Project 1: *Memory-Constrained Snake*
*Focus*: Memory management, circular buffers

*Concepts to Learn*:
- Fixed-size arrays vs dynamic lists
- Ring buffers for efficient tail tracking
- Memory profiling on microcontrollers

*Implementation Challenge*:
```python
# Store only tail positions that changed direction
# Instead of full body array (memory intensive)
tail_segments = [(x, y, direction), ...]  # Max 50 segments
```

*Extensions*:
- Add walls that grow as you eat
- Multiple food types (speed boost, score multiplier)
- 2-player competitive mode



### Project 2: *Reaction Time Trainer*
*Focus*: Timing, interrupts, state machines

*Core Mechanic*:
- Random stimulus appears (color, position)
- Player presses matching button
- Measure reaction time in milliseconds

*What You'll Learn*:
- `utime.ticks_ms()` for precise timing
- Button debouncing
- Statistical tracking (average, best time)
- Visual feedback patterns

*Challenge Mode*: 
- Simon Says memory game
- Decreasing time windows
- Multi-button combos



### Project 3: *Light & Shadow Stealth Game*
*Focus*: Visibility algorithms, sensor integration

*Core Mechanic*:
```python
# Light sources create "safe zones"
lights = [(x, y, radius), ...]

def is_lit(px, py):
    for lx, ly, r in lights:
        if distance(px, py, lx, ly) < r:
            return True
    return False

# Enemies only detect you in lit areas
```

*What You'll Learn*:
- Raycasting for shadows
- Alert states (patrol -> investigate -> chase)
- Tile-based fog of war
- Power management (lights flicker = low battery simulation)

*Hardware Extension*:
- Use real light sensor (BH1745) to affect in-game lighting
- Vibration feedback via piezo buzzer



### Project 4: *Procedural Dungeon Crawler*
*Focus*: Algorithm design, data structures

*Concepts*:
```python
# Cellular automata for cave generation
def cave_step(world):
    new_world = copy(world)
    for y, x in all_tiles:
        neighbors = count_walls_around(x, y)
        if neighbors > 4:
            new_world[y][x] = 1  # Become wall
        elif neighbors < 4:
            new_world[y][x] = 0  # Become floor
    return new_world

# BSP tree for room-based dungeons
def split_recursive(rect, min_size=4):
    if too_small(rect): return
    split_horizontal = random_choice()
    rect1, rect2 = split(rect, split_horizontal)
    split_recursive(rect1)
    split_recursive(rect2)
```

*What You'll Learn*:
- Binary Space Partitioning
- Cellular automata
- A* pathfinding for enemy AI
- Inventory system in limited RAM



### Project 5: *Physics Puzzle Game*
*Focus*: Fixed-point math, collision detection

*Core Systems*:
```python
# Fixed-point arithmetic (no floating point!)
# Store as integers: value * 256
class FixedPoint:
    def __init__(self, value):
        self.raw = int(value * 256)
    
    def add(self, other):
        return FixedPoint.from_raw(self.raw + other.raw)

# Box physics with velocity
box = {
    "x": 100 << 8,  # Fixed point
    "y": 100 << 8,
    "vx": 0,
    "vy": 0,
    "mass": 5
}
```

*What You'll Learn*:
- Fixed-point arithmetic on microcontrollers
- Verlet integration for physics
- SAT collision detection for rotated boxes
- Constraint solving (ropes, hinges)

*Game Ideas*:
- Stack boxes to reach goal
- Chain reaction puzzle (dominoes)
- Angry Birds style projectile physics



### Project 6: *Networked Multiplayer via I2C/SPI*
*Focus*: Communication protocols, synchronization

*Architecture*:
```python
# One Pico is "server", others are clients
# Server broadcasts game state every frame

# Protocol design
packet = {
    "type": "STATE",  # or "INPUT", "EVENT"
    "frame": 12345,
    "data": {
        "players": [(x1,y1), (x2,y2)],
        "entities": [...]
    }
}

# Client sends inputs only
input_packet = {
    "type": "INPUT",
    "frame": 12345,
    "buttons": 0b00001010  # Bitfield
}
```

*What You'll Learn*:
- I2C multi-master communication
- Packet serialization (struct module)
- Clock synchronization
- Handling dropped packets
- Latency hiding (client prediction)

*Game Ideas*:
- 2-4 player tag
- Cooperative puzzle solving
- Racing game with ghosts



### Project 7: *Raycasting 3D Engine*
*Focus*: Graphics optimization, DDA algorithm

*Core Concept*:
```python
# Cast rays for each screen column
for x in range(WIDTH):
    angle = player_angle + FOV * (x/WIDTH - 0.5)
    
    # DDA ray marching
    ray_x, ray_y = player_x, player_y
    step_x = cos(angle) * 0.1
    step_y = sin(angle) * 0.1
    
    distance = 0
    while not is_wall(ray_x, ray_y):
        ray_x += step_x
        ray_y += step_y
        distance += 0.1
    
    # Draw vertical line (wall slice)
    height = HEIGHT / distance
    draw_line(x, HEIGHT/2 - height/2, height)
```

*Optimizations*:
- Pre-calculated sin/cos lookup tables
- Integer-only DDA
- Distance fog (far walls = darker)
- Texture mapping with bit shifting

*What You'll Learn*:
- Ray-plane intersection math
- Perspective projection
- Lookup tables for trig
- Vertical scanline rendering



### Project 8: *AI Behavior Trees & FSM*
*Focus*: AI architecture, decision systems

*Behavior Tree Example*:
```python
class BehaviorNode:
    def execute(self, bot): pass

class Sequence:
    def execute(self, bot):
        for child in self.children:
            if child.execute(bot) == FAIL:
                return FAIL
        return SUCCESS

# Tree structure:
# Selector (OR)
#   ├─ Sequence (AND)
#   │   ├─ CanSeePlayer?
#   │   ├─ IsHealthLow?
#   │   └─ FleeFromPlayer
#   ├─ Sequence
#   │   ├─ CanSeePlayer?
#   │   └─ ChasePlayer
#   └─ Patrol
```

*What You'll Learn*:
- Finite State Machines vs Behavior Trees
- Utility-based AI (scoring actions)
- Goal-Oriented Action Planning (GOAP)
- Emergence from simple rules

*Extensions*:
- Squad tactics (flanking, covering)
- Dynamic difficulty adjustment
- Learning enemy patterns (simple ML)





### *1. Performance Profiling*
```python
import time

def profile(func):
    start = time.ticks_us()
    func()
    duration = time.ticks_diff(time.ticks_us(), start)
    print(f"{func.__name__}: {duration}us")

profile(draw_world)  # Find bottlenecks
```

### *2. Bitmasking for Tile Properties*
```python
# Pack multiple properties in one byte
SOLID = 0b00000001
WATER = 0b00000010
LAVA =  0b00000100
DOOR =  0b00001000

tile = SOLID | LAVA  # Solid lava
if tile & SOLID: print("Can't walk through")
```

### *3. Double Buffering*
```python
# Prevent screen tearing
buffer_a = bytearray(...)
buffer_b = bytearray(...)

current = buffer_a
display.init(current)

# Swap buffers each frame
current = buffer_b if current == buffer_a else buffer_a
display.init(current)
```

### *4. Save System (Flash Memory)*
```python
import flashbdev
import os

# Write high score to flash
with open('save.dat', 'wb') as f:
    f.write(struct.pack('III', score, level, time))

# Read back
with open('save.dat', 'rb') as f:
    score, level, time = struct.unpack('III', f.read(12))
```



### Learning Path Recommendation

1. *Week 1-2*: Modify base code (change colors, speeds, AI behavior)
2. *Week 3-4*: Build Snake or Reaction Trainer from scratch
3. *Week 5-6*: Implement procedural generation
4. *Week 7-8*: Add physics or networking
5. *Week 9+*: Build your own game concept

Pick one project and add:
- *Persistent storage* (save system)
- *Sound effects* (piezo buzzer)
- *External sensors* (temperature affects game speed)
- *Power optimization* (run on battery for 8+ hours)
- *Multiplayer* (wire two Picos together)



#### Debugging Tips for Microcontrollers

```python
# 1. Visual debugging (no print!)
display.set_pen(255, 0, 0)
display.circle(debug_x, debug_y, 3)  # Show problem coordinate

# 2. Simple profiler
frame_times = []
def log_frame(ms):
    frame_times.append(ms)
    if len(frame_times) > 60:
        avg = sum(frame_times) / 60
        print(f"Avg: {avg}ms")
        frame_times.clear()

# 3. State visualization
display.text(f"State:{bot['state']}", 0, 10, scale=1)

# 4. Memory check
import gc
gc.collect()
print(f"Free RAM: {gc.mem_free()} bytes")
```


### Resources

- *MicroPython Docs*: [docs.micropython.org](https://docs.micropython.org)
- *Pimoroni Libraries*: [github.com/pimoroni](https://github.com/pimoroni)
- *Game Dev Math*: gamemath.com
- *Fixed-Point Guide*: [embedded.com fixed-point guide](https://www.embedded.com/how-to-use-fixed-point-arithmetic/)

