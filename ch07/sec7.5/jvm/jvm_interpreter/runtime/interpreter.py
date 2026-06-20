import struct
import math
from typing import List, Any, Optional
from jvm_interpreter.native.native_registry import get_native_registry, NativeObject
from jvm_interpreter.models.java_objects import JavaObject, JavaArray, ObjectFactory
from jvm_interpreter.models.class_file_models import ConstantPoolEntry


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
                 exception_table: list = None):
        self.code = list(code)
        self.max_stack = max_stack
        self.max_locals = max_locals
        self.constant_pool = constant_pool
        self.class_loader = class_loader
        self.exception_table = exception_table or []

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
            170: self.instr_tableswitch, 171: self.instr_lookupswitch,
            172: self.instr_ireturn, 173: self.instr_lreturn,
            174: self.instr_freturn, 175: self.instr_dreturn,
            176: self.instr_areturn, 177: self.instr_return,
            178: self.instr_getstatic, 179: self.instr_putstatic,
            180: self.instr_getfield, 181: self.instr_putfield,
            182: self.instr_invokevirtual, 183: self.instr_invokespecial,
            184: self.instr_invokestatic, 185: self.instr_invokeinterface,
            187: self.instr_new,
            188: self.instr_newarray, 189: self.instr_anewarray,
            190: self.instr_arraylength,
            191: self.instr_athrow,
            192: self.instr_checkcast, 193: self.instr_instanceof,
            198: self.instr_ifnull, 199: self.instr_ifnonnull,
            200: self.instr_goto_w,
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

    def instr_ldc(self):
        e = self.constant_pool[self.advance() - 1]
        if e.tag == 8:
            self.stack.append(self.constant_pool[e.value - 1].value)
        elif e.tag in (3, 4):
            self.stack.append(e.value)
        else:
            raise ValueError(f"Unsupported ldc tag: {e.tag}")

    def instr_ldc_w(self):
        e = self.constant_pool[self.advance(2) - 1]
        if e.tag == 8:
            self.stack.append(self.constant_pool[e.value - 1].value)
        elif e.tag in (3, 4):
            self.stack.append(e.value)
        else:
            raise ValueError(f"Unsupported ldc_w tag: {e.tag}")

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
        self.stack.append(arr.get(idx))

    def instr_iaload(self): self._array_load()
    def instr_laload(self): self._array_load()
    def instr_faload(self): self._array_load()
    def instr_daload(self): self._array_load()
    def instr_aaload(self): self._array_load()
    def instr_baload(self): self._array_load()
    def instr_caload(self): self._array_load()
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
        arr.set(idx, val)

    def instr_iastore(self): self._array_store()
    def instr_lastore(self): self._array_store()
    def instr_fastore(self): self._array_store()
    def instr_dastore(self): self._array_store()
    def instr_aastore(self): self._array_store()
    def instr_bastore(self): self._array_store()
    def instr_castore(self): self._array_store()
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

    def instr_idiv(self):
        b=self.stack.pop(); a=self.stack.pop()
        if b == 0: raise _JavaException(None, "java.lang.ArithmeticException")
        self.stack.append(_i32(int(a / b)))

    def instr_ldiv(self):
        b=self.stack.pop(); a=self.stack.pop()
        if b == 0: raise _JavaException(None, "java.lang.ArithmeticException")
        self.stack.append(_i64(int(a / b)))

    def instr_fdiv(self):
        b=self.stack.pop(); a=self.stack.pop()
        self.stack.append(float('nan') if (math.isnan(a) or math.isnan(b)) else
                          (math.copysign(float('inf'), a) if b == 0 else a / b))

    def instr_ddiv(self):
        b=self.stack.pop(); a=self.stack.pop()
        self.stack.append(float('nan') if (math.isnan(a) or math.isnan(b)) else
                          (math.copysign(float('inf'), a) if b == 0 else a / b))

    def instr_irem(self):
        b=self.stack.pop(); a=self.stack.pop()
        if b == 0: raise _JavaException(None, "java.lang.ArithmeticException")
        self.stack.append(_i32(a - int(a / b) * b))

    def instr_lrem(self):
        b=self.stack.pop(); a=self.stack.pop()
        if b == 0: raise _JavaException(None, "java.lang.ArithmeticException")
        self.stack.append(_i64(a - int(a / b) * b))

    def instr_frem(self): b=self.stack.pop(); a=self.stack.pop(); self.stack.append(math.fmod(a, b))
    def instr_drem(self): b=self.stack.pop(); a=self.stack.pop(); self.stack.append(math.fmod(a, b))

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

    def instr_checkcast(self):
        self.advance(2)  # index; no type enforcement in this interpreter

    def instr_instanceof(self):
        index = self.advance(2)
        class_index = self.constant_pool[index - 1].value
        target = self.constant_pool[class_index - 1].value.replace('/', '.')
        obj = self.stack.pop()
        if obj is None:
            self.stack.append(0)
        else:
            actual = obj.class_name if hasattr(obj, 'class_name') else ''
            self.stack.append(1 if actual == target else 0)

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

    def _dispatch(self, class_name: str, method_name: str, descriptor: str,
                  obj: Optional[Any], args: list) -> Any:
        if self.native_registry.has_native_method(class_name, method_name):
            return self.native_registry.invoke_native_method(class_name, method_name, obj, args)
        return self._invoke_bytecode_method(class_name, method_name, descriptor, obj, args)

    def _invoke_bytecode_method(self, class_name: str, method_name: str,
                                descriptor: str, obj: Optional[Any], args: list) -> Any:
        code = self.class_loader.get_method_code(class_name, method_name)
        if not code:
            raise ValueError(f"Method not found: {class_name}.{method_name}{descriptor}")
        class_file = self.class_loader.load_class(class_name)
        exc_table = code[3] if len(code) > 3 else []
        sub = Interpreter(code[2], code[0], code[1],
                          class_file.constant_pool, self.class_loader, exc_table)
        if obj is not None:
            sub.locals[0] = obj
            for i, arg in enumerate(args):
                sub.locals[i + 1] = arg
        else:
            for i, arg in enumerate(args):
                sub.locals[i] = arg
        return sub.run()

    def _find_exception_handler(self, throw_pc: int, exc_class: str) -> Optional[int]:
        """Search exception table for a handler covering throw_pc."""
        for start, end, handler, catch_type_idx in self.exception_table:
            if start <= throw_pc < end:
                if catch_type_idx == 0:
                    return handler
                try:
                    cls_entry = self.constant_pool[catch_type_idx - 1]
                    name_entry = self.constant_pool[cls_entry.value - 1]
                    catch_class = name_entry.value.replace('/', '.')
                    if (catch_class == exc_class or
                            catch_class in ('java.lang.Exception',
                                            'java.lang.RuntimeException',
                                            'java.lang.Throwable')):
                        return handler
                except (IndexError, AttributeError):
                    pass
        return None

    def run(self) -> Optional[Any]:
        """Execute bytecode until a return instruction."""
        while self.pc < len(self.code):
            throw_pc = self.pc
            opcode = self.advance()

            if opcode not in self.instructions:
                raise ValueError(f"Unsupported opcode: {opcode} at pc={self.pc - 1}")

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
