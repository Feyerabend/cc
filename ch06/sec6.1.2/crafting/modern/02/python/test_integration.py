"""
Integration Tests for External SVG Files
Tests rendering of real SVG files with detailed validation
"""

import unittest
import os
import tempfile
import shutil
from pathlib import Path

from svg_renderer import SVGRenderer, SVGParser, Color, Rasterizer
from create_fixtures import create_test_fixtures


class TestExternalSVGRendering(unittest.TestCase):
    """Integration tests using external SVG files"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.fixture_dir = tempfile.mkdtemp(prefix='svg_test_fixtures_')
        create_test_fixtures(cls.fixture_dir)
        cls.output_dir = tempfile.mkdtemp(prefix='svg_test_output_')
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test fixtures"""
        shutil.rmtree(cls.fixture_dir, ignore_errors=True)
        shutil.rmtree(cls.output_dir, ignore_errors=True)
    
    def _get_fixture_path(self, filename):
        """Get path to a test fixture"""
        return os.path.join(self.fixture_dir, filename)
    
    def _get_output_path(self, filename):
        """Get path for output file"""
        return os.path.join(self.output_dir, filename)
    
    # ========================================================================
    # BASIC RENDERING TESTS
    # ========================================================================
    
    def test_render_simple_shapes(self):
        """Test rendering simple shapes SVG"""
        svg_path = self._get_fixture_path('simple_shapes.svg')
        renderer = SVGRenderer(svg_file=svg_path)
        rasterizer = renderer.render()
        
        self.assertIsInstance(rasterizer, Rasterizer)
        self.assertEqual(renderer.width, 400)
        self.assertEqual(renderer.height, 400)
        
        # Save output
        output_path = self._get_output_path('simple_shapes.ppm')
        renderer.save(output_path)
        self.assertTrue(os.path.exists(output_path))
    
    def test_render_complex_paths(self):
        """Test rendering complex path commands"""
        svg_path = self._get_fixture_path('complex_paths.svg')
        renderer = SVGRenderer(svg_file=svg_path)
        rasterizer = renderer.render()
        
        self.assertIsInstance(rasterizer, Rasterizer)
        self.assertEqual(renderer.width, 500)
        self.assertEqual(renderer.height, 500)
    
    def test_render_many_elements(self):
        """Test rendering SVG with many elements (stress test)"""
        svg_path = self._get_fixture_path('many_elements.svg')
        renderer = SVGRenderer(svg_file=svg_path)
        rasterizer = renderer.render()
        
        self.assertIsInstance(rasterizer, Rasterizer)
        self.assertEqual(renderer.width, 600)
        self.assertEqual(renderer.height, 600)
    
    def test_render_edge_cases(self):
        """Test rendering edge case SVG"""
        svg_path = self._get_fixture_path('edge_cases.svg')
        renderer = SVGRenderer(svg_file=svg_path)
        # Should not crash
        rasterizer = renderer.render()
        self.assertIsInstance(rasterizer, Rasterizer)
    
    def test_render_color_formats(self):
        """Test rendering various color formats"""
        svg_path = self._get_fixture_path('color_formats.svg')
        renderer = SVGRenderer(svg_file=svg_path)
        rasterizer = renderer.render()
        
        self.assertIsInstance(rasterizer, Rasterizer)
    
    def test_render_icon_example(self):
        """Test rendering real-world icon"""
        svg_path = self._get_fixture_path('icon_example.svg')
        renderer = SVGRenderer(svg_file=svg_path)
        rasterizer = renderer.render()
        
        self.assertIsInstance(rasterizer, Rasterizer)
        self.assertEqual(renderer.width, 100)
        self.assertEqual(renderer.height, 100)
    
    def test_render_polyline(self):
        """Test rendering polylines"""
        svg_path = self._get_fixture_path('polyline_test.svg')
        renderer = SVGRenderer(svg_file=svg_path)
        rasterizer = renderer.render()
        
        self.assertIsInstance(rasterizer, Rasterizer)
    
    def test_render_scientific_notation(self):
        """Test rendering coordinates in scientific notation"""
        svg_path = self._get_fixture_path('scientific_notation.svg')
        renderer = SVGRenderer(svg_file=svg_path)
        rasterizer = renderer.render()
        
        self.assertIsInstance(rasterizer, Rasterizer)
    
    def test_render_whitespace_handling(self):
        """Test rendering with excessive whitespace"""
        svg_path = self._get_fixture_path('whitespace_test.svg')
        renderer = SVGRenderer(svg_file=svg_path)
        rasterizer = renderer.render()
        
        self.assertIsInstance(rasterizer, Rasterizer)
    
    def test_render_rounded_rectangles(self):
        """Test rendering rounded rectangles"""
        svg_path = self._get_fixture_path('rounded_rects.svg')
        renderer = SVGRenderer(svg_file=svg_path)
        rasterizer = renderer.render()
        
        self.assertIsInstance(rasterizer, Rasterizer)
    
    # ========================================================================
    # PARSING VALIDATION TESTS
    # ========================================================================
    
    def test_parse_simple_shapes_elements(self):
        """Test parsing returns correct element types"""
        svg_path = self._get_fixture_path('simple_shapes.svg')
        parser = SVGParser(filename=svg_path)
        elements = parser.parse()
        
        # Should have rect, circle, ellipse, polygon
        self.assertGreaterEqual(len(elements), 4)
        types = [elem['type'] for elem in elements]
        self.assertIn('rect', types)
        self.assertIn('circle', types)
        self.assertIn('ellipse', types)
        self.assertIn('polygon', types)
    
    def test_parse_complex_paths_count(self):
        """Test parsing complex paths returns multiple paths"""
        svg_path = self._get_fixture_path('complex_paths.svg')
        parser = SVGParser(filename=svg_path)
        elements = parser.parse()
        
        path_elements = [e for e in elements if e['type'] == 'path']
        self.assertGreaterEqual(len(path_elements), 3)
    
    def test_parse_color_formats_variety(self):
        """Test parsing different color formats"""
        svg_path = self._get_fixture_path('color_formats.svg')
        parser = SVGParser(filename=svg_path)
        elements = parser.parse()
        
        # All should have valid fills
        fills = [elem.get('fill') for elem in elements]
        valid_fills = [f for f in fills if f is not None]
        self.assertGreater(len(valid_fills), 0)
        
        # Check that colors are Color objects
        for fill in valid_fills:
            if isinstance(fill, Color):
                self.assertTrue(0 <= fill.r <= 255)
                self.assertTrue(0 <= fill.g <= 255)
                self.assertTrue(0 <= fill.b <= 255)
    
    # ========================================================================
    # OUTPUT FILE VALIDATION TESTS
    # ========================================================================
    
    def test_output_ppm_format(self):
        """Test PPM output file format"""
        svg_path = self._get_fixture_path('simple_shapes.svg')
        renderer = SVGRenderer(svg_file=svg_path)
        renderer.render()
        
        output_path = self._get_output_path('format_test.ppm')
        renderer.save(output_path)
        
        # Read and validate PPM header
        with open(output_path, 'r') as f:
            lines = f.readlines()
            self.assertEqual(lines[0].strip(), 'P3')
            # Second line should be dimensions
            width, height = map(int, lines[1].split())
            self.assertEqual(width, 400)
            self.assertEqual(height, 400)
            # Third line should be max color value
            self.assertEqual(lines[2].strip(), '255')
    
    def test_output_file_size_reasonable(self):
        """Test output file size is reasonable"""
        svg_path = self._get_fixture_path('icon_example.svg')
        renderer = SVGRenderer(svg_file=svg_path)
        renderer.render()
        
        output_path = self._get_output_path('size_test.ppm')
        renderer.save(output_path)
        
        file_size = os.path.getsize(output_path)
        # 100x100 image should produce file > 10KB
        self.assertGreater(file_size, 10000)
    
    # ========================================================================
    # BATCH RENDERING TESTS
    # ========================================================================
    
    def test_render_all_fixtures(self):
        """Test rendering all fixture files without crashing"""
        fixture_files = [
            'simple_shapes.svg',
            'complex_paths.svg',
            'edge_cases.svg',
            'color_formats.svg',
            'icon_example.svg',
            'polyline_test.svg',
            'scientific_notation.svg',
            'whitespace_test.svg',
            'rounded_rects.svg',
        ]
        
        success_count = 0
        for fixture_file in fixture_files:
            try:
                svg_path = self._get_fixture_path(fixture_file)
                if os.path.exists(svg_path):
                    renderer = SVGRenderer(svg_file=svg_path)
                    rasterizer = renderer.render()
                    self.assertIsInstance(rasterizer, Rasterizer)
                    success_count += 1
            except Exception as e:
                self.fail(f"Failed to render {fixture_file}: {e}")
        
        self.assertGreater(success_count, 0)
    
    def test_save_all_formats(self):
        """Test saving in different output formats"""
        svg_path = self._get_fixture_path('simple_shapes.svg')
        renderer = SVGRenderer(svg_file=svg_path)
        renderer.render()
        
        # Test PPM format
        ppm_path = self._get_output_path('test_output.ppm')
        renderer.save(ppm_path)
        self.assertTrue(os.path.exists(ppm_path))


class TestSVGFileValidation(unittest.TestCase):
    """Test validation and error handling for SVG files"""
    
    def test_nonexistent_file(self):
        """Test handling of nonexistent file"""
        with self.assertRaises(FileNotFoundError):
            renderer = SVGRenderer(svg_file='nonexistent_file.svg')
    
    def test_empty_file(self):
        """Test handling of empty file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            temp_path = f.name
            f.write('')
        
        try:
            # Should handle gracefully
            with self.assertRaises(Exception):
                renderer = SVGRenderer(svg_file=temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_invalid_xml(self):
        """Test handling of invalid XML"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            temp_path = f.name
            f.write('<svg><rect></svg>')  # Unclosed rect tag
        
        try:
            with self.assertRaises(Exception):
                renderer = SVGRenderer(svg_file=temp_path)
                renderer.render()
        finally:
            os.unlink(temp_path)
    
    def test_malformed_svg_structure(self):
        """Test handling of malformed SVG structure"""
        svg_content = '''<?xml version="1.0"?>
            <svg>
                <rect x="abc" y="def" width="100" height="100"/>
            </svg>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            temp_path = f.name
            f.write(svg_content)
        
        try:
            # Should handle invalid coordinates
            renderer = SVGRenderer(svg_file=temp_path)
            # May fail or handle gracefully
        except Exception:
            pass  # Expected
        finally:
            os.unlink(temp_path)


class TestMemoryAndPerformance(unittest.TestCase):
    """Test memory usage and performance with large SVGs"""
    
    @classmethod
    def setUpClass(cls):
        """Create large test files"""
        cls.temp_dir = tempfile.mkdtemp(prefix='svg_perf_test_')
    
    @classmethod
    def tearDownClass(cls):
        """Clean up"""
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
    
    def test_large_canvas_size(self):
        """Test rendering large canvas"""
        svg = '''<?xml version="1.0"?>
            <svg width="2000" height="2000">
                <rect x="100" y="100" width="500" height="500" fill="red"/>
            </svg>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            temp_path = f.name
            f.write(svg)
        
        try:
            renderer = SVGRenderer(svg_file=temp_path)
            rasterizer = renderer.render()
            self.assertEqual(rasterizer.width, 2000)
            self.assertEqual(rasterizer.height, 2000)
        finally:
            os.unlink(temp_path)
    
    def test_many_small_elements(self):
        """Test rendering many small elements"""
        svg_parts = ['<?xml version="1.0"?><svg width="800" height="800">']
        
        # Create 1000 small rectangles
        for i in range(1000):
            x = (i * 7) % 800
            y = (i * 11) % 800
            svg_parts.append(f'<rect x="{x}" y="{y}" width="5" height="5" fill="red"/>')
        
        svg_parts.append('</svg>')
        svg = ''.join(svg_parts)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            temp_path = f.name
            f.write(svg)
        
        try:
            renderer = SVGRenderer(svg_file=temp_path)
            rasterizer = renderer.render()
            self.assertIsInstance(rasterizer, Rasterizer)
        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
