
## Reflection and Floor Rendering Demonstration

This interactive demo shows how *realistic reflections* are rendered on a floor plane,
combined with *diffuse lighting*, *transparency effects*, and *perspective floor rendering*.

1. *Mirror Reflection* - cube reflected across floor plane with proper transformations
2. *Transparency System* - reflections rendered with graduated opacity
3. *Diffuse Lighting* - faces brighten/darken based on angle to light
4. *Two-Pass Rendering* - back-face and front-face separation for depth
5. *Perspective Floor* - gradient floor extending to horizon
6. *Automatic Rotation* - smooth animation showing all angles


### How Reflections Work

#### The Principle

A reflection is the *mirror image* of an object across a plane.
Points are transformed symmetrically across the reflection surface.

```
     Cube
      □
  ═════════ Floor (y = -1.5)
      □
  Reflection
```

#### Planar Reflection Method

For each vertex of the cube:
1. *Measure distance* from vertex to floor plane
2. *Project same distance* on opposite side of plane
3. *Result* is the reflected vertex position

#### Mathematical Formula

Given:
- Original vertex: *V = (Vx, Vy, Vz)*
- Floor plane: *y = floorY* (e.g., y = -1.5)

The reflected point:
```
Vr = (Vx, 2 × floorY - Vy, Vz)
```

*Why this works:*
- Distance from V to floor: `Vy - floorY`
- Reflected point must be same distance below: `floorY - (Vy - floorY)`
- Simplifies to: `2 × floorY - Vy`

*Example:*
- Floor at y = -1.5
- Vertex at (1, 0.5, 2)
- Distance above floor: 0.5 - (-1.5) = 2.0
- Reflected point: (1, 2×(-1.5) - 0.5, 2) = (1, -3.5, 2)
- Distance below floor: -1.5 - (-3.5) = 2.0 ✓

#### Code Implementation

```javascript
function reflectAcrossFloor(v, floorY) {
  return [v[0], 2 * floorY - v[1], v[2]];
}

// Apply to all cube vertices
const reflectedCube = cube.map(v => reflectAcrossFloor(v, floorY));
```

### Normal Vectors in Reflections

#### The Challenge

When rendering the reflected cube, the *surface normals* must also be flipped
to ensure lighting calculations are correct.

#### Why Normals Matter

A normal vector points *perpendicular* to a surface:
- *Original cube*: normals point "outward" from cube
- *Reflected cube*: cube is "flipped upside down"
- *Problem*: if we don't flip normals, lighting will be backwards

#### The Solution

When reflecting across a horizontal plane (y = constant):
- *Flip the Y component* of the normal
- Other components remain the same

```javascript
// For horizontal floor reflection
normalReflected = [normal[0], -normal[1], normal[2]]
```

In the code, we achieve this by passing `isReflection` flag:

```javascript
let lightingNormal = normalize(normal);
if (isReflection) {
  lightingNormal = lightingNormal.map(x => -x);
}
```

This flips *all* components, which works for our symmetric lighting setup.

### Face Culling and Reflections

#### What is Face Culling?

*Face culling* means only drawing faces that point toward the camera.
This prevents rendering the "inside" of objects.

```
    Camera
      o
      v
   ┌─────┐
   │  O  │  <- Front face (visible)
   └─────┘
      x     <- Back face ("behind") (culled)
```

#### Determining Front vs Back

Use the *dot product* between:
- *Normal vector* (perpendicular to face)
- *View direction* (from face to camera)

```javascript
const viewDir = normalize(sub([0, 0, 5], center));
const isFrontFacing = dot(normalize(normal), viewDir) > 0;
```

- *Positive dot product*: face points toward camera -> front face
- *Negative dot product*: face points away -> back face

#### Reflection Reversal

When we reflect the cube, we're essentially viewing it "from the other side":
- What was a front face becomes a back face
- What was a back face becomes a front face

*Solution:* Flip the culling logic for reflections:

```javascript
let isFrontFacing = dot(normalize(normal), viewDir) > 0;

if (isReflection) {
  isFrontFacing = !isFrontFacing;
}
```

### Two-Pass Rendering for Transparency

#### Why Two Passes?

To create a sense of depth and allow "seeing through" the cube:
1. *Pass 0*: Draw back faces with high transparency (30%)
2. *Pass 1*: Draw front faces with normal transparency

This creates a *depth cue* - we can see the far side through the near side.

#### The Algorithm

```javascript
for (let pass = 0; pass < 2; pass++) {
  for (let { face } of faceDepths) {
    // Determine if front or back facing
    let isFrontFacing = /* ... */;
    
    // Skip faces not belonging to this pass
    if (pass === 0 && isFrontFacing) continue;  // Pass 0: only back
    if (pass === 1 && !isFrontFacing) continue; // Pass 1: only front
    
    // Draw with appropriate transparency
    if (pass === 0) {
      ctx.globalAlpha = alpha * 0.3; // Back: 30%
    } else {
      ctx.globalAlpha = alpha;        // Front: 100%
    }
  }
}
```

#### Visual Effect

```
Pass 0 (30% alpha)    Pass 1 (100% alpha)    Combined
     │  \                  ┌───┐              ┌───┐
     │   \                 │░░░│              │███│
     └────┘                └───┘              └───┘
   Back faces           Front faces           Depth!
```

### Reflection Transparency and Darkening

#### Making Reflections Look Real

Real reflections are:
1. *Less bright* than the original (floor absorbs some light)
2. *More transparent* (floor isn't a perfect mirror)

#### Opacity Adjustment

```javascript
if (isReflection) {
  alpha *= 0.4; // Reflection is 40% as opaque
}
```

*Why 0.4?*
- *Too high (0.8)*: reflection looks as solid as original
- *Too low (0.1)*: reflection barely visible
- *0.4*: clearly visible but obviously a reflection

#### Brightness Adjustment

```javascript
if (isReflection) {
  finalBrightness *= 0.7; // Reflection is 70% as bright
}
```

Then we darken the color:

```javascript
const darkenFactor = finalBrightness;
color = `rgb(${Math.floor(r * darkenFactor)}, 
             ${Math.floor(g * darkenFactor)}, 
             ${Math.floor(b * darkenFactor)})`;
```

#### Combined Effect

For a face with brightness 0.8 in reflection:
- Base alpha: 0.8
- Reflection multiplier: 0.4
- *Final alpha*: 0.8 × 0.4 = 0.32

- Base brightness: 0.8
- Reflection multiplier: 0.7
- *Final brightness*: 0.8 × 0.7 = 0.56

This creates a subtle, realistic reflection effect.

### Perspective Floor Rendering

#### The Challenge

Create a floor that:
1. Extends to edges of canvas
2. Shows perspective (appears to recede into distance)
3. Fades naturally into background

#### Gradient Strategy

Use a *linear gradient* from bottom to horizon:

```javascript
const gradient = ctx.createLinearGradient(0, h, 0, horizonPoint[1]);
gradient.addColorStop(0, "#909090");    // Dark at bottom
gradient.addColorStop(0.8, "#b0b0b0");  // Lighter going back
gradient.addColorStop(1, "#f0f0f0");    // Fades to background
```

*Color stops:*
- *0.0* (bottom): Darkest floor color
- *0.8* (near horizon): Lighter transition
- *1.0* (horizon): Matches background, seamless blend

#### Trapezoid Shape

The floor is drawn as a trapezoid:
- *Near edge*: full width of canvas
- *Far edge*: narrower width at horizon

```javascript
const farWidth = 8;  // Width in 3D space
const farLeft = project([-farWidth, floorY, -floorDepth]);
const farRight = project([farWidth, floorY, -floorDepth]);

ctx.beginPath();
ctx.moveTo(0, h);               // Bottom left corner
ctx.lineTo(w, h);               // Bottom right corner  
ctx.lineTo(w, horizonPoint[1]); // Right edge to horizon
ctx.lineTo(...farRight);        // Far right of floor
ctx.lineTo(...farLeft);         // Far left of floor
ctx.lineTo(0, horizonPoint[1]); // Left edge to horizon
ctx.closePath();
```

#### Why This Works

*Perspective projection* makes distant objects smaller:
- 8 units wide at z = -6 projects to ~200 pixels
- Creates natural perspective convergence
- Floor appears to extend into the distance

### Diffuse Lighting (Lambertian Reflection)

#### The Concept

Surfaces appear brighter when facing toward a light source, darker when facing away.

#### The Mathematics

Brightness depends on the *angle* between:
- *Surface normal* N (perpendicular to the face)
- *Light direction* L (from surface to light)

Formula:
```
diffuse = max(0, N · L)
```

Where *N · L* is the dot product:
```
N · L = Nx×Lx + Ny×Ly + Nz×Lz
```

#### Why This Works

The dot product of two *unit vectors* equals the *cosine* of the angle between them:

```
N · L = cos(θ)
```

- *θ = 0°* (facing light): cos(0°) = 1 -> fully bright
- *θ = 45°*: cos(45°) ≈ 0.707 -> 70% bright
- *θ = 90°* (perpendicular): cos(90°) = 0 -> no direct light
- *θ > 90°* (facing away): cos(θ) < 0 -> clamped to 0

#### Ambient + Diffuse Model

We add *ambient light* so faces never go completely black:

```javascript
const brightness = Math.max(0.4, dot(lightingNormal, lightDir)) * 0.9;
```

- *Minimum*: 0.4 (40% brightness even in shadow)
- *Maximum*: 0.4 to 1.0 range, scaled by 0.9 = 0.9 max
- *Result*: brightness from *0.4* to *0.9*

#### Code Implementation

```javascript
// Light from above and slightly forward
const lightDir = normalize([0, 3, 0.5]);

// Calculate face normal from first three vertices
const normal = cross(sub(pts3d[1], pts3d[0]), sub(pts3d[2], pts3d[0]));

// Flip normal for reflections
let lightingNormal = normalize(normal);
if (isReflection) {
  lightingNormal = lightingNormal.map(x => -x);
}

// Calculate brightness
const brightness = Math.max(0.4, dot(lightingNormal, lightDir)) * 0.9;
```

### Painter's Algorithm (Depth Sorting)

#### The Problem

In 2D canvas, there's no automatic depth buffering.
Objects drawn last appear in front, regardless of 3D position.

#### The Solution

*Sort faces by depth* before drawing:

```javascript
const faceDepths = faces.map((face, i) => {
  const pts3d = face.indices.map(i => cube[i]);
  const z = pts3d.reduce((sum, v) => sum + v[2], 0) / pts3d.length;
  return { face, z };
}).sort((a, b) => b.z - a.z); // Far to near
```

*Steps:*
1. Calculate average Z coordinate of each face
2. Sort by Z (furthest first)
3. Draw in sorted order

*Result:* Faces further from camera are drawn first, nearer faces overdraw them.

#### Limitations

Painter's algorithm fails for:
- *Overlapping polygons* (A in front of B, B in front of C, C in front of A)
- *Intersecting geometry*

For simple convex objects like cubes, it works perfectly.

### Rendering Pipeline

The complete process each frame:

```
1. Clear canvas
   v
2. Apply rotation matrices to cube vertices
   v
3. Generate reflected cube vertices
   v
4. Draw perspective floor with gradient
   v
5. Draw shadow placeholder (currently disabled)
   v
6. Draw reflected cube:
   - Two-pass rendering (back faces, then front faces)
   - Flipped face culling
   - Flipped normals for lighting
   - Reduced opacity (40%)
   - Darkened colors (70%)
   v
7. Draw main cube:
   - Two-pass rendering
   - Normal face culling
   - Normal lighting
   - Full opacity
   v
8. Loop (requestAnimationFrame)
```

### Automatic Rotation

#### The Animation

The cube rotates automatically for demonstration:

```javascript
angleX += 0.01;   // 0.01 radians per frame ≈ 0.57° per frame
angleY += 0.015;  // 0.015 radians per frame ≈ 0.86° per frame
```

At 60 FPS:
- *X rotation*: ~34° per second
- *Y rotation*: ~52° per second

#### Why Different Rates?

Using different rotation speeds (0.01 vs 0.015) creates a *Lissajous pattern* -
the cube explores all possible orientations smoothly without repeating too quickly.

*Benefits:*
- Shows all faces over time
- Demonstrates lighting from all angles
- Reflection visible from multiple perspectives
- Never gets stuck in repetitive motion

### Color Darkening Technique

#### The Challenge

Given a CSS color name (like "red"), how do we darken it?

#### The Hack Solution

```javascript
ctx.fillStyle = face.color;
ctx.fillRect(0, 0, 1, 1); // Draw 1 pixel
const imageData = ctx.getImageData(0, 0, 1, 1);
const [r, g, b] = imageData.data; // Extract RGB values
```

*How it works:*
1. Set fill color to desired color name
2. Draw a tiny 1×1 rectangle
3. Read back the pixel data
4. Browser has converted color name to RGB for us

#### Applying the Darkening

```javascript
const darkenFactor = finalBrightness; // 0.0 to 1.0
color = `rgb(${Math.floor(r * darkenFactor)}, 
             ${Math.floor(g * darkenFactor)}, 
             ${Math.floor(b * darkenFactor)})`;
```

Multiply each component by brightness:
- *Brightness 1.0*: (255, 0, 0) -> rgb(255, 0, 0) - full red
- *Brightness 0.5*: (255, 0, 0) -> rgb(127, 0, 0) - dark red
- *Brightness 0.0*: (255, 0, 0) -> rgb(0, 0, 0) - black

### Coordinate System

#### 3D Space
- *X-axis*: left (-) to right (+)
- *Y-axis*: down (-) to up (+)
- *Z-axis*: far (-) to near (+)

#### Screen Space
- *X*: left (0) to right (width)
- *Y*: top (0) to bottom (height)

#### Perspective Projection

```javascript
function project([x, y, z]) {
  const scale = 200 / (5 - z); // Camera at z=5
  return [x * scale + w/2, -y * scale + h/2];
}
```

*Key points:*
- Camera positioned at z = 5
- Objects at z = 0 (5 units away) have scale = 40
- Objects at z = 4 (1 unit away) have scale = 200
- Y is negated because screen Y increases downward

### Performance Considerations

#### Frame Rate
- *Target*: 60 FPS
- *Achieved*: Typically 60 FPS on modern browsers
- *Bottleneck*: Canvas 2D fill operations

#### Optimization Strategies

*Current optimizations:*
1. *Depth sorting once per frame* - not per pass
2. *Minimal state changes* - group similar operations
3. *requestAnimationFrame* - syncs with display refresh

*Possible improvements:*
1. *Caching projections* - if camera doesn't move
2. *Dirty rectangles* - only redraw changed areas
3. *Web Workers* - offload vector math calculations
4. *WebGL* - hardware-accelerated 3D rendering

### Shadow Implementation (Disabled)

#### Current State

The shadow code exists but is commented out:

```javascript
// const shadowVerts = pts3d.map(v => project(projectShadow(v, lightDir)));
```

#### Why Disabled?

The reflection demo focuses on:
- Reflection mechanics
- Transparency effects
- Floor perspective

Adding shadows would:
- Complicate visual clarity
- Require additional explanation
- Overlap with the separate shadow demo

#### Shadow Implementation

The `projectShadow` function is included:

```javascript
function projectShadow(v, lightDir) {
  const t = (v[1] + 1.5) / lightDir[1];
  return [
    v[0] - lightDir[0] * t,
    -1.5,
    v[2] - lightDir[2] * t
  ];
}
```

This could be enabled by uncommenting the shadow drawing code.

### Educational Value

This demo teaches:
1. *Planar reflection* - mirroring objects across a plane
2. *Normal transformation* - how surface orientations change
3. *Face culling* - determining visible surfaces
4. *Transparency composition* - layering semi-transparent objects
5. *Multi-pass rendering* - drawing objects in multiple stages
6. *Perspective projection* - 3D to 2D transformation
7. *Gradient fills* - creating smooth color transitions
8. *Lighting models* - Lambertian diffuse reflection

### Possible Extensions

#### 1. Multiple Reflection Planes

Reflect across vertical walls too:

```javascript
function reflectAcrossVertical(v, planeX) {
  return [2 * planeX - v[0], v[1], v[2]];
}
```

Create a "hall of mirrors" effect.

#### 2. Fresnel Effect

Vary reflection intensity by viewing angle:

```javascript
const viewAngle = Math.abs(dot(normalize(normal), viewDir));
const fresnelFactor = Math.pow(1 - viewAngle, 3);
const reflectionAlpha = 0.4 * fresnelFactor;
```

Grazing angles show stronger reflections.

#### 3. Distorted Reflections

Add wave distortion for water-like effect:

```javascript
function reflectWithWaves(v, floorY, time) {
  const wave = Math.sin(v[0] * 2 + time) * 0.1;
  return [v[0], 2 * (floorY + wave) - v[1], v[2]];
}
```

#### 4. Environment Mapping

Reflect a background image instead of just the cube:

```javascript
const envMap = document.createElement('img');
envMap.src = 'skybox.jpg';
// Use envMap in reflection rendering
```

#### 5. Blur Effect

Apply blur to reflection for frosted surface:

```javascript
ctx.filter = 'blur(2px)';
drawCube(reflectedCube, true);
ctx.filter = 'none';
```

#### 6. Interactive Floor Level

Add slider to adjust floor position:

```javascript
<input type="range" id="floorY" min="-3" max="0" step="0.1" value="-1.5">

floorY = parseFloat(document.getElementById('floorY').value);
```

See how reflection changes with floor position.

#### 7. Multiple Objects

Add spheres, pyramids, or other shapes:

```javascript
const sphere = generateSphereVertices(1, 16);
const reflectedSphere = sphere.map(v => reflectAcrossFloor(v, floorY));
```

### Common Pitfalls

#### 1. Forgetting to Flip Normals

*Problem:* Reflected cube has incorrect lighting
*Solution:* Remember to negate normals when `isReflection === true`

#### 2. Wrong Reflection Formula

*Problem:* Using `[v[0], -v[1], v[2]]` instead of `[v[0], 2*floorY - v[1], v[2]]`
*Result:* Cube appears to sink into ground
*Fix:* Always reflect across the actual floor position

#### 3. Drawing Order

*Problem:* Drawing reflection after main cube
*Result:* Reflection appears in front of cube
*Fix:* Always draw: floor -> reflection -> main object

#### 4. Alpha Blending

*Problem:* Setting too high or too low alpha for reflection
*Result:* Looks unrealistic
*Sweet spot:* 0.3 to 0.5 alpha multiplier

#### 5. Face Culling Direction

*Problem:* Not reversing culling for reflection
*Result:* Reflection shows wrong faces or appears hollow
*Fix:* `if (isReflection) isFrontFacing = !isFrontFacing;`

### Summary

This demonstration combines:
- *Planar reflection* via coordinate transformation
- *Normal flipping* for correct lighting
- *Face culling reversal* for proper visibility
- *Two-pass rendering* for transparency depth
- *Perspective floor* with gradient shading
- *Automatic rotation* for comprehensive viewing
- *Darkening and opacity* for realistic reflections

The result is a visually compelling demonstration of fundamental 3D graphics
techniques using only 2D canvas operations.

