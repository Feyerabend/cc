
## PL/0 Compiler with Advanced Plugin System

This version of the PL/0-like compiler, implemented in `compiler_main.py` and supported
by multiple plugin files, enhances the previous iterations by introducing advanced code
generation, performance profiling, and detailed analysis capabilities. Building on a
robust plugin architecture, nested block support, and Three-Address Code (TAC) generation,
this version adds Python code generation, optimised C code generation, performance profiling,
and (test plugin) statement counting, all organised in a structured output directory.


### Compilation Pipeline

The compilation process follows a structured pipeline:

1. *Lexing and Parsing*: The `Lexer` and `PackratParser` (from `compiler_core.py`) tokenise
   and parse PL/0 source code into an Abstract Syntax Tree (AST), supporting nested blocks
   via `NestedBlockNode`.
2. *Plugin-Based Processing*: The `PluginRegistry` (from `plugin_system.py`) orchestrates
   plugins for static analysis, code generation, optimisation, and performance profiling,
   ensuring proper dependency resolution.
3. *Output Organisation*: Outputs are written to a `<basename>_compilation/` directory,
   including generated C code, Python code, TAC, performance reports, and a summary file.
4. *New Analyses and Code Generation*: Plugins provide cyclomatic complexity, statement
   counting, constant propagation, dead code elimination, and performance profiling,
   alongside generating both standard and optimised C code, Python code, and instrumented C
   code for runtime profiling.


### Components

#### 1. *Core Compiler (`compiler_main.py`)*

The `PL0Compiler` class manages the compilation process, integrating plugins and handling
output organisation.

- *Features*:
  - Reads PL/0 source code and produces an AST.
  - Supports command-line arguments for input/output files, debug mode, plugin directory,
    and plugin listing.
  - Creates a `<basename>_compilation/` directory for outputs (e.g., `program.c`, `program.py`,
    `program.tac`, `program_summary.txt`).
  - Generates a summary file with compilation details and plugin results.
  - Example directory structure for `program.p`:
    ```
    program_compilation/
    ├── program.c
    ├── program.py
    ├── program.tac
    ├── program_optimized.c
    ├── program_instrumented.c
    ├── program_ast.txt
    ├── program_optimizations.txt
    ├── program_opt_c_analysis.txt
    ├── program_py_opt_analysis.txt
    ├── program_perf.txt
    ├── program_statements.txt
    ├── program_source.p
    └── program_summary.txt
    ```


#### 2. *Plugin System (`plugin_system.py`)*

The `PluginRegistry` supports dynamic plugin loading and dependency resolution.

- *Features*:
  - Loads plugins from a specified directory, supporting both class-based and function-based plugins.
  - Resolves dependencies using topological sorting to prevent circular dependencies.
  - Allows enabling/disabling plugins and manual execution order specification.
  - Integrates plugins seamlessly with the compiler pipeline.


#### 3. *Built-in Plugins (`builtin_plugins.py`)*

Provides foundational plugins for static analysis, TAC generation, and standard C code generation.

- *StaticAnalysisPlugin*:
  - Analyses variable declarations and usage, reporting undefined variables and procedures.
  - Outputs: List of declared/used/undefined variables and procedures.
- *TACGeneratorPlugin*:
  - Generates Three-Address Code (TAC) for intermediate representation.
  - Outputs: `program.tac`.
- *CCodeGeneratorPlugin*:
  - Generates standard C code from the AST.
  - Outputs: `program.c`.


#### 4. *Statement Counter Plugin (`test_plugin.py`)*

The `StatementCounterPlugin` counts executable statements in the AST.

- *Features*:
  - Counts `AssignNode`, `CallNode`, `ReadNode`, `WriteNode`, `IfNode`, and `WhileNode` as statements.
  - Outputs a report in `program_statements.txt` (e.g., "Total statements: 5").
  - Depends on `static_analysis` to ensure variable checks are performed first.


#### 5. *Optimised C Code Generator Plugin (`opt_c_generator.py`)*

The `OptimizationCGeneratorPlugin` performs optimisation analysis and generates optimised C code.

- *Features*:
  - Applies constant propagation and dead code elimination via `ASTOptimizer`.
  - Generates optimised C code using `OptimizedCCodeGenerator`.
  - Outputs:
    - `program_optimized.c`: Optimised C code.
    - `program_opt_c_analysis.txt`: Optimisation report detailing constant propagation and dead code elimination.
  - Depends on `static_analysis`.


#### 6. *Python Code Generator Plugin (`python_generator.py`)*

The `PythonGeneratorPlugin` performs optimisation analysis and generates Python code.

- *Features*:
  - Similar optimisation passes as `opt_c_generator.py` (constant propagation, dead code elimination).
  - Generates Python code with proper operator mapping (e.g., PL/0 `=` becomes `==`).
  - Outputs:
    - `program.py`: Executable Python code.
    - `program_py_opt_analysis.txt`: Optimisation report.
  - Depends on `static_analysis`.


#### 7. *Performance Profiler Plugin (`perf_plugin.py`)*

The `PerformanceProfilerPlugin` analyses performance characteristics and generates instrumented C code.

- *Features*:
  - Estimates time complexity (e.g., O(n), O(n²)) based on loop nesting.
  - Tracks space complexity, operation count, stack depth, memory operations, I/O operations, and procedure calls.
  - Identifies performance hotspots (e.g., heavy procedures, nested loops).
  - Generates recommendations (e.g., batch I/O, reduce loop nesting).
  - Produces instrumented C code with profiling macros for runtime metrics (execution time, operations per second).
  - Outputs:
    - `program_perf.txt`: Performance analysis report.
    - `program_instrumented.c`: Instrumented C code.
  - Depends on `static_analysis`.


#### 8. *Summary File Generation*

The `compile_file` method generates a `program_summary.txt` file summarising the compilation.

- *Features*:
  - Lists input file, compilation date, output directory, and generated files.
  - Includes plugin results (e.g., statement counts, optimisation metrics, performance complexity).
  - Example:
    ```
    PL/0 Compilation Summary for program.p
    ==================================================
    Input file: program.p
    Compilation date: 2025-08-25 17:28:00
    Output directory: program_compilation/

    Generated Files:
      • program.c - Compiled C code
      • program.py - Compiled Python code
      • program.tac - Three-Address Code
      • program_optimized.c - Optimised C code
      • program_instrumented.c - Instrumented C code
      • program_ast.txt - AST Structure
      • program_optimizations.txt - Optimisation Hints
      • program_opt_c_analysis.txt - C Optimisation Analysis
      • program_py_opt_analysis.txt - Python Optimisation Analysis
      • program_perf.txt - Performance Profile
      • program_statements.txt - Statement Count
      • program_source.p - Original Source

    Plugin Analysis Results:
      • static_analysis:
        - declared_variables: ['x', 'y']
        - used_variables: ['x']
      • statement_counter:
        - total_statements: 3
      • optimization_c_generator:
        - optimizations_applied: {'constant_propagation': 2, 'dead_code_elimination': 1}
      • python_generator:
        - optimizations_applied: {'constant_propagation': 2, 'dead_code_elimination': 1}
      • performance_profiler:
        - time_complexity: 'n'
        - space_complexity: '2'
    ```


#### 9. *Visitor Pattern Enhancements*

The Visitor pattern in `compiler_core.py` supports all plugins by defining methods for each
AST node type (`BlockNode`, `NestedBlockNode`, `AssignNode`, etc.), enabling flexible analysis
and code generation.


### Example

For an input file `program.p`:
```
var x, fact, i;
begin
    ? x;
    fact := 1;
    i := 1;
    while i <= x do
    begin
        fact := fact * i;
        i := i + 1
    end;
    if fact > 100 then
        ! fact
end.
```

1. *Lexing and Parsing*: Produces an AST with a `BlockNode` containing variables `x`,
   `fact`, `i`, a `CompoundNode` with a `ReadNode`, two `AssignNodes`, a `WhileNode`
   with a `NestedBlockNode` (containing two `AssignNodes`), and an `IfNode` with a `WriteNode`.

2. *Plugin Execution*:
   - *Static Analysis*: Reports declared (`x`, `fact`, `i`) and used variables (`x`, `fact`, `i`),
     with no undefined variables.
   - *Statement Counter*: Counts 5 statements (`ReadNode`, two `AssignNodes`, `WhileNode`, `IfNode`)
   - *Optimisation (C and Python)*: No constant folding or dead code elimination is applied,
     as the expressions (e.g., `fact * i`, `i <= x`) are not constant.
   - *Performance Profiler*: Estimates O(n) time complexity due to single `WhileNode`,
     tracks stack depth of 2 (due to nested block), and generates instrumented C code with profiling macros.
   - *TAC and Standard C Code*: Generates `program.tac` and `program.c`.

3. *Output*:
   - Directory `program_compilation/` contains all generated files.
   - Console output lists files and debug results (if `--debug` is enabled).


### Why These Enhancements?

- *Organised Outputs*: The `<basename>_compilation/` directory and summary file centralise outputs,
  improving usability.
- *Multi-Language Support*: Python code generation broadens the compiler’s applicability.
- *Optimisation*: Constant propagation and dead code elimination improve generated code efficiency.
- *Performance Insights*: The profiler identifies bottlenecks and provides actionable recommendations.
- *Extensibility*: The plugin system supports adding new analyses or code generators without
  modifying the core compiler. (You might though have to change the file extensions.)


### Limitations and Potential Improvements (Read: Projects!)

- *Optimisation Application*: While optimisations are detected, applying them to transform the
  AST is incomplete in some plugins.
- *Performance Profiling*: Static analysis could be enhanced with dynamic profiling data integration.
- *Plugin Dependencies*: Adding version checking or conflict resolution would improve robustness.
- *Error Recovery*: The parser halts on errors; adding recovery could enhance usability.
- *Metrics*: Including compilation time or memory usage in the summary could aid performance analysis.

In general the programs could benefit from more dynamic approach to loading plugins: [project](./eplugins/).


### Conclusion

This PL/0 compiler, with its advanced plugin system, offers a robust platform for code analysis,
optimisation, and multi-language code generation. The addition of Python code generation, optimised
C code, performance profiling, and statement counting, alongside organised output management, makes
it a powerful tool for developers and educators. The extensible plugin architecture ensures it
can evolve with new features, maintaining its relevance for compiler development and learning.


