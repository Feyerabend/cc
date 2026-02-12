
## Simple 3D Cube

This HTML + JavaScript code draws the vertices of a 3D cube as
dots on a 2D `<canvas>` using basic linear algebra and perspective
projection without any 3D library. It shows how to rotate, transform,
and project 3D points onto a 2D screen.

The key idea is:
1. Represent the cube in 3D using points (vertices).
2. Rotate the cube in 3D space using rotation matrices.
3. Project the 3D points to 2D so they can be drawn.
4. Draw dots at these projected points with coordinate labels.


### Mathematics and Code

__1. 3D Points (Vertices)__

Each point is [x, y, z], and the cube is defined with 8 corners:

```javascript
const vertices = [
    [-1, -1, -1], [ 1, -1, -1],
    [ 1,  1, -1], [-1,  1, -1],
    [-1, -1,  1], [ 1, -1,  1],
    [ 1,  1,  1], [-1,  1,  1]
];
```
- This gives a unit cube centered at the origin.
- The back face is at z = -1, front face at z = 1.

__2. Rotation in 3D__

Rotation matrices are used to simulate 3D rotation.

X-axis rotation matrix:

```javascript
function rotationMatrixX(angle) {
    const c = Math.cos(angle), s = Math.sin(angle);
    return [
        [1,  0,  0],
        [0,  c, -s],
        [0,  s,  c]
    ];
}
```

This rotates the point around the x-axis, affecting y and z.

Y-axis rotation matrix:

```javascript
function rotationMatrixY(angle) {
    const c = Math.cos(angle), s = Math.sin(angle);
    return [
        [ c,  0,  s],
        [ 0,  1,  0],
        [-s,  0,  c]
    ];
}
```

Rotates around y-axis, affecting x and z.

Applying a matrix:

```javascript
function matrixVectorMult(m, v) {
    return [
        m[0][0]*v[0] + m[0][1]*v[1] + m[0][2]*v[2],
        m[1][0]*v[0] + m[1][1]*v[1] + m[1][2]*v[2],
        m[2][0]*v[0] + m[2][1]*v[1] + m[2][2]*v[2],
    ];
}
```

This function multiplies a 3x3 matrix with a 3D vector.

__3. Perspective Projection__

This simulates depth--objects farther away look smaller:

```javascript
function project([x, y, z]) {
    const scale = 150 / (5 - z);
    return [
         x * scale + width  / 2,
        -y * scale + height / 2
    ];
}
```

- scale = 150 / (5 - z) decreases as z increases (further away).
- Result is 2D coordinates centered on the canvas.

__4. Draw the Vertices__

```javascript
function drawCube() {
    ctx.clearRect(0, 0, width, height);

    const Rx = rotationMatrixX(Math.PI / 6);
    const Ry = rotationMatrixY(Math.PI / 6);
    
    const transformed = vertices.map(v =>
        matrixVectorMult(Ry, matrixVectorMult(Rx, v))
    );

    transformed.forEach((vertex, i) => {
        const [x, y] = project(vertex);
        ctx.fillStyle = "#00ccff";
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, Math.PI * 2);
        ctx.fill();
        
        // Draw coordinate labels on canvas
        ctx.fillStyle = "#00ccff";
        ctx.font = "12px monospace";
        ctx.fillText(`${i}: (${x.toFixed(0)},${y.toFixed(0)})`, x + 10, y + 5);
    });
}
```
- Each vertex is first rotated (X then Y).
- Then projected to 2D.
- Finally, dots are drawn at the projected points with coordinate labels.


### Summary

This is a minimal 3D point visualizer written in plain JavaScript:
- It defines 3D geometry (cube vertices).
- Applies 3D rotation using matrix math.
- Projects the result into 2D using perspective.
- Draws dots on a `<canvas>` with coordinate labels.

