"""
Internal Object Representation for Java Classes

This module defines how objects are represented internally.
- NativeObject: Objects with Python implementations (from native_registry)
- JavaObject: Objects with bytecode implementations (from .class files)
"""

from typing import Any, Dict


class JavaObject:
    """
    Internal representation of a Java object from a custom .class file.
    
    This is NOT a native object - it represents objects whose behavior is
    defined by bytecode, not Python code.
    """
    
    def __init__(self, class_name: str):
        """
        Create a new Java object.
        
        Args:
            class_name: Fully qualified class name (e.g., "com.example.MyClass")
        """
        self.class_name = class_name
        # Instance fields: field_name -> value
        self.fields: Dict[str, Any] = {}
    
    def get_field(self, field_name: str) -> Any:
        """Get an instance field value"""
        if field_name not in self.fields:
            # Uninitialized fields default to null/0/false depending on type
            return None
        return self.fields[field_name]
    
    def set_field(self, field_name: str, value: Any):
        """Set an instance field value"""
        self.fields[field_name] = value
    
    def __repr__(self) -> str:
        return f"JavaObject({self.class_name}@{hex(id(self))})"


class JavaArray:
    """
    Internal representation of a Java array.
    """
    
    def __init__(self, component_type: str, length: int):
        """
        Create a new Java array.
        
        Args:
            component_type: Type of array elements (e.g., "int", "java.lang.String")
            length: Array length
        """
        self.component_type = component_type
        self.length = length
        
        # Initialize with default values based on type
        default_value = self._get_default_value(component_type)
        self.elements = [default_value for _ in range(length)]
    
    def _get_default_value(self, component_type: str) -> Any:
        """Get default value for a given type"""
        if component_type in ('int', 'byte', 'short', 'long'):
            return 0
        elif component_type in ('float', 'double'):
            return 0.0
        elif component_type == 'boolean':
            return False
        elif component_type == 'char':
            return '\0'
        else:
            # Reference type
            return None
    
    def get(self, index: int) -> Any:
        """Get array element at index"""
        if index < 0 or index >= self.length:
            raise IndexError(f"Array index out of bounds: {index}")
        return self.elements[index]
    
    def set(self, index: int, value: Any):
        """Set array element at index"""
        if index < 0 or index >= self.length:
            raise IndexError(f"Array index out of bounds: {index}")
        self.elements[index] = value
    
    def __repr__(self) -> str:
        return f"JavaArray({self.component_type}[{self.length}])"


class ObjectFactory:
    """
    Factory for creating Java objects.
    
    This provides a unified way to create both native and custom objects,
    checking the native registry first before falling back to custom objects.
    """
    
    def __init__(self, native_registry):
        """
        Create object factory.
        
        Args:
            native_registry: NativeRegistry instance to check for native classes
        """
        self.native_registry = native_registry
    
    def create_object(self, class_name: str) -> Any:
        """
        Create a new object instance.
        
        This checks the native registry first. If the class is native,
        it creates a native object. Otherwise, it creates a JavaObject.
        
        Args:
            class_name: Fully qualified class name
            
        Returns:
            Either a NativeObject (for stdlib) or JavaObject (for custom classes)
        """
        # Normalize class name
        class_name = class_name.replace('/', '.')
        
        # Check if native first
        if self.native_registry.has_native_constructor(class_name):
            return self.native_registry.create_native_object(class_name)
        
        # Otherwise, create custom JavaObject
        return JavaObject(class_name)
    
    def create_array(self, component_type: str, length: int) -> JavaArray:
        """
        Create a new array.
        
        Args:
            component_type: Type of array elements
            length: Array length
            
        Returns:
            JavaArray instance
        """
        return JavaArray(component_type, length)
