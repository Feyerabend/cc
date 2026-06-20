from typing import List, Optional, Any
from jvm_interpreter.runtime.class_loader import ClassLoader
from jvm_interpreter.parser.class_file_parser import parse_class_file, ClassFile
from jvm_interpreter.runtime.interpreter import Interpreter
from jvm_interpreter.utils.jvm_utils import print_class_info
from jvm_interpreter.models.java_objects import JavaArray


class JavaClassInterpreter:
    def __init__(self, class_path: List[str]):
        self.class_loader = ClassLoader(class_path)

    def load_and_parse_class(self, filename: str) -> ClassFile:
        return self.class_loader.load_class(filename)

    def get_method_code(self, class_name: str, method_name: str) -> Optional[tuple]:
        return self.class_loader.get_method_code(class_name, method_name)

    def run_method(self, class_name: str, method_name: str,
                   verbose: bool = False) -> Optional[Any]:
        class_file = self.load_and_parse_class(class_name)
        code = self.get_method_code(class_file.this_class.name, method_name)
        if not code:
            raise ValueError(f"No '{method_name}' method found in {class_name}")
        if verbose:
            print(f"Interpreting '{method_name}' method...")
        exc_table = code[3] if len(code) > 3 else []
        interpreter = Interpreter(
            code[2], code[0], code[1],
            class_file.constant_pool, self.class_loader,
            exc_table
        )
        # For main(String[] args), set locals[0] to an empty String array
        if method_name == "main":
            interpreter.locals[0] = JavaArray("java.lang.String", 0)
        result = interpreter.run()
        if verbose:
            print(f"Done. Return value: {result}")
        return result

    def print_class_details(self, class_file: ClassFile):
        print_class_info(class_file)
