
## OBJ to Animated GIF Renderer

A pipeline for rendering 3D OBJ models as rotating wireframe animations in GIF format.

This system consists of two main components:

1. *C Program* (`obj_animator.c`) - Loads an OBJ file and renders multiple animation frames to PAM 7 ASCII format
2. *Python Script* (`pam_to_gif.py`) - Merges PAM frames into an animated GIF

- Loads standard OBJ files (vertices and triangular faces)
- 3D wireframe rendering with perspective projection
- Customizable animation (frames, resolution, rotation)
- Outputs PAM 7 ASCII format (human-readable image format)
- Automatic GIF assembly with PIL/Pillow
- Support for various OBJ face formats (v, v/vt, v/vt/vn, v//vn)


### For C Program
- GCC or compatible C compiler
- Math library (libm)

### For Python Script
- Python 3.6+
- Pillow (PIL fork)

Install Python dependencies:
```bash
pip install Pillow
```

Or:
```bash
pip install Pillow --break-system-packages  # If needed on some systems
```

### Quick Start

#### Option 1: Using Make (Recommended)
```bash
# Build and create animation in one step
make animate

# This will:
# 1. Compile obj_animator.c
# 2. Generate 36 frames of test_cube.obj
# 3. Merge frames into animation.gif
```

#### Option 2: Manual Steps
```bash
# 1. Compile the C program
gcc -Wall -O2 -o obj_animator obj_animator.c -lm

# 2. Generate animation frames
./obj_animator test_cube.obj frame 36 800 600

# 3. Merge frames into GIF
python3 pam_to_gif.py "frame_*.pam" animation.gif 100 0
```

### Usage Details

#### C Program: obj_animator

```bash
./obj_animator [obj_file] [output_prefix] [num_frames] [width] [height]
```

*Arguments:*
- `obj_file` - Path to OBJ model file (default: `model.obj`)
- `output_prefix` - Prefix for output PAM files (default: `frame`)
- `num_frames` - Number of animation frames (default: `36`)
- `width` - Frame width in pixels (default: `800`)
- `height` - Frame height in pixels (default: `600`)

*Examples:*
```bash
# Use all defaults
./obj_animator

# Render teapot with 60 frames
./obj_animator teapot.obj teapot 60

# High-resolution animation
./obj_animator model.obj hires 48 1920 1080

# Quick low-res preview
./obj_animator model.obj preview 24 400 300
```

*Output:*
Creates PAM files named `{prefix}_000.pam`, `{prefix}_001.pam`, etc.

#### Python Script: pam_to_gif.py

```bash
python3 pam_to_gif.py <pattern> [output.gif] [duration_ms] [loop]
```

*Arguments:*
- `pattern` - Glob pattern for PAM files (e.g., `"frame_*.pam"`)
- `output.gif` - Output filename (default: `animation.gif`)
- `duration_ms` - Frame duration in milliseconds (default: `100`)
- `loop` - Loop count, 0 = infinite (default: `0`)

*Examples:*
```bash
# Create infinite loop animation at 10 FPS
python3 pam_to_gif.py "frame_*.pam" animation.gif 100 0

# Fast animation (20 FPS)
python3 pam_to_gif.py "frame_*.pam" fast.gif 50

# Slow animation (5 FPS)
python3 pam_to_gif.py "frame_*.pam" slow.gif 200

# Play once only
python3 pam_to_gif.py "frame_*.pam" once.gif 100 1
```

### PAM 7 ASCII Format

The PAM (Portable Arbitrary Map) format is a flexible image format.
This project uses ASCII encoding for human readability.

*Format Structure:*
```
P7
WIDTH 800
HEIGHT 600
DEPTH 3
MAXVAL 255
TUPLTYPE RGB
ENDHDR
255 0 0 128 128 128 ...
```

*Advantages:*
- Human-readable and debuggable
- Simple parsing
- No binary complications
- Easy to verify manually

### Viewing PAM Files

You can view individual PAM frames using the included viewer:

1. Open `pam7viewer.html` in a web browser
2. Drag and drop a `.pam` file
3. The image will be rendered in the browser

Or use ImageMagick:
```bash
convert frame_000.pam frame_000.png
```

### OBJ File Format

The animator supports standard OBJ files with:
- *Vertices* (v x y z)
- *Faces* (f v1 v2 v3)

Supported face formats:
- `f 1 2 3` (vertex indices only)
- `f 1/1 2/2 3/3` (vertex/texture indices)
- `f 1/1/1 2/2/2 3/3/3` (vertex/texture/normal indices)
- `f 1//1 2//2 3//3` (vertex//normal indices)

*Note:* Only triangle faces are supported. Quad faces must be triangulated.

### Customisation

#### Modifying Animation

Edit `obj_animator.c` to customize:

*Camera position:*
```c
camera.position = (Vec3){0, 0, 5};  // Move camera back/forward
```

*Initial rotation:*
```c
Vec3 object_rot = {0.2f, 0, 0};  // Tilt on X axis
```

*Background color:*
```c
clear_framebuffer(fb, 20, 20, 30);  // R, G, B (0-255)
```

*Wireframe color:*
```c
render_wireframe(fb, model, &camera, object_pos, object_rot, 
                100, 200, 255);  // Light blue (R, G, B)
```

*Rotation axis:*
```c
// In generate_animation() function:
object_rot.y = (2.0f * M_PI * frame) / num_frames;  // Y-axis (change to .x or .z)
```

#### Adding Multiple Rotations

For more complex animations, modify the rotation update:
```c
object_rot.x = (2.0f * M_PI * frame) / num_frames * 0.3f;  // Slow X rotation
object_rot.y = (2.0f * M_PI * frame) / num_frames;         // Full Y rotation
object_rot.z = (2.0f * M_PI * frame) / num_frames * 0.1f;  // Subtle Z rotation
```

### Makefile Targets

```bash
make           # Build the program
make test      # Build and run with test cube
make animate   # Build, run, and create GIF
make clean     # Remove executable, PAM files, and GIFs
```

### Troubleshooting

"Error: Cannot open file model.obj"
- Make sure the OBJ file exists
- Check the file path
- Verify the file is readable

"No vertices found in OBJ file"
- Ensure the OBJ file contains vertex lines (`v x y z`)
- Check file encoding (should be ASCII/UTF-8)

"No PAM files found matching pattern"
- Check that the C program ran successfully
- Verify PAM files were created
- Use quotes around the pattern: `"frame_*.pam"`

GIF looks wrong
- Try different duration values (50-200ms typical)
- Check PAM files with the viewer
- Verify all PAM files have the same dimensions

Math library linking error
- Add `-lm` flag when compiling manually
- Example: `gcc -o obj_animator obj_animator.c -lm`


### Project Ideas or Contributing

Feel free to extend this:
- Add backface culling
- Implement solid rendering with Z-buffer
- Support lighting and shading
- Add camera controls (orbit, zoom)
- Multi-object scenes
- Keyframe-based animation

