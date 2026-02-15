
### 1. What VRML Is

VRML is a *text-based 3D scene description language*
designed for interactive graphics on the web.

* Geometry (shapes)
* Appearance (materials, textures)
* Lighting
* Animation
* Interaction
* Scene hierarchy

Files typically use the extension: `.wrl`
VRML scenes are declarative, similar in spirit to HTML but for *3D worlds*.

More VRML objects at: [https://www.martinreddy.net/ukvrsig/vrml.html](https://www.martinreddy.net/ukvrsig/vrml.html)


#### Early 1990s – Origins

VRML emerged during the early expansion of the web when people
envisioned *“3D cyberspace”*.

* *1994* – Concept introduced at the first WWW conference
* Inspired by *Open Inventor* (Silicon Graphics scene graph API)
* Goal: platform-independent 3D content via browsers


#### VRML 1.0 (1995)

Characteristics:
* Static 3D scenes
* Based heavily on Open Inventor
* No real animation or interactivity

Focus: *geometry + appearance*


#### VRML 2.0 -> VRML97 (1996–1997)

Major upgrade:
* Animation
* Sensors (interaction)
* Scripting
* Sound
* Event-driven behavior

Standardised as:
*ISO/IEC 14772-1:1997*

This became the definitive version: *VRML97*


### 3. Core Design Principles

VRML is built around a *scene graph*:

* Hierarchical structure
* Nodes represent objects/behaviors
* Transformations propagate downward

Everything is a *node*.


### 4. Basic File Structure

A VRML file begins with a header: `#VRML V2.0 utf8`
Then follows a list of nodes.


### 5. Essential Node Types

#### 5.1 Shape Node

Defines visible objects:
```vrml
Shape {
  appearance Appearance { ... }
  geometry Box { ... }
}
```


#### 5.2 Geometry Nodes

Examples:
```vrml
Box { size 2 2 2 }
Sphere { radius 1 }
Cylinder { radius 1 height 2 }
Cone { bottomRadius 1 height 2 }
```


#### 5.3 Appearance & Material

```vrml
Appearance {
  material Material {
    diffuseColor 0.8 0.2 0.2
    specularColor 1 1 1
    shininess 0.5
  }
}
```


#### 5.4 Transform Node

Applies translation, rotation, scale:
```vrml
Transform {
  translation 0 1 0
  rotation 0 1 0 1.57
  scale 1 2 1
  children [ ... ]
}
```


#### 5.5 Lighting

```vrml
DirectionalLight {
  direction 0 -1 0
  color 1 1 1
}
```

Other types:
* PointLight
* SpotLight


### 6. Simple Example Scene

```vrml
#VRML V2.0 utf8

DirectionalLight { direction 0 -1 0 }

Transform {
  translation 0 0 0
  children [
    Shape {
      appearance Appearance {
        material Material {
          diffuseColor 0 0.6 1
        }
      }
      geometry Box { size 2 2 2 }
    }
  ]
}
```

This describes:
* One light
* One blue box


### 7. Rendering Model

VRML does *not define a renderer*, only the scene description.
Typical pipeline:

```
VRML File -> Browser Plugin / Viewer -> Scene Graph -> Graphics API (OpenGL/Direct3D)
```

Key aspects:
* Viewer interprets nodes
* Builds internal scene graph
* Applies transforms
* Sends geometry to GPU

Rendering features depended on the viewer:
* Shading
* Texture mapping
* Transparency
* Level of detail


### 8. Animation & Interaction

VRML97 introduced *event-driven behaviour*.

#### Sensors

Example:

```vrml
TouchSensor { }
TimeSensor { cycleInterval 5 loop TRUE }
```


#### Interpolators

```vrml
PositionInterpolator {
  key [0, 1]
  keyValue [0 0 0, 0 5 0]
}
```


#### ROUTE Connections

```vrml
ROUTE TimeSensor.fraction_changed TO PositionInterpolator.set_fraction
ROUTE PositionInterpolator.value_changed TO Transform.set_translation
```

This forms a *dataflow graph*.


### 9. Strengths of VRML

* Human-readable text format
* Declarative
* Cross-platform vision
* Early interactive 3D standard
* Scene graph abstraction


### 10. Limitations

#### 10.1 Performance Constraints

* CPU-heavy interpretation
* Limited GPU integration (early era)
* Large file sizes
* Slow internet connections (1990s)


#### 10.2 Dependency on Plugins

Users needed:
* Cosmo Player
* Cortona
* Blaxxun Contact

Plugins created friction and security concerns.


#### 10.3 Limited Tooling

Compared to later engines:
* Weak authoring tools
* Difficult workflows
* Primitive shaders


### 11. Why VRML Declined

#### 11.1 Web Technology Shift

* Plugin model fell out of favor
* Browsers restricted NPAPI plugins
* Security and stability issues


#### 11.2 Rise of Alternatives

* *Flash (2D dominance)*
* *Game engines*
* *WebGL*
* *HTML5 + JavaScript*


#### 11.3 Graphics Evolution

Modern needs exceeded VRML’s design:
* Programmable shaders
* Physically based rendering
* Advanced physics
* Large scenes


### 12. Successor: X3D

VRML evolved into:
*X3D (Extensible 3D)*

Enhancements:
* XML encoding
* Better extensibility
* Multiple encodings (XML, ClassicVRML, JSON)

However, X3D never achieved mainstream web dominance.


### 13. Modern Equivalent Technologies

Today’s web 3D uses:
* *WebGL*
* *Three.js*
* *Babylon.js*
* *glTF* (file format)

glTF is often called: "The JPEG of 3D"

Because:
* Efficient
* GPU-friendly
* Compact


### 14. Legacy of VRML

VRML influenced:
* Scene graph architectures
* Declarative 3D formats
* X3D
* Early web-based 3D thinking
* Standards for interactive nodes/events

Concepts like:
* Nodes
* Hierarchies
* Interpolators
* ROUTE/event systems

remain foundational.

