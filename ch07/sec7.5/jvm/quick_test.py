#!/usr/bin/env python3
"""
Quick Test - Verify JVM Interpreter Works

This script does a quick check that the interpreter is working.
No Java compiler needed - uses a pre-made test.
"""

import sys
import os

def test_imports():
    """Test that imports work"""
    print("Testing imports...", end=" ")
    try:
        from jvm_interpreter import JavaClassInterpreter
        from jvm_interpreter.native import get_native_registry
        print("  OK")
        return True
    except ImportError as e:
        print("  FAILED")
        print(f"  Error: {e}")
        return False

def test_native_registry():
    """Test native registry"""
    print("Testing native registry...", end=" ")
    try:
        from jvm_interpreter.native import get_native_registry
        
        registry = get_native_registry()
        
        # Test System.out
        system_out = registry.get_native_static_field("java.lang.System", "out")
        
        # Test StringBuilder
        sb = registry.create_native_object("java.lang.StringBuilder")
        sb = registry.invoke_native_method("java.lang.StringBuilder", "append", sb, ["Hello"])
        result = registry.invoke_native_method("java.lang.StringBuilder", "toString", sb, [])
        
        if result == "Hello":
            print("  OK")
            return True
        else:
            print("  FAILED")
            print(f"  StringBuilder test failed: got '{result}'")
            return False
            
    except Exception as e:
        print("  FAILED")
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_println():
    """Test System.out.println directly"""
    print("Testing System.out.println...", end=" ")
    try:
        from jvm_interpreter.native import get_native_registry
        import io
        import sys as python_sys
        
        registry = get_native_registry()
        
        # Get System.out
        system_out = registry.get_native_static_field("java.lang.System", "out")
        
        # The PrintStream uses print() which writes to sys.stdout
        # We need to temporarily replace its stream
        old_stream = system_out.stream
        captured = io.StringIO()
        system_out.stream = captured
        
        try:
            # Call println
            registry.invoke_native_method("java.io.PrintStream", "println", system_out, ["Test message"])
        finally:
            # Restore original stream
            system_out.stream = old_stream
        
        output = captured.getvalue().strip()
        
        if output == "Test message":
            print("  OK")
            return True
        else:
            print("  FAILED")
            print(f"  Expected: 'Test message'")
            print(f"  Got: '{output}'")
            return False
            
    except Exception as e:
        print("  FAILED")
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("JVM Interpreter Quick Test")
    print()
    
    all_passed = True
    
    all_passed &= test_imports()
    all_passed &= test_native_registry()
    all_passed &= test_println()
    
    print()
    
    if all_passed:
        print("  All tests passed!")
        print()
        print("Your JVM interpreter is working correctly.")
        print()
        print("Next steps:")
        print("1. Create a Java file: Hello.java")
        print("2. Compile it: javac Hello.java")
        print("3. Run it: python main.py Hello . -v")
    else:
        print("  Some tests failed")
        print()
        print("Please check:")
        print("1. All files extracted correctly")
        print("2. Running from correct directory (with jvm_interpreter/ folder)")
        print("3. Python 3.7+ installed")
    
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
