
## Simple 3D Cube

In the fixed version of the cube we used:

```javascript
const Rx = rotationMatrixX(Math.PI / 6);
const Ry = rotationMatrixY(Math.PI / 6);
```

- Transformation is done once, and then the cube is drawn.


### Automatically Rotating Cube

What’s added:
- A main animation loop using requestAnimationFrame(draw) to continuously redraw.
- Rotation angles angleX and angleY are incremented over time:

```javascript
angleX += 0.01;
angleY += 0.02;
```

Effect:
- The cube spins slowly and smoothly.
- Viewer sees it rotating in 3D as if it’s turning in space.

New concepts introduced:
- Animation loop.
- Dynamic (time-dependent) transformations.
- No user interaction.


### User-Controlled Cube with Angle Display

What’s added on top of Version 1:
- Mouse interaction: User can click and drag to rotate the cube.
- Event listeners for mousedown, mousemove, and mouseup track mouse dragging.
- Live update of angles (in degrees) is shown in a <div>:

```javascript
info.textContent = `angleX: ${(angleX * 180/Math.PI).toFixed(1)}°, angleY: ...`
```

- Rotation angle is based on how far the mouse has moved.

Effect:
- Viewer has full control over cube orientation.
- Rotation is responsive to user actions.
- Angles are displayed numerically to give feedback.

New concepts introduced:
- User interaction with canvas.
- Mapping mouse movement to rotation.
- Real-time status output (HUD-style feedback).


### Summary Table

|Feature                         | Static Cube | Auto-Rotation (v1) | User Control (v2)|
|-------------------------------|-------------|---------------------|-------------------|
|Draws 3D cube                  | [x]         | [x]                 | [x]|
|Rotation via matrix            | [x]         | [x]                 | [x]|
|Animation loop                 | [ ]         | [x]                 | [x]|
|Time-based angle update        | [ ]         | [x]                 | [ ]|
|User interaction (mouse drag)  | [ ]         | [ ]                 | [x]|
|Shows angles (HUD)             | [ ]         | [ ]                 | [x]|

