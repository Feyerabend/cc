
## Rotatable Solid Cube with Filled Faces

This HTML + JavaScript code renders a 3D cube with solid, colored faces
that you can rotate with your mouse. It demonstrates face-based rendering
with depth sorting.


### Key Concepts

#### 1. From Wireframe to Solid Faces

*Wireframe rendering* draws only the edges of a cube
(lines connecting vertices).

*Solid rendering* fills in the faces of the cube with colors,
creating a truly 3D appearance.

The main difference:
- Wireframe: Draw lines between pairs of vertices (edges)
- Solid: Draw filled polygons defined by groups of vertices (faces)



### The Code Structure

#### 1. Vertices (Same as Before)

The 8 corners of the cube:

```javascript
const vertices = [
    [-1,-1,-1], [1,-1,-1], [1,1,-1], [-1,1,-1],  // back face (z = -1)
    [-1,-1,1],  [1,-1,1],  [1,1,1],  [-1,1,1]    // front face (z = 1)
];
```

#### 2. Faces

Each face is defined by *4 vertex indices* that form a square:

```javascript
const faces = [
    [0,1,2,3], // back face
    [4,5,6,7], // front face
    [0,1,5,4], // bottom face
    [2,3,7,6], // top face
    [0,3,7,4], // left face
    [1,2,6,5]  // right face
];
```

*How to read this:*
- `[0,1,2,3]` means "connect vertices 0, 1, 2, 3 to form a face"
- The order matters--vertices should be listed going around the
  face (clockwise or counterclockwise)

*Visual example of the back face:*
```
Vertex 3 (-1,1,-1) -------- Vertex 2 (1,1,-1)
       |                            |
       |         BACK FACE          |
       |                            |
Vertex 0 (-1,-1,-1) ------- Vertex 1 (1,-1,-1)
```

#### 3. Face Colors

Each face gets its own color:

```javascript
const colors = [
    '#ff5555',  // red - back
    '#55ff55',  // green - front
    '#5555ff',  // blue - bottom
    '#ffff55',  // yellow - top
    '#55ffff',  // cyan - left
    '#ff55ff'   // magenta - right
];
```



### The Painter's Algorithm

#### The Problem

When you have overlapping faces,
which one should be drawn on top?

If we draw them in a random order,
faces that should be hidden might appear in front!

#### The Solution: Depth Sorting

The *painter's algorithm* works like painting a canvas:
1. Paint the furthest objects first
2. Paint closer objects on top
3. Closer objects naturally cover further ones

#### Implementation

*Step 1: Calculate each face's depth*

```javascript
const faceDepths = faces.map((face, i) => {
    // Average Z-coordinate of all 4 vertices in this face
    const avgZ = face.reduce((sum, idx) => sum + transformed[idx][2], 0) / 4;
    return { index: i, depth: avgZ };
});
```

*Why average Z?*
- Each face has 4 vertices, each with its own Z coordinate
- We take the average to get a single depth value for the entire face
- Lower Z = further away, Higher Z = closer to viewer

*Step 2: Sort faces by depth*

```javascript
faceDepths.sort((a, b) => a.depth - b.depth);
```

This sorts from *furthest to closest* (smallest Z to largest Z).

*Step 3: Draw in sorted order*

```javascript
for (const {index} of faceDepths) {
    // Draw face[index]
    // Closer faces draw over further faces automatically
}
```



### Drawing Filled Faces

#### The Process

For each face:
1. *Begin a path* at the first vertex
2. *Draw lines* to each subsequent vertex
3. *Close the path* to complete the polygon
4. *Fill* with color
5. *Stroke* the outline

#### The Code

```javascript
for (const {index} of faceDepths) {
    const face = faces[index];
    
    // Start drawing path
    ctx.beginPath();
    ctx.moveTo(projected[face[0]][0], projected[face[0]][1]);
    
    // Draw lines to other vertices
    for (let i = 1; i < face.length; i++) {
        ctx.lineTo(projected[face[i]][0], projected[face[i]][1]);
    }
    
    // Close the shape
    ctx.closePath();
    
    // Fill with solid colour
    ctx.fillStyle = colors[index];
    ctx.fill();
    
    // Draw black outline
    ctx.strokeStyle = "#000";
    ctx.stroke();
}
```

#### Why `closePath()`?

This connects the last vertex back to the first vertex, completing the polygon.

Without it, you'd have 3 sides instead of 4!



### Mouse Interaction

#### How It Works

The cube rotates based on mouse drag:

```javascript
canvas.addEventListener('mousemove', e => {
    if (!isDragging) return;
    
    const dx = e.clientX - lastX;  // horizontal movement
    const dy = e.clientY - lastY;  // vertical movement
    
    angleY += dx * 0.01;  // horizontal drag -> rotate around Y
    angleX += dy * 0.01;  // vertical drag -> rotate around X
    
    // Update display
    hud.textContent = `Angles - X: ${Math.round(angleX * 180 / Math.PI)}°, 
                                Y: ${Math.round(angleY * 180 / Math.PI)}°`;
});
```

*The mapping:*
- Drag *left/right* -> rotate around *Y-axis* (like turning your head)
- Drag *up/down* -> rotate around *X-axis* (like nodding your head)

#### The Multiplier `0.01`

This controls sensitivity:
- Smaller value = slower rotation (more precise)
- Larger value = faster rotation (more responsive)



### Animation Loop

```javascript
function animate() {
    drawCube();
    requestAnimationFrame(animate);
}

animate();
```

This creates a *continuous render loop*:
1. Draw the cube at current angles
2. Request the browser to call `animate()` again before next frame
3. Repeat indefinitely

*Why?* Even though the cube only changes when you drag it,
we redraw every frame so any mouse movement immediately shows the rotation.



### Complete Rendering Pipeline

Here's what happens each frame:

```
1. Get current rotation angles (angleX, angleY)
   v
2. Create rotation matrices from angles
   v
3. Transform all 8 vertices (rotate in 3D)
   v
4. Project transformed vertices to 2D
   v
5. Calculate depth of each face (average Z)
   v
6. Sort faces by depth (furthest first)
   v
7. Draw each face in order:
   - Draw polygon connecting 4 vertices
   - Fill with solid color
   - Stroke outline
   v
8. Display on screen
```



### Key Differences from Wireframe

| Aspect | Wireframe | Solid |
|--------|-----------|-------|
| *What's drawn* | Edges (lines) | Faces (polygons) |
| *Data structure* | Edge pairs `[0,1]` | Face vertices `[0,1,2,3]` |
| *Depth sorting* | Not needed | Critical (painter's algorithm) |
| *Performance* | Faster (12 lines) | Slower (6 polygons) |
| *Visual result* | See-through skeleton | Opaque solid object |



### Mathematical Details

#### Face Normal

Each face has a *normal vector* pointing perpendicular to it.

*If* we computed normals, we could do *backface culling*:
- Only draw faces pointing toward the camera
- Skip faces pointing away (back of the cube)
- This is more efficient than painter's algorithm

*How to compute a normal:*
```javascript
// For face with vertices v0, v1, v2
edge1 = v1 - v0
edge2 = v2 - v0
normal = cross_product(edge1, edge2)
```

#### Why We Use Average Z Instead

For a cube, all faces are flat, so averaging the Z-coordinates
of vertices gives us a good depth estimate:

```
Face depth ≈ (z₀ + z₁ + z₂ + z₃) / 4
```

This is simpler than computing normals and works well for convex objects.



### Extensions & Improvements

#### 1. Add Z-Axis Rotation

Currently only X and Y rotation:

```javascript
function rotationMatrixZ(angle) {
    const c = Math.cos(angle), s = Math.sin(angle);
    return [
        [c, -s,  0],
        [s,  c,  0],
        [0,  0,  1]
    ];
}
```

#### 2. Add Lighting

Make faces brighter/darker based on angle to light:

```javascript
// Compute face normal
const normal = computeNormal(face);

// Light direction (e.g., from top-right-front)
const light = [1, 1, 1];

// Dot product gives brightness
const brightness = dotProduct(normal, light);

// Adjust colour
ctx.fillStyle = adjustBrightness(colors[index], brightness);
```

#### 3. Smoother Rotation

Add easing for natural feel:

```javascript
let targetAngleX = 0, targetAngleY = 0;

function animate() {
    angleX += (targetAngleX - angleX) * 0.1;  // ease toward target
    angleY += (targetAngleY - angleY) * 0.1;
    drawCube();
    requestAnimationFrame(animate);
}
```

#### 4. Touch Support

Add touch events for mobile:

```javascript
canvas.addEventListener('touchstart', e => {
    const touch = e.touches[0];
    lastX = touch.clientX;
    lastY = touch.clientY;
});

canvas.addEventListener('touchmove', e => {
    e.preventDefault();
    const touch = e.touches[0];
    // .. same rotation logic
});
```



### Summary

This code demonstrates:
- *Face-based 3D rendering* (vs edge-based wireframes)
- *Painter's algorithm* for proper depth sorting
- *Solid filled polygons* with colours
- *Interactive rotation* via mouse drag
- *Real-time animation* with requestAnimationFrame

*It's a complete minimal 3D renderer with no external libraries.*

