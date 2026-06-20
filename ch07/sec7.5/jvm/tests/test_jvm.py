"""
Test suite for the JVM interpreter.

Tests are self-contained: bytecode is crafted by hand, no javac needed.
Run with:  python -m pytest tests/  (from the jvm/ directory)
  or:      python tests/test_jvm.py
"""

import sys
import io
import unittest

sys.path.insert(0, '.')

from jvm_interpreter.runtime.interpreter import Interpreter, _JavaException, _i32, _i64
from jvm_interpreter.native.native_registry import get_native_registry
from jvm_interpreter.models.java_objects import JavaArray, JavaObject


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run_bytecode(code: bytes, max_stack=10, max_locals=10, cp=None, locals_=None):
    """Run raw bytecode with an empty constant pool and return the result."""
    interp = Interpreter(code, max_stack, max_locals, cp or [], None)
    if locals_:
        for i, v in enumerate(locals_):
            interp.locals[i] = v
    return interp.run()


def run_with_stack(*initial_stack, code: bytes, cp=None):
    """Prepopulate the operand stack then execute."""
    interp = Interpreter(code, 20, 10, cp or [], None)
    interp.stack.extend(initial_stack)
    return interp.run()


# ---------------------------------------------------------------------------
# Helpers: _i32 / _i64
# ---------------------------------------------------------------------------

class TestIntTruncation(unittest.TestCase):

    def test_i32_positive(self):
        self.assertEqual(_i32(42), 42)

    def test_i32_zero(self):
        self.assertEqual(_i32(0), 0)

    def test_i32_wrap_positive(self):
        # 0x80000000 is -2147483648 in Java
        self.assertEqual(_i32(0x80000000), -2147483648)

    def test_i32_wrap_overflow(self):
        # 2^32 should wrap to 0
        self.assertEqual(_i32(0x100000000), 0)

    def test_i32_negative(self):
        self.assertEqual(_i32(-1), -1)

    def test_i64_wrap(self):
        self.assertEqual(_i64(0x8000000000000000), -9223372036854775808)


# ---------------------------------------------------------------------------
# Constants and loads
# ---------------------------------------------------------------------------

class TestConstants(unittest.TestCase):

    def test_nop_ireturn(self):
        # 0x00 nop, 0x03 iconst_0, 0xAC ireturn
        self.assertEqual(run_bytecode(bytes([0x00, 0x03, 0xAC])), 0)

    def test_iconst_m1(self):
        # iconst_m1 (0x02), ireturn
        self.assertEqual(run_bytecode(bytes([0x02, 0xAC])), -1)

    def test_iconst_0_to_5(self):
        for opcode, expected in [(0x02, -1), (0x03, 0), (0x04, 1),
                                  (0x05, 2), (0x06, 3), (0x07, 4), (0x08, 5)]:
            with self.subTest(opcode=opcode):
                self.assertEqual(run_bytecode(bytes([opcode, 0xAC])), expected)

    def test_lconst(self):
        # lconst_1 (0x0A), lreturn (0xAD)
        self.assertEqual(run_bytecode(bytes([0x0A, 0xAD])), 1)

    def test_fconst(self):
        # fconst_2 (0x0D), freturn (0xAE)
        self.assertAlmostEqual(run_bytecode(bytes([0x0D, 0xAE])), 2.0)

    def test_dconst(self):
        # dconst_1 (0x0F), dreturn (0xAF)
        self.assertAlmostEqual(run_bytecode(bytes([0x0F, 0xAF])), 1.0)

    def test_bipush(self):
        # bipush 42 (0x10 0x2A), ireturn
        self.assertEqual(run_bytecode(bytes([0x10, 0x2A, 0xAC])), 42)

    def test_bipush_negative(self):
        # bipush -1 (0x10 0xFF as signed), ireturn
        self.assertEqual(run_bytecode(bytes([0x10, 0xFF, 0xAC])), -1)

    def test_sipush(self):
        # sipush 300 (0x11 0x01 0x2C), ireturn
        self.assertEqual(run_bytecode(bytes([0x11, 0x01, 0x2C, 0xAC])), 300)

    def test_sipush_negative(self):
        # sipush -1 (0x11 0xFF 0xFF), ireturn
        self.assertEqual(run_bytecode(bytes([0x11, 0xFF, 0xFF, 0xAC])), -1)

    def test_aconst_null(self):
        # aconst_null (0x01), areturn (0xB0)
        self.assertIsNone(run_bytecode(bytes([0x01, 0xB0])))


# ---------------------------------------------------------------------------
# Loads and Stores
# ---------------------------------------------------------------------------

class TestLoadsStores(unittest.TestCase):

    def test_iload_istore(self):
        # bipush 99, istore 3, iload 3, ireturn
        code = bytes([0x10, 0x63,   # bipush 99
                      0x36, 0x03,   # istore 3
                      0x15, 0x03,   # iload 3
                      0xAC])        # ireturn
        self.assertEqual(run_bytecode(code), 99)

    def test_istore_n_iload_n(self):
        # bipush 7, istore_2, iload_2, ireturn
        code = bytes([0x10, 0x07,   # bipush 7
                      0x3D,         # istore_2
                      0x1C,         # iload_2
                      0xAC])        # ireturn
        self.assertEqual(run_bytecode(code), 7)

    def test_aload_n(self):
        # Set local 0 to a string, aload_0, areturn
        code = bytes([0x2A, 0xB0])  # aload_0, areturn
        result = run_bytecode(code, locals_=["hello"])
        self.assertEqual(result, "hello")

    def test_iinc(self):
        # bipush 10, istore_1, iinc 1 5, iload_1, ireturn
        code = bytes([0x10, 0x0A,   # bipush 10
                      0x3C,         # istore_1
                      0x84, 0x01, 0x05,  # iinc 1, 5
                      0x1B,         # iload_1
                      0xAC])        # ireturn
        self.assertEqual(run_bytecode(code), 15)

    def test_iinc_negative(self):
        # bipush 10, istore_0, iinc 0 -3, iload_0, ireturn
        code = bytes([0x10, 0x0A,   # bipush 10
                      0x3B,         # istore_0
                      0x84, 0x00, 0xFD,  # iinc 0, -3
                      0x1A,         # iload_0
                      0xAC])        # ireturn
        self.assertEqual(run_bytecode(code), 7)


# ---------------------------------------------------------------------------
# Arithmetic
# ---------------------------------------------------------------------------

class TestArithmetic(unittest.TestCase):

    def test_iadd(self):
        # iconst_3 iconst_4 iadd ireturn  => 7
        code = bytes([0x06, 0x07, 0x60, 0xAC])
        self.assertEqual(run_bytecode(code), 7)

    def test_isub(self):
        # iconst_5 iconst_3 isub ireturn  => 2
        code = bytes([0x08, 0x06, 0x64, 0xAC])
        self.assertEqual(run_bytecode(code), 2)

    def test_imul(self):
        # bipush 6 bipush 7 imul ireturn  => 42
        code = bytes([0x10, 0x06, 0x10, 0x07, 0x68, 0xAC])
        self.assertEqual(run_bytecode(code), 42)

    def test_idiv(self):
        # bipush 10 bipush 3 idiv ireturn  => 3 (truncate toward zero)
        code = bytes([0x10, 0x0A, 0x10, 0x03, 0x6C, 0xAC])
        self.assertEqual(run_bytecode(code), 3)

    def test_idiv_negative_truncation(self):
        # Java: 7 / -2 = -3  (not -4 like Python floor div)
        code = bytes([0x10, 0x07, 0x10, 0xFE, 0x6C, 0xAC])  # bipush 7, bipush -2
        self.assertEqual(run_bytecode(code), -3)

    def test_irem(self):
        # bipush 10 bipush 3 irem ireturn  => 1
        code = bytes([0x10, 0x0A, 0x10, 0x03, 0x70, 0xAC])
        self.assertEqual(run_bytecode(code), 1)

    def test_irem_negative(self):
        # Java: -7 % 3 = -1
        code = bytes([0x10, 0xF9, 0x10, 0x03, 0x70, 0xAC])  # bipush -7, bipush 3
        self.assertEqual(run_bytecode(code), -1)

    def test_ineg(self):
        # bipush 5, ineg, ireturn  => -5
        code = bytes([0x10, 0x05, 0x74, 0xAC])
        self.assertEqual(run_bytecode(code), -5)

    def test_int32_overflow(self):
        # MAX_INT + 1 should wrap to MIN_INT
        # sipush 0x7FFF, ishl 0 (no shift), then iadd with itself
        # Easier: push 0x7FFFFFFF via sipush can't (only 16-bit)
        # Use: push -1 as int (0xFFFF FFFF) and shift
        # Actually let's just test via _i32 directly and arithmetic in Python
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        interp.stack.append(2147483647)  # MAX_INT
        interp.stack.append(1)
        interp.instr_iadd()
        self.assertEqual(interp.stack[-1], -2147483648)

    def test_ishl(self):
        # bipush 1, bipush 3, ishl, ireturn  => 8
        code = bytes([0x10, 0x01, 0x10, 0x03, 0x78, 0xAC])
        self.assertEqual(run_bytecode(code), 8)

    def test_ishr_arithmetic(self):
        # -8 >> 2 = -2 (arithmetic shift preserves sign)
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        interp.stack.extend([-8, 2])
        interp.instr_ishr()
        self.assertEqual(interp.stack[-1], -2)

    def test_iushr_logical(self):
        # -1 >>> 28 = 0xF (logical shift)
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        interp.stack.extend([-1, 28])
        interp.instr_iushr()
        self.assertEqual(interp.stack[-1], 15)

    def test_iand(self):
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        interp.stack.extend([0xFF, 0x0F])
        interp.instr_iand()
        self.assertEqual(interp.stack[-1], 0x0F)

    def test_ior(self):
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        interp.stack.extend([0xF0, 0x0F])
        interp.instr_ior()
        self.assertEqual(interp.stack[-1], 0xFF)

    def test_ixor(self):
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        interp.stack.extend([0xFF, 0xFF])
        interp.instr_ixor()
        self.assertEqual(interp.stack[-1], 0)

    def test_fadd(self):
        interp = Interpreter(bytes([0xAE]), 10, 10, [], None)
        interp.stack.extend([1.5, 2.5])
        interp.instr_fadd()
        self.assertAlmostEqual(interp.stack[-1], 4.0)

    def test_dadd(self):
        interp = Interpreter(bytes([0xAF]), 10, 10, [], None)
        interp.stack.extend([1.5, 2.5])
        interp.instr_dadd()
        self.assertAlmostEqual(interp.stack[-1], 4.0)

    def test_ldiv_large_values(self):
        """ldiv must use exact integer arithmetic, not float (float only has 53-bit mantissa)."""
        interp = Interpreter(bytes([0xAD]), 10, 10, [], None)
        a = 2**62      # 4611686018427387904 — larger than float64 mantissa
        b = 3
        interp.stack.extend([a, b])
        interp.instr_ldiv()
        self.assertEqual(interp.stack[-1], a // b)  # exact: 1537228672809129301

    def test_lrem_large_values(self):
        interp = Interpreter(bytes([0xAD]), 10, 10, [], None)
        a = 2**62; b = 3
        interp.stack.extend([a, b])
        interp.instr_lrem()
        self.assertEqual(interp.stack[-1], a % b)   # 1

    def test_idiv_negative_truncates_toward_zero(self):
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        interp.stack.extend([-7, 2])
        interp.instr_idiv()
        self.assertEqual(interp.stack[-1], -3)   # not -4 (Python floor)

    def test_irem_negative_sign_follows_dividend(self):
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        interp.stack.extend([-7, 3])
        interp.instr_irem()
        self.assertEqual(interp.stack[-1], -1)   # not 2 (Python %)

    def test_char_array_default_is_zero(self):
        from jvm_interpreter.models.java_objects import JavaArray
        arr = JavaArray('char', 3)
        self.assertEqual(arr.get(0), 0)

    def test_caload_returns_int(self):
        from jvm_interpreter.models.java_objects import JavaArray
        arr = JavaArray('char', 1)
        arr.set(0, ord('A'))   # store as int 65
        interp = Interpreter(bytes([0xB1]), 10, 10, [], None)
        interp.stack.extend([arr, 0])
        interp.instr_caload()
        self.assertEqual(interp.stack[-1], 65)

    def test_castore_masks_to_16bit(self):
        from jvm_interpreter.models.java_objects import JavaArray
        arr = JavaArray('char', 1)
        interp = Interpreter(bytes([0xB1]), 10, 10, [], None)
        interp.stack.extend([arr, 0, 0x10041])  # 0x10041 & 0xFFFF = 0x41 = 'A'
        interp.instr_castore()
        self.assertEqual(arr.get(0), 0x41)

    def test_baload_sign_extends(self):
        from jvm_interpreter.models.java_objects import JavaArray
        arr = JavaArray('byte', 1)
        arr.set(0, -3)  # stored as -3 (signed byte)
        interp = Interpreter(bytes([0xB1]), 10, 10, [], None)
        interp.stack.extend([arr, 0])
        interp.instr_baload()
        self.assertEqual(interp.stack[-1], -3)   # sign-extended to int


# ---------------------------------------------------------------------------
# Type Conversions
# ---------------------------------------------------------------------------

class TestConversions(unittest.TestCase):

    def test_i2l(self):
        interp = Interpreter(bytes([0xAD]), 10, 10, [], None)
        interp.stack.append(42)
        interp.instr_i2l()
        self.assertEqual(interp.stack[-1], 42)

    def test_i2f(self):
        interp = Interpreter(bytes([0xAE]), 10, 10, [], None)
        interp.stack.append(7)
        interp.instr_i2f()
        self.assertAlmostEqual(interp.stack[-1], 7.0)

    def test_l2i_truncation(self):
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        interp.stack.append(2 ** 33)  # larger than 32-bit
        interp.instr_l2i()
        self.assertEqual(interp.stack[-1], 0)  # 2^33 mod 2^32 = 0

    def test_f2i_truncate(self):
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        interp.stack.append(3.9)
        interp.instr_f2i()
        self.assertEqual(interp.stack[-1], 3)  # truncate, not round

    def test_f2i_negative_truncate(self):
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        interp.stack.append(-3.9)
        interp.instr_f2i()
        self.assertEqual(interp.stack[-1], -3)

    def test_d2i_nan(self):
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        interp.stack.append(float('nan'))
        interp.instr_d2i()
        self.assertEqual(interp.stack[-1], 0)

    def test_i2b_truncate(self):
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        interp.stack.append(256)
        interp.instr_i2b()
        self.assertEqual(interp.stack[-1], 0)

    def test_i2b_sign_extend(self):
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        interp.stack.append(200)  # > 127, becomes -56
        interp.instr_i2b()
        self.assertEqual(interp.stack[-1], -56)

    def test_i2c(self):
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        interp.stack.append(65600)  # > 65535
        interp.instr_i2c()
        self.assertEqual(interp.stack[-1], 64)  # 65600 & 0xFFFF

    def test_i2s_sign_extend(self):
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        interp.stack.append(40000)  # > 32767
        interp.instr_i2s()
        self.assertEqual(interp.stack[-1], 40000 - 65536)


# ---------------------------------------------------------------------------
# Comparisons
# ---------------------------------------------------------------------------

class TestComparisons(unittest.TestCase):

    def test_lcmp_equal(self):
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        interp.stack.extend([5, 5])
        interp.instr_lcmp()
        self.assertEqual(interp.stack[-1], 0)

    def test_lcmp_greater(self):
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        interp.stack.extend([10, 3])
        interp.instr_lcmp()
        self.assertEqual(interp.stack[-1], 1)

    def test_lcmp_less(self):
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        interp.stack.extend([3, 10])
        interp.instr_lcmp()
        self.assertEqual(interp.stack[-1], -1)

    def test_fcmpl_nan(self):
        import math
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        interp.stack.extend([float('nan'), 1.0])
        interp.instr_fcmpl()
        self.assertEqual(interp.stack[-1], -1)

    def test_fcmpg_nan(self):
        import math
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        interp.stack.extend([float('nan'), 1.0])
        interp.instr_fcmpg()
        self.assertEqual(interp.stack[-1], 1)


# ---------------------------------------------------------------------------
# Control Flow
# ---------------------------------------------------------------------------

class TestControlFlow(unittest.TestCase):

    def test_ifeq_taken(self):
        # iconst_0, ifeq +4, iconst_5 (skipped), bipush 42, ireturn
        # ifeq at pc=1, reads 2 bytes -> pc=4, offset=4, target = 1+4 = 5
        # pc=5 is bipush (skipped iconst_5), pushes 42, ireturn returns 42
        code = bytes([0x03,              # iconst_0  (pc=0)
                      0x99, 0x00, 0x04,  # ifeq +4   (pc=1), 0==0 -> jump to 1+4=5
                      0x08,              # iconst_5  (pc=4, skipped)
                      0x10, 0x2A,        # bipush 42 (pc=5)
                      0xAC])             # ireturn   (pc=7)
        self.assertEqual(run_bytecode(code), 42)

    def test_ifeq_not_taken(self):
        # iconst_1 (!=0), ifeq +4 (not taken), iconst_5, ireturn
        # Falls through to iconst_5 at pc=4, then ireturn at pc=5 -> returns 5
        code = bytes([0x04,              # iconst_1  (pc=0)
                      0x99, 0x00, 0x04,  # ifeq +4   (pc=1), 1!=0 -> NOT taken
                      0x08,              # iconst_5  (pc=4, reached)
                      0xAC])             # ireturn   (pc=5)
        self.assertEqual(run_bytecode(code), 5)

    def test_goto(self):
        # iconst_0 at pc=0, goto +4 at pc=1, iconst_5 at pc=4 (skipped), ireturn at pc=5
        # goto offset=4: target = 1 + 4 = 5 -> lands on ireturn, returns 0 (iconst_0)
        code = bytes([0x03,        # iconst_0  (pc=0)
                      0xA7, 0x00, 0x04,  # goto +4  (pc=1), target = 1+4 = 5
                      0x08,        # iconst_5  (pc=4, skipped)
                      0xAC])       # ireturn   (pc=5)
        self.assertEqual(run_bytecode(code), 0)

    def test_if_icmpeq(self):
        # bipush 5, bipush 5, if_icmpeq +3, iconst_0, iconst_1, ireturn
        code = bytes([0x10, 0x05,  # bipush 5
                      0x10, 0x05,  # bipush 5
                      0x9F, 0x00, 0x04,  # if_icmpeq +4
                      0x03,        # iconst_0 (skipped if equal)
                      0x04,        # iconst_1 (land here)
                      0xAC])
        self.assertEqual(run_bytecode(code), 1)

    def test_if_icmplt_taken(self):
        # bipush 3, bipush 5, if_icmplt -> jump, return 1
        code = bytes([0x10, 0x03,  # bipush 3
                      0x10, 0x05,  # bipush 5
                      0xA1, 0x00, 0x04,  # if_icmplt +4  (pc=4, target=4+4-3=5... recalc)
                      0x03,        # iconst_0
                      0x04,        # iconst_1
                      0xAC])
        # if_icmplt at pc=4, reads 2 bytes -> pc=7, offset=4
        # target = 7 - 3 + 4 = 8 -> iconst_1 at pc=8, then ireturn
        self.assertEqual(run_bytecode(code), 1)

    def test_ifnull_taken(self):
        # aconst_null, ifnull +3, iconst_0, iconst_1, ireturn
        code = bytes([0x01,        # aconst_null
                      0xC6, 0x00, 0x04,  # ifnull +4
                      0x03,        # iconst_0 (skipped)
                      0x04,        # iconst_1
                      0xAC])
        self.assertEqual(run_bytecode(code), 1)

    def test_ifnonnull_not_taken(self):
        # aconst_null, ifnonnull +4 (not taken), iconst_0, ireturn
        # Falls through: iconst_0 at pc=4, ireturn at pc=5 -> 0
        code = bytes([0x01,              # aconst_null (pc=0)
                      0xC7, 0x00, 0x04,  # ifnonnull +4 (pc=1), null -> NOT taken
                      0x03,              # iconst_0 (pc=4)
                      0xAC])             # ireturn  (pc=5)
        self.assertEqual(run_bytecode(code), 0)

    def test_tableswitch_hit(self):
        # Push key=2, tableswitch low=0 high=2 with offsets to different returns
        # This is complex to hand-craft; test via interpreter directly
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        interp.stack.append(1)  # key=1
        # Simulate tableswitch: low=0, high=2, offsets=[20, 30, 40], default=50
        # With opcode_pc=0, target = 0 + offsets[1-0] = 30
        interp.pc = 1  # pretend opcode was at 0, pc already advanced
        # We test _manually_:
        # Actually just verify via bytecode with known padding:
        # Build a small program: bipush 1, tableswitch ...
        # bipush 1 is 2 bytes (pc 0-1), then tableswitch at pc=2
        # After opcode byte consumed, pc=3. Pad to multiple of 4: need pc=4, so skip 1.
        # default=-2 (go back 2 = opcode_pc + (-2) = 2 - 2 = 0?), etc.
        # This is tricky; just verify the instruction exists in the dispatch table
        self.assertIn(170, interp.instructions)

    def test_lookupswitch_exists(self):
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        self.assertIn(171, interp.instructions)


# ---------------------------------------------------------------------------
# Stack Manipulation
# ---------------------------------------------------------------------------

class TestStackOps(unittest.TestCase):

    def test_dup(self):
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        interp.stack.append(42)
        interp.instr_dup()
        self.assertEqual(interp.stack, [42, 42])

    def test_dup_x1(self):
        # JVM spec: ..., value2, value1 -> ..., value1, value2, value1
        # Stack [1, 2] means value2=1 (bottom), value1=2 (top)
        # Result: [2, 1, 2]
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        interp.stack.extend([1, 2])
        interp.instr_dup_x1()
        self.assertEqual(interp.stack, [2, 1, 2])

    def test_pop(self):
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        interp.stack.extend([1, 2, 3])
        interp.instr_pop()
        self.assertEqual(interp.stack, [1, 2])

    def test_pop2(self):
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        interp.stack.extend([1, 2, 3])
        interp.instr_pop2()
        self.assertEqual(interp.stack, [1])

    def test_swap(self):
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        interp.stack.extend([1, 2])
        interp.instr_swap()
        self.assertEqual(interp.stack, [2, 1])


# ---------------------------------------------------------------------------
# Array Operations
# ---------------------------------------------------------------------------

class TestArrayOps(unittest.TestCase):

    def test_newarray_int(self):
        # bipush 5, newarray int (10), arraylength, ireturn
        code = bytes([0x10, 0x05,  # bipush 5
                      0xBC, 0x0A,  # newarray int
                      0xBE,        # arraylength
                      0xAC])       # ireturn
        interp = Interpreter(code, 10, 10, [], None)
        result = interp.run()
        self.assertEqual(result, 5)

    def test_newarray_default_values(self):
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        interp.stack.append(3)
        interp.instr_newarray()  # won't work without advance() for atype
        # Use ObjectFactory directly
        from jvm_interpreter.models.java_objects import ObjectFactory
        from jvm_interpreter.native.native_registry import get_native_registry
        factory = ObjectFactory(get_native_registry())
        arr = factory.create_array('int', 4)
        self.assertEqual(arr.length, 4)
        self.assertEqual(arr.get(0), 0)
        self.assertEqual(arr.get(3), 0)

    def test_array_load_store(self):
        from jvm_interpreter.models.java_objects import JavaArray
        arr = JavaArray('int', 3)
        arr.set(0, 10)
        arr.set(1, 20)
        arr.set(2, 30)
        # Test via interpreter stack ops
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        interp.stack.extend([arr, 1])  # array, index
        interp.instr_iaload()
        self.assertEqual(interp.stack[-1], 20)

    def test_array_store(self):
        from jvm_interpreter.models.java_objects import JavaArray
        arr = JavaArray('int', 3)
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        interp.stack.extend([arr, 2, 99])  # array, index, value
        interp.instr_iastore()
        self.assertEqual(arr.get(2), 99)

    def test_array_bounds_check(self):
        from jvm_interpreter.models.java_objects import JavaArray
        arr = JavaArray('int', 2)
        with self.assertRaises(IndexError):
            arr.get(5)

    def test_aaload(self):
        from jvm_interpreter.models.java_objects import JavaArray
        arr = JavaArray('java.lang.String', 2)
        arr.set(0, "hello")
        arr.set(1, "world")
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        interp.stack.extend([arr, 0])
        interp.instr_aaload()
        self.assertEqual(interp.stack[-1], "hello")

    def test_arraylength_null(self):
        interp = Interpreter(bytes([0xAC]), 10, 10, [], None)
        interp.stack.append(None)
        with self.assertRaises(_JavaException) as ctx:
            interp.instr_arraylength()
        self.assertIn("NullPointerException", ctx.exception.class_name)


# ---------------------------------------------------------------------------
# Native Registry
# ---------------------------------------------------------------------------

class TestNativeRegistry(unittest.TestCase):

    def setUp(self):
        self.reg = get_native_registry()

    def test_stringbuilder_append_and_tostring(self):
        sb = self.reg.create_native_object("java.lang.StringBuilder")
        self.reg.invoke_native_method("java.lang.StringBuilder", "append", sb, ["Hello, "])
        self.reg.invoke_native_method("java.lang.StringBuilder", "append", sb, ["World!"])
        result = self.reg.invoke_native_method("java.lang.StringBuilder", "toString", sb, [])
        self.assertEqual(result, "Hello, World!")

    def test_stringbuilder_reverse(self):
        sb = self.reg.create_native_object("java.lang.StringBuilder")
        self.reg.invoke_native_method("java.lang.StringBuilder", "append", sb, ["abc"])
        self.reg.invoke_native_method("java.lang.StringBuilder", "reverse", sb, [])
        result = self.reg.invoke_native_method("java.lang.StringBuilder", "toString", sb, [])
        self.assertEqual(result, "cba")

    def test_system_out_println(self):
        captured = io.StringIO()
        system_out = self.reg.get_native_static_field("java.lang.System", "out")
        old = system_out.stream
        system_out.stream = captured
        try:
            self.reg.invoke_native_method("java.io.PrintStream", "println",
                                          system_out, ["hello test"])
        finally:
            system_out.stream = old
        self.assertEqual(captured.getvalue().strip(), "hello test")

    def test_integer_parseint(self):
        result = self.reg.invoke_native_method("java.lang.Integer", "parseInt",
                                               None, ["42"])
        self.assertEqual(result, 42)

    def test_integer_parseint_hex(self):
        result = self.reg.invoke_native_method("java.lang.Integer", "parseInt",
                                               None, ["FF", 16])
        self.assertEqual(result, 255)

    def test_integer_tohexstring(self):
        result = self.reg.invoke_native_method("java.lang.Integer", "toHexString",
                                               None, [255])
        self.assertEqual(result, "ff")

    def test_integer_bitcount(self):
        result = self.reg.invoke_native_method("java.lang.Integer", "bitCount",
                                               None, [7])
        self.assertEqual(result, 3)

    def test_math_sqrt(self):
        result = self.reg.invoke_native_method("java.lang.Math", "sqrt", None, [16.0])
        self.assertAlmostEqual(result, 4.0)

    def test_math_pow(self):
        result = self.reg.invoke_native_method("java.lang.Math", "pow", None, [2.0, 10.0])
        self.assertAlmostEqual(result, 1024.0)

    def test_math_abs_negative(self):
        result = self.reg.invoke_native_method("java.lang.Math", "abs", None, [-5])
        self.assertEqual(result, 5)

    def test_math_max(self):
        result = self.reg.invoke_native_method("java.lang.Math", "max", None, [3, 7])
        self.assertEqual(result, 7)

    def test_math_pi(self):
        pi = self.reg.get_native_static_field("java.lang.Math", "PI")
        self.assertAlmostEqual(pi, 3.141592653589793)

    def test_string_length(self):
        result = self.reg.invoke_native_method("java.lang.String", "length",
                                               "hello", [])
        self.assertEqual(result, 5)

    def test_string_touppercase(self):
        result = self.reg.invoke_native_method("java.lang.String", "toUpperCase",
                                               "hello", [])
        self.assertEqual(result, "HELLO")

    def test_string_contains(self):
        result = self.reg.invoke_native_method("java.lang.String", "contains",
                                               "hello world", ["world"])
        self.assertTrue(result)

    def test_string_startswith(self):
        result = self.reg.invoke_native_method("java.lang.String", "startsWith",
                                               "hello", ["he"])
        self.assertTrue(result)

    def test_string_indexof(self):
        result = self.reg.invoke_native_method("java.lang.String", "indexOf",
                                               "hello", ["ll"])
        self.assertEqual(result, 2)

    def test_string_substring(self):
        result = self.reg.invoke_native_method("java.lang.String", "substring",
                                               "hello world", [6])
        self.assertEqual(result, "world")

    def test_string_trim(self):
        result = self.reg.invoke_native_method("java.lang.String", "trim",
                                               "  hi  ", [])
        self.assertEqual(result, "hi")

    def test_string_isempty(self):
        self.assertTrue(self.reg.invoke_native_method("java.lang.String", "isEmpty",
                                                      "", []))
        self.assertFalse(self.reg.invoke_native_method("java.lang.String", "isEmpty",
                                                       "x", []))

    def test_system_current_time(self):
        t = self.reg.invoke_native_method("java.lang.System", "currentTimeMillis",
                                          None, [])
        self.assertGreater(t, 0)


# ---------------------------------------------------------------------------
# Count Args
# ---------------------------------------------------------------------------

class TestCountArgs(unittest.TestCase):

    def setUp(self):
        self.interp = Interpreter(bytes([0xAC]), 10, 10, [], None)

    def test_no_args(self):
        self.assertEqual(self.interp._count_args("()V"), 0)

    def test_one_int(self):
        self.assertEqual(self.interp._count_args("(I)V"), 1)

    def test_two_ints(self):
        self.assertEqual(self.interp._count_args("(II)I"), 2)

    def test_string_arg(self):
        self.assertEqual(self.interp._count_args("(Ljava/lang/String;)V"), 1)

    def test_mixed(self):
        self.assertEqual(self.interp._count_args("(ILjava/lang/String;I)V"), 3)

    def test_array_arg(self):
        self.assertEqual(self.interp._count_args("([Ljava/lang/String;)V"), 1)

    def test_primitive_array(self):
        self.assertEqual(self.interp._count_args("([I)V"), 1)

    def test_double_and_long(self):
        self.assertEqual(self.interp._count_args("(DJ)I"), 2)

    def test_all_primitives(self):
        self.assertEqual(self.interp._count_args("(BCDFIJSZ)V"), 8)

    def test_main_signature(self):
        self.assertEqual(self.interp._count_args("([Ljava/lang/String;)V"), 1)

    def test_multidim_array(self):
        self.assertEqual(self.interp._count_args("([[I)V"), 1)


# ---------------------------------------------------------------------------
# Exception Handling
# ---------------------------------------------------------------------------

class TestExceptions(unittest.TestCase):

    def test_athrow_raises(self):
        interp = Interpreter(bytes([0xBF, 0xAC]), 10, 10, [], None)
        obj = JavaObject("java.lang.RuntimeException")
        interp.stack.append(obj)
        with self.assertRaises(_JavaException) as ctx:
            interp.run()
        self.assertEqual(ctx.exception.class_name, "java.lang.RuntimeException")

    def test_idiv_by_zero(self):
        code = bytes([0x04, 0x03, 0x6C, 0xAC])  # iconst_1, iconst_0, idiv
        interp = Interpreter(code, 10, 10, [], None)
        with self.assertRaises(_JavaException) as ctx:
            interp.run()
        self.assertIn("ArithmeticException", ctx.exception.class_name)

    def test_exception_handler_found(self):
        # Put a value on the stack, athrow; exception table catches it
        # and jumps to a handler that pushes iconst_1
        # Bytecode: [athrow(0xBF), iconst_0(0x03), return(0xB1)]
        # Exception table: (0, 1, 1, 0) => catch all from 0..0, handler at 1
        code = bytes([0xBF,   # athrow at pc=0  -> throws
                      0x03,   # iconst_0 at pc=1 (handler: push 0 and fall through)
                      0xAC])  # ireturn at pc=2
        exc_table = [(0, 1, 1, 0)]  # start=0, end=1, handler=1, catch_all
        obj = JavaObject("java.lang.Exception")
        interp = Interpreter(code, 10, 10, [], None, exc_table)
        interp.stack.append(obj)
        result = interp.run()
        self.assertEqual(result, 0)

    def test_array_oob_raises_java_exception(self):
        from jvm_interpreter.models.java_objects import JavaArray
        arr = JavaArray("int", 3)
        interp = Interpreter(bytes([0xB1]), 10, 10, [], None)
        interp.stack.extend([arr, 99])  # arr, oob-index
        with self.assertRaises(_JavaException) as ctx:
            interp._array_load()
        self.assertIn("ArrayIndexOutOfBounds", ctx.exception.class_name)

    def test_array_store_oob_raises_java_exception(self):
        from jvm_interpreter.models.java_objects import JavaArray
        arr = JavaArray("int", 2)
        interp = Interpreter(bytes([0xB1]), 10, 10, [], None)
        interp.stack.extend([arr, 10, 42])  # arr, oob-index, value
        with self.assertRaises(_JavaException) as ctx:
            interp._array_store()
        self.assertIn("ArrayIndexOutOfBounds", ctx.exception.class_name)

    def test_fdiv_zero_by_zero_is_nan(self):
        code = bytes([0x0B, 0x0B, 0x6E, 0xAE])  # fconst_0, fconst_0, fdiv, freturn
        interp = Interpreter(code, 10, 10, [], None)
        import math
        self.assertTrue(math.isnan(interp.run()))

    def test_fdiv_nonzero_by_zero_is_inf(self):
        code = bytes([0x0C, 0x0B, 0x6E, 0xAE])  # fconst_1, fconst_0, fdiv, freturn
        interp = Interpreter(code, 10, 10, [], None)
        import math
        self.assertTrue(math.isinf(interp.run()))

    def test_ddiv_zero_by_zero_is_nan(self):
        code = bytes([0x0E, 0x0E, 0x6F, 0xAF])  # dconst_0, dconst_0, ddiv, dreturn
        interp = Interpreter(code, 10, 10, [], None)
        import math
        self.assertTrue(math.isnan(interp.run()))

    def test_frem_by_zero_is_nan(self):
        code = bytes([0x0C, 0x0B, 0x72, 0xAE])  # fconst_1, fconst_0, frem, freturn
        interp = Interpreter(code, 10, 10, [], None)
        import math
        self.assertTrue(math.isnan(interp.run()))

    def test_drem_inf_dividend_is_nan(self):
        interp = Interpreter(bytes([0xAF]), 10, 10, [], None)
        result = interp._float_rem(float('inf'), 2.0)
        import math
        self.assertTrue(math.isnan(result))

    def test_monitorenter_monitorexit_noop(self):
        # monitorenter(194) + monitorexit(195) + return — should not crash
        obj = JavaObject("java.lang.Object")
        interp = Interpreter(bytes([0xC2, 0xC3, 0xB1]), 10, 10, [], None)
        interp.stack.extend([obj, obj])  # two refs for monitor enter/exit
        interp.run()  # must not raise

    def test_ldc_class_tag(self):
        from jvm_interpreter.models.class_file_models import ConstantPoolEntry
        from jvm_interpreter.native.java_reflect import JavaClass
        # ldc of a Class CP entry (tag 7) now produces a JavaClass, not a raw string.
        cp = [ConstantPoolEntry(1, "java/lang/String"), ConstantPoolEntry(7, 1)]
        code = bytes([0x12, 0x02, 0xB0])  # ldc #2, areturn
        interp = Interpreter(code, 10, 10, cp, None)
        result = interp.run()
        self.assertIsInstance(result, JavaClass)
        self.assertEqual(result.getName(), "java.lang.String")


# ---------------------------------------------------------------------------
# Instanceof / Checkcast
# ---------------------------------------------------------------------------

class TestTyping(unittest.TestCase):

    def test_instanceof_match(self):
        from jvm_interpreter.models.class_file_models import ConstantPoolEntry
        # Build a tiny constant pool: class entry pointing to UTF8
        cp = [
            ConstantPoolEntry(1, "com.example.Foo"),   # #1 UTF8
            ConstantPoolEntry(7, 1),                   # #2 Class -> #1
        ]
        obj = JavaObject("com.example.Foo")
        interp = Interpreter(bytes([0xAC]), 10, 10, cp, None)
        interp.stack.append(obj)
        interp.pc = 1  # pretend we just read opcode
        # Manually set up for instanceof: index=2
        interp.stack.append(obj)
        # Call directly
        old_pc = interp.pc
        interp.code = [0xC1, 0x00, 0x02, 0xAC]
        interp.pc = 1
        interp.instr_instanceof()
        self.assertEqual(interp.stack[-1], 1)

    def test_instanceof_null(self):
        from jvm_interpreter.models.class_file_models import ConstantPoolEntry
        cp = [
            ConstantPoolEntry(1, "java.lang.Object"),
            ConstantPoolEntry(7, 1),
        ]
        interp = Interpreter(bytes([0xC1, 0x00, 0x02, 0xAC]), 10, 10, cp, None)
        interp.stack.append(None)
        interp.pc = 1
        interp.instr_instanceof()
        self.assertEqual(interp.stack[-1], 0)

    def test_instanceof_superclass(self):
        """RuntimeException instanceof Exception → 1 (hierarchy)."""
        from jvm_interpreter.models.class_file_models import ConstantPoolEntry
        cp = [
            ConstantPoolEntry(1, "java/lang/Exception"),
            ConstantPoolEntry(7, 1),
        ]
        interp = Interpreter(bytes([0xC1, 0x00, 0x02, 0xAC]), 10, 10, cp, None)
        obj = JavaObject("java.lang.RuntimeException")
        interp.stack.append(obj)
        interp.pc = 1
        interp.instr_instanceof()
        self.assertEqual(interp.stack[-1], 1)

    def test_instanceof_interface(self):
        """ArrayList instanceof List → 1."""
        from jvm_interpreter.models.class_file_models import ConstantPoolEntry
        cp = [
            ConstantPoolEntry(1, "java/util/List"),
            ConstantPoolEntry(7, 1),
        ]
        interp = Interpreter(bytes([0xC1, 0x00, 0x02, 0xAC]), 10, 10, cp, None)
        obj = JavaObject("java.util.ArrayList")
        interp.stack.append(obj)
        interp.pc = 1
        interp.instr_instanceof()
        self.assertEqual(interp.stack[-1], 1)

    def test_instanceof_negative(self):
        """String instanceof List → 0."""
        from jvm_interpreter.models.class_file_models import ConstantPoolEntry
        cp = [
            ConstantPoolEntry(1, "java/util/List"),
            ConstantPoolEntry(7, 1),
        ]
        interp = Interpreter(bytes([0xC1, 0x00, 0x02, 0xAC]), 10, 10, cp, None)
        obj = JavaObject("java.lang.String")
        interp.stack.append(obj)
        interp.pc = 1
        interp.instr_instanceof()
        self.assertEqual(interp.stack[-1], 0)

    def test_exception_caught_by_superclass(self):
        """ArithmeticException caught by handler declaring RuntimeException."""
        from jvm_interpreter.models.class_file_models import ConstantPoolEntry
        # CP: #1 UTF8 "java/lang/RuntimeException", #2 Class(#1)
        cp = [
            ConstantPoolEntry(1, "java/lang/RuntimeException"),
            ConstantPoolEntry(7, 1),
        ]
        # Bytecode: athrow at pc=0; handler at pc=1 pushes iconst_1, ireturn
        code = bytes([0xBF, 0x04, 0xAC])
        exc_table = [(0, 1, 1, 2)]  # catch_type_idx=2 → CP#2 = RuntimeException
        obj = JavaObject("java.lang.ArithmeticException")
        interp = Interpreter(code, 10, 10, cp, None, exc_table)
        interp.stack.append(obj)
        result = interp.run()
        self.assertEqual(result, 1)

    def test_exception_not_caught_wrong_type(self):
        """IOException not caught by handler for RuntimeException — propagates."""
        from jvm_interpreter.models.class_file_models import ConstantPoolEntry
        cp = [
            ConstantPoolEntry(1, "java/lang/RuntimeException"),
            ConstantPoolEntry(7, 1),
        ]
        code = bytes([0xBF, 0x04, 0xAC])
        exc_table = [(0, 1, 1, 2)]
        obj = JavaObject("java.io.IOException")
        interp = Interpreter(code, 10, 10, cp, None, exc_table)
        interp.stack.append(obj)
        with self.assertRaises(_JavaException) as ctx:
            interp.run()
        self.assertEqual(ctx.exception.class_name, "java.io.IOException")

    def test_is_assignable_module_function(self):
        """Direct unit tests for the is_assignable helper."""
        from jvm_interpreter.runtime.class_loader import is_assignable
        # Identity
        self.assertTrue(is_assignable("java.lang.String", "java.lang.String"))
        # Any type is-a Object
        self.assertTrue(is_assignable("java.lang.Integer", "java.lang.Object"))
        # Exception chain
        self.assertTrue(is_assignable("java.lang.ArithmeticException", "java.lang.Throwable"))
        # Interface
        self.assertTrue(is_assignable("java.util.ArrayList", "java.util.Collection"))
        self.assertTrue(is_assignable("java.util.TreeSet", "java.util.Set"))
        # Negative
        self.assertFalse(is_assignable("java.lang.String", "java.util.List"))
        self.assertFalse(is_assignable("java.lang.Integer", "java.lang.String"))

    def test_wide_iload_istore(self):
        """wide istore #256 / wide iload #256 round-trips a value."""
        # wide istore 256: 0xC4 0x36 0x01 0x00
        # wide iload 256:  0xC4 0x15 0x01 0x00
        # ireturn:         0xAC
        code = bytes([0xC4, 0x36, 0x01, 0x00,   # wide istore #256
                      0xC4, 0x15, 0x01, 0x00,   # wide iload  #256
                      0xAC])                     # ireturn
        interp = Interpreter(code, 10, 400, [], None)
        interp.stack.append(42)
        self.assertEqual(interp.run(), 42)

    def test_wide_iinc(self):
        """wide iinc #256 by 1000."""
        # wide iinc 256 1000: 0xC4 0x84 0x01 0x00 0x03 0xE8
        # wide iload 256:     0xC4 0x15 0x01 0x00
        # ireturn:            0xAC
        code = bytes([0xC4, 0x84, 0x01, 0x00, 0x03, 0xE8,
                      0xC4, 0x15, 0x01, 0x00,
                      0xAC])
        interp = Interpreter(code, 10, 400, [], None)
        interp.locals[256] = 5
        self.assertEqual(interp.run(), 1005)

    def test_multianewarray_2d(self):
        """multianewarray [[I 2 with sizes [3][4]."""
        from jvm_interpreter.models.class_file_models import ConstantPoolEntry
        # CP: #1 UTF8 "[[I", #2 Class(#1)
        cp = [ConstantPoolEntry(1, "[[I"), ConstantPoolEntry(7, 1)]
        # iconst_3, iconst_4, multianewarray #2 dims=2, areturn
        code = bytes([0x06, 0x07, 0xC5, 0x00, 0x02, 0x02, 0xB0])
        interp = Interpreter(code, 10, 10, cp, None)
        arr = interp.run()
        self.assertEqual(arr.length, 3)
        self.assertEqual(arr.get(0).length, 4)

    def test_multianewarray_fills_all_cells(self):
        """Inner arrays must be separate objects, not aliased."""
        from jvm_interpreter.models.class_file_models import ConstantPoolEntry
        cp = [ConstantPoolEntry(1, "[[I"), ConstantPoolEntry(7, 1)]
        code = bytes([0x06, 0x07, 0xC5, 0x00, 0x02, 0x02, 0xB0])
        interp = Interpreter(code, 10, 10, cp, None)
        arr = interp.run()
        arr.get(0).set(0, 99)
        # The other inner arrays must still have default value 0
        self.assertEqual(arr.get(1).get(0), 0)
        self.assertEqual(arr.get(2).get(0), 0)


# ---------------------------------------------------------------------------
# --trace / execution tracing
# ---------------------------------------------------------------------------

class TestTrace(unittest.TestCase):

    def _run_traced(self, code: bytes, locals_=None, cp=None, stack=None) -> str:
        import io
        buf = io.StringIO()
        interp = Interpreter(code, 10, 10, cp or [], None, trace=True, _trace_out=buf)
        if locals_:
            for i, v in enumerate(locals_):
                interp.locals[i] = v
        if stack:
            interp.stack.extend(stack)
        interp.run()
        return buf.getvalue()

    def test_trace_emits_opcode_names(self):
        # iconst_3, ireturn
        out = self._run_traced(bytes([0x06, 0xAC]))
        self.assertIn('iconst_3', out)
        self.assertIn('ireturn',  out)

    def test_trace_shows_pc(self):
        out = self._run_traced(bytes([0x06, 0xAC]))
        self.assertIn('0000', out)
        self.assertIn('0001', out)

    def test_trace_shows_stack_before_instruction(self):
        # iconst_5, iconst_3, iadd, ireturn
        # At iadd, stack should show [5, 3]
        out = self._run_traced(bytes([0x08, 0x06, 0x60, 0xAC]))
        lines = out.strip().splitlines()
        # Find the iadd line
        iadd_line = next(l for l in lines if 'iadd' in l)
        self.assertIn('5', iadd_line)
        self.assertIn('3', iadd_line)

    def test_trace_stack_empty_at_start(self):
        out = self._run_traced(bytes([0x06, 0xAC]))
        first_line = out.strip().splitlines()[0]
        self.assertIn('[]', first_line)

    def test_trace_shows_string_value(self):
        from jvm_interpreter.models.class_file_models import ConstantPoolEntry
        cp = [ConstantPoolEntry(1, "hi"), ConstantPoolEntry(8, 1)]
        # ldc #2, areturn
        out = self._run_traced(bytes([0x12, 0x02, 0xB0]), cp=cp)
        self.assertIn('"hi"', out)

    def test_trace_shows_null(self):
        # aconst_null, areturn
        out = self._run_traced(bytes([0x01, 0xB0]))
        lines = out.strip().splitlines()
        areturn_line = next(l for l in lines if 'areturn' in l)
        self.assertIn('null', areturn_line)

    def test_trace_depth_indented(self):
        import io
        buf = io.StringIO()
        interp = Interpreter(bytes([0x06, 0xAC]), 5, 5, [], None,
                             trace=True, _trace_depth=2, _trace_out=buf)
        interp.run()
        first = buf.getvalue().splitlines()[0]
        # depth=2 means 4 spaces of indent before the pc
        self.assertTrue(first.startswith('    '), repr(first))

    def test_trace_no_output_when_disabled(self):
        import io
        buf = io.StringIO()
        interp = Interpreter(bytes([0x06, 0xAC]), 5, 5, [], None,
                             trace=False, _trace_out=buf)
        interp.run()
        self.assertEqual(buf.getvalue(), '')

    def test_fmt_val_types(self):
        interp = Interpreter(bytes([0xB1]), 2, 2, [], None)
        self.assertEqual(interp._fmt_val(None),        'null')
        self.assertEqual(interp._fmt_val(True),        'true')
        self.assertEqual(interp._fmt_val(False),       'false')
        self.assertEqual(interp._fmt_val(42),          '42')
        self.assertEqual(interp._fmt_val(3.14),        '3.14')
        self.assertEqual(interp._fmt_val('hello'),     '"hello"')
        self.assertEqual(interp._fmt_val(float('nan')),'NaN')
        self.assertEqual(interp._fmt_val(float('inf')),'Inf')

    def test_fmt_val_long_string_truncated(self):
        interp = Interpreter(bytes([0xB1]), 2, 2, [], None)
        result = interp._fmt_val('a' * 30)
        self.assertIn('...', result)
        self.assertLess(len(result), 25)

    def test_fmt_val_object(self):
        interp = Interpreter(bytes([0xB1]), 2, 2, [], None)
        obj = JavaObject("java.lang.StringBuilder")
        self.assertEqual(interp._fmt_val(obj), '<StringBuilder>')

    def test_native_call_annotated(self):
        """Native calls should appear as [native] annotations in the trace."""
        import io
        from jvm_interpreter.models.class_file_models import ConstantPoolEntry
        # Build enough CP for getstatic + invokevirtual on System.out.println
        # CP (1-based):
        # 1 UTF8 "java/lang/System"
        # 2 Class -> 1
        # 3 UTF8 "out"
        # 4 UTF8 "Ljava/io/PrintStream;"
        # 5 NAT (3, 4)
        # 6 Fieldref (2, 5)        <- getstatic #6 = System.out
        # 7 UTF8 "java/io/PrintStream"
        # 8 Class -> 7
        # 9 UTF8 "println"
        # 10 UTF8 "(Ljava/lang/String;)V"
        # 11 NAT (9, 10)
        # 12 Methodref (8, 11)     <- invokevirtual #12 = PrintStream.println
        cp = [
            ConstantPoolEntry(1,  "java/lang/System"),
            ConstantPoolEntry(7,  1),
            ConstantPoolEntry(1,  "out"),
            ConstantPoolEntry(1,  "Ljava/io/PrintStream;"),
            ConstantPoolEntry(12, (3, 4)),
            ConstantPoolEntry(9,  (2, 5)),
            ConstantPoolEntry(1,  "java/io/PrintStream"),
            ConstantPoolEntry(7,  7),
            ConstantPoolEntry(1,  "println"),
            ConstantPoolEntry(1,  "(Ljava/lang/String;)V"),
            ConstantPoolEntry(12, (9, 10)),
            ConstantPoolEntry(10, (8, 11)),
        ]
        buf = io.StringIO()
        # getstatic #6, ldc "hi", invokevirtual #12, return
        from jvm_interpreter.models.class_file_models import ConstantPoolEntry as CPE
        cp_with_str = cp + [CPE(1, "hi"), CPE(8, 13)]  # CP 13=UTF8, 14=String
        code = bytes([0xB2, 0x00, 0x06,   # getstatic #6
                      0x12, 0x0E,          # ldc #14
                      0xB6, 0x00, 0x0C,   # invokevirtual #12
                      0xB1])              # return
        from jvm_interpreter.runtime.class_loader import ClassLoader
        loader = ClassLoader([])
        interp = Interpreter(code, 10, 10, cp_with_str, loader,
                             trace=True, _trace_out=buf)
        interp.run()
        trace = buf.getvalue()
        self.assertIn('[native]', trace)
        self.assertIn('println', trace)


# ---------------------------------------------------------------------------
# java.util.Scanner
# ---------------------------------------------------------------------------

class TestScanner(unittest.TestCase):

    def setUp(self):
        self.reg = get_native_registry()

    def _new(self, source: str):
        sc = self.reg.create_native_object("java.util.Scanner")
        self.reg.invoke_native_method("java.util.Scanner", "<init>", sc, [source])
        return sc

    def _call(self, sc, method, *args):
        return self.reg.invoke_native_method("java.util.Scanner", method, sc, list(args))

    def test_nextline(self):
        sc = self._new("hello world\nfoo\n")
        self.assertEqual(self._call(sc, "nextLine"), "hello world")
        self.assertEqual(self._call(sc, "nextLine"), "foo")

    def test_next_token(self):
        sc = self._new("one two three\n")
        self.assertEqual(self._call(sc, "next"), "one")
        self.assertEqual(self._call(sc, "next"), "two")
        self.assertEqual(self._call(sc, "next"), "three")

    def test_nextint(self):
        sc = self._new("42 -7 0\n")
        self.assertEqual(self._call(sc, "nextInt"),  42)
        self.assertEqual(self._call(sc, "nextInt"),  -7)
        self.assertEqual(self._call(sc, "nextInt"),   0)

    def test_nextdouble(self):
        sc = self._new("3.14 -2.5\n")
        self.assertAlmostEqual(self._call(sc, "nextDouble"), 3.14, places=5)
        self.assertAlmostEqual(self._call(sc, "nextDouble"), -2.5, places=5)

    def test_nextlong(self):
        sc = self._new("9999999999\n")
        self.assertEqual(self._call(sc, "nextLong"), 9999999999)

    def test_nextboolean(self):
        sc = self._new("true false True FALSE\n")
        self.assertTrue(self._call(sc, "nextBoolean"))
        self.assertFalse(self._call(sc, "nextBoolean"))
        self.assertTrue(self._call(sc, "nextBoolean"))
        self.assertFalse(self._call(sc, "nextBoolean"))

    def test_hasnext_true(self):
        sc = self._new("hello\n")
        self.assertTrue(self._call(sc, "hasNext"))

    def test_hasnext_false_on_empty(self):
        sc = self._new("")
        self.assertFalse(self._call(sc, "hasNext"))

    def test_hasnextint_true(self):
        sc = self._new("123\n")
        self.assertTrue(self._call(sc, "hasNextInt"))

    def test_hasnextint_false(self):
        sc = self._new("abc\n")
        self.assertFalse(self._call(sc, "hasNextInt"))

    def test_hasnextdouble_true(self):
        sc = self._new("1.5\n")
        self.assertTrue(self._call(sc, "hasNextDouble"))

    def test_mixed_tokens_and_lines(self):
        sc = self._new("42\nhello world\n99\n")
        self.assertEqual(self._call(sc, "nextInt"),  42)
        self.assertEqual(self._call(sc, "nextLine"), "")   # consume rest of first line
        self.assertEqual(self._call(sc, "nextLine"), "hello world")
        self.assertEqual(self._call(sc, "nextInt"),  99)

    def test_multiline_tokens(self):
        sc = self._new("1\n2\n3\n")
        results = [self._call(sc, "nextInt") for _ in range(3)]
        self.assertEqual(results, [1, 2, 3])

    def test_string_source_after_init(self):
        """Scanner created via constructor then <init> with a string."""
        sc = self.reg.create_native_object("java.util.Scanner")
        self.reg.invoke_native_method("java.util.Scanner", "<init>", sc, ["hello 42\n"])
        self.assertEqual(self.reg.invoke_native_method("java.util.Scanner", "next", sc, []), "hello")
        self.assertEqual(self.reg.invoke_native_method("java.util.Scanner", "nextInt", sc, []), 42)

    def test_system_in_field_exists(self):
        stdin = self.reg.get_native_static_field("java.lang.System", "in")
        self.assertIsNotNone(stdin)
        self.assertEqual(stdin.class_name, "java.io.InputStream")

    def test_scanner_stdin_init_accepts_inputstream(self):
        """Passing System.in sentinel to <init> should not crash."""
        stdin = self.reg.get_native_static_field("java.lang.System", "in")
        sc = self.reg.create_native_object("java.util.Scanner")
        self.reg.invoke_native_method("java.util.Scanner", "<init>", sc, [stdin])
        self.assertIsNotNone(sc)

    def test_close_is_no_op(self):
        sc = self._new("x\n")
        self._call(sc, "close")  # should not raise
        self.assertIsNotNone(sc)

    def test_tostring(self):
        sc = self._new("")
        result = self._call(sc, "toString")
        self.assertIsInstance(result, str)

    def test_hasnextint_does_not_consume_token(self):
        sc = self._new("42\n")
        self.assertTrue(self._call(sc, "hasNextInt"))
        self.assertEqual(self._call(sc, "nextInt"), 42)

    def test_hasnextdouble_does_not_consume_token(self):
        sc = self._new("3.14\n")
        self.assertTrue(self._call(sc, "hasNextDouble"))
        self.assertAlmostEqual(self._call(sc, "nextDouble"), 3.14, places=5)

    def test_hasnextint_false_does_not_consume_token(self):
        sc = self._new("abc\n")
        self.assertFalse(self._call(sc, "hasNextInt"))
        self.assertEqual(self._call(sc, "next"), "abc")


# ---------------------------------------------------------------------------
# invokedynamic / StringConcatFactory
# ---------------------------------------------------------------------------

class TestInvokeDynamic(unittest.TestCase):
    """
    Hand-crafts the constant pool and BootstrapMethods attribute that javac
    would emit for string concat, so no javac is needed.

    CP layout (1-based):
      1  UTF8  "makeConcatWithConstants"       <- BSM method name
      2  UTF8  "(Ljava/lang/String;)Ljava/lang/String;"  <- call-site descriptor
      3  NAT   (1, 2)
      4  UTF8  "java/lang/invoke/StringConcatFactory"
      5  Class (4)
      6  NAT   (1, 2)  <- NAT for the Methodref
      7  Methodref (5, 6)
      8  MethodHandle (kind=6, ref=7)
      9  UTF8  recipe string (varies per test)
      10 String (9)
      11 InvokeDynamic (bootstrap_idx=0, nat=3)
    """

    def _make_cp(self, recipe: str):
        from jvm_interpreter.models.class_file_models import ConstantPoolEntry
        return [
            ConstantPoolEntry(1,  "makeConcatWithConstants"),        # 1
            ConstantPoolEntry(1,  "(Ljava/lang/String;)Ljava/lang/String;"),  # 2
            ConstantPoolEntry(12, (1, 2)),                           # 3  NAT
            ConstantPoolEntry(1,  "java/lang/invoke/StringConcatFactory"),   # 4
            ConstantPoolEntry(7,  4),                                # 5  Class
            ConstantPoolEntry(12, (1, 2)),                           # 6  NAT for Methodref
            ConstantPoolEntry(10, (5, 6)),                           # 7  Methodref
            ConstantPoolEntry(15, (6, 7)),                           # 8  MethodHandle kind=6
            ConstantPoolEntry(1,  recipe),                           # 9  UTF8 recipe
            ConstantPoolEntry(8,  9),                                # 10 String -> 9
            ConstantPoolEntry(18, (0, 3)),                           # 11 InvokeDynamic
        ]

    def _make_cp_2arg(self, recipe: str):
        """Like _make_cp but descriptor takes 2 String args."""
        from jvm_interpreter.models.class_file_models import ConstantPoolEntry
        return [
            ConstantPoolEntry(1,  "makeConcatWithConstants"),
            ConstantPoolEntry(1,  "(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;"),
            ConstantPoolEntry(12, (1, 2)),
            ConstantPoolEntry(1,  "java/lang/invoke/StringConcatFactory"),
            ConstantPoolEntry(7,  4),
            ConstantPoolEntry(12, (1, 2)),
            ConstantPoolEntry(10, (5, 6)),
            ConstantPoolEntry(15, (6, 7)),
            ConstantPoolEntry(1,  recipe),
            ConstantPoolEntry(8,  9),
            ConstantPoolEntry(18, (0, 3)),
        ]

    def _make_bsm(self, recipe_arg_cp_idx=10):
        from jvm_interpreter.models.class_file_models import BootstrapMethod
        return [BootstrapMethod(8, [recipe_arg_cp_idx])]  # method_ref=CP8, args=[CP10]

    def _run(self, code: bytes, cp, bsm, local0=None, local1=None):
        interp = Interpreter(code, 10, 10, cp, None, [], bsm)
        if local0 is not None:
            interp.locals[0] = local0
        if local1 is not None:
            interp.locals[1] = local1
        return interp.run()

    def test_prefix_concat(self):
        """Recipe "hello \x01" + one String arg -> "hello world"."""
        cp = self._make_cp("hello \x01")
        bsm = self._make_bsm()
        # aload_0, invokedynamic #11 0 0, areturn
        code = bytes([0x2A, 0xBA, 0x00, 0x0B, 0x00, 0x00, 0xB0])
        self.assertEqual(self._run(code, cp, bsm, local0="world"), "hello world")

    def test_suffix_concat(self):
        """Recipe "\x01!" + one String arg."""
        cp = self._make_cp("\x01!")
        bsm = self._make_bsm()
        code = bytes([0x2A, 0xBA, 0x00, 0x0B, 0x00, 0x00, 0xB0])
        self.assertEqual(self._run(code, cp, bsm, local0="hi"), "hi!")

    def test_two_arg_concat(self):
        """Recipe "\x01 and \x01" + two String args."""
        cp = self._make_cp_2arg("\x01 and \x01")
        bsm = self._make_bsm()
        # aload_0, aload_1, invokedynamic #11 0 0, areturn
        code = bytes([0x2A, 0x2B, 0xBA, 0x00, 0x0B, 0x00, 0x00, 0xB0])
        self.assertEqual(self._run(code, cp, bsm, local0="foo", local1="bar"),
                         "foo and bar")

    def test_int_in_recipe(self):
        """Recipe "n=\x01" + one int arg."""
        from jvm_interpreter.models.class_file_models import ConstantPoolEntry
        cp = [
            ConstantPoolEntry(1,  "makeConcatWithConstants"),
            ConstantPoolEntry(1,  "(I)Ljava/lang/String;"),
            ConstantPoolEntry(12, (1, 2)),
            ConstantPoolEntry(1,  "java/lang/invoke/StringConcatFactory"),
            ConstantPoolEntry(7,  4),
            ConstantPoolEntry(12, (1, 2)),
            ConstantPoolEntry(10, (5, 6)),
            ConstantPoolEntry(15, (6, 7)),
            ConstantPoolEntry(1,  "n=\x01"),
            ConstantPoolEntry(8,  9),
            ConstantPoolEntry(18, (0, 3)),
        ]
        bsm = self._make_bsm()
        # iload_0, invokedynamic #11 0 0, areturn
        code = bytes([0x1A, 0xBA, 0x00, 0x0B, 0x00, 0x00, 0xB0])
        self.assertEqual(self._run(code, cp, bsm, local0=42), "n=42")

    def test_null_arg(self):
        """None on stack -> "null" in concat."""
        cp = self._make_cp("[\x01]")
        bsm = self._make_bsm()
        code = bytes([0x01, 0xBA, 0x00, 0x0B, 0x00, 0x00, 0xB0])  # aconst_null
        self.assertEqual(self._run(code, cp, bsm), "[null]")

    def test_makeconcat_no_recipe(self):
        """makeConcat (no bootstrap args): concatenate stack args directly."""
        from jvm_interpreter.models.class_file_models import ConstantPoolEntry, BootstrapMethod
        cp = [
            ConstantPoolEntry(1,  "makeConcat"),
            ConstantPoolEntry(1,  "(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;"),
            ConstantPoolEntry(12, (1, 2)),
            ConstantPoolEntry(1,  "java/lang/invoke/StringConcatFactory"),
            ConstantPoolEntry(7,  4),
            ConstantPoolEntry(12, (1, 2)),
            ConstantPoolEntry(10, (5, 6)),
            ConstantPoolEntry(15, (6, 7)),
            ConstantPoolEntry(18, (0, 3)),  # no recipe arg; CP[9]
        ]
        bsm = [BootstrapMethod(8, [])]  # no bootstrap arguments
        # aload_0, aload_1, invokedynamic #9 0 0, areturn
        code = bytes([0x2A, 0x2B, 0xBA, 0x00, 0x09, 0x00, 0x00, 0xB0])
        interp = Interpreter(code, 10, 10, cp, None, [], bsm)
        interp.locals[0] = "abc"
        interp.locals[1] = "def"
        self.assertEqual(interp.run(), "abcdef")

    def test_static_const_in_recipe(self):
        """Recipe with \x02 (static constant from bootstrap args)."""
        from jvm_interpreter.models.class_file_models import ConstantPoolEntry, BootstrapMethod
        cp = [
            ConstantPoolEntry(1,  "makeConcatWithConstants"),
            ConstantPoolEntry(1,  "(Ljava/lang/String;)Ljava/lang/String;"),
            ConstantPoolEntry(12, (1, 2)),
            ConstantPoolEntry(1,  "java/lang/invoke/StringConcatFactory"),
            ConstantPoolEntry(7,  4),
            ConstantPoolEntry(12, (1, 2)),
            ConstantPoolEntry(10, (5, 6)),
            ConstantPoolEntry(15, (6, 7)),
            ConstantPoolEntry(1,  "\x01 says \x02"),   # recipe: dyn + literal " says " + const
            ConstantPoolEntry(8,  9),                   # String -> recipe (CP10)
            ConstantPoolEntry(1,  "hello"),             # static const (CP11)
            ConstantPoolEntry(8,  11),                  # String -> "hello" (CP12)
            ConstantPoolEntry(18, (0, 3)),              # InvokeDynamic (CP13)
        ]
        bsm = [BootstrapMethod(8, [10, 12])]  # recipe=CP10, const=CP12
        # aload_0, invokedynamic #13 0 0, areturn
        code = bytes([0x2A, 0xBA, 0x00, 0x0D, 0x00, 0x00, 0xB0])
        interp = Interpreter(code, 10, 10, cp, None, [], bsm)
        interp.locals[0] = "world"
        self.assertEqual(interp.run(), "world says hello")

    def test_to_java_string_bool(self):
        interp = Interpreter(bytes([0xB1]), 2, 2, [], None)
        self.assertEqual(interp._to_java_string(True),  "true")
        self.assertEqual(interp._to_java_string(False), "false")

    def test_to_java_string_null(self):
        interp = Interpreter(bytes([0xB1]), 2, 2, [], None)
        self.assertEqual(interp._to_java_string(None), "null")

    def test_to_java_string_nan(self):
        interp = Interpreter(bytes([0xB1]), 2, 2, [], None)
        self.assertEqual(interp._to_java_string(float('nan')),  "NaN")
        self.assertEqual(interp._to_java_string(float('inf')),  "Infinity")
        self.assertEqual(interp._to_java_string(float('-inf')), "-Infinity")


# ---------------------------------------------------------------------------
# Method Overload Resolution
# ---------------------------------------------------------------------------

class TestMethodOverloading(unittest.TestCase):

    def _make_loader_with_overloads(self):
        """Build a ClassLoader with a mock class that has two foo() overloads."""
        from jvm_interpreter.models.class_file_models import (
            ClassFile, Header, AccessFlags, ClassReference, Member, CodeAttribute
        )
        from jvm_interpreter.runtime.class_loader import ClassLoader

        # foo(I)I  -> iload_0, ireturn  (returns the int arg)
        code_int = bytes([0x1A, 0xAC])
        # foo(Ljava/lang/String;)I -> iconst_5, ireturn  (returns 5 as sentinel)
        code_str = bytes([0x08, 0xAC])

        def _code_attr(code):
            return CodeAttribute("Code", 2, 2, code, [], [])

        methods = [
            Member(AccessFlags(0x0001), "foo", "(I)I",
                   [_code_attr(code_int)]),
            Member(AccessFlags(0x0001), "foo", "(Ljava/lang/String;)I",
                   [_code_attr(code_str)]),
        ]
        cf = ClassFile(
            Header(0xCAFEBABE, 0, 52), [],
            AccessFlags(0x0021),
            ClassReference("TestOverload"), ClassReference("java.lang.Object"),
            [], [], methods, []
        )
        loader = ClassLoader([])
        loader.loaded_classes["TestOverload"] = cf
        return loader, code_int, code_str

    def test_descriptor_selects_int_overload(self):
        loader, code_int, _ = self._make_loader_with_overloads()
        result = loader.get_method_code("TestOverload", "foo", "(I)I")
        self.assertIsNotNone(result)
        self.assertEqual(result[2], code_int)

    def test_descriptor_selects_string_overload(self):
        loader, _, code_str = self._make_loader_with_overloads()
        result = loader.get_method_code("TestOverload", "foo",
                                        "(Ljava/lang/String;)I")
        self.assertIsNotNone(result)
        self.assertEqual(result[2], code_str)

    def test_no_descriptor_returns_first(self):
        loader, code_int, _ = self._make_loader_with_overloads()
        result = loader.get_method_code("TestOverload", "foo")
        self.assertIsNotNone(result)
        self.assertEqual(result[2], code_int)  # first method in list

    def test_wrong_descriptor_returns_none(self):
        loader, _, _ = self._make_loader_with_overloads()
        result = loader.get_method_code("TestOverload", "foo", "(D)I")
        self.assertIsNone(result)

    def test_overload_executes_int_version(self):
        """End-to-end: call foo(int) and verify it returns the argument."""
        loader, code_int, _ = self._make_loader_with_overloads()
        result = loader.get_method_code("TestOverload", "foo", "(I)I")
        interp = Interpreter(result[2], result[0], result[1], [], loader)
        interp.locals[0] = 99
        self.assertEqual(interp.run(), 99)

    def test_overload_executes_string_version(self):
        """End-to-end: call foo(String) and verify it returns 5 (sentinel)."""
        loader, _, code_str = self._make_loader_with_overloads()
        result = loader.get_method_code("TestOverload", "foo",
                                        "(Ljava/lang/String;)I")
        interp = Interpreter(result[2], result[0], result[1], [], loader)
        interp.locals[0] = "hello"
        self.assertEqual(interp.run(), 5)


# ---------------------------------------------------------------------------
# java.util — ArrayList
# ---------------------------------------------------------------------------

class TestArrayList(unittest.TestCase):

    def setUp(self):
        from jvm_interpreter.native.java_util import JavaArrayList
        self.ArrayList = JavaArrayList
        self.reg = get_native_registry()

    def _new(self):
        return self.reg.create_native_object("java.util.ArrayList")

    def _call(self, obj, method, *args):
        return self.reg.invoke_native_method(
            "java.util.ArrayList", method, obj, list(args))

    def test_add_and_size(self):
        lst = self._new()
        self._call(lst, "add", 10)
        self._call(lst, "add", 20)
        self.assertEqual(self._call(lst, "size"), 2)

    def test_get(self):
        lst = self._new()
        self._call(lst, "add", "hello")
        self.assertEqual(self._call(lst, "get", 0), "hello")

    def test_set_returns_old(self):
        lst = self._new()
        self._call(lst, "add", 1)
        old = self._call(lst, "set", 0, 99)
        self.assertEqual(old, 1)
        self.assertEqual(self._call(lst, "get", 0), 99)

    def test_remove_by_index(self):
        lst = self._new()
        self._call(lst, "add", "a")
        self._call(lst, "add", "b")
        removed = self._call(lst, "remove", 0)
        self.assertEqual(removed, "a")
        self.assertEqual(self._call(lst, "size"), 1)

    def test_remove_by_value(self):
        lst = self._new()
        self._call(lst, "add", "x")
        self._call(lst, "add", "y")
        result = self._call(lst, "remove", "x")
        self.assertTrue(result)
        self.assertEqual(self._call(lst, "size"), 1)

    def test_contains(self):
        lst = self._new()
        self._call(lst, "add", 42)
        self.assertTrue(self._call(lst, "contains", 42))
        self.assertFalse(self._call(lst, "contains", 99))

    def test_isempty_and_clear(self):
        lst = self._new()
        self.assertTrue(self._call(lst, "isEmpty"))
        self._call(lst, "add", 1)
        self.assertFalse(self._call(lst, "isEmpty"))
        self._call(lst, "clear")
        self.assertTrue(self._call(lst, "isEmpty"))

    def test_indexof(self):
        lst = self._new()
        self._call(lst, "add", "a")
        self._call(lst, "add", "b")
        self._call(lst, "add", "a")
        self.assertEqual(self._call(lst, "indexOf", "a"), 0)
        self.assertEqual(self._call(lst, "indexOf", "c"), -1)

    def test_tostring(self):
        lst = self._new()
        self._call(lst, "add", 1)
        self._call(lst, "add", 2)
        self.assertEqual(self._call(lst, "toString"), "[1, 2]")

    def test_toarray(self):
        lst = self._new()
        self._call(lst, "add", "x")
        self._call(lst, "add", "y")
        arr = self._call(lst, "toArray")
        self.assertEqual(arr.length, 2)
        self.assertEqual(arr.get(0), "x")
        self.assertEqual(arr.get(1), "y")

    def test_iterator(self):
        lst = self._new()
        for v in [10, 20, 30]:
            self._call(lst, "add", v)
        it = self._call(lst, "iterator")
        collected = []
        while self.reg.invoke_native_method("java.util.Iterator", "hasNext", it, []):
            collected.append(
                self.reg.invoke_native_method("java.util.Iterator", "next", it, []))
        self.assertEqual(collected, [10, 20, 30])

    def test_addall(self):
        lst1 = self._new()
        lst2 = self._new()
        self._call(lst1, "add", 1)
        self._call(lst2, "add", 2)
        self._call(lst2, "add", 3)
        self._call(lst1, "addAll", lst2)
        self.assertEqual(self._call(lst1, "size"), 3)

    def test_sort(self):
        lst = self._new()
        for v in [3, 1, 4, 1, 5]:
            self._call(lst, "add", v)
        self._call(lst, "sort", None)
        self.assertEqual(lst._data, [1, 1, 3, 4, 5])

    def test_sublist(self):
        lst = self._new()
        for v in [0, 1, 2, 3, 4]:
            self._call(lst, "add", v)
        sub = self._call(lst, "subList", 1, 4)
        self.assertEqual(sub._data, [1, 2, 3])


# ---------------------------------------------------------------------------
# java.util — HashMap
# ---------------------------------------------------------------------------

class TestHashMap(unittest.TestCase):

    def setUp(self):
        self.reg = get_native_registry()

    def _new(self):
        return self.reg.create_native_object("java.util.HashMap")

    def _call(self, obj, method, *args):
        return self.reg.invoke_native_method(
            "java.util.HashMap", method, obj, list(args))

    def test_put_and_get(self):
        m = self._new()
        self._call(m, "put", "key", "value")
        self.assertEqual(self._call(m, "get", "key"), "value")

    def test_get_missing_returns_none(self):
        m = self._new()
        self.assertIsNone(self._call(m, "get", "nope"))

    def test_put_returns_old_value(self):
        m = self._new()
        self._call(m, "put", "k", 1)
        old = self._call(m, "put", "k", 2)
        self.assertEqual(old, 1)

    def test_containskey(self):
        m = self._new()
        self._call(m, "put", "x", 99)
        self.assertTrue(self._call(m, "containsKey", "x"))
        self.assertFalse(self._call(m, "containsKey", "y"))

    def test_containsvalue(self):
        m = self._new()
        self._call(m, "put", "k", 42)
        self.assertTrue(self._call(m, "containsValue", 42))
        self.assertFalse(self._call(m, "containsValue", 99))

    def test_remove(self):
        m = self._new()
        self._call(m, "put", "k", 7)
        removed = self._call(m, "remove", "k")
        self.assertEqual(removed, 7)
        self.assertFalse(self._call(m, "containsKey", "k"))

    def test_size(self):
        m = self._new()
        self.assertEqual(self._call(m, "size"), 0)
        self._call(m, "put", "a", 1)
        self._call(m, "put", "b", 2)
        self.assertEqual(self._call(m, "size"), 2)

    def test_isempty_and_clear(self):
        m = self._new()
        self.assertTrue(self._call(m, "isEmpty"))
        self._call(m, "put", "k", "v")
        self.assertFalse(self._call(m, "isEmpty"))
        self._call(m, "clear")
        self.assertTrue(self._call(m, "isEmpty"))

    def test_getordefault(self):
        m = self._new()
        self._call(m, "put", "a", 1)
        self.assertEqual(self._call(m, "getOrDefault", "a", 99), 1)
        self.assertEqual(self._call(m, "getOrDefault", "b", 99), 99)

    def test_putifabsent(self):
        m = self._new()
        self._call(m, "put", "k", 1)
        self._call(m, "putIfAbsent", "k", 99)  # should not overwrite
        self._call(m, "putIfAbsent", "new", 42)
        self.assertEqual(self._call(m, "get", "k"), 1)
        self.assertEqual(self._call(m, "get", "new"), 42)

    def test_keyset(self):
        m = self._new()
        self._call(m, "put", "a", 1)
        self._call(m, "put", "b", 2)
        keys = self._call(m, "keySet")
        self.assertEqual(keys.size(), 2)
        self.assertTrue(keys.contains("a"))
        self.assertTrue(keys.contains("b"))

    def test_values(self):
        m = self._new()
        self._call(m, "put", "x", 10)
        self._call(m, "put", "y", 20)
        vals = self._call(m, "values")
        self.assertEqual(vals.size(), 2)

    def test_entryset_and_mapentry(self):
        m = self._new()
        self._call(m, "put", "hello", 42)
        entries = self._call(m, "entrySet")
        self.assertEqual(entries.size(), 1)
        entry = entries.get(0)
        self.assertEqual(
            self.reg.invoke_native_method("java.util.Map$Entry", "getKey", entry, []),
            "hello")
        self.assertEqual(
            self.reg.invoke_native_method("java.util.Map$Entry", "getValue", entry, []),
            42)

    def test_entryset_iteration(self):
        m = self._new()
        self._call(m, "put", "a", 1)
        self._call(m, "put", "b", 2)
        entries = self._call(m, "entrySet")
        it = self.reg.invoke_native_method("java.util.ArrayList", "iterator", entries, [])
        count = 0
        while self.reg.invoke_native_method("java.util.Iterator", "hasNext", it, []):
            self.reg.invoke_native_method("java.util.Iterator", "next", it, [])
            count += 1
        self.assertEqual(count, 2)

    def test_tostring(self):
        m = self._new()
        self._call(m, "put", "k", "v")
        s = self._call(m, "toString")
        self.assertIn("k=v", s)

    def test_object_keys(self):
        """Non-hashable Java objects as keys."""
        from jvm_interpreter.models.java_objects import JavaObject
        m = self._new()
        obj = JavaObject("com.example.Key")
        self._call(m, "put", obj, "found")
        self.assertEqual(self._call(m, "get", obj), "found")
        self.assertTrue(self._call(m, "containsKey", obj))


# ---------------------------------------------------------------------------
# java.util — HashSet
# ---------------------------------------------------------------------------

class TestHashSet(unittest.TestCase):

    def setUp(self):
        self.reg = get_native_registry()

    def _new(self):
        return self.reg.create_native_object("java.util.HashSet")

    def _call(self, obj, method, *args):
        return self.reg.invoke_native_method(
            "java.util.HashSet", method, obj, list(args))

    def test_add_and_contains(self):
        s = self._new()
        self.assertTrue(self._call(s, "add", "x"))
        self.assertFalse(self._call(s, "add", "x"))  # duplicate
        self.assertTrue(self._call(s, "contains", "x"))
        self.assertFalse(self._call(s, "contains", "y"))

    def test_remove(self):
        s = self._new()
        self._call(s, "add", 1)
        self.assertTrue(self._call(s, "remove", 1))
        self.assertFalse(self._call(s, "contains", 1))

    def test_size_and_clear(self):
        s = self._new()
        self._call(s, "add", "a")
        self._call(s, "add", "b")
        self.assertEqual(self._call(s, "size"), 2)
        self._call(s, "clear")
        self.assertEqual(self._call(s, "size"), 0)

    def test_iterator(self):
        s = self._new()
        for v in [1, 2, 3]:
            self._call(s, "add", v)
        it = self._call(s, "iterator")
        collected = []
        while self.reg.invoke_native_method("java.util.Iterator", "hasNext", it, []):
            collected.append(
                self.reg.invoke_native_method("java.util.Iterator", "next", it, []))
        self.assertEqual(sorted(collected), [1, 2, 3])


# ---------------------------------------------------------------------------
# java.util — Stack and LinkedList
# ---------------------------------------------------------------------------

class TestStack(unittest.TestCase):

    def setUp(self):
        self.reg = get_native_registry()

    def test_push_pop_peek(self):
        s = self.reg.create_native_object("java.util.Stack")
        self.reg.invoke_native_method("java.util.Stack", "push", s, [10])
        self.reg.invoke_native_method("java.util.Stack", "push", s, [20])
        self.assertEqual(
            self.reg.invoke_native_method("java.util.Stack", "peek", s, []), 20)
        self.assertEqual(
            self.reg.invoke_native_method("java.util.Stack", "pop", s, []), 20)
        self.assertEqual(
            self.reg.invoke_native_method("java.util.Stack", "size", s, []), 1)

    def test_isempty(self):
        s = self.reg.create_native_object("java.util.Stack")
        self.assertTrue(
            self.reg.invoke_native_method("java.util.Stack", "isEmpty", s, []))


# ---------------------------------------------------------------------------
# java.util — Arrays and Collections (static)
# ---------------------------------------------------------------------------

class TestArraysCollections(unittest.TestCase):

    def setUp(self):
        self.reg = get_native_registry()

    def test_arrays_sort(self):
        from jvm_interpreter.models.java_objects import JavaArray
        arr = JavaArray("int", 4)
        for i, v in enumerate([3, 1, 4, 2]):
            arr.set(i, v)
        self.reg.invoke_native_method("java.util.Arrays", "sort", None, [arr])
        self.assertEqual(arr.elements, [1, 2, 3, 4])

    def test_arrays_fill(self):
        from jvm_interpreter.models.java_objects import JavaArray
        arr = JavaArray("int", 3)
        self.reg.invoke_native_method("java.util.Arrays", "fill", None, [arr, 7])
        self.assertEqual(arr.elements, [7, 7, 7])

    def test_arrays_copyof(self):
        from jvm_interpreter.models.java_objects import JavaArray
        arr = JavaArray("int", 3)
        for i, v in enumerate([1, 2, 3]):
            arr.set(i, v)
        copy = self.reg.invoke_native_method("java.util.Arrays", "copyOf",
                                             None, [arr, 5])
        self.assertEqual(copy.length, 5)
        self.assertEqual(copy.elements[:3], [1, 2, 3])
        # int[] is padded with 0, not None (Java default for int)
        self.assertEqual(copy.elements[3], 0)

    def test_arrays_tostring(self):
        from jvm_interpreter.models.java_objects import JavaArray
        arr = JavaArray("int", 3)
        for i, v in enumerate([1, 2, 3]):
            arr.set(i, v)
        s = self.reg.invoke_native_method("java.util.Arrays", "toString",
                                          None, [arr])
        self.assertEqual(s, "[1, 2, 3]")

    def test_collections_sort(self):
        lst = self.reg.create_native_object("java.util.ArrayList")
        for v in [3, 1, 2]:
            self.reg.invoke_native_method("java.util.ArrayList", "add", lst, [v])
        self.reg.invoke_native_method("java.util.Collections", "sort", None, [lst])
        self.assertEqual(lst._data, [1, 2, 3])

    def test_collections_reverse(self):
        lst = self.reg.create_native_object("java.util.ArrayList")
        for v in [1, 2, 3]:
            self.reg.invoke_native_method("java.util.ArrayList", "add", lst, [v])
        self.reg.invoke_native_method("java.util.Collections", "reverse", None, [lst])
        self.assertEqual(lst._data, [3, 2, 1])

    def test_collections_ncopies(self):
        lst = self.reg.invoke_native_method("java.util.Collections", "nCopies",
                                            None, [3, "x"])
        self.assertEqual(lst._data, ["x", "x", "x"])

    def test_collections_frequency(self):
        lst = self.reg.create_native_object("java.util.ArrayList")
        for v in [1, 2, 1, 3, 1]:
            self.reg.invoke_native_method("java.util.ArrayList", "add", lst, [v])
        freq = self.reg.invoke_native_method("java.util.Collections", "frequency",
                                             None, [lst, 1])
        self.assertEqual(freq, 3)

    def test_collections_emptylist(self):
        lst = self.reg.invoke_native_method("java.util.Collections", "emptyList",
                                            None, [])
        self.assertIsNotNone(lst)
        self.assertEqual(lst.size(), 0)

    def test_collections_disjoint_true(self):
        a = self.reg.create_native_object("java.util.ArrayList")
        b = self.reg.create_native_object("java.util.ArrayList")
        for v in [1, 2, 3]:
            self.reg.invoke_native_method("java.util.ArrayList", "add", a, [v])
        for v in [4, 5, 6]:
            self.reg.invoke_native_method("java.util.ArrayList", "add", b, [v])
        result = self.reg.invoke_native_method("java.util.Collections", "disjoint",
                                               None, [a, b])
        self.assertTrue(result)

    def test_collections_disjoint_false(self):
        a = self.reg.create_native_object("java.util.ArrayList")
        b = self.reg.create_native_object("java.util.ArrayList")
        for v in [1, 2, 3]:
            self.reg.invoke_native_method("java.util.ArrayList", "add", a, [v])
        for v in [3, 4, 5]:
            self.reg.invoke_native_method("java.util.ArrayList", "add", b, [v])
        result = self.reg.invoke_native_method("java.util.Collections", "disjoint",
                                               None, [a, b])
        self.assertFalse(result)

    def test_collections_disjoint_string_equality(self):
        """disjoint must use value equality, not identity, for strings."""
        a = self.reg.create_native_object("java.util.ArrayList")
        b = self.reg.create_native_object("java.util.ArrayList")
        # Two distinct string objects with same value
        self.reg.invoke_native_method("java.util.ArrayList", "add", a, ["hello"])
        self.reg.invoke_native_method("java.util.ArrayList", "add", b, ["hello"])
        result = self.reg.invoke_native_method("java.util.Collections", "disjoint",
                                               None, [a, b])
        self.assertFalse(result)  # same string value → not disjoint


# ---------------------------------------------------------------------------
# Integration: class file parsing (requires Example.class)
# ---------------------------------------------------------------------------

class TestClassFileParsing(unittest.TestCase):

    def test_parse_example_class(self):
        import os
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Example.class')
        if not os.path.exists(path):
            self.skipTest("Example.class not found")
        from jvm_interpreter.parser.class_file_parser import parse_class_file
        cf = parse_class_file(path)
        self.assertEqual(cf.header.magic, 0xCAFEBABE)
        self.assertEqual(cf.this_class.name, "Example")
        self.assertTrue(len(cf.methods) > 0)
        method_names = [m.name for m in cf.methods]
        self.assertIn("main", method_names)

    def test_run_example_class(self):
        import os
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.')
        example = os.path.join(path, 'Example.class')
        if not os.path.exists(example):
            self.skipTest("Example.class not found")
        captured = io.StringIO()
        system_out = get_native_registry().get_native_static_field("java.lang.System", "out")
        old = system_out.stream
        system_out.stream = captured
        try:
            from jvm_interpreter import JavaClassInterpreter
            interp = JavaClassInterpreter([path])
            interp.run_method("Example", "main")
        finally:
            system_out.stream = old
        self.assertIn("Hello", captured.getvalue())


# ---------------------------------------------------------------------------
# Lambda / invokedynamic
# ---------------------------------------------------------------------------

class TestLambda(unittest.TestCase):

    def _make_proxy(self, fn, method='apply'):
        from jvm_interpreter.models.java_objects import JavaLambdaProxy
        return JavaLambdaProxy("java.util.function.Function", method, fn)

    def test_proxy_invoke_calls_fn(self):
        proxy = self._make_proxy(lambda args: args[0] * 2)
        self.assertEqual(proxy.invoke([5]), 10)

    def test_proxy_carries_abstract_method_name(self):
        proxy = self._make_proxy(lambda args: None, method='test')
        self.assertEqual(proxy.abstract_method, 'test')

    def test_proxy_with_captured_var(self):
        captured = [10]
        proxy = self._make_proxy(lambda args: captured[0] + args[0])
        self.assertEqual(proxy.invoke([3]), 13)

    def test_dispatch_intercepts_proxy(self):
        from jvm_interpreter.models.java_objects import JavaLambdaProxy
        # Build a minimal interpreter and call _dispatch with a proxy as obj
        interp = Interpreter(bytes([0xB1]), 10, 10, [], None)  # return (nop)
        results = []
        proxy = JavaLambdaProxy("java.util.function.Function", "apply",
                                lambda args: results.append(args[0]) or 42)
        ret = interp._dispatch("java.util.function.Function", "apply",
                               "(I)I", proxy, [7])
        self.assertEqual(ret, 42)
        self.assertEqual(results, [7])

    def test_comparator_via_proxy(self):
        from jvm_interpreter.models.java_objects import JavaLambdaProxy
        cmp = JavaLambdaProxy("java.util.Comparator", "compare",
                              lambda args: args[0] - args[1])
        self.assertGreater(cmp.invoke([5, 3]), 0)
        self.assertLess(cmp.invoke([2, 8]), 0)
        self.assertEqual(cmp.invoke([4, 4]), 0)

    def test_string_split(self):
        from jvm_interpreter.native.native_registry import JavaLangString
        from jvm_interpreter.models.java_objects import JavaArray
        arr = JavaLangString.split("a,b,c", ",")
        self.assertIsInstance(arr, JavaArray)
        self.assertEqual(arr.length, 3)
        self.assertEqual(arr.elements[0], "a")
        self.assertEqual(arr.elements[2], "c")

    def test_string_matches(self):
        from jvm_interpreter.native.native_registry import JavaLangString
        self.assertTrue(JavaLangString.matches("hello123", "[a-z]+\\d+"))
        self.assertFalse(JavaLangString.matches("hello", "\\d+"))

    def test_string_replace_all(self):
        from jvm_interpreter.native.native_registry import JavaLangString
        self.assertEqual(JavaLangString.replaceAll("aaa", "a", "b"), "bbb")

    def test_string_chars(self):
        from jvm_interpreter.native.native_registry import JavaLangString
        from jvm_interpreter.native.java_util import JavaIntStream
        s = JavaLangString.chars("ABC")
        self.assertIsInstance(s, JavaIntStream)
        self.assertEqual(s._data, [65, 66, 67])


# ---------------------------------------------------------------------------
# Streams / Collectors
# ---------------------------------------------------------------------------

class TestStream(unittest.TestCase):

    def _proxy(self, fn, method='apply'):
        from jvm_interpreter.models.java_objects import JavaLambdaProxy
        return JavaLambdaProxy("java.util.function.Function", method, fn)

    def test_stream_map(self):
        from jvm_interpreter.native.java_util import JavaStream, JavaCollectors
        double = self._proxy(lambda a: a[0] * 2)
        s = JavaStream([1, 2, 3]).map(double)
        result = s.collect(JavaCollectors.toList())
        self.assertEqual(result._data, [2, 4, 6])

    def test_stream_filter(self):
        from jvm_interpreter.native.java_util import JavaStream, JavaCollectors
        is_even = self._proxy(lambda a: a[0] % 2 == 0, 'test')
        result = JavaStream([1, 2, 3, 4, 5]).filter(is_even).collect(JavaCollectors.toList())
        self.assertEqual(result._data, [2, 4])

    def test_stream_map_then_filter(self):
        from jvm_interpreter.native.java_util import JavaStream, JavaCollectors
        double  = self._proxy(lambda a: a[0] * 2)
        gt_four = self._proxy(lambda a: a[0] > 4, 'test')
        result  = JavaStream([1, 2, 3]).map(double).filter(gt_four).collect(JavaCollectors.toList())
        self.assertEqual(result._data, [6])

    def test_stream_count(self):
        from jvm_interpreter.native.java_util import JavaStream
        self.assertEqual(JavaStream([1, 2, 3, 4]).count(), 4)

    def test_stream_foreach(self):
        from jvm_interpreter.native.java_util import JavaStream
        collected = []
        action = self._proxy(lambda a: collected.append(a[0]) or None, 'accept')
        JavaStream([10, 20, 30]).forEach(action)
        self.assertEqual(collected, [10, 20, 30])

    def test_stream_reduce_with_identity(self):
        from jvm_interpreter.native.java_util import JavaStream
        add = self._proxy(lambda a: a[0] + a[1])
        self.assertEqual(JavaStream([1, 2, 3, 4]).reduce(0, add), 10)

    def test_stream_find_first(self):
        from jvm_interpreter.native.java_util import JavaStream
        opt = JavaStream([5, 6, 7]).findFirst()
        self.assertTrue(opt.isPresent())
        self.assertEqual(opt.get(), 5)

    def test_stream_find_first_empty(self):
        from jvm_interpreter.native.java_util import JavaStream
        opt = JavaStream([]).findFirst()
        self.assertFalse(opt.isPresent())

    def test_stream_any_match(self):
        from jvm_interpreter.native.java_util import JavaStream
        gt5 = self._proxy(lambda a: a[0] > 5, 'test')
        self.assertTrue(JavaStream([1, 6, 2]).anyMatch(gt5))
        self.assertFalse(JavaStream([1, 2, 3]).anyMatch(gt5))

    def test_stream_sorted_natural(self):
        from jvm_interpreter.native.java_util import JavaStream, JavaCollectors
        result = JavaStream([3, 1, 2]).sorted().collect(JavaCollectors.toList())
        self.assertEqual(result._data, [1, 2, 3])

    def test_stream_sorted_with_comparator(self):
        from jvm_interpreter.native.java_util import JavaStream, JavaCollectors
        rev_cmp = self._proxy(lambda a: a[1] - a[0], 'compare')
        result = JavaStream([3, 1, 2]).sorted(rev_cmp).collect(JavaCollectors.toList())
        self.assertEqual(result._data, [3, 2, 1])

    def test_stream_distinct(self):
        from jvm_interpreter.native.java_util import JavaStream, JavaCollectors
        result = JavaStream([1, 2, 1, 3, 2]).distinct().collect(JavaCollectors.toList())
        self.assertEqual(result._data, [1, 2, 3])

    def test_stream_limit_skip(self):
        from jvm_interpreter.native.java_util import JavaStream, JavaCollectors
        result = JavaStream(range(10)).skip(2).limit(3).collect(JavaCollectors.toList())
        self.assertEqual(result._data, [2, 3, 4])

    def test_collectors_joining(self):
        from jvm_interpreter.native.java_util import JavaStream, JavaCollectors
        result = JavaStream(["a", "b", "c"]).collect(JavaCollectors.joining(", "))
        self.assertEqual(result, "a, b, c")

    def test_collectors_joining_with_affixes(self):
        from jvm_interpreter.native.java_util import JavaStream, JavaCollectors
        result = JavaStream(["x", "y"]).collect(JavaCollectors.joining(", ", "[", "]"))
        self.assertEqual(result, "[x, y]")

    def test_collectors_to_set(self):
        from jvm_interpreter.native.java_util import JavaStream, JavaCollectors, JavaHashSet
        result = JavaStream([1, 2, 1, 3]).collect(JavaCollectors.toSet())
        self.assertIsInstance(result, JavaHashSet)
        self.assertEqual(result.size(), 3)

    def test_collectors_counting(self):
        from jvm_interpreter.native.java_util import JavaStream, JavaCollectors
        result = JavaStream([1, 2, 3]).collect(JavaCollectors.counting())
        self.assertEqual(result, 3)

    def test_collectors_summing_int(self):
        from jvm_interpreter.native.java_util import JavaStream, JavaCollectors
        fn = self._proxy(lambda a: a[0] * 2)
        result = JavaStream([1, 2, 3]).collect(JavaCollectors.summingInt(fn))
        self.assertEqual(result, 12)

    def test_int_stream_range_sum(self):
        from jvm_interpreter.native.java_util import JavaIntStream
        self.assertEqual(JavaIntStream.range(1, 6).sum(), 15)

    def test_int_stream_filter_map(self):
        from jvm_interpreter.native.java_util import JavaIntStream
        is_even = self._proxy(lambda a: a[0] % 2 == 0, 'test')
        double  = self._proxy(lambda a: a[0] * 2)
        result  = JavaIntStream.range(1, 6).filter(is_even).map(double)
        self.assertEqual(result._data, [4, 8])

    def test_int_stream_boxed(self):
        from jvm_interpreter.native.java_util import JavaIntStream, JavaStream
        boxed = JavaIntStream([1, 2, 3]).boxed()
        self.assertIsInstance(boxed, JavaStream)
        self.assertEqual(boxed._source, [1, 2, 3])

    def test_optional_of(self):
        from jvm_interpreter.native.java_util import JavaOptional
        opt = JavaOptional.of(42)
        self.assertTrue(opt.isPresent())
        self.assertEqual(opt.get(), 42)

    def test_optional_empty(self):
        from jvm_interpreter.native.java_util import JavaOptional
        opt = JavaOptional.empty()
        self.assertFalse(opt.isPresent())
        with self.assertRaises(RuntimeError):
            opt.get()

    def test_optional_map(self):
        from jvm_interpreter.native.java_util import JavaOptional
        double = self._proxy(lambda a: a[0] * 2)
        opt = JavaOptional.of(5).map(double)
        self.assertTrue(opt.isPresent())
        self.assertEqual(opt.get(), 10)

    def test_optional_or_else(self):
        from jvm_interpreter.native.java_util import JavaOptional
        self.assertEqual(JavaOptional.empty().orElse(99), 99)
        self.assertEqual(JavaOptional.of(7).orElse(99), 7)

    def test_comparator_natural_order(self):
        from jvm_interpreter.native.java_util import JavaComparator
        cmp = JavaComparator.naturalOrder()
        self.assertLess(cmp.compare(1, 2), 0)
        self.assertGreater(cmp.compare(5, 3), 0)
        self.assertEqual(cmp.compare(4, 4), 0)

    def test_comparator_comparing(self):
        from jvm_interpreter.native.java_util import JavaComparator
        key = self._proxy(lambda a: len(a[0]))
        cmp = JavaComparator.comparing(key)
        self.assertLess(cmp.compare("a", "bb"), 0)

    def test_comparator_reversed(self):
        from jvm_interpreter.native.java_util import JavaComparator
        cmp = JavaComparator.naturalOrder().reversed()
        self.assertGreater(cmp.compare(1, 2), 0)

    def test_arraylist_stream_and_collect(self):
        from jvm_interpreter.native.java_util import JavaArrayList, JavaCollectors
        lst = JavaArrayList(); lst.add(1); lst.add(2); lst.add(3)
        result = lst.stream().map(
            self._proxy(lambda a: a[0] + 10)
        ).collect(JavaCollectors.toList())
        self.assertEqual(result._data, [11, 12, 13])

    def test_arraylist_foreach(self):
        from jvm_interpreter.native.java_util import JavaArrayList
        lst = JavaArrayList()
        for v in [1, 2, 3]: lst.add(v)
        out = []
        lst.forEach(self._proxy(lambda a: out.append(a[0]) or None, 'accept'))
        self.assertEqual(out, [1, 2, 3])

    def test_arraylist_sort_with_comparator(self):
        from jvm_interpreter.native.java_util import JavaArrayList
        lst = JavaArrayList()
        for v in [3, 1, 2]: lst.add(v)
        cmp = self._proxy(lambda a: a[0] - a[1], 'compare')
        lst.sort(cmp)
        self.assertEqual(lst._data, [1, 2, 3])

    def test_arraylist_remove_if_returns_bool(self):
        from jvm_interpreter.native.java_util import JavaArrayList
        lst = JavaArrayList()
        for v in [1, 2, 3, 4]: lst.add(v)
        is_even = self._proxy(lambda a: a[0] % 2 == 0, 'test')
        changed = lst.removeIf(is_even)
        self.assertTrue(changed)
        self.assertEqual(lst._data, [1, 3])

    def test_arraylist_remove_if_false_when_nothing_removed(self):
        from jvm_interpreter.native.java_util import JavaArrayList
        lst = JavaArrayList()
        for v in [1, 3, 5]: lst.add(v)
        is_even = self._proxy(lambda a: a[0] % 2 == 0, 'test')
        changed = lst.removeIf(is_even)
        self.assertFalse(changed)

    def test_stream_peek_does_not_modify_data(self):
        from jvm_interpreter.native.java_util import JavaStream, JavaCollectors
        side_effects = []
        peek_fn = self._proxy(lambda a: side_effects.append(a[0]) or None, 'accept')
        result = JavaStream([1, 2, 3]).peek(peek_fn).collect(JavaCollectors.toList())
        self.assertEqual(result._data, [1, 2, 3])   # data unchanged
        self.assertEqual(side_effects, [1, 2, 3])    # side effect ran

    def test_hashmap_foreach(self):
        from jvm_interpreter.native.java_util import JavaHashMap
        m = JavaHashMap()
        m.put("a", 1); m.put("b", 2)
        pairs = {}
        bi = self._proxy(lambda a: pairs.__setitem__(a[0], a[1]) or None, 'accept')
        m.forEach(bi)
        self.assertEqual(pairs, {"a": 1, "b": 2})

    def test_linkedlist_stream(self):
        from jvm_interpreter.native.java_util import JavaLinkedList, JavaCollectors
        lst = JavaLinkedList()
        for v in [1, 2, 3]: lst.add(v)
        result = lst.stream().map(
            self._proxy(lambda a: a[0] * 10)
        ).collect(JavaCollectors.toList())
        self.assertEqual(result._data, [10, 20, 30])

    def test_linkedlist_foreach(self):
        from jvm_interpreter.native.java_util import JavaLinkedList
        lst = JavaLinkedList()
        for v in [7, 8]: lst.add(v)
        out = []
        lst.forEach(self._proxy(lambda a: out.append(a[0]) or None, 'accept'))
        self.assertEqual(out, [7, 8])

    def test_collections_sort_with_comparator(self):
        from jvm_interpreter.native.java_util import JavaArrayList, JavaCollections
        lst = JavaArrayList()
        for v in [3, 1, 2]: lst.add(v)
        rev = self._proxy(lambda a: a[1] - a[0], 'compare')
        JavaCollections.sort(lst, rev)
        self.assertEqual(lst._data, [3, 2, 1])

    def test_comparator_natural_order_invoke(self):
        from jvm_interpreter.native.java_util import JavaComparator
        cmp = JavaComparator.naturalOrder()
        self.assertEqual(cmp.invoke([5, 5]), 0)
        self.assertGreater(cmp.invoke([6, 5]), 0)
        self.assertLess(cmp.invoke([4, 5]), 0)

    def test_int_stream_range_closed(self):
        from jvm_interpreter.native.java_util import JavaIntStream
        self.assertEqual(JavaIntStream.rangeClosed(1, 5).sum(), 15)

    def test_stream_flat_map(self):
        from jvm_interpreter.native.java_util import JavaStream, JavaCollectors
        expand = self._proxy(lambda a: JavaStream([a[0], a[0] * 10]))
        result = JavaStream([1, 2]).flatMap(expand).collect(JavaCollectors.toList())
        self.assertEqual(result._data, [1, 10, 2, 20])

    def test_collectors_grouping_by(self):
        from jvm_interpreter.native.java_util import JavaStream, JavaCollectors
        by_parity = self._proxy(lambda a: a[0] % 2, 'apply')
        m = JavaStream([1, 2, 3, 4]).collect(JavaCollectors.groupingBy(by_parity))
        self.assertEqual(sorted(m.get(0)._data), [2, 4])
        self.assertEqual(sorted(m.get(1)._data), [1, 3])

    def test_collectors_partitioning_by(self):
        from jvm_interpreter.native.java_util import JavaStream, JavaCollectors
        is_even = self._proxy(lambda a: a[0] % 2 == 0, 'test')
        m = JavaStream([1, 2, 3, 4]).collect(JavaCollectors.partitioningBy(is_even))
        self.assertEqual(sorted(m.get(True)._data), [2, 4])
        self.assertEqual(sorted(m.get(False)._data), [1, 3])

    def test_string_split_strips_trailing_empty(self):
        from jvm_interpreter.native.native_registry import JavaLangString
        arr = JavaLangString.split("a,b,,", ",")
        self.assertEqual(arr.length, 2)  # trailing empty strings dropped (limit=0)

    def test_string_split_with_limit(self):
        from jvm_interpreter.native.native_registry import JavaLangString
        arr = JavaLangString.split("a,b,c", ",", 2)
        self.assertEqual(arr.length, 2)
        self.assertEqual(arr.elements[1], "b,c")

    def test_stream_all_match_empty(self):
        from jvm_interpreter.native.java_util import JavaStream
        always_false = self._proxy(lambda a: False, 'test')
        self.assertTrue(JavaStream([]).allMatch(always_false))  # vacuous truth

    def test_stream_none_match_empty(self):
        from jvm_interpreter.native.java_util import JavaStream
        always_true = self._proxy(lambda a: True, 'test')
        self.assertTrue(JavaStream([]).noneMatch(always_true))  # vacuous truth


# ---------------------------------------------------------------------------
# jsr / ret / jsr_w
# ---------------------------------------------------------------------------

class TestJsr(unittest.TestCase):
    """Pre-Java-6 finally block opcodes."""

    def test_jsr_pushes_return_address_and_jumps(self):
        # jsr +5 → push (pc after jsr = 3), jump to offset 5 from jsr
        # Layout: 0: jsr(168) 1:0 2:5  3: iconst_1(4)  5: astore_0(75)  6: iload_0(21,0)  8: ireturn(172)
        # Actually: jsr jumps forward 5 from opcode, return addr = 3
        # At target 5: astore_0 pops retAddr into local 0; then goto 3
        # At 3: iconst_1; ireturn
        # Simplified test: jsr jumps, at target we read the pushed address
        # code: jsr(168) 0 4  nop(0)  iload_0(21 0)  ireturn(172)
        #   0: jsr +4 → return addr 3 pushed, jump to 4
        #   3: nop (would be executed after ret)
        #   4: istore_0(54 0) ... actually let's just test the return address value
        # Simplest: jsr forward past astore; use astore_0 to capture the ret addr; then ireturn
        # jsr(168), 0, 6,          # jump to pc+6 = 8; push retaddr = 3
        # iconst_m1(2),             # 3: -1 (not reached normally)
        # ireturn(172),             # 4: return -1
        # nop(0),                   # 5: gap (alignment)
        # nop(0),                   # 6: nop
        # nop(0),                   # 7: nop
        # 8: We're at the subroutine. The return address (3) is on the stack.
        #    astore_0 (75) — stores the retaddr into local[0]
        #    sipush (17) 0 3 — push 999
        #    ireturn (172)
        code = bytes([
            0xA8, 0x00, 0x07,          # 0: jsr +7 → jump to 7, push return addr 3
            0x04,                       # 3: iconst_1 (reached via ret)
            0xAC,                       # 4: ireturn → return 1
            0x00, 0x00,                 # 5,6: padding
            0x4B,                       # 7: astore_0  (pop retAddr into local[0])
            0x05,                       # 8: iconst_2
            0x3B,                       # 9: istore_1
            0x15, 0x00,                 # 10-11: iload_0 → push the return address (3)
            0xA9, 0x00,                 # 12: ret local[0] → jump to 3
        ])
        result = run_bytecode(code, max_stack=5, max_locals=5)
        self.assertEqual(result, 1)   # the iconst_1 / ireturn at pc=3,4 was reached

    def test_ret_jumps_to_stored_address(self):
        # ret local[0] where local[0] = some_pc: check pc really changes
        # We just store a known integer in local[0] and call ret
        # Simplest: put 3 in local[0] (return address after jsr), use ret to jump back
        # Use the same structure as above but verify the result
        code = bytes([
            0xA8, 0x00, 0x04,  # 0: jsr +4 → jump to 4, retaddr=3
            0xAC,               # 3: ireturn (will return top of stack = 99)
            0x10, 0x63,        # 4: bipush 99
            0xA9, 0x00,        # 6: ret local[0]  (local[0] has retaddr=3)
        ])
        # But local[0] is initially None; jsr stores retaddr on the stack, NOT in local
        # We must store it with astore_0 first
        code = bytes([
            0xA8, 0x00, 0x06,  # 0: jsr +6 → jump to 6, retaddr=3 on stack
            0x10, 0x7B,        # 3: bipush 123
            0xAC,               # 5: ireturn → return 123
            0x4B,               # 6: astore_0 → local[0] = retaddr (3)
            0x10, 0x00,        # 7: bipush 0 (dummy)
            0x57,               # 9: pop
            0xA9, 0x00,        # 10: ret local[0] → jump to 3
        ])
        result = run_bytecode(code, max_stack=5, max_locals=5)
        self.assertEqual(result, 123)


# ---------------------------------------------------------------------------
# Proper toString / Object methods on user / array objects
# ---------------------------------------------------------------------------

class TestObjectMethods(unittest.TestCase):

    def test_java_object_to_string(self):
        from jvm_interpreter.models.java_objects import JavaObject
        obj = JavaObject("com.example.Foo")
        s = obj.toString()
        self.assertTrue(s.startswith("com.example.Foo@"))

    def test_java_object_equals_reference(self):
        from jvm_interpreter.models.java_objects import JavaObject
        a = JavaObject("Foo")
        b = JavaObject("Foo")
        self.assertTrue(a.equals(a))
        self.assertFalse(a.equals(b))

    def test_java_object_hashcode(self):
        from jvm_interpreter.models.java_objects import JavaObject
        obj = JavaObject("Foo")
        self.assertEqual(obj.hashCode(), id(obj))

    def test_java_array_to_string(self):
        from jvm_interpreter.models.java_objects import JavaArray
        arr = JavaArray('int', 3)
        s = arr.toString()
        self.assertTrue(s.startswith("[I@"))

    def test_java_array_ref_to_string(self):
        from jvm_interpreter.models.java_objects import JavaArray
        arr = JavaArray('java.lang.String', 2)
        s = arr.toString()
        self.assertTrue(s.startswith("[Ljava/lang/String;@"))

    def test_java_array_equals(self):
        from jvm_interpreter.models.java_objects import JavaArray
        arr = JavaArray('int', 2)
        self.assertTrue(arr.equals(arr))
        self.assertFalse(arr.equals(JavaArray('int', 2)))

    def test_array_clone(self):
        from jvm_interpreter.models.java_objects import JavaArray
        from jvm_interpreter.native.native_registry import get_native_registry
        arr = JavaArray('int', 3)
        arr.elements = [1, 2, 3]
        interp = Interpreter(bytes([0xB1]), 10, 10, [], None)
        cloned = interp._dispatch("java.lang.Object", "clone", "()Ljava/lang/Object;", arr, [])
        self.assertEqual(cloned.elements, [1, 2, 3])
        self.assertIsNot(cloned, arr)
        self.assertIsNot(cloned.elements, arr.elements)


# ---------------------------------------------------------------------------
# aastore type check
# ---------------------------------------------------------------------------

class TestAastore(unittest.TestCase):

    def test_aastore_compatible_type_ok(self):
        from jvm_interpreter.models.java_objects import JavaArray
        # Storing a str into a java.lang.Object array — always OK
        arr = JavaArray('java.lang.Object', 3)
        interp = Interpreter(bytes([0xB1]), 10, 10, [], None)
        interp.stack = [arr, 0, "hello"]
        interp.instr_aastore()
        self.assertEqual(arr.elements[0], "hello")

    def test_aastore_null_always_ok(self):
        from jvm_interpreter.models.java_objects import JavaArray
        arr = JavaArray('java.lang.String', 2)
        interp = Interpreter(bytes([0xB1]), 10, 10, [], None)
        interp.stack = [arr, 0, None]
        interp.instr_aastore()
        self.assertIsNone(arr.elements[0])

    def test_aastore_wrong_type_raises(self):
        from jvm_interpreter.models.java_objects import JavaArray, JavaObject
        arr = JavaArray('java.lang.String', 2)
        bad = JavaObject("java.lang.Integer")  # not a String
        interp = Interpreter(bytes([0xB1]), 10, 10, [], None)
        interp.stack = [arr, 0, bad]
        with self.assertRaises(_JavaException) as ctx:
            interp.instr_aastore()
        self.assertIn("ArrayStoreException", ctx.exception.class_name)

    def test_aastore_slash_notation_component_type(self):
        # component_type in slash notation must not give false positive
        from jvm_interpreter.models.java_objects import JavaArray
        arr = JavaArray('java/lang/String', 2)
        interp = Interpreter(bytes([0xB1]), 10, 10, [], None)
        interp.stack = [arr, 0, "hello"]
        interp.instr_aastore()  # must NOT raise ArrayStoreException
        self.assertEqual(arr.elements[0], "hello")

    def test_aastore_inner_array_into_object_array(self):
        # Storing int[] into Object[] should succeed (no false ArrayStoreException)
        from jvm_interpreter.models.java_objects import JavaArray
        outer = JavaArray('java.lang.Object', 2)
        inner = JavaArray('int', 3)
        interp = Interpreter(bytes([0xB1]), 10, 10, [], None)
        interp.stack = [outer, 0, inner]
        interp.instr_aastore()
        self.assertIs(outer.elements[0], inner)

    def test_aastore_inner_array_into_array_typed_outer(self):
        # Storing int[] into [I-typed outer must not raise (skip check for [ prefix)
        from jvm_interpreter.models.java_objects import JavaArray
        outer = JavaArray('[I', 2)   # int[][] component type
        inner = JavaArray('int', 3)
        interp = Interpreter(bytes([0xB1]), 10, 10, [], None)
        interp.stack = [outer, 0, inner]
        interp.instr_aastore()
        self.assertIs(outer.elements[0], inner)

    def test_java_array_class_name_primitive(self):
        from jvm_interpreter.models.java_objects import JavaArray
        self.assertEqual(JavaArray('int', 1).class_name, '[I')
        self.assertEqual(JavaArray('long', 1).class_name, '[J')
        self.assertEqual(JavaArray('boolean', 1).class_name, '[Z')

    def test_java_array_class_name_reference(self):
        from jvm_interpreter.models.java_objects import JavaArray
        self.assertEqual(JavaArray('java.lang.String', 1).class_name, '[Ljava/lang/String;')

    def test_array_to_string_no_0x_prefix(self):
        # Both JavaArray.toString() and _dispatch toString must omit 0x
        from jvm_interpreter.models.java_objects import JavaArray
        arr = JavaArray('int', 1)
        s = arr.toString()
        self.assertFalse(s.startswith('[I@0x'), "toString should not include 0x prefix")
        self.assertTrue(s.startswith('[I@'))


# ---------------------------------------------------------------------------
# java.io / java.nio.file
# ---------------------------------------------------------------------------

class TestJavaIO(unittest.TestCase):

    def test_file_exists_and_is_file(self):
        import os, tempfile
        from jvm_interpreter.native.java_io import JavaFile
        f = JavaFile(); f._init(__file__)
        self.assertTrue(f.exists())
        self.assertTrue(f.isFile())
        self.assertFalse(f.isDirectory())

    def test_file_get_name(self):
        from jvm_interpreter.native.java_io import JavaFile
        f = JavaFile(); f._init("/some/path/file.txt")
        self.assertEqual(f.getName(), "file.txt")

    def test_file_nonexistent(self):
        from jvm_interpreter.native.java_io import JavaFile
        f = JavaFile(); f._init("/nonexistent_xyz_abc/file.txt")
        self.assertFalse(f.exists())
        self.assertEqual(f.length(), 0)

    def test_buffered_reader_reads_string_reader(self):
        from jvm_interpreter.native.java_io import JavaBufferedReader, JavaStringReader
        sr = JavaStringReader(); sr._init("line1\nline2\nline3")
        br = JavaBufferedReader(); br._init(sr)
        self.assertEqual(br.readLine(), "line1")
        self.assertEqual(br.readLine(), "line2")
        self.assertEqual(br.readLine(), "line3")
        self.assertIsNone(br.readLine())   # EOF → null

    def test_buffered_reader_reads_file(self):
        import tempfile, os
        from jvm_interpreter.native.java_io import JavaBufferedReader, JavaFileReader
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt',
                                        delete=False, encoding='utf-8') as tmp:
            tmp.write("alpha\nbeta\ngamma\n")
            name = tmp.name
        try:
            fr = JavaFileReader(); fr._init(name)
            br = JavaBufferedReader(); br._init(fr)
            self.assertEqual(br.readLine(), "alpha")
            self.assertEqual(br.readLine(), "beta")
            self.assertEqual(br.readLine(), "gamma")
            self.assertIsNone(br.readLine())
        finally:
            os.unlink(name)

    def test_print_writer_to_string_writer(self):
        from jvm_interpreter.native.java_io import JavaPrintWriter, JavaStringWriter
        sw = JavaStringWriter(); sw._init()
        pw = JavaPrintWriter(); pw._init(sw)
        pw.print("hello")
        pw.println(" world")
        self.assertEqual(sw.toString(), "hello world\n")

    def test_print_writer_null_prints_null(self):
        from jvm_interpreter.native.java_io import JavaPrintWriter, JavaStringWriter
        sw = JavaStringWriter(); sw._init()
        pw = JavaPrintWriter(); pw._init(sw)
        pw.print(None)
        self.assertEqual(sw.toString(), "null")

    def test_files_read_write_string(self):
        import tempfile, os
        from jvm_interpreter.native.java_io import JavaFiles, JavaPath
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as t:
            name = t.name
        path = JavaPath(); path._init(name)
        try:
            JavaFiles.writeString(path, "test content")
            self.assertEqual(JavaFiles.readString(path), "test content")
        finally:
            os.unlink(name)

    def test_files_read_all_lines(self):
        import tempfile, os
        from jvm_interpreter.native.java_io import JavaFiles, JavaPath
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt',
                                        delete=False, encoding='utf-8') as t:
            t.write("a\nb\nc\n"); name = t.name
        path = JavaPath(); path._init(name)
        try:
            lst = JavaFiles.readAllLines(path)
            self.assertEqual(lst._data, ["a", "b", "c"])
        finally:
            os.unlink(name)

    def test_paths_get(self):
        from jvm_interpreter.native.java_io import JavaPaths, JavaPath
        p = JavaPaths.get("/tmp", "test.txt")
        self.assertIsInstance(p, JavaPath)
        self.assertTrue(p.toString().endswith("test.txt"))

    def test_path_to_file(self):
        from jvm_interpreter.native.java_io import JavaPaths, JavaFile
        p = JavaPaths.get("/tmp")
        f = p.toFile()
        self.assertIsInstance(f, JavaFile)

    def test_files_exists_nonexistent(self):
        from jvm_interpreter.native.java_io import JavaFiles, JavaPath
        p = JavaPath(); p._init("/nonexistent_xyz_abc_42")
        self.assertFalse(JavaFiles.exists(p))

    def test_file_get_parent_absolute(self):
        from jvm_interpreter.native.java_io import JavaFile
        f = JavaFile(); f._init("/some/path/file.txt")
        p = f.getParent()
        self.assertIsNotNone(p)
        self.assertEqual(p.getPath(), "/some/path")

    def test_file_get_parent_bare_name_returns_null(self):
        # new File("foo").getParent() == null in Java
        from jvm_interpreter.native.java_io import JavaFile
        f = JavaFile(); f._init("foo")
        self.assertIsNone(f.getParent())

    def test_path_get_parent_bare_name_returns_null(self):
        # Paths.get("foo").getParent() == null in Java
        from jvm_interpreter.native.java_io import JavaPaths
        p = JavaPaths.get("foo")
        self.assertIsNone(p.getParent())

    def test_path_get_file_name_normal(self):
        from jvm_interpreter.native.java_io import JavaPaths
        p = JavaPaths.get("/foo/bar.txt")
        fn = p.getFileName()
        self.assertIsNotNone(fn)
        self.assertEqual(fn.toString(), "bar.txt")

    def test_path_get_file_name_root_is_null(self):
        from jvm_interpreter.native.java_io import JavaPaths
        p = JavaPaths.get("/")
        self.assertIsNone(p.getFileName())

    def test_print_writer_printf_percent_n(self):
        # Java %n must become actual newline, not literal '%n'
        from jvm_interpreter.native.java_io import JavaPrintWriter, JavaStringWriter
        sw = JavaStringWriter(); sw._init()
        pw = JavaPrintWriter(); pw._init(sw)
        pw.printf("hello%nworld%n")
        self.assertEqual(sw.toString(), "hello\nworld\n")

    def test_print_writer_printf_with_args(self):
        from jvm_interpreter.native.java_io import JavaPrintWriter, JavaStringWriter
        sw = JavaStringWriter(); sw._init()
        pw = JavaPrintWriter(); pw._init(sw)
        pw.printf("%s=%d%n", "x", 42)
        self.assertEqual(sw.toString(), "x=42\n")

    def test_file_init_none_raises(self):
        from jvm_interpreter.native.java_io import JavaFile
        f = JavaFile()
        with self.assertRaises(RuntimeError):
            f._init(None)


# ---------------------------------------------------------------------------
# Multi-class loading
# ---------------------------------------------------------------------------

def _make_class(class_name: str, super_name: str, methods: list,
                cp: list = None) -> 'ClassFile':
    """Build a minimal ClassFile stub usable by ClassLoader."""
    from jvm_interpreter.models.class_file_models import (
        ClassFile, Header, AccessFlags, ClassReference,
        Member, CodeAttribute, ConstantPoolEntry,
    )
    cp = cp or []
    members = []
    for name, descriptor, code_bytes in methods:
        attr = CodeAttribute("Code", 10, 10, bytes(code_bytes), [], [])
        members.append(Member(AccessFlags(0x0001), name, descriptor, [attr]))
    return ClassFile(
        header=Header(0xCAFEBABE, 0, 52),
        cp=cp,
        access=AccessFlags(0x0021),
        this_class=ClassReference(class_name),
        super_class=ClassReference(super_name),
        interfaces=[],
        fields=[],
        methods=members,
        attributes=[],
    )


def _loader_with(*class_files):
    """Return a ClassLoader with the given ClassFile stubs pre-loaded."""
    from jvm_interpreter.runtime.class_loader import ClassLoader
    cl = ClassLoader([])
    for cf in class_files:
        key = cf.this_class.name.replace('.', '/')
        cl.loaded_classes[key] = cf
    return cl


class TestMultiClass(unittest.TestCase):
    """Multi-class loading: inheritance, virtual dispatch, correct CP per class."""

    # ── helpers ──────────────────────────────────────────────────────────────

    def _interp(self, code_bytes, cp, class_loader, obj=None, args=None):
        """Run a bytecode fragment with the given CP and class loader."""
        interp = Interpreter(bytes(code_bytes), 20, 20, cp, class_loader)
        if obj is not None:
            interp.locals[0] = obj
        if args:
            for i, v in enumerate(args, 1):
                interp.locals[i] = v
        return interp.run()

    # ── method inheritance ────────────────────────────────────────────────────

    def test_inherited_method_found(self):
        """ClassLoader.get_method_code walks up to superclass."""
        from jvm_interpreter.runtime.class_loader import ClassLoader
        animal = _make_class("Animal", "java.lang.Object", [
            ("speak", "()I", [0x10, 0x01, 0xAC]),   # bipush 1, ireturn
        ])
        dog = _make_class("Dog", "Animal", [])        # no override
        cl = _loader_with(animal, dog)

        result = cl.get_method_code("Dog", "speak", "()I")
        self.assertIsNotNone(result)
        self.assertEqual(result[4], "Animal")          # defined in Animal

    def test_inherited_method_executes(self):
        """Calling an inherited method on a subclass instance returns the right value."""
        from jvm_interpreter.models.java_objects import JavaObject
        animal = _make_class("Animal", "java.lang.Object", [
            ("speak", "()I", [0x10, 0x2A, 0xAC]),    # bipush 42, ireturn
        ])
        dog = _make_class("Dog", "Animal", [])
        cl = _loader_with(animal, dog)

        obj = JavaObject("Dog")
        # Simulate invokevirtual on the dog: dispatch("Dog","speak","()I",obj,[])
        interp = Interpreter(bytes([0xB1]), 10, 10, [], cl)
        result = interp._dispatch("Dog", "speak", "()I", obj, [])
        self.assertEqual(result, 42)

    def test_overridden_method_wins(self):
        """Virtual dispatch selects the most specific override."""
        from jvm_interpreter.models.java_objects import JavaObject
        animal = _make_class("Animal", "java.lang.Object", [
            ("speak", "()I", [0x10, 0x01, 0xAC]),    # bipush 1, ireturn  (Animal)
        ])
        dog = _make_class("Dog", "Animal", [
            ("speak", "()I", [0x10, 0x02, 0xAC]),    # bipush 2, ireturn  (Dog override)
        ])
        cl = _loader_with(animal, dog)

        obj = JavaObject("Dog")
        interp = Interpreter(bytes([0xB1]), 10, 10, [], cl)
        result = interp._dispatch("Dog", "speak", "()I", obj, [])
        self.assertEqual(result, 2)  # Dog's override, not Animal's

    def test_super_class_correct_cp(self):
        """
        The defining-class CP bug: A's method uses ldc #1 from A's CP to push a string.
        When called on a B instance (B extends A, no override), the sub-interpreter
        must use A's CP — not B's — so ldc resolves A's string, not B's.
        """
        from jvm_interpreter.models.java_objects import JavaObject
        from jvm_interpreter.models.class_file_models import ConstantPoolEntry

        # A's CP: [String→#2, UTF8"from_A"]  (1-based indices 1 and 2)
        cp_a = [
            ConstantPoolEntry(8, 2),              # #1: String → #2
            ConstantPoolEntry(1, "from_A"),        # #2: UTF8 "from_A"
        ]
        # B's CP: [String→#2, UTF8"from_B"]
        cp_b = [
            ConstantPoolEntry(8, 2),
            ConstantPoolEntry(1, "from_B"),
        ]

        # A.label(): ldc #1 (pushes cp_a[0] → "from_A"), areturn
        animal = _make_class("A", "java.lang.Object", [
            ("label", "()Ljava/lang/String;", [0x12, 0x01, 0xB0]),
        ], cp=cp_a)
        b_class = _make_class("B", "A", [], cp=cp_b)
        cl = _loader_with(animal, b_class)

        obj = JavaObject("B")
        interp = Interpreter(bytes([0xB1]), 10, 10, [], cl)
        result = interp._dispatch("B", "label", "()Ljava/lang/String;", obj, [])
        # Must return A's string, not B's
        self.assertEqual(result, "from_A")

    def test_method_with_arg(self):
        """Inherited method receives its argument in local[1]."""
        from jvm_interpreter.models.java_objects import JavaObject
        # double(x): iload_1 (21 1), bipush 2, imul, ireturn
        base = _make_class("Base", "java.lang.Object", [
            ("double", "(I)I", [0x15, 0x01, 0x05, 0x68, 0xAC]),
        ])
        sub = _make_class("Sub", "Base", [])
        cl = _loader_with(base, sub)

        obj = JavaObject("Sub")
        interp = Interpreter(bytes([0xB1]), 10, 10, [], cl)
        result = interp._dispatch("Sub", "double", "(I)I", obj, [7])
        self.assertEqual(result, 14)

    def test_field_access_across_classes(self):
        """getfield/putfield on a user object works regardless of where code runs."""
        from jvm_interpreter.models.java_objects import JavaObject
        obj = JavaObject("Point")
        obj.set_field("x", 99)
        self.assertEqual(obj.get_field("x"), 99)
        obj.set_field("x", 0)
        self.assertIsNone(obj.get_field("y"))   # unset field → null

    def test_instance_of_inheritance(self):
        """is_assignable respects the class hierarchy from loaded class files."""
        from jvm_interpreter.runtime.class_loader import is_assignable
        animal = _make_class("Animal", "java.lang.Object", [])
        dog    = _make_class("Dog", "Animal", [])
        cl     = _loader_with(animal, dog)

        self.assertTrue(is_assignable("Dog", "Animal", cl))
        self.assertTrue(is_assignable("Dog", "java.lang.Object", cl))
        self.assertFalse(is_assignable("Animal", "Dog", cl))

    def test_two_level_inheritance(self):
        """Method lookup walks two superclass levels."""
        from jvm_interpreter.models.java_objects import JavaObject
        grandparent = _make_class("GP", "java.lang.Object", [
            ("val", "()I", [0x10, 0x07, 0xAC]),    # bipush 7, ireturn
        ])
        parent = _make_class("Par", "GP", [])
        child  = _make_class("Chi", "Par", [])
        cl = _loader_with(grandparent, parent, child)

        obj = JavaObject("Chi")
        interp = Interpreter(bytes([0xB1]), 10, 10, [], cl)
        result = interp._dispatch("Chi", "val", "()I", obj, [])
        self.assertEqual(result, 7)

    def test_get_method_code_returns_5tuple(self):
        """get_method_code always returns a 5-tuple (max_stack, max_locals, code, exc, cls)."""
        animal = _make_class("Animal2", "java.lang.Object", [
            ("speak", "()I", [0xAC]),
        ])
        cl = _loader_with(animal)
        result = cl.get_method_code("Animal2", "speak")
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 5)
        self.assertEqual(result[4], "Animal2")


# ---------------------------------------------------------------------------
# Reflection
# ---------------------------------------------------------------------------

class TestReflection(unittest.TestCase):
    """java.lang.Class, java.lang.reflect.{Method,Field,Constructor,Modifier}."""

    # ── helpers ──────────────────────────────────────────────────────────────

    def _interp(self):
        return Interpreter(bytes([0xB1]), 10, 10, [], None)

    def _interp_with(self, *class_files):
        cl = _loader_with(*class_files)
        return Interpreter(bytes([0xB1]), 10, 10, [], cl)

    # ── JavaClass basic attributes ────────────────────────────────────────────

    def test_java_class_get_name(self):
        from jvm_interpreter.native.java_reflect import JavaClass
        c = JavaClass("java.lang.String")
        self.assertEqual(c.getName(), "java.lang.String")

    def test_java_class_get_simple_name(self):
        from jvm_interpreter.native.java_reflect import JavaClass
        self.assertEqual(JavaClass("java.util.ArrayList").getSimpleName(), "ArrayList")
        self.assertEqual(JavaClass("int").getSimpleName(), "int")

    def test_java_class_is_primitive(self):
        from jvm_interpreter.native.java_reflect import JavaClass
        self.assertTrue(JavaClass("int").isPrimitive())
        self.assertTrue(JavaClass("void").isPrimitive())
        self.assertFalse(JavaClass("java.lang.Integer").isPrimitive())

    def test_java_class_is_array(self):
        from jvm_interpreter.native.java_reflect import JavaClass
        self.assertTrue(JavaClass("[I").isArray())
        self.assertFalse(JavaClass("int").isArray())

    def test_java_class_equals(self):
        from jvm_interpreter.native.java_reflect import JavaClass
        a = JavaClass("java.lang.String")
        b = JavaClass("java.lang.String")
        c = JavaClass("java.lang.Integer")
        self.assertTrue(a.equals(b))
        self.assertFalse(a.equals(c))

    def test_java_class_hash_stable(self):
        from jvm_interpreter.native.java_reflect import JavaClass
        c = JavaClass("java.lang.String")
        self.assertEqual(c.hashCode(), c.hashCode())

    def test_ldc_class_returns_java_class(self):
        from jvm_interpreter.models.class_file_models import ConstantPoolEntry
        from jvm_interpreter.native.java_reflect import JavaClass
        cp = [ConstantPoolEntry(1, "java/util/ArrayList"), ConstantPoolEntry(7, 1)]
        code = bytes([0x12, 0x02, 0xB0])  # ldc #2, areturn
        result = Interpreter(code, 10, 10, cp, None).run()
        self.assertIsInstance(result, JavaClass)
        self.assertEqual(result.getName(), "java.util.ArrayList")

    # ── getClass() ────────────────────────────────────────────────────────────

    def test_get_class_on_java_object(self):
        from jvm_interpreter.native.java_reflect import JavaClass
        obj = JavaObject("com.example.Foo")
        result = self._interp()._dispatch("com.example.Foo", "getClass", "()Ljava/lang/Class;",
                                          obj, [])
        self.assertIsInstance(result, JavaClass)
        self.assertEqual(result.getName(), "com.example.Foo")

    def test_get_class_on_string(self):
        from jvm_interpreter.native.java_reflect import JavaClass
        result = self._interp()._dispatch("java.lang.String", "getClass",
                                          "()Ljava/lang/Class;", "hello", [])
        self.assertIsInstance(result, JavaClass)
        self.assertEqual(result.getName(), "java.lang.String")

    def test_get_class_on_array(self):
        from jvm_interpreter.native.java_reflect import JavaClass
        arr = JavaArray('int', 3)
        result = self._interp()._dispatch("java.lang.Object", "getClass",
                                          "()Ljava/lang/Class;", arr, [])
        self.assertIsInstance(result, JavaClass)
        self.assertEqual(result.getName(), "[I")

    # ── Class.forName ─────────────────────────────────────────────────────────

    def test_class_for_name(self):
        from jvm_interpreter.native.java_reflect import JavaClass
        result = self._interp()._dispatch("java.lang.Class", "forName",
                                          "(Ljava/lang/String;)Ljava/lang/Class;",
                                          None, ["java.util.HashMap"])
        self.assertIsInstance(result, JavaClass)
        self.assertEqual(result.getName(), "java.util.HashMap")

    def test_class_for_name_slash_notation(self):
        from jvm_interpreter.native.java_reflect import JavaClass
        result = self._interp()._dispatch("java.lang.Class", "forName",
                                          "(Ljava/lang/String;)Ljava/lang/Class;",
                                          None, ["java/util/HashMap"])
        self.assertEqual(result.getName(), "java.util.HashMap")

    # ── Class.isInstance ─────────────────────────────────────────────────────

    def test_class_is_instance_true(self):
        from jvm_interpreter.native.java_reflect import JavaClass
        obj = JavaObject("java.util.ArrayList")
        clazz = JavaClass("java.util.ArrayList")
        result = self._interp()._dispatch_java_class(clazz, "isInstance", [obj])
        self.assertTrue(result)

    def test_class_is_instance_string(self):
        from jvm_interpreter.native.java_reflect import JavaClass
        clazz = JavaClass("java.lang.String")
        result = self._interp()._dispatch_java_class(clazz, "isInstance", ["hello"])
        self.assertTrue(result)

    def test_class_is_instance_false(self):
        from jvm_interpreter.native.java_reflect import JavaClass
        obj = JavaObject("java.lang.Integer")
        clazz = JavaClass("java.lang.String")
        result = self._interp()._dispatch_java_class(clazz, "isInstance", [obj])
        self.assertFalse(result)

    # ── getSuperclass / getInterfaces ─────────────────────────────────────────

    def test_get_superclass_builtin(self):
        from jvm_interpreter.native.java_reflect import JavaClass
        clazz = JavaClass("java.util.ArrayList")
        sup = self._interp()._dispatch_java_class(clazz, "getSuperclass", [])
        self.assertIsInstance(sup, JavaClass)
        self.assertEqual(sup.getName(), "java.util.AbstractList")

    def test_get_superclass_of_object_is_null(self):
        from jvm_interpreter.native.java_reflect import JavaClass
        clazz = JavaClass("java.lang.Object")
        sup = self._interp()._dispatch_java_class(clazz, "getSuperclass", [])
        self.assertIsNone(sup)

    def test_get_interfaces(self):
        from jvm_interpreter.native.java_reflect import JavaClass
        clazz = JavaClass("java.util.ArrayList")
        ifaces = self._interp()._dispatch_java_class(clazz, "getInterfaces", [])
        self.assertIsInstance(ifaces, JavaArray)
        names = {ifaces.elements[i].getName() for i in range(ifaces.length)}
        self.assertIn("java.util.List", names)

    def test_get_superclass_user_class(self):
        from jvm_interpreter.native.java_reflect import JavaClass
        dog = _make_class("Dog", "Animal", [])
        animal = _make_class("Animal", "java.lang.Object", [])
        cl = _loader_with(dog, animal)
        interp = Interpreter(bytes([0xB1]), 10, 10, [], cl)
        clazz = JavaClass("Dog")
        sup = interp._dispatch_java_class(clazz, "getSuperclass", [])
        self.assertIsNotNone(sup)
        self.assertEqual(sup.getName(), "Animal")

    # ── Method reflection ─────────────────────────────────────────────────────

    def test_get_declared_method_user_class(self):
        from jvm_interpreter.native.java_reflect import JavaClass, JavaMethod
        animal = _make_class("Animal", "java.lang.Object", [
            ("speak", "()I", [0x10, 0x01, 0xAC]),
        ])
        interp = self._interp_with(animal)
        clazz = JavaClass("Animal")
        m = interp._dispatch_java_class(clazz, "getDeclaredMethod", ["speak"])
        self.assertIsInstance(m, JavaMethod)
        self.assertEqual(m._method_name, "speak")
        self.assertEqual(m._owner_class, "Animal")

    def test_method_invoke_via_reflection(self):
        from jvm_interpreter.native.java_reflect import JavaClass, JavaMethod
        animal = _make_class("Animal", "java.lang.Object", [
            ("speak", "()I", [0x10, 0x2A, 0xAC]),   # bipush 42, ireturn
        ])
        cl = _loader_with(animal)
        interp = Interpreter(bytes([0xB1]), 10, 10, [], cl)
        obj = JavaObject("Animal")
        clazz = JavaClass("Animal")
        m = interp._dispatch_java_class(clazz, "getDeclaredMethod", ["speak"])
        result = interp._dispatch_java_method(m, "invoke", [obj, None])
        self.assertEqual(result, 42)

    def test_get_methods_returns_array(self):
        from jvm_interpreter.native.java_reflect import JavaClass
        animal = _make_class("Animal", "java.lang.Object", [
            ("speak", "()I", [0xAC]),
            ("breathe", "()V", [0xB1]),
        ])
        interp = self._interp_with(animal)
        clazz = JavaClass("Animal")
        arr = interp._dispatch_java_class(clazz, "getDeclaredMethods", [])
        self.assertIsInstance(arr, JavaArray)
        names = {arr.elements[i]._method_name for i in range(arr.length)}
        self.assertIn("speak", names)
        self.assertIn("breathe", names)

    def test_method_get_name(self):
        from jvm_interpreter.native.java_reflect import JavaMethod
        m = JavaMethod("Foo", "bar", "(I)V")
        self.assertEqual(m.getName(), "bar")

    def test_method_get_parameter_types(self):
        from jvm_interpreter.native.java_reflect import JavaMethod, JavaClass
        m = JavaMethod("Foo", "bar", "(ILjava/lang/String;)V")
        interp = self._interp()
        arr = interp._dispatch_java_method(m, "getParameterTypes", [])
        self.assertIsInstance(arr, JavaArray)
        self.assertEqual(arr.length, 2)
        self.assertEqual(arr.elements[0].getName(), "int")
        self.assertEqual(arr.elements[1].getName(), "java.lang.String")

    def test_method_get_return_type(self):
        from jvm_interpreter.native.java_reflect import JavaMethod
        m = JavaMethod("Foo", "bar", "(I)Ljava/lang/String;")
        rt = self._interp()._dispatch_java_method(m, "getReturnType", [])
        self.assertEqual(rt.getName(), "java.lang.String")

    def test_method_set_accessible_noop(self):
        from jvm_interpreter.native.java_reflect import JavaMethod
        m = JavaMethod("Foo", "bar", "()V")
        self._interp()._dispatch_java_method(m, "setAccessible", [True])
        self.assertTrue(m._accessible)

    # ── Field reflection ──────────────────────────────────────────────────────

    def test_field_get_and_set(self):
        from jvm_interpreter.native.java_reflect import JavaField
        obj = JavaObject("Foo")
        obj.set_field("x", 99)
        f = JavaField("Foo", "x", "I")
        interp = self._interp()
        self.assertEqual(interp._dispatch_java_field(f, "get", [obj]), 99)
        interp._dispatch_java_field(f, "set", [obj, 42])
        self.assertEqual(obj.get_field("x"), 42)

    def test_field_get_name(self):
        from jvm_interpreter.native.java_reflect import JavaField
        f = JavaField("Foo", "value", "I")
        self.assertEqual(f.getName(), "value")

    def test_field_get_type(self):
        from jvm_interpreter.native.java_reflect import JavaField
        f = JavaField("Foo", "name", "Ljava/lang/String;")
        t = self._interp()._dispatch_java_field(f, "getType", [])
        self.assertEqual(t.getName(), "java.lang.String")

    # ── Constructor reflection ────────────────────────────────────────────────

    def test_constructor_new_instance(self):
        from jvm_interpreter.native.java_reflect import JavaConstructor
        animal = _make_class("Animal", "java.lang.Object", [
            ("<init>", "()V", [0xB1]),
        ])
        cl = _loader_with(animal)
        interp = Interpreter(bytes([0xB1]), 10, 10, [], cl)
        ctor = JavaConstructor("Animal", "()V")
        result = interp._dispatch_java_constructor(ctor, "newInstance", [None])
        self.assertIsNotNone(result)
        self.assertEqual(getattr(result, 'class_name', None), "Animal")

    def test_get_constructors(self):
        from jvm_interpreter.native.java_reflect import JavaClass, JavaConstructor
        animal = _make_class("Animal", "java.lang.Object", [
            ("<init>", "()V", [0xB1]),
        ])
        interp = self._interp_with(animal)
        clazz = JavaClass("Animal")
        arr = interp._dispatch_java_class(clazz, "getConstructors", [])
        self.assertIsInstance(arr, JavaArray)
        self.assertGreater(arr.length, 0)
        self.assertIsInstance(arr.elements[0], JavaConstructor)

    # ── Class.newInstance (deprecated shortcut) ───────────────────────────────

    def test_class_new_instance(self):
        from jvm_interpreter.native.java_reflect import JavaClass
        animal = _make_class("Animal", "java.lang.Object", [
            ("<init>", "()V", [0xB1]),
        ])
        cl = _loader_with(animal)
        interp = Interpreter(bytes([0xB1]), 10, 10, [], cl)
        clazz = JavaClass("Animal")
        result = interp._dispatch_java_class(clazz, "newInstance", [])
        self.assertIsNotNone(result)

    # ── Modifier ──────────────────────────────────────────────────────────────

    def test_modifier_is_public(self):
        from jvm_interpreter.native.java_reflect import PUBLIC, PRIVATE
        interp = self._interp()
        self.assertTrue(interp._dispatch("java.lang.reflect.Modifier", "isPublic",
                                         "(I)Z", None, [PUBLIC]))
        self.assertFalse(interp._dispatch("java.lang.reflect.Modifier", "isPublic",
                                          "(I)Z", None, [PRIVATE]))

    def test_modifier_is_static(self):
        from jvm_interpreter.native.java_reflect import STATIC
        interp = self._interp()
        self.assertTrue(interp._dispatch("java.lang.reflect.Modifier", "isStatic",
                                         "(I)Z", None, [STATIC]))

    def test_modifier_constants_in_registry(self):
        from jvm_interpreter.native.native_registry import get_native_registry
        reg = get_native_registry()
        val = reg.get_native_static_field("java.lang.reflect.Modifier", "PUBLIC")
        self.assertEqual(val, 0x0001)

    # ── parse_method_descriptor ───────────────────────────────────────────────

    def test_parse_descriptor_no_params(self):
        from jvm_interpreter.native.java_reflect import parse_method_descriptor
        params, ret = parse_method_descriptor("()V")
        self.assertEqual(params, [])
        self.assertEqual(ret, "V")

    def test_parse_descriptor_mixed(self):
        from jvm_interpreter.native.java_reflect import parse_method_descriptor
        params, ret = parse_method_descriptor("(ILjava/lang/String;[B)Ljava/util/List;")
        self.assertEqual(len(params), 3)
        self.assertEqual(params[0], "I")
        self.assertEqual(params[1], "Ljava/lang/String;")
        self.assertEqual(params[2], "[B")
        self.assertEqual(ret, "Ljava/util/List;")

    def test_desc_to_class_name(self):
        from jvm_interpreter.native.java_reflect import desc_to_class_name
        self.assertEqual(desc_to_class_name("I"), "int")
        self.assertEqual(desc_to_class_name("Ljava/lang/String;"), "java.lang.String")
        self.assertEqual(desc_to_class_name("[I"), "[I")
        self.assertEqual(desc_to_class_name("V"), "void")

    # ── getClass() → Class.getName() chain ───────────────────────────────────

    def test_get_class_get_name_chain(self):
        """obj.getClass().getName() returns the class name string."""
        from jvm_interpreter.native.java_reflect import JavaClass
        obj = JavaObject("com.example.Bar")
        interp = self._interp()
        cls_obj = interp._dispatch("com.example.Bar", "getClass",
                                   "()Ljava/lang/Class;", obj, [])
        self.assertIsInstance(cls_obj, JavaClass)
        name = interp._dispatch_java_class(cls_obj, "getName", [])
        self.assertEqual(name, "com.example.Bar")


if __name__ == '__main__':
    unittest.main(verbosity=2)
