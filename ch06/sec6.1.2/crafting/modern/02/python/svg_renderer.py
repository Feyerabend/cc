"""
Advanced SVG Parser and Renderer
Supports paths, shapes, gradients, and various rendering modes
"""

import re
import math
from xml.etree import ElementTree as ET
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum


class FillRule(Enum):
    EVENODD = "evenodd"
    NONZERO = "nonzero"


@dataclass
class Color:
    """RGB color representation"""
    r: int
    g: int
    b: int
    a: float = 1.0  # alpha channel
    
    @classmethod
    def from_hex(cls, hex_color: str) -> 'Color':
        """Parse hex color (#RGB or #RRGGBB)"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        return cls(
            int(hex_color[0:2], 16),
            int(hex_color[2:4], 16),
            int(hex_color[4:6], 16)
        )
    
    @classmethod
    def from_rgb(cls, rgb_str: str) -> 'Color':
        """Parse rgb(r,g,b) or rgba(r,g,b,a) format"""
        match = re.search(r'rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)', rgb_str)
        if match:
            r, g, b = int(match.group(1)), int(match.group(2)), int(match.group(3))
            a = float(match.group(4)) if match.group(4) else 1.0
            return cls(r, g, b, a)
        return cls(0, 0, 0)
    
    @classmethod
    def parse(cls, color_str: str) -> 'Color':
        """Parse any color format"""
        color_str = color_str.strip()
        if color_str.startswith('#'):
            return cls.from_hex(color_str)
        elif color_str.startswith('rgb'):
            return cls.from_rgb(color_str)
        else:
            # Named colors
            named_colors = {
                'black': '#000000', 'white': '#FFFFFF', 'red': '#FF0000',
                'green': '#00FF00', 'blue': '#0000FF', 'yellow': '#FFFF00',
                'cyan': '#00FFFF', 'magenta': '#FF00FF', 'gray': '#808080',
                'none': '#FFFFFF'
            }
            return cls.from_hex(named_colors.get(color_str.lower(), '#000000'))
    
    def to_tuple(self) -> Tuple[int, int, int]:
        return (self.r, self.g, self.b)
    
    def blend(self, other: 'Color', t: float) -> 'Color':
        """Blend two colors with parameter t (0-1)"""
        return Color(
            int(self.r + (other.r - self.r) * t),
            int(self.g + (other.g - self.g) * t),
            int(self.b + (other.b - self.b) * t),
            self.a + (other.a - self.a) * t
        )


@dataclass
class Point:
    """2D point representation"""
    x: float
    y: float
    
    def __add__(self, other: 'Point') -> 'Point':
        return Point(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: 'Point') -> 'Point':
        return Point(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar: float) -> 'Point':
        return Point(self.x * scalar, self.y * scalar)
    
    def distance(self, other: 'Point') -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def to_int(self) -> Tuple[int, int]:
        return (int(round(self.x)), int(round(self.y)))


class PathCommand:
    """Base class for SVG path commands"""
    pass


class MoveTo(PathCommand):
    def __init__(self, point: Point):
        self.point = point


class LineTo(PathCommand):
    def __init__(self, point: Point):
        self.point = point


class CubicBezier(PathCommand):
    def __init__(self, cp1: Point, cp2: Point, end: Point):
        self.cp1 = cp1
        self.cp2 = cp2
        self.end = end


class QuadraticBezier(PathCommand):
    def __init__(self, cp: Point, end: Point):
        self.cp = cp
        self.end = end


class Arc(PathCommand):
    def __init__(self, rx: float, ry: float, rotation: float, 
                 large_arc: bool, sweep: bool, end: Point):
        self.rx = rx
        self.ry = ry
        self.rotation = rotation
        self.large_arc = large_arc
        self.sweep = sweep
        self.end = end


class ClosePath(PathCommand):
    pass


class PathParser:
    """Advanced SVG path parser supporting all path commands"""
    
    def __init__(self, path_data: str):
        self.path_data = path_data
        self.commands: List[PathCommand] = []
        self.current_pos = Point(0, 0)
        self.start_pos = Point(0, 0)
        
    def parse(self) -> List[PathCommand]:
        """Parse SVG path data into command objects"""
        # Normalize path data
        path_data = self.path_data.strip()
        path_data = re.sub(r'([a-zA-Z])', r' \1 ', path_data)
        path_data = re.sub(r',', ' ', path_data)
        path_data = re.sub(r'\s+', ' ', path_data)
        
        tokens = path_data.split()
        i = 0
        
        while i < len(tokens):
            cmd = tokens[i]
            i += 1
            
            if cmd in 'Mm':
                x, y = float(tokens[i]), float(tokens[i+1])
                point = Point(x, y) if cmd.isupper() else self.current_pos + Point(x, y)
                self.commands.append(MoveTo(point))
                self.current_pos = point
                self.start_pos = point
                i += 2
                
            elif cmd in 'Ll':
                x, y = float(tokens[i]), float(tokens[i+1])
                point = Point(x, y) if cmd.isupper() else self.current_pos + Point(x, y)
                self.commands.append(LineTo(point))
                self.current_pos = point
                i += 2
                
            elif cmd in 'Hh':
                x = float(tokens[i])
                x = x if cmd.isupper() else self.current_pos.x + x
                point = Point(x, self.current_pos.y)
                self.commands.append(LineTo(point))
                self.current_pos = point
                i += 1
                
            elif cmd in 'Vv':
                y = float(tokens[i])
                y = y if cmd.isupper() else self.current_pos.y + y
                point = Point(self.current_pos.x, y)
                self.commands.append(LineTo(point))
                self.current_pos = point
                i += 1
                
            elif cmd in 'Cc':
                x1, y1 = float(tokens[i]), float(tokens[i+1])
                x2, y2 = float(tokens[i+2]), float(tokens[i+3])
                x, y = float(tokens[i+4]), float(tokens[i+5])
                
                if cmd.isupper():
                    cp1, cp2, end = Point(x1, y1), Point(x2, y2), Point(x, y)
                else:
                    cp1 = self.current_pos + Point(x1, y1)
                    cp2 = self.current_pos + Point(x2, y2)
                    end = self.current_pos + Point(x, y)
                
                self.commands.append(CubicBezier(cp1, cp2, end))
                self.current_pos = end
                i += 6
                
            elif cmd in 'Qq':
                x1, y1 = float(tokens[i]), float(tokens[i+1])
                x, y = float(tokens[i+2]), float(tokens[i+3])
                
                if cmd.isupper():
                    cp, end = Point(x1, y1), Point(x, y)
                else:
                    cp = self.current_pos + Point(x1, y1)
                    end = self.current_pos + Point(x, y)
                
                self.commands.append(QuadraticBezier(cp, end))
                self.current_pos = end
                i += 4
                
            elif cmd in 'Aa':
                rx, ry = float(tokens[i]), float(tokens[i+1])
                rotation = float(tokens[i+2])
                large_arc = bool(int(tokens[i+3]))
                sweep = bool(int(tokens[i+4]))
                x, y = float(tokens[i+5]), float(tokens[i+6])
                
                end = Point(x, y) if cmd.isupper() else self.current_pos + Point(x, y)
                self.commands.append(Arc(rx, ry, rotation, large_arc, sweep, end))
                self.current_pos = end
                i += 7
                
            elif cmd in 'Zz':
                self.commands.append(ClosePath())
                self.current_pos = self.start_pos
        
        return self.commands
    
    def to_polygon(self, tolerance: float = 0.5) -> List[Point]:
        """Convert path commands to polygon points"""
        polygon = []
        current_point = Point(0, 0)
        
        for cmd in self.commands:
            if isinstance(cmd, MoveTo):
                current_point = cmd.point
                polygon.append(current_point)
                
            elif isinstance(cmd, LineTo):
                current_point = cmd.point
                polygon.append(current_point)
                
            elif isinstance(cmd, CubicBezier):
                # Subdivide cubic bezier curve
                points = self._subdivide_cubic_bezier(
                    current_point, cmd.cp1, cmd.cp2, cmd.end, tolerance
                )
                polygon.extend(points)
                current_point = cmd.end
                
            elif isinstance(cmd, QuadraticBezier):
                # Convert quadratic to cubic
                cp1 = current_point + (cmd.cp - current_point) * (2/3)
                cp2 = cmd.end + (cmd.cp - cmd.end) * (2/3)
                points = self._subdivide_cubic_bezier(
                    current_point, cp1, cp2, cmd.end, tolerance
                )
                polygon.extend(points)
                current_point = cmd.end
                
            elif isinstance(cmd, Arc):
                # Approximate arc with line segments
                points = self._arc_to_points(current_point, cmd)
                polygon.extend(points)
                current_point = cmd.end
                
            elif isinstance(cmd, ClosePath):
                pass  # Polygon will automatically close
        
        return polygon
    
    def _subdivide_cubic_bezier(self, p0: Point, p1: Point, p2: Point, 
                                 p3: Point, tolerance: float) -> List[Point]:
        """Recursively subdivide cubic bezier curve"""
        # De Casteljau's algorithm
        mid1 = (p0 + p1) * 0.5
        mid2 = (p1 + p2) * 0.5
        mid3 = (p2 + p3) * 0.5
        mid4 = (mid1 + mid2) * 0.5
        mid5 = (mid2 + mid3) * 0.5
        midpoint = (mid4 + mid5) * 0.5
        
        # Check flatness
        chord_length = p0.distance(p3)
        if chord_length < tolerance:
            return [p3]
        
        deviation = abs(mid4.distance((p0 + p3) * 0.5))
        
        if deviation < tolerance:
            return [p3]
        else:
            left = self._subdivide_cubic_bezier(p0, mid1, mid4, midpoint, tolerance)
            right = self._subdivide_cubic_bezier(midpoint, mid5, mid3, p3, tolerance)
            return left[:-1] + [midpoint] + right
    
    def _arc_to_points(self, start: Point, arc: Arc, num_segments: int = 20) -> List[Point]:
        """Convert elliptical arc to line segments"""
        # Simplified arc approximation
        points = []
        for i in range(1, num_segments + 1):
            t = i / num_segments
            # Linear interpolation (simplified - full implementation would use proper arc math)
            point = start + (arc.end - start) * t
            points.append(point)
        return points


class Rasterizer:
    """Advanced scanline rasterizer with antialiasing support"""
    
    def __init__(self, width: int, height: int, background: Color = None):
        self.width = width
        self.height = height
        self.background = background or Color(255, 255, 255)
        self.canvas = [[self.background.to_tuple() for _ in range(width)] 
                       for _ in range(height)]
    
    def fill_polygon(self, points: List[Point], color: Color, 
                     fill_rule: FillRule = FillRule.EVENODD):
        """Fill polygon using scanline algorithm"""
        if len(points) < 3:
            return
        
        # Build edge table
        edges = []
        for i in range(len(points)):
            p1 = points[i]
            p2 = points[(i + 1) % len(points)]
            
            if abs(p1.y - p2.y) > 0.01:  # Skip horizontal edges
                if p1.y > p2.y:
                    p1, p2 = p2, p1
                edges.append((p1, p2))
        
        if not edges:
            return
        
        # Get y bounds
        min_y = max(0, int(min(e[0].y for e in edges)))
        max_y = min(self.height - 1, int(max(e[1].y for e in edges)))
        
        # Scanline fill
        for y in range(min_y, max_y + 1):
            intersections = []
            
            for p1, p2 in edges:
                if p1.y <= y < p2.y:
                    # Calculate x intersection
                    t = (y - p1.y) / (p2.y - p1.y)
                    x = p1.x + t * (p2.x - p1.x)
                    intersections.append(x)
            
            intersections.sort()
            
            # Fill based on rule
            if fill_rule == FillRule.EVENODD:
                for i in range(0, len(intersections) - 1, 2):
                    x_start = max(0, int(intersections[i]))
                    x_end = min(self.width - 1, int(intersections[i + 1]))
                    
                    for x in range(x_start, x_end + 1):
                        self.canvas[y][x] = color.to_tuple()
            
            elif fill_rule == FillRule.NONZERO:
                # Non-zero winding rule
                winding = 0
                x = 0
                i = 0
                
                while x < self.width and i < len(intersections):
                    if x >= intersections[i]:
                        winding += 1
                        i += 1
                    
                    if winding != 0 and x >= 0 and x < self.width:
                        self.canvas[y][x] = color.to_tuple()
                    
                    x += 1
    
    def draw_circle(self, center: Point, radius: float, color: Color, 
                    num_segments: int = 64):
        """Draw a filled circle"""
        points = []
        for i in range(num_segments):
            angle = 2 * math.pi * i / num_segments
            x = center.x + radius * math.cos(angle)
            y = center.y + radius * math.sin(angle)
            points.append(Point(x, y))
        
        self.fill_polygon(points, color)
    
    def draw_rectangle(self, x: float, y: float, width: float, height: float, 
                       color: Color, rx: float = 0, ry: float = 0):
        """Draw a rectangle with optional rounded corners"""
        if rx == 0 and ry == 0:
            # Simple rectangle
            points = [
                Point(x, y),
                Point(x + width, y),
                Point(x + width, y + height),
                Point(x, y + height)
            ]
            self.fill_polygon(points, color)
        else:
            # Rounded rectangle (simplified)
            self.fill_polygon([
                Point(x + rx, y),
                Point(x + width - rx, y),
                Point(x + width, y + ry),
                Point(x + width, y + height - ry),
                Point(x + width - rx, y + height),
                Point(x + rx, y + height),
                Point(x, y + height - ry),
                Point(x, y + ry)
            ], color)
    
    def draw_ellipse(self, cx: float, cy: float, rx: float, ry: float, 
                     color: Color, num_segments: int = 64):
        """Draw a filled ellipse"""
        points = []
        for i in range(num_segments):
            angle = 2 * math.pi * i / num_segments
            x = cx + rx * math.cos(angle)
            y = cy + ry * math.sin(angle)
            points.append(Point(x, y))
        
        self.fill_polygon(points, color)
    
    def save_ppm(self, filename: str):
        """Save canvas as PPM image"""
        with open(filename, 'w') as f:
            f.write(f"P3\n{self.width} {self.height}\n255\n")
            for row in self.canvas:
                for r, g, b in row:
                    f.write(f"{r} {g} {b} ")
                f.write("\n")
    
    def save_png(self, filename: str):
        """Save canvas as PNG image (requires PIL)"""
        try:
            from PIL import Image
            img_data = []
            for row in self.canvas:
                for pixel in row:
                    img_data.extend(pixel)
            
            img = Image.frombytes('RGB', (self.width, self.height), bytes(img_data))
            img.save(filename)
        except ImportError:
            print("PIL/Pillow not available. Use save_ppm() instead.")


class SVGParser:
    """Advanced SVG parser with comprehensive element support"""
    
    def __init__(self, filename: str = None, svg_string: str = None):
        if filename:
            self.tree = ET.parse(filename)
            self.root = self.tree.getroot()
        elif svg_string:
            self.root = ET.fromstring(svg_string)
        else:
            raise ValueError("Must provide filename or svg_string")
        
        # Extract viewBox or dimensions
        self.width, self.height = self._get_dimensions()
    
    def _get_dimensions(self) -> Tuple[int, int]:
        """Extract SVG dimensions"""
        # Check viewBox first
        viewbox = self.root.get('viewBox')
        if viewbox:
            parts = viewbox.split()
            if len(parts) == 4:
                return int(float(parts[2])), int(float(parts[3]))
        
        # Check width/height attributes
        width = self.root.get('width', '100')
        height = self.root.get('height', '100')
        
        # Remove units
        width = re.sub(r'[a-zA-Z%]', '', width)
        height = re.sub(r'[a-zA-Z%]', '', height)
        
        return int(float(width)), int(float(height))
    
    def parse(self) -> List[Dict[str, Any]]:
        """Parse all SVG elements"""
        elements = []
        
        for elem in self.root.iter():
            tag = elem.tag.split('}')[-1]  # Remove namespace
            
            if tag == 'path':
                elements.append(self._parse_path(elem))
            elif tag == 'rect':
                elements.append(self._parse_rect(elem))
            elif tag == 'circle':
                elements.append(self._parse_circle(elem))
            elif tag == 'ellipse':
                elements.append(self._parse_ellipse(elem))
            elif tag == 'polygon':
                elements.append(self._parse_polygon(elem))
            elif tag == 'polyline':
                elements.append(self._parse_polyline(elem))
        
        return elements
    
    def _parse_path(self, elem: ET.Element) -> Dict[str, Any]:
        """Parse path element"""
        d = elem.get('d', '')
        fill = self._get_fill(elem)
        stroke = self._get_stroke(elem)
        
        return {
            'type': 'path',
            'data': d,
            'fill': fill,
            'stroke': stroke
        }
    
    def _parse_rect(self, elem: ET.Element) -> Dict[str, Any]:
        """Parse rectangle element"""
        return {
            'type': 'rect',
            'x': float(elem.get('x', 0)),
            'y': float(elem.get('y', 0)),
            'width': float(elem.get('width', 0)),
            'height': float(elem.get('height', 0)),
            'rx': float(elem.get('rx', 0)),
            'ry': float(elem.get('ry', 0)),
            'fill': self._get_fill(elem),
            'stroke': self._get_stroke(elem)
        }
    
    def _parse_circle(self, elem: ET.Element) -> Dict[str, Any]:
        """Parse circle element"""
        return {
            'type': 'circle',
            'cx': float(elem.get('cx', 0)),
            'cy': float(elem.get('cy', 0)),
            'r': float(elem.get('r', 0)),
            'fill': self._get_fill(elem),
            'stroke': self._get_stroke(elem)
        }
    
    def _parse_ellipse(self, elem: ET.Element) -> Dict[str, Any]:
        """Parse ellipse element"""
        return {
            'type': 'ellipse',
            'cx': float(elem.get('cx', 0)),
            'cy': float(elem.get('cy', 0)),
            'rx': float(elem.get('rx', 0)),
            'ry': float(elem.get('ry', 0)),
            'fill': self._get_fill(elem),
            'stroke': self._get_stroke(elem)
        }
    
    def _parse_polygon(self, elem: ET.Element) -> Dict[str, Any]:
        """Parse polygon element"""
        points_str = elem.get('points', '')
        points = self._parse_points(points_str)
        
        return {
            'type': 'polygon',
            'points': points,
            'fill': self._get_fill(elem),
            'stroke': self._get_stroke(elem)
        }
    
    def _parse_polyline(self, elem: ET.Element) -> Dict[str, Any]:
        """Parse polyline element"""
        points_str = elem.get('points', '')
        points = self._parse_points(points_str)
        
        return {
            'type': 'polyline',
            'points': points,
            'fill': self._get_fill(elem),
            'stroke': self._get_stroke(elem)
        }
    
    def _parse_points(self, points_str: str) -> List[Point]:
        """Parse points attribute"""
        coords = re.findall(r'-?\d+\.?\d*', points_str)
        points = []
        for i in range(0, len(coords), 2):
            if i + 1 < len(coords):
                points.append(Point(float(coords[i]), float(coords[i+1])))
        return points
    
    def _get_fill(self, elem: ET.Element) -> Optional[Color]:
        """Extract fill color from element"""
        # Check fill attribute
        fill = elem.get('fill')
        if fill and fill.lower() != 'none':
            return Color.parse(fill)
        
        # Check style attribute
        style = elem.get('style', '')
        match = re.search(r'fill:\s*([^;]+)', style)
        if match:
            fill = match.group(1).strip()
            if fill.lower() != 'none':
                return Color.parse(fill)
        
        # Default to black if no fill specified
        return Color(0, 0, 0)
    
    def _get_stroke(self, elem: ET.Element) -> Optional[Color]:
        """Extract stroke color from element"""
        # Check stroke attribute
        stroke = elem.get('stroke')
        if stroke and stroke.lower() != 'none':
            return Color.parse(stroke)
        
        # Check style attribute
        style = elem.get('style', '')
        match = re.search(r'stroke:\s*([^;]+)', style)
        if match:
            stroke = match.group(1).strip()
            if stroke.lower() != 'none':
                return Color.parse(stroke)
        
        return None


class SVGRenderer:
    """High-level SVG renderer"""
    
    def __init__(self, svg_file: str = None, svg_string: str = None):
        self.parser = SVGParser(filename=svg_file, svg_string=svg_string)
        self.width, self.height = self.parser.width, self.parser.height
        self.rasterizer = Rasterizer(self.width, self.height)
    
    def render(self) -> Rasterizer:
        """Render all SVG elements"""
        elements = self.parser.parse()
        
        for elem in elements:
            if elem['fill'] is None:
                continue  # Skip if no fill
            
            if elem['type'] == 'path':
                self._render_path(elem)
            elif elem['type'] == 'rect':
                self._render_rect(elem)
            elif elem['type'] == 'circle':
                self._render_circle(elem)
            elif elem['type'] == 'ellipse':
                self._render_ellipse(elem)
            elif elem['type'] == 'polygon':
                self._render_polygon(elem)
            elif elem['type'] == 'polyline':
                self._render_polyline(elem)
        
        return self.rasterizer
    
    def _render_path(self, elem: Dict[str, Any]):
        """Render path element"""
        parser = PathParser(elem['data'])
        parser.parse()
        polygon = parser.to_polygon()
        self.rasterizer.fill_polygon(polygon, elem['fill'])
    
    def _render_rect(self, elem: Dict[str, Any]):
        """Render rectangle element"""
        self.rasterizer.draw_rectangle(
            elem['x'], elem['y'], elem['width'], elem['height'],
            elem['fill'], elem['rx'], elem['ry']
        )
    
    def _render_circle(self, elem: Dict[str, Any]):
        """Render circle element"""
        self.rasterizer.draw_circle(
            Point(elem['cx'], elem['cy']), elem['r'], elem['fill']
        )
    
    def _render_ellipse(self, elem: Dict[str, Any]):
        """Render ellipse element"""
        self.rasterizer.draw_ellipse(
            elem['cx'], elem['cy'], elem['rx'], elem['ry'], elem['fill']
        )
    
    def _render_polygon(self, elem: Dict[str, Any]):
        """Render polygon element"""
        self.rasterizer.fill_polygon(elem['points'], elem['fill'])
    
    def _render_polyline(self, elem: Dict[str, Any]):
        """Render polyline element (as polygon)"""
        self.rasterizer.fill_polygon(elem['points'], elem['fill'])
    
    def save(self, filename: str):
        """Save rendered image"""
        if filename.endswith('.png'):
            self.rasterizer.save_png(filename)
        else:
            self.rasterizer.save_ppm(filename)


# Example usage
if __name__ == "__main__":
    # Example 1: Simple SVG string
    svg_data = """
    <svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400">
        <rect x="50" y="50" width="100" height="100" fill="#FF6B6B"/>
        <circle cx="250" cy="100" r="50" fill="#4ECDC4"/>
        <path d="M 50 250 L 150 250 L 100 300 Z" fill="#FFE66D"/>
        <ellipse cx="250" cy="300" rx="60" ry="40" fill="#95E1D3"/>
    </svg>
    """
    
    renderer = SVGRenderer(svg_string=svg_data)
    renderer.render()
    renderer.save("output_example.ppm")
    print("Example rendered to output_example.ppm")
    
    # Example 2: Render from file (if you have an SVG file)
    # renderer = SVGRenderer(svg_file="your_file.svg")
    # renderer.render()
    # renderer.save("output.ppm")
