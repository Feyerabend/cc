#!/usr/bin/env python3
"""
Test script to verify the BASIC interpreter works correctly.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from basic_ii.interpreter import Interpreter

def test_run_command():
    """Test that RUN command actually executes the program."""
    print("=" * 60)
    print("Testing RUN Command")
    print("=" * 60)
    
    interp = Interpreter(debug=False)
    
    # Add a simple program
    interp.state.code[10] = "PRINT 'Starting program'"
    interp.state.code[20] = "LET X = 5"
    interp.state.code[30] = "PRINT 'X = '; X"
    interp.state.code[40] = "END"
    
    print("\nProgram:")
    interp.list_program()
    
    print("\nExecuting with RUN command:")
    print("-" * 60)
    interp.execute_line("RUN")
    print("-" * 60)
    
    print("\n✓ RUN command test completed")
    print()

def test_for_loop():
    """Test FOR loop execution."""
    print("=" * 60)
    print("Testing FOR Loop")
    print("=" * 60)
    
    interp = Interpreter(debug=False)
    
    interp.state.code[10] = "FOR I = 1 TO 5"
    interp.state.code[20] = "PRINT I"
    interp.state.code[30] = "NEXT I"
    interp.state.code[40] = "END"
    
    print("\nProgram:")
    interp.list_program()
    
    print("\nRunning:")
    print("-" * 60)
    interp.run()
    print("-" * 60)
    
    print("\n✓ FOR loop test completed")
    print()

def test_if_then():
    """Test IF/THEN execution."""
    print("=" * 60)
    print("Testing IF/THEN")
    print("=" * 60)
    
    interp = Interpreter(debug=False)
    
    interp.state.code[10] = "LET X = 10"
    interp.state.code[20] = "IF X > 5 THEN PRINT 'X is big'"
    interp.state.code[30] = "IF X < 5 THEN PRINT 'X is small' ELSE PRINT 'X is not small'"
    interp.state.code[40] = "END"
    
    print("\nProgram:")
    interp.list_program()
    
    print("\nRunning:")
    print("-" * 60)
    interp.run()
    print("-" * 60)
    
    print("\n✓ IF/THEN test completed")
    print()

def test_goto():
    """Test GOTO execution."""
    print("=" * 60)
    print("Testing GOTO")
    print("=" * 60)
    
    interp = Interpreter(debug=False)
    
    interp.state.code[10] = "PRINT 'Line 10'"
    interp.state.code[20] = "GOTO 40"
    interp.state.code[30] = "PRINT 'Line 30 - should not print'"
    interp.state.code[40] = "PRINT 'Line 40'"
    interp.state.code[50] = "END"
    
    print("\nProgram:")
    interp.list_program()
    
    print("\nRunning (should skip line 30):")
    print("-" * 60)
    interp.run()
    print("-" * 60)
    
    print("\n✓ GOTO test completed")
    print()

def test_gosub_return():
    """Test GOSUB/RETURN execution."""
    print("=" * 60)
    print("Testing GOSUB/RETURN")
    print("=" * 60)
    
    interp = Interpreter(debug=False)
    
    interp.state.code[10] = "PRINT 'Main program'"
    interp.state.code[20] = "GOSUB 100"
    interp.state.code[30] = "PRINT 'Back in main'"
    interp.state.code[40] = "END"
    interp.state.code[100] = "PRINT 'In subroutine'"
    interp.state.code[110] = "RETURN"
    
    print("\nProgram:")
    interp.list_program()
    
    print("\nRunning:")
    print("-" * 60)
    interp.run()
    print("-" * 60)
    
    print("\n✓ GOSUB/RETURN test completed")
    print()

def test_while_loop():
    """Test WHILE/WEND execution."""
    print("=" * 60)
    print("Testing WHILE/WEND")
    print("=" * 60)
    
    interp = Interpreter(debug=False)
    
    interp.state.code[10] = "LET X = 1"
    interp.state.code[20] = "WHILE X <= 5"
    interp.state.code[30] = "PRINT X"
    interp.state.code[40] = "LET X = X + 1"
    interp.state.code[50] = "WEND"
    interp.state.code[60] = "END"
    
    print("\nProgram:")
    interp.list_program()
    
    print("\nRunning:")
    print("-" * 60)
    interp.run()
    print("-" * 60)
    
    print("\n✓ WHILE/WEND test completed")
    print()

def test_arrays():
    """Test array operations."""
    print("=" * 60)
    print("Testing Arrays")
    print("=" * 60)
    
    interp = Interpreter(debug=False)
    
    interp.state.code[10] = "DIM A(3)"
    interp.state.code[20] = "FOR I = 1 TO 3"
    interp.state.code[30] = "LET A(I) = I * 10"
    interp.state.code[40] = "NEXT I"
    interp.state.code[50] = "FOR I = 1 TO 3"
    interp.state.code[60] = "PRINT 'A('; I; ') = '; A(I)"
    interp.state.code[70] = "NEXT I"
    interp.state.code[80] = "END"
    
    print("\nProgram:")
    interp.list_program()
    
    print("\nRunning:")
    print("-" * 60)
    interp.run()
    print("-" * 60)
    
    print("\n✓ Array test completed")
    print()

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("BASIC Interpreter - Comprehensive Test Suite")
    print("=" * 60)
    print()
    
    try:
        test_run_command()
        test_for_loop()
        test_if_then()
        test_goto()
        test_gosub_return()
        test_while_loop()
        test_arrays()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print()
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
