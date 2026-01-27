#!/usr/bin/env python3

import sys
import os
from typing import Dict, Any

from compiler_core import *
from plugin_system import PluginRegistry
from builtin_plugins import register_builtin_plugins


class PL0Compiler:
    def __init__(self):
        self.messages = MessageCollector()
        self.registry = PluginRegistry()
        
        # Register built-in plugins -- move?
        register_builtin_plugins(self.registry)
    
    def add_plugin(self, plugin: Plugin):
        self.registry.register(plugin)
    
    def add_plugin_function(self, name: str, func, description: str = "", 
                           version: str = "1.0", dependencies=None):
        self.registry.register_function(name, func, description, version, dependencies or [])
    
    def load_plugins(self, directory: str):
        if not os.path.exists(directory):
            self.messages.warning(f"Plugin directory not found: {directory}")
            return
        
        self.registry.load_from_directory(directory, self.messages)
    
    def enable_debug(self):
        self.messages.enable_debug(True)
    
    def list_plugins(self):
        plugins = self.registry.list_plugins()
        print("\nRegistered Plugins:")
        print("-" * 60)
        for plugin in plugins:
            status = "ENABLED" if plugin["enabled"] else "DISABLED"
            deps = ", ".join(plugin["dependencies"]) if plugin["dependencies"] else "None"
            print(f"Name: {plugin['name']}")
            print(f"  Description: {plugin['description']}")
            print(f"  Version: {plugin['version']}")
            print(f"  Status: {status}")
            print(f"  Dependencies: {deps}")
            print()
    
    def enable_plugin(self, name: str, enabled: bool = True):
        self.registry.enable_plugin(name, enabled)
    
    def compile_string(self, code: str) -> Dict[str, Any]:
        self.messages.clear()
        
        try:
            # Lexical analysis
            lexer = Lexer(code, self.messages)
            
            # Syntax analysis
            parser = PackratParser(lexer.tokens, self.messages)
            ast = parser.parse()
            
            # Create context and run plugins
            context = CompilerContext()
            context = self.registry.run_all(ast, context, self.messages)
            
            return {
                "success": not self.messages.has_errors(),
                "ast": ast,
                "context": context,
                "messages": self.messages.get_messages(),
                "outputs": context.generated_outputs,
                "plugin_results": context.plugin_results
            }
            
        except Exception as e:
            self.messages.error(f"Compilation failed: {str(e)}", source="Compiler")
            return {
                "success": False,
                "ast": None,
                "context": None,
                "messages": self.messages.get_messages(),
                "outputs": {},
                "plugin_results": {}
            }
    
    @staticmethod
    def compile_file(input_filename: str, output_filename: str = None, debug: bool = False, 
                     plugins_dir: str = None, list_plugins: bool = False):
        compiler = PL0Compiler()
        
        if debug:
            compiler.enable_debug()
        
        # Load plugins -- if directory specified
        if plugins_dir:
            compiler.load_plugins(plugins_dir)
        
        if list_plugins:
            compiler.list_plugins()
            return
        
        try:
            with open(input_filename, 'r') as file:
                code = file.read()
        except IOError as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
        
        if output_filename is None:
            output_filename = input_filename.rsplit('.', 1)[0] + ".c"
        
        result = compiler.compile_string(code)
        
        if result["success"]:
            # Create output directory based on input filename
            base_name = os.path.splitext(os.path.basename(input_filename))[0]
            output_dir = f"{base_name}_compilation"
            
            # Create the directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            print(f"Created compilation directory: {output_dir}/")
            
            # Write outputs
            compiler._write_outputs(result, base_name, output_dir, input_filename, output_filename)
            
            print(f"\nCompilation complete! All files saved to: {output_dir}/")
            
            # Show plugin results if debug enabled
            if debug and result["plugin_results"]:
                print("\nPlugin Results:")
                for name, results in result["plugin_results"].items():
                    print(f"  {name}: {results}")
                
        else:
            print("Compilation failed with errors:", file=sys.stderr)
            for msg in result["messages"]:
                if msg.level == MessageLevel.ERROR:
                    print(f"  {msg}", file=sys.stderr)
            sys.exit(1)
    
    def _write_outputs(self, result, base_name, output_dir, input_filename, output_filename):
        # File extension mapping
        file_extensions = {
            "documentation": ".md",
            "ast_structure": "_ast.txt",
            "optimization_hints": "_optimizations.txt",
            "optimization_analysis": "_opt_analysis.txt",
            "peephole_analysis": "_peephole.txt",
            "variable_report": "_variables.txt",
            "statement_report": "_statements.txt",
            "opt_c_code": "_optimized.c",
            "opt_c_analysis": "_opt_c_analysis.txt",
            "py_code": ".py",
            "py_opt_analysis": "_py_opt_analysis.txt",
            "perf_profile": "_perf.txt",
            "instr_c_code": "_instrumented.c"
        }

        # Write main outputs
        if "c_code" in result["outputs"]:
            c_output_path = os.path.join(output_dir, f"{base_name}.c")
            with open(c_output_path, 'w') as file:
                file.write(result["outputs"]["c_code"])
            print(f"Generated C code: {c_output_path}")

        # Rewrite!?
        if "tac_code" in result["outputs"]:
            tac_output_path = os.path.join(output_dir, f"{base_name}.tac")
            with open(tac_output_path, 'w') as file:
                file.write(result["outputs"]["tac_code"])
            print(f"Generated TAC code: {tac_output_path}")
        
        # Write other plugin outputs
        for output_name, content in result["outputs"].items():
            if output_name not in ["c_code", "tac_code"]:
                extension = file_extensions.get(output_name, f"_{output_name}.txt")
                output_file = os.path.join(output_dir, f"{base_name}{extension}")
                
                with open(output_file, 'w') as file:
                    file.write(content)
                print(f"Generated {output_name.replace('_', ' ')}: {output_file}")
        
        # Copy original source
        self._copy_source(input_filename, output_dir, base_name)
        
        # Create summary
        self._create_summary(result, input_filename, output_dir, base_name, file_extensions)
        
        # Also keep main C file in current directory for compatibility - skip?
        #if output_filename and "c_code" in result["outputs"]:
        #    with open(output_filename, 'w') as file:
        #        file.write(result["outputs"]["c_code"])
        #    print(f"Main C file also saved as: {output_filename}")


    # ? do we need more source
    def _copy_source(self, input_filename, output_dir, base_name):
        source_copy_path = os.path.join(output_dir, f"{base_name}_source.p")
        try:
            with open(input_filename, 'r') as source:
                with open(source_copy_path, 'w') as copy:
                    copy.write(source.read())
            print(f"Copied source: {source_copy_path}")
        except IOError:
            pass  # Don't fail if we can't copy source
    
    def _create_summary(self, result, input_filename, output_dir, base_name, file_extensions):
        summary_path = os.path.join(output_dir, f"{base_name}_summary.txt")
        with open(summary_path, 'w') as summary:
            summary.write(f"PL/0 Compilation Summary for {input_filename}\n")
            summary.write("=" * 50 + "\n\n")
            summary.write(f"Input file: {input_filename}\n")
            summary.write(f"Compilation date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            summary.write(f"Output directory: {output_dir}\n\n")
            
            summary.write("Generated Files:\n")
            for output_name in result["outputs"]:
                if output_name == "c_code":
                    summary.write(f"  • {base_name}.c - Compiled C code\n")
                elif output_name == "tac_code":
                    summary.write(f"  • {base_name}.tac - Three-Address Code\n")
                else:
                    extension = file_extensions.get(output_name, f"_{output_name}.txt")
                    summary.write(f"  • {base_name}{extension} - {output_name.replace('_', ' ').title()}\n")
            
            if result["plugin_results"]:
                summary.write("\nPlugin Analysis Results:\n")
                for plugin_name, plugin_data in result["plugin_results"].items():
                    summary.write(f"  • {plugin_name}:\n")
                    if isinstance(plugin_data, dict):
                        for key, value in plugin_data.items():
                            summary.write(f"    - {key}: {value}\n")
                    else:
                        summary.write(f"    - {plugin_data}\n")
        
        print(f"Generated summary: {summary_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: compiler_main.py <input_filename> [output_filename] [--debug] [--plugins <directory>] [--list-plugins]", file=sys.stderr)
        sys.exit(1)
    
    input_filename = sys.argv[1]
    output_filename = None
    debug = False
    plugins_dir = None
    list_plugins = False
    
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--debug":
            debug = True
        elif arg == "--list-plugins":
            list_plugins = True
        elif arg == "--plugins":
            if i + 1 < len(sys.argv):
                plugins_dir = sys.argv[i + 1]
                i += 1
            else:
                print("Error: --plugins requires a directory argument", file=sys.stderr)
                sys.exit(1)
        else:
            output_filename = arg
        i += 1
    # normalise plugins_dir, so Makefile can do whatever it wants
    plugins_dir = os.path.join(os.path.dirname(__file__), plugins_dir)
    PL0Compiler.compile_file(input_filename, output_filename, debug, plugins_dir, list_plugins)


if __name__ == "__main__":
    main()
