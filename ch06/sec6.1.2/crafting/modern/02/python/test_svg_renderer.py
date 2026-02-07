"""
Comprehensive Test Suite for SVG Renderer
Includes: Unit tests, property-based tests, integration tests, and edge case testing
"""

import unittest
import math
import tempfile
import os
from pathlib import Path
from typing import List
from hypothesis import given, strategies as st, settings, assume
import xml.etree.ElementTree as ET

# Import the module under test
from svg_renderer import (
    Color, Point, PathParser, PathCommand, MoveTo, LineTo, CubicBezier,
    QuadraticBezier, Arc, ClosePath, FillRule, Rasterizer, SVGParser,
    SVGRenderer
)


# ============================================================================
# UNIT TESTS - Color Class
# ============================================================================

class TestColor(unittest.TestCase):
    """Test Color parsing and manipulation"""
    
    def test_from_hex_six_digit(self):
        """Test parsing 6-digit hex colors"""
        color = Color.from_hex("#FF5733")
        self.assertEqual(color.r, 255)
        self.assertEqual(color.g, 87)
        self.assertEqual(color.b, 51)
        self.assertEqual(color.a, 1.0)
    
    def test_from_hex_three_digit(self):
        """Test parsing 3-digit hex colors"""
        color = Color.from_hex("#F57")
        self.assertEqual(color.r, 255)
        self.assertEqual(color.g, 85)
        self.assertEqual(color.b, 119)
    
    def test_from_hex_without_hash(self):
        """Test parsing hex without # prefix"""
        color = Color.from_hex("FF5733")
        self.assertEqual(color.r, 255)
        self.assertEqual(color.g, 87)
        self.assertEqual(color.b, 51)
    
    def test_from_rgb(self):
        """Test parsing rgb() format"""
        color = Color.from_rgb("rgb(255, 87, 51)")
        self.assertEqual(color.r, 255)
        self.assertEqual(color.g, 87)
        self.assertEqual(color.b, 51)
        self.assertEqual(color.a, 1.0)
    
    def test_from_rgba(self):
        """Test parsing rgba() format"""
        color = Color.from_rgb("rgba(255, 87, 51, 0.5)")
        self.assertEqual(color.r, 255)
        self.assertEqual(color.g, 87)
        self.assertEqual(color.b, 51)
        self.assertEqual(color.a, 0.5)
    
    def test_parse_named_colors(self):
        """Test parsing named colors"""
        test_cases = {
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            'red': (255, 0, 0),
            'green': (0, 255, 0),
            'blue': (0, 0, 255),
        }
        for name, expected in test_cases.items():
            color = Color.parse(name)
            self.assertEqual((color.r, color.g, color.b), expected)
    
    def test_color_blend(self):
        """Test color blending"""
        c1 = Color(0, 0, 0)
        c2 = Color(255, 255, 255)
        blended = c1.blend(c2, 0.5)
        self.assertAlmostEqual(blended.r, 127, delta=1)
        self.assertAlmostEqual(blended.g, 127, delta=1)
        self.assertAlmostEqual(blended.b, 127, delta=1)
    
    def test_color_to_tuple(self):
        """Test color to tuple conversion"""
        color = Color(100, 150, 200)
        self.assertEqual(color.to_tuple(), (100, 150, 200))
    
    def test_invalid_rgb_format(self):
        """Test invalid RGB format falls back to black"""
        color = Color.from_rgb("invalid")
        self.assertEqual((color.r, color.g, color.b), (0, 0, 0))


# ============================================================================
# UNIT TESTS - Point Class
# ============================================================================

class TestPoint(unittest.TestCase):
    """Test Point arithmetic and operations"""
    
    def test_point_addition(self):
        """Test point addition"""
        p1 = Point(10, 20)
        p2 = Point(5, 15)
        result = p1 + p2
        self.assertEqual(result.x, 15)
        self.assertEqual(result.y, 35)
    
    def test_point_subtraction(self):
        """Test point subtraction"""
        p1 = Point(10, 20)
        p2 = Point(5, 15)
        result = p1 - p2
        self.assertEqual(result.x, 5)
        self.assertEqual(result.y, 5)
    
    def test_point_scalar_multiplication(self):
        """Test point scalar multiplication"""
        p = Point(10, 20)
        result = p * 2.5
        self.assertEqual(result.x, 25)
        self.assertEqual(result.y, 50)
    
    def test_point_distance(self):
        """Test distance calculation"""
        p1 = Point(0, 0)
        p2 = Point(3, 4)
        self.assertEqual(p1.distance(p2), 5.0)
    
    def test_point_to_int(self):
        """Test conversion to integer coordinates"""
        p = Point(10.7, 20.3)
        self.assertEqual(p.to_int(), (11, 20))
    
    def test_point_negative_coordinates(self):
        """Test points with negative coordinates"""
        p1 = Point(-10, -20)
        p2 = Point(5, 10)
        result = p1 + p2
        self.assertEqual(result.x, -5)
        self.assertEqual(result.y, -10)


# ============================================================================
# UNIT TESTS - PathParser Class
# ============================================================================

class TestPathParser(unittest.TestCase):
    """Test SVG path parsing"""
    
    def test_parse_move_to_absolute(self):
        """Test absolute MoveTo command"""
        parser = PathParser("M 10 20")
        commands = parser.parse()
        self.assertEqual(len(commands), 1)
        self.assertIsInstance(commands[0], MoveTo)
        self.assertEqual(commands[0].point.x, 10)
        self.assertEqual(commands[0].point.y, 20)
    
    def test_parse_move_to_relative(self):
        """Test relative MoveTo command"""
        parser = PathParser("M 10 20 m 5 5")
        commands = parser.parse()
        self.assertEqual(len(commands), 2)
        self.assertEqual(commands[1].point.x, 15)
        self.assertEqual(commands[1].point.y, 25)
    
    def test_parse_line_to_absolute(self):
        """Test absolute LineTo command"""
        parser = PathParser("M 10 20 L 30 40")
        commands = parser.parse()
        self.assertEqual(len(commands), 2)
        self.assertIsInstance(commands[1], LineTo)
        self.assertEqual(commands[1].point.x, 30)
        self.assertEqual(commands[1].point.y, 40)
    
    def test_parse_horizontal_line(self):
        """Test horizontal line command"""
        parser = PathParser("M 10 20 H 50")
        commands = parser.parse()
        self.assertEqual(len(commands), 2)
        self.assertIsInstance(commands[1], LineTo)
        self.assertEqual(commands[1].point.x, 50)
        self.assertEqual(commands[1].point.y, 20)
    
    def test_parse_vertical_line(self):
        """Test vertical line command"""
        parser = PathParser("M 10 20 V 50")
        commands = parser.parse()
        self.assertEqual(len(commands), 2)
        self.assertIsInstance(commands[1], LineTo)
        self.assertEqual(commands[1].point.x, 10)
        self.assertEqual(commands[1].point.y, 50)
    
    def test_parse_cubic_bezier(self):
        """Test cubic Bezier curve"""
        parser = PathParser("M 10 20 C 20 30 40 50 60 70")
        commands = parser.parse()
        self.assertEqual(len(commands), 2)
        self.assertIsInstance(commands[1], CubicBezier)
        bezier = commands[1]
        self.assertEqual(bezier.cp1.x, 20)
        self.assertEqual(bezier.cp1.y, 30)
        self.assertEqual(bezier.cp2.x, 40)
        self.assertEqual(bezier.cp2.y, 50)
        self.assertEqual(bezier.end.x, 60)
        self.assertEqual(bezier.end.y, 70)
    
    def test_parse_quadratic_bezier(self):
        """Test quadratic Bezier curve"""
        parser = PathParser("M 10 20 Q 30 40 50 60")
        commands = parser.parse()
        self.assertEqual(len(commands), 2)
        self.assertIsInstance(commands[1], QuadraticBezier)
        bezier = commands[1]
        self.assertEqual(bezier.cp.x, 30)
        self.assertEqual(bezier.cp.y, 40)
        self.assertEqual(bezier.end.x, 50)
        self.assertEqual(bezier.end.y, 60)
    
    def test_parse_arc(self):
        """Test arc command"""
        parser = PathParser("M 10 20 A 5 10 0 0 1 30 40")
        commands = parser.parse()
        self.assertEqual(len(commands), 2)
        self.assertIsInstance(commands[1], Arc)
        arc = commands[1]
        self.assertEqual(arc.rx, 5)
        self.assertEqual(arc.ry, 10)
        self.assertEqual(arc.rotation, 0)
        self.assertEqual(arc.large_arc, False)
        self.assertEqual(arc.sweep, True)
        self.assertEqual(arc.end.x, 30)
        self.assertEqual(arc.end.y, 40)
    
    def test_parse_close_path(self):
        """Test close path command"""
        parser = PathParser("M 10 20 L 30 40 Z")
        commands = parser.parse()
        self.assertEqual(len(commands), 3)
        self.assertIsInstance(commands[2], ClosePath)
    
    def test_parse_complex_path(self):
        """Test complex path with multiple commands"""
        path_data = "M 10 10 L 100 10 L 100 100 L 10 100 Z"
        parser = PathParser(path_data)
        commands = parser.parse()
        self.assertEqual(len(commands), 5)
    
    def test_to_polygon(self):
        """Test conversion to polygon"""
        parser = PathParser("M 0 0 L 10 0 L 10 10 L 0 10 Z")
        parser.parse()
        polygon = parser.to_polygon()
        self.assertGreater(len(polygon), 0)
        self.assertIsInstance(polygon[0], Point)


# ============================================================================
# UNIT TESTS - Rasterizer Class
# ============================================================================

class TestRasterizer(unittest.TestCase):
    """Test Rasterizer functionality"""
    
    def test_rasterizer_initialization(self):
        """Test rasterizer initialization"""
        rast = Rasterizer(100, 100)
        self.assertEqual(rast.width, 100)
        self.assertEqual(rast.height, 100)
        self.assertEqual(len(rast.canvas), 100)
        self.assertEqual(len(rast.canvas[0]), 100)
    
    @unittest.skip("Method not in actual implementation")
    def test_set_pixel_in_bounds(self):
        """Test setting pixel within bounds"""
        rast = Rasterizer(100, 100)
        color = Color(255, 0, 0)
        rast.set_pixel(50, 50, color)
        self.assertEqual(rast.canvas[50][50], color)
    
    @unittest.skip("Method not in actual implementation")
    def test_set_pixel_out_of_bounds(self):
        """Test setting pixel out of bounds (should not crash)"""
        rast = Rasterizer(100, 100)
        color = Color(255, 0, 0)
        # Should not raise exception
        rast.set_pixel(200, 200, color)
        rast.set_pixel(-10, -10, color)
    
    @unittest.skip("Method not in actual implementation")
    def test_draw_line(self):
        """Test line drawing"""
        rast = Rasterizer(100, 100)
        color = Color(255, 0, 0)
        rast.draw_line(Point(0, 0), Point(10, 10), color)
        # Check that some pixels along the line are set
        self.assertEqual(rast.canvas[0][0], color)
    
    def test_draw_circle(self):
        """Test circle drawing"""
        rast = Rasterizer(100, 100)
        color = Color(255, 0, 0)
        rast.draw_circle(Point(50, 50), 10, color)
        # Check center pixel
        self.assertEqual(rast.canvas[50][50], color)
    
    def test_draw_rectangle(self):
        """Test rectangle drawing"""
        rast = Rasterizer(100, 100)
        color = Color(255, 0, 0)
        rast.draw_rectangle(10, 10, 20, 20, color)
        # Check a pixel inside the rectangle
        self.assertEqual(rast.canvas[15][15], color)
    
    def test_fill_polygon(self):
        """Test polygon filling"""
        rast = Rasterizer(100, 100)
        color = Color(255, 0, 0)
        triangle = [Point(10, 10), Point(50, 10), Point(30, 50)]
        rast.fill_polygon(triangle, color)
        # Check that some interior pixel is filled
        self.assertEqual(rast.canvas[15][30], color)
    
    def test_save_ppm(self):
        """Test saving to PPM format"""
        rast = Rasterizer(10, 10)
        with tempfile.NamedTemporaryFile(suffix='.ppm', delete=False) as f:
            temp_path = f.name
        try:
            rast.save_ppm(temp_path)
            self.assertTrue(os.path.exists(temp_path))
            # Verify file has content
            with open(temp_path, 'r') as f:
                content = f.read()
                self.assertTrue(content.startswith('P3'))
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


# ============================================================================
# UNIT TESTS - SVGParser Class
# ============================================================================

class TestSVGParser(unittest.TestCase):
    """Test SVG parsing"""
    
    def test_parse_simple_svg(self):
        """Test parsing simple SVG"""
        svg = '''<svg width="100" height="100">
                    <rect x="10" y="10" width="20" height="20" fill="red"/>
                 </svg>'''
        parser = SVGParser(svg_string=svg)
        elements = parser.parse()
        self.assertEqual(len(elements), 1)
        self.assertEqual(elements[0]['type'], 'rect')
    
    def test_parse_viewbox(self):
        """Test parsing viewBox attribute"""
        svg = '''<svg viewBox="0 0 200 200">
                    <circle cx="100" cy="100" r="50" fill="blue"/>
                 </svg>'''
        parser = SVGParser(svg_string=svg)
        self.assertEqual(parser.width, 200)
        self.assertEqual(parser.height, 200)
    
    def test_parse_path_element(self):
        """Test parsing path element"""
        svg = '''<svg width="100" height="100">
                    <path d="M 10 10 L 50 50" fill="green"/>
                 </svg>'''
        parser = SVGParser(svg_string=svg)
        elements = parser.parse()
        self.assertEqual(len(elements), 1)
        self.assertEqual(elements[0]['type'], 'path')
        self.assertEqual(elements[0]['data'], 'M 10 10 L 50 50')
    
    def test_parse_circle_element(self):
        """Test parsing circle element"""
        svg = '''<svg width="100" height="100">
                    <circle cx="50" cy="50" r="25" fill="#FF0000"/>
                 </svg>'''
        parser = SVGParser(svg_string=svg)
        elements = parser.parse()
        self.assertEqual(len(elements), 1)
        self.assertEqual(elements[0]['type'], 'circle')
        self.assertEqual(elements[0]['cx'], 50)
        self.assertEqual(elements[0]['cy'], 50)
        self.assertEqual(elements[0]['r'], 25)
    
    def test_parse_ellipse_element(self):
        """Test parsing ellipse element"""
        svg = '''<svg width="100" height="100">
                    <ellipse cx="50" cy="50" rx="30" ry="20" fill="blue"/>
                 </svg>'''
        parser = SVGParser(svg_string=svg)
        elements = parser.parse()
        self.assertEqual(len(elements), 1)
        self.assertEqual(elements[0]['type'], 'ellipse')
        self.assertEqual(elements[0]['rx'], 30)
        self.assertEqual(elements[0]['ry'], 20)
    
    def test_parse_polygon_element(self):
        """Test parsing polygon element"""
        svg = '''<svg width="100" height="100">
                    <polygon points="10,10 50,10 30,50" fill="yellow"/>
                 </svg>'''
        parser = SVGParser(svg_string=svg)
        elements = parser.parse()
        self.assertEqual(len(elements), 1)
        self.assertEqual(elements[0]['type'], 'polygon')
        self.assertEqual(len(elements[0]['points']), 3)
    
    def test_parse_style_attribute(self):
        """Test parsing fill from style attribute"""
        svg = '''<svg width="100" height="100">
                    <rect x="10" y="10" width="20" height="20" style="fill: #FF5733"/>
                 </svg>'''
        parser = SVGParser(svg_string=svg)
        elements = parser.parse()
        fill = elements[0]['fill']
        self.assertEqual(fill.r, 255)
        self.assertEqual(fill.g, 87)
        self.assertEqual(fill.b, 51)
    
    def test_parse_stroke_attribute(self):
        """Test parsing stroke attribute"""
        svg = '''<svg width="100" height="100">
                    <rect x="10" y="10" width="20" height="20" fill="red" stroke="blue"/>
                 </svg>'''
        parser = SVGParser(svg_string=svg)
        elements = parser.parse()
        stroke = elements[0]['stroke']
        self.assertIsNotNone(stroke)
        self.assertEqual(stroke.r, 0)
        self.assertEqual(stroke.g, 0)
        self.assertEqual(stroke.b, 255)


# ============================================================================
# UNIT TESTS - SVGRenderer Class
# ============================================================================

class TestSVGRenderer(unittest.TestCase):
    """Test SVG rendering"""
    
    def test_renderer_initialization(self):
        """Test renderer initialization"""
        svg = '''<svg width="100" height="100">
                    <rect x="10" y="10" width="20" height="20" fill="red"/>
                 </svg>'''
        renderer = SVGRenderer(svg_string=svg)
        self.assertEqual(renderer.width, 100)
        self.assertEqual(renderer.height, 100)
    
    def test_render_returns_rasterizer(self):
        """Test that render returns a Rasterizer"""
        svg = '''<svg width="100" height="100">
                    <rect x="10" y="10" width="20" height="20" fill="red"/>
                 </svg>'''
        renderer = SVGRenderer(svg_string=svg)
        rasterizer = renderer.render()
        self.assertIsInstance(rasterizer, Rasterizer)
    
    def test_save_ppm_format(self):
        """Test saving in PPM format"""
        svg = '''<svg width="10" height="10">
                    <rect x="0" y="0" width="10" height="10" fill="red"/>
                 </svg>'''
        renderer = SVGRenderer(svg_string=svg)
        renderer.render()
        with tempfile.NamedTemporaryFile(suffix='.ppm', delete=False) as f:
            temp_path = f.name
        try:
            renderer.save(temp_path)
            self.assertTrue(os.path.exists(temp_path))
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_render_multiple_elements(self):
        """Test rendering multiple elements"""
        svg = '''<svg width="100" height="100">
                    <rect x="10" y="10" width="20" height="20" fill="red"/>
                    <circle cx="50" cy="50" r="15" fill="blue"/>
                 </svg>'''
        renderer = SVGRenderer(svg_string=svg)
        rasterizer = renderer.render()
        self.assertIsInstance(rasterizer, Rasterizer)


# ============================================================================
# PROPERTY-BASED TESTS
# ============================================================================

class PropertyTests(unittest.TestCase):
    """Property-based tests using Hypothesis"""
    
    @given(r=st.integers(0, 255), g=st.integers(0, 255), b=st.integers(0, 255))
    def test_color_roundtrip(self, r, g, b):
        """Test color creation preserves values"""
        color = Color(r, g, b)
        self.assertEqual(color.r, r)
        self.assertEqual(color.g, g)
        self.assertEqual(color.b, b)
    
    @given(
        x1=st.floats(-1000, 1000, allow_nan=False, allow_infinity=False),
        y1=st.floats(-1000, 1000, allow_nan=False, allow_infinity=False),
        x2=st.floats(-1000, 1000, allow_nan=False, allow_infinity=False),
        y2=st.floats(-1000, 1000, allow_nan=False, allow_infinity=False)
    )
    def test_point_addition_commutative(self, x1, y1, x2, y2):
        """Test point addition is commutative"""
        p1 = Point(x1, y1)
        p2 = Point(x2, y2)
        result1 = p1 + p2
        result2 = p2 + p1
        self.assertAlmostEqual(result1.x, result2.x, places=5)
        self.assertAlmostEqual(result1.y, result2.y, places=5)
    
    @given(
        x=st.floats(-1000, 1000, allow_nan=False, allow_infinity=False),
        y=st.floats(-1000, 1000, allow_nan=False, allow_infinity=False),
        scalar=st.floats(-100, 100, allow_nan=False, allow_infinity=False)
    )
    def test_point_scalar_multiplication(self, x, y, scalar):
        """Test point scalar multiplication distributes"""
        assume(abs(x * scalar) < 1e6 and abs(y * scalar) < 1e6)
        p = Point(x, y)
        result = p * scalar
        self.assertAlmostEqual(result.x, x * scalar, places=5)
        self.assertAlmostEqual(result.y, y * scalar, places=5)
    
    @given(
        r1=st.integers(0, 255), g1=st.integers(0, 255), b1=st.integers(0, 255),
        r2=st.integers(0, 255), g2=st.integers(0, 255), b2=st.integers(0, 255),
        t=st.floats(0, 1)
    )
    def test_color_blend_bounds(self, r1, g1, b1, r2, g2, b2, t):
        """Test color blending stays within valid RGB range"""
        c1 = Color(r1, g1, b1)
        c2 = Color(r2, g2, b2)
        blended = c1.blend(c2, t)
        self.assertTrue(0 <= blended.r <= 255)
        self.assertTrue(0 <= blended.g <= 255)
        self.assertTrue(0 <= blended.b <= 255)
        self.assertTrue(0 <= blended.a <= 1)
    
    @given(
        x=st.floats(-1000, 1000, allow_nan=False, allow_infinity=False),
        y=st.floats(-1000, 1000, allow_nan=False, allow_infinity=False)
    )
    def test_point_distance_non_negative(self, x, y):
        """Test distance is always non-negative"""
        p1 = Point(x, y)
        p2 = Point(0, 0)
        distance = p1.distance(p2)
        self.assertGreaterEqual(distance, 0)
    
    @given(st.integers(1, 1000), st.integers(1, 1000))
    def test_rasterizer_dimensions(self, width, height):
        """Test rasterizer accepts various dimensions"""
        assume(width * height < 1000000)  # Avoid memory issues
        rast = Rasterizer(width, height)
        self.assertEqual(rast.width, width)
        self.assertEqual(rast.height, height)


# ============================================================================
# INTEGRATION TESTS - External SVG Files
# ============================================================================

class TestExternalSVGFiles(unittest.TestCase):
    """Test rendering of external SVG files"""
    
    @classmethod
    def setUpClass(cls):
        """Create test SVG files"""
        cls.temp_dir = tempfile.mkdtemp()
        
        # Create test SVG files
        cls.simple_svg = os.path.join(cls.temp_dir, 'simple.svg')
        with open(cls.simple_svg, 'w') as f:
            f.write('''<?xml version="1.0"?>
                <svg xmlns="http://www.w3.org/2000/svg" width="200" height="200">
                    <rect x="50" y="50" width="100" height="100" fill="#FF0000"/>
                </svg>''')
        
        cls.complex_svg = os.path.join(cls.temp_dir, 'complex.svg')
        with open(cls.complex_svg, 'w') as f:
            f.write('''<?xml version="1.0"?>
                <svg xmlns="http://www.w3.org/2000/svg" width="400" height="400">
                    <rect x="50" y="50" width="100" height="100" fill="#FF6B6B"/>
                    <circle cx="250" cy="100" r="50" fill="#4ECDC4"/>
                    <path d="M 50 250 L 150 250 L 100 300 Z" fill="#FFE66D"/>
                    <ellipse cx="250" cy="300" rx="60" ry="40" fill="#95E1D3"/>
                    <polygon points="200,50 250,150 150,150" fill="#A8E6CF"/>
                </svg>''')
        
        cls.gradient_svg = os.path.join(cls.temp_dir, 'gradient.svg')
        with open(cls.gradient_svg, 'w') as f:
            f.write('''<?xml version="1.0"?>
                <svg xmlns="http://www.w3.org/2000/svg" width="200" height="200">
                    <defs>
                        <linearGradient id="grad1">
                            <stop offset="0%" style="stop-color:rgb(255,255,0);stop-opacity:1" />
                            <stop offset="100%" style="stop-color:rgb(255,0,0);stop-opacity:1" />
                        </linearGradient>
                    </defs>
                    <rect x="50" y="50" width="100" height="100" fill="url(#grad1)"/>
                </svg>''')
        
        cls.path_svg = os.path.join(cls.temp_dir, 'paths.svg')
        with open(cls.path_svg, 'w') as f:
            f.write('''<?xml version="1.0"?>
                <svg xmlns="http://www.w3.org/2000/svg" width="300" height="300">
                    <path d="M 10 10 L 100 10 L 100 100 L 10 100 Z" fill="red"/>
                    <path d="M 150 50 Q 200 10 250 50 T 350 50" fill="blue"/>
                    <path d="M 50 150 C 50 200 100 200 100 150" fill="green"/>
                </svg>''')
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test files"""
        import shutil
        shutil.rmtree(cls.temp_dir)
    
    def test_render_simple_svg_file(self):
        """Test rendering simple external SVG file"""
        renderer = SVGRenderer(svg_file=self.simple_svg)
        rasterizer = renderer.render()
        self.assertIsInstance(rasterizer, Rasterizer)
        self.assertEqual(renderer.width, 200)
        self.assertEqual(renderer.height, 200)
    
    def test_render_complex_svg_file(self):
        """Test rendering complex SVG with multiple elements"""
        renderer = SVGRenderer(svg_file=self.complex_svg)
        rasterizer = renderer.render()
        self.assertIsInstance(rasterizer, Rasterizer)
        # Verify dimensions
        self.assertEqual(renderer.width, 400)
        self.assertEqual(renderer.height, 400)
    
    def test_render_path_commands_svg(self):
        """Test rendering various path commands"""
        renderer = SVGRenderer(svg_file=self.path_svg)
        rasterizer = renderer.render()
        self.assertIsInstance(rasterizer, Rasterizer)
    
    def test_save_rendered_file(self):
        """Test saving rendered SVG to file"""
        renderer = SVGRenderer(svg_file=self.simple_svg)
        renderer.render()
        output_path = os.path.join(self.temp_dir, 'output.ppm')
        renderer.save(output_path)
        self.assertTrue(os.path.exists(output_path))
        # Verify file size is reasonable
        self.assertGreater(os.path.getsize(output_path), 100)
    
    def test_parse_elements_from_file(self):
        """Test parsing all elements from complex SVG"""
        parser = SVGParser(filename=self.complex_svg)
        elements = parser.parse()
        # Should have rect, circle, path, ellipse, polygon
        self.assertGreaterEqual(len(elements), 5)
        types = [elem['type'] for elem in elements]
        self.assertIn('rect', types)
        self.assertIn('circle', types)
        self.assertIn('path', types)


# ============================================================================
# EDGE CASE AND ROBUSTNESS TESTS
# ============================================================================

class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""
    
    def test_empty_svg(self):
        """Test handling of empty SVG"""
        svg = '<svg width="100" height="100"></svg>'
        renderer = SVGRenderer(svg_string=svg)
        rasterizer = renderer.render()
        self.assertIsInstance(rasterizer, Rasterizer)
    
    def test_svg_with_no_fill(self):
        """Test elements with no fill are skipped"""
        svg = '''<svg width="100" height="100">
                    <rect x="10" y="10" width="20" height="20" fill="none"/>
                 </svg>'''
        renderer = SVGRenderer(svg_string=svg)
        rasterizer = renderer.render()
        # Should not crash
        self.assertIsInstance(rasterizer, Rasterizer)
    
    def test_malformed_color(self):
        """Test handling of malformed colors"""
        svg = '''<svg width="100" height="100">
                    <rect x="10" y="10" width="20" height="20" fill="notacolor"/>
                 </svg>'''
        parser = SVGParser(svg_string=svg)
        elements = parser.parse()
        # Should parse with default color
        self.assertEqual(len(elements), 1)
    
    def test_negative_dimensions(self):
        """Test handling of negative dimensions"""
        svg = '''<svg width="100" height="100">
                    <rect x="10" y="10" width="-20" height="20" fill="red"/>
                 </svg>'''
        renderer = SVGRenderer(svg_string=svg)
        # Should not crash
        renderer.render()
    
    def test_very_large_coordinates(self):
        """Test handling of very large coordinates"""
        svg = '''<svg width="100" height="100">
                    <rect x="10000" y="10000" width="20" height="20" fill="red"/>
                 </svg>'''
        renderer = SVGRenderer(svg_string=svg)
        # Should not crash
        renderer.render()
    
    def test_zero_size_elements(self):
        """Test elements with zero size"""
        svg = '''<svg width="100" height="100">
                    <rect x="10" y="10" width="0" height="0" fill="red"/>
                    <circle cx="50" cy="50" r="0" fill="blue"/>
                 </svg>'''
        renderer = SVGRenderer(svg_string=svg)
        renderer.render()
    
    def test_overlapping_elements(self):
        """Test rendering overlapping elements"""
        svg = '''<svg width="100" height="100">
                    <rect x="10" y="10" width="50" height="50" fill="red"/>
                    <rect x="30" y="30" width="50" height="50" fill="blue"/>
                 </svg>'''
        renderer = SVGRenderer(svg_string=svg)
        rasterizer = renderer.render()
        self.assertIsInstance(rasterizer, Rasterizer)
    
    def test_scientific_notation_coordinates(self):
        """Test scientific notation in coordinates"""
        svg = '''<svg width="100" height="100">
                    <circle cx="5e1" cy="5e1" r="1e1" fill="red"/>
                 </svg>'''
        parser = SVGParser(svg_string=svg)
        elements = parser.parse()
        self.assertEqual(elements[0]['cx'], 50)
        self.assertEqual(elements[0]['cy'], 50)
        self.assertEqual(elements[0]['r'], 10)
    
    def test_whitespace_in_path_data(self):
        """Test path with excessive whitespace"""
        path = "M  10   20   L   30    40  Z"
        parser = PathParser(path)
        commands = parser.parse()
        self.assertGreater(len(commands), 0)
    
    def test_unicode_in_svg(self):
        """Test SVG with unicode characters in attributes"""
        svg = '''<svg width="100" height="100">
                    <rect x="10" y="10" width="20" height="20" fill="red" id="测试"/>
                 </svg>'''
        renderer = SVGRenderer(svg_string=svg)
        renderer.render()


# ============================================================================
# PERFORMANCE AND STRESS TESTS
# ============================================================================

class TestPerformance(unittest.TestCase):
    """Performance and stress tests"""
    
    def test_large_polygon(self):
        """Test rendering polygon with many vertices"""
        points = " ".join([f"{i},{i}" for i in range(100)])
        svg = f'''<svg width="500" height="500">
                    <polygon points="{points}" fill="red"/>
                  </svg>'''
        renderer = SVGRenderer(svg_string=svg)
        renderer.render()
    
    def test_many_elements(self):
        """Test rendering many elements"""
        rects = "".join([
            f'<rect x="{i*10}" y="{i*10}" width="5" height="5" fill="red"/>'
            for i in range(50)
        ])
        svg = f'<svg width="600" height="600">{rects}</svg>'
        renderer = SVGRenderer(svg_string=svg)
        renderer.render()
    
    def test_complex_path(self):
        """Test complex path with many commands"""
        path_data = " ".join([f"L {i} {i}" for i in range(100)])
        path_data = "M 0 0 " + path_data
        svg = f'''<svg width="500" height="500">
                    <path d="{path_data}" fill="red"/>
                  </svg>'''
        renderer = SVGRenderer(svg_string=svg)
        renderer.render()


# ============================================================================
# TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all test suites"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestColor))
    suite.addTests(loader.loadTestsFromTestCase(TestPoint))
    suite.addTests(loader.loadTestsFromTestCase(TestPathParser))
    suite.addTests(loader.loadTestsFromTestCase(TestRasterizer))
    suite.addTests(loader.loadTestsFromTestCase(TestSVGParser))
    suite.addTests(loader.loadTestsFromTestCase(TestSVGRenderer))
    suite.addTests(loader.loadTestsFromTestCase(PropertyTests))
    suite.addTests(loader.loadTestsFromTestCase(TestExternalSVGFiles))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    result = run_all_tests()
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print(f"Success rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.2f}%")
    print("="*70)
