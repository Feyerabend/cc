
## Mathematics of 3D Cube Rendering

This document explains mathematical concepts needed to render a 3D cube on a 2D screen,
from 3D coordinate representation to final 2D projection.



### 1. 3D Coordinate System

#### Cartesian Coordinates
A point in 3D space is represented by three coordinates: *P = (x, y, z)*

- *x-axis*: left-right (negative to positive)
- *y-axis*: down-up (negative to positive)
- *z-axis*: far-near (negative to positive, towards viewer)

#### The Cube
A unit cube centered at the origin has 8 vertices at all combinations of +/-1:
-
```
Vertex 0: (-1, -1, -1)  — back-bottom-left
Vertex 1: ( 1, -1, -1)  — back-bottom-right
Vertex 2: ( 1,  1, -1)  — back-top-right
Vertex 3: (-1,  1, -1)  — back-top-left
Vertex 4: (-1, -1,  1)  — front-bottom-left
Vertex 5: ( 1, -1,  1)  — front-bottom-right
Vertex 6: ( 1,  1,  1)  — front-top-right
Vertex 7: (-1,  1,  1)  — front-top-left
```



### 2. 3D Rotation Using Matrices

To rotate objects in 3D, we use *rotation matrices*.
These are 3×3 matrices that transform a 3D point.

#### Matrix-Vector Multiplication

Given a 3×3 matrix *M* and a 3D vector *v = (x, y, z)*, the multiplication *M · v* produces a new vector:

```
         [m₀₀  m₀₁  m₀₂]   [x]   [m₀₀·x + m₀₁·y + m₀₂·z]
M · v =  [m₁₀  m₁₁  m₁₂] · [y] = [m₁₀·x + m₁₁·y + m₁₂·z]
         [m₂₀  m₂₁  m₂₂]   [z]   [m₂₀·x + m₂₁·y + m₂₂·z]
```

#### Rotation Around X-Axis

Rotating by angle *θ* around the x-axis:

```
         [1    0       0   ]
Rₓ(θ) =  [0   cos(θ) -sin(θ)]
         [0   sin(θ)  cos(θ)]
```

*Effect*:
- x-coordinate stays the same
- y and z rotate in the yz-plane

*Example*: Rotating point (0, 1, 0) by 90° (π/2 radians):
```
Rₓ(π/2) · [0, 1, 0] = [0, 0, 1]
```
The point moves from +y to +z axis.

#### Rotation Around Y-Axis

Rotating by angle *θ* around the y-axis:

```
         [ cos(θ)  0  sin(θ)]
Rᵧ(θ) =  [   0     1    0   ]
         [-sin(θ)  0  cos(θ)]
```

*Effect*:
- y-coordinate stays the same
- x and z rotate in the xz-plane

*Example*: Rotating point (1, 0, 0) by 90° (π/2 radians):
```
Rᵧ(π/2) · [1, 0, 0] = [0, 0, -1]
```
The point moves from +x to -z axis.

#### Rotation Around Z-Axis

Rotating by angle *θ* around the z-axis:

```
         [cos(θ) -sin(θ)   0]
Rᵧ(θ) =  [sin(θ)  cos(θ)   0]
         [  0       0      1]
```

*Effect*:
- z-coordinate stays the same
- x and y rotate in the xy-plane

#### Combining Rotations

To apply multiple rotations, multiply the matrices together, then apply to the vector:

```
v' = Rᵧ(θᵧ) · Rₓ(θₓ) · v
```

*Important*: Matrix multiplication is *not commutative*, meaning:
```
Rᵧ · Rₓ ≠ Rₓ · Rᵧ
```

The order matters! Rotating around X then Y gives a different result than Y then X.



### 3. Perspective Projection

#### The Problem
We need to convert 3D coordinates (x, y, z) into 2D screen coordinates (x', y').

#### The Camera Model

Imagine a camera at position (0, 0, d) looking toward the origin, where d is the camera distance.

The projection plane (screen) is perpendicular to the z-axis at some distance from the camera.

#### Similar Triangles

Perspective projection uses the principle of *similar triangles*:

```
      Camera                Screen              Object
        |                     |                   |
     (0,0,d)               (0,0,0)             (x,y,z)
        |                     |                   |
        +---------------------+---------+---------+
             distance = d          distance = d-z
```

By similar triangles:
```
x' / x = d / (d - z)
y' / y = d / (d - z)
```

Solving for x' and y':
```
x' = x · d / (d - z)
y' = y · d / (d - z)
```

#### Simplification

Define *scale factor* s:
```
s = d / (d - z)
```

Then:
```
x' = x · s
y' = y · s
```

#### Why This Creates Perspective

- When *z is small* (far from camera): d - z ≈ d, so s ≈ 1 -> objects appear normal size
- When *z is large* (close to camera): d - z is small, so s is large -> objects appear larger
- When *z is negative* (behind camera): d - z > d, so s < 1 -> objects appear smaller

This mimics how our eyes see the world: closer objects appear larger.

#### Screen Centering

The projection gives coordinates centered at (0, 0).
To center on a screen of width W and height H:

```
screen_x = x' + W/2
screen_y = -y' + H/2    (flip y because screen y increases downward)
```

#### Example Calculation

Given:
- Point: (2, 1, 3)
- Camera distance: d = 5
- Screen: 600×600 pixels

```
s = 5 / (5 - 3) = 5/2 = 2.5

x' = 2 · 2.5 = 5
y' = 1 · 2.5 = 2.5

screen_x = 5 + 300 = 305
screen_y = -2.5 + 300 = 297.5
```



### 4. The Complete Pipeline

To render a 3D cube:

#### Step 1: Define Geometry
```
vertices = [
    (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1,-1),
    (-1, -1,  1), (1, -1,  1), (1, 1,  1), (-1, 1, 1)
]
```

#### Step 2: Apply Rotations
For each vertex v:
```
v_rotated = Rᵧ(angle_y) · Rₓ(angle_x) · v
```

Example with angle_x = angle_y = π/6 (30°):
```
Rₓ = [1     0        0    ]
     [0     0.866   -0.5  ]
     [0     0.5      0.866]

Rᵧ = [ 0.866   0    0.5  ]
     [ 0       1    0    ]
     [-0.5     0    0.866]

For v = (1, 1, -1):
  v_x = Rₓ · v = (1, 1.366, -0.366)
  v_rotated = Rᵧ · v_x = (1.049, 1.366, -1.232)
```

#### Step 3: Project to 2D
For each rotated vertex (x, y, z):
```
s = d / (d - z)
 x_2d = x · s + screen_width  / 2
y_2d = -y · s + screen_height / 2
```

Example with d=5, screen=600×600, v=(1.049, 1.366, -1.232):
```
s = 5 / (5 - (-1.232)) = 5 / 6.232 = 0.802

x_2d =  1.049 · 0.802 + 300 = 341.4
y_2d = -1.366 · 0.802 + 300 = 298.9
```

#### Step 4: Draw
Plot dots at the projected (x_2d, y_2d) coordinates.



### 5. Key Mathematical Properties

#### Homogeneous Coordinates
The projection can also be expressed using 4D homogeneous coordinates:
```
[x]      [x']
[y]  ->  [y']
[z]      [z']
[1]      [w]

Then: screen_x = x'/w, screen_y = y'/w
```

#### Field of View
The ratio d/screen_width controls the field of view (FOV):
- Larger d -> narrower FOV (telephoto lens)
- Smaller d -> wider FOV (wide-angle lens)

#### Depth Buffer
The z-coordinate after rotation determines which objects are in front.
This is used in 3D graphics for hidden surface removal.



### 6. Summary of Formulas

*3D Rotation (X-axis)*:
```
[x']   [1      0        0   ] [x]
[y'] = [0    cos(θ)  -sin(θ)] [y]
[z']   [0    sin(θ)   cos(θ)] [z]
```

*3D Rotation (Y-axis)*:
```
[x']   [ cos(θ)  0   sin(θ)] [x]
[y'] = [   0     1     0   ] [y]
[z']   [-sin(θ)  0   cos(θ)] [z]
```

*Perspective Projection*:
```
scale = d / (d - z)
x_screen =  x · scale + screen_width  / 2
y_screen = -y · scale + screen_height / 2
```



### 7. Extensions

#### Multiple Rotations
Combine rotations by multiplying matrices:
```
R_combined = Rz(θz) · Ry(θy) · Rx(θx)
```

#### Translation
Move the cube in 3D by adding a translation vector:
```
v_translated = v + T, where T = (tx, ty, tz)
```

#### Scaling
Make the cube larger or smaller:
```
v_scaled = s · v, where s is a scalar
```

#### Animation
Vary the rotation angles over time:
```
angle_x(t) = ωx · t
angle_y(t) = ωy · t
```
where ωx, ωy are angular velocities.


*This covers the mathematics needed to render a 3D cube on a 2D screen.*
