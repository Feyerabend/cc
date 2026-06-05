"""
Native Method Registry for JVM Interpreter

This module provides a clear separation between:
1. Native implementations of Java standard library classes
2. Custom user classes loaded from .class files

The registry is checked FIRST before attempting bytecode interpretation.
"""

from typing import Any, Callable, Dict, Optional
import sys


class NativeObject:
    """Base class for all native Java objects implemented in Python"""
    
    def __init__(self, class_name: str):
        self.class_name = class_name
        self.fields: Dict[str, Any] = {}
    
    def get_field(self, name: str) -> Any:
        return self.fields.get(name)
    
    def set_field(self, name: str, value: Any):
        self.fields[name] = value


class JavaLangObject(NativeObject):
    """Native implementation of java.lang.Object"""
    
    def __init__(self):
        super().__init__("java.lang.Object")
    
    def equals(self, other) -> bool:
        return self is other
    
    def hashCode(self) -> int:
        return id(self)
    
    def toString(self) -> str:
        return f"{self.class_name}@{hex(id(self))}"
    
    def getClass(self) -> str:
        return self.class_name


class JavaLangStringBuilder(NativeObject):
    """Native implementation of java.lang.StringBuilder"""
    
    def __init__(self):
        super().__init__("java.lang.StringBuilder")
        self.value = ""
    
    def append(self, value: Any) -> 'JavaLangStringBuilder':
        self.value += str(value)
        return self
    
    def toString(self) -> str:
        return self.value


class JavaIoPrintStream(NativeObject):
    """Native implementation of java.io.PrintStream"""
    
    def __init__(self, stream=None):
        super().__init__("java.io.PrintStream")
        self.stream = stream or sys.stdout
    
    def println(self, s: Any = ""):
        print(s, file=self.stream)
    
    def print(self, s: Any):
        print(s, end='', file=self.stream)


class JavaLangSystem(NativeObject):
    """Native implementation of java.lang.System"""
    
    # Static field: System.out
    out = JavaIoPrintStream()
    
    @staticmethod
    def currentTimeMillis() -> int:
        import time
        return int(time.time() * 1000)


class NativeRegistry:
    """
    Registry for native Java standard library implementations.
    
    This provides a clean separation between:
    - Native methods (implemented in Python)
    - Custom methods (loaded from .class files and executed as bytecode)
    """
    
    def __init__(self):
        # Map of class_name -> {method_name -> callable}
        self._methods: Dict[str, Dict[str, Callable]] = {}
        
        # Map of class_name -> {field_name -> value}
        self._static_fields: Dict[str, Dict[str, Any]] = {}
        
        # Map of class_name -> constructor callable
        self._constructors: Dict[str, Callable] = {}
        
        self._register_natives()
    
    def _register_natives(self):
        """Register all native Java standard library implementations"""
        
        # java.lang.Object
        self.register_constructor("java.lang.Object", lambda: JavaLangObject())
        self.register_method("java.lang.Object", "equals", lambda self, other: self.equals(other))
        self.register_method("java.lang.Object", "hashCode", lambda self: self.hashCode())
        self.register_method("java.lang.Object", "toString", lambda self: self.toString())
        self.register_method("java.lang.Object", "<init>", lambda self: None)
        
        # java.lang.StringBuilder
        self.register_constructor("java.lang.StringBuilder", lambda: JavaLangStringBuilder())
        self.register_method("java.lang.StringBuilder", "append", 
                           lambda self, value: self.append(value))
        self.register_method("java.lang.StringBuilder", "toString", 
                           lambda self: self.toString())
        self.register_method("java.lang.StringBuilder", "<init>", lambda self: None)
        
        # java.io.PrintStream
        self.register_constructor("java.io.PrintStream", lambda: JavaIoPrintStream())
        self.register_method("java.io.PrintStream", "println", 
                           lambda self, s="": self.println(s))
        self.register_method("java.io.PrintStream", "print", 
                           lambda self, s: self.print(s))
        
        # java.lang.System (static fields and methods)
        self.register_static_field("java.lang.System", "out", JavaLangSystem.out)
        self.register_static_method("java.lang.System", "currentTimeMillis", 
                                   lambda: JavaLangSystem.currentTimeMillis())
    
    def register_constructor(self, class_name: str, constructor: Callable):
        """Register a native constructor for a class"""
        self._constructors[class_name] = constructor
    
    def register_method(self, class_name: str, method_name: str, method: Callable):
        """Register a native instance method"""
        if class_name not in self._methods:
            self._methods[class_name] = {}
        self._methods[class_name][method_name] = method
    
    def register_static_method(self, class_name: str, method_name: str, method: Callable):
        """Register a native static method"""
        self.register_method(class_name, method_name, method)
    
    def register_static_field(self, class_name: str, field_name: str, value: Any):
        """Register a native static field"""
        if class_name not in self._static_fields:
            self._static_fields[class_name] = {}
        self._static_fields[class_name][field_name] = value
    
    def is_native_class(self, class_name: str) -> bool:
        """Check if a class has native implementation"""
        class_name = class_name.replace('/', '.')
        return (class_name in self._constructors or 
                class_name in self._methods or 
                class_name in self._static_fields)
    
    def has_native_method(self, class_name: str, method_name: str) -> bool:
        """Check if a specific method has native implementation"""
        class_name = class_name.replace('/', '.')
        return class_name in self._methods and method_name in self._methods[class_name]
    
    def has_native_constructor(self, class_name: str) -> bool:
        """Check if a class has a native constructor"""
        class_name = class_name.replace('/', '.')
        return class_name in self._constructors
    
    def has_native_static_field(self, class_name: str, field_name: str) -> bool:
        """Check if a static field is native"""
        class_name = class_name.replace('/', '.')
        return class_name in self._static_fields and field_name in self._static_fields[class_name]
    
    def create_native_object(self, class_name: str) -> NativeObject:
        """Create a new instance of a native class"""
        class_name = class_name.replace('/', '.')
        if class_name not in self._constructors:
            raise ValueError(f"No native constructor for {class_name}")
        return self._constructors[class_name]()
    
    def invoke_native_method(self, class_name: str, method_name: str, 
                            obj: Optional[Any], args: list) -> Any:
        """Invoke a native method"""
        class_name = class_name.replace('/', '.')
        
        if not self.has_native_method(class_name, method_name):
            raise ValueError(f"No native method {class_name}.{method_name}")
        
        method = self._methods[class_name][method_name]
        
        # For instance methods, pass 'self' as first argument
        if obj is not None:
            return method(obj, *args)
        else:
            # Static method
            return method(*args)
    
    def get_native_static_field(self, class_name: str, field_name: str) -> Any:
        """Get a native static field value"""
        class_name = class_name.replace('/', '.')
        
        if not self.has_native_static_field(class_name, field_name):
            raise ValueError(f"No native static field {class_name}.{field_name}")
        
        return self._static_fields[class_name][field_name]
    
    def set_native_static_field(self, class_name: str, field_name: str, value: Any):
        """Set a native static field value"""
        class_name = class_name.replace('/', '.')
        
        if class_name not in self._static_fields:
            self._static_fields[class_name] = {}
        
        self._static_fields[class_name][field_name] = value


# Global singleton instance
_native_registry = NativeRegistry()


def get_native_registry() -> NativeRegistry:
    """Get the global native registry instance"""
    return _native_registry
