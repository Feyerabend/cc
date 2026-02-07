#!/usr/bin/env python3
"""
SVG Parser Demonstration - Logic Auditor Methodology

This script demonstrates the admissibility-based approach to SVG processing.
Each example shows how the parser enforces formal constraints.
"""

from svg_parser import SVGProcessor, SVGConfig, SVGError, SVGErrorType
import sys


def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def try_process(processor: SVGProcessor, svg: str, description: str):
    """Attempt to process SVG and report results"""
    print(f"Test: {description}")
    print(f"Input:\n{svg[:200]}{'...' if len(svg) > 200 else ''}\n")
    
    try:
        result = processor.process(svg)
        height = len(result)
        width = len(result[0]) if height > 0 else 0
        print(f"✓ SUCCESS: Rendered {width}x{height} image")
        
        # Sample some pixels
        if height > 0 and width > 0:
            center = result[height//2][width//2]
            print(f"  Center pixel: RGBA{center}")
    
    except SVGError as e:
        print(f"✗ REJECTED: {e.error_type.value}")
        print(f"  Reason: {e.message}")
        if e.context:
            print(f"  Context: {e.context}")
    
    except Exception as e:
        print(f"✗ UNEXPECTED ERROR: {type(e).__name__}: {e}")
    
    print()


def main():
    """Run comprehensive demonstration"""
    
    print_section("SVG Parser - Logic Auditor Demonstration")
    print("This demonstrates formal admissibility enforcement at each stage.")
    print("Each test shows how constraints prevent invalid program states.\n")
    
    # ========================================================================
    # Valid Cases - Admissible Worlds
    # ========================================================================
    
    print_section("ADMISSIBLE WORLDS - Valid SVG Processing")
    
    processor = SVGProcessor()
    
    try_process(
        processor,
        """<svg width="200" height="200">
            <rect x="50" y="50" width="100" height="100" fill="red"/>
        </svg>""",
        "Simple rectangle (basic admissible world)"
    )
    
    try_process(
        processor,
        """<svg width="300" height="300">
            <circle cx="150" cy="150" r="100" fill="blue"/>
        </svg>""",
        "Circle rendering"
    )
    
    try_process(
        processor,
        """<svg width="400" height="400">
            <rect x="0" y="0" width="400" height="400" fill="white"/>
            <rect x="100" y="100" width="200" height="200" fill="red"/>
            <circle cx="200" cy="200" r="80" fill="yellow"/>
            <circle cx="200" cy="200" r="50" fill="blue"/>
        </svg>""",
        "Multiple overlapping shapes (painter's algorithm)"
    )
    
    try_process(
        processor,
        """<svg width="200" height="200">
            <g>
                <g>
                    <rect x="50" y="50" width="100" height="100" fill="green"/>
                </g>
            </g>
        </svg>""",
        "Nested groups (bounded depth)"
    )
    
    try_process(
        processor,
        """<svg width="150" height="150">
            <path d="M 50 50 L 100 50 L 100 100 L 50 100 Z" fill="magenta"/>
        </svg>""",
        "Simple path (closed square)"
    )
    
    # ========================================================================
    # Text-Level Inadmissible Worlds
    # ========================================================================
    
    print_section("TEXT-LEVEL VIOLATIONS - A_text Failures")
    
    try_process(
        processor,
        """<svg width="200" height="200">
            <rect x="10" y="10" width="50" height="50" fill="red">
        </svg>""",
        "Malformed XML (unclosed tag) - MUST BE REJECTED"
    )
    
    try_process(
        processor,
        """<!DOCTYPE svg [
            <!ENTITY external SYSTEM "http://malicious.com/data">
        ]>
        <svg>&external;</svg>""",
        "External entity reference - SECURITY VIOLATION"
    )
    
    # ========================================================================
    # AST-Level Inadmissible Worlds
    # ========================================================================
    
    print_section("AST-LEVEL VIOLATIONS - A_ast Failures")
    
    try_process(
        processor,
        """<svg width="200" height="200">
            <script>alert('XSS')</script>
            <rect width="100" height="100"/>
        </svg>""",
        "Unsupported element (<script>) - MUST BE REJECTED"
    )
    
    # Test depth limit
    config_shallow = SVGConfig(max_nesting_depth=3)
    processor_shallow = SVGProcessor(config_shallow)
    
    deep_svg = "<svg>" + "<g>" * 10 + "<rect/>" + "</g>" * 10 + "</svg>"
    try_process(
        processor_shallow,
        deep_svg,
        "Excessive nesting depth - RESOURCE EXHAUSTION PREVENTED"
    )
    
    # Test node count limit
    config_limited = SVGConfig(max_node_count=10)
    processor_limited = SVGProcessor(config_limited)
    
    many_rects = "<svg>" + "<rect/>" * 100 + "</svg>"
    try_process(
        processor_limited,
        many_rects,
        "Excessive node count - MEMORY EXHAUSTION PREVENTED"
    )
    
    # ========================================================================
    # Semantic-Level Inadmissible Worlds
    # ========================================================================
    
    print_section("SEMANTIC-LEVEL VIOLATIONS - A_scene Failures")
    
    try_process(
        processor,
        """<svg width="200" height="200">
            <rect x="10" y="10" width="-50" height="50" fill="red"/>
        </svg>""",
        "Negative width (non-admissible geometry) - HANDLED GRACEFULLY"
    )
    
    # Test path command limit
    config_limited_path = SVGConfig(max_path_commands=5)
    processor_limited_path = SVGProcessor(config_limited_path)
    
    long_path_data = " ".join([f"M {i} {i} L {i+1} {i+1}" for i in range(100)])
    try_process(
        processor_limited_path,
        f'<svg><path d="{long_path_data}"/></svg>',
        "Excessive path commands - COMPLEXITY ATTACK PREVENTED"
    )
    
    # ========================================================================
    # Render-Level Inadmissible Worlds
    # ========================================================================
    
    print_section("RENDER-LEVEL VIOLATIONS - A_render Failures")
    
    try_process(
        processor,
        """<svg width="1000000" height="1000000">
            <rect width="100" height="100"/>
        </svg>""",
        "Enormous canvas - MEMORY BOMB PREVENTED"
    )
    
    # ========================================================================
    # Edge Cases - Boundary Conditions
    # ========================================================================
    
    print_section("EDGE CASES - Boundary Conditions")
    
    try_process(
        processor,
        '<svg width="100" height="100"></svg>',
        "Empty SVG (minimal valid world)"
    )
    
    try_process(
        processor,
        """<svg width="100" height="100">
            <rect x="10" y="10" width="0" height="0" fill="red"/>
        </svg>""",
        "Zero-dimension shape (degenerate but valid)"
    )
    
    try_process(
        processor,
        """<svg width="1" height="1">
            <rect width="1" height="1" fill="#123456"/>
        </svg>""",
        "Minimal 1x1 image"
    )
    
    # ========================================================================
    # Determinism Verification
    # ========================================================================
    
    print_section("DETERMINISM VERIFICATION - A_render Guarantee")
    
    test_svg = """<svg width="100" height="100">
        <rect x="10" y="10" width="80" height="80" fill="red"/>
        <circle cx="50" cy="50" r="30" fill="blue"/>
    </svg>"""
    
    print("Processing same SVG three times...")
    results = []
    for i in range(3):
        result = processor.process(test_svg)
        results.append(result)
        print(f"  Run {i+1}: {len(result)}x{len(result[0])} image")
    
    if results[0] == results[1] == results[2]:
        print("✓ DETERMINISM VERIFIED: All outputs identical")
    else:
        print("✗ DETERMINISM FAILED: Outputs differ")
    
    # ========================================================================
    # PPM Export Example
    # ========================================================================
    
    print_section("PPM EXPORT EXAMPLE")
    
    simple_svg = """<svg width="20" height="20">
        <rect x="0" y="0" width="10" height="10" fill="red"/>
        <rect x="10" y="0" width="10" height="10" fill="green"/>
        <rect x="0" y="10" width="10" height="10" fill="blue"/>
        <rect x="10" y="10" width="10" height="10" fill="yellow"/>
    </svg>"""
    
    try:
        ppm = processor.process_to_ppm(simple_svg)
        print("Generated 20x20 PPM image (2x2 color quadrants)")
        print(f"PPM size: {len(ppm)} bytes")
        print(f"Header: {ppm.split(chr(10))[0:3]}")
        print("✓ PPM export successful")
        
        # Optionally save to file
        with open('./example.ppm', 'w') as f:
            f.write(ppm)
        print("Saved to example.ppm")
    
    except Exception as e:
        print(f"✗ PPM export failed: {e}")
    
    # ========================================================================
    # Summary
    # ========================================================================
    
    print_section("SUMMARY")
    
    print("""
Key Principles Demonstrated:

1. ADMISSIBILITY AT EVERY STAGE
   - Text → AST: Only well-formed, safe XML
   - AST → Scene: Only supported elements, bounded resources
   - Scene → Image: Only finite geometry, deterministic output

2. TOTAL FUNCTIONS
   - No crashes on malformed input
   - Explicit, typed errors for all rejection cases
   - No undefined behavior

3. FORMAL CONSTRAINTS
   - Depth limits prevent stack overflow
   - Node count limits prevent memory exhaustion
   - Command limits prevent complexity attacks
   - Finiteness checks prevent numerical instability

4. SECURITY BY CONSTRUCTION
   - No external resources
   - No script execution
   - No buffer overflows
   - No resource exhaustion

The implementation is correct because:
  "All reachable states correspond to admissible SVG interpretations"

This is the Logic Auditor methodology applied to real code.
""")


if __name__ == '__main__':
    main()
