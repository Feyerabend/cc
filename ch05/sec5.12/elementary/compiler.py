#!/usr/bin/env python3

import sys
from lexer import tokenize
from parser import Parser
from semantic import SemanticAnalyzer
from codegen import CodeGenerator
from vm import VirtualMachine

def compile_and_run(source_code, verbose=False):
    try:
        # Lexical analysis
        if verbose:
            print("=== LEXICAL ANALYSIS ===")
        tokens = tokenize(source_code)
        if verbose:
            for token in tokens:
                print(f"  {token}")
            print()
        
        # Syntax analysis
        if verbose:
            print("=== SYNTAX ANALYSIS ===")
        parser = Parser(tokens)
        ast = parser.parse()
        if verbose:
            print(f"  {ast}")
            print()
        
        # Semantic analysis
        if verbose:
            print("=== SEMANTIC ANALYSIS ===")
        analyzer = SemanticAnalyzer(ast)
        errors = analyzer.analyze()
        if errors:
            print("Semantic errors found:")
            for error in errors:
                print(f"  - {error}")
            return False
        if verbose:
            print("  No errors found")
            print()
        
        # Code generation
        if verbose:
            print("=== CODE GENERATION ===")
        generator = CodeGenerator(ast)
        instructions = generator.generate()
        if verbose:
            for i, instr in enumerate(instructions):
                print(f"  {i:3}: {instr}")
            print()
        
        # Execution
        if verbose:
            print("=== EXECUTION ===")
        vm = VirtualMachine()
        vm.load(instructions)
        vm.run()
        
        if verbose:
            print()
            print("=== FINAL MEMORY STATE ===")
            for var, value in vm.memory.items():
                print(f"  {var} = {value}")
        
        return True
    
    except SyntaxError as e:
        print(f"Syntax Error: {e}")
        return False
    except RuntimeError as e:
        print(f"Runtime Error: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python compiler.py <source_file> [--verbose]")
        sys.exit(1)
    
    filename = sys.argv[1]
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    
    try:
        with open(filename, 'r') as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
        sys.exit(1)
    
    success = compile_and_run(source_code, verbose)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
