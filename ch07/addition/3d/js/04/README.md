
## From Traditional Methods to Modern Shaders

These examples simulate a software rasteriser (CPU-based rendering) to illustrate
core concepts in computer graphics. We'll start with traditional "fixed-function"
rendering and progress to programmable shaders, highlighting their differences.

The goal is to provide a hands-on tutorial for understanding how 3D graphics work
under the hood. No external libraries are used--just plain JavaScript.
- A rotating 3D model (toggle animation with the button).
- Shading mode switches (e.g., color interpolation vs. lighting).
- Basic controls for interaction.


### Part 1: Introduction to 3D Rendering

3D rendering is the process of converting a 3D model (made of vertices, triangles,
and attributes like colors or textures) into a 2D image on your screen.
- *Transformation*: Positioning and rotating the model in 3D space.
- *Projection*: Converting 3D coordinates to 2D screen space (like a camera view).
- *Rasterization*: Filling in pixels within triangles.
- *Shading/Lighting*: Calculating colors for surfaces based on light, materials, etc.
- *Depth Testing*: Handling overlapping objects (using a depth buffer to determine visibility).

Rendering can be done on the CPU (software, as in these examples) or GPU
(hardware-accelerated, like in WebGL). These demos use CPU rendering for
educational purposes, making the process slower but easier to inspect.

Key pipeline stages (simplified):
1. Vertex processing (transform positions).
2. Primitive assembly (form triangles).
3. Rasterization (convert triangles to pixels).
4. Fragment processing (color each pixel).
5. Output (write to the screen).

Now, let's compare traditional vs. shader-based approaches.


### Part 2: Traditional (Fixed-Function) Rendering

In traditional rendering (common in early 3D graphics like old video games or
simple software renderers), the pipeline is "fixed"--you can't easily customise
each stage. Lighting and colors are calculated *once per triangle* (or per face),
leading to a faceted look. This is efficient for low-poly models but lacks smoothness.


#### Characteristics
- *Lighting Calculation*: Done per triangle using the face's normal vector
  (a direction perpendicular to the surface). For example, diffuse lighting
  computes how much light hits the flat face.
- *No Per-Pixel Granularity*: The entire triangle gets a uniform color.
  No smooth gradients unless you subdivide into more triangles.
- *Interpolation*: Limited--usually just depth for hidden surface removal (z-buffering).
- *Pros*: Simple, fast for basic scenes.
- *Cons*: Looks blocky; hard to add complex effects like per-pixel lighting or textures without hacks.
- *Backface Culling*: Skips drawing triangles facing away from the camera.
- *Sorting*: Often uses "painter's algorithm" (sort triangles by depth and
  draw back-to-front) or a depth buffer.

#### Example: `traditional.html`
- *What it does*: Renders a simple pyramid made of multiple triangles.
  Lighting is calculated once per face for flat shading.
- *Modes*:
  - Flat Shading: Lit colors per triangle.
  - Wireframe: Outlines only.
  - Solid Color: No lighting, just base colors.
- *How to Run*: Open in browser. Click "Toggle Animation" to rotate;
  "Change Mode" to switch rendering styles.
- *Code Highlights*:
  - Transformation using a rotation matrix.
  - Normal calculation for lighting: `normal.dot(lightDir)`.
  - Filling triangles with `ctx.fill()` for solid colors.
  - Painter's algorithm for depth sorting.

Try it: Notice the sharp edges between triangles--no smooth blending.


### Part 3: Shader-Based Rendering

Modern rendering (e.g., in GPUs via OpenGL/WebGL) uses *programmable shaders*--small
programs that run at specific pipeline stages. This allows fine-grained control:
- *Vertex Shader*: Runs once per vertex. Transforms positions, passes attributes
  (e.g., colors, normals, UVs) to the next stage.
- *Fragment Shader* (aka Pixel Shader): Runs once per pixel (fragment) inside a
  triangle. Computes the final color, often using interpolated data from vertices.
- *Interpolation*: Automatic--values like colors or normals are smoothly blended
  across the triangle using barycentric coordinates.

Shaders enable realistic effects like smooth lighting, textures, and animations at the pixel level.

#### Key Differences from Traditional Rendering
- *Granularity*: Traditional = per-triangle; Shaders = per-vertex + per-pixel.
- *Flexibility*: Shaders are programmable (you write code for each stage).
  Traditional is fixed.
- *Interpolation*: Shaders interpolate *everything* (colors, normals, textures)
  smoothly, creating gradients. Traditional might only interpolate depth.
- *Effects*: Shaders make per-pixel lighting, texture mapping, and custom effects easy.
  Traditional requires more triangles or approximations.
- *Performance*: On GPU, shaders are massively parallel (millions of pixels at once).
  Our CPU sim is slower but shows the logic.
- *Pipeline Stages*: More explicit separation--vertex shader feeds interpolated data to fragment shader.
- *Depth Handling*: Both use depth buffers, but shaders support advanced blending/transparency.

#### Example 1: Basic Triangle - `shader.html`
- *What it does*: Renders a single rotating triangle
  with interpolated colors or simple lighting.
- *Modes*:
  - Color Interpolation: Smooth rainbow gradient.
  - Lighting: Per-pixel diffuse lighting on a fixed purple color.
- *Code Highlights*:
  - Vertex Shader: Transforms positions, passes colors/normals.
  - Fragment Shader: Interpolates and computes final color.
  - Barycentric interpolation for smooth blending.
  - Depth buffer for pixel-level occlusion (though simple here).

Observe: Switch to lighting mode--the color varies smoothly
across the triangle, unlike traditional flat shading.

#### Example 2: Sphere - `sphere.html`
- *What it does*: A meshed sphere (many triangles) with color
  interpolation or per-pixel lighting.
- *Modes*: Same as above.
- *Why a Sphere?*: Shows how subdivision (more triangles) +
  interpolation creates smooth curves. Colors are based on vertex positions.
- *Code Highlights*: Procedural mesh generation (`createSphere` function)
  Normals interpolated for lighting.

Compare to traditional: A traditional sphere would look faceted unless heavily subdivided.

#### Example 3: Pyramid - `pyramid.html`
- *What it does*: A low-poly pyramid with per-face normals.
- *Modes*: Color interpolation or lighting.
- *Difference from Sphere*: Flat sides emphasize how shaders can
  still produce smooth gradients within faces, but the overall shape is angular.

#### Example 4: Texture Mapping - `texture.html`
- *What it does*: Sphere with a checkerboard texture applied via UV coordinates.
- *Modes*:
  - Texture: Plain checkerboard.
  - Texture with Lighting: Modulates texture by per-pixel light.
- *What is Texture Mapping?*: UVs (2D coords) map image pixels to 3D surfaces.
  Interpolated in shaders.
- *Code Highlights*: `sampleTexture` for bilinear sampling (simplified);
  UV interpolation.

This is hard in traditional rendering without per-pixel support.

#### Example 5: OBJ Model Loading - `obj-shader.html`
- *What it does*: Loads a user-uploaded `.obj` file (3D model)
  and renders it with textures/lighting.
- *Modes*: Texture or Texture with Lighting.
- *How to Use*: Click the file input to upload an `.obj`
  (e.g., a simple cube or teapot). It parses vertices, UVs, normals, and faces.
- *Code Highlights*:
  - Asynchronous OBJ parsing (handles large files with progress bar).
  - Falls back to checker texture if no MTL (material) is provided.
  - Backface culling via normal direction.

Tip: Download free `.obj` models from sites like Sketchfab (export as OBJ).
Note: This parser is basic--no materials or complex groups.

### Part 4: Key Concepts in Depth
- *Rendering Pipeline*:
  - Traditional: Combined steps (transform + light + fill).
  - Shaders: Separate programmable stages (vertex → rasterize/interpolate → fragment).
- *Interpolation & Barycentric Coordinates*: Weights pixels based on distance to vertices.
  Enables smoothness.
- *Normals*: For lighting. In shaders, interpolated per-pixel (Gouraud/Phong shading).
- *Depth Buffer (Z-Buffer)*: Array storing depth per pixel; prevents drawing over closer objects.
- *Matrices*: Used for rotations/projections. Our examples use a simple 4x4 matrix.
- *Limitations of These Demos*: CPU-based, so slow for complex models (e.g., high-poly OBJs).
  Real GPUs handle billions of operations/sec.
- *Extensions*: Add perspective projection, camera controls, or real textures (load images via `Image` object).

### Part 5: Running and Experimenting
* Modify the code:
   - Change light direction in fragment shaders.
   - Add more effects (e.g., specular highlights:
     `Math.pow(Math.max(0, view.dot(reflect)), shininess)`).
   - Increase mesh resolution in `createSphere`.
* Compare: Run `traditional.html` vs. `shader.html` side-by-side.

