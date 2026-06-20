from typing import List, Dict, Any, Optional, Tuple
from jvm_interpreter.parser.class_file_parser import parse_class_file
from jvm_interpreter.models.class_file_models import ClassFile, CodeAttribute, Header, AccessFlags, ClassReference
from jvm_interpreter.native.native_registry import get_native_registry


class ClassLoader:
    """
    ClassLoader with native/custom separation and superclass method lookup.

    For native classes: returns a minimal stub (no .class file needed).
    For custom classes: loads and parses the .class file.
    """

    def __init__(self, class_path: List[str]):
        self.class_path = class_path
        self.loaded_classes: Dict[str, ClassFile] = {}
        self.static_fields: Dict[str, Any] = {}
        self.native_registry = get_native_registry()

    def load_class(self, class_name: str) -> ClassFile:
        """Load a class by name (dot or slash notation)."""
        class_name_slash = class_name.replace('.', '/')
        class_name_dot   = class_name.replace('/', '.')

        if class_name_slash in self.loaded_classes:
            return self.loaded_classes[class_name_slash]

        if self.native_registry.is_native_class(class_name_dot):
            stub = ClassFile(
                header=Header(0xCAFEBABE, 0, 52),
                cp=[],
                access=AccessFlags(0x0021),
                this_class=ClassReference(class_name_dot),
                super_class=ClassReference("java.lang.Object"),
                interfaces=[],
                fields=[],
                methods=[],
                attributes=[]
            )
            self.loaded_classes[class_name_slash] = stub
            return stub

        for path in self.class_path:
            try:
                file_path = f"{path}/{class_name_slash}.class"
                class_file = parse_class_file(file_path)
                self.loaded_classes[class_name_slash] = class_file
                self._initialize_class(class_file)
                return class_file
            except FileNotFoundError:
                continue

        raise ValueError(f"Class {class_name} not found in class path: {self.class_path}")

    def _initialize_class(self, class_file: ClassFile):
        """Run the static initializer <clinit> if present."""
        for method in class_file.methods:
            if method.name == "<clinit>":
                for attr in method.attributes:
                    if isinstance(attr, CodeAttribute):
                        from jvm_interpreter.runtime.interpreter import Interpreter
                        interp = Interpreter(
                            attr.code, attr.max_stack, attr.max_locals,
                            class_file.constant_pool, self,
                            attr.exceptions
                        )
                        interp.run()
                        return

    def get_method_code(self, class_name: str, method_name: str,
                        _visited: set = None) -> Optional[Tuple]:
        """
        Return (max_stack, max_locals, code_bytes, exception_table) for a method.

        Walks the superclass chain if the method is not found in the given class.
        Returns None if the method is native (handled by the native registry).
        """
        class_name_dot = class_name.replace('/', '.')

        if _visited is None:
            _visited = set()
        if class_name_dot in _visited:
            return None
        _visited.add(class_name_dot)

        if self.native_registry.has_native_method(class_name_dot, method_name):
            return None

        try:
            class_file = self.load_class(class_name)
        except ValueError:
            return None

        for method in class_file.methods:
            if method.name == method_name:
                for attr in method.attributes:
                    if isinstance(attr, CodeAttribute):
                        return (attr.max_stack, attr.max_locals,
                                attr.code, attr.exceptions)

        # Not found — try superclass
        super_name = class_file.super_class.name
        if (super_name and
                super_name not in (class_name_dot, 'java.lang.Object', 'java/lang/Object')):
            result = self.get_method_code(super_name, method_name, _visited)
            if result is not None:
                return result

        # Check if native registry covers the superclass chain
        if self.native_registry.has_native_method(class_name_dot, method_name):
            return None

        return None

    def resolve_field(self, class_name: str, field_name: str) -> Any:
        """Resolve a static field value."""
        class_name_dot = class_name.replace('/', '.')
        if self.native_registry.has_native_static_field(class_name_dot, field_name):
            return self.native_registry.get_native_static_field(class_name_dot, field_name)
        key = f"{class_name_dot}.{field_name}"
        return self.static_fields.get(key)

    def set_field(self, class_name: str, field_name: str, value: Any):
        """Set a static field value."""
        class_name_dot = class_name.replace('/', '.')
        if self.native_registry.has_native_static_field(class_name_dot, field_name):
            self.native_registry.set_native_static_field(class_name_dot, field_name, value)
        else:
            self.static_fields[f"{class_name_dot}.{field_name}"] = value
