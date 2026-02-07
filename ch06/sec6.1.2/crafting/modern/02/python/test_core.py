"""
Core Test Suite for SVG Renderer (No External Dependencies)
Basic unit and integration tests without property-based testing
"""

import unittest
import math
import tempfile
import os
import shutil
from pathlib import Path

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
    
    def test_parse_line_to_absolute(self):
        """Test absolute LineTo command"""
        parser = PathParser("M 10 20 L 30 40")
        commands = parser.parse()
        self.assertEqual(len(commands), 2)
        self.assertIsInstance(commands[1], LineTo)
        self.assertEqual(commands[1].point.x, 30)
        self.assertEqual(commands[1].point.y, 40)
    
    def test_parse_cubic_bezier(self):
        """Test cubic Bezier curve"""
        parser = PathParser("M 10 20 C 20 30 40 50 60 70")
        commands = parser.parse()
        self.assertEqual(len(commands), 2)
        self.assertIsInstance(commands[1], CubicBezier)
    
    def test_parse_close_path(self):
        """Test close path command"""
        parser = PathParser("M 10 20 L 30 40 Z")
        commands = parser.parse()
        self.assertEqual(len(commands), 3)
        self.assertIsInstance(commands[2], ClosePath)
    
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
    
    def test_draw_circle(self):
        """Test circle drawing"""
        rast = Rasterizer(100, 100)
        color = Color(255, 0, 0)
        rast.draw_circle(Point(50, 50), 10, color)
        # Check that canvas was modified
        self.assertIsNotNone(rast.canvas)
    
    def test_draw_rectangle(self):
        """Test rectangle drawing"""
        rast = Rasterizer(100, 100)
        color = Color(255, 0, 0)
        rast.draw_rectangle(10, 10, 20, 20, color)
        # Check a pixel inside the rectangle should be colored
        self.assertEqual(rast.canvas[15][15], color.to_tuple())
    
    def test_fill_polygon(self):
        """Test polygon filling"""
        rast = Rasterizer(100, 100)
        color = Color(255, 0, 0)
        triangle = [Point(10, 10), Point(50, 10), Point(30, 50)]
        rast.fill_polygon(triangle, color)
        # Verify canvas was modified
        self.assertIsNotNone(rast.canvas)
    
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


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestBasicIntegration(unittest.TestCase):
    """Basic integration tests"""
    
    def test_render_multiple_elements(self):
        """Test rendering multiple elements"""
        svg = '''<svg width="100" height="100">
                    <rect x="10" y="10" width="20" height="20" fill="red"/>
                    <circle cx="50" cy="50" r="15" fill="blue"/>
                 </svg>'''
        renderer = SVGRenderer(svg_string=svg)
        rasterizer = renderer.render()
        self.assertIsInstance(rasterizer, Rasterizer)
    
    def test_render_and_save(self):
        """Test full render and save pipeline"""
        svg = '''<svg width="50" height="50">
                    <rect x="10" y="10" width="20" height="20" fill="red"/>
                 </svg>'''
        renderer = SVGRenderer(svg_string=svg)
        renderer.render()
        
        with tempfile.NamedTemporaryFile(suffix='.ppm', delete=False) as f:
            temp_path = f.name
        try:
            renderer.save(temp_path)
            self.assertTrue(os.path.exists(temp_path))
            self.assertGreater(os.path.getsize(temp_path), 100)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


if __name__ == '__main__':
    unittest.main(verbosity=2)
