#!/usr/bin/env python3
"""
Standalone Test Runner - No pytest required
Tests all admissibility constraints
"""

from svg_parser import (
    SVGProcessor, SVGConfig, SVGError, SVGErrorType,
    SVGTransform
)


class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def record_pass(self, name):
        self.passed += 1
        print(f"✓ {name}")
    
    def record_fail(self, name, reason):
        self.failed += 1
        self.errors.append((name, reason))
        print(f"✗ {name}: {reason}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*70}")
        print(f"Results: {self.passed}/{total} passed, {self.failed}/{total} failed")
        if self.errors:
            print(f"\nFailed tests:")
            for name, reason in self.errors:
                print(f"  - {name}: {reason}")
        print(f"{'='*70}")
        return self.failed == 0


def test_external_entities_forbidden():
    """A_text: External entities must be rejected"""
    processor = SVGProcessor()
    
    with_entity = """<!DOCTYPE svg [
        <!ENTITY external SYSTEM "http://evil.com/data">
    ]>
    <svg>&external;</svg>"""
    
    try:
        processor.process(with_entity)
        return False, "Did not raise SVGError"
    except SVGError as e:
        if e.error_type == SVGErrorType.EXTERNAL_ENTITY:
            return True, None
        else:
            return False, f"Wrong error type: {e.error_type} (expected EXTERNAL_ENTITY)"
    except Exception as e:
        return False, f"Wrong exception: {type(e).__name__}"


def test_transform_composition_overflow_detected():
    """A_scene: Transform composition must detect overflow"""
    # Use values that actually overflow to infinity
    t1 = SVGTransform((1e308, 0, 0, 1e308, 0, 0))
    t2 = SVGTransform((1e308, 0, 0, 1e308, 0, 0))
    
    try:
        result = t1.compose(t2)
        return False, "Did not raise SVGError on overflow"
    except SVGError as e:
        if e.error_type == SVGErrorType.INVALID_TRANSFORM:
            return True, None
        else:
            return False, f"Wrong error type: {e.error_type}"
    except Exception as e:
        return False, f"Wrong exception: {type(e).__name__}"


def test_path_command_limit_enforced():
    """A_scene: Path command count must be bounded"""
    config = SVGConfig(max_path_commands=10)
    processor = SVGProcessor(config)
    
    # Create path with many commands
    path_data = " ".join([f"M {i} {i} L {i+1} {i+1}" for i in range(100)])
    svg = f'<svg><path d="{path_data}"/></svg>'
    
    try:
        processor.process(svg)
        return False, "Did not raise SVGError on too many path commands"
    except SVGError as e:
        if e.error_type == SVGErrorType.INVALID_PATH:
            return True, None
        else:
            return False, f"Wrong error type: {e.error_type}"
    except Exception as e:
        return False, f"Wrong exception: {type(e).__name__}"


def test_memory_bounded():
    """A_render: Image size must not exceed memory bounds"""
    processor = SVGProcessor()
    
    # Try to create enormous image
    huge_svg = '<svg width="100000" height="100000"></svg>'
    
    try:
        processor.process(huge_svg)
        return False, "Did not raise SVGError on huge image"
    except SVGError as e:
        if e.error_type == SVGErrorType.NON_FINITE_GEOMETRY:
            return True, None
        else:
            return False, f"Wrong error type: {e.error_type}"
    except Exception as e:
        return False, f"Wrong exception: {type(e).__name__}"


def test_malformed_xml():
    """A_text: Malformed XML must be rejected"""
    processor = SVGProcessor()
    svg = '<svg><rect></svg>'  # Unclosed rect
    
    try:
        processor.process(svg)
        return False, "Did not raise SVGError"
    except SVGError as e:
        if e.error_type == SVGErrorType.MALFORMED_XML:
            return True, None
        else:
            return False, f"Wrong error type: {e.error_type}"
    except Exception as e:
        return False, f"Wrong exception: {type(e).__name__}"


def test_unsupported_element():
    """A_ast: Unsupported elements must be rejected"""
    processor = SVGProcessor()
    svg = '<svg><script>alert("xss")</script></svg>'
    
    try:
        processor.process(svg)
        return False, "Did not raise SVGError"
    except SVGError as e:
        if e.error_type == SVGErrorType.UNSUPPORTED_ELEMENT:
            return True, None
        else:
            return False, f"Wrong error type: {e.error_type}"
    except Exception as e:
        return False, f"Wrong exception: {type(e).__name__}"


def test_depth_limit():
    """A_ast: Depth limit must be enforced"""
    config = SVGConfig(max_nesting_depth=3)
    processor = SVGProcessor(config)
    
    deep_svg = "<svg>" + "<g>" * 10 + "</g>" * 10 + "</svg>"
    
    try:
        processor.process(deep_svg)
        return False, "Did not raise SVGError"
    except SVGError as e:
        if e.error_type == SVGErrorType.DEPTH_EXCEEDED:
            return True, None
        else:
            return False, f"Wrong error type: {e.error_type}"
    except Exception as e:
        return False, f"Wrong exception: {type(e).__name__}"


def test_valid_svg():
    """Valid SVG should process successfully"""
    processor = SVGProcessor()
    svg = '<svg width="100" height="100"><rect width="50" height="50" fill="red"/></svg>'
    
    try:
        result = processor.process(svg)
        if len(result) == 100 and len(result[0]) == 100:
            return True, None
        else:
            return False, f"Wrong dimensions: {len(result)}x{len(result[0])}"
    except Exception as e:
        return False, f"Unexpected error: {type(e).__name__}: {e}"


def test_deterministic():
    """A_render: Rendering must be deterministic"""
    processor = SVGProcessor()
    svg = '<svg width="50" height="50"><rect width="50" height="50" fill="blue"/></svg>'
    
    try:
        result1 = processor.process(svg)
        result2 = processor.process(svg)
        result3 = processor.process(svg)
        
        if result1 == result2 == result3:
            return True, None
        else:
            return False, "Results not identical"
    except Exception as e:
        return False, f"Unexpected error: {type(e).__name__}: {e}"


def main():
    """Run all tests"""
    print("="*70)
    print("SVG Parser Test Suite - Admissibility Enforcement")
    print("="*70)
    print()
    
    results = TestResult()
    
    tests = [
        ("Malformed XML rejection", test_malformed_xml),
        ("External entity rejection", test_external_entities_forbidden),
        ("Unsupported element rejection", test_unsupported_element),
        ("Depth limit enforcement", test_depth_limit),
        ("Transform overflow detection", test_transform_composition_overflow_detected),
        ("Path command limit enforcement", test_path_command_limit_enforced),
        ("Memory bounds enforcement", test_memory_bounded),
        ("Valid SVG processing", test_valid_svg),
        ("Deterministic rendering", test_deterministic),
    ]
    
    for name, test_func in tests:
        try:
            passed, reason = test_func()
            if passed:
                results.record_pass(name)
            else:
                results.record_fail(name, reason)
        except Exception as e:
            results.record_fail(name, f"Test error: {type(e).__name__}: {e}")
    
    print()
    success = results.summary()
    
    if success:
        print("\n🎉 All admissibility constraints properly enforced!")
    else:
        print("\n⚠️  Some constraints need fixing")
    
    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
