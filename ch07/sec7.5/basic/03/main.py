#!/usr/bin/env python3
"""
BASIC Interpreter - Command Line Interface
Main entry point for the BASIC interpreter.
"""
import sys
import os
import readline  # For command history in interactive mode
from basic_ii.interpreter import Interpreter
from basic_ii.parsing.tokenizer import Tokenizer
from basic_ii.parsing.parser import ExpressionParser
from basic_ii.execution.evaluator import ExpressionEvaluator


def print_banner():
    """Print welcome banner."""
    print("=" * 60)
    print("BASIC Interpreter - Version 2.0")
    print("=" * 60)
    print("Type HELP for help, BYE to exit")
    print()


def interactive_mode(interpreter: Interpreter):
    """Run the interpreter in interactive mode."""
    print_banner()
    
    while True:
        try:
            # Get user input
            line = input("> ").strip()
            
            if not line:
                continue
            
            # Check if it's a numbered line (program line)
            parts = line.split(None, 1)
            if parts and parts[0].isdigit():
                # It's a program line - store it
                line_num = int(parts[0])
                content = parts[1] if len(parts) > 1 else ""
                
                if content:
                    # Add/update line
                    interpreter.state.code[line_num] = content
                else:
                    # Empty content - delete line
                    if line_num in interpreter.state.code:
                        del interpreter.state.code[line_num]
                        print(f"Deleted line {line_num}")
            else:
                # Direct command - execute immediately
                interpreter.execute_line(line)
        
        except KeyboardInterrupt:
            print("\n(Interrupted - use BYE to exit)")
            continue
        
        except EOFError:
            print("\nBye Bye!")
            break
        
        except Exception as e:
            print(f"Error: {e}")
            if "--debug" in sys.argv:
                import traceback
                traceback.print_exc()


def run_program_file(interpreter: Interpreter, filename: str, trace: bool = False):
    """Load and run a BASIC program file."""
    try:
        # Load the program
        interpreter.load_program(filename)
        print(f"Loaded {len(interpreter.state.code)} lines from {filename}")
        
        # Run it
        print("Running program..")
        print("-" * 60)
        interpreter.run(trace=trace)
        print("-" * 60)
        print("Program completed")
        
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nProgram interrupted")
        print(f"Stopped at line {interpreter.state.get_current_line()}")
        
        # Enter interactive mode for debugging
        print("\nEntering interactive mode (use CONTINUE to resume, BYE to exit)")
        interactive_mode(interpreter)
    except Exception as e:
        print(f"Error: {e}")
        if "--debug" in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def show_usage():
    """Show usage information."""
    print("""
Usage: python -m basic_ii.main [options] [file.bas]

Options:
  [no args]          - Start in interactive mode
  file.bas           - Load and run BASIC program
  --trace            - Enable trace mode (show each line)
  --debug            - Enable debug mode (show stack traces)
  --help, -h         - Show this help message

Interactive Mode:
  Enter BASIC commands directly or numbered program lines
  Type HELP for command list
  Type BYE to exit

Examples:
  python -m basic_ii.main
  python -m basic_ii.main program.bas
  python -m basic_ii.main --trace program.bas
  python -m basic_ii.main --debug test.bas
""")


def main():
    """Main entry point."""
    # Parse command line arguments
    args = sys.argv[1:]
    
    # Check for help
    if "--help" in args or "-h" in args:
        show_usage()
        return
    
    # Check for trace mode
    trace = "--trace" in args
    if trace:
        args.remove("--trace")
    
    # Check for debug mode
    debug = "--debug" in args
    if debug:
        args.remove("--debug")
    
    # Create interpreter
    interpreter = Interpreter(debug=debug)
    
    # Determine mode
    if args:
        # File mode
        filename = args[0]
        run_program_file(interpreter, filename, trace=trace)
    else:
        # Interactive mode
        interactive_mode(interpreter)


if __name__ == "__main__":
    main()
