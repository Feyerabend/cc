
## 3D Raycasting World with OBJ Model Sprites

This is a *raycasting engine* that creates a 3D first-person view
from a 2D map, similar to classic games like Wolfenstein 3D (1992)
and early Doom. The rendering technique creates the illusion of 3D
using only 2D calculations and clever projection. This version builds
on the core engine by incorporating billboard sprites rendered from
OBJ 3D models, transforming them into multi-angle 2D images for
real-time performance.

*Read the Web Workers documentation first if comparing to raytracing demos*--this
focuses on raycasting and sprite systems.


### From Raytracing to Raycasting

Previous demos used *raytracing*—simulating light physics
for photorealistic rendering:
- Multiple ray bounces per pixel
- Reflections, shadows, lighting calculations
- Slow but accurate (~30-60 FPS with workers)

This demo uses *raycasting*—a simplified technique for real-time 3D:
- One ray per vertical screen column
- No reflections or secondary rays
- Fast rendering suitable for games (~60+ FPS)

```
Raytracing (workers.html)     Raycasting (3d-world-sprites.html)
     ┌---┐                            ┌---┐
     │ ● │ Per pixel                  │ ● │ Per column
     └---┘                            └---┘
    ██████ 400×400 = 160K rays        ████ 800 rays
```

### The Core Concept

Raycasting simulates 3D by casting rays from the player's position
in the direction they're looking. Each ray travels until it hits a
wall, and the distance determines how tall to draw that wall slice
on screen.

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

Walls appear taller when closer, shorter when far away.
This uses *perspective projection*:

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


### Single-threaded Implementation

Unlike raytracing demos, this runs on a *single thread*:
- No Web Workers
- Direct canvas manipulation
- Simpler code architecture

*Why?*
- Raycasting is ~1000× faster than raytracing
- 800 rays vs 160,000 ray calculations
- Single thread easily achieves 60 FPS


### The 2D Map Representation: Grid-Based Level

The world is stored as a 2D array:
```javascript
const map = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    // .. 16×16 grid
];

const TILE_SIZE = 64;  // Each tile is 64x64 units
```

*Format:*
- `1` = wall (solid)
- `0` = empty (walkable)
- Each cell is 64×64 pixels

*Map structure:*
- Outer walls form boundary
- Interior rooms and corridors
- Simple collision detection

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


### Player Movement System: WASD Controls

```javascript
const player = {
    x: TILE_SIZE * 2,        // Position in pixels
    y: TILE_SIZE * 2,
    angle: 0,                // Viewing direction (radians)
    moveSpeed: 3,            // Pixels per frame
    turnSpeed: 0.05          // Radians per frame
};
```


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
if (!isColliding(player.x, player.y + moveY)) {
    player.y += moveY;
}
```

*Separate X/Y collision* allows sliding along walls instead of getting stuck.

```javascript
function isColliding(x, y) {
    const mapX = Math.floor(x / TILE_SIZE);
    const mapY = Math.floor(y / TILE_SIZE);
    return map[mapY][mapX] === 1;
}
```


### Wall Rendering: Vertical Strips

```javascript
for (let i = 0; i < NUM_RAYS; i++) {
    const rayAngle = player.angle - FOV / 2 + (i / NUM_RAYS) * FOV;
    const distance = castRay(rayAngle);
    const correctedDistance = distance * Math.cos(rayAngle - player.angle);
    
    // Calculate wall height
    const wallHeight = (TILE_SIZE * canvas.height) / (correctedDistance + 0.0001);
    const brightness = Math.max(0, 255 - (correctedDistance / MAX_DEPTH) * 255);
    
    // Draw vertical line
    ctx.fillStyle = `rgb(${brightness * 0.8}, ${brightness * 0.4}, ${brightness * 0.4})`;
    ctx.fillRect(i, (canvas.height - wallHeight) / 2, 1, wallHeight);
}
```

*Process:*
1. For each screen column (800 columns)
2. Cast ray at appropriate angle
3. Calculate wall height (inversely proportional to distance)
4. Dim walls based on distance (fog effect)
5. Draw centered vertical strip


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


### The Z-Buffer: Depth Information

For proper object rendering (sprites),
we store the distance of each screen column:

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

*Purpose:* Store distance-to-wall for each screen column.

*Used later for:* Determining if sprites are behind walls.

```
Screen column:  0   1   2   3   4    ...
Z-buffer:     [120, 95, 80, 85, 110, ...]
              (distance to wall)
```


### Sprite System: Billboard Objects

*Sprites* are 2D images that always face the player (billboarding).

```javascript
const objects = [
    { x: TILE_SIZE * 6.5, y: TILE_SIZE * 2.5, radius: 25 },
    { x: TILE_SIZE * 9.5, y: TILE_SIZE * 4.5, radius: 25 },
    // ... more objects
];
```

#### Why Sprites?

*Classic 3D game technique:*
- *DOOM* (1993)—enemies, items, decorations
- *Duke Nukem 3D* (1996)—monsters, props
- *Blood* (1997)—NPCs, pickups

*Advantages:*
- Much faster than 3D models
- Artistic freedom (hand-drawn)
- Simple to implement

*Disadvantage:*
- Look flat from side angles


### Sprite Rendering Pipeline

```javascript
// 1. Calculate sprite visibility
const visibleObjects = objects
    .map(obj => {
        const dx = obj.x - player.x;
        const dy = obj.y - player.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        const angle = Math.atan2(dy, dx);
        return { obj, distance, angle };
    })
    .filter(({ distance }) => distance < MAX_DEPTH)
    .sort((a, b) => b.distance - a.distance);  // Far to near
```

*Sorting* ensures distant objects are drawn before near objects (painter's algorithm).

#### Sprite Screen Position

```javascript
let relativeAngle = angle - player.angle;

// Normalize to -π to π
while (relativeAngle < -Math.PI) relativeAngle += Math.PI * 2;
while (relativeAngle > Math.PI) relativeAngle -= Math.PI * 2;

// Check if in FOV
if (Math.abs(relativeAngle) > FOV / 2 + 0.5) continue;

// Calculate screen position
const spriteScreenX = (relativeAngle / FOV + 0.5) * canvas.width;
```

#### Sprite Size

```javascript
const spriteHeight = (TILE_SIZE * canvas.height) / (distance + 0.0001);
const spriteWidth = spriteHeight;  // Square sprites
```

*Same formula as walls*—distant objects appear smaller.

#### Z-Buffer Integration: Visibility Check

```javascript
for (let x = Math.max(0, startX); x < Math.min(canvas.width, endX); x++) {
    // Z-buffer check
    if (distance < zBuffer[x]) {
        // Sprite is in front of wall—draw it
        ctx.drawImage(sprite, texX, 0, 1, sprite.height, x, y, 1, spriteHeight);
    } else {
        // Wall is in front—skip this column
    }
}
```

*Column-by-column rendering:*
- Check if sprite is closer than wall at this column
- Draw if closer, skip if behind
- Allows sprites to be partially occluded


### OBJ Model Loading: 3D to Sprite Conversion

This is the *key addition*—loading actual 3D models and converting them to sprites.

```javascript
document.getElementById('objUpload').addEventListener('change', (event) => {
    const file = event.target.files[0];
    const reader = new FileReader();
    reader.onload = (e) => {
        parseOBJ(e.target.result);
    };
    reader.readAsText(file);
});
```

#### OBJ Format Parsing

```javascript
function parseOBJ(text) {
    const lines = text.split('\n');
    const vertices = [];
    const normals = [];
    const faces = [];
    
    for (const line of lines) {
        const parts = line.trim().split(/\s+/);
        
        if (parts[0] === 'v') {
            // Vertex: v x y z
            vertices.push([
                parseFloat(parts[1]),
                parseFloat(parts[2]),
                parseFloat(parts[3])
            ]);
        } else if (parts[0] === 'vn') {
            // Normal: vn x y z
            normals.push([
                parseFloat(parts[1]),
                parseFloat(parts[2]),
                parseFloat(parts[3])
            ]);
        } else if (parts[0] === 'f') {
            // Face: f v1/vt1/vn1 v2/vt2/vn2 v3/vt3/vn3
            // Parse triangles
        }
    }
}
```

*OBJ is a text format:*
- `v` lines define vertices (3D points)
- `vn` lines define normals (surface directions)
- `f` lines define faces (triangles connecting vertices)


#### WebGL Rendering: 3D Model to Image

```javascript
function initWebGL() {
    modelCanvas = document.createElement('canvas');
    modelCanvas.width = 128;
    modelCanvas.height = 128;
    modelGL = modelCanvas.getContext('webgl', { 
        alpha: true, 
        antialias: true,
        preserveDrawingBuffer: true 
    });
}
```

*WebGL* is used to render the 3D model to an offscreen canvas.


#### Shaders

```glsl
// Vertex shader
attribute vec4 aVertexPosition;
attribute vec3 aVertexNormal;
uniform mat4 uModelViewMatrix;
uniform mat4 uProjectionMatrix;
void main() {
    gl_Position = uProjectionMatrix * uModelViewMatrix * aVertexPosition;
    vNormal = (uNormalMatrix * vec4(aVertexNormal, 0.0)).xyz;
}

// Fragment shader
void main() {
    vec3 lightDir = normalize(vec3(0.5, 1.0, 0.8));
    float diff = max(dot(normalize(vNormal), lightDir), 0.0);
    vec3 baseColor = vec3(0.2, 0.5, 0.8);
    gl_FragColor = vec4(baseColor * (0.4 + diff * 0.8), 1.0);
}
```

*Simple lighting:* Ambient + diffuse shading.


#### Multi-Angle Pre-rendering

```javascript
function generateSpritesFromModel(modelData) {
    const numAngles = 8;  // 8 directions (45° each)
    const sprites = [];
    
    for (let i = 0; i < numAngles; i++) {
        const angle = (i / numAngles) * Math.PI * 2;
        
        // Rotate camera around model
        const radius = 2.5;
        const cameraX = Math.cos(angle) * radius;
        const cameraZ = Math.sin(angle) * radius;
        
        // Render from this angle
        renderModelToCanvas(modelData, cameraX, 0, cameraZ);
        
        // Extract as image
        const img = new Image();
        img.src = modelCanvas.toDataURL();
        sprites.push(img);
    }
    
    return sprites;
}
```

*Process:*
1. Render model from 8 different angles (360° / 8 = 45° apart)
2. Each render produces a 128×128 image
3. Store as sprite array
4. During gameplay, select closest angle


#### Sprite Angle Selection

```javascript
// Calculate which sprite angle to show
const dx = obj.x - player.x;
const dy = obj.y - player.y;
const angleToObject = Math.atan2(dy, dx);

// Rotate by 180° since we want the side facing the player
let viewAngle = angleToObject + Math.PI;

// Normalize to 0 to 2π
while (viewAngle < 0) viewAngle += Math.PI * 2;
while (viewAngle >= Math.PI * 2) viewAngle -= Math.PI * 2;

const spriteIndex = Math.floor((viewAngle / (Math.PI * 2)) * obj.sprites.length);
const sprite = obj.sprites[spriteIndex];
```

*Example:* Player at 0°, object at 45°
- `angleToObject = 45°`
- `viewAngle = 45° + 180° = 225°`
- `spriteIndex = floor((225° / 360°) × 8) = floor(5) = 5`
- Use sprite[5]


#### Model Normalisation: Fitting to View

```javascript
// Find bounding box
let minX = Infinity, maxX = -Infinity;
let minY = Infinity, maxY = -Infinity;
let minZ = Infinity, maxZ = -Infinity;

for (const vertex of vertices) {
    minX = Math.min(minX, vertex[0]);
    maxX = Math.max(maxX, vertex[0]);
    // ... same for Y and Z
}

// Calculate center and scale
const centerX = (minX + maxX) / 2;
const centerY = (minY + maxY) / 2;
const centerZ = (minZ + maxZ) / 2;
const scale = 1.0 / Math.max(maxX - minX, maxY - minY, maxZ - minZ);

// Normalize vertices
for (let i = 0; i < vertices.length; i++) {
    vertices[i][0] = (vertices[i][0] - centerX) * scale;
    vertices[i][1] = (vertices[i][1] - centerY) * scale;
    vertices[i][2] = (vertices[i][2] - centerZ) * scale;
}
```

*Purpose:* Models come in arbitrary sizes—normalize to fit in [-0.5, 0.5] cube.


### Minimap System: Top-Down View

```javascript
function renderMinimap() {
    const scale = minimap.width / (MAP_SIZE * TILE_SIZE);
    
    // Draw walls
    for (let y = 0; y < MAP_SIZE; y++) {
        for (let x = 0; x < MAP_SIZE; x++) {
            if (map[y][x] === 1) {
                mmCtx.fillStyle = '#666';
                mmCtx.fillRect(
                    x * TILE_SIZE * scale,
                    y * TILE_SIZE * scale,
                    TILE_SIZE * scale,
                    TILE_SIZE * scale
                );
            }
        }
    }
    
    // Draw objects
    mmCtx.fillStyle = '#44f';
    for (const obj of objects) {
        mmCtx.beginPath();
        mmCtx.arc(obj.x * scale, obj.y * scale, 4, 0, Math.PI * 2);
        mmCtx.fill();
    }
    
    // Draw player
    mmCtx.fillStyle = '#0f0';
    mmCtx.beginPath();
    mmCtx.arc(player.x * scale, player.y * scale, 5, 0, Math.PI * 2);
    mmCtx.fill();
}
```

*Shows:*
- Gray walls
- Blue object positions
- Green player with direction indicator


### Performance Optimisations

#### 1. Fixed Step Size
Instead of checking every pixel, we step by 0.5 units:
```javascript
distance += 0.5;  // Balance between accuracy and speed
```

#### 2. Maximum Depth
Stop casting when rays go too far:
```javascript
if (distance > MAX_DEPTH) break;
```

#### 3. Single Pixel Columns
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

### From 2D to Pseudo-3D: The Technique

*Raycasting is 2.5D:*
- World is 2D grid (map array)
- Rendering produces 3D perspective view
- Walls are infinitely tall (no height variation)
- Floor and ceiling are flat planes


### Limitations of Raycasting

#### What Raycasting CAN do:
- Vertical walls of uniform height
- Fast rendering (simple calculations)
- Atmospheric lighting/fog
- Sprite objects (billboards)

#### What Raycasting CANNOT do:
- Looking up/down (no Y-axis rotation)
- Rooms above rooms (no height variation)
- Sloped walls or floors
- Curved surfaces
- Complex 3D geometry

For these features, you need full *3D polygon rendering*
(like Quake, modern 3D engines).


### Performance Characteristics

*Raycasting (this demo):*
- FPS: 60+ (capped by requestAnimationFrame)
- CPU: ~5-10% (single core)
- 800 ray calculations per frame
- No multi-threading needed

*Raytracing (previous demo):*
- FPS: 30-60 (with 4 workers)
- CPU: 100% (all cores)
- 160,000 ray calculations per frame
- Required Web Workers for reasonable FPS

*Speedup:* ~200× reduction in computation (800 vs 160,000 rays)


### Key Architecture Differences

| Aspect | Raytracer (workers.html) | Raycaster (3d-world-sprites.html) |
|--------|--------------------------|-----------------------------------|
| *Threading* | Multi-threaded (Web Workers) | Single-threaded |
| *Rendering* | Physics-accurate raytracing | Fast grid-based raycasting |
| *Rays* | 160,000 per frame | 800 per frame |
| *Scene* | Floating sphere | Grid-based level |
| *Objects* | Raytraced sphere | Billboard sprites |
| *Movement* | Animated sphere | Player control (WASD) |
| *Performance* | 30-60 FPS (CPU-intensive) | 60+ FPS (lightweight) |
| *Use case* | Realistic rendering | Real-time games |


### Historical Context: The Raycasting Era

*Wolfenstein 3D (1992):*
- First mainstream raycasting game
- Grid-based levels
- 90° walls only
- No floor/ceiling textures
- Sprite enemies

*DOOM (1993):*
- Enhanced "DOOM engine"
- Non-orthogonal walls
- Height variation
- Textured floors/ceilings
- Multiple light levels

*This demo:* Similar to Wolfenstein approach—pure raycasting with sprite objects.


### Modern Applications

*Where raycasting still shines:*
- Retro game development
- Mobile games (low CPU overhead)
- Educational projects
- Prototyping 3D games
- Embedded systems

*When to use modern 3D instead:*
- True 3D environments needed
- Complex geometry
- Modern graphics features
- Non-grid-based worlds


### Try It Yourself

Experiment with these constants to see how they affect rendering:

```javascript
const FOV = Math.PI / 3;        // Try π/4 (narrow) or π/2 (wide)
const NUM_RAYS = canvas.width;  // Try 400 for pixelated look
const TILE_SIZE = 64;           // Try 32 (larger world) or 128 (smaller)
const MAX_DEPTH = 800;          // Try 400 (more fog) or 1600 (see further)
```


### Extension Ideas

*Enhance the world:*
- Add textured walls (sample from texture images)
- Different wall heights
- Doors and animated walls
- Multiple floor levels

*Improve sprites:*
- More angles (16 or 32 instead of 8)
- Animated sprites (walking, attacking)
- Multiple 3D models per object type
- Sprite scaling and effects

*Add gameplay:*
- Enemy AI (pathfinding on grid)
- Shooting mechanics
- Item collection
- Health system
- Level progression

*Technical improvements:*
- DDA algorithm (faster raycasting)
- Texture mapping on walls
- Dynamic lighting
- Particle effects
- Sound spatialisation
