"""
Native Method Registry for JVM Interpreter

Provides Python implementations of Java standard library classes.
The registry is consulted before attempting bytecode interpretation.
"""

import sys
import math
from typing import Any, Callable, Dict, Optional


class NativeObject:
    """Base class for all native Java objects implemented in Python."""

    def __init__(self, class_name: str):
        self.class_name = class_name
        self.fields: Dict[str, Any] = {}

    def get_field(self, name: str) -> Any:
        return self.fields.get(name)

    def set_field(self, name: str, value: Any):
        self.fields[name] = value


# ===== java.lang.Object =====

class JavaLangObject(NativeObject):
    def __init__(self):
        super().__init__("java.lang.Object")

    def equals(self, other) -> bool: return self is other
    def hashCode(self) -> int: return id(self)
    def toString(self) -> str: return f"{self.class_name}@{hex(id(self))}"
    def getClass(self) -> str: return self.class_name


# ===== java.lang.StringBuilder =====

class JavaLangStringBuilder(NativeObject):
    def __init__(self):
        super().__init__("java.lang.StringBuilder")
        self.value = ""

    def append(self, v: Any) -> 'JavaLangStringBuilder':
        if v is None:
            self.value += "null"
        elif isinstance(v, bool):
            self.value += "true" if v else "false"
        else:
            self.value += str(v)
        return self

    def toString(self) -> str: return self.value
    def length(self) -> int: return len(self.value)
    def charAt(self, i: int) -> int: return ord(self.value[i])
    def reverse(self) -> 'JavaLangStringBuilder':
        self.value = self.value[::-1]
        return self
    def deleteCharAt(self, i: int) -> 'JavaLangStringBuilder':
        self.value = self.value[:i] + self.value[i+1:]
        return self
    def insert(self, offset: int, s: Any) -> 'JavaLangStringBuilder':
        self.value = self.value[:offset] + str(s) + self.value[offset:]
        return self


# ===== java.io.PrintStream =====

class JavaIoPrintStream(NativeObject):
    def __init__(self, stream=None):
        super().__init__("java.io.PrintStream")
        self.stream = stream or sys.stdout

    def println(self, s: Any = ""):
        text = "null" if s is None else ("true" if s is True else "false" if s is False else str(s))
        print(text, file=self.stream)

    def print(self, s: Any):
        text = "null" if s is None else ("true" if s is True else "false" if s is False else str(s))
        print(text, end='', file=self.stream)

    def printf(self, fmt: Any, *args) -> 'JavaIoPrintStream':
        text = str(fmt) % args if args else str(fmt)
        print(text, end='', file=self.stream)
        return self

    def flush(self): pass


# ===== java.lang.System =====

class JavaLangSystem(NativeObject):
    out = JavaIoPrintStream()
    err = JavaIoPrintStream(sys.stderr)

    @staticmethod
    def currentTimeMillis() -> int:
        import time
        return int(time.time() * 1000)

    @staticmethod
    def nanoTime() -> int:
        import time
        return int(time.time_ns())

    @staticmethod
    def exit(code: int): sys.exit(code)

    @staticmethod
    def arraycopy(src, src_pos, dst, dst_pos, length):
        for i in range(length):
            dst.set(dst_pos + i, src.get(src_pos + i))


# ===== java.lang.Integer =====

class JavaLangInteger(NativeObject):
    MAX_VALUE = 2147483647
    MIN_VALUE = -2147483648

    def __init__(self, value: int = 0):
        super().__init__("java.lang.Integer")
        self._value = int(value)

    def intValue(self) -> int: return self._value
    def longValue(self) -> int: return self._value
    def floatValue(self) -> float: return float(self._value)
    def doubleValue(self) -> float: return float(self._value)
    def toString(self) -> str: return str(self._value)
    def equals(self, other) -> bool:
        return isinstance(other, JavaLangInteger) and self._value == other._value
    def compareTo(self, other) -> int:
        return 0 if self._value == other._value else (1 if self._value > other._value else -1)
    def hashCode(self) -> int: return self._value

    @staticmethod
    def parseInt(s: str, radix: int = 10) -> int: return int(s, radix)

    @staticmethod
    def valueOf(v: Any) -> 'JavaLangInteger':
        return JavaLangInteger(int(v))

    @staticmethod
    def toBinaryString(v: int) -> str: return bin(v & 0xFFFFFFFF)[2:]

    @staticmethod
    def toHexString(v: int) -> str: return hex(v & 0xFFFFFFFF)[2:]

    @staticmethod
    def toOctalString(v: int) -> str: return oct(v & 0xFFFFFFFF)[2:]

    @staticmethod
    def bitCount(v: int) -> int: return bin(v & 0xFFFFFFFF).count('1')

    @staticmethod
    def max(a: int, b: int) -> int: return max(a, b)

    @staticmethod
    def min(a: int, b: int) -> int: return min(a, b)

    @staticmethod
    def sum(a: int, b: int) -> int: return a + b

    @staticmethod
    def compare(a: int, b: int) -> int: return 0 if a == b else (1 if a > b else -1)

    @staticmethod
    def reverse(v: int) -> int:
        bits = f'{v & 0xFFFFFFFF:032b}'
        return int(bits[::-1], 2)

    @staticmethod
    def highestOneBit(v: int) -> int:
        v &= 0xFFFFFFFF
        if v == 0: return 0
        return 1 << (v.bit_length() - 1)

    @staticmethod
    def numberOfLeadingZeros(v: int) -> int:
        v &= 0xFFFFFFFF
        return 32 if v == 0 else 32 - v.bit_length()

    @staticmethod
    def numberOfTrailingZeros(v: int) -> int:
        v &= 0xFFFFFFFF
        if v == 0: return 32
        count = 0
        while (v & 1) == 0:
            v >>= 1; count += 1
        return count


# ===== java.lang.Long =====

class JavaLangLong(NativeObject):
    def __init__(self, value: int = 0):
        super().__init__("java.lang.Long")
        self._value = int(value)

    def longValue(self) -> int: return self._value
    def intValue(self) -> int: return self._value & 0xFFFFFFFF
    def doubleValue(self) -> float: return float(self._value)
    def toString(self) -> str: return str(self._value)

    @staticmethod
    def parseLong(s: str, radix: int = 10) -> int: return int(s, radix)

    @staticmethod
    def valueOf(v: Any) -> 'JavaLangLong': return JavaLangLong(int(v))

    @staticmethod
    def toHexString(v: int) -> str: return hex(v & 0xFFFFFFFFFFFFFFFF)[2:]

    @staticmethod
    def bitCount(v: int) -> int: return bin(v & 0xFFFFFFFFFFFFFFFF).count('1')

    @staticmethod
    def max(a: int, b: int) -> int: return max(a, b)

    @staticmethod
    def min(a: int, b: int) -> int: return min(a, b)


# ===== java.lang.Double / Float =====

class JavaLangDouble(NativeObject):
    def __init__(self, value: float = 0.0):
        super().__init__("java.lang.Double")
        self._value = float(value)

    def doubleValue(self) -> float: return self._value
    def floatValue(self) -> float: return self._value
    def intValue(self) -> int: return int(self._value)
    def toString(self) -> str: return str(self._value)

    @staticmethod
    def parseDouble(s: str) -> float: return float(s)

    @staticmethod
    def valueOf(v: Any) -> 'JavaLangDouble': return JavaLangDouble(float(v))

    @staticmethod
    def isNaN(v: float) -> bool: return math.isnan(v)

    @staticmethod
    def isInfinite(v: float) -> bool: return math.isinf(v)

    @staticmethod
    def max(a: float, b: float) -> float: return max(a, b)

    @staticmethod
    def min(a: float, b: float) -> float: return min(a, b)

    @staticmethod
    def compare(a: float, b: float) -> int: return 0 if a == b else (1 if a > b else -1)


# ===== java.lang.String (as Python str wrappers) =====

class JavaLangString:
    """Static methods for java.lang.String — strings are kept as Python str objects."""

    @staticmethod
    def length(s: str) -> int: return len(s)

    @staticmethod
    def charAt(s: str, i: int) -> int: return ord(s[i])

    @staticmethod
    def substring(s: str, start: int, end: int = None) -> str:
        return s[start:] if end is None else s[start:end]

    @staticmethod
    def indexOf(s: str, ch_or_str, from_index: int = 0) -> int:
        if isinstance(ch_or_str, int):
            ch_or_str = chr(ch_or_str)
        return s.find(ch_or_str, from_index)

    @staticmethod
    def lastIndexOf(s: str, ch_or_str, from_index: int = None) -> int:
        if isinstance(ch_or_str, int):
            ch_or_str = chr(ch_or_str)
        end = from_index + 1 if from_index is not None else len(s)
        return s.rfind(ch_or_str, 0, end)

    @staticmethod
    def equals(s: str, other) -> bool: return s == other

    @staticmethod
    def equalsIgnoreCase(s: str, other: str) -> bool:
        return isinstance(other, str) and s.lower() == other.lower()

    @staticmethod
    def compareTo(s: str, other: str) -> int:
        return 0 if s == other else (1 if s > other else -1)

    @staticmethod
    def toUpperCase(s: str) -> str: return s.upper()

    @staticmethod
    def toLowerCase(s: str) -> str: return s.lower()

    @staticmethod
    def trim(s: str) -> str: return s.strip()

    @staticmethod
    def strip(s: str) -> str: return s.strip()

    @staticmethod
    def isEmpty(s: str) -> bool: return len(s) == 0

    @staticmethod
    def isBlank(s: str) -> bool: return len(s.strip()) == 0

    @staticmethod
    def contains(s: str, other: str) -> bool: return other in s

    @staticmethod
    def startsWith(s: str, prefix: str) -> bool: return s.startswith(prefix)

    @staticmethod
    def endsWith(s: str, suffix: str) -> bool: return s.endswith(suffix)

    @staticmethod
    def concat(s: str, other: str) -> str: return s + other

    @staticmethod
    def replace(s: str, old, new) -> str:
        if isinstance(old, int): old = chr(old)
        if isinstance(new, int): new = chr(new)
        return s.replace(old, new)

    @staticmethod
    def toCharArray(s: str):
        from jvm_interpreter.models.java_objects import JavaArray
        arr = JavaArray('char', len(s))
        for i, c in enumerate(s): arr.elements[i] = ord(c)
        return arr

    @staticmethod
    def valueOf(v: Any) -> str:
        if v is None: return "null"
        if isinstance(v, bool): return "true" if v else "false"
        return str(v)

    @staticmethod
    def format(fmt: str, *args) -> str: return fmt % args if args else fmt

    @staticmethod
    def join(delimiter: str, *parts) -> str: return delimiter.join(str(p) for p in parts)


# ===== java.lang.Math =====

class JavaLangMath:
    @staticmethod
    def abs(v): return abs(v)

    @staticmethod
    def max(a, b): return max(a, b)

    @staticmethod
    def min(a, b): return min(a, b)

    @staticmethod
    def sqrt(v: float) -> float: return math.sqrt(v)

    @staticmethod
    def pow(base: float, exp: float) -> float: return math.pow(base, exp)

    @staticmethod
    def floor(v: float) -> float: return math.floor(v)

    @staticmethod
    def ceil(v: float) -> float: return math.ceil(v)

    @staticmethod
    def round(v: float) -> int: return int(math.floor(v + 0.5))

    @staticmethod
    def log(v: float) -> float: return math.log(v)

    @staticmethod
    def log10(v: float) -> float: return math.log10(v)

    @staticmethod
    def exp(v: float) -> float: return math.exp(v)

    @staticmethod
    def sin(v: float) -> float: return math.sin(v)

    @staticmethod
    def cos(v: float) -> float: return math.cos(v)

    @staticmethod
    def tan(v: float) -> float: return math.tan(v)

    @staticmethod
    def asin(v: float) -> float: return math.asin(v)

    @staticmethod
    def acos(v: float) -> float: return math.acos(v)

    @staticmethod
    def atan(v: float) -> float: return math.atan(v)

    @staticmethod
    def atan2(y: float, x: float) -> float: return math.atan2(y, x)

    @staticmethod
    def random() -> float:
        import random
        return random.random()

    @staticmethod
    def toRadians(deg: float) -> float: return math.radians(deg)

    @staticmethod
    def toDegrees(rad: float) -> float: return math.degrees(rad)

    @staticmethod
    def signum(v: float) -> float:
        return 0.0 if v == 0 else (1.0 if v > 0 else -1.0)

    @staticmethod
    def hypot(x: float, y: float) -> float: return math.hypot(x, y)

    PI = math.pi
    E  = math.e


# ===== NativeRegistry =====

class NativeRegistry:
    """Registry of Java standard library implementations in Python."""

    def __init__(self):
        self._methods: Dict[str, Dict[str, Callable]] = {}
        self._static_fields: Dict[str, Dict[str, Any]] = {}
        self._constructors: Dict[str, Callable] = {}
        self._register_natives()

    def _register_natives(self):

        # --- java.lang.Object ---
        self.register_constructor("java.lang.Object", lambda: JavaLangObject())
        self.register_method("java.lang.Object", "<init>", lambda self: None)
        self.register_method("java.lang.Object", "equals",   lambda self, o: self.equals(o))
        self.register_method("java.lang.Object", "hashCode", lambda self: self.hashCode())
        self.register_method("java.lang.Object", "toString", lambda self: self.toString())
        self.register_method("java.lang.Object", "getClass", lambda self: self.getClass())

        # --- java.lang.StringBuilder ---
        self.register_constructor("java.lang.StringBuilder", lambda: JavaLangStringBuilder())
        self.register_method("java.lang.StringBuilder", "<init>", lambda self: None)
        self.register_method("java.lang.StringBuilder", "append",
                             lambda self, v: self.append(v))
        self.register_method("java.lang.StringBuilder", "toString",
                             lambda self: self.toString())
        self.register_method("java.lang.StringBuilder", "length",
                             lambda self: self.length())
        self.register_method("java.lang.StringBuilder", "charAt",
                             lambda self, i: self.charAt(i))
        self.register_method("java.lang.StringBuilder", "reverse",
                             lambda self: self.reverse())
        self.register_method("java.lang.StringBuilder", "deleteCharAt",
                             lambda self, i: self.deleteCharAt(i))
        self.register_method("java.lang.StringBuilder", "insert",
                             lambda self, offset, s: self.insert(offset, s))

        # --- java.io.PrintStream ---
        self.register_constructor("java.io.PrintStream", lambda: JavaIoPrintStream())
        self.register_method("java.io.PrintStream", "println",
                             lambda self, s="": self.println(s))
        self.register_method("java.io.PrintStream", "print",
                             lambda self, s: self.print(s))
        self.register_method("java.io.PrintStream", "printf",
                             lambda self, fmt, *args: self.printf(fmt, *args))
        self.register_method("java.io.PrintStream", "flush", lambda self: self.flush())

        # --- java.lang.System ---
        self.register_static_field("java.lang.System", "out", JavaLangSystem.out)
        self.register_static_field("java.lang.System", "err", JavaLangSystem.err)
        self.register_static_method("java.lang.System", "currentTimeMillis",
                                    lambda: JavaLangSystem.currentTimeMillis())
        self.register_static_method("java.lang.System", "nanoTime",
                                    lambda: JavaLangSystem.nanoTime())
        self.register_static_method("java.lang.System", "exit",
                                    lambda code: JavaLangSystem.exit(code))
        self.register_static_method("java.lang.System", "arraycopy",
                                    lambda src, sp, dst, dp, n:
                                    JavaLangSystem.arraycopy(src, sp, dst, dp, n))

        # --- java.lang.Integer ---
        self.register_constructor("java.lang.Integer", lambda: JavaLangInteger())
        self.register_method("java.lang.Integer", "<init>",
                             lambda self, v=0: setattr(self, '_value', int(v)))
        self.register_method("java.lang.Integer", "intValue",    lambda self: self.intValue())
        self.register_method("java.lang.Integer", "longValue",   lambda self: self.longValue())
        self.register_method("java.lang.Integer", "floatValue",  lambda self: self.floatValue())
        self.register_method("java.lang.Integer", "doubleValue", lambda self: self.doubleValue())
        self.register_method("java.lang.Integer", "toString",    lambda self: self.toString())
        self.register_method("java.lang.Integer", "equals",      lambda self, o: self.equals(o))
        self.register_method("java.lang.Integer", "compareTo",   lambda self, o: self.compareTo(o))
        self.register_method("java.lang.Integer", "hashCode",    lambda self: self.hashCode())
        self.register_static_method("java.lang.Integer", "parseInt",
                                    lambda s, r=10: JavaLangInteger.parseInt(s, r))
        self.register_static_method("java.lang.Integer", "valueOf",
                                    lambda v: JavaLangInteger.valueOf(v))
        self.register_static_method("java.lang.Integer", "toBinaryString",
                                    lambda v: JavaLangInteger.toBinaryString(v))
        self.register_static_method("java.lang.Integer", "toHexString",
                                    lambda v: JavaLangInteger.toHexString(v))
        self.register_static_method("java.lang.Integer", "toOctalString",
                                    lambda v: JavaLangInteger.toOctalString(v))
        self.register_static_method("java.lang.Integer", "bitCount",
                                    lambda v: JavaLangInteger.bitCount(v))
        self.register_static_method("java.lang.Integer", "max",
                                    lambda a, b: JavaLangInteger.max(a, b))
        self.register_static_method("java.lang.Integer", "min",
                                    lambda a, b: JavaLangInteger.min(a, b))
        self.register_static_method("java.lang.Integer", "sum",
                                    lambda a, b: JavaLangInteger.sum(a, b))
        self.register_static_method("java.lang.Integer", "compare",
                                    lambda a, b: JavaLangInteger.compare(a, b))
        self.register_static_method("java.lang.Integer", "reverse",
                                    lambda v: JavaLangInteger.reverse(v))
        self.register_static_method("java.lang.Integer", "highestOneBit",
                                    lambda v: JavaLangInteger.highestOneBit(v))
        self.register_static_method("java.lang.Integer", "numberOfLeadingZeros",
                                    lambda v: JavaLangInteger.numberOfLeadingZeros(v))
        self.register_static_method("java.lang.Integer", "numberOfTrailingZeros",
                                    lambda v: JavaLangInteger.numberOfTrailingZeros(v))
        self.register_static_field("java.lang.Integer", "MAX_VALUE",
                                   JavaLangInteger.MAX_VALUE)
        self.register_static_field("java.lang.Integer", "MIN_VALUE",
                                   JavaLangInteger.MIN_VALUE)

        # --- java.lang.Long ---
        self.register_constructor("java.lang.Long", lambda: JavaLangLong())
        self.register_method("java.lang.Long", "<init>",
                             lambda self, v=0: setattr(self, '_value', int(v)))
        self.register_method("java.lang.Long", "longValue",  lambda self: self.longValue())
        self.register_method("java.lang.Long", "intValue",   lambda self: self.intValue())
        self.register_method("java.lang.Long", "doubleValue",lambda self: self.doubleValue())
        self.register_method("java.lang.Long", "toString",   lambda self: self.toString())
        self.register_static_method("java.lang.Long", "parseLong",
                                    lambda s, r=10: JavaLangLong.parseLong(s, r))
        self.register_static_method("java.lang.Long", "valueOf",
                                    lambda v: JavaLangLong.valueOf(v))
        self.register_static_method("java.lang.Long", "toHexString",
                                    lambda v: JavaLangLong.toHexString(v))
        self.register_static_method("java.lang.Long", "bitCount",
                                    lambda v: JavaLangLong.bitCount(v))
        self.register_static_method("java.lang.Long", "max",
                                    lambda a, b: JavaLangLong.max(a, b))
        self.register_static_method("java.lang.Long", "min",
                                    lambda a, b: JavaLangLong.min(a, b))

        # --- java.lang.Double ---
        self.register_constructor("java.lang.Double", lambda: JavaLangDouble())
        self.register_method("java.lang.Double", "<init>",
                             lambda self, v=0.0: setattr(self, '_value', float(v)))
        self.register_method("java.lang.Double", "doubleValue", lambda self: self.doubleValue())
        self.register_method("java.lang.Double", "floatValue",  lambda self: self.floatValue())
        self.register_method("java.lang.Double", "intValue",    lambda self: self.intValue())
        self.register_method("java.lang.Double", "toString",    lambda self: self.toString())
        self.register_static_method("java.lang.Double", "parseDouble",
                                    lambda s: JavaLangDouble.parseDouble(s))
        self.register_static_method("java.lang.Double", "valueOf",
                                    lambda v: JavaLangDouble.valueOf(v))
        self.register_static_method("java.lang.Double", "isNaN",
                                    lambda v: JavaLangDouble.isNaN(v))
        self.register_static_method("java.lang.Double", "isInfinite",
                                    lambda v: JavaLangDouble.isInfinite(v))
        self.register_static_method("java.lang.Double", "max",
                                    lambda a, b: JavaLangDouble.max(a, b))
        self.register_static_method("java.lang.Double", "min",
                                    lambda a, b: JavaLangDouble.min(a, b))
        self.register_static_method("java.lang.Double", "compare",
                                    lambda a, b: JavaLangDouble.compare(a, b))

        # --- java.lang.String (instance methods called on Python str objects) ---
        self.register_method("java.lang.String", "length",
                             lambda self: JavaLangString.length(self))
        self.register_method("java.lang.String", "charAt",
                             lambda self, i: JavaLangString.charAt(self, i))
        self.register_method("java.lang.String", "substring",
                             lambda self, s, e=None: JavaLangString.substring(self, s, e))
        self.register_method("java.lang.String", "indexOf",
                             lambda self, v, f=0: JavaLangString.indexOf(self, v, f))
        self.register_method("java.lang.String", "lastIndexOf",
                             lambda self, v, f=None: JavaLangString.lastIndexOf(self, v, f))
        self.register_method("java.lang.String", "equals",
                             lambda self, o: JavaLangString.equals(self, o))
        self.register_method("java.lang.String", "equalsIgnoreCase",
                             lambda self, o: JavaLangString.equalsIgnoreCase(self, o))
        self.register_method("java.lang.String", "compareTo",
                             lambda self, o: JavaLangString.compareTo(self, o))
        self.register_method("java.lang.String", "toUpperCase",
                             lambda self: JavaLangString.toUpperCase(self))
        self.register_method("java.lang.String", "toLowerCase",
                             lambda self: JavaLangString.toLowerCase(self))
        self.register_method("java.lang.String", "trim",
                             lambda self: JavaLangString.trim(self))
        self.register_method("java.lang.String", "strip",
                             lambda self: JavaLangString.strip(self))
        self.register_method("java.lang.String", "isEmpty",
                             lambda self: JavaLangString.isEmpty(self))
        self.register_method("java.lang.String", "isBlank",
                             lambda self: JavaLangString.isBlank(self))
        self.register_method("java.lang.String", "contains",
                             lambda self, o: JavaLangString.contains(self, o))
        self.register_method("java.lang.String", "startsWith",
                             lambda self, p: JavaLangString.startsWith(self, p))
        self.register_method("java.lang.String", "endsWith",
                             lambda self, s: JavaLangString.endsWith(self, s))
        self.register_method("java.lang.String", "concat",
                             lambda self, o: JavaLangString.concat(self, o))
        self.register_method("java.lang.String", "replace",
                             lambda self, old, new: JavaLangString.replace(self, old, new))
        self.register_method("java.lang.String", "toCharArray",
                             lambda self: JavaLangString.toCharArray(self))
        self.register_method("java.lang.String", "toString",
                             lambda self: self)
        self.register_method("java.lang.String", "hashCode",
                             lambda self: hash(self))
        self.register_static_method("java.lang.String", "valueOf",
                                    lambda v: JavaLangString.valueOf(v))
        self.register_static_method("java.lang.String", "format",
                                    lambda fmt, *args: JavaLangString.format(fmt, *args))

        # --- java.lang.Math (all static) ---
        _math = JavaLangMath
        for name, fn in [
            ("abs", lambda v: _math.abs(v)),
            ("max", lambda a, b: _math.max(a, b)),
            ("min", lambda a, b: _math.min(a, b)),
            ("sqrt", lambda v: _math.sqrt(v)),
            ("pow", lambda b, e: _math.pow(b, e)),
            ("floor", lambda v: _math.floor(v)),
            ("ceil", lambda v: _math.ceil(v)),
            ("round", lambda v: _math.round(v)),
            ("log", lambda v: _math.log(v)),
            ("log10", lambda v: _math.log10(v)),
            ("exp", lambda v: _math.exp(v)),
            ("sin", lambda v: _math.sin(v)),
            ("cos", lambda v: _math.cos(v)),
            ("tan", lambda v: _math.tan(v)),
            ("asin", lambda v: _math.asin(v)),
            ("acos", lambda v: _math.acos(v)),
            ("atan", lambda v: _math.atan(v)),
            ("atan2", lambda y, x: _math.atan2(y, x)),
            ("random", lambda: _math.random()),
            ("toRadians", lambda v: _math.toRadians(v)),
            ("toDegrees", lambda v: _math.toDegrees(v)),
            ("signum", lambda v: _math.signum(v)),
            ("hypot", lambda x, y: _math.hypot(x, y)),
        ]:
            self.register_static_method("java.lang.Math", name, fn)
        self.register_static_field("java.lang.Math", "PI", math.pi)
        self.register_static_field("java.lang.Math", "E",  math.e)

    # ===== Registry API =====

    def register_constructor(self, class_name: str, constructor: Callable):
        self._constructors[class_name] = constructor

    def register_method(self, class_name: str, method_name: str, method: Callable):
        if class_name not in self._methods:
            self._methods[class_name] = {}
        self._methods[class_name][method_name] = method

    def register_static_method(self, class_name: str, method_name: str, method: Callable):
        self.register_method(class_name, method_name, method)

    def register_static_field(self, class_name: str, field_name: str, value: Any):
        if class_name not in self._static_fields:
            self._static_fields[class_name] = {}
        self._static_fields[class_name][field_name] = value

    def is_native_class(self, class_name: str) -> bool:
        class_name = class_name.replace('/', '.')
        return (class_name in self._constructors or
                class_name in self._methods or
                class_name in self._static_fields)

    def has_native_method(self, class_name: str, method_name: str) -> bool:
        class_name = class_name.replace('/', '.')
        return class_name in self._methods and method_name in self._methods[class_name]

    def has_native_constructor(self, class_name: str) -> bool:
        return class_name.replace('/', '.') in self._constructors

    def has_native_static_field(self, class_name: str, field_name: str) -> bool:
        class_name = class_name.replace('/', '.')
        return class_name in self._static_fields and field_name in self._static_fields[class_name]

    def create_native_object(self, class_name: str) -> NativeObject:
        class_name = class_name.replace('/', '.')
        if class_name not in self._constructors:
            raise ValueError(f"No native constructor for {class_name}")
        return self._constructors[class_name]()

    def invoke_native_method(self, class_name: str, method_name: str,
                             obj: Optional[Any], args: list) -> Any:
        class_name = class_name.replace('/', '.')
        if not self.has_native_method(class_name, method_name):
            raise ValueError(f"No native method {class_name}.{method_name}")
        method = self._methods[class_name][method_name]
        return method(obj, *args) if obj is not None else method(*args)

    def get_native_static_field(self, class_name: str, field_name: str) -> Any:
        class_name = class_name.replace('/', '.')
        if not self.has_native_static_field(class_name, field_name):
            raise ValueError(f"No native static field {class_name}.{field_name}")
        return self._static_fields[class_name][field_name]

    def set_native_static_field(self, class_name: str, field_name: str, value: Any):
        class_name = class_name.replace('/', '.')
        if class_name not in self._static_fields:
            self._static_fields[class_name] = {}
        self._static_fields[class_name][field_name] = value


_native_registry = NativeRegistry()


def get_native_registry() -> NativeRegistry:
    return _native_registry
