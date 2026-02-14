
## Sprite Rendering in Raycasting

While walls are rendered using raycasting, *objects* (enemies, items, decorations)
use a completely different technique called *billboard sprites*. This document
explains how 3D models are converted to sprites and rendered in the raycasting world.

*Problem*: Raycasting works great for walls because:
- Walls are vertical and aligned to a grid
- We can check map tiles efficiently
- Walls are always at right angles

*But objects are different:*
- They can be anywhere in the world (not grid-aligned)
- They have complex shapes (not simple rectangles)
- They need to show different sides as you walk around them

*Solution*: Pre-render objects as 2D sprites and display them as
*billboards* (always facing the camera).


### The Two-Phase Rendering Process

#### Phase 1: Wall Rendering (with Z-Buffer)

```javascript
const zBuffer = new Array(screenWidth);

for (let x = 0; x < screenWidth; x++) {
    const distance = castRay(angle);
    zBuffer= distance;  // CRITICAL: Save wall distance
    
    drawWallColumn(x, distance);
}
```

The *Z-buffer* stores the distance to the wall for each screen column.
This becomes crucial in Phase 2.


#### Phase 2: Sprite Rendering

```javascript
// Sort objects by distance (far to near)
objects.sort((a, b) => b.distance - a.distance);

// Draw each sprite
for (const obj of objects) {
    for (let x = spriteLeft; x < spriteRight; x++) {
        // KEY CHECK: Is sprite closer than wall?
        if (objectDistance < zBuffer[x]) {
            drawSpritePixel(x, y);  // Draw sprite
        } else {
            // Skip - wall is in front
        }
    }
}
```

This ensures sprites are *occluded* by walls correctly.


### Billboard Sprites: The Technique

#### What is a Billboard?

A billboard is a 2D image that *always faces the camera*.
Like a cardboard cutout that rotates to face you as you walk around it.

```
    Top view:

    You move here ->  You
                     /
                    /
    Sprite rotates: O  (always facing you)
                    \
    You move here ->  You
```


#### Multi-Angle Sprites

To show different sides of objects, we pre-render the 3D model from multiple angles:

```javascript
const NUM_ANGLES = 16;  // 16 viewing angles (every 22.5°)

for (let i = 0; i < NUM_ANGLES; i++) {
    const angle = (i / NUM_ANGLES) * Math.PI * 2;
    sprites[i] = renderModelFromAngle(angle);
}
```

This creates 16 sprites showing the object from:
- Front (0°)
- Front-right (22.5°)
- Right (45°)
- Back-right (67.5°)
- ... and so on around 360°


### WebGL Model Pre-Rendering

#### The Pipeline

1. *Load OBJ file* -> Parse vertices, normals, faces
2. *For each angle* -> Render model with WebGL
3. *Capture to image* -> Convert WebGL canvas to Image
4. *Store sprite* -> Keep in memory for fast access

#### Rendering a Single Sprite

```javascript
function renderModelSprite(angleY) {
    // Set up WebGL canvas (128x128 transparent background)
    modelGL.clearColor(0, 0, 0, 0);
    
    // Camera at fixed position
    mat4.translate(modelViewMatrix, [0, 0, -3]);
    
    // Scale model to fit nicely
    const scale = 1.2 / modelSize;
    mat4.scale(modelViewMatrix, [scale, scale, scale]);
    
    // Center the model
    mat4.translate(modelViewMatrix, [-centerX, -centerY, -centerZ]);
    
    // ROTATE the model (not the camera!)
    mat4.rotateY(modelViewMatrix, angleY);
    
    // Render to canvas
    gl.drawElements(gl.TRIANGLES, indexCount, gl.UNSIGNED_SHORT, 0);
    
    // Convert to Image
    return new Image(modelCanvas.toDataURL());
}
```

*Key insight*: We rotate the *model*, not the camera.
This way sprite 0 shows the front, sprite 8 shows the back, etc.

#### Lighting in Sprites

Simple directional lighting creates depth:

```glsl
// Fragment shader
vec3 lightDir = normalize(vec3(0.5, 1.0, 0.8));
float diff = max(dot(normal, lightDir), 0.0);

vec3 ambient = baseColor * 0.4;   // Base lighting
vec3 diffuse = baseColor * diff * 0.8;  // Directional light

gl_FragColor = vec4(ambient + diffuse, 1.0);
```

This bakes the lighting into the sprite image.

### Selecting the Correct Sprite

When rendering, we need to pick which of the 16 sprites
to show based on where the player is standing:

```javascript
// Calculate angle from player to object
const dx = object.x - player.x;
const dy = object.y - player.y;
const angleToObject = Math.atan2(dy, dx);

// We want to show the side facing us (add 180°)
let viewAngle = angleToObject + Math.PI;

// Normalize to 0-2π range
while (viewAngle < 0) viewAngle += Math.PI * 2;
while (viewAngle >= Math.PI * 2) viewAngle -= Math.PI * 2;

// Pick the closest sprite
const spriteIndex = Math.floor((viewAngle / (Math.PI * 2)) * NUM_ANGLES);
const sprite = object.sprites[spriteIndex];
```

*Example*: 
- If you're east of the object, you see the west-facing sprite
- If you're north, you see the south-facing sprite
- Smooth rotation as you circle around

### Sprite Positioning and Sizing

#### Screen Position

Calculate where the sprite appears horizontally:

```javascript
// 1. Get angle from player view to object
const dx = object.x - player.x;
const dy = object.y - player.y;
const angleToObject = Math.atan2(dy, dx);

// 2. Get relative angle (within FOV)
let relativeAngle = angleToObject - player.angle;

// Normalize to -π to π
while (relativeAngle < -Math.PI) relativeAngle += Math.PI * 2;
while (relativeAngle > Math.PI) relativeAngle -= Math.PI * 2;

// 3. Skip if outside FOV
if (Math.abs(relativeAngle) > FOV / 2) continue;

// 4. Project to screen X position
const screenX = (relativeAngle / FOV + 0.5) * screenWidth;
```

This converts world position -> view angle -> screen pixel.

#### Sprite Size

Like walls, sprites scale with distance using perspective:

```javascript
const distance = Math.sqrt(dx * dx + dy * dy);

// Same formula as wall height!
const spriteHeight = (TILE_SIZE * screenHeight) / distance;
const spriteWidth = spriteHeight;  // Keep 1:1 aspect ratio

// Vertical centering
const spriteY = (screenHeight - spriteHeight) / 2;
```

### Column-by-Column Rendering

Unlike drawing a full image at once, we draw sprites *one vertical strip at a time* to enable per-pixel z-buffering:

```javascript
const spriteLeft = Math.floor(screenX - spriteWidth / 2);
const spriteRight = Math.floor(screenX + spriteWidth / 2);

for (let x = spriteLeft; x < spriteRight; x++) {
    // Check screen bounds
    if (x < 0 || x >= screenWidth) continue;
    
    // Z-BUFFER CHECK
    if (objectDistance >= zBuffer[x]) continue;  // Wall is closer
    
    // Calculate which column of the sprite to draw
    const texX = ((x - spriteLeft) / spriteWidth) * sprite.width;
    
    // Draw this vertical stripe
    ctx.drawImage(
        sprite,
        texX, 0, 1, sprite.height,      // Source: 1px wide column
        x, spriteY, 1, spriteHeight     // Dest: 1px wide column
    );
}
```

*Why column-by-column?*
- Each column can be independently z-buffered
- Sprites can be partially occluded by walls
- More accurate depth sorting

### Depth Sorting

Objects must be drawn *far to near* (painter's algorithm):

```javascript
const visibleObjects = objects
    .map(obj => ({
        obj,
        distance: Math.sqrt(
            (obj.x - player.x) * 2 + 
            (obj.y - player.y) * 2
        )
    }))
    .filter(({ distance }) => distance < MAX_DEPTH)
    .sort((a, b) => b.distance - a.distance);  // Far to near!

// Now render in order
for (const { obj, distance } of visibleObjects) {
    renderSprite(obj, distance);
}
```

*Why far to near?*
- Far objects get drawn first
- Near objects overdraw them
- Combined with z-buffer for wall occlusion

### Transparency Handling

Sprites typically have transparent backgrounds:

```javascript
// WebGL rendering with alpha
modelGL.clearColor(0, 0, 0, 0);  // Transparent clear
modelGL.enable(gl.BLEND);
modelGL.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);

// Canvas respects alpha when drawing
ctx.drawImage(sprite, x, y, width, height);
```

Transparent pixels let the background show through.


### Performance Considerations

#### Memory vs. Quality Tradeoff

```javascript
// More angles = smoother rotation, more memory
const angles = 8;   // 45° steps, 8 sprites   (~1 MB)
const angles = 16;  // 22.5° steps, 16 sprites (~2 MB)
const angles = 32;  // 11.25° steps, 32 sprites (~4 MB)
```

Most games use 8 angles for enemies, 16+ for important objects.

#### Pre-rendering Benefits

*Pros:*
- Fast runtime rendering (just draw images)
- Complex lighting baked in
- Consistent style
- Works with any model format

*Cons:*
- Memory usage (N angles × M objects)
- Loading time (must render all sprites)
- Fixed lighting (can't change dynamically)


### Advanced Techniques

#### Sprite Animation

Add multiple frames per angle:

```javascript
object.sprites = [
    [ frame0_angle0, frame1_angle0, frame2_angle0 ],  // Angle 0
    [ frame0_angle1, frame1_angle1, frame2_angle1 ],  // Angle 1
    // ...
];

// Select frame based on time
const frameIndex = Math.floor(time / frameDelay) % numFrames;
const sprite = object.sprites[angleIndex][frameIndex];
```

#### Vertical Offset

Make objects float or vary in height:

```javascript
const spriteY = (screenHeight - spriteHeight) / 2 + object.verticalOffset;
```

#### Size Variation

Different sized objects in the world:

```javascript
const baseSize = object.scale * TILE_SIZE;
const spriteHeight = (baseSize * screenHeight) / distance;
```

#### Mirroring

Reduce memory by mirroring sprites:

```javascript
// Only render right side (angles 0-7)
// Mirror for left side (angles 8-15)
if (angleIndex >= 8) {
    ctx.scale(-1, 1);  // Horizontal flip
    angleIndex = 16 - angleIndex;
}
```

### Collision Detection

Objects have circular collision bounds:

```javascript
function checkCollision(playerX, playerY, object) {
    const dx = playerX - object.x;
    const dy = playerY - object.y;
    const distance = Math.sqrt(dx * dx + dy * dy);
    
    return distance < (object.radius + PLAYER_RADIUS);
}
```

Simple and fast for sphere-sphere collision.


### Comparison to Modern 3D

#### Raycasting + Sprites (This approach)
- Pre-rendered 2D images
- Billboard rotation
- Fast rendering
- Limited perspectives

#### Full 3D (Modern games)
- Real-time polygon rendering
- Dynamic lighting
- Free camera movement
- Higher complexity

*Sprite technique advantages:*
- Retro aesthetic
- Lower hardware requirements
- Artistic control (hand-drawn possible)
- Consistent performance


### Historical Context

This technique was used in:
- *Wolfenstein 3D* (1992): 8-angle sprites
- *Doom* (1993): 5-8 angle sprites with rotation
- *Duke Nukem 3D* (1996): Pre-rendered 3D sprites
- *Diablo* (1996): High-quality pre-rendered sprites

Modern "boomer shooters" still use this aesthetic!


### Implementation Checklist

- Pre-render model from N angles using WebGL
- Store sprites in object array
- Calculate object screen position
- Determine correct sprite angle
- Size sprite based on distance
- Sort objects by distance (far to near)
- Z-buffer check per column
- Handle transparency
- Collision detection with radius


### Troubleshooting

Sprites don't rotate:
- Check angle calculation (player -> object)
- Verify sprite generation rotates model
- Ensure angleIndex wraps correctly (0-15)

Sprites appear through walls:
- Verify z-buffer is filled during wall rendering
- Check distance calculation uses same units
- Ensure column-by-column rendering with z-check

Sprites flicker:
- Sort objects by distance (far to near)
- Check for floating point precision errors
- Ensure consistent distance calculation

Wrong sprite angle shown:
- Verify angle normalization (0 to 2π)
- Check if model rotation is applied correctly
- Test with distinctive front/back model


### Further Experimentation

Try modifying these parameters:

```javascript
const NUM_ANGLES = 16;          // Sprite count per object
const SPRITE_RESOLUTION = 128;  // Texture size
const OBJECT_SCALE = 1.2;       // World size relative to tiles
```


*Related*: See `README.md` for wall rendering documentation.
