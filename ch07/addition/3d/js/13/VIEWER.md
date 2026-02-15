
## Conceptual Minimal VRML Viewer

The renderer included might do some objects justice, but not others.
You will have to enhance this to your desire. Improve on the parser,
but also the renderer.

A minimal VRML viewer is essentially:
*A tolerant text parser + scene flattener + basic 3D renderer*

A VRML viewer can be decomposed into five logical stages:
```
VRML Text -> Lexer/Parser -> Scene Graph -> Renderable Data -> Renderer
```

*Responsibility:* Acquire VRML content.

Possible sources:
* Local `.wrl` file
* URL
* Embedded string

Tasks:
* Read text
* Validate header (`#VRML V1.0 ascii` or `#VRML V2.0 utf8`)
* Normalize line endings / whitespace

Minimal viewer assumption:s
* Only VRML97 (`V2.0`)
* Ignore encoding complexity



### Lexing & Parsing

#### Lexer

Transforms raw text into tokens:
* Identifiers (`Shape`, `Transform`)
* Numbers (`1.0`, `-2.3`)
* Brackets (`{ } [ ]`)
* Keywords (`DEF`, `USE`, `ROUTE`)

Minimal viewer simplification:
* Line-based parsing instead of full grammar
* Regex/token scanning is sufficient


#### Parser

Builds a *scene graph* representation.
VRML is hierarchical:

```vrml
Transform {
  children [
    Shape { ... }
  ]
}
```

Parser tasks:
* Track brace depth
* Recognize node types
* Extract fields
* Maintain current state

State typically includes:
* Active transform matrix
* Current material
* Coordinate arrays
* Named node dictionary (`DEF/USE`)

Minimal viewer simplifications:
* Support only core nodes:
  * `Transform`
  * `Shape`
  * `Appearance`
  * `Material`
  * Geometry primitives (`Box`, `Sphere`, etc.)
  * `Coordinate`
  * `IndexedFaceSet`
* Ignore scripting (`Script`)
* Ignore ROUTE/event model
* Ignore PROTO definitions


### Scene Graph Representation

Internal structure:
```
Node
 ├── TransformNode
 ├── GeometryNode
 ├── MaterialNode
 └── GroupNode
```

Each node stores:
* Local transform
* Children
* Geometry data (optional)
* Appearance data (optional)

Minimal viewer shortcut. Instead of storing a full graph:

-> *Flatten during parsing*

Output directly: List of Renderable Objects

Each object contains:
* Final transform
* Geometry buffers
* Material parameters

Why flatten?
* Easier renderer
* No runtime traversal
* Adequate for static scenes

Trade-off:
* Harder to support animation later


### Geometry Processing

#### IndexedFaceSet Handling

Convert:s
```
Coordinates + Indices -> Triangles
```

Steps:
1. Resolve coordinate indices
2. Triangulate polygons (fan triangulation)
3. Expand indexed geometry into flat arrays (optional)

Minimal viewer simplification:
* Always triangulate
* Ignore concave polygon correctness
* No topology validation


#### Normal Generation

If normals absent:
* Compute per-face normals
* Accumulate per-vertex
* Normalise

Minimal viewer simplification:s
* Flat shading acceptable
* Smooth shading optional


#### Transform Application

Two strategies:

*Option A: CPU transform*

* Apply transforms once
* Store world-space vertices

*Option B: GPU transform*

* Keep local vertices
* Send transform matrix to shader

Minimal viewer preference:
* CPU transform = simpler shaders
* GPU transform = more scalable


### Rendering Layer

#### Camera

Minimal camera model:
* Perspective projection
* Orbit rotation
* Zoom (distance)


#### Shader / Fixed Pipeline

Minimal lighting model:
* Ambient + Diffuse + Specular (Phong/Blinn)

Inputs:
* Position
* Normal
* Material parameters

Simplifications:
* Single directional light
* No shadows
* No textures initially


#### Draw Calls

Per renderable object:
```
Bind buffers -> Set uniforms -> Draw triangles
```

Optional modes:
* Wireframe
* Solid



### Remarks With a Minimal Viewer in Mind

#### Parsing Strategy Trade-offs

__Full Grammar vs Heuristic Parsing__

*Full VRML grammar:*
* Complex
* Accurate
* Supports PROTO/Script/events

*Heuristic line parser:*
* Fast to implement
* Fragile but workable
* Suitable for subset viewer

Minimal viewer typically chooses:
-> Heuristic parsing

Implication:
* Must tolerate malformed VRML
* Accept partial compatibility


#### Scene Graph vs Flattened Model

__Scene Graph Advantages__

* Natural VRML mapping
* Animation support
* Dynamic transforms

__Flattened Model Advantages__

* Simple renderer
* Lower runtime overhead
* Easier debugging

Minimal viewer commonly:
-> Flattens transforms + materials

Limitation:
* ROUTE / TimeSensor / Interpolator harder later


#### Indexed Geometry Pitfalls

VRML IndexedFaceSet allows:
* Arbitrary polygons
* Multiple index streams
* Optional normals/colors/texcoords

Minimal viewer simplification:
* Only `coordIndex`
* Ignore creaseAngle
* Ignore per-face vs per-vertex normals

Consequences:
* Some models shade incorrectly
* Hard edges lost


#### Transform Semantics Complexity

VRML transforms can stack:
```
Transform A
  Transform B
    Shape
```

Viewer must:
* Multiply matrices correctly
* Preserve parent state

Minimal viewer pitfalls:
* Incorrect matrix order
* Mutating shared state

Best practice:
* Clone state per node
* Immutable transform propagation


#### Material Interpretation Issues

VRML Material fields:
* diffuseColor
* ambientIntensity
* specularColor
* emissiveColor
* shininess
* transparency

Minimal viewer simplification:
* Map directly to shader uniforms
* Ignore emissive/transparency initially

Visual impact:
* Scenes look darker/brighter than intended
* Glass/transparency ignored


#### Performance Observations

Minimal viewer often:
* Expands indexed geometry -> duplicates vertices
* CPU-side transforms

Fine for:
* Small/medium VRML scenes

Problematic for:
* Large CAD/scan models

Optimisations later:
* Index buffers
* GPU transforms
* Vertex cache reuse


#### Feature Scope Decisions

Minimal viewer should explicitly decide:

*Supported*
* Static geometry
* Materials
* Basic transforms
* Primitive shapes

*Ignored*
* Script nodes
* Sensors
* ROUTE/event graph
* PROTO
* LOD, Billboard, Switch

Why? VRML is a *full interactive runtime*, not just geometry.
Supporting everything ≈ building a small engine.


#### Numerical / Data Robustness

Common VRML issues:
* Missing normals
* Degenerate faces
* Out-of-range indices
* Mixed winding order

Minimal viewer must:
* Validate indices
* Skip invalid faces
* Avoid NaNs propagating to GPU


#### Lighting Expectations Mismatch

VRML viewers historically implemented:
* Headlight
* Default lights

Minimal viewer choice:
-> Provide implicit light if none defined

Otherwise:
* Scene may render black



#### UX Implications

Minimal viewer interaction model:
* Orbit rotation
* Zoom
* Reset view

Nice additions:
* Bounding box framing
* Wireframe toggle
* Stats/debug panel



