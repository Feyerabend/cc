"""
Test fixtures generator for SVG Renderer
Creates various SVG test files for integration testing
"""

import os
from pathlib import Path


def create_test_fixtures(output_dir="test_fixtures"):
    """Create comprehensive test SVG files"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Simple shapes
    simple_shapes = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400">
    <rect x="50" y="50" width="100" height="100" fill="#FF6B6B"/>
    <circle cx="250" cy="100" r="50" fill="#4ECDC4"/>
    <ellipse cx="100" cy="250" rx="60" ry="40" fill="#95E1D3"/>
    <polygon points="250,200 300,300 200,300" fill="#FFE66D"/>
</svg>'''
    
    # 2. Complex paths
    complex_paths = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="500" height="500" viewBox="0 0 500 500">
    <!-- Simple line path -->
    <path d="M 50 50 L 150 50 L 150 150 L 50 150 Z" fill="#FF0000"/>
    
    <!-- Quadratic bezier -->
    <path d="M 200 50 Q 250 10 300 50 T 400 50" fill="none" stroke="#00FF00" stroke-width="2"/>
    
    <!-- Cubic bezier -->
    <path d="M 50 200 C 50 300 200 300 200 200" fill="#0000FF" opacity="0.5"/>
    
    <!-- Arc -->
    <path d="M 250 200 A 50 50 0 0 1 350 200" fill="none" stroke="#FF00FF" stroke-width="3"/>
    
    <!-- Complex shape with multiple commands -->
    <path d="M 50 350 L 100 350 L 100 400 Q 75 425 50 400 Z" fill="#FFFF00"/>
</svg>'''
    
    # 3. Gradients (basic - may not be fully supported)
    gradients = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300">
    <defs>
        <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style="stop-color:rgb(255,255,0);stop-opacity:1" />
            <stop offset="100%" style="stop-color:rgb(255,0,0);stop-opacity:1" />
        </linearGradient>
    </defs>
    <rect x="50" y="50" width="200" height="100" fill="url(#grad1)"/>
    <rect x="50" y="175" width="200" height="100" fill="#00FF00"/>
</svg>'''
    
    # 4. Nested groups and transforms
    groups_transforms = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400">
    <g id="group1">
        <rect x="50" y="50" width="100" height="100" fill="red"/>
        <circle cx="100" cy="100" r="30" fill="blue"/>
    </g>
    <g id="group2" transform="translate(200, 0)">
        <rect x="50" y="50" width="100" height="100" fill="green"/>
        <circle cx="100" cy="100" r="30" fill="yellow"/>
    </g>
</svg>'''
    
    # 5. Stress test - many elements
    many_elements = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="600" height="600">
'''
    for i in range(20):
        for j in range(20):
            x = i * 30
            y = j * 30
            r = (i * 20 + j * 10) % 255
            g = (i * 10 + j * 20) % 255
            b = (i * 15 + j * 15) % 255
            many_elements += f'    <rect x="{x}" y="{y}" width="25" height="25" fill="#{r:02x}{g:02x}{b:02x}"/>\n'
    many_elements += '</svg>'
    
    # 6. Edge cases
    edge_cases = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400">
    <!-- Zero size elements -->
    <rect x="10" y="10" width="0" height="0" fill="red"/>
    <circle cx="50" cy="50" r="0" fill="blue"/>
    
    <!-- Negative coordinates -->
    <rect x="-50" y="-50" width="100" height="100" fill="green"/>
    
    <!-- Very large coordinates -->
    <rect x="10000" y="10000" width="100" height="100" fill="yellow"/>
    
    <!-- Overlapping elements -->
    <rect x="100" y="100" width="100" height="100" fill="red" opacity="0.5"/>
    <rect x="150" y="150" width="100" height="100" fill="blue" opacity="0.5"/>
    
    <!-- No fill -->
    <rect x="300" y="100" width="50" height="50" fill="none" stroke="black"/>
</svg>'''
    
    # 7. Color formats
    color_formats = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="500" height="300">
    <!-- Hex colors -->
    <rect x="10" y="10" width="80" height="80" fill="#FF0000"/>
    <rect x="100" y="10" width="80" height="80" fill="#F00"/>
    
    <!-- RGB colors -->
    <rect x="10" y="100" width="80" height="80" fill="rgb(0, 255, 0)"/>
    <rect x="100" y="100" width="80" height="80" fill="rgba(0, 0, 255, 0.5)"/>
    
    <!-- Named colors -->
    <rect x="10" y="200" width="80" height="80" fill="red"/>
    <rect x="100" y="200" width="80" height="80" fill="blue"/>
    <rect x="190" y="200" width="80" height="80" fill="green"/>
    <rect x="280" y="200" width="80" height="80" fill="yellow"/>
    
    <!-- Style attribute -->
    <rect x="200" y="10" width="80" height="80" style="fill: #FF00FF"/>
    <rect x="290" y="10" width="80" height="80" style="fill: rgb(255, 165, 0)"/>
</svg>'''
    
    # 8. Real-world icon example
    icon_example = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">
    <!-- House icon -->
    <polygon points="50,10 90,50 80,50 80,90 60,90 60,65 40,65 40,90 20,90 20,50 10,50" fill="#8B4513"/>
    <rect x="40" y="65" width="20" height="25" fill="#654321"/>
    <rect x="30" y="35" width="15" height="15" fill="#87CEEB"/>
    <rect x="55" y="35" width="15" height="15" fill="#87CEEB"/>
</svg>'''
    
    # 9. Polyline test
    polyline_test = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400">
    <polyline points="10,10 50,50 90,10 130,50 170,10" 
              fill="none" stroke="blue" stroke-width="3"/>
    <polyline points="200,10 250,80 300,10" 
              fill="yellow" stroke="red" stroke-width="2"/>
    <polygon points="50,150 100,200 0,200" fill="green"/>
</svg>'''
    
    # 10. Scientific notation coordinates
    scientific_notation = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300">
    <rect x="5e1" y="5e1" width="1e2" height="1e2" fill="red"/>
    <circle cx="2e2" cy="1.5e2" r="3e1" fill="blue"/>
</svg>'''
    
    # 11. Whitespace handling
    whitespace_test = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200">
    <path d="M  10   20   L   50    60   L  10   60  Z" fill="red"/>
    <rect x="100" y="50" width="80" height="80" fill="blue"/>
</svg>'''
    
    # 12. Rounded rectangles
    rounded_rects = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300">
    <rect x="50" y="50" width="100" height="100" rx="10" ry="10" fill="red"/>
    <rect x="200" y="50" width="100" height="100" rx="20" ry="5" fill="blue"/>
    <rect x="50" y="200" width="100" height="50" rx="25" ry="25" fill="green"/>
</svg>'''
    
    # Save all files
    fixtures = {
        'simple_shapes.svg': simple_shapes,
        'complex_paths.svg': complex_paths,
        'gradients.svg': gradients,
        'groups_transforms.svg': groups_transforms,
        'many_elements.svg': many_elements,
        'edge_cases.svg': edge_cases,
        'color_formats.svg': color_formats,
        'icon_example.svg': icon_example,
        'polyline_test.svg': polyline_test,
        'scientific_notation.svg': scientific_notation,
        'whitespace_test.svg': whitespace_test,
        'rounded_rects.svg': rounded_rects,
    }
    
    for filename, content in fixtures.items():
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Created: {filepath}")
    
    print(f"\n✓ Created {len(fixtures)} test fixture files in '{output_dir}/'")
    return output_dir


if __name__ == '__main__':
    create_test_fixtures()
