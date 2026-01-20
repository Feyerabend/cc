
## Hypothetical Preprocessing in Procedural Languages

In procedural programming language like Algol, Pascal or PL/0, a hypothetical
preprocessor can be used to provide additional capabilities and improvements in
how the code is written and interpreted before it's passed to the main compiler
or interpreter. Enhancing comments, could be a natural starting point for
preprocessing in out pseudo-language, but we can think more broadly about useful
features that could improve the developer experience and program functionality.


__1. Enhanced Comments (Meta-Comments):__

- Comment-based Directives: Allow comments to carry meta-information or directives that can
  influence how the code is processed, such as variable definitions, type information,
  compiler directives, or configuration settings.

- Example:
```
/* @define a 10 */
```

- These could allow the preprocessor to “define” constants or variables before the program
  is parsed, similar to #define in C-like languages.


__2. Macros and Inline Code Expansion:__

- Macro Substitution: Allow developers to define macros (or templates) that expand into
  reusable code blocks.

- Example:
```
/* @macro add_two(x) (x + 2) */
let result = add_two(5);
```

- The preprocessor could expand add_two(5) into (5 + 2) before compiling the program.


__3. Conditional Compilation (if statements in code):__

- Platform/Environment-Specific Code: Include code only for certain platforms or conditions.

- Example:
```
/* @if DEBUG */
let debug_message = "Debugging";
/* @endif */
```

- This could allow certain blocks of code to only be included in the output when the condition is met.


__4. Code Reordering and Optimizations__

- Rearranging Code: The preprocessor could optimise the code in certain ways before the main
  compiler gets it. For example, reordering function calls or moving definitions for better
  performance.

- Inlining Functions or Loop Unrolling: For performance reasons, certain functions could be
  automatically inlined if they meet certain conditions.


__5. Annotations or Documentation Generation:__

- Automatic Documentation: Comments or special annotations in the code could be processed to
  automatically generate documentation or additional files.

- Example:
```
/* @doc "This function calculates the factorial" */
function factorial(n) { ... }
```
- The preprocessor could then generate a markdown or HTML file with documentation for each function.


__6. Cross-Language Integration:__

- Foreign Function Interface (FFI): Allow the preprocessor to define bindings to external code
  written in other languages (like C).

- Example:
```
/* @ffi extern "C" "factorial(int n)" */
let result = factorial(5);
```

- This allows linking to code outside the PL/0 language.


### Implementing a Simple Preprocessor in Python

1. Define the Preprocessor

We would define a class that performs the preprocessing tasks. For simplicity, only handling
enhanced comments and basic macro substitution. It can be complicated pretty soon, handling
macros and the intension of macros.

```python
import re

class Preprocessor:
    def __init__(self):
        self.macros = {}

    def process(self, source_code):
        # 1: handle macro definitions and remove them from the source
        source_code = self._handle_macros(source_code)
        
        # 2: handle meta-comments (still, leave them for potential further processing)
        source_code = self._handle_meta_comments(source_code)
        
        return source_code

    # @macro
    def _handle_macros(self, code):
        # find /* @macro name(args) value */
        macro_pattern = re.compile(r"/\*\s*@macro\s+(\w+)\((.*?)\)\s+(.+?)\s*\*/", re.DOTALL)
        macros_found = re.findall(macro_pattern, code)

        # store macros in dictionary
        for name, args, value in macros_found:
            self.macros[name] = (args.split(','), value.strip())

        # remove macro defs from code (since they are only for preprocessing)
        code = re.sub(macro_pattern, '', code)

        # replace macro invocations with expanded value
        for name, (args, value) in self.macros.items():
            # replace any instance of macro name with its def
            macro_call_pattern = re.compile(rf"\b{name}\((.*?)\)", re.DOTALL)
            code = re.sub(macro_call_pattern, self._expand_macro(name, args, value), code)

        return code

    def _expand_macro(self, name, args, value):
        def expand(match):
            # get arguments passed to the macro call
            call_args = match.group(1).split(',')
            
            # strip extra spaces from arguments
            call_args = [arg.strip() for arg in call_args]
            
            # create a local copy of the value for replacement
            expanded_value = value
            
            # replace each argument placeholder with corresponding value
            for arg, call_arg in zip(args, call_args):
                # replace the argument with the value passed
                expanded_value = expanded_value.replace(arg.strip(), call_arg)

            return expanded_value

        return expand

    def _handle_meta_comments(self, code):
        # replace specific comment patterns (variable definitions or conditional compilation)
        code = re.sub(r"/\*\s*@define\s+(\w+)\s+(\d+)\s*\*/", self._define_variable, code)
        return code

    def _define_variable(self, match):
        var_name, value = match.groups()
        return f"let {var_name} = {value};"

# example
source_code = """
/* @macro add_two(x) (x + 2) */
let result = add_two(5);

/* @define a 10 */
let x = a;
"""

preprocessor = Preprocessor()
processed_code = preprocessor.process(source_code)
print(processed_code)
```


- Macro Handling: We define a basic macro system where macros are specified in a comment
  using /* @macro name(args) value */. The preprocessor replaces occurrences of name(args)
  in the code with value, replacing arguments where necessary.

- Meta-Comments: We handle a simple @define directive, which allows defining a variable in
  the form /* @define a 10 */. The preprocessor replaces it with the corresponding code: let a = 10;.


Sample Output:

```
let result = (5 + 2);
let x = 10;
```

### Projects: Expanding the Preprocessor

To make this preprocessor more powerful, you can add more capabilities such as:
- *Conditional Compilation*: Use /* @if condition */ and /* @endif */ to enable/disable
  parts of the code.
- *Automatic Documentation Generation*: Parse special comments that describe functions
  and automatically generate documentation in a separate file.
- *Foreign Function Interface (FFI)*: Define external functions in the preprocessor
  and map them to corresponding code in other languages.

The basic structure would remain similar, focusing on scanning for comments, matching
specific patterns, and performing transformations on the code before it is parsed by
the main interpreter or compiler.
