"""
FunLang REPL - Interactive Read-Eval-Print-Loop

A full-featured REPL for the FunLang functional programming language.

Features:
- Multi-line input support
- Command history
- Special commands (:help, :quit, :load, etc.)
- Variable persistence across evaluations
- Pretty printing of results
"""


import readline
import os
from typing import Any, Dict, Optional
from funlang_parser import compile_funlang, FunLangCompiler
from functional_vm import FunctionalVM, ASTNode, NodeType, let, seq
from functional_core import Maybe, Result, Some, Err


class REPL:
    """Interactive REPL for FunLang."""
    
    def __init__(self):
        self.compiler = FunLangCompiler()
        self.vm = FunctionalVM(debug=False)
        self.environment: Dict[str, Any] = {}
        self.history_file = os.path.expanduser("~/.funlang_history")
        self.multiline_buffer = []
        self.in_multiline = False
        
        # Set up readline
        self._setup_readline()
        
    def _setup_readline(self):
        """Configure readline for command history and completion."""
        try:
            if os.path.exists(self.history_file):
                readline.read_history_file(self.history_file)
            readline.set_history_length(1000)
        except (FileNotFoundError, PermissionError):
            pass
    
    def _save_history(self):
        """Save command history to file."""
        try:
            readline.write_history_file(self.history_file)
        except (FileNotFoundError, PermissionError):
            pass
    
    def print_banner(self):
        """Print welcome banner."""
        print("=" * 60)
        print("  FunLang REPL v1.0")
        print("  A Functional Programming Language")
        print("=" * 60)
        print("Type ':help' for help, ':quit' to exit")
        print()
    
    def print_help(self):
        """Print help message."""
        print("""
Available commands:
  :help              Show this help message
  :quit, :q, :exit   Exit the REPL
  :clear             Clear the screen
  :env               Show all defined variables
  :reset             Reset the environment
  :load <file>       Load and execute a FunLang file
  :type <expr>       Show the type of an expression (placeholder)
  :debug on|off      Enable/disable debug mode
  
Multi-line input:
  - Use '\\' at the end of a line to continue
  - Or just start typing, REPL will detect incomplete expressions
  
Examples:
  > 2 + 3
  > let double = fn x -> x * 2 in double 21
  > let add = fn a -> fn b -> a + b
  > :env
""")
    
    def show_environment(self):
        """Show all variables in the environment."""
        if not self.environment:
            print("(empty environment)")
        else:
            print("Environment:")
            for name, value in sorted(self.environment.items()):
                # Try to show a nice representation
                val_str = str(value)
                if len(val_str) > 50:
                    val_str = val_str[:47] + "..."
                print(f"  {name} = {val_str}")
    
    def reset_environment(self):
        """Reset the environment."""
        self.environment.clear()
        self.vm = FunctionalVM(debug=False)
        print("Environment reset.")
    
    def load_file(self, filename: str):
        """Load and execute a FunLang file."""
        try:
            with open(filename, 'r') as f:
                source = f.read()
            
            print(f"Loading {filename}...")
            result = self.evaluate(source)
            if result is not None:
                self.print_result(result)
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found")
        except Exception as e:
            print(f"Error loading file: {e}")
    
    def set_debug(self, mode: str):
        """Enable or disable debug mode."""
        if mode.lower() in ['on', 'true', '1']:
            self.vm.debug = True
            print("Debug mode: ON")
        elif mode.lower() in ['off', 'false', '0']:
            self.vm.debug = False
            print("Debug mode: OFF")
        else:
            print("Usage: :debug on|off")
    
    def handle_command(self, line: str) -> bool:
        """Handle special commands. Returns True if should continue, False to quit."""
        cmd = line.strip()
        
        if cmd in [':quit', ':q', ':exit']:
            return False
        
        elif cmd == ':help':
            self.print_help()
        
        elif cmd == ':clear':
            os.system('clear' if os.name != 'nt' else 'cls')
        
        elif cmd == ':env':
            self.show_environment()
        
        elif cmd == ':reset':
            self.reset_environment()
        
        elif cmd.startswith(':load '):
            filename = cmd[6:].strip()
            self.load_file(filename)
        
        elif cmd.startswith(':debug '):
            mode = cmd[7:].strip()
            self.set_debug(mode)
        
        elif cmd.startswith(':type '):
            expr = cmd[6:].strip()
            print("Type inference not yet implemented")
        
        else:
            print(f"Unknown command: {cmd}")
            print("Type ':help' for available commands")
        
        return True
    
    def is_complete_expression(self, source: str) -> bool:
        """Check if the source code is a complete expression."""
        # Simple heuristic: count opening and closing brackets/parens
        # This is not perfect but works for most cases
        
        open_parens = source.count('(') - source.count(')')
        open_brackets = source.count('[') - source.count(']')
        
        # Check for incomplete let/if/case
        lines = source.strip().split('\n')
        last_line = lines[-1].strip() if lines else ""
        
        # Keywords that suggest more input is needed
        incomplete_keywords = ['let', 'in', 'if', 'then', 'else', 'case', 'of', 'fn', '->']
        
        # If last line ends with these, we need more
        for kw in incomplete_keywords:
            if last_line.endswith(kw):
                return False
        
        # If brackets/parens are unbalanced, incomplete
        if open_parens != 0 or open_brackets != 0:
            return False
        
        # If line ends with operator or comma, incomplete
        if last_line.endswith((',', '+', '-', '*', '/', '=', '<', '>', '|')):
            return False
        
        return True
    
    def evaluate(self, source: str) -> Any:
        """Evaluate source code and return the result."""
        try:
            # Compile the source
            ast = self.compiler.compile(source)
            
            # Wrap in environment if we have stored variables
            if self.environment:
                # Build nested let expressions for each variable
                wrapped_ast = ast
                for name, value in self.environment.items():
                    # We can't easily re-inject runtime values into AST
                    # So we just run with the current VM state
                    pass
            
            # Run the program
            result = self.vm.run(ast)
            
            # Try to extract top-level let bindings
            self._extract_bindings(source, result)
            
            return result
            
        except SyntaxError as e:
            print(f"Syntax error: {e}")
            return None
        except Exception as e:
            print(f"Runtime error: {e}")
            import traceback
            if self.vm.debug:
                traceback.print_exc()
            return None
    
    def _extract_bindings(self, source: str, result: Any):
        """Extract top-level let bindings and add to environment."""
        # This is a simplified version - just parse let statements
        source = source.strip()
        if source.startswith('let ') and ' = ' in source:
            # Try to extract variable name
            try:
                parts = source.split('=', 1)
                if len(parts) == 2:
                    var_part = parts[0].replace('let', '').strip()
                    if ' ' not in var_part:  # Simple variable name
                        self.environment[var_part] = result
            except:
                pass
    
    def print_result(self, result: Any):
        """Pretty print a result."""
        if result is None:
            return
        
        # Handle special types
        if isinstance(result, Result):
            if result.is_err():
                print(f"Err: {result}")
            else:
                print(f"=> {result}")
        elif isinstance(result, Maybe):
            print(f"=> {result}")
        else:
            print(f"=> {result}")
    
    def get_prompt(self) -> str:
        """Get the appropriate prompt."""
        if self.in_multiline:
            return "... "
        return ">>> "
    
    def run(self):
        """Main REPL loop."""
        self.print_banner()
        
        try:
            while True:
                try:
                    # Get input
                    prompt = self.get_prompt()
                    line = input(prompt)
                    
                    # Handle empty lines
                    if not line.strip():
                        if self.in_multiline:
                            # Empty line in multiline mode - try to evaluate
                            source = '\n'.join(self.multiline_buffer)
                            self.multiline_buffer = []
                            self.in_multiline = False
                            
                            if source.strip():
                                result = self.evaluate(source)
                                if result is not None:
                                    self.print_result(result)
                        continue
                    
                    # Handle commands
                    if line.startswith(':'):
                        if not self.handle_command(line):
                            break
                        continue
                    
                    # Handle line continuation
                    if line.endswith('\\'):
                        self.multiline_buffer.append(line[:-1])
                        self.in_multiline = True
                        continue
                    
                    # Add to multiline buffer if in multiline mode
                    if self.in_multiline:
                        self.multiline_buffer.append(line)
                        source = '\n'.join(self.multiline_buffer)
                        
                        # Check if complete
                        if self.is_complete_expression(source):
                            self.multiline_buffer = []
                            self.in_multiline = False
                            
                            result = self.evaluate(source)
                            if result is not None:
                                self.print_result(result)
                        # Otherwise, continue collecting input
                        continue
                    
                    # Single line - check if it's complete
                    if not self.is_complete_expression(line):
                        self.multiline_buffer = [line]
                        self.in_multiline = True
                        continue
                    
                    # Evaluate single complete line
                    result = self.evaluate(line)
                    if result is not None:
                        self.print_result(result)
                
                except KeyboardInterrupt:
                    print("\nKeyboardInterrupt")
                    self.multiline_buffer = []
                    self.in_multiline = False
                    continue
                
                except EOFError:
                    print("\nExiting...")
                    break
        
        finally:
            self._save_history()
            print("Goodbye!")


def main():
    """Run the REPL."""
    repl = REPL()
    repl.run()


if __name__ == "__main__":
    main()
