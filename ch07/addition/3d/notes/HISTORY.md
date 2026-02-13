
## A Journey Through 3D Graphics: From Wireframes to Photorealism

Welcome to a brief exploration of 3D development. This field is a constant
dialogue between abstract mathematics, human perception, and the raw limits
of hardware. Over the last sixty years, it has transformed from simple lines
on a screen into the immersive, photorealistic worlds we see in modern
gaming and cinema.


### 1. The Mathematical Big Bang (1960s – 1970s)

In the beginning, 3D graphics were purely symbolic. Because hardware was
severely limited, researchers focused on mathematical abstractions rather
than visual beauty.

* *The Sketchpad Revolution*: In 1963, Ivan Sutherland’s Sketchpad
  introduced interactive modeling, allowing users to manipulate
  vertices and edges directly.
* *Wireframe Models*: Objects were represented as "skeletons" of vertices,
  edges, and faces, but only the outlines were rendered.
* *The Foundation*: This era established the essential math we still use today:
  Euclidean geometry, vector algebra, and transformation matrices.



### 2. Defining Solidity (1970s – 1980s)

As computers became more capable, the focus shifted from "outlines" to
"surfaces." The *polygon*--specifically the triangle--became the universal
building block of 3D objects.


#### Shading and Light

To make a flat polygon look like a curved surface, researchers developed
interpolation techniques:

* *Flat Shading*: One uniform color per face; looks very "blocky".
* *Gouraud Shading (1971)*: Interpolates color across a face based
  on its corners, smoothing out the appearance.
* *Phong Shading*: Interpolates the "normals" (the direction a surface
  faces) for much more accurate highlights and reflections.


#### The Visibility Problem

If two objects overlap, how does the computer know which one is in front?

* *Z-Buffering*: Invented by Edwin Catmull in 1974, this stores depth
  values for every pixel, ensuring objects are drawn in the correct order.
* **ack-face Culling*: An optimisation that tells the computer not to
  waste time drawing polygons that are facing away from the camera.



### 3. The Illusion of Detail (1980s – 1990s)

Adding more polygons to make an object look "real" is computationally
expensive. *Texture Mapping* changed the game by allowing 2D images
to be "wrapped" around 3D meshes.

* *UV Mapping*: Defined by Edwin Catmull, this allows for complex
  surface patterns without increasing geometric complexity.
* *Surface Illusions*: Techniques like *Bump Mapping* and
  *Normal Mapping* were developed to fake small details
  (like cracks or pores) by manipulating how light hits the surface.
* *Gaming Milestones*: Titles like *Doom* popularised pseudo-3D,
  while *Quake* introduced players to fully polygonal, interactive 3D worlds.



### 4. The Rise of the GPU (1990s – 2000s)

Originally, the "CPU" did all the math. The 1990s saw the birth of
the *Graphics Processing Unit (GPU)*--hardware dedicated entirely
to the "Rasterisation Pipeline".

* *Fixed-Function to Programmable*: Early GPUs had set ways of doing
  things. By the early 2000s, *Programmable Shaders* (Vertex and Fragment
  shaders) allowed developers to write custom code for lighting and materials.
* *Optimisation*: Techniques like *Level of Detail (LOD)* were refined,
  allowing the engine to swap high-detail models for low-detail ones
  when they are far away.



### 5. Modern Realism & AI (2010s – Present)

Today, we have moved away from "artistic hacks" and toward true physical simulation.


#### Physically Based Rendering (PBR)

Instead of picking colors, artists now define materials by physical properties
like *Roughness* and *Metallicness*, ensuring they react realistically to light
in any environment.


#### Ray Tracing

While traditional rendering (rasterisation) "guesses" where light goes,
*Ray Tracing* simulates the actual path of light rays.

* *NVIDIA RTX*: In 2018, hardware support made real-time ray-traced
  reflections, shadows, and global illumination possible.

#### The AI Era

Modern graphics now rely on "Intelligence" to save performance:

* *AI Upscaling (DLSS)*: Using AI to render at a low resolution and "guess"
  the missing pixels to reach 4K.
* *Denoising*: Cleaning up "grainy" ray-traced images using machine learning.



### Summary

| Era | Focus | Key Technology |
|-----|-------|----------------|
| *1960s* | Representation | Wireframes & Euclidean Math |
| *1970s* | Solidity | Polygons & Z-Buffering |
| *1980s* | Surfaces | Texture Mapping & Shading Models |
| *1990s* | Speed | Hardware Acceleration (GPUs) |
| *2000s* | Flexibility | Programmable Shaders |
| *2010s* | Physics | PBR & Real-time Ray Tracing |
| *2020s* | Intelligence | AI Denoising & Procedural Geometry |

