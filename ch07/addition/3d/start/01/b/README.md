
## Simple 3D Cube

This HTML + JavaScript code draws a 3D cube on a 2D <canvas> using basic linear algebra and perspective
projection any 3D library. It shows how to rotate, transform, and project 3D points onto a 2D screen.

The key idea is:
1. Represent the cube in 3D using points (vertices).
2. Rotate the cube in 3D space using rotation matrices.
3. Project the 3D points to 2D so they can be drawn.
4. Draw lines (edges) between these projected points.


### Mathematics and Code

__1. 3D Points (Vertices)__

Each point is [x, y, z], and the cube is defined with 8 corners:

```javascript
const vertices = [
    [-1, -1, -1], [1, -1, -1],
    [1,  1, -1], [-1,  1, -1],
    [-1, -1,  1], [1, -1,  1],
    [1,  1,  1], [-1,  1,  1]
];
```
- This gives a unit cube centered at the origin.
- The back face is at z = -1, front face at z = 1.

__2. Edges__

Pairs of indices connecting vertices:

```javascript
const edges = [
    [0,1],[1,2],[2,3],[3,0], // back square
    [4,5],[5,6],[6,7],[7,4], // front square
    [0,4],[1,5],[2,6],[3,7]  // connections between front and back
];
```

__3. Rotation in 3D__

Rotation matrices are used to simulate 3D rotation.

X-axis rotation matrix:

```javascript
function rotationMatrixX(angle) {
    const c = Math.cos(angle), s = Math.sin(angle);
    return [
        [1, 0, 0],
        [0, c, -s],
        [0, s, c]
    ];
}
```

This rotates the point around the x-axis, affecting y and z.

Y-axis rotation matrix:

```javascript
function rotationMatrixY(angle) {
    const c = Math.cos(angle), s = Math.sin(angle);
    return [
        [c, 0, s],
        [0, 1, 0],
        [-s, 0, c]
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

__4. Perspective Projection__

This simulates depth — objects farther away look smaller:

```javascript
function project([x, y, z]) {
    const scale = 150 / (5 - z);
    return [
        x * scale + width / 2,
        -y * scale + height / 2
    ];
}
```

- scale = 150 / (5 - z) decreases as z increases (further away).
- Result is 2D coordinates centered on the canvas.

__5. Draw the Cube__

```javascript
function drawCube() {
    ctx.clearRect(0, 0, width, height);

    const Rx = rotationMatrixX(Math.PI / 6);
    const Ry = rotationMatrixY(Math.PI / 6);
    
    const transformed = vertices.map(v =>
        matrixVectorMult(Ry, matrixVectorMult(Rx, v))
    );

    edges.forEach(([a, b]) => {
        const [x1, y1] = project(transformed[a]);
        const [x2, y2] = project(transformed[b]);
        ctx.strokeStyle = "#00ccff";
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
    });
}
```
- Each vertex is first rotated (X then Y).
- Then projected to 2D.
- Finally, lines are drawn between projected points.


### Summary

This is a minimal 3D renderer written in plain JavaScript:
- It defines 3D geometry (cube).
- Applies 3D rotation using matrix math.
- Projects the result into 2D using perspective.
- Draws it on a <canvas>.

