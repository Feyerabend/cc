"""
Demo script showing the improved SVG renderer capabilities
"""

from svg_renderer import (
    SVGRenderer, Color, Point, Rasterizer, PathParser,
    FillRule, PathCommand, MoveTo, LineTo, CubicBezier
)


def demo_basic_shapes():
    """Demo 1: Basic shapes with various colors"""
    print("Demo 1: Creating basic shapes...")
    
    svg = """
    <svg xmlns="http://www.w3.org/2000/svg" width="500" height="400">
        <!-- Rectangles -->
        <rect x="20" y="20" width="100" height="80" fill="#FF6B6B"/>
        <rect x="140" y="20" width="100" height="80" fill="#4ECDC4"/>
        
        <!-- Circles -->
        <circle cx="70" cy="180" r="40" fill="#FFE66D"/>
        <circle cx="190" cy="180" r="40" fill="#95E1D3"/>
        
        <!-- Ellipses -->
        <ellipse cx="70" cy="300" rx="50" ry="30" fill="#F38181"/>
        <ellipse cx="190" cy="300" rx="50" ry="30" fill="#AA96DA"/>
        
        <!-- Triangle using path -->
        <path d="M 300 50 L 400 50 L 350 120 Z" fill="#FCBAD3"/>
        
        <!-- Star using polygon -->
        <polygon points="350,180 370,230 425,230 380,265 400,320 350,285 300,320 320,265 275,230 330,230" 
                 fill="#FFFFD2"/>
    </svg>
    """
    
    renderer = SVGRenderer(svg_string=svg)
    renderer.render()
    renderer.save("demo1_basic_shapes.ppm")
    print("✓ Saved to demo1_basic_shapes.ppm")


def demo_complex_paths():
    """Demo 2: Complex paths with bezier curves"""
    print("\nDemo 2: Creating complex paths with curves...")
    
    svg = """
    <svg xmlns="http://www.w3.org/2000/svg" width="500" height="300">
        <!-- Heart shape using cubic bezier -->
        <path d="M 250,100 
                 C 250,80 230,60 200,60 
                 C 170,60 150,80 150,110 
                 C 150,140 250,200 250,200 
                 C 250,200 350,140 350,110 
                 C 350,80 330,60 300,60 
                 C 270,60 250,80 250,100 Z" 
              fill="#FF1744"/>
        
        <!-- Wave using smooth curves -->
        <path d="M 50,250 
                 Q 100,200 150,250 
                 Q 200,300 250,250 
                 Q 300,200 350,250 
                 Q 400,300 450,250 
                 L 450,280 L 50,280 Z" 
              fill="#00BCD4"/>
    </svg>
    """
    
    renderer = SVGRenderer(svg_string=svg)
    renderer.render()
    renderer.save("demo2_complex_paths.ppm")
    print("✓ Saved to demo2_complex_paths.ppm")


def demo_color_formats():
    """Demo 3: Different color format support"""
    print("\nDemo 3: Testing various color formats...")
    
    svg = """
    <svg xmlns="http://www.w3.org/2000/svg" width="400" height="300">
        <!-- Hex colors -->
        <rect x="20" y="20" width="80" height="60" fill="#FF5722"/>
        
        <!-- Short hex -->
        <rect x="120" y="20" width="80" height="60" fill="#F52"/>
        
        <!-- RGB -->
        <rect x="220" y="20" width="80" height="60" fill="rgb(76, 175, 80)"/>
        
        <!-- Named colors -->
        <rect x="20" y="100" width="80" height="60" fill="red"/>
        <rect x="120" y="100" width="80" height="60" fill="blue"/>
        <rect x="220" y="100" width="80" height="60" fill="green"/>
        
        <!-- Style attribute -->
        <rect x="20" y="180" width="80" height="60" style="fill:#9C27B0"/>
        <rect x="120" y="180" width="80" height="60" style="fill:cyan"/>
    </svg>
    """
    
    renderer = SVGRenderer(svg_string=svg)
    renderer.render()
    renderer.save("demo3_colors.ppm")
    print("✓ Saved to demo3_colors.ppm")


def demo_programmatic_rendering():
    """Demo 4: Programmatic rendering without SVG"""
    print("\nDemo 4: Creating image programmatically...")
    
    rasterizer = Rasterizer(400, 400, Color(240, 240, 240))
    
    # Draw a gradient-like effect with circles
    for i in range(20):
        radius = 150 - i * 7
        color = Color(255 - i * 10, 100 + i * 5, 150 + i * 5)
        rasterizer.draw_circle(Point(200, 200), radius, color)
    
    # Add some decorative shapes
    rasterizer.draw_rectangle(50, 50, 80, 80, Color(255, 200, 0))
    rasterizer.draw_rectangle(270, 270, 80, 80, Color(0, 200, 255))
    
    rasterizer.save_ppm("demo4_programmatic.ppm")
    print("✓ Saved to demo4_programmatic.ppm")


def demo_path_parser():
    """Demo 5: Advanced path parsing"""
    print("\nDemo 5: Testing path parser with various commands...")
    
    svg = """
    <svg xmlns="http://www.w3.org/2000/svg" width="500" height="400">
        <!-- Absolute commands -->
        <path d="M 50 50 L 150 50 L 150 150 L 50 150 Z" fill="#E91E63"/>
        
        <!-- Relative commands -->
        <path d="M 200 50 l 100 0 l 0 100 l -100 0 z" fill="#3F51B5"/>
        
        <!-- Horizontal and vertical lines -->
        <path d="M 350 50 h 100 v 100 h -100 v -100" fill="#009688"/>
        
        <!-- Cubic bezier (absolute) -->
        <path d="M 50 200 C 50 250 150 250 150 300 L 50 300 Z" fill="#FF9800"/>
        
        <!-- Quadratic bezier (relative) -->
        <path d="M 200 200 q 50 50 100 0 l 0 100 l -100 0 z" fill="#8BC34A"/>
    </svg>
    """
    
    renderer = SVGRenderer(svg_string=svg)
    renderer.render()
    renderer.save("demo5_path_commands.ppm")
    print("✓ Saved to demo5_path_commands.ppm")


def demo_composite_scene():
    """Demo 6: Complex composite scene"""
    print("\nDemo 6: Creating a composite scene...")
    
    svg = """
    <svg xmlns="http://www.w3.org/2000/svg" width="600" height="400" viewBox="0 0 600 400">
        <!-- Sky -->
        <rect x="0" y="0" width="600" height="250" fill="#87CEEB"/>
        
        <!-- Sun -->
        <circle cx="500" cy="80" r="40" fill="#FFD700"/>
        
        <!-- Ground -->
        <rect x="0" y="250" width="600" height="150" fill="#90EE90"/>
        
        <!-- House body -->
        <rect x="150" y="180" width="120" height="100" fill="#D2691E"/>
        
        <!-- Roof -->
        <path d="M 140 180 L 210 130 L 280 180 Z" fill="#8B4513"/>
        
        <!-- Door -->
        <rect x="190" y="230" width="40" height="50" fill="#654321"/>
        
        <!-- Window -->
        <rect x="165" y="200" width="30" height="30" fill="#ADD8E6"/>
        <rect x="225" y="200" width="30" height="30" fill="#ADD8E6"/>
        
        <!-- Tree trunk -->
        <rect x="400" y="200" width="30" height="80" fill="#8B4513"/>
        
        <!-- Tree foliage -->
        <circle cx="350" cy="200" r="40" fill="#228B22"/>
        <circle cx="415" cy="180" r="45" fill="#228B22"/>
        <circle cx="450" cy="210" r="35" fill="#228B22"/>
        
        <!-- Clouds -->
        <ellipse cx="100" cy="60" rx="40" ry="25" fill="#FFFFFF"/>
        <ellipse cx="130" cy="60" rx="35" ry="20" fill="#FFFFFF"/>
        <ellipse cx="115" cy="50" rx="30" ry="20" fill="#FFFFFF"/>
        
        <ellipse cx="350" cy="80" rx="50" ry="30" fill="#FFFFFF"/>
        <ellipse cx="390" cy="80" rx="40" ry="25" fill="#FFFFFF"/>
    </svg>
    """
    
    renderer = SVGRenderer(svg_string=svg)
    renderer.render()
    renderer.save("demo6_scene.ppm")
    print("✓ Saved to demo6_scene.ppm")


def print_improvements():
    """Print a summary of improvements"""
    print("\n" + "="*60)
    print("KEY IMPROVEMENTS IN THE NEW SVG RENDERER")
    print("="*60)
    
    improvements = [
        ("Better Architecture", [
            "Object-oriented design with clear class separation",
            "Dataclasses for cleaner data structures (Color, Point)",
            "Enum for fill rules instead of strings"
        ]),
        ("Enhanced Path Parsing", [
            "Support for ALL SVG path commands (M, L, H, V, C, Q, A, Z)",
            "Both absolute and relative command variants",
            "Proper quadratic bezier support",
            "Arc approximation",
            "More robust tokenization"
        ]),
        ("Better Color Handling", [
            "Multiple color format support (hex, rgb, rgba, named colors)",
            "Short hex color support (#RGB)",
            "Alpha channel support for future transparency",
            "Color blending capability"
        ]),
        ("Improved Rendering", [
            "Cleaner scanline algorithm",
            "Support for even-odd and non-zero fill rules",
            "Better curve subdivision algorithm",
            "Ellipse and rounded rectangle support",
            "More accurate bezier approximation"
        ]),
        ("More SVG Elements", [
            "path, rect, circle, ellipse",
            "polygon and polyline support",
            "Style and attribute parsing",
            "ViewBox support"
        ]),
        ("Better Code Quality", [
            "Type hints throughout",
            "Comprehensive docstrings",
            "Separation of concerns",
            "Extensible design for future features"
        ]),
        ("Additional Features", [
            "PNG output support (with PIL)",
            "Programmatic rendering API",
            "Configurable background color",
            "Point/Vector math utilities"
        ])
    ]
    
    for title, items in improvements:
        print(f"\n{title}:")
        for item in items:
            print(f"  ✓ {item}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    print("SVG Renderer Improvement Demos")
    print("="*60)
    
    # Run all demos
    demo_basic_shapes()
    demo_complex_paths()
    demo_color_formats()
    demo_programmatic_rendering()
    demo_path_parser()
    demo_composite_scene()
    
    # Print summary
    print_improvements()
    
    print("\n✨ All demos completed!")
    print("Check the generated .ppm files to see the results.")
    print("You can view PPM files with image viewers like GIMP, IrfanView, or convert to PNG.")
