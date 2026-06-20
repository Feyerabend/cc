import sys
import struct
import math
from typing import List, Any, Optional
from jvm_interpreter.native.native_registry import get_native_registry, NativeObject
from jvm_interpreter.models.java_objects import JavaObject, JavaArray, ObjectFactory, JavaLambdaProxy
from jvm_interpreter.native.java_reflect import (
    JavaClass, JavaMethod, JavaField, JavaConstructor,
    parse_method_descriptor, desc_to_class_name, PUBLIC,
)
from jvm_interpreter.models.class_file_models import ConstantPoolEntry
from jvm_interpreter.constants.jvm_constants import OPCODES
from jvm_interpreter.runtime.class_loader import is_assignable


class _JavaException(Exception):
    """Wraps a Java object thrown by athrow"""
    def __init__(self, java_obj: Any, class_name: str):
        self.java_obj = java_obj
        self.class_name = class_name
        super().__init__(f"Java {class_name}")


def _i32(v: int) -> int:
    v &= 0xFFFFFFFF
    return v - 0x100000000 if v >= 0x80000000 else v


def _i64(v: int) -> int:
    v &= 0xFFFFFFFFFFFFFFFF
    return v - 0x10000000000000000 if v >= 0x8000000000000000 else v


class Interpreter:
    """JVM bytecode interpreter"""

    RETURN_OPCODES = frozenset({172, 173, 174, 175, 176, 177})

    def __init__(self, code: bytes, max_stack: int, max_locals: int,
                 constant_pool: List[ConstantPoolEntry], class_loader: Any,
                 exception_table: list = None, bootstrap_methods: list = None,
                 trace: bool = False, _trace_depth: int = 0,
                 _trace_out=None):
        self.code = list(code)
        self.max_stack = max_stack
        self.max_locals = max_locals
        self.constant_pool = constant_pool
        self.class_loader = class_loader
        self.exception_table = exception_table or []
        self.bootstrap_methods = bootstrap_methods or []
        self._trace = trace
        self._trace_depth = _trace_depth
        self._trace_out = _trace_out if _trace_out is not None else sys.stderr

        self.pc = 0
        self.stack: List[Any] = []
        self.locals: List[Any] = [None] * max_locals

        self.native_registry = get_native_registry()
        self.object_factory = ObjectFactory(self.native_registry)

        self.instructions = {
            0: self.instr_nop,
            1: self.instr_aconst_null,
            2: self.instr_iconst, 3: self.instr_iconst, 4: self.instr_iconst,
            5: self.instr_iconst, 6: self.instr_iconst, 7: self.instr_iconst,
            8: self.instr_iconst,
            9: self.instr_lconst, 10: self.instr_lconst,
            11: self.instr_fconst, 12: self.instr_fconst, 13: self.instr_fconst,
            14: self.instr_dconst, 15: self.instr_dconst,
            16: self.instr_bipush,
            17: self.instr_sipush,
            18: self.instr_ldc,
            19: self.instr_ldc_w,
            20: self.instr_ldc2_w,
            21: self.instr_iload, 22: self.instr_lload, 23: self.instr_fload,
            24: self.instr_dload, 25: self.instr_aload,
            26: self.instr_iload_n, 27: self.instr_iload_n,
            28: self.instr_iload_n, 29: self.instr_iload_n,
            30: self.instr_lload_n, 31: self.instr_lload_n,
            32: self.instr_lload_n, 33: self.instr_lload_n,
            34: self.instr_fload_n, 35: self.instr_fload_n,
            36: self.instr_fload_n, 37: self.instr_fload_n,
            38: self.instr_dload_n, 39: self.instr_dload_n,
            40: self.instr_dload_n, 41: self.instr_dload_n,
            42: self.instr_aload_n, 43: self.instr_aload_n,
            44: self.instr_aload_n, 45: self.instr_aload_n,
            46: self.instr_iaload, 47: self.instr_laload,
            48: self.instr_faload, 49: self.instr_daload,
            50: self.instr_aaload, 51: self.instr_baload,
            52: self.instr_caload, 53: self.instr_saload,
            54: self.instr_istore, 55: self.instr_lstore,
            56: self.instr_fstore, 57: self.instr_dstore,
            58: self.instr_astore,
            59: self.instr_istore_n, 60: self.instr_istore_n,
            61: self.instr_istore_n, 62: self.instr_istore_n,
            63: self.instr_lstore_n, 64: self.instr_lstore_n,
            65: self.instr_lstore_n, 66: self.instr_lstore_n,
            67: self.instr_fstore_n, 68: self.instr_fstore_n,
            69: self.instr_fstore_n, 70: self.instr_fstore_n,
            71: self.instr_dstore_n, 72: self.instr_dstore_n,
            73: self.instr_dstore_n, 74: self.instr_dstore_n,
            75: self.instr_astore_n, 76: self.instr_astore_n,
            77: self.instr_astore_n, 78: self.instr_astore_n,
            79: self.instr_iastore, 80: self.instr_lastore,
            81: self.instr_fastore, 82: self.instr_dastore,
            83: self.instr_aastore, 84: self.instr_bastore,
            85: self.instr_castore, 86: self.instr_sastore,
            87: self.instr_pop, 88: self.instr_pop2,
            89: self.instr_dup,
            90: self.instr_dup_x1, 91: self.instr_dup_x2,
            92: self.instr_dup2, 93: self.instr_dup2_x1, 94: self.instr_dup2_x2,
            95: self.instr_swap,
            96: self.instr_iadd, 97: self.instr_ladd,
            98: self.instr_fadd, 99: self.instr_dadd,
            100: self.instr_isub, 101: self.instr_lsub,
            102: self.instr_fsub, 103: self.instr_dsub,
            104: self.instr_imul, 105: self.instr_lmul,
            106: self.instr_fmul, 107: self.instr_dmul,
            108: self.instr_idiv, 109: self.instr_ldiv,
            110: self.instr_fdiv, 111: self.instr_ddiv,
            112: self.instr_irem, 113: self.instr_lrem,
            114: self.instr_frem, 115: self.instr_drem,
            116: self.instr_ineg, 117: self.instr_lneg,
            118: self.instr_fneg, 119: self.instr_dneg,
            120: self.instr_ishl, 121: self.instr_lshl,
            122: self.instr_ishr, 123: self.instr_lshr,
            124: self.instr_iushr, 125: self.instr_lushr,
            126: self.instr_iand, 127: self.instr_land,
            128: self.instr_ior, 129: self.instr_lor,
            130: self.instr_ixor, 131: self.instr_lxor,
            132: self.instr_iinc,
            133: self.instr_i2l, 134: self.instr_i2f, 135: self.instr_i2d,
            136: self.instr_l2i, 137: self.instr_l2f, 138: self.instr_l2d,
            139: self.instr_f2i, 140: self.instr_f2l, 141: self.instr_f2d,
            142: self.instr_d2i, 143: self.instr_d2l, 144: self.instr_d2f,
            145: self.instr_i2b, 146: self.instr_i2c, 147: self.instr_i2s,
            148: self.instr_lcmp,
            149: self.instr_fcmpl, 150: self.instr_fcmpg,
            151: self.instr_dcmpl, 152: self.instr_dcmpg,
            153: self.instr_ifeq, 154: self.instr_ifne,
            155: self.instr_iflt, 156: self.instr_ifge,
            157: self.instr_ifgt, 158: self.instr_ifle,
            159: self.instr_if_icmpeq, 160: self.instr_if_icmpne,
            161: self.instr_if_icmplt, 162: self.instr_if_icmpge,
            163: self.instr_if_icmpgt, 164: self.instr_if_icmple,
            165: self.instr_if_acmpeq, 166: self.instr_if_acmpne,
            167: self.instr_goto,
            168: self.instr_jsr, 169: self.instr_ret,
            170: self.instr_tableswitch, 171: self.instr_lookupswitch,
            172: self.instr_ireturn, 173: self.instr_lreturn,
            174: self.instr_freturn, 175: self.instr_dreturn,
            176: self.instr_areturn, 177: self.instr_return,
            178: self.instr_getstatic, 179: self.instr_putstatic,
            180: self.instr_getfield, 181: self.instr_putfield,
            182: self.instr_invokevirtual, 183: self.instr_invokespecial,
            184: self.instr_invokestatic, 185: self.instr_invokeinterface,
            186: self.instr_invokedynamic,
            187: self.instr_new,
            188: self.instr_newarray, 189: self.instr_anewarray,
            190: self.instr_arraylength,
            191: self.instr_athrow,
            192: self.instr_checkcast, 193: self.instr_instanceof,
            194: self.instr_monitorenter, 195: self.instr_monitorexit,
            196: self.instr_wide, 197: self.instr_multianewarray,
            198: self.instr_ifnull, 199: self.instr_ifnonnull,
            200: self.instr_goto_w, 201: self.instr_jsr_w,
        }

    def advance(self, n: int = 1) -> int:
        v = 0
        for _ in range(n):
            v = (v << 8) | self.code[self.pc]
            self.pc += 1
        return v

    # ===== Constants =====

    def instr_nop(self): pass
    def instr_aconst_null(self): self.stack.append(None)
    def instr_iconst(self): self.stack.append(self.code[self.pc - 1] - 3)
    def instr_lconst(self): self.stack.append(self.code[self.pc - 1] - 9)
    def instr_fconst(self): self.stack.append(float(self.code[self.pc - 1] - 11))
    def instr_dconst(self): self.stack.append(float(self.code[self.pc - 1] - 14))

    def instr_bipush(self):
        self.stack.append(struct.unpack('!b', bytes([self.advance()]))[0])

    def instr_sipush(self):
        self.stack.append(struct.unpack('!h', bytes([self.advance(), self.advance()]))[0])

    def _ldc_push(self, e):
        if e.tag == 8:    # String
            self.stack.append(self.constant_pool[e.value - 1].value)
        elif e.tag in (3, 4):  # Integer, Float
            self.stack.append(e.value)
        elif e.tag == 7:  # Class literal → JavaClass (enables reflection on class objects)
            self.stack.append(JavaClass(self.constant_pool[e.value - 1].value))
        else:
            raise ValueError(f"Unsupported ldc tag: {e.tag}")

    def instr_ldc(self):
        self._ldc_push(self.constant_pool[self.advance() - 1])

    def instr_ldc_w(self):
        self._ldc_push(self.constant_pool[self.advance(2) - 1])

    def instr_ldc2_w(self):
        e = self.constant_pool[self.advance(2) - 1]
        if e.tag in (5, 6):
            self.stack.append(e.value)
        else:
            raise ValueError(f"Unsupported ldc2_w tag: {e.tag}")

    # ===== Loads =====

    def instr_iload(self): self.stack.append(self.locals[self.advance()])
    def instr_lload(self): self.stack.append(self.locals[self.advance()])
    def instr_fload(self): self.stack.append(self.locals[self.advance()])
    def instr_dload(self): self.stack.append(self.locals[self.advance()])
    def instr_aload(self): self.stack.append(self.locals[self.advance()])

    def instr_iload_n(self): self.stack.append(self.locals[self.code[self.pc - 1] - 26])
    def instr_lload_n(self): self.stack.append(self.locals[self.code[self.pc - 1] - 30])
    def instr_fload_n(self): self.stack.append(self.locals[self.code[self.pc - 1] - 34])
    def instr_dload_n(self): self.stack.append(self.locals[self.code[self.pc - 1] - 38])
    def instr_aload_n(self): self.stack.append(self.locals[self.code[self.pc - 1] - 42])

    def _array_load(self):
        idx = self.stack.pop()
        arr = self.stack.pop()
        if arr is None:
            raise _JavaException(None, "java.lang.NullPointerException")
        try:
            self.stack.append(arr.get(idx))
        except IndexError:
            raise _JavaException(None, "java.lang.ArrayIndexOutOfBoundsException")

    def instr_iaload(self): self._array_load()
    def instr_laload(self): self._array_load()
    def instr_faload(self): self._array_load()
    def instr_daload(self): self._array_load()
    def instr_aaload(self): self._array_load()

    def instr_baload(self):
        idx = self.stack.pop(); arr = self.stack.pop()
        if arr is None: raise _JavaException(None, "java.lang.NullPointerException")
        try:
            v = arr.get(idx)
            if isinstance(v, bool): self.stack.append(1 if v else 0); return
            v = v & 0xFF
            self.stack.append(v - 256 if v >= 128 else v)  # sign-extend byte → int
        except IndexError:
            raise _JavaException(None, "java.lang.ArrayIndexOutOfBoundsException")

    def instr_caload(self):
        idx = self.stack.pop(); arr = self.stack.pop()
        if arr is None: raise _JavaException(None, "java.lang.NullPointerException")
        try:
            v = arr.get(idx)
            self.stack.append(ord(v) if isinstance(v, str) else (v & 0xFFFF))
        except IndexError:
            raise _JavaException(None, "java.lang.ArrayIndexOutOfBoundsException")

    def instr_saload(self): self._array_load()

    # ===== Stores =====

    def instr_istore(self): self.locals[self.advance()] = self.stack.pop()
    def instr_lstore(self): self.locals[self.advance()] = self.stack.pop()
    def instr_fstore(self): self.locals[self.advance()] = self.stack.pop()
    def instr_dstore(self): self.locals[self.advance()] = self.stack.pop()
    def instr_astore(self): self.locals[self.advance()] = self.stack.pop()

    def instr_istore_n(self): self.locals[self.code[self.pc - 1] - 59] = self.stack.pop()
    def instr_lstore_n(self): self.locals[self.code[self.pc - 1] - 63] = self.stack.pop()
    def instr_fstore_n(self): self.locals[self.code[self.pc - 1] - 67] = self.stack.pop()
    def instr_dstore_n(self): self.locals[self.code[self.pc - 1] - 71] = self.stack.pop()
    def instr_astore_n(self): self.locals[self.code[self.pc - 1] - 75] = self.stack.pop()

    def _array_store(self):
        val = self.stack.pop()
        idx = self.stack.pop()
        arr = self.stack.pop()
        if arr is None:
            raise _JavaException(None, "java.lang.NullPointerException")
        try:
            arr.set(idx, val)
        except IndexError:
            raise _JavaException(None, "java.lang.ArrayIndexOutOfBoundsException")

    def instr_iastore(self): self._array_store()
    def instr_lastore(self): self._array_store()
    def instr_fastore(self): self._array_store()
    def instr_dastore(self): self._array_store()
    def instr_aastore(self):
        val = self.stack.pop()
        idx = self.stack.pop()
        arr = self.stack.pop()
        if arr is None:
            raise _JavaException(None, "java.lang.NullPointerException")
        # ArrayStoreException: non-null value must be assignable to component type
        if val is not None:
            ct = arr.component_type.replace('/', '.')  # normalize slash→dot
            # Skip check for Object arrays, unknown types, and array-of-array types
            if ct and ct not in ('java.lang.Object', 'object') and not ct.startswith('['):
                val_cls = getattr(val, 'class_name', None)
                if val_cls is None:
                    val_cls = 'java.lang.String' if isinstance(val, str) else 'java.lang.Object'
                val_cls = val_cls.replace('/', '.')
                if not is_assignable(val_cls, ct, self.class_loader):
                    raise _JavaException(None, "java.lang.ArrayStoreException")
        try:
            arr.set(idx, val)
        except IndexError:
            raise _JavaException(None, "java.lang.ArrayIndexOutOfBoundsException")

    def instr_bastore(self):
        val = self.stack.pop(); idx = self.stack.pop(); arr = self.stack.pop()
        if arr is None: raise _JavaException(None, "java.lang.NullPointerException")
        try:
            if arr.component_type == 'boolean':
                arr.set(idx, bool(val & 1))
            else:                            # byte: truncate to signed 8-bit
                v = val & 0xFF
                arr.set(idx, v - 256 if v >= 128 else v)
        except IndexError:
            raise _JavaException(None, "java.lang.ArrayIndexOutOfBoundsException")

    def instr_castore(self):
        val = self.stack.pop(); idx = self.stack.pop(); arr = self.stack.pop()
        if arr is None: raise _JavaException(None, "java.lang.NullPointerException")
        try:
            arr.set(idx, (ord(val) if isinstance(val, str) else val) & 0xFFFF)
        except IndexError:
            raise _JavaException(None, "java.lang.ArrayIndexOutOfBoundsException")

    def instr_sastore(self): self._array_store()

    # ===== Stack Manipulation =====

    def instr_pop(self): self.stack.pop()
    def instr_pop2(self): self.stack.pop(); self.stack.pop()
    def instr_dup(self): self.stack.append(self.stack[-1])

    def instr_dup_x1(self):
        v1 = self.stack.pop(); v2 = self.stack.pop()
        self.stack.extend([v1, v2, v1])

    def instr_dup_x2(self):
        v1 = self.stack.pop(); v2 = self.stack.pop(); v3 = self.stack.pop()
        self.stack.extend([v1, v3, v2, v1])

    def instr_dup2(self):
        v1 = self.stack[-1]; v2 = self.stack[-2]
        self.stack.extend([v2, v1])

    def instr_dup2_x1(self):
        v1 = self.stack.pop(); v2 = self.stack.pop(); v3 = self.stack.pop()
        self.stack.extend([v2, v1, v3, v2, v1])

    def instr_dup2_x2(self):
        v1 = self.stack.pop(); v2 = self.stack.pop()
        v3 = self.stack.pop(); v4 = self.stack.pop()
        self.stack.extend([v2, v1, v4, v3, v2, v1])

    def instr_swap(self):
        v1 = self.stack.pop(); v2 = self.stack.pop()
        self.stack.extend([v1, v2])

    # ===== Arithmetic =====

    def instr_iadd(self): b=self.stack.pop(); a=self.stack.pop(); self.stack.append(_i32(a+b))
    def instr_ladd(self): b=self.stack.pop(); a=self.stack.pop(); self.stack.append(_i64(a+b))
    def instr_fadd(self): b=self.stack.pop(); a=self.stack.pop(); self.stack.append(a+b)
    def instr_dadd(self): b=self.stack.pop(); a=self.stack.pop(); self.stack.append(a+b)

    def instr_isub(self): b=self.stack.pop(); a=self.stack.pop(); self.stack.append(_i32(a-b))
    def instr_lsub(self): b=self.stack.pop(); a=self.stack.pop(); self.stack.append(_i64(a-b))
    def instr_fsub(self): b=self.stack.pop(); a=self.stack.pop(); self.stack.append(a-b)
    def instr_dsub(self): b=self.stack.pop(); a=self.stack.pop(); self.stack.append(a-b)

    def instr_imul(self): b=self.stack.pop(); a=self.stack.pop(); self.stack.append(_i32(a*b))
    def instr_lmul(self): b=self.stack.pop(); a=self.stack.pop(); self.stack.append(_i64(a*b))
    def instr_fmul(self): b=self.stack.pop(); a=self.stack.pop(); self.stack.append(a*b)
    def instr_dmul(self): b=self.stack.pop(); a=self.stack.pop(); self.stack.append(a*b)

    @staticmethod
    def _trunc_div(a: int, b: int) -> int:
        """Integer division truncating toward zero (Java semantics, exact for all bit widths)."""
        sign = -1 if (a < 0) ^ (b < 0) else 1
        return sign * (abs(a) // abs(b))

    def instr_idiv(self):
        b=self.stack.pop(); a=self.stack.pop()
        if b == 0: raise _JavaException(None, "java.lang.ArithmeticException")
        self.stack.append(_i32(self._trunc_div(a, b)))

    def instr_ldiv(self):
        b=self.stack.pop(); a=self.stack.pop()
        if b == 0: raise _JavaException(None, "java.lang.ArithmeticException")
        self.stack.append(_i64(self._trunc_div(a, b)))

    def _float_div(self, a, b) -> float:
        if math.isnan(a) or math.isnan(b):
            return float('nan')
        if b == 0.0:
            return float('nan') if a == 0.0 else math.copysign(float('inf'), a * b)
        return a / b

    def instr_fdiv(self):
        b=self.stack.pop(); a=self.stack.pop(); self.stack.append(self._float_div(a, b))

    def instr_ddiv(self):
        b=self.stack.pop(); a=self.stack.pop(); self.stack.append(self._float_div(a, b))

    def instr_irem(self):
        b=self.stack.pop(); a=self.stack.pop()
        if b == 0: raise _JavaException(None, "java.lang.ArithmeticException")
        self.stack.append(_i32(a - self._trunc_div(a, b) * b))

    def instr_lrem(self):
        b=self.stack.pop(); a=self.stack.pop()
        if b == 0: raise _JavaException(None, "java.lang.ArithmeticException")
        self.stack.append(_i64(a - self._trunc_div(a, b) * b))

    def _float_rem(self, a, b) -> float:
        if math.isnan(a) or math.isnan(b) or math.isinf(a) or b == 0.0:
            return float('nan')
        if math.isinf(b):
            return a
        return math.fmod(a, b)

    def instr_frem(self):
        b=self.stack.pop(); a=self.stack.pop(); self.stack.append(self._float_rem(a, b))

    def instr_drem(self):
        b=self.stack.pop(); a=self.stack.pop(); self.stack.append(self._float_rem(a, b))

    def instr_ineg(self): self.stack.append(_i32(-self.stack.pop()))
    def instr_lneg(self): self.stack.append(_i64(-self.stack.pop()))
    def instr_fneg(self): self.stack.append(-self.stack.pop())
    def instr_dneg(self): self.stack.append(-self.stack.pop())

    # ===== Shifts =====

    def instr_ishl(self): b=self.stack.pop(); a=self.stack.pop(); self.stack.append(_i32(a << (b & 0x1f)))
    def instr_lshl(self): b=self.stack.pop(); a=self.stack.pop(); self.stack.append(_i64(a << (b & 0x3f)))
    def instr_ishr(self): b=self.stack.pop(); a=self.stack.pop(); self.stack.append(_i32(a >> (b & 0x1f)))
    def instr_lshr(self): b=self.stack.pop(); a=self.stack.pop(); self.stack.append(_i64(a >> (b & 0x3f)))

    def instr_iushr(self):
        b=self.stack.pop(); a=self.stack.pop()
        self.stack.append(_i32((a & 0xFFFFFFFF) >> (b & 0x1f)))

    def instr_lushr(self):
        b=self.stack.pop(); a=self.stack.pop()
        self.stack.append(_i64((a & 0xFFFFFFFFFFFFFFFF) >> (b & 0x3f)))

    # ===== Bitwise =====

    def instr_iand(self): b=self.stack.pop(); a=self.stack.pop(); self.stack.append(_i32(a & b))
    def instr_land(self): b=self.stack.pop(); a=self.stack.pop(); self.stack.append(_i64(a & b))
    def instr_ior(self):  b=self.stack.pop(); a=self.stack.pop(); self.stack.append(_i32(a | b))
    def instr_lor(self):  b=self.stack.pop(); a=self.stack.pop(); self.stack.append(_i64(a | b))
    def instr_ixor(self): b=self.stack.pop(); a=self.stack.pop(); self.stack.append(_i32(a ^ b))
    def instr_lxor(self): b=self.stack.pop(); a=self.stack.pop(); self.stack.append(_i64(a ^ b))

    def instr_iinc(self):
        idx = self.advance()
        c = struct.unpack('!b', bytes([self.advance()]))[0]
        self.locals[idx] = _i32(self.locals[idx] + c)

    # ===== Conversions =====

    def instr_i2l(self): self.stack.append(int(self.stack.pop()))
    def instr_i2f(self): self.stack.append(float(self.stack.pop()))
    def instr_i2d(self): self.stack.append(float(self.stack.pop()))
    def instr_l2i(self): self.stack.append(_i32(int(self.stack.pop())))
    def instr_l2f(self): self.stack.append(float(self.stack.pop()))
    def instr_l2d(self): self.stack.append(float(self.stack.pop()))

    def instr_f2i(self):
        v = self.stack.pop()
        self.stack.append(0 if math.isnan(v) else _i32(int(math.trunc(v))))

    def instr_f2l(self):
        v = self.stack.pop()
        self.stack.append(0 if math.isnan(v) else _i64(int(math.trunc(v))))

    def instr_f2d(self): self.stack.append(float(self.stack.pop()))

    def instr_d2i(self):
        v = self.stack.pop()
        self.stack.append(0 if math.isnan(v) else _i32(int(math.trunc(v))))

    def instr_d2l(self):
        v = self.stack.pop()
        self.stack.append(0 if math.isnan(v) else _i64(int(math.trunc(v))))

    def instr_d2f(self): self.stack.append(float(self.stack.pop()))

    def instr_i2b(self):
        v = self.stack.pop() & 0xFF
        self.stack.append(v - 256 if v >= 128 else v)

    def instr_i2c(self): self.stack.append(self.stack.pop() & 0xFFFF)

    def instr_i2s(self):
        v = self.stack.pop() & 0xFFFF
        self.stack.append(v - 65536 if v >= 32768 else v)

    # ===== Comparisons =====

    def instr_lcmp(self):
        b=self.stack.pop(); a=self.stack.pop()
        self.stack.append(0 if a == b else 1 if a > b else -1)

    def _fcmp(self, nan_val: int):
        b=self.stack.pop(); a=self.stack.pop()
        if math.isnan(a) or math.isnan(b):
            self.stack.append(nan_val)
        else:
            self.stack.append(0 if a == b else 1 if a > b else -1)

    def instr_fcmpl(self): self._fcmp(-1)
    def instr_fcmpg(self): self._fcmp(1)
    def instr_dcmpl(self): self._fcmp(-1)
    def instr_dcmpg(self): self._fcmp(1)

    # ===== Branches =====

    def _off(self) -> int:
        return struct.unpack('!h', bytes([self.advance(), self.advance()]))[0]

    def instr_ifeq(self):
        off = self._off()
        if self.stack.pop() == 0: self.pc = self.pc - 3 + off

    def instr_ifne(self):
        off = self._off()
        if self.stack.pop() != 0: self.pc = self.pc - 3 + off

    def instr_iflt(self):
        off = self._off()
        if self.stack.pop() < 0: self.pc = self.pc - 3 + off

    def instr_ifge(self):
        off = self._off()
        if self.stack.pop() >= 0: self.pc = self.pc - 3 + off

    def instr_ifgt(self):
        off = self._off()
        if self.stack.pop() > 0: self.pc = self.pc - 3 + off

    def instr_ifle(self):
        off = self._off()
        if self.stack.pop() <= 0: self.pc = self.pc - 3 + off

    def instr_if_icmpeq(self):
        off = self._off(); b=self.stack.pop(); a=self.stack.pop()
        if a == b: self.pc = self.pc - 3 + off

    def instr_if_icmpne(self):
        off = self._off(); b=self.stack.pop(); a=self.stack.pop()
        if a != b: self.pc = self.pc - 3 + off

    def instr_if_icmplt(self):
        off = self._off(); b=self.stack.pop(); a=self.stack.pop()
        if a < b: self.pc = self.pc - 3 + off

    def instr_if_icmpge(self):
        off = self._off(); b=self.stack.pop(); a=self.stack.pop()
        if a >= b: self.pc = self.pc - 3 + off

    def instr_if_icmpgt(self):
        off = self._off(); b=self.stack.pop(); a=self.stack.pop()
        if a > b: self.pc = self.pc - 3 + off

    def instr_if_icmple(self):
        off = self._off(); b=self.stack.pop(); a=self.stack.pop()
        if a <= b: self.pc = self.pc - 3 + off

    def instr_if_acmpeq(self):
        off = self._off(); b=self.stack.pop(); a=self.stack.pop()
        if a is b: self.pc = self.pc - 3 + off

    def instr_if_acmpne(self):
        off = self._off(); b=self.stack.pop(); a=self.stack.pop()
        if a is not b: self.pc = self.pc - 3 + off

    def instr_ifnull(self):
        off = self._off()
        if self.stack.pop() is None: self.pc = self.pc - 3 + off

    def instr_ifnonnull(self):
        off = self._off()
        if self.stack.pop() is not None: self.pc = self.pc - 3 + off

    def instr_goto(self):
        off = self._off()
        self.pc = self.pc - 3 + off

    def instr_goto_w(self):
        raw = bytes([self.advance(), self.advance(), self.advance(), self.advance()])
        off = struct.unpack('!i', raw)[0]
        self.pc = self.pc - 5 + off

    def instr_jsr(self):
        """Jump subroutine (pre-Java-6 finally blocks): push return address, jump."""
        off = self._off()              # reads 2 bytes; pc now = opcode_pc + 3
        self.stack.append(self.pc)     # return address = instruction after jsr
        self.pc = self.pc - 3 + off   # jump to opcode_pc + off

    def instr_jsr_w(self):
        """Wide jump subroutine (4-byte offset)."""
        raw = bytes([self.advance(), self.advance(), self.advance(), self.advance()])
        off = struct.unpack('!i', raw)[0]
        self.stack.append(self.pc)     # return address
        self.pc = self.pc - 5 + off

    def instr_ret(self):
        """Return from subroutine: jump to address stored in local variable."""
        idx = self.advance()
        self.pc = self.locals[idx]

    def instr_tableswitch(self):
        opcode_pc = self.pc - 1
        while self.pc % 4 != 0:
            self.pc += 1
        default = struct.unpack('!i', bytes([self.advance(), self.advance(),
                                             self.advance(), self.advance()]))[0]
        low =     struct.unpack('!i', bytes([self.advance(), self.advance(),
                                             self.advance(), self.advance()]))[0]
        high =    struct.unpack('!i', bytes([self.advance(), self.advance(),
                                             self.advance(), self.advance()]))[0]
        offsets = []
        for _ in range(high - low + 1):
            off = struct.unpack('!i', bytes([self.advance(), self.advance(),
                                             self.advance(), self.advance()]))[0]
            offsets.append(off)
        key = self.stack.pop()
        if low <= key <= high:
            self.pc = opcode_pc + offsets[key - low]
        else:
            self.pc = opcode_pc + default

    def instr_lookupswitch(self):
        opcode_pc = self.pc - 1
        while self.pc % 4 != 0:
            self.pc += 1
        default = struct.unpack('!i', bytes([self.advance(), self.advance(),
                                             self.advance(), self.advance()]))[0]
        npairs =  struct.unpack('!i', bytes([self.advance(), self.advance(),
                                             self.advance(), self.advance()]))[0]
        pairs = {}
        for _ in range(npairs):
            k =   struct.unpack('!i', bytes([self.advance(), self.advance(),
                                             self.advance(), self.advance()]))[0]
            off = struct.unpack('!i', bytes([self.advance(), self.advance(),
                                             self.advance(), self.advance()]))[0]
            pairs[k] = off
        key = self.stack.pop()
        self.pc = opcode_pc + (pairs[key] if key in pairs else default)

    # ===== Returns =====

    def instr_ireturn(self): return self.stack.pop()
    def instr_lreturn(self): return self.stack.pop()
    def instr_freturn(self): return self.stack.pop()
    def instr_dreturn(self): return self.stack.pop()
    def instr_areturn(self): return self.stack.pop()
    def instr_return(self):  return None

    # ===== Fields =====

    def instr_getstatic(self):
        index = self.advance(2)
        class_name, field_name = self._resolve_field_ref(index)
        if self.native_registry.has_native_static_field(class_name, field_name):
            self.stack.append(self.native_registry.get_native_static_field(class_name, field_name))
        else:
            self.stack.append(self.class_loader.resolve_field(class_name, field_name))

    def instr_putstatic(self):
        index = self.advance(2)
        class_name, field_name = self._resolve_field_ref(index)
        self.class_loader.set_field(class_name, field_name, self.stack.pop())

    def instr_getfield(self):
        index = self.advance(2)
        _, field_name = self._resolve_field_ref(index)
        obj = self.stack.pop()
        if obj is None:
            raise _JavaException(None, "java.lang.NullPointerException")
        self.stack.append(obj.get_field(field_name) if hasattr(obj, 'get_field')
                          else getattr(obj, field_name, None))

    def instr_putfield(self):
        index = self.advance(2)
        _, field_name = self._resolve_field_ref(index)
        value = self.stack.pop()
        obj = self.stack.pop()
        if obj is None:
            raise _JavaException(None, "java.lang.NullPointerException")
        if hasattr(obj, 'set_field'):
            obj.set_field(field_name, value)
        else:
            setattr(obj, field_name, value)

    # ===== Method Invocation =====

    def instr_invokevirtual(self):
        index = self.advance(2)
        class_name, method_name, descriptor = self._resolve_method_ref(index)
        args = self._pop_args(descriptor)
        obj = self.stack.pop()
        if obj is None:
            raise _JavaException(None, "java.lang.NullPointerException")
        actual = obj.class_name if isinstance(obj, (JavaObject, NativeObject)) else class_name
        result = self._dispatch(actual, method_name, descriptor, obj, args)
        if not descriptor.endswith(')V'):
            self.stack.append(result)

    def instr_invokespecial(self):
        index = self.advance(2)
        class_name, method_name, descriptor = self._resolve_method_ref(index)
        args = self._pop_args(descriptor)
        obj = self.stack.pop()
        if obj is None:
            raise _JavaException(None, "java.lang.NullPointerException")
        result = self._dispatch(class_name, method_name, descriptor, obj, args)
        if not descriptor.endswith(')V'):
            self.stack.append(result)

    def instr_invokestatic(self):
        index = self.advance(2)
        class_name, method_name, descriptor = self._resolve_method_ref(index)
        args = self._pop_args(descriptor)
        result = self._dispatch(class_name, method_name, descriptor, None, args)
        if not descriptor.endswith(')V'):
            self.stack.append(result)

    def instr_invokeinterface(self):
        index = self.advance(2)
        self.advance()  # count byte
        self.advance()  # zero byte
        class_name, method_name, descriptor = self._resolve_method_ref(index)
        args = self._pop_args(descriptor)
        obj = self.stack.pop()
        if obj is None:
            raise _JavaException(None, "java.lang.NullPointerException")
        actual = obj.class_name if isinstance(obj, (JavaObject, NativeObject)) else class_name
        result = self._dispatch(actual, method_name, descriptor, obj, args)
        if not descriptor.endswith(')V'):
            self.stack.append(result)

    def _resolve_method_handle(self, cp_idx: int) -> tuple:
        """Return (ref_kind, class_name, method_name, descriptor) for a MethodHandle CP entry."""
        mh  = self.constant_pool[cp_idx - 1]          # tag 15: (ref_kind, ref_cp_idx)
        ref = self.constant_pool[mh.value[1] - 1]     # tag 10/11: (class_idx, nat_idx)
        cls_ptr = self.constant_pool[ref.value[0] - 1]
        class_name  = self.constant_pool[cls_ptr.value - 1].value.replace('/', '.')
        nat = self.constant_pool[ref.value[1] - 1].value
        method_name = self.constant_pool[nat[0] - 1].value
        descriptor  = self.constant_pool[nat[1] - 1].value
        return mh.value[0], class_name, method_name, descriptor

    def instr_invokedynamic(self):
        index = self.advance(2)
        self.advance(); self.advance()                  # reserved 0, 0
        entry = self.constant_pool[index - 1]           # tag 18: (bsm_idx, nat_cp_idx)
        bootstrap_idx, nat_cp_idx = entry.value

        nat        = self.constant_pool[nat_cp_idx - 1].value
        site_name  = self.constant_pool[nat[0] - 1].value   # abstract method or concat name
        descriptor = self.constant_pool[nat[1] - 1].value   # call-site descriptor

        if not self.bootstrap_methods or bootstrap_idx >= len(self.bootstrap_methods):
            raise ValueError(f"invokedynamic: no bootstrap method at index {bootstrap_idx}")
        bsm = self.bootstrap_methods[bootstrap_idx]

        # Resolve bootstrap class/method via MethodHandle → Methodref chain
        mh           = self.constant_pool[bsm.method_ref_index - 1]
        mref         = self.constant_pool[mh.value[1] - 1]
        bsm_cls_ptr  = self.constant_pool[mref.value[0] - 1]
        bsm_class    = self.constant_pool[bsm_cls_ptr.value - 1].value.replace('/', '.')
        bsm_nat      = self.constant_pool[mref.value[1] - 1].value
        bsm_method   = self.constant_pool[bsm_nat[0] - 1].value

        # ── StringConcatFactory ───────────────────────────────────────────────
        if 'StringConcatFactory' in bsm_class:
            args = self._pop_args(descriptor)
            if bsm_method == 'makeConcatWithConstants' and bsm.arguments:
                recipe_entry = self.constant_pool[bsm.arguments[0] - 1]
                recipe = (self.constant_pool[recipe_entry.value - 1].value
                          if recipe_entry.tag == 8 else recipe_entry.value)
                static_consts = []
                for ai in bsm.arguments[1:]:
                    c = self.constant_pool[ai - 1]
                    static_consts.append(
                        self.constant_pool[c.value - 1].value if c.tag == 8 else c.value)
                result = self._apply_string_recipe(recipe, args, static_consts)
            else:
                result = ''.join(self._to_java_string(a) for a in args)
            if not descriptor.endswith(')V'):
                self.stack.append(result)

        # ── LambdaMetafactory ────────────────────────────────────────────────
        elif 'LambdaMetafactory' in bsm_class:
            captured = self._pop_args(descriptor)       # captured variables from stack
            if len(bsm.arguments) < 2:
                raise ValueError("LambdaMetafactory: need at least 2 bootstrap args")
            ref_kind, impl_cls, impl_mth, impl_dsc = \
                self._resolve_method_handle(bsm.arguments[1])

            # Functional interface name from the call-site return type
            ret = descriptor[descriptor.index(')') + 1:]
            iface = ret[1:-1].replace('/', '.') if ret.startswith('L') and ret.endswith(';') \
                    else 'java.lang.Object'

            # Build an invoke closure (captures everything by value via defaults)
            def _mk_invoke(cap, rk, ic, im, id_, it):
                def _invoke(args):
                    all_args = cap + args
                    if rk in (5, 7, 9):   # virtual / special / interface
                        recv = all_args[0] if all_args else None
                        return it._dispatch(ic, im, id_, recv, all_args[1:])
                    elif rk == 8:          # newInvokeSpecial — allocate + <init>
                        obj = it.object_factory.create_object(ic)
                        it._dispatch(ic, im, id_, obj, all_args)
                        return obj
                    else:                  # 6 = invokeStatic (most lambda bodies)
                        return it._dispatch(ic, im, id_, None, all_args)
                return _invoke

            proxy = JavaLambdaProxy(
                iface, site_name,
                _mk_invoke(list(captured), ref_kind, impl_cls, impl_mth, impl_dsc, self))
            self.stack.append(proxy)

        else:
            raise ValueError(
                f"invokedynamic: unsupported bootstrap {bsm_class}.{bsm_method}")

    def instr_new(self):
        index = self.advance(2)
        class_index = self.constant_pool[index - 1].value
        class_name = self.constant_pool[class_index - 1].value
        self.stack.append(self.object_factory.create_object(class_name))

    def instr_newarray(self):
        atype = self.advance()
        length = self.stack.pop()
        type_map = {4: 'boolean', 5: 'char', 6: 'float', 7: 'double',
                    8: 'byte', 9: 'short', 10: 'int', 11: 'long'}
        self.stack.append(self.object_factory.create_array(type_map.get(atype, 'int'), length))

    def instr_anewarray(self):
        index = self.advance(2)
        class_index = self.constant_pool[index - 1].value
        class_name = self.constant_pool[class_index - 1].value
        length = self.stack.pop()
        self.stack.append(self.object_factory.create_array(class_name, length))

    def instr_arraylength(self):
        arr = self.stack.pop()
        if arr is None:
            raise _JavaException(None, "java.lang.NullPointerException")
        self.stack.append(arr.length)

    def instr_athrow(self):
        exc = self.stack.pop()
        cls = exc.class_name if hasattr(exc, 'class_name') else "java.lang.Throwable"
        raise _JavaException(exc, cls)

    def instr_wide(self):
        _XLOAD  = {21, 22, 23, 24, 25}
        _XSTORE = {54, 55, 56, 57, 58}
        op = self.advance()
        if op == 132:   # iinc with 16-bit index and 16-bit signed constant
            idx   = self.advance(2)
            const = self.advance(2)
            if const >= 32768: const -= 65536
            self.locals[idx] = _i32(self.locals[idx] + const)
        elif op in _XLOAD:
            self.stack.append(self.locals[self.advance(2)])
        elif op in _XSTORE:
            self.locals[self.advance(2)] = self.stack.pop()
        elif op == 169:  # ret (return address from JSR)
            self.pc = self.locals[self.advance(2)]
        else:
            raise ValueError(f"wide: unsupported sub-opcode {op:#04x}")

    def instr_multianewarray(self):
        index      = self.advance(2)
        dimensions = self.advance()
        sizes = [self.stack.pop() for _ in range(dimensions)]
        sizes.reverse()   # stack top was innermost; we want outermost first
        # Decode element type from the descriptor (strip leading '[')
        class_index = self.constant_pool[index - 1].value
        desc = self.constant_pool[class_index - 1].value  # e.g. "[[I"
        depth = 0
        while depth < len(desc) and desc[depth] == '[':
            depth += 1
        base = desc[depth:]
        _PRIM = {'I': 'int', 'J': 'long', 'F': 'float', 'D': 'double',
                 'Z': 'boolean', 'B': 'byte', 'S': 'short', 'C': 'char'}
        if base in _PRIM:
            elem_type = _PRIM[base]
        elif base.startswith('L') and base.endswith(';'):
            elem_type = base[1:-1].replace('/', '.')
        else:
            elem_type = base

        def _make(dim_idx: int):
            size = sizes[dim_idx]
            if dim_idx == len(sizes) - 1:
                return self.object_factory.create_array(elem_type, size)
            arr = self.object_factory.create_array('java.lang.Object', size)
            for i in range(size):
                arr.set(i, _make(dim_idx + 1))
            return arr

        self.stack.append(_make(0))

    def instr_monitorenter(self): self.stack.pop()   # no-op (single-threaded)
    def instr_monitorexit(self):  self.stack.pop()   # no-op

    def instr_checkcast(self):
        index = self.advance(2)
        obj = self.stack[-1]   # peek — leave on stack
        if obj is None:
            return              # null passes any cast
        class_index = self.constant_pool[index - 1].value
        target = self.constant_pool[class_index - 1].value.replace('/', '.')
        actual = obj.class_name if hasattr(obj, 'class_name') else type(obj).__name__
        if not is_assignable(actual, target, self.class_loader):
            raise _JavaException(None, "java.lang.ClassCastException")

    def instr_instanceof(self):
        index = self.advance(2)
        class_index = self.constant_pool[index - 1].value
        target = self.constant_pool[class_index - 1].value.replace('/', '.')
        obj = self.stack.pop()
        if obj is None:
            self.stack.append(0)
        else:
            actual = obj.class_name if hasattr(obj, 'class_name') else type(obj).__name__
            self.stack.append(1 if is_assignable(actual, target, self.class_loader) else 0)

    # ===== Helpers =====

    def _resolve_field_ref(self, index: int) -> tuple:
        fr = self.constant_pool[index - 1]
        cls_ptr = self.constant_pool[fr.value[0] - 1]
        class_name = self.constant_pool[cls_ptr.value - 1].value.replace('/', '.')
        nat = self.constant_pool[fr.value[1] - 1].value
        field_name = self.constant_pool[nat[0] - 1].value
        return class_name, field_name

    def _resolve_method_ref(self, index: int) -> tuple:
        mr = self.constant_pool[index - 1]
        cls_ptr = self.constant_pool[mr.value[0] - 1]
        class_name = self.constant_pool[cls_ptr.value - 1].value.replace('/', '.')
        nat = self.constant_pool[mr.value[1] - 1].value
        method_name = self.constant_pool[nat[0] - 1].value
        descriptor = self.constant_pool[nat[1] - 1].value
        return class_name, method_name, descriptor

    # ===== Trace helpers =====

    def _fmt_val(self, v) -> str:
        if v is None:            return 'null'
        if isinstance(v, bool):  return 'true' if v else 'false'
        if isinstance(v, int):   return str(v)
        if isinstance(v, float):
            if math.isnan(v):    return 'NaN'
            if math.isinf(v):    return 'Inf' if v > 0 else '-Inf'
            return str(v)
        if isinstance(v, str):
            s = v if len(v) <= 14 else v[:11] + '...'
            return f'"{s}"'
        if hasattr(v, 'class_name'):
            return f'<{v.class_name.rsplit(".", 1)[-1]}>'
        return repr(v)[:16]

    def _fmt_stack(self) -> str:
        return '[' + ', '.join(self._fmt_val(v) for v in self.stack) + ']'

    def _to_java_string(self, v) -> str:
        if v is None:
            return "null"
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, float):
            if math.isnan(v):  return "NaN"
            if math.isinf(v):  return "Infinity" if v > 0 else "-Infinity"
            return str(v)
        if hasattr(v, 'class_name') and self.native_registry.has_native_method(
                v.class_name, 'toString'):
            return self.native_registry.invoke_native_method(
                v.class_name, 'toString', v, [])
        return str(v)

    def _apply_string_recipe(self, recipe: str, dynamic_args: list,
                             static_consts: list) -> str:
        """Apply a StringConcatFactory recipe: \\x01=dynamic arg, \\x02=static const."""
        parts = []
        dyn_i = const_i = 0
        for ch in recipe:
            if ch == '\x01':
                parts.append(self._to_java_string(
                    dynamic_args[dyn_i] if dyn_i < len(dynamic_args) else ''))
                dyn_i += 1
            elif ch == '\x02':
                parts.append(self._to_java_string(
                    static_consts[const_i] if const_i < len(static_consts) else ''))
                const_i += 1
            else:
                parts.append(ch)
        return ''.join(parts)

    def _count_args(self, descriptor: str) -> int:
        """Count parameters in a JVM method descriptor.
        Handles primitives (BCDFIJSZ), reference types (Lclass;), and arrays ([...)."""
        if not descriptor.startswith('('):
            return 0
        i = 1
        count = 0
        while i < len(descriptor) and descriptor[i] != ')':
            c = descriptor[i]
            if c in 'BCDFIJSZ':
                count += 1
                i += 1
            elif c == 'L':
                count += 1
                i = descriptor.index(';', i) + 1
            elif c == '[':
                while descriptor[i] == '[':
                    i += 1
                if descriptor[i] == 'L':
                    i = descriptor.index(';', i) + 1
                else:
                    i += 1
                count += 1
            else:
                break
        return count

    def _pop_args(self, descriptor: str) -> list:
        count = self._count_args(descriptor)
        args = [self.stack.pop() for _ in range(count)]
        args.reverse()
        return args

    def _find_native_class_for(self, class_name: str, method_name: str) -> Optional[str]:
        """BFS over type hierarchy to find the nearest class with `method_name` as native."""
        from jvm_interpreter.runtime.class_loader import _BUILTIN_SUPERS
        visited: set = set()
        frontier = [class_name]
        while frontier:
            cls = frontier.pop()
            if cls in visited:
                continue
            visited.add(cls)
            if self.native_registry.has_native_method(cls, method_name):
                return cls
            entry = _BUILTIN_SUPERS.get(cls)
            if entry is not None:
                super_cls, ifaces = entry
                if super_cls:
                    frontier.append(super_cls)
                frontier.extend(ifaces)
            elif self.class_loader is not None:
                try:
                    cf = self.class_loader.load_class(cls)
                    if cf.super_class and cf.super_class.name:
                        frontier.append(cf.super_class.name)
                    for iface in cf.interfaces:
                        frontier.append(iface.name)
                except Exception:
                    pass
        return None

    def _dispatch(self, class_name: str, method_name: str, descriptor: str,
                  obj: Optional[Any], args: list) -> Any:
        def _trace_native(cls):
            if self._trace:
                indent = '  ' * self._trace_depth
                short = cls.rsplit('.', 1)[-1]
                print(f"{indent}      [native] {short}.{method_name}", file=self._trace_out)

        # Lambda / method-reference proxy — call the underlying implementation directly
        if isinstance(obj, JavaLambdaProxy):
            return obj.invoke(args)

        # Array pseudo-methods (arrays have no class file; dispatch them directly)
        if isinstance(obj, JavaArray):
            if method_name == 'clone':
                new_arr = JavaArray(obj.component_type, obj.length)
                new_arr.elements = list(obj.elements)
                return new_arr
            if method_name == 'toString':
                _type_chars = {'int': 'I', 'long': 'J', 'float': 'F', 'double': 'D',
                               'boolean': 'Z', 'char': 'C', 'byte': 'B', 'short': 'S'}
                tc = _type_chars.get(obj.component_type,
                                     'L' + obj.component_type.replace('.', '/') + ';')
                return f'[{tc}@{hex(id(obj))[2:]}'
            if method_name == 'hashCode':  return id(obj)
            if method_name == 'equals':    return obj is args[0] if args else False
            if method_name == 'getClass':  return JavaClass(obj.class_name)
            if method_name == 'length':    return obj.length   # rare but possible
            # Anything else on an array: fall through and let it fail naturally

        # Universal getClass() — must come before the registry (registry falls back
        # to self.getClass() which fails for plain Python objects like str).
        if method_name == 'getClass' and not args:
            return self._get_object_class(obj)

        # Static Class.forName(name) — needs the class-loader, so intercepted here.
        if obj is None and class_name == 'java.lang.Class' and method_name == 'forName':
            name = (str(args[0]) if args else '').replace('/', '.')
            if self.class_loader:
                try: self.class_loader.load_class(name)
                except Exception: pass
            return JavaClass(name)

        # Reflection object dispatch — instance methods on Class/Method/Field/Constructor
        if isinstance(obj, JavaClass):
            return self._dispatch_java_class(obj, method_name, args)
        if isinstance(obj, JavaMethod):
            return self._dispatch_java_method(obj, method_name, args)
        if isinstance(obj, JavaField):
            return self._dispatch_java_field(obj, method_name, args)
        if isinstance(obj, JavaConstructor):
            return self._dispatch_java_constructor(obj, method_name, args)

        # 1. Direct native method (fast path)
        if self.native_registry.has_native_method(class_name, method_name):
            _trace_native(class_name)
            return self.native_registry.invoke_native_method(class_name, method_name, obj, args)

        # 2. Bytecode method (walks superclass chain via class loader)
        if self.class_loader is not None:
            code = self.class_loader.get_method_code(class_name, method_name, descriptor)
            if code is not None:
                return self._invoke_bytecode_method(class_name, method_name, descriptor, obj, args)

        # 3. Inherited native method (user class extends a native stdlib class)
        native_cls = self._find_native_class_for(class_name, method_name)
        if native_cls:
            _trace_native(native_cls)
            return self.native_registry.invoke_native_method(native_cls, method_name, obj, args)

        raise ValueError(f"Method not found: {class_name}.{method_name}{descriptor}")

    def _invoke_bytecode_method(self, class_name: str, method_name: str,
                                descriptor: str, obj: Optional[Any], args: list) -> Any:
        code = self.class_loader.get_method_code(class_name, method_name, descriptor)
        if not code:
            raise ValueError(f"Method not found: {class_name}.{method_name}{descriptor}")
        # code[4] = defining_class: the class that actually owns this bytecode.
        # Its CP must be used — not the called class's CP — so inherited methods
        # resolve their own CP indices correctly.
        defining_class = code[4] if len(code) > 4 else class_name
        class_file = self.class_loader.load_class(defining_class)
        exc_table = code[3] if len(code) > 3 else []
        bsm = self.class_loader.get_bootstrap_methods(defining_class) \
              if self.class_loader else []

        if self._trace:
            indent = '  ' * self._trace_depth
            # Show both receiver class and defining class when they differ
            recv = class_name.rsplit('.', 1)[-1]
            defn = defining_class.rsplit('.', 1)[-1]
            label = f"{recv}({defn})" if recv != defn else recv
            print(f"{indent}>> {label}.{method_name}{descriptor}",
                  file=self._trace_out)

        sub = Interpreter(code[2], code[0], code[1],
                          class_file.constant_pool, self.class_loader, exc_table, bsm,
                          trace=self._trace, _trace_depth=self._trace_depth + 1,
                          _trace_out=self._trace_out)
        slot = 0
        if obj is not None:
            sub.locals[slot] = obj
            slot += 1
        # Assign args respecting 2-slot layout for long (J) and double (D)
        di = 1  # index into descriptor, past '('
        for arg in args:
            sub.locals[slot] = arg
            c = descriptor[di] if di < len(descriptor) else ')'
            if c == '[':
                while di < len(descriptor) and descriptor[di] == '[':
                    di += 1
                if di < len(descriptor) and descriptor[di] == 'L':
                    di = descriptor.index(';', di) + 1
                else:
                    di += 1
                slot += 1
            elif c == 'L':
                di = descriptor.index(';', di) + 1
                slot += 1
            elif c in 'JD':   # category-2: occupies 2 local variable slots
                di += 1
                slot += 2
            else:
                di += 1
                slot += 1

        result = sub.run()

        if self._trace:
            indent = '  ' * self._trace_depth
            recv = class_name.rsplit('.', 1)[-1]
            defn = defining_class.rsplit('.', 1)[-1]
            label = f"{recv}({defn})" if recv != defn else recv
            print(f"{indent}<< {label}.{method_name} -> {self._fmt_val(result)}",
                  file=self._trace_out)

        return result

    # ===== Reflection helpers =====

    def _get_object_class(self, obj) -> JavaClass:
        """Return a JavaClass representing the runtime type of any value."""
        if isinstance(obj, JavaClass):
            return JavaClass('java.lang.Class')
        if isinstance(obj, JavaArray):
            return JavaClass(obj.class_name)
        cn = getattr(obj, 'class_name', None)
        if cn:
            return JavaClass(cn.replace('/', '.'))
        if isinstance(obj, str):   return JavaClass('java.lang.String')
        if isinstance(obj, bool):  return JavaClass('java.lang.Boolean')
        if isinstance(obj, int):   return JavaClass('java.lang.Integer')
        if isinstance(obj, float): return JavaClass('java.lang.Double')
        return JavaClass('java.lang.Object')

    def _dispatch_java_class(self, obj: JavaClass, method_name: str, args: list):
        cn = obj._class_name
        if method_name == 'getName':           return obj.getName()
        if method_name == 'getCanonicalName':  return obj.getCanonicalName()
        if method_name == 'getSimpleName':     return obj.getSimpleName()
        if method_name == 'getTypeName':       return obj.getTypeName()
        if method_name == 'toString':          return obj.toString()
        if method_name == 'isPrimitive':       return obj.isPrimitive()
        if method_name == 'isArray':           return obj.isArray()
        if method_name == 'isInterface':       return self._reflect_is_interface(cn)
        if method_name == 'isEnum':            return False
        if method_name == 'isAnnotation':      return False
        if method_name == 'isSynthetic':       return False
        if method_name == 'isAnonymousClass':  return False
        if method_name == 'isMemberClass':     return False
        if method_name == 'equals':
            return obj.equals(args[0]) if args else False
        if method_name == 'hashCode':          return obj.hashCode()
        if method_name == 'getClass':          return JavaClass('java.lang.Class')

        if method_name == 'isInstance':
            target = args[0] if args else None
            if target is None: return False
            actual = getattr(target, 'class_name', None)
            if actual is None:
                if isinstance(target, str):   actual = 'java.lang.String'
                elif isinstance(target, bool): actual = 'java.lang.Boolean'
                elif isinstance(target, int):  actual = 'java.lang.Integer'
                elif isinstance(target, float):actual = 'java.lang.Double'
                else:                          actual = 'java.lang.Object'
            return is_assignable(actual.replace('/', '.'), cn, self.class_loader)

        if method_name == 'getSuperclass':     return self._reflect_superclass(cn)
        if method_name == 'getInterfaces':     return self._reflect_interfaces(cn)
        if method_name == 'getModifiers':      return self._reflect_class_modifiers(cn)
        if method_name == 'getMethods':        return self._reflect_methods(cn, False)
        if method_name == 'getDeclaredMethods':return self._reflect_methods(cn, True)
        if method_name == 'getFields':         return self._reflect_fields(cn, False)
        if method_name == 'getDeclaredFields': return self._reflect_fields(cn, True)
        if method_name in ('getMethod', 'getDeclaredMethod'):
            mname = str(args[0]) if args else ''
            param_cls = list(args[1:]) if len(args) > 1 else []
            return self._reflect_get_method(cn, mname, param_cls,
                                            method_name == 'getDeclaredMethod')
        if method_name in ('getField', 'getDeclaredField'):
            fname = str(args[0]) if args else ''
            return self._reflect_get_field(cn, fname)
        if method_name in ('getConstructors', 'getDeclaredConstructors'):
            return self._reflect_constructors(cn)
        if method_name in ('getConstructor', 'getDeclaredConstructor'):
            param_cls = list(args) if args else []
            return self._reflect_get_constructor(cn, param_cls)
        if method_name == 'newInstance':
            new_obj = self.object_factory.create_object(cn)
            try: self._dispatch(cn, '<init>', '()V', new_obj, [])
            except ValueError: pass   # <init> not found for native class — fine
            return new_obj
        if method_name == 'cast':
            return args[0] if args else None
        if method_name == 'getEnumConstants': return None
        if method_name == 'getComponentType':
            if obj.isArray() and cn.startswith('['):
                return JavaClass(desc_to_class_name(cn[1:]))
            return None
        if method_name == 'forName':
            name = (str(args[0]) if args else '').replace('/', '.')
            return JavaClass(name)
        if method_name == 'desiredAssertionStatus': return False
        return None  # unrecognized — don't raise

    def _dispatch_java_method(self, obj: JavaMethod, method_name: str, args: list):
        if method_name == 'invoke':
            target    = args[0] if args else None
            args_arr  = args[1] if len(args) > 1 else None
            call_args = []
            if isinstance(args_arr, JavaArray):
                call_args = list(args_arr.elements[:args_arr.length])
            actual = self._get_object_class(target)._class_name if target is not None \
                     else obj._owner_class
            return self._dispatch(actual.replace('/', '.'), obj._method_name,
                                  obj._descriptor, target, call_args)
        if method_name == 'getName':           return obj.getName()
        if method_name == 'toString':          return obj.toString()
        if method_name == 'getModifiers':      return obj.getModifiers()
        if method_name == 'setAccessible':     obj.setAccessible(args[0] if args else True); return None
        if method_name == 'isAccessible':      return obj.isAccessible()
        if method_name == 'trySetAccessible':  obj.setAccessible(True); return True
        if method_name == 'getDeclaringClass': return JavaClass(obj._owner_class)
        if method_name == 'getReturnType':
            _, ret = parse_method_descriptor(obj._descriptor)
            return JavaClass(desc_to_class_name(ret))
        if method_name == 'getParameterTypes':
            params, _ = parse_method_descriptor(obj._descriptor)
            arr = JavaArray('java.lang.Class', len(params))
            for i, p in enumerate(params): arr.elements[i] = JavaClass(desc_to_class_name(p))
            return arr
        if method_name == 'getParameterCount':
            params, _ = parse_method_descriptor(obj._descriptor)
            return len(params)
        if method_name in ('equals', 'hashCode'):
            return obj.equals(args[0]) if method_name == 'equals' else obj.hashCode()
        if method_name == 'getClass': return JavaClass('java.lang.reflect.Method')
        return None

    def _dispatch_java_field(self, obj: JavaField, method_name: str, args: list):
        if method_name == 'get':
            target = args[0] if args else None
            if target is None:
                return self.class_loader.resolve_field(obj._owner_class, obj._field_name) \
                       if self.class_loader else None
            return target.get_field(obj._field_name) if hasattr(target, 'get_field') else None
        if method_name == 'set':
            target = args[0] if args else None
            value  = args[1] if len(args) > 1 else None
            if target is None:
                if self.class_loader: self.class_loader.set_field(obj._owner_class, obj._field_name, value)
            elif hasattr(target, 'set_field'):
                target.set_field(obj._field_name, value)
            return None
        # Primitive typed getters — just forward to get() and let caller coerce
        if method_name in ('getInt', 'getLong', 'getFloat', 'getDouble',
                           'getBoolean', 'getByte', 'getChar', 'getShort'):
            target = args[0] if args else None
            if target is None:
                return self.class_loader.resolve_field(obj._owner_class, obj._field_name) \
                       if self.class_loader else 0
            return target.get_field(obj._field_name) if hasattr(target, 'get_field') else 0
        if method_name in ('setInt', 'setLong', 'setFloat', 'setDouble',
                           'setBoolean', 'setByte', 'setChar', 'setShort'):
            target = args[0] if args else None
            value  = args[1] if len(args) > 1 else None
            if target is None:
                if self.class_loader: self.class_loader.set_field(obj._owner_class, obj._field_name, value)
            elif hasattr(target, 'set_field'):
                target.set_field(obj._field_name, value)
            return None
        if method_name == 'getName':           return obj.getName()
        if method_name == 'toString':          return obj.toString()
        if method_name == 'getModifiers':      return obj.getModifiers()
        if method_name == 'setAccessible':     obj.setAccessible(args[0] if args else True); return None
        if method_name == 'isAccessible':      return obj.isAccessible()
        if method_name == 'trySetAccessible':  obj.setAccessible(True); return True
        if method_name == 'getDeclaringClass': return JavaClass(obj._owner_class)
        if method_name == 'getType':
            return JavaClass(desc_to_class_name(obj._type_desc))
        if method_name in ('equals', 'hashCode'):
            return obj.equals(args[0]) if method_name == 'equals' else obj.hashCode()
        if method_name == 'getClass': return JavaClass('java.lang.reflect.Field')
        return None

    def _dispatch_java_constructor(self, obj: JavaConstructor, method_name: str, args: list):
        if method_name == 'newInstance':
            args_arr  = args[0] if args else None
            call_args = []
            if isinstance(args_arr, JavaArray):
                call_args = list(args_arr.elements[:args_arr.length])
            new_obj = self.object_factory.create_object(obj._owner_class)
            self._dispatch(obj._owner_class, '<init>', obj._descriptor, new_obj, call_args)
            return new_obj
        if method_name == 'getName':           return obj.getName()
        if method_name == 'toString':          return obj.toString()
        if method_name == 'getModifiers':      return obj.getModifiers()
        if method_name == 'setAccessible':     obj.setAccessible(args[0] if args else True); return None
        if method_name == 'isAccessible':      return obj.isAccessible()
        if method_name == 'trySetAccessible':  obj.setAccessible(True); return True
        if method_name == 'getDeclaringClass': return JavaClass(obj._owner_class)
        if method_name == 'getParameterTypes':
            params, _ = parse_method_descriptor(obj._descriptor)
            arr = JavaArray('java.lang.Class', len(params))
            for i, p in enumerate(params): arr.elements[i] = JavaClass(desc_to_class_name(p))
            return arr
        if method_name == 'getParameterCount':
            params, _ = parse_method_descriptor(obj._descriptor)
            return len(params)
        if method_name in ('equals', 'hashCode'):
            return obj.equals(args[0]) if method_name == 'equals' else obj.hashCode()
        if method_name == 'getClass': return JavaClass('java.lang.reflect.Constructor')
        return None

    # ---- Class introspection internals ----

    _KNOWN_INTERFACES = frozenset({
        'java.lang.Iterable', 'java.lang.Comparable', 'java.lang.CharSequence',
        'java.io.Serializable', 'java.io.Closeable', 'java.io.AutoCloseable',
        'java.util.Collection', 'java.util.List', 'java.util.Set', 'java.util.Map',
        'java.util.Queue', 'java.util.Deque', 'java.util.SortedSet', 'java.util.NavigableSet',
        'java.util.SortedMap', 'java.util.NavigableMap', 'java.util.RandomAccess',
        'java.lang.Runnable', 'java.util.concurrent.Callable',
        'java.util.function.Function', 'java.util.function.Consumer',
        'java.util.function.Supplier', 'java.util.function.Predicate',
        'java.util.function.BiFunction', 'java.util.function.BiConsumer',
        'java.util.function.BiPredicate', 'java.util.function.UnaryOperator',
        'java.util.function.BinaryOperator', 'java.util.Comparator',
        'java.util.stream.Stream', 'java.util.stream.IntStream',
        'java.util.stream.BaseStream', 'java.util.stream.Collector',
        'java.io.Reader', 'java.io.Writer', 'java.io.InputStream', 'java.io.OutputStream',
        'java.nio.file.Path',
    })

    def _reflect_is_interface(self, class_name: str) -> bool:
        if class_name in self._KNOWN_INTERFACES:
            return True
        if self.class_loader:
            try:
                cf = self.class_loader.load_class(class_name)
                return bool(cf.access.value & 0x0200)
            except Exception:
                pass
        return False

    def _reflect_superclass(self, class_name: str):
        from jvm_interpreter.runtime.class_loader import _BUILTIN_SUPERS
        if class_name in ('java.lang.Object', 'void') or JavaClass(class_name).isPrimitive():
            return None
        entry = _BUILTIN_SUPERS.get(class_name)
        if entry is not None:
            super_name, _ = entry
            return JavaClass(super_name) if super_name else None
        if self.class_loader:
            try:
                cf = self.class_loader.load_class(class_name)
                sn = cf.super_class.name
                if sn: return JavaClass(sn.replace('/', '.'))
            except Exception:
                pass
        return JavaClass('java.lang.Object')

    def _reflect_interfaces(self, class_name: str) -> JavaArray:
        from jvm_interpreter.runtime.class_loader import _BUILTIN_SUPERS
        ifaces = []
        entry = _BUILTIN_SUPERS.get(class_name)
        if entry is not None:
            _, iface_names = entry
            ifaces = [JavaClass(n) for n in iface_names]
        elif self.class_loader:
            try:
                cf = self.class_loader.load_class(class_name)
                ifaces = [JavaClass(i.name.replace('/', '.')) for i in cf.interfaces]
            except Exception:
                pass
        arr = JavaArray('java.lang.Class', len(ifaces))
        for i, c in enumerate(ifaces): arr.elements[i] = c
        return arr

    def _reflect_class_modifiers(self, class_name: str) -> int:
        if self.class_loader:
            try:
                cf = self.class_loader.load_class(class_name)
                return cf.access.value
            except Exception:
                pass
        return PUBLIC

    def _reflect_class_chain(self, class_name: str) -> list:
        """Return [class_name, super, ...] stopping before java.lang.Object."""
        from jvm_interpreter.runtime.class_loader import _BUILTIN_SUPERS
        chain = []
        cn, visited = class_name, set()
        while cn and cn not in ('java.lang.Object', '') and cn not in visited:
            visited.add(cn); chain.append(cn)
            entry = _BUILTIN_SUPERS.get(cn)
            if entry:
                cn = entry[0] or ''
            elif self.class_loader:
                try:
                    cf = self.class_loader.load_class(cn)
                    cn = cf.super_class.name.replace('/', '.') if cf.super_class else ''
                except Exception:
                    break
            else:
                break
        return chain

    def _reflect_methods(self, class_name: str, declared_only: bool) -> JavaArray:
        from jvm_interpreter.models.class_file_models import CodeAttribute
        classes = [class_name] if declared_only else self._reflect_class_chain(class_name)
        seen, methods = set(), []
        for cn in classes:
            if self.class_loader:
                try:
                    cf = self.class_loader.load_class(cn)
                    for m in cf.methods:
                        if m.name.startswith('<'): continue
                        sig = (m.name, m.descriptor)
                        if sig not in seen:
                            seen.add(sig)
                            methods.append(JavaMethod(cn, m.name, m.descriptor, m.access.value))
                    continue
                except Exception:
                    pass
            # Fall back to native registry
            for mname in self.native_registry._methods.get(cn, {}):
                if not mname.startswith('<'):
                    sig = (mname, '')
                    if sig not in seen:
                        seen.add(sig)
                        methods.append(JavaMethod(cn, mname, '()Ljava/lang/Object;', PUBLIC))
        arr = JavaArray('java.lang.reflect.Method', len(methods))
        for i, m in enumerate(methods): arr.elements[i] = m
        return arr

    def _reflect_fields(self, class_name: str, declared_only: bool) -> JavaArray:
        classes = [class_name] if declared_only else self._reflect_class_chain(class_name)
        seen, fields = set(), []
        for cn in classes:
            if self.class_loader:
                try:
                    cf = self.class_loader.load_class(cn)
                    for f in cf.fields:
                        if f.name not in seen:
                            seen.add(f.name)
                            fields.append(JavaField(cn, f.name, f.descriptor, f.access.value))
                    continue
                except Exception:
                    pass
        arr = JavaArray('java.lang.reflect.Field', len(fields))
        for i, f in enumerate(fields): arr.elements[i] = f
        return arr

    def _reflect_get_method(self, class_name: str, name: str, param_cls: list,
                            declared_only: bool) -> JavaMethod:
        classes = [class_name] if declared_only else self._reflect_class_chain(class_name)
        for cn in classes:
            if self.class_loader:
                try:
                    cf = self.class_loader.load_class(cn)
                    for m in cf.methods:
                        if m.name == name:
                            return JavaMethod(cn, m.name, m.descriptor, m.access.value)
                except Exception:
                    pass
            if self.native_registry.has_native_method(cn, name):
                return JavaMethod(cn, name, '()Ljava/lang/Object;', PUBLIC)
        raise _JavaException(None, 'java.lang.NoSuchMethodException')

    def _reflect_get_field(self, class_name: str, field_name: str) -> JavaField:
        for cn in self._reflect_class_chain(class_name):
            if self.class_loader:
                try:
                    cf = self.class_loader.load_class(cn)
                    for f in cf.fields:
                        if f.name == field_name:
                            return JavaField(cn, f.name, f.descriptor, f.access.value)
                except Exception:
                    pass
        raise _JavaException(None, 'java.lang.NoSuchFieldException')

    def _reflect_constructors(self, class_name: str) -> JavaArray:
        ctors = []
        if self.class_loader:
            try:
                cf = self.class_loader.load_class(class_name)
                for m in cf.methods:
                    if m.name == '<init>':
                        ctors.append(JavaConstructor(class_name, m.descriptor, m.access.value))
            except Exception:
                pass
        if not ctors:
            ctors = [JavaConstructor(class_name, '()V', PUBLIC)]
        arr = JavaArray('java.lang.reflect.Constructor', len(ctors))
        for i, c in enumerate(ctors): arr.elements[i] = c
        return arr

    def _reflect_get_constructor(self, class_name: str, param_cls: list) -> JavaConstructor:
        if self.class_loader:
            try:
                cf = self.class_loader.load_class(class_name)
                for m in cf.methods:
                    if m.name == '<init>':
                        return JavaConstructor(class_name, m.descriptor, m.access.value)
            except Exception:
                pass
        return JavaConstructor(class_name, '()V', PUBLIC)

    def _find_exception_handler(self, throw_pc: int, exc_class: str) -> Optional[int]:
        """Search exception table for a handler covering throw_pc."""
        for start, end, handler, catch_type_idx in self.exception_table:
            if start <= throw_pc < end:
                if catch_type_idx == 0:   # catch-all (finally)
                    return handler
                try:
                    cls_entry = self.constant_pool[catch_type_idx - 1]
                    name_entry = self.constant_pool[cls_entry.value - 1]
                    catch_class = name_entry.value.replace('/', '.')
                    if is_assignable(exc_class, catch_class, self.class_loader):
                        return handler
                except (IndexError, AttributeError):
                    pass
        return None

    def run(self) -> Optional[Any]:
        """Execute bytecode until a return instruction."""
        indent = '  ' * self._trace_depth
        while self.pc < len(self.code):
            throw_pc = self.pc
            opcode = self.advance()

            if opcode not in self.instructions:
                raise ValueError(f"Unsupported opcode: {opcode} at pc={self.pc - 1}")

            if self._trace:
                name = OPCODES.get(opcode, (f'?{opcode}', 0))[0]
                print(f"{indent}{throw_pc:04d}  {name:<20} {self._fmt_stack()}",
                      file=self._trace_out)

            try:
                result = self.instructions[opcode]()
            except _JavaException as exc:
                handler = self._find_exception_handler(throw_pc, exc.class_name)
                if handler is not None:
                    self.stack.clear()
                    self.stack.append(exc.java_obj)
                    self.pc = handler
                    continue
                raise

            if opcode in self.RETURN_OPCODES:
                return result

        return None
