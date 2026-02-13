
## Raytraced Bouncing Sphere with Texture

This explains the mathematics in simple terms. You'll see how each concept helps create the image
on the canvas and where it appears in the code. The renderer shoots rays from a camera to draw a
sphere and a plane, adding shadows for realism. It animates the sphere's position with a bounce,
includes specular highlights for a shiny effect, and maps a user-uploaded texture onto the sphere
instead of cycling colors.

This builds on the explanations in the READMEs for "sphere.html" (basic raytracing and shadows),
"animate-light.html" (advanced shading), and "bouncing-sphere.html" (position animation). Refer to
those for details on vectors, intersections, shading, shadows, camera/FOV, and bouncing. Here, we'll
focus on the new texture mapping while briefly recapping how it integrates with the existing math.
(Note: Color cycling is replaced by texture; the bounce remains.)


### 1. Vectors: Moving and Pointing in 3D Space

(See "sphere.html" README for full details.) Vectors position the camera, light, and sphere center.
The bouncing updates the center each frame, and texture mapping uses vectors for hit points to
compute coordinates.


### 2. Ray-Sphere Intersection: Finding Where Rays Hit the Sphere

(See "sphere.html" README for full details.) The quadratic equation finds ray hits. Bouncing updates
the center, and on hit, you now use the point to calculate texture coordinates instead of animated color.


### 3. Ray-Plane Intersection: Drawing the Ground

(See "sphere.html" README for full details.) Plane math is unchanged; shadows move with the bouncing sphere.


### 4. Shading: Lighting the Sphere with Diffuse, Ambient, and Specular

(See "animate-light.html" README for full details.) Shading combines diffuse, ambient, and specular.
Instead of HSL color, you sample from the texture and scale it by lighting factors.


### 5. Shadow Rays: Adding Shadows on the Plane

(See "sphere.html" README for full details.) Shadow checks use the updated bouncing position; no changes otherwise.


### 6. Camera and Field of View: Setting Up the View

(See "sphere.html" README for full details.) Pixel-to-ray mapping captures the bouncing and textured sphere.


### 7. Bouncing Animation: Making the Sphere Move Up and Down

(See "bouncing-sphere.html" README for full details.) Sine wave oscillates the sphere's height; integrates
with texture by updating the center for intersections and sampling.


### 8. Texture Mapping: Applying an Image to the Sphere

To texture the sphere, you load a user-uploaded image, calculate UV coordinates (a 2D mapping) at each
hit point, and sample the image's color there. This wraps the texture around the sphere like a map on a globe,
replacing uniform or animated colors with detailed patterns.

Textures add visual detail without more geometry, using math to "unwrap" the 3D surface to 2D image space.
Spherical mapping projects the texture as if from a cylinder or sphere, simple for balls but can distort at poles.

- *Loading Texture*: Upload an image, draw to a hidden canvas, get pixel data as an array.
- *UV Coordinates*: For a hit point, compute U (horizontal) and V (vertical) in [0,1]:
  - U from azimuthal angle: `0.5 + atan2(z, x) / (2π)`.
  - V from polar angle: `0.5 - asin(y / r) / π` (r is radius).
- *Sampling*: Map UV to image pixels (floor and modulo for wrapping), get RGB from data array.
- *Integration*: On sphere hit, sample texture color, then apply shading (multiply by diffuse + ambient, add specular).

You load and sample the texture here:
```javascript
// Texture handling
let textureImage = null;
let textureCtx = null;
const textureCanvas = document.createElement('canvas');

textureInput.addEventListener('change', (event) => {
    const file = event.target.files[0];
    if (file) {
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
    }
});

function getTextureColor(u, v) {
    if (!textureImage) return [255, 255, 255]; // Default white if no texture
    const x = Math.floor(u * textureImage.width) % textureImage.width;
    const y = Math.floor(v * textureImage.height) % textureImage.height;
    const index = (y * textureImage.width + x) * 4;
    return [
        textureImage.data[index],
        textureImage.data[index + 1],
        textureImage.data[index + 2]
    ];
}
```
And map UV on hit:
```javascript
const hitRelative = hitPoint.subtract(SPHERE_CENTER);
const u = 0.5 + Math.atan2(hitRelative.z, hitRelative.x) / (2 * Math.PI);
const v = 0.5 - Math.asin(hitRelative.y / SPHERE_RADIUS) / Math.PI;
const sphereColor = getTextureColor(u, v);
```
- `hitRelative` is hit point relative to center (like a direction vector).
- `atan2(z, x)` gives horizontal angle (longitude).
- `asin(y / r)` gives vertical angle (latitude), adjusted for V.
- Sampling uses floor for nearest pixel (simple, no filtering); modulo wraps texture.

You wrap an image on the sphere using spherical coordinates to get UV, then fetch colors.
The code loads the texture as data and samples it in shading, blending with lights.


### Connecting It All

These math concepts work together to create your textured, bouncing scene:
- *Vectors*, *intersections*, *shading*, *shadows*, *camera/FOV*, and *bouncing* form the base (see previous READMEs).
- *Texture mapping* adds detail by loading an image, computing UV at hits, and sampling colors for shading.
The renderer recalculates everything per frame, so bouncing moves the textured sphere and its shadow.

Each piece of math builds part of the image, and the code ties them
together by calculating positions, intersections, textures, colors, and lighting for every pixel in each frame.

### Project Idea: Explore the Math
To deepen your understanding, try tweaking these in the code:
- Change UV formulas (e.g., swap atan2 args) to rotate or flip the texture.
- Add simple bilinear filtering in `getTextureColor` for smoother sampling (average nearby pixels).
- Make texture repeat differently (e.g., remove modulo for clamping) or add distortion (e.g., noise in UV).
- Combine with color cycling: Tint the sampled color with HSL hue.
- Upload different images (e.g., Earth map) and adjust `BASE_Y` to match bounce with texture theme.

This renderer is a great way to see the algorithms and mathematics in action,
and playing with the code will help you grasp how each formula shapes the final image.
