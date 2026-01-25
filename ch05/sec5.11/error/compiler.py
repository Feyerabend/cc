#!/usr/bin/env python3

import sys
from lexer import tokenize
from parser import Parser
from semantic import SemanticAnalyzer
from codegen import CodeGenerator
from vm import VirtualMachine
from error_reporter import ErrorReporter, ErrorSeverity, ErrorCategory, TooManyErrorsException

def compile_and_run(source_code, verbose=False, stop_on_error=False, context_lines=0):
    """
    Compile and run source code with comprehensive error reporting.
    
    Args:
        source_code: The source code to compile
        verbose: Print detailed compilation stages
        stop_on_error: Stop at first error phase instead of collecting all errors
        context_lines: Number of lines before/after to show in error context (0 for single line)
    
    Returns:
        True if compilation and execution succeeded, False otherwise
    """
    reporter = ErrorReporter(source_code, context_lines=context_lines)
    
    try:
        # Phase 1: Lexical Analysis
        if verbose:
            print("-" * 50)
            print("PHASE 1: LEXICAL ANALYSIS\n")
        
        tokens = tokenize(source_code, reporter)
        
        if verbose and not reporter.has_errors():
            print(f"  Tokenisation successful: {len(tokens)} tokens")
            for token in tokens[:10]:  # Show first 10 tokens
                print(f"  {token}")
            if len(tokens) > 10:
                print(f"  .. and {len(tokens) - 10} more")
            print()
        
        if reporter.has_errors() and stop_on_error:
            reporter.print_report()
            return False
        
        # Phase 2: Syntax Analysis
        if verbose:
            print("-" * 50)
            print("PHASE 2: SYNTAX ANALYSIS\n")
        
        parser = Parser(tokens, reporter)
        ast = parser.parse()
        
        if verbose and not reporter.has_errors():
            print(f"  Parsing successful")
            print(f"  AST: {ast}")
            print()
        
        if reporter.has_errors() and stop_on_error:
            reporter.print_report()
            return False
        
        # Phase 3: Semantic Analysis
        if verbose:
            print("-" * 50)
            print("PHASE 3: SEMANTIC ANALYSIS\n")
        
        analyzer = SemanticAnalyzer(ast, reporter)
        analyzer.analyze()
        analyzer.check_unused_variables()
        
        if verbose and not reporter.has_errors():
            print(f"  Semantic analysis successful")
            print(f"  Symbol table: {list(analyzer.symbol_table.keys())}")
            print()
        
        # Stop if there are any errors (even if not in stop_on_error mode)
        if reporter.has_errors():
            reporter.print_report()
            return False
        
        # Phase 4: Code Generation
        if verbose:
            print("-" * 50)
            print("PHASE 4: CODE GENERATION\n")
        
        generator = CodeGenerator(ast)
        instructions = generator.generate()
        
        if verbose:
            print(f"  Code generation successful: {len(instructions)} instructions")
            for i, instr in enumerate(instructions):
                print(f"  {i:3}: {instr}")
            print()
        
        # Phase 5: Execution
        if verbose:
            print("-" * 50)
            print("PHASE 5: EXECUTION\n\n")
        
        vm = VirtualMachine()
        vm.load(instructions)
        
        try:
            vm.run()
        except RuntimeError as e:
            reporter.report(
                ErrorSeverity.ERROR,
                ErrorCategory.RUNTIME,
                str(e),
                suggestion="Check your program logic and input values."
            )
            reporter.print_report()
            return False
        except Exception as e:
            reporter.report(
                ErrorSeverity.FATAL,
                ErrorCategory.RUNTIME,
                f"Unexpected runtime error: {e}",
                suggestion="This may be a bug in the compiler or VM."
            )
            reporter.print_report()
            import traceback
            traceback.print_exc()
            return False
        
        if verbose:
            print()
            print("-" * 50)
            print("FINAL MEMORY STATE\n")
            for var, value in vm.memory.items():
                print(f"  {var} = {value}")
            print()
        
        # Print warnings if any
        if reporter.warnings:
            reporter.print_report(show_warnings=True)
        elif verbose:
            print("  Execution completed successfully with no warnings")
        
        return True
    
    except TooManyErrorsException:
        reporter.print_report()
        return False
    except KeyboardInterrupt:
        print("\n\nCompilation interrupted by user")
        return False
    except Exception as e:
        reporter.report(
            ErrorSeverity.FATAL,
            ErrorCategory.SYNTAX,
            f"Unexpected compiler error: {e}",
            suggestion="This may be a bug in the compiler. Please report this issue."
        )
        reporter.print_report()
        if verbose:
            import traceback
            traceback.print_exc()
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python compiler.py <source_file> [options]")
        print("\nOptions:")
        print("  --verbose, -v       Show detailed compilation stages")
        print("  --stop-on-error     Stop at first error phase (default: collect all errors)")
        print("  --context N         Show N lines before/after errors (default: 0)")
        print("  --help, -h          Show this help message")
        sys.exit(1)
    
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Compiler with Enhanced Error Reporting")
        print("=" * 70)
        print("\nUsage: python compiler.py <source_file> [options]")
        print("\nOptions:")
        print("  --verbose, -v        Show detailed compilation stages")
        print("  --stop-on-error      Stop at first error phase")
        print("  --context N          Show N lines of context around errors")
        print("  --help, -h           Show this help message")
        print("\nError Reporting:")
        print("  By default, the compiler collects errors from all phases")
        print("  before reporting them. Use --stop-on-error to stop at the")
        print("  first phase that encounters errors.")
        print("\nContext Display:")
        print("  Use --context to show surrounding lines for better error")
        print("  understanding. Example: --context 2 shows 2 lines before")
        print("  and after each error.")
        print("\nExample:")
        print("  python compiler.py program.txt --verbose --context 2")
        sys.exit(0)
    
    filename = sys.argv[1]
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    stop_on_error = "--stop-on-error" in sys.argv
    
    # Parse context lines argument
    context_lines = 0
    for i, arg in enumerate(sys.argv):
        if arg == "--context" and i + 1 < len(sys.argv):
            try:
                context_lines = int(sys.argv[i + 1])
            except ValueError:
                print(f"Error: Invalid context value '{sys.argv[i + 1]}', using default (0)")
    
    try:
        with open(filename, 'r') as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    
    print(f"Compiling: {filename}")
    print()
    
    success = compile_and_run(source_code, verbose=verbose, stop_on_error=stop_on_error, context_lines=context_lines)
    
    print()
    if success:
        print("  Compilation and execution completed successfully")
    else:
        print("  Compilation failed")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
