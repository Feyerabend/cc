
### Shadow Casting and Lighting Demonstration

This interactive demo shows how *realistic shadows* are cast from a point light
source onto a floor plane, combined with *diffuse lighting* on the cube faces.



### Key Features

1. *Point Light Source* - visible glowing sphere showing light position
2. *Ray-Cast Shadows* - proper planar projection onto floor
3. *Diffuse Lighting* - faces brighten/darken based on angle to light
4. *Light Ray Visualization* - toggle to show how shadows form (educational)
5. *Interactive Rotation* - drag to rotate cube and see shadow change
6. *Grid Floor* - depth perception and spatial reference



### How Shadows Work

#### The Principle

A shadow is formed when light rays from a *point source*
are blocked by an object and cannot reach a surface.

```
        ☀ Light Source
       /|\
      / | \
     /  |  \
    / Cube  \
   /    □    \
  /___________\
 Floor  Shadow
```

#### Ray Casting Method

For each vertex of the cube:
1. *Cast a ray* from the light source through the vertex
2. *Find intersection* with the floor plane (y = floorLevel)
3. *Mark this point* - it's part of the shadow boundary

#### Mathematical Formula

Given:
- Light position: *L = (Lx, Ly, Lz)*
- Cube vertex: *V = (Vx, Vy, Vz)*
- Floor plane: *y = floorLevel* (e.g., y = -2)

The ray equation:
```
P(t) = L + t × (V - L)
```

Where *t* is a parameter (t=0 at light, t=1 at vertex, t>1 beyond vertex).

To find where this ray hits the floor (y = floorLevel):
```
Py(t) = Ly + t × (Vy - Ly) = floorLevel

Solving for t:
t = (floorLevel - Ly) / (Vy - Ly)
```

The shadow point on the floor:
```
Sx = Lx + t × (Vx - Lx)
Sy = floorLevel
Sz = Lz + t × (Vz - Lz)
```

#### Code Implementation

```javascript
function projectShadowPoint([x, y, z]) {
    // Direction from light to point
    const dx = x - lightPos[0];
    const dy = y - lightPos[1];
    const dz = z - lightPos[2];
    
    // Parameter t where ray hits floor
    const t = (floorLevel - lightPos[1]) / dy;
    
    // Shadow position
    return [
        lightPos[0] + t * dx,
        floorLevel,
        lightPos[2] + t * dz
    ];
}
```



### Convex Hull for Shadow Silhouette

#### The Problem

When we project all 8 cube vertices onto the floor, we get 8 shadow points.
But connecting them in cube-vertex order creates a weird shape with internal divisions.

*Solution*: Use a *convex hull* algorithm to find only the *outer boundary* points.

#### What is a Convex Hull?

The convex hull is the smallest convex polygon that contains
all points--like stretching a rubber band around the points.

```
Points:     * * *        Convex Hull:    /-\
            *   *                       /   \
            * * *                       \___/
```

#### Graham Scan Algorithm

We use a variation of the Graham scan:
1. *Sort points* by x-coordinate (then y)
2. *Build lower hull* - walk left to right, removing points that create right turns
3. *Build upper hull* - walk right to left, removing points that create right turns
4. *Combine* lower and upper hulls

#### Cross Product for Turn Detection
To determine if three points make a left or right turn:

```javascript
cross(O, A, B) = (A.x - O.x) × (B.y - O.y) - (A.y - O.y) × (B.x - O.x)
```

- *Positive*: Left turn → keep point
- *Negative or Zero*: Right turn → remove previous point

#### Result

The convex hull gives us the *actual silhouette* of the shadow--just the outer boundary points,
which we connect to create a single filled polygon.



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

- *θ = 0°* (facing light): cos(0°) = 1 → fully bright
- *θ = 45°*: cos(45°) ≈ 0.707 → 70% bright
- *θ = 90°* (perpendicular): cos(90°) = 0 → no direct light
- *θ > 90°* (facing away): cos(θ) < 0 → clamped to 0


#### Ambient + Diffuse Model

We add *ambient light* so faces never go completely black:

```javascript
const ambient = 0.3;  // 30% minimum brightness
const diffuse = Math.max(0, dotProduct(normal, lightDir));
const brightness = ambient + (1 - ambient) × diffuse;
```

This gives brightness from *0.3* (dark side) to *1.0* (bright side).

#### Transforming Normals

When the cube rotates, the face normals must rotate too:

```javascript
const transformedNormals = faceNormals.map(n => 
    normalize(matrixVectorMult(Ry, matrixVectorMult(Rx, n)))
);
```

*Important*: Always normalize after transformation to keep it a unit vector.

#### Adjusting Color Brightness

Multiply RGB components by brightness:

```javascript
function adjustBrightness(color, brightness) {
    const r = parseInt(color.slice(1,3), 16);
    const g = parseInt(color.slice(3,5), 16);
    const b = parseInt(color.slice(5,7), 16);
    
    return `rgb(${Math.floor(r * brightness)}, 
                 ${Math.floor(g * brightness)}, 
                 ${Math.floor(b * brightness)})`;
}
```



### Light Ray Visualisation

#### Toggle Button

Click *"Show Light Rays"* to toggle educational overlays:

*When ON* (default):
- Dashed yellow lines from light → cube vertex → floor
- Yellow dots marking shadow points on floor
- Shows exactly how shadow is formed

*When OFF*:
- Clean view with just cube, shadow, and light
- Better for appreciating the final result

#### What The Rays Show

Each ray demonstrates:
1. Light travels from source in straight lines
2. Light is blocked by cube vertices
3. Shadow forms where light cannot reach
4. All shadow points lie on the floor plane



### Rendering Pipeline

The complete process each frame:

```
1. Clear canvas
   v
2. Apply rotation matrices to cube vertices
   v
3. Apply rotation matrices to face normals
   v
4. Draw floor with grid
   v
5. Project shadow:
   - Cast rays through all 8 vertices
   - Find floor intersections
   - Compute convex hull
   - Fill shadow polygon
   v
6. [If rays enabled] Draw light rays and shadow points
   v
7. For each face:
   - Calculate lighting (N · L)
   - Adjust color brightness
   - Sort by depth (painter's algorithm)
   - Draw face
   v
8. Draw light source indicator
```



### Light Position Effects

Current: `lightPos = [3, 5, 3]`

#### X Coordinate (left/right)
- *x = -5*: Light far left → shadow extends right
- *x = 0*: Light centered → shadow centered
- *x = 5*: Light far right → shadow extends left

#### Y Coordinate (height)
- *y = 2*: Low light → long, stretched shadow
- *y = 5*: Medium height → moderate shadow
- *y = 10*: High light → short, compact shadow
- *y = 100*: Very high → shadow almost directly below cube

#### Z Coordinate (front/back)
- *z = -5*: Light behind → shadow toward camera
- *z = 0*: Light at cube depth
- *z = 5*: Light in front → shadow away from camera



### Interactive Controls

#### Mouse Drag
- *Drag horizontally* → rotate around Y-axis (turn left/right)
- *Drag vertically* → rotate around X-axis (tilt up/down)
- *Release* → cursor changes back to grab

#### Toggle Button
- *Click* → show/hide light rays
- *Active state* → yellow background when rays visible



### Technical Details

#### Coordinate System
- *X-axis*: left (-) to right (+)
- *Y-axis*: down (-) to up (+)
- *Z-axis*: far (-) to near (+)

#### Floor Plane
- Fixed at *y = -2*
- Drawn from this point downward
- Grid helps show perspective

#### Perspective Projection
```javascript
scale = 150 / (5 - z)
screenX = x × scale + width/2
screenY = -y × scale + height/2
```

Objects closer (higher z) appear larger.



### Performance Considerations

#### Convex Hull Complexity
- *Time*: O(n log n) for n points
- For 8 cube vertices: very fast
- Could be optimized with pre-computed silhouettes for static geometry

#### Drawing Order
1. Floor (background)
2. Shadow (on floor)
3. Rays (if enabled)
4. Cube faces (painter's algorithm)
5. Light (foreground)

#### Frame Rate
- *60 FPS* typical on modern browsers
- `requestAnimationFrame` syncs with display refresh



### Educational Value

This demo teaches:
1. *Ray casting* - fundamental technique in graphics
2. *Planar projection* - how 3D→2D works for specific planes
3. *Convex hull* - computational geometry algorithm
4. *Lighting models* - basic Lambertian diffuse reflection
5. *Dot product* - angle calculation in 3D
6. *Painter's algorithm* - depth sorting for rendering



### Possible Extensions

#### 1. Multiple Light Sources
Add more lights with different colors:
```javascript
const lights = [
    {pos: [3, 5, 3], color: '#ffff00'},
    {pos: [-2, 4, -2], color: '#ff00ff'}
];
```

#### 2. Soft Shadows
Blur the shadow edges:
```javascript
ctx.shadowBlur = 10;
ctx.shadowColor = 'rgba(0,0,0,0.3)';
```

#### 3. Specular Highlights
Add shiny reflections (Phong/Blinn-Phong):
```javascript
const R = reflect(L, N);
const specular = Math.pow(max(0, R·V), shininess);
```

#### 4. Colored Shadows
Light color affects shadow tint:
```javascript
ctx.fillStyle = `rgba(${r}, ${g}, ${b}, 0.5)`;
```

#### 5. Shadow Attenuation
Fade shadow with distance from cube:
```javascript
const distance = length(cubePos - shadowPoint);
const opacity = max(0, 0.5 - distance × 0.05);
```

#### 6. Dynamic Light Control
Add sliders to move light position:
```html
<input type="range" id="lightX" min="-10" max="10" value="3">
<input type="range" id="lightY" min="2" max="15" value="5">
<input type="range" id="lightZ" min="-10" max="10" value="3">
```



### Summary

This demonstration combines:
- *Shadow casting* via ray-plane intersection
- *Convex hull* for proper silhouette
- *Diffuse lighting* using dot product
- *Interactive controls* for exploration
- *Educational visualization* of how light creates shadows

