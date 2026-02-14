"""
Showing how to use the refactored BASIC interpreter.
Sans REPL.
"""

from basic_ii.interpreter import Interpreter


def example_direct_execution():
    """Example: Execute BASIC statements directly."""
    print("- Direct Execution Example -")
    
    interp = Interpreter(debug=False)
    
    # Execute statements one at a time
    interp.execute_line("LET X = 10")
    interp.execute_line("LET Y = 20")
    interp.execute_line("PRINT X + Y")
    
    # Implicit LET
    interp.execute_line("Z = X * Y")
    interp.execute_line("PRINT 'Z ='; Z")
    
    print()


def example_array_usage():
    """Example: Using arrays."""
    print("- Array Example -n")
    
    interp = Interpreter(debug=False)
    
    # Declare array
    interp.execute_line("DIM A(5)")
    
    # Set values
    interp.execute_line("A(1) = 100")
    interp.execute_line("A(2) = 200")
    interp.execute_line("A(3) = A(1) + A(2)")
    
    # Print values
    interp.execute_line("PRINT A(1), A(2), A(3)")
    
    # 2D array
    interp.execute_line("DIM B(3, 3)")
    interp.execute_line("B(1,1) = 11")
    interp.execute_line("B(2,2) = 22")
    interp.execute_line("PRINT B(1,1); ' '; B(2,2)")
    
    print()


def example_control_flow():
    """Example: Control flow statements."""
    print("- Control Flow Example -")
    
    interp = Interpreter(debug=False)
    
    # IF/THEN
    interp.execute_line("X = 15")
    interp.execute_line("IF X > 10 THEN PRINT 'X is large'")
    interp.execute_line("IF X < 5 THEN PRINT 'X is small' ELSE PRINT 'X is not small'")
    
    print()


def example_loops():
    """Example: FOR and WHILE loops."""
    print("- Loop Example -n")
    
    interp = Interpreter(debug=False)
    
    # Manual program entry for FOR loop
    interp.state.code[10] = "REM FOR loop example"
    interp.state.code[20] = "FOR I = 1 TO 5"
    interp.state.code[30] = "PRINT I * I"
    interp.state.code[40] = "NEXT I"
    interp.state.code[50] = "END"
    
    print("FOR loop program:")
    interp.list_program()
    print("\nRunning:")
    interp.run()
    
    print()
    
    # WHILE loop
    interp2 = Interpreter(debug=False)
    interp2.state.code[10] = "REM WHILE loop example"
    interp2.state.code[20] = "X = 1"
    interp2.state.code[30] = "WHILE X <= 5"
    interp2.state.code[40] = "PRINT X"
    interp2.state.code[50] = "X = X + 1"
    interp2.state.code[60] = "WEND"
    interp2.state.code[70] = "END"
    
    print("WHILE loop program:")
    interp2.list_program()
    print("\nRunning:")
    interp2.run()
    
    print()


def example_subroutines():
    """Example: GOSUB/RETURN."""
    print("- Subroutine Example -")
    
    interp = Interpreter(debug=False)
    
    interp.state.code[10] = "REM Main program"
    interp.state.code[20] = "X = 5"
    interp.state.code[30] = "GOSUB 100"
    interp.state.code[40] = "PRINT 'Back in main'"
    interp.state.code[50] = "END"
    interp.state.code[100] = "REM Subroutine"
    interp.state.code[110] = "PRINT 'In subroutine, X='; X"
    interp.state.code[120] = "RETURN"
    
    print("Program with subroutine:")
    interp.list_program()
    print("\nRunning:")
    interp.run()
    
    print()


def example_system_commands():
    """Example: System commands."""
    print("- System Commands Example -")
    
    interp = Interpreter(debug=False)
    
    # Add some code
    interp.state.code[10] = "PRINT 'Line 10'"
    interp.state.code[20] = "PRINT 'Line 20'"
    interp.state.code[30] = "END"
    
    print("Original program:")
    interp.execute_line("LIST")
    
    print("\nAfter REN 100, 10:")
    interp.execute_line("REN 100, 10")
    interp.execute_line("LIST")
    
    print("\nDeleting line 110:")
    interp.execute_line("DEL 110")
    interp.execute_line("LIST")
    
    print()


def example_file_operations():
    """Example: Save and load programs."""
    print("- File Operations Example -")
    
    import tempfile
    import os
    
    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.bas', delete=False)
    temp_filename = temp_file.name
    temp_file.close()
    
    try:
        # Create and save a program
        interp = Interpreter(debug=False)
        interp.state.code[10] = "REM Test program"
        interp.state.code[20] = "PRINT 'Hello from file'"
        interp.state.code[30] = "END"
        
        print("Saving program:")
        interp.execute_line(f"SAVE '{temp_filename}'")
        
        # Load in new interpreter
        interp2 = Interpreter(debug=False)
        print(f"\nLoading into new interpreter:")
        interp2.execute_line(f"LOAD '{temp_filename}'")
        
        print("\nLoaded program:")
        interp2.execute_line("LIST")
        
    finally:
        # Clean up
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
    
    print()


def example_expression_evaluation():
    """Example: How expression evaluation works internally."""
    print("- Expression Evaluation Example -")
    
    from basic_ii.parsing.tokenizer import Tokenizer
    from basic_ii.parsing.parser import ExpressionParser
    from basic_ii.execution.evaluator import ExpressionEvaluator
    from basic_ii.core.state import InterpreterState
    
    # Create state with some variables
    state = InterpreterState()
    state.set_variable("X", 10)
    state.set_variable("Y", 5)
    
    # Expression to evaluate: X * 2 + Y
    expression_text = "X * 2 + Y"
    
    # Step 1: Tokenize
    print(f"Expression: {expression_text}")
    tokenizer = Tokenizer(expression_text)
    tokens = tokenizer.tokenize()
    print(f"Tokens: {[f'{t.type}({t.value})' for t in tokens]}")
    
    # Step 2: Parse to AST
    parser = ExpressionParser(tokens)
    ast = parser.parse()
    print(f"AST: {ast}")
    
    # Step 3: Evaluate
    evaluator = ExpressionEvaluator(state)
    result = evaluator.evaluate(ast)
    print(f"Result: {result}")
    print(f"Expected: {10 * 2 + 5} = 25")
    
    print()


if __name__ == "__main__":
    print("-" * 50)
    print("BASIC Interpreter - Some Examples")
    print("-" * 50)
    print()
    
    example_direct_execution()
    example_array_usage()
    example_control_flow()
    example_loops()
    example_subroutines()
    example_system_commands()
    example_file_operations()
    example_expression_evaluation()
    
    print("-" * 25)
    print("Examples complete!")
    print("-" * 25)
    print()
    print("Try running the example programs in bas/ directory:")
    print("  python -m main bas/hello.bas")

