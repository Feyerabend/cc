from typing import List, Dict, Any, Optional, Tuple
from jvm_interpreter.parser.class_file_parser import parse_class_file
from jvm_interpreter.models.class_file_models import ClassFile, CodeAttribute, Header, AccessFlags, ClassReference
from jvm_interpreter.native.native_registry import get_native_registry

# (superclass, [interfaces]) for Java stdlib types we never load as .class files
_BUILTIN_SUPERS: Dict[str, Optional[tuple]] = {
    'java.lang.Object':                   None,
    'java.lang.String':                   ('java.lang.Object',    ['java.lang.Comparable', 'java.lang.CharSequence']),
    'java.lang.Number':                   ('java.lang.Object',    []),
    'java.lang.Integer':                  ('java.lang.Number',    ['java.lang.Comparable']),
    'java.lang.Long':                     ('java.lang.Number',    ['java.lang.Comparable']),
    'java.lang.Float':                    ('java.lang.Number',    ['java.lang.Comparable']),
    'java.lang.Double':                   ('java.lang.Number',    ['java.lang.Comparable']),
    'java.lang.Boolean':                  ('java.lang.Object',    ['java.lang.Comparable']),
    'java.lang.Character':                ('java.lang.Object',    ['java.lang.Comparable']),
    'java.lang.Throwable':                ('java.lang.Object',    ['java.io.Serializable']),
    'java.lang.Error':                    ('java.lang.Throwable', []),
    'java.lang.Exception':                ('java.lang.Throwable', []),
    'java.lang.RuntimeException':         ('java.lang.Exception', []),
    'java.lang.ArithmeticException':      ('java.lang.RuntimeException', []),
    'java.lang.NullPointerException':     ('java.lang.RuntimeException', []),
    'java.lang.IndexOutOfBoundsException':('java.lang.RuntimeException', []),
    'java.lang.ArrayIndexOutOfBoundsException': ('java.lang.IndexOutOfBoundsException', []),
    'java.lang.StringIndexOutOfBoundsException':('java.lang.IndexOutOfBoundsException', []),
    'java.lang.ClassCastException':        ('java.lang.RuntimeException', []),
    'java.lang.ArrayStoreException':       ('java.lang.RuntimeException', []),
    'java.lang.CloneNotSupportedException':('java.lang.Exception', []),
    'java.lang.InterruptedException':      ('java.lang.Exception', []),
    'java.lang.ClassNotFoundException':   ('java.lang.ReflectiveOperationException', []),
    'java.lang.ReflectiveOperationException': ('java.lang.Exception', []),
    'java.lang.IllegalArgumentException': ('java.lang.RuntimeException', []),
    'java.lang.IllegalStateException':    ('java.lang.RuntimeException', []),
    'java.lang.UnsupportedOperationException': ('java.lang.RuntimeException', []),
    'java.lang.NumberFormatException':    ('java.lang.IllegalArgumentException', []),
    'java.lang.StackOverflowError':       ('java.lang.VirtualMachineError', []),
    'java.lang.VirtualMachineError':      ('java.lang.Error', []),
    'java.lang.OutOfMemoryError':         ('java.lang.VirtualMachineError', []),
    'java.lang.AssertionError':           ('java.lang.Error', []),
    # java.util exceptions
    'java.util.NoSuchElementException':        ('java.lang.RuntimeException', []),
    'java.util.EmptyStackException':           ('java.lang.RuntimeException', []),
    'java.util.ConcurrentModificationException': ('java.lang.RuntimeException', []),
    'java.util.InputMismatchException':        ('java.util.NoSuchElementException', []),
    # Interfaces
    'java.lang.Iterable':       ('java.lang.Object', []),
    'java.lang.Comparable':     ('java.lang.Object', []),
    'java.lang.CharSequence':   ('java.lang.Object', []),
    'java.io.Serializable':     ('java.lang.Object', []),
    'java.util.Collection':     ('java.lang.Object', ['java.lang.Iterable']),
    'java.util.List':           ('java.lang.Object', ['java.util.Collection']),
    'java.util.Set':            ('java.lang.Object', ['java.util.Collection']),
    'java.util.SortedSet':      ('java.lang.Object', ['java.util.Set']),
    'java.util.NavigableSet':   ('java.lang.Object', ['java.util.SortedSet']),
    'java.util.Queue':          ('java.lang.Object', ['java.util.Collection']),
    'java.util.Deque':          ('java.lang.Object', ['java.util.Queue']),
    'java.util.Map':            ('java.lang.Object', []),
    'java.util.SortedMap':      ('java.lang.Object', ['java.util.Map']),
    'java.util.NavigableMap':   ('java.lang.Object', ['java.util.SortedMap']),
    'java.util.RandomAccess':   ('java.lang.Object', []),
    # Collection classes
    'java.util.AbstractCollection': ('java.lang.Object',              ['java.util.Collection']),
    'java.util.AbstractList':        ('java.util.AbstractCollection',  ['java.util.List']),
    'java.util.AbstractSequentialList': ('java.util.AbstractList',     []),
    'java.util.AbstractSet':         ('java.util.AbstractCollection',  ['java.util.Set']),
    'java.util.AbstractMap':         ('java.lang.Object',              ['java.util.Map']),
    'java.util.ArrayList':   ('java.util.AbstractList',          ['java.util.List', 'java.util.RandomAccess']),
    'java.util.LinkedList':  ('java.util.AbstractSequentialList', ['java.util.List', 'java.util.Deque']),
    'java.util.Vector':      ('java.util.AbstractList',          ['java.util.List']),
    'java.util.Stack':       ('java.util.Vector',                []),
    'java.util.HashSet':     ('java.util.AbstractSet',           ['java.util.Set']),
    'java.util.TreeSet':     ('java.util.AbstractSet',           ['java.util.SortedSet', 'java.util.NavigableSet']),
    'java.util.HashMap':     ('java.util.AbstractMap',           ['java.util.Map']),
    'java.util.TreeMap':     ('java.util.AbstractMap',           ['java.util.SortedMap', 'java.util.NavigableMap']),
    # java.io
    'java.io.Closeable':             ('java.lang.Object', ['java.io.AutoCloseable']),
    'java.io.AutoCloseable':         ('java.lang.Object', []),
    'java.io.InputStream':           ('java.lang.Object', ['java.io.Closeable']),
    'java.io.OutputStream':          ('java.lang.Object', ['java.io.Closeable']),
    'java.io.PrintStream':           ('java.io.OutputStream', []),
    'java.io.Reader':                ('java.lang.Object', ['java.io.Closeable']),
    'java.io.Writer':                ('java.lang.Object', ['java.io.Closeable']),
    'java.io.File':                  ('java.lang.Object', ['java.io.Serializable']),
    'java.io.FileReader':            ('java.io.Reader',   []),
    'java.io.FileWriter':            ('java.io.Writer',   []),
    'java.io.InputStreamReader':     ('java.io.Reader',   []),
    'java.io.OutputStreamWriter':    ('java.io.Writer',   []),
    'java.io.BufferedReader':        ('java.io.Reader',   []),
    'java.io.BufferedWriter':        ('java.io.Writer',   []),
    'java.io.PrintWriter':           ('java.io.Writer',   []),
    'java.io.StringReader':          ('java.io.Reader',   []),
    'java.io.StringWriter':          ('java.io.Writer',   []),
    'java.io.IOException':            ('java.lang.Exception', []),
    'java.io.FileNotFoundException':  ('java.io.IOException', []),
    # java.lang.reflect
    'java.lang.Class':                ('java.lang.Object',    ['java.io.Serializable']),
    'java.lang.reflect.AccessibleObject': ('java.lang.Object', []),
    'java.lang.reflect.Member':       ('java.lang.Object',    []),
    'java.lang.reflect.Method':       ('java.lang.reflect.AccessibleObject', ['java.lang.reflect.Member']),
    'java.lang.reflect.Field':        ('java.lang.reflect.AccessibleObject', ['java.lang.reflect.Member']),
    'java.lang.reflect.Constructor':  ('java.lang.reflect.AccessibleObject', ['java.lang.reflect.Member']),
    'java.lang.reflect.Modifier':     ('java.lang.Object',    []),
    'java.lang.reflect.Array':        ('java.lang.Object',    []),
    'java.lang.NoSuchMethodException': ('java.lang.ReflectiveOperationException', []),
    'java.lang.NoSuchFieldException':  ('java.lang.ReflectiveOperationException', []),
    'java.lang.reflect.InvocationTargetException': ('java.lang.ReflectiveOperationException', []),
    # java.nio.file
    'java.nio.file.Path':            ('java.lang.Object', ['java.lang.Comparable']),
    'java.nio.file.Paths':           ('java.lang.Object', []),
    'java.nio.file.Files':           ('java.lang.Object', []),
    'java.nio.charset.Charset':      ('java.lang.Object', []),
    'java.nio.charset.StandardCharsets': ('java.lang.Object', []),
    # Functional interfaces (java.util.function + java.lang)
    'java.lang.Runnable':                   ('java.lang.Object', []),
    'java.util.concurrent.Callable':        ('java.lang.Object', []),
    'java.util.function.Supplier':          ('java.lang.Object', []),
    'java.util.function.Consumer':          ('java.lang.Object', []),
    'java.util.function.BiConsumer':        ('java.lang.Object', []),
    'java.util.function.Function':          ('java.lang.Object', []),
    'java.util.function.BiFunction':        ('java.lang.Object', []),
    'java.util.function.Predicate':         ('java.lang.Object', []),
    'java.util.function.BiPredicate':       ('java.lang.Object', []),
    'java.util.function.UnaryOperator':     ('java.lang.Object', ['java.util.function.Function']),
    'java.util.function.BinaryOperator':    ('java.lang.Object', ['java.util.function.BiFunction']),
    'java.util.function.IntFunction':       ('java.lang.Object', []),
    'java.util.function.IntUnaryOperator':  ('java.lang.Object', []),
    'java.util.function.IntBinaryOperator': ('java.lang.Object', []),
    'java.util.function.ToIntFunction':     ('java.lang.Object', []),
    'java.util.function.ToLongFunction':    ('java.lang.Object', []),
    'java.util.function.ToDoubleFunction':  ('java.lang.Object', []),
    'java.util.function.LongUnaryOperator': ('java.lang.Object', []),
    'java.util.function.DoubleUnaryOperator': ('java.lang.Object', []),
    'java.util.Comparator':                 ('java.lang.Object', []),
    # Streams
    'java.util.stream.Stream':              ('java.lang.Object', []),
    'java.util.stream.IntStream':           ('java.lang.Object', []),
    'java.util.stream.LongStream':          ('java.lang.Object', []),
    'java.util.stream.DoubleStream':        ('java.lang.Object', []),
    'java.util.stream.BaseStream':          ('java.lang.Object', []),
    'java.util.stream.Collector':           ('java.lang.Object', []),
    'java.util.Optional':                   ('java.lang.Object', []),
    'java.util.OptionalInt':                ('java.lang.Object', []),
}


def is_assignable(actual: str, target: str, class_loader=None) -> bool:
    """Return True if actual is-a target (subclass or interface implementation).

    Uses a BFS over superclass + interface edges. Consults the built-in
    stdlib table first; falls back to class-file metadata for user classes.
    """
    if actual == target or target == 'java.lang.Object':
        return True
    visited: set = set()
    frontier = [actual]
    while frontier:
        cls = frontier.pop()
        if cls in visited:
            continue
        visited.add(cls)
        if cls == target:
            return True
        entry = _BUILTIN_SUPERS.get(cls)
        if entry is not None:
            super_cls, ifaces = entry
            if super_cls:
                frontier.append(super_cls)
            frontier.extend(ifaces)
        elif class_loader is not None:
            try:
                cf = class_loader.load_class(cls)
                if cf.super_class and cf.super_class.name not in ('', None, 'java.lang.Object'):
                    frontier.append(cf.super_class.name)
                for iface in cf.interfaces:
                    frontier.append(iface.name)
            except Exception:
                pass
    return False


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

    def get_bootstrap_methods(self, class_name: str) -> list:
        """Return the list of BootstrapMethod entries for the given class."""
        from jvm_interpreter.models.class_file_models import BootstrapMethodsAttribute
        try:
            class_file = self.load_class(class_name)
        except ValueError:
            return []
        for attr in class_file.attributes:
            if isinstance(attr, BootstrapMethodsAttribute):
                return attr.methods
        return []

    def _initialize_class(self, class_file: ClassFile):
        """Run the static initializer <clinit> if present."""
        from jvm_interpreter.models.class_file_models import BootstrapMethodsAttribute
        bsm = []
        for attr in class_file.attributes:
            if isinstance(attr, BootstrapMethodsAttribute):
                bsm = attr.methods
                break
        for method in class_file.methods:
            if method.name == "<clinit>":
                for attr in method.attributes:
                    if isinstance(attr, CodeAttribute):
                        from jvm_interpreter.runtime.interpreter import Interpreter
                        interp = Interpreter(
                            attr.code, attr.max_stack, attr.max_locals,
                            class_file.constant_pool, self,
                            attr.exceptions, bsm
                        )
                        interp.run()
                        return

    def get_method_code(self, class_name: str, method_name: str,
                        descriptor: str = None,
                        _visited: set = None) -> Optional[Tuple]:
        """
        Return (max_stack, max_locals, code_bytes, exception_table, defining_class) for a method.

        The 5th element is the fully-qualified dot-notation name of the class that
        actually defines the method (which may be a superclass of class_name). Callers
        that invoke bytecode must load *that* class's constant pool, not the called
        class's pool — otherwise CP-index references in the inherited method are wrong.

        When descriptor is given, matches name + descriptor (overload resolution).
        When descriptor is None, matches by name only (used for <clinit> etc.).
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
                if descriptor is None or method.descriptor == descriptor:
                    for attr in method.attributes:
                        if isinstance(attr, CodeAttribute):
                            return (attr.max_stack, attr.max_locals,
                                    attr.code, attr.exceptions, class_name_dot)

        # Not found — try superclass
        super_name = class_file.super_class.name
        if (super_name and
                super_name not in (class_name_dot, 'java.lang.Object', 'java/lang/Object')):
            result = self.get_method_code(super_name, method_name, descriptor, _visited)
            if result is not None:
                return result

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
