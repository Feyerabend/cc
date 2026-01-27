
## An Expanded Compiler

The updated `compiler.py` builds upon the previous version by introducing a modular
plugin architecture, enhanced error handling, support for nested blocks, Three-Address
Code (TAC) generation, and static analysis, while maintaining the core functionality
of compiling a PL/0-like language to C code. This follow-up focuses on the new
features and extensions, avoiding repetition of the previous description. It covers
the enhanced compilation process, new components (e.g., plugins, `NestedBlockNode`,
`MessageCollector`), and how they improve the compiler’s flexibility, robustness,
and utility.


### Compilation Process

The expanded compiler retains the core pipeline—lexing, parsing, semantic analysis,
and code generation—but introduces a *plugin-based architecture* to make the compiler
extensible.

1. *Lexing with Improved Messaging*: The `Lexer` uses a `MessageCollector` for
   structured error and debug messages.

2. *Parsing with Nested Blocks*: The `PackratParser` now supports `NestedBlockNode`
   for local variable declarations within `begin .. end` blocks.

3. *Plugin-Based Processing*: A `PluginRegistry` manages plugins for static analysis,
   TAC generation, C code generation, and potential user-defined optimisations.

4. *Static Analysis and TAC Generation*: New plugins analyze variable usage and
   generate intermediate TAC, enhancing debugging and optimisation capabilities.

5. *Code Reconstruction*: A `CodeReconstructor` can regenerate PL/0 source code
   from an AST, useful for saving optimised versions.

6. *Output Options*: The compiler generates both C code and TAC, with an option
   to save optimised PL/0 source code.


### Extended Components


#### 1. *MessageCollector and CompilerMessage*

The `MessageCollector` class replaces direct `print` statements for debugging
and error reporting, providing a structured way to log messages with different
severity levels (`DEBUG`, `INFO`, `WARNING`, `ERROR`).

- *Key Features*:
  - Messages include a level, position, source (e.g., "Lexer", "Parser"), and
    optional context.
  - Supports enabling/disabling debug messages via `enable_debug`.
  - Tracks errors to determine compilation success (`has_errors`).
  - Example: `[ERROR] in Parser at position 5: Expected 'then'` provides precise
    diagnostics.
- *Improvement*: Replaces ad-hoc `print` statements in the original, making it
  easier to filter messages, integrate with tools, or extend for IDE support.


#### 2. *NestedBlockNode*

The new `NestedBlockNode` extends the AST to support variable declarations
within `begin .. end` blocks, enabling local scoping in compound statements.

- *Key Features*:
  - Represents a block with local variables and statements (e.g., `begin var x; x := 5; end`).
  - Handled by the parser’s `statement` method, which checks for `var` declarations after `begin`.
  - Supported by the `CCompiler` and `CodeReconstructor` for correct scoping and code generation.
- *Improvement*: The original compiler only allowed variable declarations in top-level `BlockNode`s.
  This extension supports more flexible scoping, aligning with modern programming language semantics.


#### 3. *PluginRegistry and Plugin System*

The `PluginRegistry` introduces a modular architecture, allowing the compiler to execute a series
of plugins (e.g., static analysis, TAC generation, C code generation) in a configurable order.

- *Key Features*:
  - Plugins are subclasses of the abstract `Plugin` class or callable functions decorated with `@plugin`.
  - Built-in plugins include `StaticAnalysisPlugin`, `TACGeneratorPlugin`, and `CCodeGeneratorPlugin`.
  - Supports loading external plugins from Python files in a specified directory (`load_plugins`).
  - Plugins store results in `CompilerContext.plugin_results` and outputs (e.g., C code, TAC) in `generated_outputs`.
  - Example: `registry.set_order(["static_analysis", "tac_generator", "c_generator"])` defines the execution sequence.
- *Improvement*: The original compiler had a fixed `CCompiler` for code generation. The plugin system
  decouples processing stages, enabling extensibility (e.g., adding optimization plugins) and reusability.


#### 4. *StaticAnalysisPlugin and StaticAnalyzer*

The `StaticAnalysisPlugin` runs a `StaticAnalyzer` visitor to perform semantic checks, identifying
undeclared variables and undefined procedures.

- *Key Features*:
  - Tracks declared variables, used variables, undefined variables, and procedures using a scope stack.
  - Issues warnings for issues like undeclared variables (e.g., `WARNING: Variable 'x' used but not declared`).
  - Returns analysis results (e.g., lists of declared and undefined variables) stored in `CompilerContext.plugin_results`.
- *Improvement*: The original lacked semantic analysis, risking runtime errors from undeclared variables.
  This plugin adds robustness by catching errors early.


#### 5. *TACGeneratorPlugin and TACGenerator*

The `TACGeneratorPlugin` introduces an intermediate representation (Three-Address Code) via the
`TACGenerator` visitor, useful for debugging, optimisation, or alternative backends.

- *Key Features*:
  - Generates TAC instructions like `t0 := x + y`, `IF_FALSE t0 GOTO L1`, or `WRITE x`.
  - Uses temporary variables (`t0`, `t1`, etc.) and labels (`L1`, `L2`, etc.) for control flow.
  - Outputs TAC to a `.tac` file alongside the C code.
  - Example for `x := y + 1`:
    ```
    t0 := y + 1
    x := t0
    ```
- *Improvement*: The original directly generated C code. TAC provides a simpler, platform-independent
  intermediate form, facilitating optimizations or targeting different backends.


#### 6. *CodeReconstructor*

The `CodeReconstructor` visitor regenerates PL/0 source code from an AST, primarily for saving
optimised versions of the program.

- *Key Features*:
  - Traverses the AST to produce formatted PL/0 code, preserving structure and indentation.
  - Handles all node types, including `NestedBlockNode`, with proper syntax (e.g., `begin var x; x := 5; end`).
  - Used when `--save-optimized` is specified to write optimized PL/0 code to a `_optimized.pl0` file.
- *Improvement*: The original lacked the ability to reconstruct source code. This feature
  supports debugging and optimisation workflows by allowing inspection of transformed ASTs.


#### 7. *Enhanced PL0Compiler*

The `PL0Compiler` class is revamped to orchestrate the plugin-based compilation process.

- *Key Features*:
  - Manages a `MessageCollector` and `PluginRegistry`.
  - Supports `compile_string` for in-memory compilation, returning a dictionary with AST,
    context, messages, outputs, and plugin results.
  - `compile_file_with_optimization` adds support for saving optimized source code and
    reporting optimization statistics.
  - Command-line options: `--debug`, `--plugins <directory>`, `--save-optimized`.
- *Improvement*: Replaces the original `PL0Compiler.compile_file` with a more flexible
  interface, supporting plugins, TAC output, and optimized source code generation.


#### 8. *Extended CompilerContext*

The `CompilerContext` is enhanced to support plugins and additional outputs.

- *New Features*:
  - Stores `plugin_results` (e.g., static analysis results) and `generated_outputs`
    (e.g., `c_code`, `tac_code`).
  - Tracks `optimized_ast` for optimized source code reconstruction.
  - Adds `block_counter` for potential future use (e.g., unique block identifiers).
- *Improvement*: The original context only managed scopes and C code. The new version
  supports multiple outputs and plugin extensibility.


#### 9. *Visitor Pattern Enhancements*

The Visitor pattern is extended to support `NestedBlockNode` and new plugins
(`StaticAnalyzer`, `TACGenerator`, `CodeReconstructor`).

- *New Visitor Methods*:
  - `visit_nested_block` in `CCompiler`, `StaticAnalyzer`, `TACGenerator`, and
    `CodeReconstructor` handles local variable declarations in nested blocks.
- *Improvement*: The original Visitor pattern only supported C code generation.
  The extended pattern supports multiple tasks (analysis, TAC generation, code
  reconstruction), making it more versatile.


### Example Workflow with New Features

For an input file `example.pl0`:
```
var x;
begin
    var y;
    y := 5;
    ! y;
end;
end.
```

1. *Lexing*:
   - Tokens include `("var", "kw")`, `("y", "id")`, etc., with messages logged via `MessageCollector`.
   - Example message: `[DEBUG] in Lexer at position 10: Lexer produced token: 'y' (id)`.

2. *Parsing*:
   - AST includes a `BlockNode` with a `NestedBlockNode` for the `begin ... end` block containing `y`.
   - Example message: `[DEBUG] in Parser at position 5: Parsed nested block with variables`.

3. *Plugin Execution*:
   - *Static Analysis*: Warns if `y` is used outside its scope; reports declared variables (`x`, `y`).
   - *TAC Generation*:
     ```
     DECLARE x
     DECLARE y
     y := 5
     WRITE y
     ```
   - *C Code Generation*:
     ```c
     #include <stdio.h>

     int x;

     int main() {
         {
             int y;
             y = 5;
             printf("%d\n", y);
         }
         return 0;
     }
     ```

4. *Output*:
   - C code written to `example.c`.
   - TAC written to `example.tac`.
   - If `--save-optimized` is used, optimised PL/0 code (if an optimiser plugin exists)
     is saved to `example_optimized.pl0`.


### Why Extend with These Features?

- *Plugin Architecture*: Enables extensibility (e.g., adding optimisers, new backends) without modifying core code.
- *Nested Blocks*: Supports local variable scoping, improving language expressiveness.
- *Static Analysis*: Catches semantic errors early, enhancing reliability.
- *TAC Generation*: Provides an intermediate representation for debugging, optimisation, or alternative code generation.
- *Improved Diagnostics*: Structured messages with `MessageCollector` make debugging easier.
- *Code Reconstruction*: Allows inspection and reuse of optimised ASTs.


### Limitations and Potential Improvements

- *Optimisation Plugin*: The code references an `optimized_ast` but lacks! a built-in optimiser plugin.
  Adding one (e.g., for constant folding) would complete the optimisation pipeline.
- *Error Recovery*: The parser stops on the first error; adding recovery mechanisms could
  allow processing to continue for multiple errors.
- *Plugin Configuration*: The plugin order is fixed at initialisation; dynamic configuration
  (e.g., via a config file, or other automatic ways) could improve flexibility.
- *TAC Utilisation*: TAC is generated but not used for optimisation or alternative backends;
  integrating it with an optimiser or another code generator would add value.


### Conclusion

The enhanced `compiler.py` extends the original by introducing a plugin-based architecture, nested block
support, static analysis, TAC generation, and source code reconstruction. These additions make the compiler
more modular, robust, and suitable for advanced use cases like optimisation and debugging. The plugin
system and `MessageCollector` improve extensibility and diagnostics, while `NestedBlockNode` and
`TACGenerator` enhance the language’s capabilities and provide an intermediate representation. This
version is a foundation for further extensions, such as custom (built-in) optimisers or alternative backends,
while maintaining the simplicity of the original PL/0-like compiler.

