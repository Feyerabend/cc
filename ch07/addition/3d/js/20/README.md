
## 3D Raycasting World

This is a *raycasting engine* that creates a 3D first-person view from a 2D map,
similar to classic games like Wolfenstein 3D (1992) and early Doom. The rendering
technique creates the illusion of 3D using only 2D calculations and clever projection.


### The Core Concept

Raycasting simulates 3D by casting rays from the player's position in the direction
they're looking. Each ray travels until it hits a wall, and the distance determines
how tall to draw that wall slice on screen.

```
Player view angle: 60° FOV (Field of View)
     /‾‾‾‾‾‾‾‾‾\
    /           \
   /   Camera    \
  /    Position   \
 /                 \
└-------------------┘
    Screen (800px)
```


### Step-by-Step Rendering Process

#### 1. *Ray Casting* (Wall Detection)

For each vertical column on the screen (800 rays for 800px width):

```javascript
// Calculate ray angle for this column
const rayAngle = player.angle - FOV/2 + (column / screenWidth) * FOV;

// Cast ray using DDA (Digital Differential Analysis)
let distance = 0;
while (!hitWall && distance < MAX_DEPTH) {
    distance += 0.5;  // Step forward
    
    // Calculate world position
    const testX = player.x + cos(rayAngle) * distance;
    const testY = player.y + sin(rayAngle) * distance;
    
    // Check if we hit a wall in the 2D map
    const mapX = floor(testX / TILE_SIZE);
    const mapY = floor(testY / TILE_SIZE);
    
    if (map[mapY][mapX] === 1) {
        hitWall = true;
    }
}
```


#### 2. *Fish-Eye Correction*

Raw distances create a "fish-eye" distortion effect.
We correct this by projecting onto the view plane:

```javascript
// Without correction: walls appear curved
const rawDistance = distance;

// With correction: straight walls
const correctedDistance = distance * cos(rayAngle - player.angle);
```

*Why this works:*
- Rays at the edge of FOV travel at an angle
- They measure diagonal distance (longer than perpendicular)
- Multiplying by cosine projects onto the perpendicular view plane

```
        Wall
         |
    d    |
   /‾\   |
  / α \  |
 /     \ |
Player   |
         |

corrected_d = d * cos(α)
```

#### 3. *Wall Height Calculation*

Walls appear taller when closer, shorter when far away. This uses *perspective projection*:

```javascript
const wallHeight = (TILE_SIZE * screenHeight) / correctedDistance;
```

*The math:*
- `TILE_SIZE` = actual wall height in world units (64 units)
- `screenHeight` = screen resolution (600px)
- Division by distance = perspective scaling
- When distance is small → wallHeight is large
- When distance is large → wallHeight is small


#### 4. *Vertical Centering*

Walls are drawn centered vertically on screen to simulate eye-level view:

```javascript
const wallTop = (screenHeight - wallHeight) / 2;
const wallBottom = wallTop + wallHeight;

// Draw wall stripe
ctx.fillRect(column, wallTop, 1, wallHeight);
```


#### 5. *Distance-Based Shading*

Walls fade to darkness with distance to create depth perception:

```javascript
const brightness = max(0, 255 - (distance / MAX_DEPTH) * 255);
const color = rgb(brightness, brightness * 0.5, brightness * 0.5);
```

This simulates *fog* or *atmospheric perspective* - a natural depth cue.


### The Z-Buffer

For proper object rendering (sprites), we store the distance of each screen column:

```javascript
const zBuffer = new Array(screenWidth);

// During wall rendering
for (let x = 0; x < screenWidth; x++) {
    const distance = castRay(angle);
    zBuffer[x] = distance;  // Store for later
    
    // Draw wall..
}

// Later, when drawing sprites
if (spriteDistance < zBuffer[x]) {
    // Sprite is closer than wall, draw it
    drawSpriteColumn(x);
}
```

This ensures sprites appear *behind* walls when appropriate.


### The 2D Map Representation

The world is stored as a 2D array:

```javascript
const map = [
    [1,1,1,1,1,1],  // 1 = Wall
    [1,0,0,0,0,1],  // 0 = Empty space
    [1,0,0,0,0,1],
    [1,0,0,0,0,1],
    [1,1,1,1,1,1]
];

const TILE_SIZE = 64;  // Each tile is 64x64 units
```

*Player position* is in world coordinates:
- `player.x = 128` = 2 tiles from left edge
- `player.y = 128` = 2 tiles from top edge

*Collision detection* checks tiles around player position:

```javascript
const mapX = floor(player.x / TILE_SIZE);
const mapY = floor(player.y / TILE_SIZE);

if (map[mapY][mapX] === 1) {
    // Collision! Can't move here
}
```


### Performance Optimisations

### 1. Fixed Step Size
Instead of checking every pixel, we step by 0.5 units:
```javascript
distance += 0.5;  // Balance between accuracy and speed
```

### 2. Maximum Depth
Stop casting when rays go too far:
```javascript
if (distance > MAX_DEPTH) break;
```

### 3. Single Pixel Columns
Each ray draws exactly 1 pixel wide column:
```javascript
ctx.fillRect(x, y, 1, height);  // Width = 1
```


### Mathematical Foundations

#### Trigonometry

The engine heavily uses sine and cosine for direction calculations:

```javascript
// Convert angle to direction vector
const dx = cos(angle);  // X component
const dy = sin(angle);  // Y component

// Move in that direction
newX = x + dx * speed;
newY = y + dy * speed;
```

#### Perspective Projection

The fundamental perspective equation:

```
screen_size = (real_size * screen_distance) / world_distance

Rearranged:
screen_size = (real_size * constant) / world_distance
```

In code:
```javascript
wallHeight = (TILE_SIZE * screenHeight) / distance;
```

### Ceiling and Floor

Currently rendered as flat colors:

```javascript
// Ceiling (top half)
ctx.fillStyle = '#2a2a3a';
ctx.fillRect(0, 0, width, height/2);

// Floor (bottom half)  
ctx.fillStyle = '#4a4a4a';
ctx.fillRect(0, height/2, width, height/2);
```

*Could be enhanced with:*
- Texture mapping (like floor tiles)
- Distance-based shading
- Reflections


### Input and Movement

#### Rotation
```javascript
if (keyPressed('LEFT'))  player.angle -= TURN_SPEED;
if (keyPressed('RIGHT')) player.angle += TURN_SPEED;
```

#### Movement
```javascript
// Calculate movement vector based on view direction
const moveX = cos(player.angle) * MOVE_SPEED;
const moveY = sin(player.angle) * MOVE_SPEED;

// Apply with collision detection
if (!isColliding(player.x + moveX, player.y)) {
    player.x += moveX;
}
```

*Separate X/Y collision* allows sliding along walls instead of getting stuck.

### Limitations of Raycasting

#### What Raycasting CAN do:
- Vertical walls of uniform height
- Fast rendering (simple calculations)
- Atmospheric lighting/fog
- Sprite objects (billboards)

### What Raycasting CANNOT do:
- Looking up/down (no Y-axis rotation)
- Rooms above rooms (no height variation)
- Sloped walls or floors
- Curved surfaces
- Complex 3D geometry

For these features, you need full *3D polygon rendering* (like Quake, modern 3D engines).


### Game Loop

The main rendering cycle:

```javascript
function gameLoop() {
    updatePlayer();      // Handle input, update position
    render3D();          // Cast rays, draw walls
    renderSprites();     // Draw objects (see separate docs)
    renderMinimap();     // Top-down 2D view
    requestAnimationFrame(gameLoop);  // ~60 FPS
}
```


### Coordinate Systems

#### World Space
- Origin (0,0) at top-left
- X increases right
- Y increases down
- Units: arbitrary (typically 64 units = 1 tile)

#### Screen Space
- Origin (0,0) at top-left
- X increases right  
- Y increases down
- Units: pixels

#### Angles
- 0 radians = facing right (+X)
- π/2 radians = facing down (+Y)
- π radians = facing left (-X)
- 3π/2 radians = facing up (-Y)



### Try It Yourself

Experiment with these constants to see how they affect rendering:

```javascript
const FOV = Math.PI / 3;        // Try π/4 (narrow) or π/2 (wide)
const NUM_RAYS = canvas.width;  // Try 400 for pixelated look
const TILE_SIZE = 64;           // Try 32 (larger world) or 128 (smaller)
const MAX_DEPTH = 800;          // Try 400 (more fog) or 1600 (see further)
```



*Note*: Object/sprite rendering uses a different technique
(billboard sprites with z-buffering) and is documented
in [SPRITES.md](./SPRITES.md).
