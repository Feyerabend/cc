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