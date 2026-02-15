
## Raytracing a Sphere

This explains the mathematics in simple terms. You'll see how each concept helps create the image
on the canvas and where it appears in the code. The renderer shoots rays from a camera to draw a
sphere and a plane, adding shadows for realism.


### 1. Vectors: Moving and Pointing in 3D Space

As previously we use vectors. Vectors are like arrows that tell you a position or direction in
3D space. They have three numbers (x, y, z) to show where something is or which way it’s pointing.
You use vectors to represent the camera, light, sphere center, and the direction of rays.

Vectors let you calculate where rays go, how light hits objects, and where shadows fall. You add,
subtract, or scale vectors to move points or adjust directions.

The `Vector` class handles all vector operations:
- *Position Vectors*: You define the camera (`cameraPos`), light (`lightPos`),
  and sphere center (`sphereCenter`) as vectors:
  ```javascript
  const sphereCenter = new Vector(0, 0, 0);
  const lightPos = new Vector(2, 3, 4);
  const cameraPos = new Vector(0, 0, 3);
  ```
- *Operations*: You subtract vectors to find distances
  (e.g., `cameraPos.subtract(sphereCenter)`), add
  them to move points, or scale them to adjust length:
  ```javascript
  class Vector {
      subtract(v) {
          return new Vector(this.x - v.x, this.y - v.y, this.z - v.z);
      }
      add(v) {
          return new Vector(this.x + v.x, this.y + v.y, this.z + v.z);
      }
      scale(s) {
          return new Vector(this.x * s, this.y * s, this.z * s);
      }
  }
  ```
- *Dot Product*: You use the dot product to measure how aligned
  two directions are (e.g., for lighting):
  ```javascript
  dot(v) {
      return this.x * v.x + this.y * v.y + this.z * v.z;
  }
  ```
- *Normalisation*: You make vectors unit length (size 1)
  to focus on direction:
  ```javascript
  normalize() {
      const mag = Math.sqrt(this.dot(this));
      return mag > 0 ? new Vector(this.x / mag, this.y / mag, this.z / mag) : this;
  }
  ```

Think of vectors as tools to describe points (like the camera)
or directions (like rays). The code uses them everywhere to
position objects and calculate how they interact.


### 2. Ray-Sphere Intersection: Finding Where Rays Hit the Sphere

To draw the sphere, you shoot a ray (like a laser) from the camera through each pixel
and check if it hits the sphere. This uses a quadratic equation to find where the ray
touches the sphere’s surface.

If the ray hits the sphere, you know where to color the pixel. The math tells you the
exact point of contact, which you need for lighting and shadows.

A sphere is defined by its center and radius. A ray is a starting point (camera) and
a direction. You solve a quadratic equation to find if and where the ray hits:
- Ray: `P = O + t * D` (where `O` is the camera position, `D` is the ray direction, `t`
  is distance along the ray).
- Sphere: `(P - C) · (P - C) = r²` (where `C` is the sphere center, `r` is the radius).
- Combine them to get: `a * t² + b * t + c = 0`, where:
  - `a = D · D` (always 1 for a normalised ray).
  - `b = 2 * (O - C) · D`.
  - `c = (O - C) · (O - C) - r²`.
- Solve for `t` using the quadratic formula: `t = (-b ± √(b² - 4ac)) / (2a)`.
- If `b² - 4ac` (the discriminant) is positive, the ray hits the sphere.

You calculate this in the ray-sphere intersection part:
```javascript
const oc = cameraPos.subtract(sphereCenter);
const a = rayDir.dot(rayDir);
const b = 2 * oc.dot(rayDir);
const c = oc.dot(oc) - sphereRadius * sphereRadius;
const discriminant = b * b - 4 * a * c;
if (discriminant >= 0) {
    const sqrtDisc = Math.sqrt(discriminant);
    let t0 = (-b - sqrtDisc) / (2 * a);
    let t1 = (-b + sqrtDisc) / (2 * a);
    t = t0 > 0 ? t0 : t1 > 0 ? t1 : Infinity;
    if (t < Infinity) {
        const hitPoint = cameraPos.add(rayDir.scale(t));
        // .. lighting calculations ..
    }
}
```
- `oc` is the vector from camera to sphere center (`O - C`).
- `a`, `b`, `c` form the quadratic equation.
- You check the discriminant to see if there’s a hit, then 
  pick the closest positive `t` to find the hit point.

You use a quadratic equation to find where a ray hits the sphere,
like solving where a line touches a ball.
The code does this for every pixel to draw the sphere.


### 3. Ray-Plane Intersection: Drawing the Ground

The plane (the ground) is a flat surface at `y = -1.5`.
You check if a ray hits it by calculating how far the
ray travels to reach that height.

The plane gives you a ground for the sphere to sit on,
and you need to know where rays hit it to color it or
check for shadows.

A plane is defined by a point and a normal (a vector
pointing up, here `[0, 1, 0]`). For a ray `P = O + t * D`,
you find where it hits the plane `y = planeY`:
- Plane equation: `(P - Q) · N = 0`, where `Q` is a point on the
  plane (e.g., `[0, planeY, 0]`), `N` is the normal `[0, 1, 0]`.
- Substitute `P = O + t * D`: `(O + t * D - Q) · N = 0`.
- For `y = planeY`, this simplifies to: `t = (planeY - O.y) / D.y`.
- If `t > 0`, the ray hits the plane at `P = O + t * D`.

You compute the plane intersection here:
```javascript
const planeT = (planeY - cameraPos.y) / rayDir.y;
if (planeT > 0 && (discriminant < 0 || planeT < t)) {
    const planeHit = cameraPos.add(rayDir.scale(planeT));
    // .. shadow and lighting calculations ..
}
```
- `planeT` is the distance `t` where the ray hits `y = -1.5`.
- You check if `planeT > 0` (hit is in front of the camera) and
  if it’s closer than the sphere hit (`planeT < t`).

You calculate where a ray hits the ground by solving a simple equation
for the y-coordinate. The code uses this to draw the plane and check
if it’s closer than the sphere.


### 4. Lambertian Shading: Lighting the Sphere

Lambertian shading makes surfaces brighter when they face the light.
You calculate how much light hits the sphere by checking the angle
between the surface’s normal (a vector pointing outward) and the light direction.

This gives the sphere a realistic look, brighter where it faces the
light and darker elsewhere, mimicking how light works in real life.

The brightness (diffuse term) is based on the dot product of the
surface normal and light direction:
- Brightness = `max(0, N · L)`, where `N` is the normal, `L` is the light direction.
- The dot product measures how aligned two vectors are. If they point
  the same way, it’s 1 (bright); if perpendicular, it’s 0 (dark).
- You multiply this by the sphere’s color to get the final color.

You calculate this for the sphere:
```javascript
const hitPoint = cameraPos.add(rayDir.scale(t));
const normal = hitPoint.subtract(sphereCenter).normalize();
const lightDir = lightPos.subtract(hitPoint).normalize();
const diffuse = Math.max(0, normal.dot(lightDir));
color = [255 * diffuse, 100 * diffuse, 100 * diffuse];
```
- `normal` is the direction from the sphere’s center to the hit point, normalized.
- `lightDir` points from the hit point to the light.
- `diffuse` is the dot product, capped at 0 to avoid negative light.
- You scale a reddish color `[255, 100, 100]` by `diffuse` to shade the sphere.

You make the sphere look lit by checking how much its surface faces the light.
The code uses a dot product to figure this out and colors the sphere accordingly.


### 5. Shadow Rays: Adding Shadows on the Plane

To create shadows, you shoot a "shadow ray" from the plane to the light and
check if the sphere blocks it. If it does, the plane is darker.

Shadows make the scene look more real by showing where light is blocked,
like the sphere casting a shadow on the ground.

You use the same ray-sphere intersection math for the shadow ray:
- Shadow ray: Starts at the plane hit point, goes toward the light.
- Check if it hits the sphere before reaching the light using the
  quadratic equation (like ray-sphere intersection).
- If there’s a hit and it’s closer than the light, the point is in shadow.

You check for shadows on the plane:
```javascript
const shadowRayOrigin = planeHit;
const ocShadow = shadowRayOrigin.subtract(sphereCenter);
const bShadow = 2 * ocShadow.dot(lightDir);
const cShadow = ocShadow.dot(ocShadow) - sphereRadius * sphereRadius;
const discriminantShadow = bShadow * bShadow - 4 * cShadow;
if (discriminantShadow < 0 || lightDist < 0.01) {
    const planeDiffuse = Math.max(0, new Vector(0, 1, 0).dot(lightDir));
    color = [50 * planeDiffuse, 50 * planeDiffuse, 50 * planeDiffuse];
} else {
    color = [10, 10, 10];
}
```
- `shadowRayOrigin` is the plane hit point.
- You compute the quadratic equation for the shadow ray hitting the sphere.
- If `discriminantShadow < 0` (no hit) or `lightDist < 0.01` (hit is beyond light),
  the plane is lit with diffuse shading.
- Otherwise, it’s in shadow and gets a dark color `[10, 10, 10]`.

You check if the sphere blocks light to the plane by shooting a ray to the light.
The code uses the same math as before to see if the sphere is in the way.


### 6. Camera and Field of View: Setting Up the View

The camera defines where you’re looking from, and the field of view (FOV) controls
how wide your view is. You map each pixel to a 3D ray direction to simulate what the camera sees.

This lets you create a 3D scene from a 2D canvas, deciding what part of the world is visible.

You convert pixel coordinates (x, y) to 3D ray directions:
- Normalize pixels to a range of [-1, 1] for x and y, adjusted by the aspect ratio and FOV.
- For a pixel (x, y), the ray direction is `(nx, ny, -1)`, where:
  - `nx = (2 * x / width - 1) * scale * aspect`.
  - `ny = (1 - 2 * y / height) * scale`.
  - `scale = tan(FOV / 2)` controls the view angle.
- Normalize the direction to ensure consistent ray length.

You set up the camera and FOV here:
```javascript
const fov = 90;
const scale = Math.tan(fov * 0.5 * Math.PI / 180);
const aspect = width / height;
const nx = (2 * x / width - 1) * scale * aspect;
const ny = (1 - 2 * y / height) * scale;
const rayDir = new Vector(nx, ny, -1).normalize();
```
- `fov = 90` sets a wide view (90 degrees).
- `scale` converts the FOV to a scaling factor using the tangent function.
- `aspect` adjusts for the canvas’s width-to-height ratio.
- `nx` and `ny` map the pixel to a 3D direction, with `z = -1` pointing into the scene.

You turn 2D pixel coordinates into 3D rays to mimic a camera. The code uses FOV
and canvas size to decide where each ray points.


### Connecting It All

These math concepts work together to create your scene:
- *Vectors* let you position the camera, sphere, light, and plane, and define ray directions.
- *Ray-Sphere Intersection* finds where rays hit the sphere to draw it.
- *Ray-Plane Intersection* draws the ground plane.
- *Lambertian Shading* makes the sphere look lit realistically.
- *Shadow Rays* add shadows by checking if the sphere blocks light to the plane.
- *Camera and FOV* set up your view, turning pixels into rays.

Each piece of math builds part of the image, and the code ties them
together by calculating positions, intersections, and colors for every pixel.

### Project Idea: Explore the Math
To deepen your understanding, try tweaking these in the code:
- Change the FOV (`fov`) to see a wider or narrower view and observe how `scale` affects the scene.
- Move the light (`lightPos`) and see how shadows and shading change.
- Adjust the sphere’s radius (`sphereRadius`) and predict how the quadratic equation’s solutions shift.
- Add a small offset to `shadowRayOrigin` (e.g., `planeHit.add(lightDir.scale(0.01))`) to avoid self-shadowing glitches.

This renderer is a great way to see the algorithms and mathematics in action,
and playing with the code will help you grasp how each formula shapes the final image.

