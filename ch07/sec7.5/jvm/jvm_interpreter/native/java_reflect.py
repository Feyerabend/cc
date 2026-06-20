"""
Native implementations of java.lang.Class, java.lang.reflect.{Method,Field,Constructor,Modifier}.

Dispatch for instance methods on JavaClass/Method/Field/Constructor is handled
inside Interpreter._dispatch (it needs the class-loader at call time).
This module provides only the data objects and a registration stub.
"""

from jvm_interpreter.native.native_registry import NativeObject


# ---------------------------------------------------------------------------
# java.lang.Class
# ---------------------------------------------------------------------------

class JavaClass(NativeObject):
    """java.lang.Class — runtime type token."""

    def __init__(self, class_name: str):
        super().__init__("java.lang.Class")
        self._class_name = class_name.replace('/', '.')

    def getName(self) -> str:          return self._class_name
    def getCanonicalName(self) -> str: return self._class_name
    def getTypeName(self) -> str:      return self._class_name

    def getSimpleName(self) -> str:
        name = self._class_name
        dims = 0
        while name.startswith('['):
            dims += 1
            name = name[1:]
        if name.startswith('L') and name.endswith(';'):
            name = name[1:-1].replace('/', '.')
        name = name.rsplit('.', 1)[-1]
        return name + '[]' * dims

    def isPrimitive(self) -> bool:
        return self._class_name in (
            'int', 'long', 'float', 'double', 'boolean', 'char', 'byte', 'short', 'void')

    def isArray(self) -> bool:
        return self._class_name.startswith('[')

    def toString(self) -> str:
        return 'class ' + self._class_name

    def equals(self, other) -> bool:
        return isinstance(other, JavaClass) and self._class_name == other._class_name

    def hashCode(self) -> int:
        return hash(self._class_name)

    def __repr__(self) -> str:
        return f"JavaClass({self._class_name})"


# ---------------------------------------------------------------------------
# java.lang.reflect.Method
# ---------------------------------------------------------------------------

class JavaMethod(NativeObject):
    """java.lang.reflect.Method — a reflectively-obtained method."""

    def __init__(self, owner_class: str, method_name: str, descriptor: str,
                 modifiers: int = 0x0001):
        super().__init__("java.lang.reflect.Method")
        self._owner_class = owner_class.replace('/', '.')
        self._method_name = method_name
        self._descriptor  = descriptor
        self._modifiers   = modifiers
        self._accessible  = True

    def getName(self) -> str:      return self._method_name
    def getModifiers(self) -> int: return self._modifiers

    def setAccessible(self, flag):
        self._accessible = bool(flag)

    def isAccessible(self) -> bool: return self._accessible

    def toString(self) -> str:
        return f"{self._owner_class}.{self._method_name}{self._descriptor}"

    def equals(self, other) -> bool:
        return (isinstance(other, JavaMethod) and
                self._owner_class == other._owner_class and
                self._method_name == other._method_name and
                self._descriptor  == other._descriptor)

    def hashCode(self) -> int:
        return hash((self._owner_class, self._method_name, self._descriptor))

    def __repr__(self) -> str:
        return f"Method({self._owner_class}.{self._method_name})"


# ---------------------------------------------------------------------------
# java.lang.reflect.Field
# ---------------------------------------------------------------------------

class JavaField(NativeObject):
    """java.lang.reflect.Field — a reflectively-obtained field."""

    def __init__(self, owner_class: str, field_name: str,
                 type_descriptor: str = 'Ljava/lang/Object;',
                 modifiers: int = 0x0001):
        super().__init__("java.lang.reflect.Field")
        self._owner_class = owner_class.replace('/', '.')
        self._field_name  = field_name
        self._type_desc   = type_descriptor
        self._modifiers   = modifiers
        self._accessible  = True

    def getName(self) -> str:      return self._field_name
    def getModifiers(self) -> int: return self._modifiers

    def setAccessible(self, flag):
        self._accessible = bool(flag)

    def isAccessible(self) -> bool: return self._accessible

    def toString(self) -> str:
        return f"{self._owner_class}.{self._field_name}"

    def equals(self, other) -> bool:
        return (isinstance(other, JavaField) and
                self._owner_class == other._owner_class and
                self._field_name  == other._field_name)

    def hashCode(self) -> int:
        return hash((self._owner_class, self._field_name))

    def __repr__(self) -> str:
        return f"Field({self._owner_class}.{self._field_name})"


# ---------------------------------------------------------------------------
# java.lang.reflect.Constructor
# ---------------------------------------------------------------------------

class JavaConstructor(NativeObject):
    """java.lang.reflect.Constructor — a reflectively-obtained constructor."""

    def __init__(self, owner_class: str, descriptor: str = '()V',
                 modifiers: int = 0x0001):
        super().__init__("java.lang.reflect.Constructor")
        self._owner_class = owner_class.replace('/', '.')
        self._descriptor  = descriptor
        self._modifiers   = modifiers
        self._accessible  = True

    def getName(self) -> str:      return self._owner_class
    def getModifiers(self) -> int: return self._modifiers

    def setAccessible(self, flag):
        self._accessible = bool(flag)

    def isAccessible(self) -> bool: return self._accessible

    def toString(self) -> str:
        return f"{self._owner_class}{self._descriptor}"

    def equals(self, other) -> bool:
        return (isinstance(other, JavaConstructor) and
                self._owner_class == other._owner_class and
                self._descriptor  == other._descriptor)

    def hashCode(self) -> int:
        return hash((self._owner_class, self._descriptor))

    def __repr__(self) -> str:
        return f"Constructor({self._owner_class})"


# ---------------------------------------------------------------------------
# java.lang.reflect.Modifier  — bit-flag constants
# ---------------------------------------------------------------------------

PUBLIC       = 0x0001
PRIVATE      = 0x0002
PROTECTED    = 0x0004
STATIC       = 0x0008
FINAL        = 0x0010
SYNCHRONIZED = 0x0020
VOLATILE     = 0x0040
TRANSIENT    = 0x0080
NATIVE       = 0x0100
INTERFACE    = 0x0200
ABSTRACT     = 0x0400
STRICT       = 0x0800


def _modifier_string(mod: int) -> str:
    pairs = [
        (PUBLIC, "public"), (PRIVATE, "private"), (PROTECTED, "protected"),
        (STATIC, "static"), (FINAL, "final"), (SYNCHRONIZED, "synchronized"),
        (VOLATILE, "volatile"), (TRANSIENT, "transient"), (NATIVE, "native"),
        (INTERFACE, "interface"), (ABSTRACT, "abstract"), (STRICT, "strictfp"),
    ]
    return " ".join(name for flag, name in pairs if mod & flag)


# ---------------------------------------------------------------------------
# Descriptor helpers
# ---------------------------------------------------------------------------

_PRIM_MAP = {
    'I': 'int', 'J': 'long', 'F': 'float', 'D': 'double',
    'Z': 'boolean', 'C': 'char', 'B': 'byte', 'S': 'short', 'V': 'void',
}


def parse_method_descriptor(descriptor: str):
    """Return ([param_type_strings], return_type_string) from a JVM method descriptor."""
    if not descriptor.startswith('('):
        return [], descriptor
    params = []
    i = 1
    while i < len(descriptor) and descriptor[i] != ')':
        ch = descriptor[i]
        if ch == 'L':
            end = descriptor.index(';', i)
            params.append(descriptor[i:end + 1])
            i = end + 1
        elif ch == '[':
            j = i + 1
            while j < len(descriptor) and descriptor[j] == '[':
                j += 1
            if j < len(descriptor) and descriptor[j] == 'L':
                end = descriptor.index(';', j)
                params.append(descriptor[i:end + 1])
                i = end + 1
            else:
                params.append(descriptor[i:j + 1])
                i = j + 1
        else:
            params.append(ch)
            i += 1
    ret = descriptor[i + 1:] if i < len(descriptor) else 'V'
    return params, ret


def desc_to_class_name(desc: str) -> str:
    """Convert a single JVM type descriptor to a dot-notation class name."""
    if desc in _PRIM_MAP:
        return _PRIM_MAP[desc]
    if desc.startswith('L') and desc.endswith(';'):
        return desc[1:-1].replace('/', '.')
    return desc  # array descriptor or already a plain name


# ---------------------------------------------------------------------------
# Registration — stubs so is_native_class() works; real dispatch is in Interpreter
# ---------------------------------------------------------------------------

def register_java_reflect(registry):
    """Register stubs for all reflection types and Modifier static fields/methods."""

    # java.lang.Class
    registry.register_constructor("java.lang.Class",
                                  lambda: JavaClass("java.lang.Object"))
    # Stub so invokestatic Class.forName is visible to is_native_class;
    # real forName is intercepted before the registry in Interpreter._dispatch.
    registry.register_static_method("java.lang.Class", "forName",
                                    lambda n, *_: JavaClass(str(n).replace('/', '.')))

    # java.lang.reflect.Method / Field / Constructor
    registry.register_constructor("java.lang.reflect.Method",
                                  lambda: JavaMethod("java.lang.Object", "unknown", "()V"))
    registry.register_constructor("java.lang.reflect.Field",
                                  lambda: JavaField("java.lang.Object", "unknown"))
    registry.register_constructor("java.lang.reflect.Constructor",
                                  lambda: JavaConstructor("java.lang.Object"))

    # java.lang.reflect.Modifier — static fields
    for name, val in [
        ("PUBLIC", PUBLIC), ("PRIVATE", PRIVATE), ("PROTECTED", PROTECTED),
        ("STATIC", STATIC), ("FINAL", FINAL), ("SYNCHRONIZED", SYNCHRONIZED),
        ("VOLATILE", VOLATILE), ("TRANSIENT", TRANSIENT), ("NATIVE", NATIVE),
        ("INTERFACE", INTERFACE), ("ABSTRACT", ABSTRACT), ("STRICT", STRICT),
    ]:
        registry.register_static_field("java.lang.reflect.Modifier", name, val)

    # Modifier static methods
    registry.register_static_method("java.lang.reflect.Modifier", "isPublic",
                                    lambda m: bool(int(m) & PUBLIC))
    registry.register_static_method("java.lang.reflect.Modifier", "isPrivate",
                                    lambda m: bool(int(m) & PRIVATE))
    registry.register_static_method("java.lang.reflect.Modifier", "isProtected",
                                    lambda m: bool(int(m) & PROTECTED))
    registry.register_static_method("java.lang.reflect.Modifier", "isStatic",
                                    lambda m: bool(int(m) & STATIC))
    registry.register_static_method("java.lang.reflect.Modifier", "isFinal",
                                    lambda m: bool(int(m) & FINAL))
    registry.register_static_method("java.lang.reflect.Modifier", "isAbstract",
                                    lambda m: bool(int(m) & ABSTRACT))
    registry.register_static_method("java.lang.reflect.Modifier", "isInterface",
                                    lambda m: bool(int(m) & INTERFACE))
    registry.register_static_method("java.lang.reflect.Modifier", "isNative",
                                    lambda m: bool(int(m) & NATIVE))
    registry.register_static_method("java.lang.reflect.Modifier", "isSynchronized",
                                    lambda m: bool(int(m) & SYNCHRONIZED))
    registry.register_static_method("java.lang.reflect.Modifier", "isTransient",
                                    lambda m: bool(int(m) & TRANSIENT))
    registry.register_static_method("java.lang.reflect.Modifier", "isVolatile",
                                    lambda m: bool(int(m) & VOLATILE))
    registry.register_static_method("java.lang.reflect.Modifier", "toString",
                                    lambda m: _modifier_string(int(m)))
