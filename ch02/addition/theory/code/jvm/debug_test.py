#!/usr/bin/env python3
"""
Debug test to understand System.out behaviour
"""

import io
import sys

print("=== Debug Test ===\n")

# Step 1: Import and get System.out
print("Step 1: Getting System.out from registry")
from jvm_interpreter.native import get_native_registry

registry = get_native_registry()
system_out = registry.get_native_static_field("java.lang.System", "out")

print(f"  System.out object: {system_out}")
print(f"  System.out id: {id(system_out)}")
print(f"  System.out.stream: {system_out.stream}")
print(f"  System.out.stream id: {id(system_out.stream)}")
print()

# Step 2: Redirect the stream
print("Step 2: Redirecting stream")
old_stream = system_out.stream
captured = io.StringIO()
system_out.stream = captured

print(f"  New stream: {system_out.stream}")
print(f"  New stream id: {id(system_out.stream)}")
print()

# Step 3: Call println directly through registry
print("Step 3: Calling println through registry")
registry.invoke_native_method("java.io.PrintStream", "println", system_out, ["Direct call test"])

output1 = captured.getvalue()
print(f"  Captured: '{output1.strip()}'")
print()

# Step 4: Now create interpreter and run Java code
print("Step 4: Running Java code through interpreter")
captured.truncate(0)
captured.seek(0)

from jvm_interpreter import JavaClassInterpreter

# Create a simple test if .class file exists
if True:  # We'll test with quick_test style
    print("  (Simulating Java call)")
    # Simulate what the interpreter does
    registry.invoke_native_method("java.io.PrintStream", "println", system_out, ["Java code test"])
    
    output2 = captured.getvalue()
    print(f"  Captured: '{output2.strip()}'")
    print()

# Step 5: Check if System.out is the same object everywhere
print("Step 5: Checking object identity")
system_out_again = registry.get_native_static_field("java.lang.System", "out")
print(f"  Same object? {system_out is system_out_again}")
print(f"  ID matches? {id(system_out) == id(system_out_again)}")
print()

# Restore
system_out.stream = old_stream

print("=== End Debug Test ===")
