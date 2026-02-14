from typing import List, Dict, Any, Optional, Tuple
from jvm_interpreter.parser.class_file_parser import parse_class_file
from jvm_interpreter.models.class_file_models import ClassFile, CodeAttribute, Header, AccessFlags, ClassReference
from jvm_interpreter.native.native_registry import get_native_registry


class ClassLoader:
    """
    ClassLoader with native/custom separation.
    
    For native classes: Returns minimal stub (no actual .class file needed)
    For custom classes: Loads and parses .class file
    """
    
    def __init__(self, class_path: List[str]):
        """Initialize class loader"""
        self.class_path = class_path
        self.loaded_classes: Dict[str, ClassFile] = {}
        self.static_fields: Dict[str, Any] = {}
        self.native_registry = get_native_registry()
    
    def load_class(self, class_name: str) -> ClassFile:
        """Load a class by name"""
        # Normalize class name (both / and . should work)
        class_name_slash = class_name.replace('.', '/')
        class_name_dot = class_name.replace('/', '.')
        
        # Check cache first
        if class_name_slash in self.loaded_classes:
            return self.loaded_classes[class_name_slash]
        
        # CHECK IF NATIVE CLASS
        if self.native_registry.is_native_class(class_name_dot):
            # For native classes, create minimal stub
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
        
        # NOT NATIVE - load from .class file
        for path in self.class_path:
            try:
                file_path = f"{path}/{class_name_slash}.class"
                class_file = parse_class_file(file_path)
                self.loaded_classes[class_name_slash] = class_file
                
                # Initialize class (run <clinit> if present)
                self._initialize_class(class_file)
                
                return class_file
                
            except FileNotFoundError:
                continue
        
        # Class not found
        raise ValueError(
            f"Class {class_name} not found in class path: {self.class_path}"
        )
    
    def _initialize_class(self, class_file: ClassFile):
        """Initialize a class (run static initializer <clinit> if present)"""
        # Look for <clinit> method
        for method in class_file.methods:
            if method.name == "<clinit>":
                # Run static initializer
                for attr in method.attributes:
                    if isinstance(attr, CodeAttribute):
                        # Import here to avoid circular dependency
                        from jvm_interpreter.runtime.interpreter import Interpreter
                        
                        interp = Interpreter(
                            attr.code,
                            attr.max_stack,
                            attr.max_locals,
                            class_file.constant_pool,
                            self
                        )
                        interp.run()
                        return
    
    def get_method_code(self, class_name: str, method_name: str) -> Optional[Tuple[int, int, bytes]]:
        """Get bytecode for a method"""
        class_name_dot = class_name.replace('/', '.')
        
        # CHECK IF NATIVE
        if self.native_registry.has_native_method(class_name_dot, method_name):
            # Native methods don't have bytecode
            return None
        
        # CUSTOM METHOD - load class and find method
        class_file = self.load_class(class_name)
        
        # Search for method
        for method in class_file.methods:
            if method.name == method_name:
                # Find Code attribute
                for attr in method.attributes:
                    if isinstance(attr, CodeAttribute):
                        return (attr.max_stack, attr.max_locals, attr.code)
        
        # Method not found
        return None
    
    def resolve_field(self, class_name: str, field_name: str) -> Any:
        """Resolve a static field value"""
        class_name_dot = class_name.replace('/', '.')
        
        # CHECK IF NATIVE FIELD
        if self.native_registry.has_native_static_field(class_name_dot, field_name):
            return self.native_registry.get_native_static_field(class_name_dot, field_name)
        
        # CUSTOM FIELD - check our storage
        key = f"{class_name_dot}.{field_name}"
        return self.static_fields.get(key)
    
    def set_field(self, class_name: str, field_name: str, value: Any):
        """Set a static field value"""
        class_name_dot = class_name.replace('/', '.')
        
        # For native fields, update in registry
        if self.native_registry.has_native_static_field(class_name_dot, field_name):
            self.native_registry.set_native_static_field(class_name_dot, field_name, value)
        else:
            # For custom fields, store locally
            key = f"{class_name_dot}.{field_name}"
            self.static_fields[key] = value
