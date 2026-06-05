#!/usr/bin/env python3
"""
JVM Interpreter Setup Verification

This script verifies that your JVM interpreter is properly set up
and can execute Java bytecode.
"""

import sys
import os

def check_python_version():
    """Check if Python version is 3.7+"""
    print("Checking Python version...", end=" ")
    if sys.version_info < (3, 7):
        print("  FAILED")
        print(f"  Python 3.7+ required, found {sys.version}")
        return False
    print(f"  OK (Python {sys.version_info.major}.{sys.version_info.minor})")
    return True

def check_package_structure():
    """Check if package structure is correct"""
    print("Checking package structure...", end=" ")
    
    required_files = [
        "jvm_interpreter/__init__.py",
        "jvm_interpreter/api/jvm_api.py",
        "jvm_interpreter/runtime/interpreter.py",
        "jvm_interpreter/runtime/class_loader.py",
        "jvm_interpreter/native/native_registry.py",
        "jvm_interpreter/models/java_objects.py",
        "jvm_interpreter/parser/class_file_parser.py",
        "main.py"
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            print("  FAILED")
            print(f"  Missing: {file}")
            return False
    
    print("  OK")
    return True

def check_imports():
    """Check if imports work"""
    print("Checking imports...", end=" ")
    
    try:
        from jvm_interpreter import JavaClassInterpreter
        from jvm_interpreter.native import get_native_registry
        from jvm_interpreter.models import JavaObject, ObjectFactory
        print("  OK")
        return True
    except ImportError as e:
        print("  FAILED")
        print(f"  Import error: {e}")
        return False

def check_native_registry():
    """Check if native registry is working"""
    print("Checking native registry...", end=" ")
    
    try:
        from jvm_interpreter.native import get_native_registry
        
        registry = get_native_registry()
        
        # Check System.out
        if not registry.has_native_static_field("java.lang.System", "out"):
            print("  FAILED")
            print("  System.out not registered")
            return False
        
        # Check StringBuilder
        if not registry.has_native_constructor("java.lang.StringBuilder"):
            print("  FAILED")
            print("  StringBuilder not registered")
            return False
        
        # Check PrintStream.println
        if not registry.has_native_method("java.io.PrintStream", "println"):
            print("  FAILED")
            print("  PrintStream.println not registered")
            return False
        
        print("  OK")
        return True
    except Exception as e:
        print("  FAILED")
        print(f"  Error: {e}")
        return False

def create_test_java_file():
    """Create a simple test Java file"""
    java_code = '''public class SetupTest {
    public static void main(String[] args) {
        System.out.println("JVM Interpreter is working!");
    }
}
'''
    
    with open("SetupTest.java", "w") as f:
        f.write(java_code)
    
    print("Created SetupTest.java")

def compile_test_file():
    """Compile the test Java file"""
    print("Compiling SetupTest.java...", end=" ")
    
    import subprocess
    
    try:
        result = subprocess.run(
            ["javac", "SetupTest.java"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("  FAILED")
            print(f"  javac error: {result.stderr}")
            print("  Note: Make sure Java compiler (javac) is installed")
            return False
        
        if not os.path.exists("SetupTest.class"):
            print("  FAILED")
            print("  SetupTest.class not created")
            return False
        
        print("  OK")
        return True
        
    except FileNotFoundError:
        print("  SKIPPED")
        print("  javac not found - please install Java JDK to compile test")
        return False

def run_test_file():
    """Run the test Java file with the interpreter"""
    
    if not os.path.exists("SetupTest.class"):
        print("  SKIPPED (no .class file)")
        return False
    
    try:
        print("[1/5] Importing modules...")
        from jvm_interpreter.native import get_native_registry
        import io
        
        print("[2/5] Getting System.out...")
        registry = get_native_registry()
        system_out = registry.get_native_static_field("java.lang.System", "out")
        
        print("[3/5] Redirecting output stream...")
        old_stream = system_out.stream
        captured_output = io.StringIO()
        system_out.stream = captured_output
        
        try:
            print("[4/5] Creating interpreter and running SetupTest.main()...")
            from jvm_interpreter import JavaClassInterpreter
            interpreter = JavaClassInterpreter(class_path=['.'])
            result = interpreter.run_method('SetupTest', 'main')
            print("[5/5] Execution complete")
        finally:
            system_out.stream = old_stream
        
        # Get the captured output
        output = captured_output.getvalue().strip()
        
        print(f"\n  Captured output: '{output}'")
        print(f"  Output length: {len(output)} chars")
        
        if output == "JVM Interpreter is working!":
            print("  Test PASSED")
            return True
        else:
            print("  Test FAILED")
            print(f"  Expected: 'JVM Interpreter is working!'")
            print(f"  Got: '{output}'")
            return False
            
    except Exception as e:
        print(f"  FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def cleanup():
    """Clean up test files"""
    print("\nCleaning up test files...", end=" ")
    
    files_to_remove = ["SetupTest.java", "SetupTest.class"]
    
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
    
    print("  Done")

def main():
    """Run all verification checks"""
    print("-" * 60)
    print("JVM Interpreter Setup Verification")
    print("-" * 60)
    print()
    
    all_passed = True
    
    # Basic checks
    all_passed &= check_python_version()
    all_passed &= check_package_structure()
    all_passed &= check_imports()
    all_passed &= check_native_registry()
    
    print()
    
    # Functional test
    print("-" * 60)
    print("Running Functional Test")
    print("-" * 60)
    print()
    
    create_test_java_file()
    compiled = compile_test_file()
    
    if compiled:
        all_passed &= run_test_file()
        cleanup()
    else:
        print("\n  Skipping interpreter test (compilation failed)")
        print("  You can still use the interpreter with pre-compiled .class files")
        cleanup()
    
    print()
    print("-" * 60)
    
    if all_passed:
        print("  All checks passed!")
        print()
        print("Your JVM interpreter is ready to use.")
        print("Try: python main.py YourClass . -v")
    else:
        print("  Some checks failed")
        print()
        print("Please review the errors above and:")
        print("1. Make sure all files are extracted properly")
        print("2. Make sure you're running from the correct directory")
    
    print("-" * 60)

if __name__ == "__main__":
    main()
