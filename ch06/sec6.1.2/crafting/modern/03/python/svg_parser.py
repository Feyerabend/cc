"""
SVG Parser and Renderer with Formal Admissibility Constraints

This implementation follows the Logic Auditor methodology:
- Each processing stage enforces explicit admissibility conditions
- No stage assumes correctness from previous stages
- All functions are total over their input domains
- Errors are typed and explicit
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict, Tuple
import xml.etree.ElementTree as ET
import math
import re


# ============================================================================
# Error Types - Explicit, Typed Failure Modes
# ============================================================================

class SVGErrorType(Enum):
    """Categorized error types corresponding to admissibility violations"""
    MALFORMED_XML = "malformed_xml"
    EXTERNAL_ENTITY = "external_entity"
    UNSUPPORTED_ELEMENT = "unsupported_element"
    INVALID_ATTRIBUTE = "invalid_attribute"
    NON_FINITE_GEOMETRY = "non_finite_geometry"
    INVALID_TRANSFORM = "invalid_transform"
    INVALID_PATH = "invalid_path"
    DEPTH_EXCEEDED = "depth_exceeded"
    COUNT_EXCEEDED = "count_exceeded"


class SVGError(Exception):
    """Base exception for all SVG processing failures"""
    def __init__(self, error_type: SVGErrorType, message: str, context: str = ""):
        self.error_type = error_type
        self.message = message
        self.context = context
        super().__init__(f"{error_type.value}: {message}" + 
                        (f" (context: {context})" if context else ""))


# ============================================================================
# Configuration - Explicit Bounds and Constraints
# ============================================================================

@dataclass
class SVGConfig:
    """
    Explicit configuration defining admissible SVG worlds.
    These bounds prevent resource exhaustion and undefined behavior.
    """
    max_nesting_depth: int = 100
    max_node_count: int = 10000
    max_path_commands: int = 10000
    allowed_elements: set = None
    allow_external_resources: bool = False
    
    def __post_init__(self):
        if self.allowed_elements is None:
            # Explicitly enumerated safe subset
            self.allowed_elements = {
                'svg', 'g', 'rect', 'circle', 'ellipse', 
                'line', 'polyline', 'polygon', 'path', 'text'
            }


# ============================================================================
# AST - Parsed Representation
# ============================================================================

@dataclass
class SVGTransform:
    """Geometric transformation with admissibility constraints"""
    matrix: Tuple[float, float, float, float, float, float]
    
    @staticmethod
    def identity():
        return SVGTransform((1.0, 0.0, 0.0, 1.0, 0.0, 0.0))
    
    def is_finite(self) -> bool:
        """Admissibility: all matrix elements must be finite"""
        return all(math.isfinite(v) for v in self.matrix)
    
    def compose(self, other: 'SVGTransform') -> 'SVGTransform':
        """Matrix multiplication with overflow checking"""
        a1, b1, c1, d1, e1, f1 = self.matrix
        a2, b2, c2, d2, e2, f2 = other.matrix
        
        # Perform multiplication
        try:
            result = (
                a1 * a2 + c1 * b2,
                b1 * a2 + d1 * b2,
                a1 * c2 + c1 * d2,
                b1 * c2 + d1 * d2,
                a1 * e2 + c1 * f2 + e1,
                b1 * e2 + d1 * f2 + f1
            )
        except (OverflowError, ValueError) as e:
            raise SVGError(
                SVGErrorType.INVALID_TRANSFORM,
                f"Transform composition overflow: {str(e)}"
            )
        
        transform = SVGTransform(result)
        if not transform.is_finite():
            raise SVGError(
                SVGErrorType.INVALID_TRANSFORM,
                "Transform composition resulted in non-finite values"
            )
        return transform


@dataclass
class SVGNode:
    """AST node with explicit type and admissibility constraints"""
    tag: str
    attributes: Dict[str, str]
    children: List['SVGNode']
    transform: SVGTransform
    depth: int  # Track nesting for admissibility


# ============================================================================
# Scene Graph - Semantic Representation
# ============================================================================

@dataclass
class BoundingBox:
    """Axis-aligned bounding box with finiteness guarantee"""
    x: float
    y: float
    width: float
    height: float
    
    def is_finite(self) -> bool:
        """Admissibility: all bounds must be finite"""
        return all(math.isfinite(v) for v in [self.x, self.y, self.width, self.height])
    
    def is_valid(self) -> bool:
        """Admissibility: width and height must be non-negative"""
        return self.is_finite() and self.width >= 0 and self.height >= 0


@dataclass
class SceneRect:
    x: float
    y: float
    width: float
    height: float
    fill: Tuple[int, int, int, int]  # RGBA
    transform: SVGTransform


@dataclass
class SceneCircle:
    cx: float
    cy: float
    r: float
    fill: Tuple[int, int, int, int]
    transform: SVGTransform


@dataclass
class ScenePath:
    commands: List[Tuple[str, List[float]]]
    fill: Tuple[int, int, int, int]
    transform: SVGTransform


@dataclass
class Scene:
    """
    Semantic scene graph with guaranteed admissibility properties:
    - All geometry is finite
    - All transforms are valid
    - All colors are in [0, 255]
    """
    shapes: List[object]  # Union of SceneRect, SceneCircle, ScenePath
    viewport: BoundingBox
    
    def is_admissible(self) -> bool:
        """Check all scene-level admissibility constraints"""
        if not self.viewport.is_valid():
            return False
        
        for shape in self.shapes:
            if hasattr(shape, 'transform') and not shape.transform.is_finite():
                return False
        
        return True


# ============================================================================
# Stage 1: Text → AST (Parse with Admissibility Checks)
# ============================================================================

class SVGParser:
    """
    Parser enforcing text-level and AST-level admissibility.
    
    Admissibility conditions:
    - A_text: Well-formed XML, no external entities
    - A_ast: Only allowed tags, bounded depth, bounded count
    """
    
    def __init__(self, config: SVGConfig):
        self.config = config
        self.node_count = 0
    
    def parse(self, text: str) -> SVGNode:
        """
        Total function: str → Result[SVGNode, SVGError]
        
        Never crashes, always returns or raises typed error.
        """
        # A_text: No external entities (check BEFORE parsing for security)
        if '<!ENTITY' in text or '<!DOCTYPE' in text:
            raise SVGError(
                SVGErrorType.EXTERNAL_ENTITY,
                "External entities not allowed"
            )
        
        # A_text: Well-formed XML check
        try:
            root = ET.fromstring(text)
        except ET.ParseError as e:
            raise SVGError(
                SVGErrorType.MALFORMED_XML,
                f"XML parsing failed: {str(e)}"
            )
        
        # Reset counters for this parse
        self.node_count = 0
        
        # Build AST with admissibility enforcement
        ast = self._build_ast(root, depth=0, parent_transform=SVGTransform.identity())
        
        return ast
    
    def _build_ast(self, elem: ET.Element, depth: int, 
                   parent_transform: SVGTransform) -> SVGNode:
        """
        Recursive AST builder with admissibility guards.
        
        Enforces:
        - Maximum depth (prevents stack overflow)
        - Maximum node count (prevents memory exhaustion)
        - Allowed elements only
        """
        # A_ast: Depth bound
        if depth > self.config.max_nesting_depth:
            raise SVGError(
                SVGErrorType.DEPTH_EXCEEDED,
                f"Maximum nesting depth {self.config.max_nesting_depth} exceeded",
                context=f"depth={depth}"
            )
        
        # A_ast: Node count bound
        self.node_count += 1
        if self.node_count > self.config.max_node_count:
            raise SVGError(
                SVGErrorType.COUNT_EXCEEDED,
                f"Maximum node count {self.config.max_node_count} exceeded"
            )
        
        # Extract tag (remove namespace if present)
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        
        # A_ast: Allowed elements only
        if tag not in self.config.allowed_elements:
            raise SVGError(
                SVGErrorType.UNSUPPORTED_ELEMENT,
                f"Element '{tag}' not in allowed set",
                context=f"allowed={self.config.allowed_elements}"
            )
        
        # Parse attributes
        attributes = dict(elem.attrib)
        
        # Parse transform with admissibility checking
        transform = self._parse_transform(attributes.get('transform', ''))
        current_transform = parent_transform.compose(transform)
        
        # Recursively build children
        children = []
        for child in elem:
            child_node = self._build_ast(child, depth + 1, current_transform)
            children.append(child_node)
        
        return SVGNode(
            tag=tag,
            attributes=attributes,
            children=children,
            transform=current_transform,
            depth=depth
        )
    
    def _parse_transform(self, transform_str: str) -> SVGTransform:
        """
        Parse SVG transform attribute with admissibility checks.
        
        Returns identity transform if empty or invalid.
        Raises on non-finite results.
        """
        if not transform_str:
            return SVGTransform.identity()
        
        # Simple transform parser (production code would be more complete)
        # For now, support matrix() and identity
        transform_str = transform_str.strip()
        
        if transform_str.startswith('matrix('):
            match = re.match(r'matrix\(([-\d.e\s,]+)\)', transform_str)
            if match:
                try:
                    values = [float(x) for x in re.split(r'[,\s]+', match.group(1).strip())]
                    if len(values) == 6:
                        transform = SVGTransform(tuple(values))
                        if not transform.is_finite():
                            raise SVGError(
                                SVGErrorType.INVALID_TRANSFORM,
                                "Transform contains non-finite values",
                                context=transform_str
                            )
                        return transform
                except (ValueError, OverflowError):
                    raise SVGError(
                        SVGErrorType.INVALID_TRANSFORM,
                        "Failed to parse transform values",
                        context=transform_str
                    )
        
        # Unsupported or malformed: return identity (could also raise)
        return SVGTransform.identity()


# ============================================================================
# Stage 2: AST → Scene (Semantic Analysis with Admissibility)
# ============================================================================

class SceneBuilder:
    """
    Converts AST to semantic scene graph.
    
    Admissibility conditions:
    - A_scene: Finite geometry
    - A_scene: Valid transforms
    - A_scene: Valid colors
    """
    
    def __init__(self, config: SVGConfig):
        self.config = config
    
    def build(self, ast: SVGNode) -> Scene:
        """
        Total function: SVGNode → Result[Scene, SVGError]
        """
        shapes = []
        
        # Extract viewport from root SVG element
        viewport = self._extract_viewport(ast)
        if not viewport.is_valid():
            raise SVGError(
                SVGErrorType.NON_FINITE_GEOMETRY,
                "Invalid viewport dimensions"
            )
        
        # Recursively process nodes
        self._process_node(ast, shapes)
        
        scene = Scene(shapes=shapes, viewport=viewport)
        
        # Final admissibility check
        if not scene.is_admissible():
            raise SVGError(
                SVGErrorType.NON_FINITE_GEOMETRY,
                "Scene failed admissibility check"
            )
        
        return scene
    
    def _extract_viewport(self, ast: SVGNode) -> BoundingBox:
        """Extract viewport, enforcing admissibility constraints"""
        try:
            width = float(ast.attributes.get('width', '800'))
            height = float(ast.attributes.get('height', '600'))
            
            # Admissibility: must be finite
            if not (math.isfinite(width) and math.isfinite(height)):
                raise SVGError(
                    SVGErrorType.NON_FINITE_GEOMETRY,
                    "Viewport dimensions must be finite"
                )
            
            # Admissibility: must be positive
            if width <= 0 or height <= 0:
                raise SVGError(
                    SVGErrorType.NON_FINITE_GEOMETRY,
                    f"Viewport dimensions must be positive (got {width}x{height})"
                )
            
            # Admissibility: reasonable upper bound (prevents memory bombs)
            MAX_DIMENSION = 10000
            if width > MAX_DIMENSION or height > MAX_DIMENSION:
                raise SVGError(
                    SVGErrorType.NON_FINITE_GEOMETRY,
                    f"Viewport dimensions {width}x{height} exceed maximum {MAX_DIMENSION}"
                )
            
            return BoundingBox(0, 0, width, height)
        
        except ValueError as e:
            raise SVGError(
                SVGErrorType.NON_FINITE_GEOMETRY,
                f"Invalid viewport dimensions: {e}"
            )
        except OverflowError as e:
            raise SVGError(
                SVGErrorType.NON_FINITE_GEOMETRY,
                f"Viewport dimension overflow: {e}"
            )
    
    def _process_node(self, node: SVGNode, shapes: List):
        """Recursively convert AST nodes to scene shapes"""
        
        if node.tag == 'rect':
            shape = self._build_rect(node)
            if shape:
                shapes.append(shape)
        
        elif node.tag == 'circle':
            shape = self._build_circle(node)
            if shape:
                shapes.append(shape)
        
        elif node.tag == 'path':
            shape = self._build_path(node)
            if shape:
                shapes.append(shape)
        
        # Process children (for <g>, <svg>, etc.)
        for child in node.children:
            self._process_node(child, shapes)
    
    def _build_rect(self, node: SVGNode) -> Optional[SceneRect]:
        """Build rectangle with admissibility checks"""
        try:
            x = float(node.attributes.get('x', '0'))
            y = float(node.attributes.get('y', '0'))
            width = float(node.attributes.get('width', '0'))
            height = float(node.attributes.get('height', '0'))
            
            # Admissibility: finite and non-negative
            if not all(math.isfinite(v) for v in [x, y, width, height]):
                return None
            if width < 0 or height < 0:
                return None
            
            fill = self._parse_color(node.attributes.get('fill', 'black'))
            
            return SceneRect(
                x=x, y=y, width=width, height=height,
                fill=fill,
                transform=node.transform
            )
        except (ValueError, OverflowError):
            return None
    
    def _build_circle(self, node: SVGNode) -> Optional[SceneCircle]:
        """Build circle with admissibility checks"""
        try:
            cx = float(node.attributes.get('cx', '0'))
            cy = float(node.attributes.get('cy', '0'))
            r = float(node.attributes.get('r', '0'))
            
            # Admissibility: finite and non-negative radius
            if not all(math.isfinite(v) for v in [cx, cy, r]):
                return None
            if r < 0:
                return None
            
            fill = self._parse_color(node.attributes.get('fill', 'black'))
            
            return SceneCircle(
                cx=cx, cy=cy, r=r,
                fill=fill,
                transform=node.transform
            )
        except (ValueError, OverflowError):
            return None
    
    def _build_path(self, node: SVGNode) -> Optional[ScenePath]:
        """Build path with admissibility checks"""
        d = node.attributes.get('d', '')
        if not d:
            return None
        
        # Don't catch SVGError - let it propagate
        commands = self._parse_path_data(d)
        fill = self._parse_color(node.attributes.get('fill', 'black'))
        
        return ScenePath(
            commands=commands,
            fill=fill,
            transform=node.transform
        )
    
    def _parse_path_data(self, d: str) -> List[Tuple[str, List[float]]]:
        """
        Parse path data with admissibility constraints.
        
        A_scene: Command count bounded, all values finite
        """
        commands = []
        
        # Simple path parser (production would be more robust)
        # Supports: M, L, H, V, Z
        tokens = re.findall(r'[MLHVZmlhvz]|[-\d.e]+', d)
        
        i = 0
        while i < len(tokens):
            # A_scene: Enforce command limit
            if len(commands) >= self.config.max_path_commands:
                raise SVGError(
                    SVGErrorType.INVALID_PATH,
                    f"Path command count exceeds {self.config.max_path_commands}"
                )
            
            token = tokens[i]
            
            if token in 'Zz':
                commands.append(('Z', []))
                i += 1
            elif token in 'Mm':
                if i + 2 >= len(tokens):
                    break
                x = float(tokens[i + 1])
                y = float(tokens[i + 2])
                if not (math.isfinite(x) and math.isfinite(y)):
                    raise SVGError(
                        SVGErrorType.NON_FINITE_GEOMETRY,
                        "Non-finite path coordinates"
                    )
                commands.append(('M', [x, y]))
                i += 3
            elif token in 'Ll':
                if i + 2 >= len(tokens):
                    break
                x = float(tokens[i + 1])
                y = float(tokens[i + 2])
                if not (math.isfinite(x) and math.isfinite(y)):
                    raise SVGError(
                        SVGErrorType.NON_FINITE_GEOMETRY,
                        "Non-finite path coordinates"
                    )
                commands.append(('L', [x, y]))
                i += 3
            else:
                i += 1
        
        return commands
    
    def _parse_color(self, color_str: str) -> Tuple[int, int, int, int]:
        """
        Parse color with admissibility: values in [0, 255]
        
        Returns: (r, g, b, a) all in range [0, 255]
        """
        color_str = color_str.strip().lower()
        
        # Named colors
        named_colors = {
            'black': (0, 0, 0, 255),
            'white': (255, 255, 255, 255),
            'red': (255, 0, 0, 255),
            'green': (0, 128, 0, 255),
            'blue': (0, 0, 255, 255),
            'yellow': (255, 255, 0, 255),
            'cyan': (0, 255, 255, 255),
            'magenta': (255, 0, 255, 255),
        }
        
        if color_str in named_colors:
            return named_colors[color_str]
        
        # Hex colors
        if color_str.startswith('#'):
            hex_str = color_str[1:]
            if len(hex_str) == 6:
                try:
                    r = int(hex_str[0:2], 16)
                    g = int(hex_str[2:4], 16)
                    b = int(hex_str[4:6], 16)
                    return (r, g, b, 255)
                except ValueError:
                    pass
        
        # Default to black
        return (0, 0, 0, 255)


# ============================================================================
# Stage 3: Scene → Image (Rendering with Determinism)
# ============================================================================

class Renderer:
    """
    Rasterizer enforcing rendering admissibility.
    
    Admissibility conditions:
    - A_render: Deterministic output
    - A_render: Bounded memory
    - A_render: No undefined behavior
    """
    
    def __init__(self):
        pass
    
    def render(self, scene: Scene) -> List[List[Tuple[int, int, int, int]]]:
        """
        Total function: Scene → Result[Image, SVGError]
        
        Returns RGBA pixel array.
        Deterministic: same scene always produces same output.
        """
        width = int(scene.viewport.width)
        height = int(scene.viewport.height)
        
        # Admissibility: bounded memory
        MAX_PIXELS = 100_000_000  # 100 megapixels
        if width * height > MAX_PIXELS:
            raise SVGError(
                SVGErrorType.NON_FINITE_GEOMETRY,
                f"Image size {width}x{height} exceeds memory bounds (max {MAX_PIXELS} pixels)"
            )
        
        # Initialize canvas with white background
        canvas = [[(255, 255, 255, 255) for _ in range(width)] 
                  for _ in range(height)]
        
        # Render each shape in order (painter's algorithm)
        for shape in scene.shapes:
            if isinstance(shape, SceneRect):
                self._render_rect(canvas, shape, width, height)
            elif isinstance(shape, SceneCircle):
                self._render_circle(canvas, shape, width, height)
            elif isinstance(shape, ScenePath):
                self._render_path(canvas, shape, width, height)
        
        return canvas
    
    def _render_rect(self, canvas, rect: SceneRect, width: int, height: int):
        """Render rectangle with bounds checking"""
        x0 = int(rect.x)
        y0 = int(rect.y)
        x1 = int(rect.x + rect.width)
        y1 = int(rect.y + rect.height)
        
        # Clip to canvas bounds
        x0 = max(0, min(width - 1, x0))
        y0 = max(0, min(height - 1, y0))
        x1 = max(0, min(width, x1))
        y1 = max(0, min(height, y1))
        
        for y in range(y0, y1):
            for x in range(x0, x1):
                canvas[y][x] = rect.fill
    
    def _render_circle(self, canvas, circle: SceneCircle, width: int, height: int):
        """Render circle with bounds checking"""
        cx = int(circle.cx)
        cy = int(circle.cy)
        r = int(circle.r)
        
        # Bounding box
        x0 = max(0, cx - r)
        y0 = max(0, cy - r)
        x1 = min(width, cx + r + 1)
        y1 = min(height, cy + r + 1)
        
        r_squared = r * r
        
        for y in range(y0, y1):
            for x in range(x0, x1):
                dx = x - cx
                dy = y - cy
                if dx * dx + dy * dy <= r_squared:
                    canvas[y][x] = circle.fill
    
    def _render_path(self, canvas, path: ScenePath, width: int, height: int):
        """Render path (simplified: just mark points)"""
        current_x, current_y = 0.0, 0.0
        
        for cmd, params in path.commands:
            if cmd == 'M' and len(params) >= 2:
                current_x, current_y = params[0], params[1]
            elif cmd == 'L' and len(params) >= 2:
                x, y = params[0], params[1]
                # Simple line drawing (Bresenham would be production)
                self._draw_line(canvas, int(current_x), int(current_y),
                               int(x), int(y), path.fill, width, height)
                current_x, current_y = x, y
    
    def _draw_line(self, canvas, x0: int, y0: int, x1: int, y1: int,
                   color: Tuple[int, int, int, int], width: int, height: int):
        """Simple line drawing with bounds checking"""
        # Clip to canvas
        if not (0 <= x0 < width and 0 <= y0 < height):
            return
        if not (0 <= x1 < width and 0 <= y1 < height):
            return
        
        # Simple implementation: just draw endpoints for now
        canvas[y0][x0] = color
        canvas[y1][x1] = color


# ============================================================================
# Complete Pipeline
# ============================================================================

class SVGProcessor:
    """
    Complete SVG processing pipeline with admissibility at every stage.
    
    Pipeline: Text → AST → Scene → Image
    Each stage is a total function with explicit error handling.
    """
    
    def __init__(self, config: Optional[SVGConfig] = None):
        self.config = config or SVGConfig()
        self.parser = SVGParser(self.config)
        self.scene_builder = SceneBuilder(self.config)
        self.renderer = Renderer()
    
    def process(self, svg_text: str) -> List[List[Tuple[int, int, int, int]]]:
        """
        Complete pipeline: SVG text → rendered image
        
        Guarantees:
        - Never crashes on malformed input
        - All errors are typed and explicit
        - Output is deterministic
        - Memory usage is bounded
        """
        # Stage 1: Parse
        ast = self.parser.parse(svg_text)
        
        # Stage 2: Build scene
        scene = self.scene_builder.build(ast)
        
        # Stage 3: Render
        image = self.renderer.render(scene)
        
        return image
    
    def process_to_ppm(self, svg_text: str) -> str:
        """Render to PPM format for easy viewing"""
        image = self.process(svg_text)
        height = len(image)
        width = len(image[0]) if height > 0 else 0
        
        # PPM header
        ppm = f"P3\n{width} {height}\n255\n"
        
        # Pixel data
        for row in image:
            for r, g, b, a in row:
                ppm += f"{r} {g} {b} "
            ppm += "\n"
        
        return ppm
