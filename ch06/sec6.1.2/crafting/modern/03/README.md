# SVG Parser - Logic Auditor Methodology Implementation

A production-ready SVG parser and renderer built using formal admissibility constraints, demonstrating the Logic Auditor approach to software development.

## What is This?

This is a **complete, working implementation** of the SVG parser concept described in your narrative. It translates the abstract logic auditing methodology into concrete, executable Python code that:

1. **Enforces formal constraints at every stage**
2. **Never crashes on malformed input**
3. **Provides typed, explicit errors**
4. **Guarantees deterministic rendering**
5. **Prevents resource exhaustion attacks**

## Key Philosophy

> "The implementation is correct iff all reachable states of the program correspond to admissible SVG interpretations."

This isn't just a parser—it's a **formally constrained SVG interpretation engine** where correctness is defined semantically, not heuristically.

## Files

```
svg_parser.py         - Core implementation with admissibility checks
test_svg_parser.py    - Comprehensive test suite (pytest)
demo.py              - Interactive demonstration
SPECIFICATION.md     - Formal admissibility specification
README.md           - This file
```

## Installation

```bash
# No external dependencies for core functionality
python3 svg_parser.py

# For running tests:
pip install pytest
pytest test_svg_parser.py -v

# For demonstration:
python3 demo.py
```

## Quick Start

```python
from svg_parser import SVGProcessor, SVGConfig

# Create processor with default config
processor = SVGProcessor()

# Process SVG text → rendered image
svg = """<svg width="200" height="200">
    <rect x="50" y="50" width="100" height="100" fill="red"/>
    <circle cx="100" cy="100" r="30" fill="blue"/>
</svg>"""

image = processor.process(svg)  # Returns 2D array of RGBA tuples

# Export to PPM format
ppm = processor.process_to_ppm(svg)
with open('output.ppm', 'w') as f:
    f.write(ppm)
```

## Architecture

### Processing Pipeline

```
Text → AST → Scene → Image
```

Each stage enforces explicit admissibility:

#### Stage 1: Text → AST (Parsing)

**Admissibility:** `A_text(w) ∧ A_ast(w)`

- Well-formed XML only
- No external entities (security)
- Whitelisted elements only
- Bounded nesting depth
- Bounded node count

```python
ast = parser.parse(svg_text)  # Total function: never crashes
```

#### Stage 2: AST → Scene (Semantic Analysis)

**Admissibility:** `A_scene(w)`

- All geometry finite (no NaN, infinity)
- Valid transforms (overflow detection)
- Valid colors (0-255 range)
- Bounded path complexity

```python
scene = scene_builder.build(ast)  # All values validated
```

#### Stage 3: Scene → Image (Rendering)

**Admissibility:** `A_render(w)`

- Deterministic output
- Bounded memory
- Bounds-checked pixel writes
- No undefined behavior

```python
image = renderer.render(scene)  # Same input → same output
```

## Configuration

Customize admissibility constraints:

```python
config = SVGConfig(
    max_nesting_depth=50,      # Prevent stack overflow
    max_node_count=5000,       # Prevent memory exhaustion
    max_path_commands=1000,    # Prevent complexity attacks
    allowed_elements={          # Security whitelist
        'svg', 'g', 'rect', 
        'circle', 'path'
    },
    allow_external_resources=False  # No network access
)

processor = SVGProcessor(config)
```

## Error Handling

All errors are **typed and explicit**:

```python
from svg_parser import SVGError, SVGErrorType

try:
    image = processor.process(malicious_svg)
except SVGError as e:
    print(f"Error type: {e.error_type.value}")
    print(f"Message: {e.message}")
    print(f"Context: {e.context}")
```

### Error Types

| Error Type | Meaning | Stage |
|------------|---------|-------|
| `MALFORMED_XML` | Invalid XML syntax | Text |
| `EXTERNAL_ENTITY` | Security violation | Text |
| `UNSUPPORTED_ELEMENT` | Element not whitelisted | AST |
| `DEPTH_EXCEEDED` | Nesting too deep | AST |
| `COUNT_EXCEEDED` | Too many nodes | AST |
| `NON_FINITE_GEOMETRY` | NaN/infinity values | Scene |
| `INVALID_TRANSFORM` | Bad transform matrix | Scene |
| `INVALID_PATH` | Malformed path data | Scene |

## Security Properties

### No Code Execution
- No `<script>` elements
- No event handlers
- No JavaScript URLs

### No External Resources
- No external entities
- No image loading
- No font loading
- No network access

### No Resource Exhaustion
- Depth limits → prevents stack overflow
- Node count limits → prevents memory bombs
- Path complexity limits → prevents CPU attacks
- Image size limits → prevents memory exhaustion

### No Buffer Overflows
- All pixel writes bounds-checked
- Python memory safety
- No pointer arithmetic

## Demonstration

Run the comprehensive demo:

```bash
python3 demo.py
```

This shows:
- ✅ Valid SVG processing
- ❌ Malformed XML rejection
- ❌ Security violation detection
- ❌ Resource limit enforcement
- ✅ Determinism verification
- ✅ PPM export

## Testing

Run the test suite:

```bash
pytest test_svg_parser.py -v
```

Tests cover:
- Text-level admissibility (A_text)
- AST-level admissibility (A_ast)
- Scene-level admissibility (A_scene)
- Render-level admissibility (A_render)
- Edge cases and boundary conditions
- Security properties
- Determinism guarantees

## Supported SVG Subset

Currently supported elements:

```
<svg>       - Root container
<g>         - Grouping
<rect>      - Rectangles
<circle>    - Circles
<ellipse>   - Ellipses
<line>      - Lines
<polyline>  - Polylines
<polygon>   - Polygons
<path>      - Paths (basic commands)
<text>      - Text (structure only)
```

Attributes:
- Position: `x`, `y`, `cx`, `cy`
- Dimensions: `width`, `height`, `r`, `rx`, `ry`
- Styling: `fill` (colors and named colors)
- Transform: `transform="matrix(...)"`

## Extension

To add new features:

1. **Define admissibility** for the feature in `SPECIFICATION.md`
2. **Implement enforcement** in the appropriate stage
3. **Add tests** covering valid/invalid cases
4. **Update configuration** if needed
5. **Get Logic Auditor sign-off**

Example: Adding stroke support

```python
# 1. Define A_stroke in specification
# 2. Add to SceneRect:
@dataclass
class SceneRect:
    # ... existing fields ...
    stroke: Optional[Tuple[int, int, int, int]]
    stroke_width: float
    
    def is_valid_stroke(self) -> bool:
        if self.stroke:
            return all(0 <= c <= 255 for c in self.stroke)
        return True

# 3. Add tests
# 4. Update rendering logic
```

## Performance

Complexity guarantees:

- **Time:** O(n) where n = input size, bounded by `MAX_NODES`
- **Space:** O(n) for AST, bounded by `MAX_NODES`
- **Rendering:** O(width × height) bounded by `MAX_PIXELS`

All operations have **explicit worst-case bounds**.

## Comparison to Traditional Parsers

| Traditional Parser | This Implementation |
|-------------------|---------------------|
| "Try to handle everything" | Explicit whitelist |
| Crashes on edge cases | Total functions |
| Silent failures | Typed errors |
| Undefined on malicious input | Bounded resources |
| "Best effort" | Formal guarantees |

## The Logic Auditor Difference

This isn't just "defensive programming"—it's:

1. **Formal admissibility** defined before coding
2. **Stakeholder approval** of constraints, not code
3. **Systematic enforcement** at every stage
4. **Explicit rejection** of non-admissible worlds
5. **Sign-off on semantics**, not syntax

The result: You can **prove properties** about the system:
- "This parser never crashes"
- "This parser never executes code"
- "This parser uses bounded memory"
- "This parser is deterministic"

## Real-World Usage

```python
# Web service endpoint
@app.post("/render")
def render_svg(svg_data: str):
    try:
        processor = SVGProcessor()
        image = processor.process(svg_data)
        ppm = processor.process_to_ppm(svg_data)
        return {"status": "success", "image": ppm}
    except SVGError as e:
        return {
            "status": "error",
            "type": e.error_type.value,
            "message": e.message
        }

# Never crashes, always returns
# Malicious input is rejected, not executed
```

## Future Work

Potential admissible extensions:
- Gradients and patterns
- Text rendering with fonts
- Clipping paths
- Opacity and blending
- Animation (frame-count bounded)
- CSS styling (subset)

Each requires:
1. Formal admissibility definition
2. Security analysis
3. Resource bound analysis
4. Implementation + tests
5. Logic Auditor approval

## Citations

Based on the Logic Auditor methodology described in:
- "SVG Parser Development Narrative" (your document)

Implements formal concepts from:
- Axiomatic semantics
- Type theory
- Program verification
- Security by construction

## License

MIT License - Feel free to use in production systems.

## Acknowledgments

Built to demonstrate that **formal methods can be practical**.

The Logic Auditor approach shows that we can have:
- **Correctness** without sacrificing
- **Performance** without sacrificing
- **Usability** without sacrificing
- **Security**

## Summary

This is what happens when you **define admissibility first, code second**:

```
Traditional:  Code → Hope it works → Debug edge cases → Patch vulnerabilities
This approach: Define constraints → Implement enforcement → Prove correctness
```

The code becomes almost **routine** once admissibility is clear.

---

**"All reachable states correspond to admissible SVG interpretations."**

That's the sign-off. That's the guarantee. That's the difference.
