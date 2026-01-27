
## Project: Extended Plugin System

Create a new plugin for the PL/0 compiler to make the plugin system
more flexible by introducing a configuration file for managing plugins and
their output filenames, rather than hardcoding them in `compiler_main.py`.
This will be presented as a task for you to implement, ensuring a modular
and maintainable solution.

This will help you get started with code.


### Task: Creating and Integrating a New Plugin with a Configuration File

We will develop a new plugin for the PL/0 compiler and enhance the system
to use a configuration file for managing plugins and their output filenames.
This will involve creating the plugin, updating the codebase to support a
config file, and modifying `compiler_main.py` to use this config instead
of the hardcoded file extension mapping.


#### Step 1: Create a New Plugin

We'll create a plugin called `VariableReportPlugin` that generates a report
listing all variables declared in the program, including their scope level.
The plugin will produce an output file named `variable_report.txt`.


```python
#!/usr/bin/env python3

from compiler_core import Plugin, ASTNode, CompilerContext, MessageCollector, Visitor, BlockNode, NestedBlockNode, AssignNode, CallNode, ReadNode, WriteNode, CompoundNode, IfNode, WhileNode, OperationNode, VariableNode, NumberNode

class VariableReportPlugin(Plugin):
    def __init__(self):
        super().__init__(
            "variable_report",
            "Generates a report of all declared variables and their scope levels",
            "1.0"
        )
        self.dependencies = ["static_analysis"]  # depends on static analysis for variable declarations
    
    def run(self, ast: ASTNode, context: CompilerContext, messages: MessageCollector) -> dict:
        analyzer = VariableReportAnalyzer(messages)
        report = analyzer.analyze(ast, context)
        context.generated_outputs["variable_report"] = "\n".join(report)
        return {"variable_count": len(report), "report_lines": report}

class VariableReportAnalyzer(Visitor):
    def __init__(self, messages: MessageCollector):
        self.messages = messages
        self.report = []
        self.current_scope_level = 0
    
    def analyze(self, ast: ASTNode, context: CompilerContext) -> list:
        ast.accept(self)
        return self.report
    
    def visit_block(self, node: BlockNode):
        self.current_scope_level += 1
        for var in node.variables:
            self.report.append(f"Variable '{var}' declared at scope level {self.current_scope_level}")
        for proc_name, proc_body in node.procedures:
            self.report.append(f"Procedure '{proc_name}' at scope level {self.current_scope_level}")
            proc_body.accept(self)
        node.statement.accept(self)
        self.current_scope_level -= 1
    
    def visit_nested_block(self, node: NestedBlockNode):
        self.current_scope_level += 1
        for var in node.variables:
            self.report.append(f"Variable '{var}' declared at scope level {self.current_scope_level}")
        for stmt in node.statements:
            stmt.accept(self)
        self.current_scope_level -= 1
    
    def visit_assign(self, node: AssignNode):
        node.expression.accept(self)
    
    def visit_call(self, node: CallNode):
        pass
    
    def visit_read(self, node: ReadNode):
        pass
    
    def visit_write(self, node: WriteNode):
        node.expression.accept(self)
    
    def visit_compound(self, node: CompoundNode):
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_if(self, node: IfNode):
        node.condition.accept(self)
        node.then_statement.accept(self)
    
    def visit_while(self, node: WhileNode):
        node.condition.accept(self)
        node.body.accept(self)
    
    def visit_operation(self, node: OperationNode):
        node.left.accept(self)
        node.right.accept(self)
    
    def visit_variable(self, node: VariableNode):
        pass
    
    def visit_number(self, node: NumberNode):
        pass
```

This plugin:
- Extends the `Plugin` class and depends on `static_analysis` to ensure variables
  are validated.
- Uses a `VariableReportAnalyzer` (a `Visitor`) to traverse the AST and collect
  variable declarations with their scope levels.
- Stores the report in `context.generated_outputs["variable_report"]` and returns
  metadata about the report.


#### Step 2: Create a Configuration File

To make the plugin system more flexible, we’ll introduce a JSON configuration file
to specify active plugins and their output file extensions. This replaces the
hardcoded `file_extensions` mapping in `compiler_main.py`.

```json
{
  "plugins": [
    {
      "name": "static_analysis",
      "enabled": true,
      "output_extension": null
    },
    {
      "name": "tac_generator",
      "enabled": true,
      "output_extension": ".tac"
    },
    {
      "name": "c_code_generator",
      "enabled": true,
      "output_extension": ".c"
    },
    {
      "name": "statement_counter",
      "enabled": true,
      "output_extension": "_statements.txt"
    },
    {
      "name": "variable_report",
      "enabled": true,
      "output_extension": "_variables.txt"
    }
  ]
}
```

This JSON file:
- Lists each plugin by name.
- Specifies whether the plugin is enabled.
- Defines the output file extension (if any) for the plugin’s
  output in `context.generated_outputs`.


#### Step 3: Update `builtin_plugins.py` to Register the New Plugin

Modify `builtin_plugins.py` to include the new `VariableReportPlugin` in
the registration process.

```python
#!/usr/bin/env python3

from typing import Dict, Any, List, Set
from compiler_core import *
from variable_report_plugin import VariableReportPlugin

def register_builtin_plugins(registry):
    """Register all built-in plugins with the registry"""
    registry.register(StaticAnalysisPlugin())
    registry.register(TACGeneratorPlugin())
    registry.register(CCodeGeneratorPlugin())
    registry.register(StatementCounterPlugin())
    registry.register(VariableReportPlugin())


class StaticAnalysisPlugin(Plugin):
    def __init__(self):
        super().__init__(
            "static_analysis",
            "Analyzes variable usage and declarations",
            "1.0"
        )
    
    def run(self, ast, context, messages):
        analyzer = StaticAnalyzer(messages)
        return analyzer.analyze(ast)


class StaticAnalyzer(Visitor):
    def __init__(self, messages):
        self.messages = messages
        self.scopes = [set()]
        self.declared_vars = set()
        self.used_vars = set()
        self.undefined_vars = set()
        self.procedures = set()
        
    def analyze(self, ast: ASTNode) -> Dict[str, Any]:
        ast.accept(self)
        return {
            "declared_variables": list(self.declared_vars),
            "used_variables": list(self.used_vars),
            "undefined_variables": list(self.undefined_vars),
            "procedures": list(self.procedures)
        }
    
    def enter_scope(self):
        self.scopes.append(set())
    
    def exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()
    
    def declare_variable(self, name: str):
        self.scopes[-1].add(name)
        self.declared_vars.add(name)
    
    def use_variable(self, name: str):
        self.used_vars.add(name)
        for scope in reversed(self.scopes):
            if name in scope:
                return
        self.undefined_vars.add(name)
        self.messages.warning(f"Variable '{name}' used but not declared", source="StaticAnalysis")
    
    def visit_block(self, node: BlockNode):
        self.enter_scope()
        for var in node.variables:
            self.declare_variable(var)
        for proc_name, proc_body in node.procedures:
            self.procedures.add(proc_name)
            proc_body.accept(self)
        node.statement.accept(self)
        self.exit_scope()
    
    def visit_nested_block(self, node: NestedBlockNode):
        self.enter_scope()
        for var in node.variables:
            self.declare_variable(var)
        for stmt in node.statements:
            stmt.accept(self)
        self.exit_scope()
    
    def visit_assign(self, node: AssignNode):
        self.use_variable(node.var_name)
        node.expression.accept(self)
    
    def visit_call(self, node: CallNode):
        if node.proc_name not in self.procedures:
            self.messages.warning(f"Procedure '{node.proc_name}' called but not declared", source="StaticAnalysis")
    
    def visit_read(self, node: ReadNode):
        self.use_variable(node.var_name)
    
    def visit_write(self, node: WriteNode):
        node.expression.accept(self)
    
    def visit_compound(self, node: CompoundNode):
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_if(self, node: IfNode):
        node.condition.accept(self)
        node.then_statement.accept(self)
    
    def visit_while(self, node: WhileNode):
        node.condition.accept(self)
        node.body.accept(self)
    
    def visit_operation(self, node: OperationNode):
        node.left.accept(self)
        node.right.accept(self)
    
    def visit_variable(self, node: VariableNode):
        self.use_variable(node.name)
    
    def visit_number(self, node: NumberNode):
        pass


class TACGeneratorPlugin(Plugin):
    def __init__(self):
        super().__init__(
            "tac_generator",
            "Generates Three-Address Code",
            "1.0"
        )        
        self.dependencies = ["static_analysis"]
    
    def run(self, ast, context, messages):
        generator = TACGenerator(messages)
        tac_code = generator.generate(ast)
        context.generated_outputs["tac_code"] = "\n".join(tac_code)
        return {"generated": True, "instructions": len(tac_code)}


class TACGenerator(Visitor):
    def __init__(self, messages: MessageCollector):
        self.messages = messages
        self.code = []
        self.temp_counter = 0
        self.label_counter = 0
    
    def generate(self, ast: ASTNode) -> List[str]:
        ast.accept(self)
        return self.code
    
    def new_temp(self) -> str:
        temp = f"t{self.temp_counter}"
        self.temp_counter += 1
        return temp
    
    def new_label(self) -> str:
        label = f"L{self.label_counter}"
        self.label_counter += 1
        return label
    
    def visit_block(self, node: BlockNode):
        for var in node.variables:
            self.code.append(f"DECLARE {var}")
        for proc_name, proc_body in node.procedures:
            self.code.append(f"PROC {proc_name}:")
            proc_body.accept(self)
            self.code.append(f"ENDPROC {proc_name}")
        node.statement.accept(self)
    
    def visit_assign(self, node: AssignNode):
        expr_result = node.expression.accept(self)
        self.code.append(f"{node.var_name} := {expr_result}")
    
    def visit_call(self, node: CallNode):
        self.code.append(f"CALL {node.proc_name}")
    
    def visit_read(self, node: ReadNode):
        self.code.append(f"READ {node.var_name}")
    
    def visit_write(self, node: WriteNode):
        expr_result = node.expression.accept(self)
        self.code.append(f"WRITE {expr_result}")
    
    def visit_compound(self, node: CompoundNode):
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_nested_block(self, node: NestedBlockNode):
        for var in node.variables:
            self.code.append(f"DECLARE {var}")
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_if(self, node: IfNode):
        cond_result = node.condition.accept(self)
        else_label = self.new_label()
        self.code.append(f"IF NOT {cond_result} GOTO {else_label}")
        node.then_statement.accept(self)
        self.code.append(f"LABEL {else_label}")
    
    def visit_while(self, node: WhileNode):
        start_label = self.new_label()
        end_label = self.new_label()
        self.code.append(f"LABEL {start_label}")
        cond_result = node.condition.accept(self)
        self.code.append(f"IF NOT {cond_result} GOTO {end_label}")
        node.body.accept(self)
        self.code.append(f"GOTO {start_label}")
        self.code.append(f"LABEL {end_label}")
    
    def visit_operation(self, node: OperationNode):
        left_result = node.left.accept(self)
        right_result = node.right.accept(self)
        temp = self.new_temp()
        self.code.append(f"{temp} := {left_result} {node.operator} {right_result}")
        return temp
    
    def visit_variable(self, node: VariableNode):
        return node.name
    
    def visit_number(self, node: NumberNode):
        return str(node.value)


class CCodeGeneratorPlugin(Plugin):
    def __init__(self):
        super().__init__(
            "c_code_generator",
            "Generates C code from the AST",
            "1.0"
        )
        self.dependencies = ["static_analysis"]
    
    def run(self, ast, context, messages):
        generator = CCodeGenerator(messages)
        c_code = generator.generate(ast)
        context.generated_outputs["c_code"] = c_code
        return {"generated": True, "lines": len(c_code.split('\n'))}


class CCodeGenerator(Visitor):
    def __init__(self, messages: MessageCollector):
        self.messages = messages
        self.code = []
        self.indent_level = 0
    
    def generate(self, ast: ASTNode) -> str:
        self.code.append("#include <stdio.h>")
        self.code.append("")
        self.code.append("int main() {")
        self.indent_level += 1
        ast.accept(self)
        self.indent_level -= 1
        self.code.append("    return 0;")
        self.code.append("}")
        return "\n".join(self.code)
    
    def add_line(self, line: str):
        self.code.append("    " * self.indent_level + line)
    
    def visit_block(self, node: BlockNode):
        for var in node.variables:
            self.add_line(f"int {var};")
        for proc_name, proc_body in node.procedures:
            self.add_line(f"void {proc_name}() {{")
            self.indent_level += 1
            proc_body.accept(self)
            self.indent_level -= 1
            self.add_line("}")
        node.statement.accept(self)
    
    def visit_assign(self, node: AssignNode):
        expr_code = node.expression.accept(self)
        self.add_line(f"{node.var_name} = {expr_code};")
    
    def visit_call(self, node: CallNode):
        self.add_line(f"{node.proc_name}();")
    
    def visit_read(self, node: ReadNode):
        self.add_line(f"scanf(\"%d\", &{node.var_name});")
    
    def visit_write(self, node: WriteNode):
        expr_code = node.expression.accept(self)
        self.add_line(f"printf(\"%d\\n\", {expr_code});")
    
    def visit_compound(self, node: CompoundNode):
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_nested_block(self, node: NestedBlockNode):
        for var in node.variables:
            self.add_line(f"int {var};")
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_if(self, node: IfNode):
        cond_code = node.condition.accept(self)
        self.add_line(f"if ({cond_code}) {{")
        self.indent_level += 1
        node.then_statement.accept(self)
        self.indent_level -= 1
        self.add_line("}")
    
    def visit_while(self, node: WhileNode):
        cond_code = node.condition.accept(self)
        self.add_line(f"while ({cond_code}) {{")
        self.indent_level += 1
        node.body.accept(self)
        self.indent_level -= 1
        self.add_line("}")
    
    def visit_operation(self, node: OperationNode):
        left_code = node.left.accept(self)
        right_code = node.right.accept(self)
        return f"({left_code} {node.operator} {right_code})"
    
    def visit_variable(self, node: VariableNode):
        return node.name
    
    def visit_number(self, node: NumberNode):
        return str(node.value)
```

Changes:
- Imported `VariableReportPlugin` from `variable_report_plugin.py`.
- Added `registry.register(VariableReportPlugin())` to `register_builtin_plugins`.


#### Step 4: Update `compiler_main.py` to Use the Configuration File

Modify `compiler_main.py` to load the plugin configuration from `plugins_config.json`
and use it to manage plugin output filenames, replacing the hardcoded `file_extensions`
mapping. Also add support for loading the config file via a command-line argument.

```python
#!/usr/bin/env python3

import sys
import os
import json
from typing import Dict, Any

from compiler_core import *
from plugin_system import PluginRegistry
from builtin_plugins import register_builtin_plugins


class PL0Compiler:
    def __init__(self):
        self.messages = MessageCollector()
        self.registry = PluginRegistry()
        self.plugin_config = {}
        
        # Register built-in plugins
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
    
    def load_plugin_config(self, config_path: str):
        if not os.path.exists(config_path):
            self.messages.warning(f"Plugin config file not found: {config_path}")
            return
        try:
            with open(config_path, 'r') as f:
                self.plugin_config = json.load(f)
            for plugin in self.plugin_config.get("plugins", []):
                name = plugin.get("name")
                enabled = plugin.get("enabled", True)
                if name in self.registry.plugins:
                    self.registry.enable_plugin(name, enabled)
                    self.messages.info(f"Set plugin {name} enabled={enabled}")
        except json.JSONDecodeError as e:
            self.messages.error(f"Failed to parse plugin config: {e}", source="Compiler")
    
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
                     plugins_dir: str = None, plugin_config: str = None, list_plugins: bool = False):
        compiler = PL0Compiler()
        
        if debug:
            compiler.enable_debug()
        
        # Load plugins -- if directory specified
        if plugins_dir:
            compiler.load_plugins(plugins_dir)
        
        # Load plugin configuration
        if plugin_config:
            compiler.load_plugin_config(plugin_config)
        
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
        # Write outputs based on plugin configuration
        for output_name, content in result["outputs"].items():
            # Find the plugin config with this output
            extension = None
            for plugin in self.plugin_config.get("plugins", []):
                if plugin["name"] == output_name or plugin.get("output_key") == output_name:
                    extension = plugin.get("output_extension")
                    break
            if extension is None:
                extension = f"_{output_name}.txt"  # Fallback
            output_file = os.path.join(output_dir, f"{base_name}{extension}")
            
            with open(output_file, 'w') as file:
                file.write(content)
            print(f"Generated {output_name.replace('_', ' ')}: {output_file}")
        
        # Copy original source
        self._copy_source(input_filename, output_dir, base_name)
        
        # Create summary
        self._create_summary(result, input_filename, output_dir, base_name)
    
    def _copy_source(self, input_filename, output_dir, base_name):
        source_copy_path = os.path.join(output_dir, f"{base_name}_source.p")
        try:
            with open(input_filename, 'r') as source:
                with open(source_copy_path, 'w') as copy:
                    copy.write(source.read())
            print(f"Copied source: {source_copy_path}")
        except IOError:
            pass  # Don't fail if we can't copy source
    
    def _create_summary(self, result, input_filename, output_dir, base_name):
        summary_path = os.path.join(output_dir, f"{base_name}_summary.txt")
        with open(summary_path, 'w') as summary:
            summary.write(f"PL/0 Compilation Summary for {input_filename}\n")
            summary.write("=" * 50 + "\n\n")
            summary.write(f"Input file: {input_filename}\n")
            summary.write(f"Compilation date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            summary.write(f"Output directory: {output_dir}\n\n")
            
            summary.write("Generated Files:\n")
            for output_name in result["outputs"]:
                extension = None
                for plugin in self.plugin_config.get("plugins", []):
                    if plugin["name"] == output_name or plugin.get("output_key") == output_name:
                        extension = plugin.get("output_extension")
                        break
                if extension is None:
                    extension = f"_{output_name}.txt"
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
        print("Usage: compiler_main.py <input_filename> [output_filename] [--debug] [--plugins <directory>] [--config <config_file>] [--list-plugins]", file=sys.stderr)
        sys.exit(1)
    
    input_filename = sys.argv[1]
    output_filename = None
    debug = False
    plugins_dir = None
    plugin_config = None
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
        elif arg == "--config":
            if i + 1 < len(sys.argv):
                plugin_config = sys.argv[i + 1]
                i += 1
            else:
                print("Error: --config requires a file argument", file=sys.stderr)
                sys.exit(1)
        else:
            output_filename = arg
        i += 1
    
    # Normalise paths
    if plugins_dir:
        plugins_dir = os.path.join(os.path.dirname(__file__), plugins_dir)
    if plugin_config:
        plugin_config = os.path.join(os.path.dirname(__file__), plugin_config)
    
    PL0Compiler.compile_file(input_filename, output_filename, debug, plugins_dir, plugin_config, list_plugins)


if __name__ == "__main__":
    main()
```

Changes:
- Added `plugin_config` attribute to `PL0Compiler` to store the configuration.
- Added `load_plugin_config` method to read the JSON config file and enable/disable plugins.
- Modified `compile_file` to accept a `plugin_config` argument for the config file path.
- Updated `_write_outputs` to use the config file for output extensions instead of the
  hardcoded `file_extensions` mapping.
- Updated `_create_summary` to use the config file for output extensions.
- Modified `main` to handle a new `--config` command-line argument for specifying the config file path.


#### Step 5: Test the Plugin

Test the new plugin:
```pascal
var x, y;
begin
    x := 5;
    begin
        var z;
        z := x + 3;
    end;
end.
```

Running the compiler with:
```
python3 compiler_main.py input.p --config plugins_config.json --debug
```

The `VariableReportPlugin` will generate a `variable_report.txt` file in the output
directory with content like:
```
Variable 'x' declared at scope level 1
Variable 'y' declared at scope level 1
Variable 'z' declared at scope level 2
```


#### Summary of Changes

1. *New Plugin*: Created `VariableReportPlugin` to generate a variable report.
2. *Configuration File*: Introduced `plugins_config.json` to manage plugins and
   their output extensions.
3. *Updated `builtin_plugins.py`*: Added registration for the new plugin.
4. *Updated `compiler_main.py`*: Replaced hardcoded file extensions with config-based
   handling and added support for loading the config file.
5. *Benefits*:
   - The config file makes it easy to enable/disable plugins and specify output
     extensions without modifying code.
   - New plugins can be added by updating the config file and registering them
     (either in `builtin_plugins.py` or via the plugin directory).
   - The system is now more modular and easier to maintain.

