
## 3D Textured Cube Renderer

A software-based 3D renderer written in C that renders a rotating
textured cube with proper perspective-correct texture mapping and lighting.

This renderer demonstrates fundamental 3D graphics concepts including:
- 3D transformations (translation, rotation)
- Perspective projection
- Perspective-correct texture mapping
- Backface culling
- Phong lighting model (ambient + diffuse)
- Rasterization with barycentric coordinates

- *main.c* - Entry point, sets up camera, creates cube model, runs animation loop
- *model.c/h* - Model data structures, cube geometry creation, texture loading (PAM format)
- *rendering.c/h* - Core rendering pipeline, texture mapping, triangle rasterization
- *rmath.c/h* - Math library (vectors, matrices, transformations)
- *texture.pam* - Input texture file (512x512 RGB image in PAM format)


### How Texture Mapping Works

#### 1. UV Coordinates Per Face

Each triangle in the cube has *pre-defined texture coordinates* (UVs) 
that are stored in the model at creation time:

```c
// Example: Front face, first triangle
model->tex_coords[6] = (TexCoord){0, 1};  // bottom-left vertex
model->tex_coords[7] = (TexCoord){1, 0};  // top-right vertex
model->tex_coords[8] = (TexCoord){1, 1};  // bottom-right vertex
```

- Each face gets its own UV mapping from (0,0) to (1,1)
- The cube has 12 triangles (2 per face × 6 faces) = 36 texture coordinates total
- These UVs are *fixed to the geometry* and never recalculated


#### 2. Perspective-Correct Interpolation

The key to avoiding texture warping is *perspective-correct interpolation*.
When rasterising a triangle, we cannot simply interpolate texture coordinates
linearly in screen space.

__Why Linear Interpolation Fails__

```
Wrong (causes warping):
u = w1*u1 + w2*u2 + w3*u3
v = w1*v1 + w2*v2 + w3*v3
```

Linear interpolation in screen space causes the famous "texture swimming" or
"convex/concave illusion" because it doesn't account for perspective foreshortening.

__Correct Approach__

```c
// Step 1: Precompute 1/z for each vertex
float inv_z1 = 1.0f / z1;
float inv_z2 = 1.0f / z2;
float inv_z3 = 1.0f / z3;

// Step 2: Precompute u/z and v/z
float u1_over_z = u1 * inv_z1;
float v1_over_z = v1 * inv_z1;
// ... same for u2, v2, u3, v3

// Step 3: Interpolate using barycentric weights
float inv_z = w1*inv_z1 + w2*inv_z2 + w3*inv_z3;
float u_over_z = w1*u1_over_z + w2*u2_over_z + w3*u3_over_z;
float v_over_z = w1*v1_over_z + w2*v2_over_z + w3*v3_over_z;

// Step 4: Recover perspective-correct u and v
float z = 1.0f / inv_z;
float u = u_over_z * z;
float v = v_over_z * z;
```

*Critical Detail*: The `z` values used must be *view-space depth* 
(distance from camera), NOT post-projection z values.


#### 3. View-Space Depth

The renderer computes two sets of vertex positions:

```c
Mat4 model_view = mat4_multiply(view, model_matrix);
Mat4 mvp = mat4_multiply(projection, model_view);

// View-space position (for depth)
view_space_vertices[i] = mat4_transform_vec3(model_view, model->vertices[i]);

// Projected position (for screen coordinates)
projected_vertices[i] = mat4_transform_vec3(mvp, model->vertices[i]);
```

For perspective correction, we use:
```c
z = -view_space_vertices[i].z;  // Negative because camera looks down -Z
```


#### 4. Barycentric Coordinate Interpolation

For each pixel inside a triangle:

```c
// Calculate barycentric weights (w1, w2, w3)
// These tell us how much each vertex contributes to this pixel

float area = (v2.x - v1.x) * (v3.y - v1.y) - (v3.x - v1.x) * (v2.y - v1.y);
float inv_area = 1.0f / area;

float w1 = ((v2.x - px) * (v3.y - py) - (v3.x - px) * (v2.y - py)) * inv_area;
float w2 = ((v3.x - px) * (v1.y - py) - (v1.x - px) * (v3.y - py)) * inv_area;
float w3 = 1.0f - w1 - w2;
```

If all weights are >= 0, the pixel is inside the triangle.


#### 5. Texture Sampling

Once we have perspective-correct UV coordinates:

```c
Vec3 sample_texture(Model* model, float u, float v) {
    // Wrap coordinates (for tiling textures)
    u = u - floorf(u);
    v = v - floorf(v);
    
    // Map to pixel coordinates
    int x = (int)(u * (model->tex_width - 1));
    int y = (int)(v * (model->tex_height - 1));
    
    // Lookup RGB value
    int index = (y * model->tex_width + x) * 3;
    return (Vec3){
        model->texture[index] / 255.0f,
        model->texture[index + 1] / 255.0f,
        model->texture[index + 2] / 255.0f
    };
}
```


#### 6. Lighting

The final pixel color combines the texture color with lighting:

```c
Vec3 calculate_lighting(Vec3 surface_normal, Vec3 base_color, Light* light) {
    // Ambient component (base illumination)
    Vec3 ambient = base_color * light->ambient_color * light->ambient_intensity;
    
    // Diffuse component (directional lighting)
    float diffuse_factor = max(0, dot(normal, light_direction));
    Vec3 diffuse = base_color * light->color * light->intensity * diffuse_factor;
    
    // Combine
    return clamp(ambient + diffuse, 0.0, 1.0);
}
```


### Compilation

```bash
gcc -o renderer main.c model.c rendering.c rmath.c -lm -O2
```

## Usage

```bash
./renderer
```

Generates 60 animation frames: `frame_000.pam` through `frame_059.pam`

Convert to PNG:
```bash
convert frame_000.pam frame_000.png
```


### Texture Format

The renderer supports PAM (Portable Arbitrary Map) format textures:

```
P7
WIDTH 512
HEIGHT 512
DEPTH 3
MAXVAL 255
TUPLTYPE RGB
ENDHDR
<binary RGB data>
```


### Concepts Summary

#### What Works

1. *Fixed UVs* - Texture coordinates are baked into the model geometry
2. *Perspective Correction* - Interpolate u/z, v/z, and 1/z instead of u, v
3. *View-Space Depth* - Use camera-space z values, not post-projection
4. *Proper Interpolation* - Barycentric coordinates ensure smooth gradients

### What Does Not

1. Recalculating UVs based on rotated vertex positions
2. Linear interpolation of u, v in screen space
3. Using post-projection z values for perspective correction
4. Incorrect barycentric coordinate calculation


### Performance Notes

- Software rendering: ~60 frames in a few seconds on modern hardware
- No GPU acceleration
- Triangle rasterization is the bottleneck (each pixel checks barycentric coords)
- Painter's algorithm for depth sorting (sorts triangles by average z)


### Mathematical Foundation

The perspective-correct formula derives from:

```
In 3D space: Q = (1-u-v)·P1 + u·P2 + v·P3
After projection: Q' = (1-u'-v')·P1' + u'·P2' + v'·P3'

Where: u' = u/z / ((1-u-v)/z1 + u/z2 + v/z3)
       v' = v/z / ((1-u-v)/z1 + u/z2 + v/z3)

Solving for u, v given screen-space u', v' requires the reciprocal interpolation.
```

This is why we interpolate 1/z, u/z, v/z and then recover u and v by dividing.


### References

- [Texture Mapping](https://en.wikipedia.org/wiki/Texture_mapping)
- [Perspective Correct Interpolation](https://www.comp.nus.edu.sg/~lowkl/publications/lowk_persp_interp_techrep.pdf)
- [Barycentric Coordinates](https://en.wikipedia.org/wiki/Barycentric_coordinate_system)


### Notes

This implementation prioritizes *correctness and clarity* over performance.
It demonstrates the fundamental algorithms used in hardware GPU rasterisers,
just implemented in software.

The perspective-correct interpolation is particularly important--without it,
textures appear to "swim" or warp across rotating surfaces, creating visual
artifacts that break the illusion of 3D.
