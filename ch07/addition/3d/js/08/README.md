
## Raytraced Sphere with Animated Color

This explains the mathematics in simple terms. You'll see how each concept helps create the image
on the canvas and where it appears in the code. The renderer shoots rays from a camera to draw a
sphere and a plane, adding shadows for realism. It also animates the sphere's color over time and
includes specular highlights for a shiny effect.


### 1. Vectors: Moving and Pointing in 3D Space

As previously we use vectors. Vectors are like arrows that tell you a position or direction in
3D space. They have three numbers (x, y, z) to show where something is or which way it’s pointing.
You use vectors to represent the camera, light, sphere center, and the direction of rays.

Vectors let you calculate where rays go, how light hits objects, and where shadows fall. You add,
subtract, or scale vectors to move points or adjust directions.

The `Vector` class handles all vector operations:
- *Position Vectors*: You define the camera (`CAMERA_POS`), light (`LIGHT_POS`),
  and sphere center (`SPHERE_CENTER`) as vectors:
  ```javascript
  const SPHERE_CENTER = { x: 0, y: 0, z: 0 };
  const LIGHT_POS = { x: 2, y: 3, z: 4 };
  const CAMERA_POS = { x: 0, y: 0, z: 3 };
  ```
- *Operations*: You subtract vectors to find distances
  (e.g., `new Vector(CAMERA_POS.x, CAMERA_POS.y, CAMERA_POS.z).subtract(SPHERE_CENTER)`), add
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
const oc = new Vector(CAMERA_POS.x, CAMERA_POS.y, CAMERA_POS.z).subtract(SPHERE_CENTER);
const a = rayDir.dot(rayDir);
const b = 2 * oc.dot(rayDir);
const c = oc.dot(oc) - SPHERE_RADIUS * SPHERE_RADIUS;
const discriminant = b * b - 4 * a * c;
if (discriminant >= 0) {
    const sqrtDisc = Math.sqrt(discriminant);
    const t0 = (-b - sqrtDisc) / (2 * a);
    const t1 = (-b + sqrtDisc) / (2 * a);
    t = t0 > EPSILON ? t0 : t1 > EPSILON ? t1 : Infinity;
    if (t < Infinity) {
        const hitPoint = new Vector(CAMERA_POS.x, CAMERA_POS.y, CAMERA_POS.z).add(rayDir.scale(t));
        // .. lighting calculations ..
    }
}
```
- `oc` is the vector from camera to sphere center (`O - C`).
- `a`, `b`, `c` form the quadratic equation.
- You check the discriminant to see if there’s a hit, then 
  pick the closest positive `t` to find the hit point (using `EPSILON` to avoid tiny errors).

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
const planeT = (PLANE_Y - CAMERA_POS.y) / rayDir.y;
if (planeT > EPSILON && (discriminant < 0 || planeT < t)) {
    const planeHit = new Vector(CAMERA_POS.x, CAMERA_POS.y, CAMERA_POS.z).add(rayDir.scale(planeT));
    // .. shadow and lighting calculations ..
}
```
- `planeT` is the distance `t` where the ray hits `y = -1.5`.
- You check if `planeT > EPSILON` (hit is in front of the camera) and
  if it’s closer than the sphere hit (`planeT < t`).

You calculate where a ray hits the ground by solving a simple equation
for the y-coordinate. The code uses this to draw the plane and check
if it’s closer than the sphere.


### 4. Shading: Lighting the Sphere with Diffuse, Ambient, and Specular

Shading makes surfaces brighter when they face the light and adds shiny highlights.
You calculate diffuse (basic lighting), ambient (soft fill light), and specular (glossy reflections)
using the surface normal, light direction, and view direction.

This gives the sphere a realistic look, with bright areas, soft shadows, and shiny spots,
mimicking how light bounces off surfaces in real life.

- *Diffuse*: Brightness = `max(0, N · L)`, where `N` is the normal, `L` is the light direction.
- *Ambient*: A constant light (e.g., 0.2) to fill dark areas.
- *Specular*: Shiny highlight = `(max(0, N · H))^power`, where `H` is the halfway vector
  between light and view directions, and `power` controls sharpness.
- Combine: Final intensity = diffuse + ambient + specular.

You calculate this for the sphere:
```javascript
const hitPoint = new Vector(CAMERA_POS.x, CAMERA_POS.y, CAMERA_POS.z).add(rayDir.scale(t));
const normal = hitPoint.subtract(SPHERE_CENTER).normalize();
const lightDir = new Vector(LIGHT_POS.x, LIGHT_POS.y, LIGHT_POS.z).subtract(hitPoint).normalize();
const viewDir = rayDir.scale(-1);
const halfDir = lightDir.add(viewDir).normalize();
const diffuse = Math.max(0, normal.dot(lightDir));
const specular = Math.pow(Math.max(0, normal.dot(halfDir)), SPECULAR_POWER);
color = [
    sphereColor[0] * (diffuse + AMBIENT_LIGHT) + 255 * specular,
    sphereColor[1] * (diffuse + AMBIENT_LIGHT) + 255 * specular,
    sphereColor[2] * (diffuse + AMBIENT_LIGHT) + 255 * specular
].map(c => Math.min(255, Math.max(0, c)));
```
- `normal` is the direction from the sphere’s center to the hit point, normalized.
- `lightDir` points from the hit point to the light.
- `viewDir` is the opposite of the ray direction (from hit to camera).
- `halfDir` is the halfway vector for specular.
- `diffuse` and `specular` are dot products, with specular raised to `SPECULAR_POWER = 20`.
- You scale the animated `sphereColor` by (diffuse + ambient) and add white specular.

You make the sphere look lit and shiny by combining diffuse, ambient, and specular terms.
The code uses dot products to compute these and blends them for the final color.


### 5. Shadow Rays: Adding Shadows on the Plane

To create shadows, you shoot a "shadow ray" from the plane to the light and
check if the sphere blocks it. If it does, the plane is darker.

Shadows make the scene look more real by showing where light is blocked,
like the sphere casting a shadow on the ground.

You use the same ray-sphere intersection math for the shadow ray:
- Shadow ray: Starts at the plane hit point (offset slightly to avoid errors), goes toward the light.
- Check if it hits the sphere before reaching the light using the
  quadratic equation (like ray-sphere intersection).
- If there’s a hit and it’s closer than the light, the point is in shadow.

You check for shadows on the plane:
```javascript
const toLight = new Vector(LIGHT_POS.x - planeHit.x, LIGHT_POS.y - planeHit.y, LIGHT_POS.z - planeHit.z);
const lightDist = Math.sqrt(toLight.dot(toLight));
const lightDir = toLight.normalize();

// Shadow ray
const shadowRayOrigin = planeHit.add(lightDir.scale(EPSILON));
const ocShadow = shadowRayOrigin.subtract(SPHERE_CENTER);
const bShadow = 2 * ocShadow.dot(lightDir);
const cShadow = ocShadow.dot(ocShadow) - SPHERE_RADIUS * SPHERE_RADIUS;
const discriminantShadow = bShadow * bShadow - 4 * cShadow;

if (discriminantShadow < 0 || lightDist < EPSILON) {
    const planeDiffuse = Math.max(0, new Vector(0, 1, 0).dot(lightDir));
    color = PLANE_COLOR.map(c => Math.min(255, c * (planeDiffuse + AMBIENT_LIGHT)));
} else {
    color = SHADOW_COLOR.map(c => Math.min(255, c * AMBIENT_LIGHT));
}
```
- `toLight` is the vector from plane hit to light, used for distance and direction.
- `shadowRayOrigin` is offset by `EPSILON` to avoid self-intersection.
- You compute the quadratic equation for the shadow ray hitting the sphere.
- If `discriminantShadow < 0` (no hit) or `lightDist < EPSILON` (hit is beyond light),
  the plane is lit with diffuse + ambient.
- Otherwise, it’s in shadow and gets ambient-only dark color.

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
const scale = Math.tan(FOV * 0.5 * Math.PI / 180);
const aspect = WIDTH / HEIGHT;
const rayX = (2 * x / WIDTH - 1) * scale * aspect;
const rayY = (1 - 2 * y / HEIGHT) * scale;
const rayDir = new Vector(rayX, rayY, -1).normalize();
```
- `FOV = 90` sets a wide view (90 degrees).
- `scale` converts the FOV to a scaling factor using the tangent function.
- `aspect` adjusts for the canvas’s width-to-height ratio.
- `rayX` and `rayY` map the pixel to a 3D direction, with `z = -1` pointing into the scene.

You turn 2D pixel coordinates into 3D rays to mimic a camera. The code uses FOV
and canvas size to decide where each ray points.


### 7. Color Animation: Cycling Colors with HSL to RGB

To animate the sphere’s color, you use HSL (Hue, Saturation, Lightness) values and convert
them to RGB (Red, Green, Blue) for the canvas. The hue changes over time to cycle through colors.

This adds motion to the scene, making the sphere change color smoothly like a rainbow effect.

HSL is a color model where:
- Hue (0-1) selects the color (red at 0, green at 1/3, blue at 2/3).
- Saturation (0-1) controls color intensity (0 is gray, 1 is vivid).
- Lightness (0-1) controls brightness (0 is black, 1 is white).
You convert HSL to RGB using a formula that calculates each channel based on hue segments.

You animate and convert color here:
```javascript
const hue = (time % COLOR_CYCLE_MS) / COLOR_CYCLE_MS;
const sphereColor = hslToRgb(hue, 0.8, 0.5);
```
And the conversion function:
```javascript
function hslToRgb(h, s, l) {
    let r, g, b;
    if (s === 0) {
        r = g = b = l;
    } else {
        const hue2rgb = (p, q, t) => {
            if (t < 0) t += 1;
            if (t > 1) t -= 1;
            if (t < 1/6) return p + (q - p) * 6 * t;
            if (t < 1/2) return q;
            if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
            return p;
        };
        const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
        const p = 2 * l - q;
        r = hue2rgb(p, q, h + 1/3);
        g = hue2rgb(p, q, h);
        b = hue2rgb(p, q, h - 1/3);
    }
    return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
}
```
- `hue` cycles from 0 to 1 over `COLOR_CYCLE_MS = 10000` milliseconds.
- `hslToRgb` uses the hue to compute RGB values, with fixed saturation (0.8) and lightness (0.5).
- You apply this color in shading: `sphereColor[0] * (diffuse + AMBIENT_LIGHT) + 255 * specular`.

You cycle the sphere’s color using HSL for smooth transitions, then convert to RGB.
The code updates hue based on time and uses it in every frame for animation.


### Connecting It All

These math concepts work together to create your animated scene:
- *Vectors* let you position the camera, sphere, light, and plane, and define ray directions.
- *Ray-Sphere Intersection* finds where rays hit the sphere to draw it.
- *Ray-Plane Intersection* draws the ground plane.
- *Shading* makes the sphere look lit realistically with diffuse, ambient, and specular components.
- *Shadow Rays* add shadows by checking if the sphere blocks light to the plane.
- *Camera and FOV* set up your view, turning pixels into rays.
- *Color Animation* cycles the sphere's color over time using HSL to RGB conversion.

Each piece of math builds part of the image, and the code ties them
together by calculating positions, intersections, colors, and lighting for every pixel in each frame.

### Project Idea: Explore the Math
To deepen your understanding, try tweaking these in the code:
- Change the FOV (`FOV`) to see a wider or narrower view and observe how `scale` affects the scene.
- Adjust the color cycle speed (`COLOR_CYCLE_MS`) or HSL values (e.g., saturation or lightness) to create different animations.
- Move the light (`LIGHT_POS`) and see how shadows, diffuse, and specular change.
- Increase `SPECULAR_POWER` for sharper highlights or add it to the plane for a shiny floor.
- Add a small offset to `shadowRayOrigin` (already using `EPSILON`) and experiment to avoid self-shadowing glitches.

This renderer is a great way to see the algorithms and mathematics in action,
and playing with the code will help you grasp how each formula shapes the final image.
## Raytraced Sphere with Animated Color

This explains the mathematics in simple terms. You'll see how each concept helps create the image
on the canvas and where it appears in the code. The renderer shoots rays from a camera to draw a
sphere and a plane, adding shadows for realism. It also animates the sphere's color over time and
includes specular highlights for a shiny effect.


### 1. Vectors: Moving and Pointing in 3D Space

As previously we use vectors. Vectors are like arrows that tell you a position or direction in
3D space. They have three numbers (x, y, z) to show where something is or which way it’s pointing.
You use vectors to represent the camera, light, sphere center, and the direction of rays.

Vectors let you calculate where rays go, how light hits objects, and where shadows fall. You add,
subtract, or scale vectors to move points or adjust directions.

The `Vector` class handles all vector operations:
- *Position Vectors*: You define the camera (`CAMERA_POS`), light (`LIGHT_POS`),
  and sphere center (`SPHERE_CENTER`) as vectors:
  ```javascript
  const SPHERE_CENTER = { x: 0, y: 0, z: 0 };
  const LIGHT_POS = { x: 2, y: 3, z: 4 };
  const CAMERA_POS = { x: 0, y: 0, z: 3 };
  ```
- *Operations*: You subtract vectors to find distances
  (e.g., `new Vector(CAMERA_POS.x, CAMERA_POS.y, CAMERA_POS.z).subtract(SPHERE_CENTER)`), add
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
const oc = new Vector(CAMERA_POS.x, CAMERA_POS.y, CAMERA_POS.z).subtract(SPHERE_CENTER);
const a = rayDir.dot(rayDir);
const b = 2 * oc.dot(rayDir);
const c = oc.dot(oc) - SPHERE_RADIUS * SPHERE_RADIUS;
const discriminant = b * b - 4 * a * c;
if (discriminant >= 0) {
    const sqrtDisc = Math.sqrt(discriminant);
    const t0 = (-b - sqrtDisc) / (2 * a);
    const t1 = (-b + sqrtDisc) / (2 * a);
    t = t0 > EPSILON ? t0 : t1 > EPSILON ? t1 : Infinity;
    if (t < Infinity) {
        const hitPoint = new Vector(CAMERA_POS.x, CAMERA_POS.y, CAMERA_POS.z).add(rayDir.scale(t));
        // .. lighting calculations ..
    }
}
```
- `oc` is the vector from camera to sphere center (`O - C`).
- `a`, `b`, `c` form the quadratic equation.
- You check the discriminant to see if there’s a hit, then 
  pick the closest positive `t` to find the hit point (using `EPSILON` to avoid tiny errors).

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
const planeT = (PLANE_Y - CAMERA_POS.y) / rayDir.y;
if (planeT > EPSILON && (discriminant < 0 || planeT < t)) {
    const planeHit = new Vector(CAMERA_POS.x, CAMERA_POS.y, CAMERA_POS.z).add(rayDir.scale(planeT));
    // .. shadow and lighting calculations ..
}
```
- `planeT` is the distance `t` where the ray hits `y = -1.5`.
- You check if `planeT > EPSILON` (hit is in front of the camera) and
  if it’s closer than the sphere hit (`planeT < t`).

You calculate where a ray hits the ground by solving a simple equation
for the y-coordinate. The code uses this to draw the plane and check
if it’s closer than the sphere.


### 4. Shading: Lighting the Sphere with Diffuse, Ambient, and Specular

Shading makes surfaces brighter when they face the light and adds shiny highlights.
You calculate diffuse (basic lighting), ambient (soft fill light), and specular (glossy reflections)
using the surface normal, light direction, and view direction.

This gives the sphere a realistic look, with bright areas, soft shadows, and shiny spots,
mimicking how light bounces off surfaces in real life.

- *Diffuse*: Brightness = `max(0, N · L)`, where `N` is the normal, `L` is the light direction.
- *Ambient*: A constant light (e.g., 0.2) to fill dark areas.
- *Specular*: Shiny highlight = `(max(0, N · H))^power`, where `H` is the halfway vector
  between light and view directions, and `power` controls sharpness.
- Combine: Final intensity = diffuse + ambient + specular.

You calculate this for the sphere:
```javascript
const hitPoint = new Vector(CAMERA_POS.x, CAMERA_POS.y, CAMERA_POS.z).add(rayDir.scale(t));
const normal = hitPoint.subtract(SPHERE_CENTER).normalize();
const lightDir = new Vector(LIGHT_POS.x, LIGHT_POS.y, LIGHT_POS.z).subtract(hitPoint).normalize();
const viewDir = rayDir.scale(-1);
const halfDir = lightDir.add(viewDir).normalize();
const diffuse = Math.max(0, normal.dot(lightDir));
const specular = Math.pow(Math.max(0, normal.dot(halfDir)), SPECULAR_POWER);
color = [
    sphereColor[0] * (diffuse + AMBIENT_LIGHT) + 255 * specular,
    sphereColor[1] * (diffuse + AMBIENT_LIGHT) + 255 * specular,
    sphereColor[2] * (diffuse + AMBIENT_LIGHT) + 255 * specular
].map(c => Math.min(255, Math.max(0, c)));
```
- `normal` is the direction from the sphere’s center to the hit point, normalized.
- `lightDir` points from the hit point to the light.
- `viewDir` is the opposite of the ray direction (from hit to camera).
- `halfDir` is the halfway vector for specular.
- `diffuse` and `specular` are dot products, with specular raised to `SPECULAR_POWER = 20`.
- You scale the animated `sphereColor` by (diffuse + ambient) and add white specular.

You make the sphere look lit and shiny by combining diffuse, ambient, and specular terms.
The code uses dot products to compute these and blends them for the final color.


### 5. Shadow Rays: Adding Shadows on the Plane

To create shadows, you shoot a "shadow ray" from the plane to the light and
check if the sphere blocks it. If it does, the plane is darker.

Shadows make the scene look more real by showing where light is blocked,
like the sphere casting a shadow on the ground.

You use the same ray-sphere intersection math for the shadow ray:
- Shadow ray: Starts at the plane hit point (offset slightly to avoid errors), goes toward the light.
- Check if it hits the sphere before reaching the light using the
  quadratic equation (like ray-sphere intersection).
- If there’s a hit and it’s closer than the light, the point is in shadow.

You check for shadows on the plane:
```javascript
const toLight = new Vector(LIGHT_POS.x - planeHit.x, LIGHT_POS.y - planeHit.y, LIGHT_POS.z - planeHit.z);
const lightDist = Math.sqrt(toLight.dot(toLight));
const lightDir = toLight.normalize();

// Shadow ray
const shadowRayOrigin = planeHit.add(lightDir.scale(EPSILON));
const ocShadow = shadowRayOrigin.subtract(SPHERE_CENTER);
const bShadow = 2 * ocShadow.dot(lightDir);
const cShadow = ocShadow.dot(ocShadow) - SPHERE_RADIUS * SPHERE_RADIUS;
const discriminantShadow = bShadow * bShadow - 4 * cShadow;

if (discriminantShadow < 0 || lightDist < EPSILON) {
    const planeDiffuse = Math.max(0, new Vector(0, 1, 0).dot(lightDir));
    color = PLANE_COLOR.map(c => Math.min(255, c * (planeDiffuse + AMBIENT_LIGHT)));
} else {
    color = SHADOW_COLOR.map(c => Math.min(255, c * AMBIENT_LIGHT));
}
```
- `toLight` is the vector from plane hit to light, used for distance and direction.
- `shadowRayOrigin` is offset by `EPSILON` to avoid self-intersection.
- You compute the quadratic equation for the shadow ray hitting the sphere.
- If `discriminantShadow < 0` (no hit) or `lightDist < EPSILON` (hit is beyond light),
  the plane is lit with diffuse + ambient.
- Otherwise, it’s in shadow and gets ambient-only dark color.

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
const scale = Math.tan(FOV * 0.5 * Math.PI / 180);
const aspect = WIDTH / HEIGHT;
const rayX = (2 * x / WIDTH - 1) * scale * aspect;
const rayY = (1 - 2 * y / HEIGHT) * scale;
const rayDir = new Vector(rayX, rayY, -1).normalize();
```
- `FOV = 90` sets a wide view (90 degrees).
- `scale` converts the FOV to a scaling factor using the tangent function.
- `aspect` adjusts for the canvas’s width-to-height ratio.
- `rayX` and `rayY` map the pixel to a 3D direction, with `z = -1` pointing into the scene.

You turn 2D pixel coordinates into 3D rays to mimic a camera. The code uses FOV
and canvas size to decide where each ray points.


### 7. Color Animation: Cycling Colors with HSL to RGB

To animate the sphere’s color, you use HSL (Hue, Saturation, Lightness) values and convert
them to RGB (Red, Green, Blue) for the canvas. The hue changes over time to cycle through colors.

This adds motion to the scene, making the sphere change color smoothly like a rainbow effect.

HSL is a color model where:
- Hue (0-1) selects the color (red at 0, green at 1/3, blue at 2/3).
- Saturation (0-1) controls color intensity (0 is gray, 1 is vivid).
- Lightness (0-1) controls brightness (0 is black, 1 is white).
You convert HSL to RGB using a formula that calculates each channel based on hue segments.

You animate and convert color here:
```javascript
const hue = (time % COLOR_CYCLE_MS) / COLOR_CYCLE_MS;
const sphereColor = hslToRgb(hue, 0.8, 0.5);
```
And the conversion function:
```javascript
function hslToRgb(h, s, l) {
    let r, g, b;
    if (s === 0) {
        r = g = b = l;
    } else {
        const hue2rgb = (p, q, t) => {
            if (t < 0) t += 1;
            if (t > 1) t -= 1;
            if (t < 1/6) return p + (q - p) * 6 * t;
            if (t < 1/2) return q;
            if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
            return p;
        };
        const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
        const p = 2 * l - q;
        r = hue2rgb(p, q, h + 1/3);
        g = hue2rgb(p, q, h);
        b = hue2rgb(p, q, h - 1/3);
    }
    return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
}
```
- `hue` cycles from 0 to 1 over `COLOR_CYCLE_MS = 10000` milliseconds.
- `hslToRgb` uses the hue to compute RGB values, with fixed saturation (0.8) and lightness (0.5).
- You apply this color in shading: `sphereColor[0] * (diffuse + AMBIENT_LIGHT) + 255 * specular`.

You cycle the sphere’s color using HSL for smooth transitions, then convert to RGB.
The code updates hue based on time and uses it in every frame for animation.


### Connecting It All

These math concepts work together to create your animated scene:
- *Vectors* let you position the camera, sphere, light, and plane, and define ray directions.
- *Ray-Sphere Intersection* finds where rays hit the sphere to draw it.
- *Ray-Plane Intersection* draws the ground plane.
- *Shading* makes the sphere look lit realistically with diffuse, ambient, and specular components.
- *Shadow Rays* add shadows by checking if the sphere blocks light to the plane.
- *Camera and FOV* set up your view, turning pixels into rays.
- *Color Animation* cycles the sphere's color over time using HSL to RGB conversion.

Each piece of math builds part of the image, and the code ties them
together by calculating positions, intersections, colors, and lighting for every pixel in each frame.

### Project Idea: Explore the Math
To deepen your understanding, try tweaking these in the code:
- Change the FOV (`FOV`) to see a wider or narrower view and observe how `scale` affects the scene.
- Adjust the color cycle speed (`COLOR_CYCLE_MS`) or HSL values (e.g., saturation or lightness) to create different animations.
- Move the light (`LIGHT_POS`) and see how shadows, diffuse, and specular change.
- Increase `SPECULAR_POWER` for sharper highlights or add it to the plane for a shiny floor.
- Add a small offset to `shadowRayOrigin` (already using `EPSILON`) and experiment to avoid self-shadowing glitches.

This renderer is a great way to see the algorithms and mathematics in action,
and playing with the code will help you grasp how each formula shapes the final image.

