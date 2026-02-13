
## Raytraced Bouncing Sphere with Animated Color

This explains the mathematics in simple terms. You'll see how each concept helps create the image
on the canvas and where it appears in the code. The renderer shoots rays from a camera to draw a
sphere and a plane, adding shadows for realism. It also animates the sphere's color over time,
includes specular highlights for a shiny effect, and makes the sphere bounce up and down on the plane.

This builds on the explanations in the READMEs for "sphere.html" (basic raytracing and shadows) and
"animate-light.html" (color animation and advanced shading). Refer to those for details on vectors,
intersections, shading, shadows, camera/FOV, and color cycling. Here, we'll focus on the new bouncing
animation while briefly recapping how it integrates with the existing math.


### 1. Vectors: Moving and Pointing in 3D Space

(See "sphere.html" README for full details.) Vectors position the camera, light, and sphere center.
In this version, the sphere's center Y-coordinate changes over time for bouncing, but vectors still
handle all calculations like hit points and directions.

The `Vector` class remains the same, used for operations like subtracting to find distances or
normalizing for lighting.


### 2. Ray-Sphere Intersection: Finding Where Rays Hit the Sphere

(See "sphere.html" README for full details.) The quadratic equation finds ray hits on the sphere.
Here, since the sphere moves (bouncing), you update its center each frame before intersection checks.

The code recalculates the sphere center dynamically:
```javascript
const bounceY = BASE_Y + Math.abs(Math.sin(bouncePhase * Math.PI * 2)) * BOUNCE_HEIGHT;
const SPHERE_CENTER = { x: 0, y: bounceY, z: 0 };
```
Then proceeds with the standard intersection math using the updated center.


### 3. Ray-Plane Intersection: Drawing the Ground

(See "sphere.html" README for full details.) The plane intersection uses a simple equation for
the fixed ground at `y = PLANE_Y`. The bouncing sphere casts a moving shadow on it, but the plane
math stays the same.


### 4. Shading: Lighting the Sphere with Diffuse, Ambient, and Specular

(See "animate-light.html" README for full details.) Diffuse, ambient, and specular terms light the
sphere. The animated color from HSL-to-RGB is scaled by these factors. Bouncing doesn't change the
shading math, but the moving position affects hit points and thus lighting angles.


### 5. Shadow Rays: Adding Shadows on the Plane

(See "sphere.html" README for full details.) Shadow rays check if the sphere blocks light to the plane.
With bouncing, the shadow moves as the sphere's position changes, creating dynamic shadows. The math
remains the quadratic check, but uses the updated sphere center each frame.


### 6. Camera and Field of View: Setting Up the View

(See "sphere.html" README for full details.) Pixel-to-ray mapping with FOV creates the view. The
bouncing happens in world space, so rays capture the motion without changes to camera math.


### 7. Color Animation: Cycling Colors with HSL to RGB

(See "animate-light.html" README for full details.) HSL hue cycles over time for color changes.
This combines with bouncing for a lively effect, applied in shading after intersection.


### 8. Bouncing Animation: Making the Sphere Move Up and Down

To animate the sphere bouncing, you oscillate its Y-position using a sine wave. This creates smooth,
periodic up-and-down motion, like a ball bouncing on the ground. The sine function provides natural
easing (slow at peaks, fast at bottom).

This adds vertical movement to the scene, making the sphere appear to bounce while updating shadows
and lighting in real-time. It's a simple harmonic motion approximation, ignoring physics like gravity
or damping for simplicity.

The position follows a sine wave: `y = base + amplitude * |sin(phase)|`.
- *Phase*: A value from 0 to 1 that cycles over time, scaled to radians for sine.
- *Sine Wave*: `sin(θ)` oscillates between -1 and 1. You take the absolute value for a "bounce"
  (positive hump) and multiply by height for amplitude.
- *Cycle*: Phase wraps every `BOUNCE_CYCLE_MS` milliseconds, creating repeated bounces.
- *Base and Height*: `BASE_Y` sets the lowest point (where the sphere touches the plane, adjusted
  for radius), and `BOUNCE_HEIGHT` sets how high it goes.

You calculate the bounce in `traceRay` (per frame):
```javascript
const bouncePhase = (time % BOUNCE_CYCLE_MS) / BOUNCE_CYCLE_MS;
const bounceY = BASE_Y + Math.abs(Math.sin(bouncePhase * Math.PI * 2)) * BOUNCE_HEIGHT;
const SPHERE_CENTER = { x: 0, y: bounceY, z: 0 };
```
- `bouncePhase` is time modulo cycle duration, normalized to [0, 1].
- `Math.PI * 2` converts phase to a full cycle in radians (one sine period).
- `Math.abs` flips the negative part of sine to create a bouncing "up-only" motion.
- `BASE_Y = -0.5` ensures the sphere's bottom touches `PLANE_Y = -1.5` at rest (since radius is 1).
- `BOUNCE_HEIGHT = 1.0` sets max lift.

The rest of the raytracing (intersections, shading) uses this updated `SPHERE_CENTER`, so the bounce
affects hits, lights, and shadows automatically.

You create bouncing with a sine wave to oscillate the sphere's height. The code updates the center
each frame, letting the existing math handle the visual changes.


### Connecting It All

These math concepts work together to create your animated scene:
- *Vectors*, *intersections*, *shading*, *shadows*, *camera/FOV*, and *color animation* form the base (see previous READMEs).
- *Bouncing animation* adds motion by updating the sphere's position with a sine wave each frame.
The renderer recalculates everything per frame, so bouncing naturally moves the sphere, shifts shadows,
and keeps color cycling.

Each piece of math builds part of the image, and the code ties them
together by calculating positions, intersections, colors, and lighting for every pixel in each frame.

### Project Idea: Explore the Math
To deepen your understanding, try tweaking these in the code:
- Change the bounce speed (`BOUNCE_CYCLE_MS`) or height (`BOUNCE_HEIGHT`) to see faster/slower or higher bounces.
- Replace `Math.abs(Math.sin(...))` with just `Math.sin(...) + 1` for a different oscillation (e.g., floating instead of bouncing).
- Add X/Z movement (e.g., `x: Math.sin(bouncePhase * Math.PI * 2) * 0.5`) for circling while bouncing.
- Sync bounce with color cycle by sharing phases or linking hue to height.
- Experiment with `EPSILON` in shadows to fix any artifacts from the moving sphere.

This renderer is a great way to see the algorithms and mathematics in action,
and playing with the code will help you grasp how each formula shapes the final image.
