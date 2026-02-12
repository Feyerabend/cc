
## 3D Technical Glossary

This glossary provides definitions for key technical terms used in 3D computer graphics, focusing on rendering
pipelines, geometric primitives, and GPU programming concepts.


### Vertex (Vertices)

*Explanation:* In 3D computer graphics, a vertex is a fundamental point in 3D Euclidean space, defined by its
coordinates (typically $x, y, z$). Beyond just position, a vertex can also store other attributes such as colour,
normal vector, tangent vector, texture coordinates ($u, v$), and sometimes bone weights. These attributes are
crucial for rendering and shading.

*Example:* Vertices are the atomic components of any 3D mesh. During the rendering pipeline, vertex data is
transformed (e.g., from model space to clip space) before being passed to the rasteriser. For example, a single
vertex could be defined as $V = (x, y, z, r, g, b, nx, ny, nz, u, v)$.

*Reference:* Real-time rendering pipelines, computer graphics fundamentals.



### Edge

*Explanation:* An edge is a line segment connecting two vertices in a 3D mesh. Edges form the boundaries of
polygons and define the connectivity between vertices, structuring the overall topology of a 3D object.

*Example:* Edges are fundamental to defining the shape and wireframe of a model. In mesh editing, operations
like 'extrude edge' or 'bevel edge' directly manipulate these elements to refine geometry. An edge $E$ can be
represented as an ordered pair of vertex indices $(v_1, v_2)$.

*Reference:* Polygonal mesh topology, computational geometry.



### Face (Polygon)

*Explanation:* A face (or polygon) is a planar region enclosed by a set of connected edges and vertices. In
most real-time 3D graphics, faces are typically triangles (tri-faces) or quadrilaterals (quad-faces), as
triangles are the most basic and robust geometric primitive for rasterization and rendering. Faces define
the visible surfaces of a 3D model.

*Example:* Faces are the renderable surfaces of a 3D model. During rasterization, each face is broken down
into pixels. For example, a cube has six faces, each typically represented by two triangles for a total of
twelve triangles.

*Reference:* Geometric primitives, mesh representation.



### Polygon

*Explanation:* In 3D computer graphics, a polygon is the fundamental building block of a 3D model. It is a
closed, two-dimensional shape formed by three or more vertices (points) connected by edges (lines). Polygons
are typically triangulated (divided into triangles) for rendering efficiency. While often used interchangeably
with "face," "polygon" can sometimes refer to the conceptual mathematical shape, whereas "face" is its
implementation in a mesh.

*Example:* Understanding polygons is essential because all 3D models are ultimately composed of them. For
instance, a simple cube is made of 6 square polygons, each of which can be represented as two triangles for
rendering.

*Reference:* General 3D modeling principles, geometric primitives.



### Mesh

*Explanation:* A mesh refers to the collection of vertices, edges, and faces (polygons) that define the shape
and surface of a 3D object. It's the wireframe structure upon which textures and materials are applied and is
the primary data structure for representing geometry in most 3D applications.

*Example:* A well-constructed mesh is essential for good deformation during animation and efficient rendering.
A low-polygon mesh might be used for real-time applications like games, while a high-polygon mesh is common
for film production.

*Reference:* 3D modeling terminology, data structures in computer graphics.



### Normal Vector

*Explanation:* A normal vector (or simply "normal") is a vector that is perpendicular (at a 90-degree angle) to
a surface at a given point. In 3D graphics, normals are crucial for determining how light reflects off a surface
and for calculating shading. Vertex normals define the orientation of a surface at each vertex, while interpolated
normals (used in Phong shading) provide a smoother representation across a polygon.

*Example:* Accurate normal vectors are fundamental for correct lighting. If a flat face has a normal pointing
directly up, a light source from above will illuminate it brightly. If the normal is incorrect, the lighting
will appear wrong, even on a perfectly flat surface.

*Reference:* Vector mathematics in computer graphics, lighting models.



### Texture Mapping

*Explanation:* Texture mapping is the process of applying a 2D image (a "texture") onto the surface of a 3D model.
This is achieved by mapping the 3D coordinates of the model's surface to 2D coordinates (UV coordinates) on the texture
image, allowing for the addition of colour, detail, and surface properties without increasing the geometric complexity
of the model.

*Example:* Texture mapping is essential for creating realistic and detailed 3D scenes efficiently. A simple flat
quad can represent a wooden floor, with a high-resolution wood grain texture mapped onto it to provide visual detail.

*Reference:* Basic texturing in computer graphics.



### UV Mapping

*Explanation:* UV mapping is the specific process of creating and arranging the 2D texture coordinates (often called UVs)
that connect a 3D model's surface to a 2D texture image. It involves unfolding the 3D mesh into a flat 2D layout, allowing
artists to paint or apply textures accurately without distortion. The "U" and "V" refer to the axes of this 2D texture
space, analogous to X and Y.

*Example:* UV mapping is used for adding realistic detail and colour to 3D models. Without proper UVs, a texture of a
brick wall applied to a house model would appear stretched or misaligned.

*Reference:* Texture mapping techniques in computer graphics, 3D modeling workflow.



### Normal Map

*Explanation:* A normal map is a type of texture map that stores surface normal information in its RGB channels. This
information allows a low-polygon model to simulate the appearance of a high-polygon model's surface details (like bumps,
cracks, or wrinkles) without actually increasing the polygon count. It achieves this by altering how light interacts
with the surface at the pixel level.

*Example:* Normal maps are widely used in video games and real-time rendering to achieve highly detailed visuals efficiently.
For instance, a simple flat wall in a game can look like it has intricate brickwork thanks to a normal map, saving
significant processing power.

*Reference:* Advanced texturing techniques, PBR (Physically Based Rendering).



### Shader

*Explanation:* A shader is a small program executed on the GPU that determines how graphics are rendered. There are
several types, but the most common are:
* *Vertex Shaders:* Process individual vertex data, performing transformations (e.g., model-view-projection)
  and passing attributes to the next stage.
* *Fragment (Pixel) Shaders:* Determine the final colour of each pixel (or fragment) on the screen, often
  performing lighting calculations, texture lookups, and applying material properties.
* *Geometry Shaders:* (Optional) Can generate or destroy primitives (points, lines, triangles) on the fly
  based on input primitives.
* *Tessellation Shaders:* (Hull and Domain Shaders) Used for dynamic mesh subdivision.
* *Compute Shaders:* General-purpose shaders for parallel computation on the GPU, not directly for rendering
  but used for tasks like physics or simulations.

*Example:* Shaders are the heart of modern real-time rendering, offering immense flexibility and programmability
for visual effects. A fragment shader is responsible for applying a metallic look to an object by calculating how
light reflects off its surface based on its material properties and incoming light.

*Reference:* GPU programming, OpenGL Shading Language (GLSL), High-Level Shading Language (HLSL).



### Shader Graph / Material Editor

*Explanation:* A shader graph (or node-based material editor) is a visual programming interface used to create complex
shaders and materials without writing code. Users connect nodes representing various operations (e.g., texture
sampling, mathematical functions, lighting models) with wires to define the flow of data and computations that
determine a material's appearance.

*Example:* Shader graphs make shader development more accessible to artists and designers, enabling rapid prototyping
and iterative design of realistic or stylized materials. An artist might combine a base colour texture, a normal map,
and a roughness map using a shader graph to define the look of a rusty metal surface.

*Reference:* Game engine material systems (e.g., Unreal Engine's Material Editor, Unity's Shader Graph, Blender's Node
Editor).



### Gouraud Shading

*Explanation:* Gouraud shading is an interpolation technique used to smooth the appearance of surfaces in 3D graphics
by interpolating colour values across the face of a polygon. It calculates the colour (or lighting) at each vertex of
a polygon, and then interpolates these colours linearly across the face during rasterization, resulting in a smoother
gradient compared to flat shading.

*Example:* Gouraud shading reduces the faceted look of low-polygon models without increasing the polygon count, making
it a common choice for performance-sensitive applications. If a vertex is red, another green, and a third blue, Gouraud
shading would create a smooth gradient from red to green to blue across the triangular face.

*Reference:* Classic shading models, computer graphics rendering algorithms.



### Phong Shading

*Explanation:* Phong shading is an illumination model that calculates lighting at each pixel (or fragment) of a surface,
rather than just at the vertices like Gouraud shading. It interpolates the surface normals across the polygon during
rasterisation and then calculates the lighting equation for each individual pixel using the interpolated normal, resulting
in a much smoother and more accurate representation of reflections and highlights.

*Example:* Phong shading provides a more realistic appearance, particularly for specular highlights, as it doesn't suffer
from the interpolation artifacts of Gouraud shading. A small, sharp specular highlight will appear accurately rounded on
a Phong-shaded surface, whereas it might appear faceted with Gouraud shading.

*Reference:* Illumination models, advanced shading techniques.



### Tessellation

*Explanation:* Tessellation is a technique that dynamically subdivides a coarse 3D mesh into a finer, higher-resolution
mesh during the rendering pipeline. This process creates more triangles on the GPU, allowing for greater geometric detail
to be added to surfaces without requiring the CPU to manage a high-polygon base mesh. It's often controlled by
tessellation factors, which determine the level of subdivision based on factors like distance from the camera.

*Example:* Tessellation is used for adaptive detail and cinematic quality in real-time rendering. For instance, a terrain
might appear flat from a distance but, as the camera approaches, tessellation can automatically add geometric detail like
bumps and valleys to the ground, giving it a more realistic appearance without prohibitive memory costs.

*Reference:* Modern GPU pipelines (e.g., DirectX 11+, OpenGL 4+), tessellation shaders.



### Rasterisation

*Explanation:* Rasterisation is the process of converting vector graphics (such as 3D models composed of vertices, edges,
and polygons) into a raster image (a grid of pixels) for display on a screen. It involves determining which pixels on the
screen are covered by each geometric primitive and then interpolating vertex attributes (like colour, texture coordinates,
or normals) across those pixels to determine their final colour.

*Example:* Rasterisation is the core rendering technique for almost all real-time 3D applications (e.g., video games).
When a triangle is processed by the rasteriser, it determines every pixel that falls within its boundaries and prepares
them for the fragment shader.

*Reference:* Real-time rendering pipeline, fixed-function pipeline vs. programmable pipeline.



### Fragment

*Explanation:* In the rasterisation stage of the rendering pipeline, a "fragment" is a potential pixel. It's the data
generated for each pixel that a primitive (like a triangle) covers. A fragment contains all the interpolated attributes
needed by the fragment shader, such as interpolated colour, texture coordinates, and interpolated normal vector, along
with its screen-space coordinates and depth value. Not all fragments become actual pixels (e.g., due to depth testing).

*Example:* The fragment shader operates on fragments. For instance, if a triangle covers 100 screen pixels, the rasteriser
will generate 100 fragments, and the fragment shader will execute for each one, determining its final colour.

*Reference:* Rasterization, fragment shader.



### Z-buffering (Depth Buffering)

*Explanation:* Z-buffering (or depth buffering) is a technique used during rasterization to determine which pixels are
visible when multiple objects overlap. It involves storing a depth value (the Z-coordinate) for each pixel in a special
buffer (the Z-buffer). When a new pixel is rendered, its depth is compared to the existing depth in the Z-buffer. If the
new pixel is closer to the camera, it overwrites the existing pixel colour and depth; otherwise, it is discarded.

*Example:* Z-buffering is critical for correctly rendering overlapping objects, preventing further objects from drawing
over closer ones. Without it, objects further away could be drawn on top of closer objects, leading to visual errors.

*Reference:* Visibility determination, real-time rendering techniques.



### Framebuffer

*Explanation:* A framebuffer is a digital memory buffer in a computer's RAM or VRAM that holds a complete frame of image
data ready for display on a screen. It typically consists of several logical buffers:
* *colour Buffer:* Stores the final RGBA colour values for each pixel.
* *Depth Buffer (Z-buffer):* Stores depth information for depth testing.
* *Stencil Buffer:* Stores additional per-pixel information for advanced effects (e.g., masking, shadows).
* *Accumulation Buffer:* (Less common now) Used for effects like motion blur or depth of field by accumulating multiple frames.

*Example:* The rendering pipeline renders to the framebuffer. Once all drawing commands for a frame are complete, the
contents of the colour buffer are sent to the display. When rendering a scene, objects are drawn into the colour buffer,
and their depth is written to the depth buffer to handle visibility.

*Reference:* Graphics hardware, rendering pipeline.



### Transform (Transformation Matrix)

*Explanation:* A transform in 3D graphics refers to the mathematical operations of translation (moving), rotation
(orienting), and scaling (resising) of objects, points, or vectors in 3D space. These operations are typically represented
by a 4x4 matrix (a transformation matrix). Chaining multiple transforms together (e.g., scale then rotate then translate)
is done by multiplying their respective matrices.

*Example:* Transforms are fundamental to positioning and orienting every object in a 3D scene. An object's
"model matrix" transforms it from its local object space into the global "world space," while the "view matrix"
transforms from world space to camera space, and the "projection matrix" transforms to clip space.

*Reference:* Linear algebra for computer graphics, 3D rendering pipeline.



### Model-View-Projection (MVP) Matrix

*Explanation:* The MVP matrix is a composite transformation matrix crucial for rendering 3D objects onto a 2D screen.
It is the product of three individual matrices:
1. *Model Matrix:* Transforms vertices from the object's local space to the world space.
2. *View Matrix:* Transforms vertices from world space to the camera's view space (or eye space).
3. *Projection Matrix:* Transforms vertices from view space to clip space (a normalized cube from -1 to 1
   on each axis), preparing them for rasterisation.
The combined MVP matrix allows vertices to be transformed from their initial definition to their final screen
position in a single multiplication.

*Example:* The MVP matrix is applied in the vertex shader for every vertex to position it correctly on the screen.
For example, if a vertex is at $(0,0,0)$ in its local model space, the MVP matrix determines where that point appears
on your screen based on the object's position, camera's position, and camera's perspective.

*Reference:* Graphics pipeline, vertex shading.



### Back-face Culling

*Explanation:* Back-face culling is an optimisation technique used in 3D rendering to avoid rendering polygons that
are facing away from the camera. In a closed 3D model, the faces pointing away from the viewer are generally hidden
by the front-facing faces. By determining the orientation of a face relative to the camera (e.g., using its normal
vector and the camera's direction), these "back faces" can be discarded early in the rendering pipeline, saving
processing time.

*Example:* This technique significantly improves rendering performance by reducing the number of polygons that need
to be processed by the later stages of the pipeline. For a simple cube, back-face culling means only 3 of its 6 faces
need to be drawn at any given time.

*Reference:* Rendering optimisations, graphics pipeline.



### Occlusion Culling

*Explanation:* Occlusion culling is a rendering optimization technique that prevents objects or parts of objects
from being rendered if they are completely hidden from the camera by other, closer objects (occluders). Unlike back-face
culling which deals with individual polygon orientation, occlusion culling considers entire objects or groups of
objects. It often involves pre-computation or real-time depth tests to identify occluded geometry.

*Example:* Occlusion culling is critical for performance in complex indoor scenes or highly detailed environments.
In a building, if you are looking at a wall, occlusion culling would prevent the rendering of rooms and objects behind
that wall, even if they are within the camera's frustum.

*Reference:* Rendering optimisations, game engine architecture.



### Render Queue

*Explanation:* The render queue (or rendering queue) is a mechanism within a graphics engine that manages the order
in which objects are drawn. Objects are typically sorted based on various criteria, such as material properties
(e.g., opaque vs. transparent), distance from the camera, or shader requirements. This ordering is crucial for correct
blending of transparent objects, optimizing state changes on the GPU, and achieving desired visual effects.

*Example:* Correct render queue management is essential for visual fidelity, especially with transparency. Opaque objects
are usually rendered first (to fill the depth buffer), followed by transparent objects sorted from back to front, so
their colours blend correctly with what's already been drawn.

*Reference:* Game engine rendering loop, rendering pipeline management.



### Draw Call

*Explanation:* A draw call is a command issued by the CPU to the GPU, instructing it to draw a batch of primitives
(e.g., triangles). Each draw call incurs some CPU overhead (e.g., setting up GPU state, submitting data). Optimising
the number of draw calls (batching primitives together) is a key strategy for improving real-time rendering performance,
as high draw call counts can bottleneck the CPU.

*Example:* Reducing draw calls is a major optimisation target in game development. Instead of issuing a separate draw
call for every small object, a game engine might combine all similar objects into a single mesh and issue one draw
call for them.

*Reference:* Performance optimisation, GPU architecture, rendering API (e.g., DirectX, OpenGL, Vulkan).



### PBR (Physically Based Rendering)

*Explanation:* PBR is a collection of rendering techniques and shading models designed to simulate the interaction of
light with materials in a physically plausible way. This approach aims for more realistic and consistent lighting
across various lighting conditions, based on real-world material properties such as albedo, metallicness, roughness,
and specular F0. PBR workflows often rely on energy conservation and microfacet theory.

*Example:* PBR has become the industry standard for realistic graphics in games and film due to its consistent results
and easier material authoring. A PBR material for gold will look like gold under any light, whereas older non-PBR
materials might require manual tweaking per lighting setup.

*Reference:* Modern rendering techniques, material science, computer graphics research.



### Ray Tracing

*Explanation:* Ray tracing is a rendering technique that simulates the path of light as individual "rays" from
the camera through the 3D scene. For each pixel on the screen, a ray is cast into the scene, and its interactions
with objects (reflections, refractions, shadows, etc.) are calculated to determine the final colour of that pixel.
This often results in highly realistic lighting and reflections but can be computationally expensive.

*Example:* Ray tracing produces highly realistic images, especially regarding reflections, refractions, and global
illumination, making it a cornerstone of photorealistic rendering in film and architectural visualisation. An example
would be rendering a scene with a reflective metallic sphere accurately showing reflections of its surroundings.

*Reference:* Computer graphics rendering algorithms, advanced rendering techniques.



### Global Illumination (GI)

*Explanation:* Global Illumination refers to algorithms that simulate how light interacts with a scene in a holistic
way, accounting for indirect lighting phenomena beyond direct illumination. This includes effects like diffuse
interreflection (light bouncing off surfaces and illuminating others), caustics (light focused by transparent objects),
and colour bleeding (light picking up the colour of a surface it reflects off). GI significantly enhances realism but
is computationally intensive.

*Example:* GI is crucial for photorealistic rendering, as it captures the subtle ways light fills a space. A room lit
only by a window would have parts of its walls indirectly illuminated by light bouncing off the floor and other walls,
an effect only captured by GI.

*Reference:* Advanced rendering algorithms, ray tracing, path tracing, radiosity.



### Ambient Occlusion (AO)

*Explanation:* Ambient Occlusion is a shading technique that approximates how exposed each point in a scene is to
ambient light. Areas that are more occluded (e.g., cracks, corners, crevices) receive less ambient light and appear
darker, adding subtle shadows and visual depth that enhances realism. It's an approximation of global illumination
and is much faster to compute.

*Example:* AO greatly improves the perceived realism of a scene by adding soft contact shadows and defining spatial
relationships between objects. A common application is Screen Space Ambient Occlusion (SSAO), which computes AO based
on depth and normal information available in the screen buffer.

*Reference:* Shading techniques, real-time rendering optimisations.



### LOD (Level of Detail)

*Explanation:* Level of Detail is a technique used to optimize rendering performance by providing different versions
of a 3D model (or other assets like textures) with varying levels of geometric complexity. Objects further from the
camera are rendered with lower-polygon LODs, while closer objects use higher-polygon LODs. This reduces the computational
load without significantly impacting visual quality.

*Example:* LOD systems are indispensable in large open-world games. A tree in the distance might be a simple billboard
or a very low-poly mesh, but as the player approaches, it smoothly transitions to a more detailed mesh with higher polygon
count.

*Reference:* Real-time rendering optimisations, game development.



### Rigging

*Explanation:* Rigging is the process of creating a hierarchical "skeleton" or "rig" for a 3D model, typically for
animation. This involves placing bones (joints) within the model and associating parts of the mesh with those bones,
allowing animators to pose and deform the model by manipulating the rig rather than individual vertices. Skinning is
the process of binding the mesh to the bones.

*Example:* Rigging is essential for animating characters and complex deformable objects. A character rig allows an
animator to move an arm by rotating a single "upper arm bone" rather than manually adjusting thousands of vertices.

*Reference:* 3D animation pipelines, character animation.



### Skinning

*Explanation:* Skinning is the process of associating the vertices of a 3D mesh with the bones of a rig. Each vertex
is assigned weight values that determine how much it is influenced by one or more bones. When a bone moves, the
vertices weighted to it deform the mesh, allowing for realistic character animation.

*Example:* Skinning enables organic deformation of character meshes. If a character's elbow bends, the vertices
around the elbow joint are influenced by both the upper arm bone and the forearm bone, causing the mesh to bend
smoothly.

*Reference:* Character animation, rigging.



### Keyframe

*Explanation:* In animation, a keyframe is a specific point in time where the properties of an object (e.g., position,
rotation, scale, colour) are explicitly defined. The animation software then interpolates or "tweens" the values
between these keyframes to create smooth motion.

*Example:* Keyframes are the backbone of most animation workflows. To animate a bouncing ball, an animator would
set keyframes for its position at the top of its arc and at the bottom of its bounce.

*Reference:* Principles of animation, animation software terminology.



### Render Farm

*Explanation:* A render farm is a cluster of networked computers (or cloud-based servers) dedicated to rendering
3D images and animations. Rendering complex 3D scenes can be highly computationally intensive, so distributing the
workload across multiple machines significantly speeds up the process.

*Example:* Render farms are crucial for large-scale production, enabling studios to meet tight deadlines for animated
films or visual effects. Without a render farm, rendering a feature-length animated movie would take an impossibly
long time on a single computer.

*Reference:* 3D production pipelines, cloud computing in graphics.



### Voxel

*Explanation:* A voxel (short for "volume pixel") is a unit of graphic information that defines a point in 3D space.
Analogous to a 2D pixel, a voxel represents a value on a regular grid in 3D space, often storing properties like colour,
density, or temperature. Voxel-based rendering represents objects as collections of these volumetric elements rather
than polygons.

*Example:* Voxels are used in medical imaging (e.g., CT scans, MRI), volume rendering, and increasingly in games for
destructible environments or infinite procedural worlds. A cloud, for instance, might be represented more naturally
as a collection of voxels rather than a polygon mesh.

*Reference:* Volumetric rendering, discrete geometry.



### Octree

*Explanation:* An octree is a tree data structure in which each internal node has exactly eight children. Octrees
are commonly used to subdivide a 3D space, often to organize spatial data (like voxels or objects) or for efficient
spatial queries such as collision detection or frustum culling. Each node represents a cubical region of space.

*Example:* Octrees efficiently manage large 3D scenes by quickly narrowing down the search space for objects. When
performing a raycast (e.g., for picking an object with the mouse), an octree can rapidly identify which objects a
ray intersects without checking every object in the scene.

*Reference:* Spatial data structures, computer graphics algorithms.



### Bounding Box (AABB)

*Explanation:* A bounding box is the smallest axis-aligned box (Axis-Aligned Bounding Box or AABB) that completely
encloses a 3D object or a group of objects. It's a simple geometric primitive used for quick and coarse collision
detection, frustum culling, and other spatial queries. Because it's axis-aligned, its calculation and intersection
tests are very fast.

*Example:* Bounding boxes are a fundamental optimization. Instead of performing expensive per-polygon collision tests
between two complex models, an engine first checks if their simple bounding boxes intersect. Only if they do, a more
precise (and costly) test is performed.

*Reference:* Collision detection, spatial partitioning, real-time rendering optimisations.



### Frustum Culling

*Explanation:* Frustum culling is a rendering optimisation technique that eliminates objects from the rendering
pipeline if they lie entirely outside the camera's viewing frustum. The viewing frustum is a pyramid-like shape
that defines the visible volume of the camera. Objects outside this volume cannot be seen by the camera and are
thus not rendered, saving significant processing time.

*Example:* Frustum culling is essential for optimising performance in any 3D scene. If a character is walking
through a level, only the parts of the level visible through the camera's "lens" (frustum) are drawn, ignoring
everything behind or to the sides.

*Reference:* Visibility determination, rendering pipeline optimisations.



### Deferred Shading

*Explanation:* Deferred shading (or deferred rendering) is a rendering technique that separates the geometry
pass from the lighting pass. In the first pass, geometric data (position, normal, albedo, etc.) is rendered
into multiple intermediate textures called a G-buffer. In the second pass, a single full-screen shader then
reads from this G-buffer to perform all lighting calculations, typically for many light sources.

*Example:* Deferred shading is highly efficient for scenes with many dynamic light sources, as lighting
calculations are performed once per pixel, rather than once per pixel per light per object. This avoids
redundant lighting calculations compared to forward rendering.

*Reference:* Modern rendering architectures, real-time rendering.



### Forward Shading

*Explanation:* Forward shading (or forward rendering) is a traditional rendering technique where each object is
rendered individually, and for each object, all lighting calculations are performed on its pixels as it is drawn.
This means that lighting for an object is computed based on all relevant light sources directly in the fragment shader.

*Example:* Forward shading is simpler to implement and handles transparency more naturally than deferred shading.
It is often preferred for scenes with fewer lights or when complex per-pixel transparency is required.

*Reference:* Rendering architectures, real-time rendering.



### Compute Shader

*Explanation:* A compute shader is a general-purpose shader program that runs on the GPU, designed for parallel
computation on arbitrary data, not just for rendering graphics. It operates on data within GPU memory (e.g., buffers,
textures) and can perform tasks like physics simulations, particle systems, image processing, or data manipulation
that are not directly tied to drawing triangles to the screen.

*Example:* Compute shaders enable powerful GPU acceleration for non-rendering tasks. For example, a game might use
a compute shader to simulate the fluid dynamics of water or the behavior of a massive flock of birds, leveraging
the GPU's parallel processing capabilities.

*Reference:* GPU programming, parallel computing, modern graphics APIs (e.g., OpenGL 4.3+, DirectX 11+).



### Signed Distance Field (SDF)

*Explanation:* A Signed Distance Field (SDF) is a mathematical function that, for any given point in space, returns
the shortest distance from that point to the surface of an object. The "signed" part means the distance is positive
if the point is outside the object and negative if it's inside. SDFs can represent complex shapes and are powerful
for rendering, collision detection, and procedural generation.

*Example:* SDFs are used for rendering techniques like ray marching (where rays step through the field) to render
smooth, complex shapes without traditional polygons. They are also excellent for booleans (combining/subtracting
shapes) and for creating smooth blends between objects.

*Reference:* Ray marching, procedural generation, computational geometry.



### Instancing

*Explanation:* Instancing is a rendering optimization technique used to draw multiple copies of the same 3D mesh
(or "instance") with a single draw call. Instead of submitting the geometry for each copy individually, the GPU
is given the mesh once, along with an array of per-instance data (e.g., position, rotation, scale, colour variations)
for each copy. This significantly reduces CPU overhead.

*Example:* Instancing is vital for rendering large numbers of identical or similar objects efficiently, such as a
forest of trees, a crowd of characters, or an army of identical units in a game. Instead of hundreds of draw calls
for hundreds of trees, there might be just one.

*Reference:* Rendering optimisations, GPU pipeline.



### Vertex Buffer Object (VBO)

*Explanation:* A Vertex Buffer Object (VBO) is a memory buffer on the GPU used to store vertex data (positions,
normals, texture coordinates, colours, etc.). Storing vertex data on the GPU and binding it for drawing reduces
the need to repeatedly transfer data from the CPU to the GPU, leading to significant performance improvements
in real-time rendering.

*Example:* VBOs are a fundamental part of modern OpenGL/DirectX rendering. When an application renders a character,
its entire mesh data (vertices) is typically stored in a VBO on the graphics card's memory, ready to be processed
by the vertex shader.

*Reference:* OpenGL, DirectX, GPU memory management.



### Index Buffer Object (IBO)

*Explanation:* An Index Buffer Object (IBO), also known as an Element Buffer Object (EBO) in OpenGL, is a memory buffer
on the GPU used to store the indices (references) of vertices that form primitives (e.g., triangles). Instead of
duplicating vertex data for shared vertices (e.g., a vertex shared by multiple triangles), an IBO allows the graphics
card to reuse existing vertex data by referencing it by its index, leading to more efficient memory usage and transfers.

*Example:* IBOs are crucial for efficient mesh rendering. Without an IBO, a cube would need 36 vertices (6 faces * 2
triangles/face * 3 vertices/triangle). With an IBO, it only needs 8 unique vertices, and the IBO defines how these 8
vertices are connected to form the 12 triangles.

*Reference:* OpenGL, DirectX, GPU memory management, mesh data structures.



### View Frustum

*Explanation:* The view frustum is the pyramid-shaped volume of space that is visible to the camera. It is defined
by the camera's position, direction, and its lens properties (field of view, aspect ratio, near clip plane, and far
clip plane). Only objects or parts of objects within this frustum will be rendered.

*Example:* Understanding the view frustum is fundamental to camera setup and rendering optimisations like frustum
culling. Objects entirely outside this volume are immediately discarded, saving rendering time.

*Reference:* Camera projection, 3D graphics fundamentals.



## Bump Map

*Explanation:* A bump map is a grayscale texture map used to simulate the appearance of surface irregularities
(bumps and dents) on a 3D model without actually altering the underlying geometry. It works by storing intensity
values that displace the surface normal virtually during shading. Brighter areas indicate "higher" points, and
darker areas indicate "lower" points. This virtual displacement affects how light interacts with the surface,
creating the illusion of detail. Unlike normal maps, bump maps only provide height information, which is then
converted into normal deviations.

*Example:* Bump maps are an older, but still relevant, technique for adding fine surface detail efficiently,
especially on objects viewed at a shallow angle. For instance, a bump map can make a flat brick wall texture
appear to have individual bricks protruding, catching light and casting subtle self-shadows, without adding
a single polygon to the wall mesh.

Reference: Texture mapping, classic shading techniques, computer graphics fundamentals.



### Affine Transformation

*Explanation:* An affine transformation is a type of geometric transformation that preserves collinearity (points
on a line remain on a line) and ratios of distances along a line. It includes translation, rotation, scaling,
reflection, and shear. In 3D graphics, these transformations are typically represented by $4 \times 4$ matrices,
where the last row is $(0, 0, 0, 1)$ for standard affine transformations.

*Example:* Affine transformations are the backbone of how objects are positioned, oriented, and scaled in a 3D scene.
Every object's model matrix, view matrix, and projection matrix are all types of affine (or projective, for
projection) transformations.

*Reference:* Linear algebra for computer graphics, geometric transformations.



### Homogeneous Coordinates

*Explanation:* Homogeneous coordinates are a system of coordinates used in computer graphics and projective geometry
to represent points and vectors. A 3D point $(x, y, z)$ is represented as a 4D vector $(x, y, z, w)$, where $w$ is
typically 1 for points and 0 for vectors. This allows all affine transformations (translation, rotation, scaling)
to be represented as matrix multiplications, simplifying the mathematical pipeline. Division by $w$ (perspective
division) occurs at the end of the projection stage.

*Example:* Homogeneous coordinates unify the mathematical representation of translations with rotations and scaling,
allowing all transformations to be combined into a single matrix multiplication. This is crucial for efficient GPU
processing. For instance, a point $(X, Y, Z)$ becomes $(X, Y, Z, 1)$ before matrix multiplication.

*Reference:* Projective geometry, linear algebra in computer graphics.



### Orthographic Projection

*Explanation:* Orthographic projection is a type of 3D projection where objects are projected onto the viewing plane
with parallel lines, meaning there is no perspective distortion. Objects of the same size appear the same size regardless
of their distance from the camera. It is commonly used for technical drawings, architectural blueprints, or isometric
views where accurate measurements and lack of distortion are desired.

*Example:* Orthographic projection is used when maintaining relative sizes and measurements is more important than
visual realism. For example, in a CAD software, an orthographic top-down view of a building ensures that all walls
of the same length appear equally long, regardless of their position in the scene.

*Reference:* Camera projection, computer graphics fundamentals.



### Perspective Projection

*Explanation:* Perspective projection is a type of 3D projection that simulates how the human eye perceives depth and
distance. Objects further from the camera appear smaller, and parallel lines appear to converge at a vanishing point.
This creates a sense of realism and depth in the rendered image. It's the most common projection type for games, films,
and general 3D visualisation.

*Example:* Perspective projection is used for creating realistic 3D scenes. When looking down a long road, the edges of
the road appear to converge in the distance due to perspective projection.

*Reference:* Camera projection, computer graphics fundamentals.



### Clipping

*Explanation:* Clipping is the process of discarding (or "clipping") parts of geometric primitives (points, lines,
triangles) that lie outside the camera's viewing frustum or other defined clipping planes. This ensures that only
the visible portions of the scene are sent to the rasteriser, saving significant processing time. It occurs after
vertex transformation but before rasterisation.

*Example:* Clipping is a necessary step in the rendering pipeline for efficiency and correctness. If a triangle
extends partially off-screen, clipping will cut it, creating new vertices at the intersection points with the
frustum boundaries, ensuring only the visible part is drawn.

*Reference:* Graphics pipeline, visibility determination.



### Vertex Array Object (VAO)

*Explanation:* A Vertex Array Object (VAO) is an OpenGL object that encapsulates all the state needed to describe
vertex data for rendering. This includes pointers to Vertex Buffer Objects (VBOs), the layout of attributes within
those VBOs (e.g., position, normal, UVs), and the binding to an Index Buffer Object (IBO). Binding a VAO restores
all this state at once, simplifying rendering code and improving performance.

*Example:* VAOs streamline the process of preparing vertex data for drawing. Instead of setting up buffer bindings
and attribute pointers for each draw call, an application can simply bind a VAO and then issue a draw call for a
specific mesh.

*Reference:* OpenGL programming, modern graphics APIs.



### State Machine (Graphics API)

*Explanation:* Many traditional graphics APIs (like older OpenGL) operate as state machines. This means that rendering
settings (such as current shader program, blend mode, depth test settings, active textures, etc.) are set globally.
Subsequent drawing commands then use these currently active "states" until they are changed. This contrasts with more
modern, object-oriented APIs (like Vulkan or DirectX 12) which are often "stateless" and require all necessary state
to be specified explicitly for each command.

*Example:* Understanding the state machine model is crucial when programming with APIs like OpenGL. If you enable
blending, all subsequent objects will be blended until blending is explicitly disabled.

*Reference:* Graphics API design, OpenGL programming.



### Blending (Alpha Blending)

*Explanation:* Blending, specifically alpha blending, is a technique used to combine the colors of a newly rendered
(source) pixel with an existing pixel in the framebuffer (destination pixel). It relies on the alpha channel
(transparency) of the source color. A common blend formula is: $C_{final} = C_{source} \times \alpha_{source} + C_{destination}
\times (1 - \alpha_{source})$, where $C$ represents color components and $\alpha$ is the alpha value. This creates
transparent or translucent effects.

*Example:* Blending is essential for rendering transparent objects like glass, water, or particle effects. To correctly
render a transparent window, the background scene is drawn first, and then the window is drawn on top, using blending
to allow the background to show through.

*Reference:* Rendering effects, rasterisation, alpha compositing.



### Stencil Buffer

*Explanation:* The stencil buffer is an additional per-pixel buffer in the framebuffer (alongside the color and depth
buffers) that stores integer values (typically 8 bits per pixel). It allows for masking and selective rendering. Pixels
can be conditionally rendered based on the value in the stencil buffer, enabling complex effects like reflections,
shadows, portals, or outlining.

*Example:* The stencil buffer is used for effects like planar reflections. First, a scene is drawn, marking the reflection
plane in the stencil buffer. Then, the scene is drawn again (possibly inverted and translated), but only where the
stencil buffer indicates the reflection plane, ensuring the reflection only appears on the mirror surface.

*Reference:* Advanced rendering effects, framebuffer operations.



### Frame Rate (FPS)

*Explanation:* Frame rate, commonly measured in Frames Per Second (FPS), is the frequency (rate) at which consecutive
images (frames) are displayed on a screen. A higher frame rate generally results in smoother animation and a more
responsive user experience, as more visual updates occur per second. Typical target frame rates are 30 FPS for consoles
and 60 FPS or higher for PCs.

*Example:* Frame rate is a key performance metric in real-time 3D applications like video games. A low frame rate
(e.g., consistently below 30 FPS) results in a "choppy" or "laggy" visual experience.

*Reference:* Real-time graphics performance, human perception.



### VSync (Vertical Synchronization)

*Explanation:* VSync (Vertical Synchronization) is a display option that synchronises the frame rate of the graphics
card with the refresh rate of the monitor. When VSync is enabled, the graphics card waits for the monitor's vertical
blanking interval before sending a new frame to the display. This prevents "screen tearing," where parts of multiple
frames are displayed simultaneously, but it can introduce input lag if the frame rate drops below the monitor's refresh
rate.

*Example:* VSync is used to ensure visual smoothness and prevent tearing. If a game renders at 100 FPS on a 60Hz monitor
without VSync, you would see tearing artifacts. With VSync, it caps the framerate at 60 FPS, ensuring each frame is
complete when displayed.

*Reference:* Display technology, real-time graphics performance.



### Render Pipeline

*Explanation:* The render pipeline (or graphics pipeline) is the sequence of stages that 3D data goes through from
its initial definition in an application to its final display as 2D pixels on a screen. It typically involves stages
like application stage (CPU), geometry stage (vertex processing, transformations, culling), and rasterisation stage
(fragment processing, shading, pixel output). Modern pipelines are highly programmable, especially on the GPU.

*Example:* Understanding the render pipeline is fundamental to graphics programming, as it dictates the order of
operations and where different computations occur. A vertex shader runs early in the pipeline to transform geometry,
while a fragment shader runs later to determine pixel colors.

*Reference:* Computer graphics architecture, GPU architecture.



### Texture Filtering (Bilinear, Trilinear, Anisotropic)

*Explanation:* Texture filtering refers to techniques used to determine the color of a pixel when its texture
coordinate does not perfectly align with a texel (texture pixel). This is necessary to prevent aliasing artifacts
(jagged edges, shimmering) when textures are scaled up or down.
* *Bilinear Filtering:* Interpolates between the four nearest texels.
* *Trilinear Filtering:* Adds interpolation between mipmap levels to reduce aliasing further, especially at distance.
* *Anisotropic Filtering:* The most advanced, it samples textures non-uniformly along the direction of the view,
significantly improving clarity for textures viewed at oblique angles.

*Example:* Texture filtering ensures textures look smooth and clear regardless of scale or viewing angle. Without
it, a texture seen from a distance would appear blocky or shimmer due to aliasing. Anisotropic filtering is especially
important for ground textures stretching into the distance.

*Reference:* Texture mapping, real-time rendering.



### Mipmap

*Explanation:* Mipmaps (derived from the Latin "multum in parvo" meaning "much in little") are pre-calculated,
optimised sequences of progressively smaller and lower-resolution images of a given texture. Each mipmap level
is typically half the size (width and height) of the previous level. During rendering, the graphics hardware
automatically selects the appropriate mipmap level based on the distance of the textured object from the camera,
reducing aliasing and improving performance.

*Example:* Mipmaps are crucial for reducing visual artifacts like shimmering and moiré patterns when textures are
viewed from a distance, and for optimising memory bandwidth by sampling smaller texture data. A brick wall texture
might have a 1024x1024 base texture, then a 512x512 mipmap, a 256x256, and so on, down to a tiny 1x1 pixel version.

*Reference:* Texture mapping, real-time rendering.

