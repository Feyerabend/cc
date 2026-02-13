
## Raytraced Bouncing Sphere with Texture and Reflection

This interactive demo shows how *raytracing* creates photorealistic 3D rendering,
including *texture mapping*, *specular highlights*, *shadows*, and *reflections*.

1. *Raytracing Renderer* - physically-based light simulation pixel-by-pixel
2. *Ray-Sphere Intersection* - mathematical solution for sphere rendering
3. *Ray-Plane Intersection* - ground plane with proper lighting
4. *Shadow Rays* - accurate hard shadows cast by sphere onto plane
5. *Reflection Rays* - recursive raytracing for mirror reflections on floor
6. *Spherical Texture Mapping* - wrap 2D images onto 3D sphere
7. *Animated Texture Rotation* - texture spins independently of sphere motion
8. *Specular Lighting* - shiny highlights using Blinn-Phong model
9. *Bouncing Animation* - physics-inspired vertical and horizontal motion
10. *File Upload* - load custom textures interactively


### What is Raytracing?

*Raytracing* simulates how light actually works in the real world:
- Light travels in straight lines (rays)
- Rays bounce off surfaces
- Colors come from where rays eventually hit

### The Core Idea

Instead of projecting 3D objects onto screen (like rasterization),
raytracing works *backwards*:

```
   EYE          SCREEN          SCENE
    👁  ------>  [pixel] ------>  🌍
         ray              ray hits object
```

For each pixel:
1. *Cast a ray* from camera through that pixel
2. *Find what it hits* (sphere, plane, nothing)
3. *Calculate color* based on lighting, shadows, reflections
4. *Write color* to pixel


### Why Raytracing?

*Advantages:*
- *Physically accurate* - simulates real light behavior
- *Natural reflections* - mirrors, water, glass just work
- *Accurate shadows* - hard and soft shadows are automatic
- *Simple to understand* - ray-object intersection is pure math

*Disadvantages:*
- *Slow* - must trace rays for every pixel, every frame
- *CPU-bound* - this demo runs on CPU, not GPU
- *Scales poorly* - double resolution = 4× the rays

This is why modern games use *rasterization* for real-time rendering,
but raytracing is making a comeback with GPU acceleration (RTX, etc.).


### Ray-Sphere Intersection: The Problem

Given:
- *Ray origin*: O = (Ox, Oy, Oz) - camera position
- *Ray direction*: D = (Dx, Dy, Dz) - direction through pixel
- *Sphere center*: C = (Cx, Cy, Cz) - where sphere is located
- *Sphere radius*: r - size of sphere

*Question:* Does the ray hit the sphere? If so, where?

### Ray Equation

A ray is a point that moves along a direction:

```
P(t) = O + t × D
```

Where *t* is a parameter:
- *t = 0*: at ray origin (camera)
- *t = 1*: one unit along ray direction
- *t > 0*: in front of camera
- *t < 0*: behind camera (we ignore these)

### Sphere Equation

A sphere is all points at distance *r* from center *C*:

```
|P - C| = r
|P - C|² = r²
```

Expanded:
```
(Px - Cx)² + (Py - Cy)² + (Pz - Cz)² = r²
```

### Solving the Intersection

Substitute ray equation into sphere equation:

```
|O + t×D - C|² = r²
```

Let *OC = O - C* (vector from sphere center to ray origin):

```
|OC + t×D|² = r²
```

Expand the dot product:

```
(OC + t×D) · (OC + t×D) = r²
OC·OC + 2t(OC·D) + t²(D·D) = r²
```

Rearrange into *quadratic equation* form:

```
(D·D)t² + 2(OC·D)t + (OC·OC - r²) = 0
```

Standard quadratic: *at² + bt + c = 0*

Where:
- *a = D·D* (always 1 if D is normalized)
- *b = 2(OC·D)*
- *c = OC·OC - r²*

### The Quadratic Formula

```
t = (-b ± √(b² - 4ac)) / 2a
```

The *discriminant* (b² - 4ac) tells us:
- *< 0*: No intersection (ray misses sphere)
- *= 0*: One intersection (ray is tangent to sphere)
- *> 0*: Two intersections (ray enters and exits sphere)

### Code

```javascript
const oc = new Vector(CAMERA_POS.x, CAMERA_POS.y, CAMERA_POS.z).subtract(SPHERE_CENTER);
const a = rayDir.dot(rayDir);  // Usually 1 for normalized rays
const b = 2 * oc.dot(rayDir);
const c = oc.dot(oc) - SPHERE_RADIUS * SPHERE_RADIUS;
const discriminant = b * b - 4 * a * c;

if (discriminant >= 0) {
    const sqrtDisc = Math.sqrt(discriminant);
    const t0 = (-b - sqrtDisc) / (2 * a);  // Near intersection
    const t1 = (-b + sqrtDisc) / (2 * a);  // Far intersection
    
    // Use the nearest positive t
    t = t0 > EPSILON ? t0 : t1 > EPSILON ? t1 : Infinity;
}
```

### Why Two Solutions?

When a ray hits a sphere, it typically intersects at two points:

```
    O (camera)
     \
      \  t0 (entry)
       \ /
        •-------•  Sphere
               t1 (exit)
```

- *t0* (smaller): where ray enters sphere (front surface)
- *t1* (larger): where ray exits sphere (back surface)

We want *t0* for rendering the visible front surface.

### The EPSILON Check

```javascript
t = t0 > EPSILON ? t0 : t1 > EPSILON ? t1 : Infinity;
```

*Why not just `t0 > 0`?*

Due to floating-point precision, when casting rays from a surface,
the ray might immediately re-intersect the same surface at t ≈ 0.00000001.

*EPSILON* (typically 0.01) prevents this "self-intersection" problem:
- Ignore intersections closer than EPSILON
- Ensures ray has actually left the surface before checking for hits



### Ray-Plane Intersection: The Problem

Given:
- *Ray origin*: O
- *Ray direction*: D
- *Plane*: y = constant (horizontal plane)

*Question:* Where does ray hit plane?

### Plane Equation

For a horizontal plane at y = PLANE_Y:

```
P.y = PLANE_Y
```

### Solving the Intersection

Ray equation component-wise:
```
P(t) = O + t × D
Py(t) = Oy + t × Dy
```

At intersection:
```
Oy + t × Dy = PLANE_Y
```

Solve for t:
```
t = (PLANE_Y - Oy) / Dy
```

### Special Cases

*If Dy = 0:*
- Ray is parallel to plane
- Either never intersects (if Oy ≠ PLANE_Y)
- Or lies entirely in plane (if Oy = PLANE_Y)

*If Dy > 0:*
- Ray points upward
- Might hit plane behind camera (negative t)

*If Dy < 0:*
- Ray points downward
- Will hit plane in front (positive t)

### Code

```javascript
const planeT = (PLANE_Y - CAMERA_POS.y) / rayDir.y;

if (planeT > EPSILON) {  // Only if in front of camera
    const planeHit = new Vector(CAMERA_POS.x, CAMERA_POS.y, CAMERA_POS.z)
        .add(rayDir.scale(planeT));
    // planeHit is the 3D point where ray hit the plane
}
```

### Determining What's Closer

When ray hits both sphere and plane, which do we see?

```javascript
if (planeT > EPSILON && planeT < t) {
    // Plane is closer - draw plane
} else if (t < Infinity) {
    // Sphere is closer - draw sphere
}
```

The object with *smaller t* is closer to camera.



### Shadow Rays: The Concept

A point is in *shadow* if there's an obstruction between it and the light source.

```
    ☀ Light
    |  \
    |   \  (blocked)
    |    \
  Sphere  •---X  Point on plane (in shadow)
```

### The Shadow Ray Test

From a point on the plane:
1. *Cast ray toward light* (shadow ray)
2. *Check for intersections* before reaching light
3. *If hit*: point is in shadow
4. *If clear*: point is lit

### Code Implementation

```javascript
// Point on plane where primary ray hit
const planeHit = /* ... */;

// Direction from plane to light
const toLight = new Vector(LIGHT_POS.x - planeHit.x, 
                          LIGHT_POS.y - planeHit.y, 
                          LIGHT_POS.z - planeHit.z);
const lightDist = Math.sqrt(toLight.dot(toLight));
const lightDir = toLight.normalize();

// Shadow ray origin (slightly offset to prevent self-intersection)
const shadowRayOrigin = planeHit.add(lightDir.scale(EPSILON));

// Test if shadow ray hits sphere
const ocShadow = shadowRayOrigin.subtract(SPHERE_CENTER);
const bShadow = 2 * ocShadow.dot(lightDir);
const cShadow = ocShadow.dot(ocShadow) - SPHERE_RADIUS * SPHERE_RADIUS;
const discriminantShadow = bShadow * bShadow - 4 * cShadow;

if (discriminantShadow >= 0) {
    // Shadow ray hit sphere - point is in shadow
    planeColor = SHADOW_COLOR.map(c => c * AMBIENT_LIGHT);
} else {
    // Shadow ray clear - point is lit
    const diffuse = Math.max(0, normal.dot(lightDir));
    planeColor = PLANE_COLOR.map(c => c * (diffuse + AMBIENT_LIGHT));
}
```

### Why Check Distance?

Actually, we should also verify the intersection is *before* the light:

```javascript
if (discriminantShadow >= 0) {
    const tShadow = (-bShadow - Math.sqrt(discriminantShadow)) / 2;
    if (tShadow > EPSILON && tShadow < lightDist) {
        // Object blocks light
    }
}
```

This prevents objects *behind* the light from casting shadows forward.

### Hard vs Soft Shadows

This demo produces *hard shadows* (sharp edges) because:
- Light is a *point source* (infinitely small)
- Either you can see the light or you can't (binary)

*Soft shadows* require:
- *Area lights* (light has size)
- *Multiple shadow rays* per point
- Average the results



### Reflection Rays: The Concept

Reflective surfaces (mirrors, water, polished metal) show images of other objects.

```
    👁 Eye
      \
       \  Primary ray
        \
         •-----------> Reflection ray
        Plane        /
                   Sphere (reflected)
```

### The Reflection Formula

Given:
- *Incident ray*: I (direction hitting surface)
- *Surface normal*: N (perpendicular to surface)

*Reflected ray* direction:
```
R = I - 2(I·N)N
```

*Derivation:*

The reflection has two components:
1. *Parallel component*: stays the same
2. *Perpendicular component*: flips direction

The perpendicular component is: *(I·N)N*
To flip it: *-2(I·N)N*
Add to original: *I - 2(I·N)N*

### Visual Explanation

```
     N (normal)
     ↑
     |
I ↘  |  ↗ R
  ↘ | ↗
   ↘|↗
════•════ Surface
```

Angle of incidence = Angle of reflection

### Code

```javascript
// For horizontal plane, normal is simply (0, 1, 0)
const planeNormal = new Vector(0, 1, 0);

// Calculate reflection direction
const reflectDir = rayDir.subtract(
    planeNormal.scale(2 * rayDir.dot(planeNormal))
).normalize();

// Origin of reflection ray (slightly above surface)
const reflectOrigin = planeHit.add(planeNormal.scale(EPSILON));

// Now trace the reflection ray to see what it hits
// (Same sphere intersection code, but with reflectDir and reflectOrigin)
```

### Recursive Raytracing

In full raytracing, reflections can reflect reflections:

```
Eye → Mirror1 → Mirror2 → Object
```

This requires *recursive* ray tracing:

```javascript
function trace(origin, direction, depth) {
    if (depth > MAX_DEPTH) return BACKGROUND_COLOR;
    
    const hit = findIntersection(origin, direction);
    if (hit.material.reflective) {
        const reflectDir = reflect(direction, hit.normal);
        const reflectColor = trace(hit.point, reflectDir, depth + 1);
        return blend(hit.color, reflectColor);
    }
    return hit.color;
}
```

*This demo uses single-level reflection:*
- Primary ray hits plane
- Reflection ray from plane checks for sphere
- No further recursion

### Blending Reflection

Real surfaces are partially reflective:

```javascript
const PLANE_REFLECTION = 0.4; // 40% reflective

color = [
    planeColor[0] * (1 - PLANE_REFLECTION) + reflectColor[0] * PLANE_REFLECTION,
    planeColor[1] * (1 - PLANE_REFLECTION) + reflectColor[1] * PLANE_REFLECTION,
    planeColor[2] * (1 - PLANE_REFLECTION) + reflectColor[2] * PLANE_REFLECTION
];
```

*Result:*
- 60% of final color from plane's own color (diffuse + shadow)
- 40% from reflected image of sphere



### Spherical Texture Mapping: The Challenge

We have:
- *3D sphere surface* - infinite points in 3D space
- *2D texture image* - finite pixels in rectangle

*Goal:* Map texture pixels onto sphere surface

### UV Coordinates

*UV coordinates* are 2D coordinates on a texture:
- *u*: horizontal (0 to 1, wraps around sphere)
- *v*: vertical (0 to 1, from bottom to top)

Like latitude and longitude on Earth.

### Spherical Mapping Formula

Given a point *P* on the sphere surface, relative to sphere center:

```javascript
const hitRelative = hitPoint.subtract(SPHERE_CENTER);
```

*Calculate u (horizontal wrap):*
```javascript
const u = 0.5 + Math.atan2(hitRelative.z, hitRelative.x) / (2 * Math.PI);
```

*Explanation:*
- `Math.atan2(z, x)` gives angle in XZ plane (-π to π)
- Divide by 2π to normalize to (-0.5 to 0.5)
- Add 0.5 to shift to (0 to 1)

*Calculate v (vertical):*
```javascript
const v = 0.5 - Math.asin(hitRelative.y / SPHERE_RADIUS) / Math.PI;
```

*Explanation:*
- `hitRelative.y / SPHERE_RADIUS` normalizes y to (-1 to 1)
- `Math.asin(...)` gives angle from equator (-π/2 to π/2)
- Divide by π to get (-0.5 to 0.5)
- Subtract from 0.5 to flip (texture v=0 at top, v=1 at bottom)

### Visual Representation

```
    v=0 (top)
     ___
   /     \
  |   u=0 |  u=1 (same line - wraps)
  |       |
   \     /
    ---
    v=1 (bottom)
```

### Texture Lookup

```javascript
function getTextureColor(u, v, time) {
    const x = Math.floor(u * textureImage.width) % textureImage.width;
    const y = Math.floor(v * textureImage.height) % textureImage.height;
    const index = (y * textureImage.width + x) * 4;
    return [
        textureImage.data[index],      // Red
        textureImage.data[index + 1],  // Green
        textureImage.data[index + 2]   // Blue
    ];
}
```

*Steps:*
1. Scale u,v (0-1) to pixel coordinates
2. Use modulo to handle wrapping
3. Calculate 1D array index from 2D coordinates
4. Extract RGB values

### Texture Rotation

To make texture spin around sphere:

```javascript
const rotationPhase = (time % ROTATION_CYCLE_MS) / ROTATION_CYCLE_MS;
const uRotated = (u + rotationPhase) % 1.0;
```

*Effect:*
- `rotationPhase` goes from 0 to 1 over ROTATION_CYCLE_MS milliseconds
- Add to u coordinate
- Modulo wraps around (1.2 becomes 0.2)
- Texture appears to rotate around sphere's vertical axis



### Lighting Models: Diffuse Lighting (Lambertian)

Surface brightness depends on angle to light:

```javascript
const diffuse = Math.max(0, normal.dot(lightDir));
```

- *Perpendicular to light* (dot = 0): dark
- *Facing light* (dot = 1): bright
- *Away from light* (dot < 0): clamped to 0

### Ambient Lighting

Minimum brightness, simulating scattered light:

```javascript
const AMBIENT_LIGHT = 0.2;  // 20% minimum brightness
const totalLight = diffuse + AMBIENT_LIGHT;
```

Without ambient, shadowed areas would be completely black.

### Specular Highlights (Blinn-Phong)

Shiny surfaces have bright *specular highlights* where they reflect light directly.

*Phong model:*
```
R = reflect(L, N)  (reflection of light)
specular = (R · V)^shininess
```

*Blinn-Phong model* (faster, used in this demo):
```
H = normalize(L + V)  (halfway vector)
specular = (N · H)^shininess
```

*Code:*
```javascript
const lightDir = /* normalized direction to light */;
const viewDir = rayDir.scale(-1);  // Direction to camera
const halfDir = lightDir.add(viewDir).normalize();
const specular = Math.pow(Math.max(0, normal.dot(halfDir)), SPECULAR_POWER);
```

*Why halfway vector?*
- *H* is halfway between light and view direction
- When surface normal aligns with H, perfect reflection occurs
- Cheaper to compute than full reflection

### Specular Power

```javascript
const SPECULAR_POWER = 30;
```

*Effect of power:*
- *Low (5-10)*: Large, diffuse highlights (matte surface)
- *Medium (20-40)*: Moderate highlights (plastic, polished wood)
- *High (100-1000)*: Tiny, intense highlights (mirror, metal)

*Math:*
- `0.9^30 ≈ 0.04` - even slight misalignment dims highlight
- `0.99^30 ≈ 0.74` - only very precise alignment stays bright
- Creates sharp, focused highlight

### Combining All Lighting

```javascript
color = [
    sphereColor[0] * (diffuse + AMBIENT_LIGHT) + 255 * specular,
    sphereColor[1] * (diffuse + AMBIENT_LIGHT) + 255 * specular,
    sphereColor[2] * (diffuse + AMBIENT_LIGHT) + 255 * specular
].map(c => Math.min(255, Math.max(0, c)));
```

*Components:*
1. *Base color* from texture: `sphereColor[i]`
2. *Diffuse + ambient* lighting: `(diffuse + AMBIENT_LIGHT)`
3. *Specular highlight*: `255 * specular` (white light)
4. *Clamping*: ensure 0-255 range



### Animation System: Vertical Bounce

```javascript
const bouncePhase = (time % BOUNCE_CYCLE_MS) / BOUNCE_CYCLE_MS;
const bounceY = BASE_Y + Math.abs(Math.sin(bouncePhase * Math.PI * 2)) * BOUNCE_HEIGHT;
```

*Breakdown:*
- `time % BOUNCE_CYCLE_MS`: time within current cycle (0 to BOUNCE_CYCLE_MS)
- Divide by BOUNCE_CYCLE_MS: normalize to 0-1
- Multiply by 2π: convert to 0-2π radians
- `Math.sin(...)`: oscillates -1 to 1
- `Math.abs(...)`: makes it 0 to 1 (always positive)
- Multiply by BOUNCE_HEIGHT: scale to desired bounce height
- Add BASE_Y: offset to base position

*Result:*
```
Height
  ^
  |     __        __
  |   /    \    /    \
  |__|______|__|______|___> Time
     0    0.5   1    1.5
```

Sphere bounces up and down smoothly.

### Horizontal Bounce

```javascript
const horizontalPhase = (time % HORIZONTAL_BOUNCE_CYCLE_MS) / HORIZONTAL_BOUNCE_CYCLE_MS;
const bounceX = Math.sin(horizontalPhase * Math.PI * 2) * HORIZONTAL_BOUNCE_AMPLITUDE;
```

*Difference from vertical:*
- *No `Math.abs()`*: oscillates negative to positive
- *Different cycle time*: creates variety
- *Result*: moves left-right while bouncing up-down

### Why Different Cycle Times?

```javascript
BOUNCE_CYCLE_MS = 2000;              // 2 seconds
HORIZONTAL_BOUNCE_CYCLE_MS = 3000;   // 3 seconds
ROTATION_CYCLE_MS = 5000;            // 5 seconds
```

*Different periods create complex motion:*
- Not locked in sync
- Sphere traces unique path each loop
- More interesting visually
- Eventually repeats after LCM(2000, 3000, 5000) = 30 seconds

## Camera and Perspective

### Camera Setup

```javascript
const CAMERA_POS = { x: 0, y: 0, z: 3.5 };
const FOV = 60;  // Degrees
```

*Camera is at (0, 0, 3.5):*
- Centered horizontally (x = 0)
- Centered vertically (y = 0)
- 3.5 units in front of origin (z = 3.5)

### Field of View (FOV)

*FOV* determines how "wide" the camera sees:

```
    Small FOV (30°)        Large FOV (90°)
         |  |              \        /
         |  |               \      /
         |  |                \    /
        📷               📷
    (telephoto)           (wide-angle)
```

### Generating Camera Rays

```javascript
const scale = Math.tan(FOV * 0.5 * Math.PI / 180);
const aspect = WIDTH / HEIGHT;
const rayX = (2 * x / WIDTH - 1) * scale * aspect;
const rayY = (1 - 2 * y / HEIGHT) * scale;
const rayDir = new Vector(rayX, rayY, -1).normalize();
```

*Step-by-step:*

1. *Convert FOV to scale:*
   - `FOV * 0.5` = half the FOV angle
   - Convert to radians
   - `Math.tan(...)` gives scale factor

2. *Normalize pixel coordinates:*
   - `2 * x / WIDTH - 1`: converts x from [0, WIDTH] to [-1, 1]
   - `1 - 2 * y / HEIGHT`: converts y from [0, HEIGHT] to [1, -1] (flipped)

3. *Apply scale and aspect:*
   - Multiply by scale for FOV
   - Multiply x by aspect ratio for wide/tall screens

4. *Create ray direction:*
   - `(rayX, rayY, -1)`: point on image plane 1 unit in front of camera
   - `-1` for z means "into the screen"
   - Normalize to unit length

### Image Plane Concept

```
        Image Plane (z = -1)
            ___
           | • | (rayX, rayY, -1)
           |   |
           |___|
              |
              📷 Camera (0, 0, 0)
```

The image plane is a virtual rectangle 1 unit in front of the camera.
Each pixel corresponds to a point on this plane.



### Rendering Pipeline: Full Render Loop

```
1. For each pixel (x, y):
   v
2. Generate camera ray through pixel
   v
3. Calculate sphere position (animated)
   v
4. Test ray-sphere intersection
   ├─ If hit:
   │   ├─ Calculate UV coordinates
   │   ├─ Sample texture color
   │   ├─ Calculate normal vector
   │   ├─ Compute diffuse lighting
   │   ├─ Compute specular highlight
   │   └─ Combine into final color
   └─ Set color to background
   v
5. Test ray-plane intersection
   └─ If hit AND closer than sphere:
       ├─ Cast shadow ray to light
       ├─ Determine if in shadow
       ├─ Calculate plane lighting
       ├─ Cast reflection ray
       ├─ Test reflection ray for sphere hit
       ├─ Calculate reflection color
       └─ Blend plane color with reflection
   v
6. Write final color to pixel
   v
7. Repeat for all pixels
   v
8. Display frame
   v
9. requestAnimationFrame → loop
```

### Performance Characteristics

*Complexity:*
- *Per pixel*: 1 primary ray, potentially 1 shadow ray, 1 reflection ray
- *Total rays per frame*: 400×400 × 3 = 480,000 rays
- *At 60 FPS*: 28.8 million rays per second

*Why it's slow:*
- Each ray requires:
  - Quadratic equation solution
  - Square root calculation
  - Multiple dot products
  - Trigonometry for UV mapping
- No spatial acceleration structure (everything tested every ray)

*Optimizations possible:*
- Bounding volume hierarchies (BVH)
- Spatial partitioning (octrees, kd-trees)
- Early ray termination
- GPU acceleration (WebGL fragment shaders)



### Texture Upload System: HTML File Input

```html
<input type="file" id="textureInput" accept="image/*">
```

*Accepts* any image format supported by browser (jpg, png, gif, webp, etc.)

### Loading Image

```javascript
textureInput.addEventListener('change', (event) => {
    const file = event.target.files[0];
    const reader = new FileReader();
    reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
            textureCanvas.width = img.width;
            textureCanvas.height = img.height;
            textureCtx = textureCanvas.getContext('2d');
            textureCtx.drawImage(img, 0, 0);
            textureImage = textureCtx.getImageData(0, 0, img.width, img.height);
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
});
```

*Process:*
1. *FileReader* reads file as Data URL
2. Create *Image* element, set source to Data URL
3. When image loads, draw to *off-screen canvas*
4. Extract *ImageData* (raw RGBA pixel array)
5. Store for texture lookups

### Why Off-Screen Canvas?

```javascript
const textureCanvas = document.createElement('canvas');
```

*Not added to DOM* - purely for pixel manipulation:
- Draw image to canvas
- Extract raw pixel data
- Access individual RGBA values efficiently

### Default Texture

```javascript
if (!textureImage) return [255, 255, 255];
```

Before image is loaded, sphere is rendered as *white*.
Could be changed to checkerboard, solid color, etc.



### Vector Math Utilities: Vector Class

```javascript
class Vector {
    constructor(x, y, z) {
        this.x = x;
        this.y = y;
        this.z = z;
    }
}
```

Cleaner than using arrays `[x, y, z]` - more readable, chainable methods.

### Vector Operations

*Subtraction:*
```javascript
subtract(v) {
    return new Vector(this.x - v.x, this.y - v.y, this.z - v.z);
}
```
Used for: ray directions, normals, relative positions

*Addition:*
```javascript
add(v) {
    return new Vector(this.x + v.x, this.y + v.y, this.z + v.z);
}
```
Used for: moving points along rays

*Scaling:*
```javascript
scale(s) {
    return new Vector(this.x * s, this.y * s, this.z * s);
}
```
Used for: multiplying by t parameter, adjusting magnitudes

*Dot Product:*
```javascript
dot(v) {
    return this.x * v.x + this.y * v.y + this.z * v.z;
}
```
Used for: lighting calculations, angles, projections

*Normalization:*
```javascript
normalize() {
    const mag = Math.sqrt(this.dot(this));
    return mag > 0 ? new Vector(this.x / mag, this.y / mag, this.z / mag) : this;
}
```
Used for: converting directions to unit vectors (length 1)



### Constants and Tuning: Scene Constants

```javascript
const BOUNCE_CYCLE_MS = 2000;              // Vertical bounce period
const BOUNCE_HEIGHT = 1.0;                 // How high sphere bounces
const BASE_Y = -0.5;                       // Resting position
const HORIZONTAL_BOUNCE_CYCLE_MS = 3000;   // Horizontal motion period
const HORIZONTAL_BOUNCE_AMPLITUDE = 0.8;   // How far left/right
const ROTATION_CYCLE_MS = 5000;            // Texture rotation period
```

*Experiment by changing:*
- Faster bounces: reduce BOUNCE_CYCLE_MS
- Higher bounces: increase BOUNCE_HEIGHT
- Wider motion: increase HORIZONTAL_BOUNCE_AMPLITUDE

### Lighting Constants

```javascript
const LIGHT_POS = { x: 2, y: 3, z: 4 };  // Upper-right-front
const AMBIENT_LIGHT = 0.2;                // 20% minimum brightness
const SPECULAR_POWER = 30;                // Shininess
```

*Effects of changing:*
- Move light: changes shadow direction, highlight position
- Increase ambient: brightens shadows (less contrast)
- Increase specular power: sharper, smaller highlights

### Material Constants

```javascript
const PLANE_REFLECTION = 0.4;  // 40% reflective floor
```

*Effects:*
- 0.0: Matte floor (no reflection)
- 0.5: Half mirror
- 1.0: Perfect mirror

### Rendering Constants

```javascript
const EPSILON = 0.01;  // Minimum ray distance
```

*Critical for:*
- Preventing self-intersection
- Ensuring rays leave surface before next collision test


### Demo

This demo teaches:

1. *Raytracing fundamentals* - how physically-based rendering works
2. *Geometric intersections* - solving ray-sphere, ray-plane equations
3. *Quadratic equations* - practical application in graphics
4. *Shadow mapping* - occlusion testing with shadow rays
5. *Reflection* - recursive ray bouncing
6. *Texture mapping* - UV coordinates on spherical surfaces
7. *Lighting models* - diffuse (Lambert), specular (Blinn-Phong)
8. *Vector mathematics* - dot products, normalization in practice
9. *Animation* - parametric motion with sine waves
10. *Performance considerations* - why raytracing is expensive


### 1. Multiple Spheres

```javascript
const spheres = [
    { center: {x: 0, y: 0, z: 0}, radius: 1, color: [255, 0, 0] },
    { center: {x: 2, y: 0, z: -1}, radius: 0.5, color: [0, 255, 0] }
];
```

Test ray against all spheres, render closest hit.

### 2. Soft Shadows

Cast multiple shadow rays to area light:

```javascript
const shadowSamples = 16;
let shadowAmount = 0;
for (let i = 0; i < shadowSamples; i++) {
    const randomLightPos = jitterLightPosition(LIGHT_POS, 0.5);
    if (shadowRayHitsSphere(randomLightPos)) shadowAmount++;
}
const shadowFactor = shadowAmount / shadowSamples;
```

### 3. Depth of Field

Simulate camera lens by jittering ray origins:

```javascript
const focalDistance = 3.0;
const aperture = 0.1;
const focalPoint = CAMERA_POS.add(rayDir.scale(focalDistance));
const randomOffset = randomInCircle(aperture);
const newOrigin = CAMERA_POS.add(randomOffset);
const newDir = focalPoint.subtract(newOrigin).normalize();
```

### 4. Refraction (Glass)

Add ray bending through transparent objects:

```javascript
const refractDir = refract(rayDir, normal, 1.0, 1.5); // Air to glass
const refractedColor = trace(hitPoint, refractDir, depth + 1);
```

### 5. Environment Mapping

Use skybox texture for background and reflections:

```javascript
function getEnvironmentColor(direction) {
    const u = 0.5 + Math.atan2(direction.z, direction.x) / (2 * Math.PI);
    const v = 0.5 - Math.asin(direction.y) / Math.PI;
    return sampleTexture(environmentMap, u, v);
}
```

### 6. Normal Mapping

Add surface detail without geometry:

```javascript
const normalFromMap = sampleNormalMap(u, v);
const perturbedNormal = applyNormalMap(geometricNormal, normalFromMap, tangent, bitangent);
```

### 7. Antialiasing

Average multiple rays per pixel:

```javascript
for (let sy = 0; sy < 2; sy++) {
    for (let sx = 0; sx < 2; sx++) {
        const jitterX = x + sx * 0.5;
        const jitterY = y + sy * 0.5;
        colorSum = colorSum.add(traceRay(jitterX, jitterY, time));
    }
}
finalColor = colorSum.scale(0.25); // Average 4 samples
```

### 8. GPU Acceleration

Port to WebGL fragment shader:

```glsl
void main() {
    vec2 uv = gl_FragCoord.xy / resolution;
    vec3 rayDir = getRayDirection(uv);
    vec3 color = traceRay(cameraPos, rayDir);
    gl_FragColor = vec4(color, 1.0);
}
```

*Benefit:* 100-1000× faster on modern GPUs



### 1. Not Normalizing Directions

*Problem:* Ray directions or normals not unit length
*Result:* Incorrect lighting, intersection bugs
*Fix:* Always `.normalize()` after creating/transforming directions

### 2. Self-Intersection

*Problem:* Forgetting EPSILON offset when casting shadow/reflection rays
*Result:* Surface appears shadowed by itself, sparkly artifacts
*Fix:* `origin = hitPoint.add(normal.scale(EPSILON))`

### 3. Negative t Values

*Problem:* Using negative t (hits behind camera)
*Result:* Objects appear in front when they're behind
*Fix:* `if (t > EPSILON)` checks

### 4. Integer Division

*Problem:* `(y * WIDTH + x) * 4` using floating point
*Result:* Wrong array indices, garbage pixels
*Fix:* Ensure x and y are integers (loop variables)

### 5. Clamping Colors

*Problem:* Specular highlights create values > 255
*Result:* Overflow, wrong colors
*Fix:* `.map(c => Math.min(255, Math.max(0, c)))`

### 6. Reflection Direction

*Problem:* Wrong sign in reflection formula
*Result:* Rays bounce in wrong direction
*Fix:* `R = I - 2(I·N)N` (note the minus)


