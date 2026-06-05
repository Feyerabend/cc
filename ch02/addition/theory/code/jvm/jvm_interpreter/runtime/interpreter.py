import struct
from typing import List, Dict, Any, Optional
from jvm_interpreter.native.native_registry import get_native_registry, NativeObject
from jvm_interpreter.models.java_objects import JavaObject, JavaArray, ObjectFactory
from jvm_interpreter.models.class_file_models import ConstantPoolEntry, CodeAttribute


class Interpreter:
    """JVM bytecode interpreter with native method support"""
    
    def __init__(self, code: bytes, max_stack: int, max_locals: int, 
                 constant_pool: List[ConstantPoolEntry], class_loader: Any):
        """Initialize interpreter"""
        self.code = list(code)
        self.max_stack = max_stack
        self.max_locals = max_locals
        self.constant_pool = constant_pool
        self.class_loader = class_loader
        
        # Runtime state
        self.pc = 0
        self.stack: List[Any] = []
        self.locals: List[Any] = [None] * max_locals
        
        # Native registry
        self.native_registry = get_native_registry()
        
        # Object factory for creating instances
        self.object_factory = ObjectFactory(self.native_registry)
        
        # Instruction dispatch table
        self.instructions = {
            1: self.instr_aconst_null,
            2: self.instr_iconst,
            3: self.instr_iconst,
            4: self.instr_iconst,
            5: self.instr_iconst,
            6: self.instr_iconst,
            7: self.instr_iconst,
            8: self.instr_iconst,
            9: self.instr_lconst,
            10: self.instr_lconst,
            11: self.instr_fconst,
            12: self.instr_fconst,
            13: self.instr_fconst,
            14: self.instr_dconst,
            15: self.instr_dconst,
            16: self.instr_bipush,
            17: self.instr_sipush,
            18: self.instr_ldc,
            19: self.instr_ldc_w,
            21: self.instr_iload,
            22: self.instr_lload,
            23: self.instr_fload,
            24: self.instr_dload,
            25: self.instr_aload,
            26: self.instr_iload_n,
            27: self.instr_iload_n,
            28: self.instr_iload_n,
            29: self.instr_iload_n,
            30: self.instr_lload_n,
            31: self.instr_lload_n,
            32: self.instr_lload_n,
            33: self.instr_lload_n,
            34: self.instr_fload_n,
            35: self.instr_fload_n,
            36: self.instr_fload_n,
            37: self.instr_fload_n,
            38: self.instr_dload_n,
            39: self.instr_dload_n,
            40: self.instr_dload_n,
            41: self.instr_dload_n,
            42: self.instr_aload_n,
            43: self.instr_aload_n,
            44: self.instr_aload_n,
            45: self.instr_aload_n,
            54: self.instr_istore,
            55: self.instr_lstore,
            56: self.instr_fstore,
            57: self.instr_dstore,
            58: self.instr_astore,
            59: self.instr_istore_n,
            60: self.instr_istore_n,
            61: self.instr_istore_n,
            62: self.instr_istore_n,
            63: self.instr_lstore_n,
            64: self.instr_lstore_n,
            65: self.instr_lstore_n,
            66: self.instr_lstore_n,
            67: self.instr_fstore_n,
            68: self.instr_fstore_n,
            69: self.instr_fstore_n,
            70: self.instr_fstore_n,
            71: self.instr_dstore_n,
            72: self.instr_dstore_n,
            73: self.instr_dstore_n,
            74: self.instr_dstore_n,
            75: self.instr_astore_n,
            76: self.instr_astore_n,
            77: self.instr_astore_n,
            78: self.instr_astore_n,
            87: self.instr_pop,
            88: self.instr_pop2,
            89: self.instr_dup,
            96: self.instr_iadd,
            100: self.instr_isub,
            104: self.instr_imul,
            108: self.instr_idiv,
            112: self.instr_irem,
            153: self.instr_ifeq,
            154: self.instr_ifne,
            155: self.instr_iflt,
            156: self.instr_ifge,
            157: self.instr_ifgt,
            158: self.instr_ifle,
            159: self.instr_if_icmpeq,
            160: self.instr_if_icmpne,
            161: self.instr_if_icmplt,
            162: self.instr_if_icmpge,
            163: self.instr_if_icmpgt,
            164: self.instr_if_icmple,
            167: self.instr_goto,
            172: self.instr_ireturn,
            176: self.instr_areturn,
            177: self.instr_return,
            178: self.instr_getstatic,
            179: self.instr_putstatic,
            180: self.instr_getfield,
            181: self.instr_putfield,
            182: self.instr_invokevirtual,
            183: self.instr_invokespecial,
            184: self.instr_invokestatic,
            185: self.instr_invokeinterface,
            187: self.instr_new,
        }
    
    def advance(self, n: int = 1) -> int:
        """Read n bytes from bytecode and advance PC"""
        value = 0
        for _ in range(n):
            value = (value << 8) | self.code[self.pc]
            self.pc += 1
        return value
    
    # ========== Stack/Load/Store Instructions ==========
    
    def instr_aconst_null(self):
        self.stack.append(None)
    
    def instr_iconst(self):
        opcode = self.code[self.pc - 1]
        self.stack.append(opcode - 3)
    
    def instr_lconst(self):
        opcode = self.code[self.pc - 1]
        self.stack.append(opcode - 9)
    
    def instr_fconst(self):
        opcode = self.code[self.pc - 1]
        self.stack.append(float(opcode - 11))
    
    def instr_dconst(self):
        opcode = self.code[self.pc - 1]
        self.stack.append(float(opcode - 14))
    
    def instr_bipush(self):
        value = struct.unpack('!b', bytes([self.advance()]))[0]
        self.stack.append(value)
    
    def instr_sipush(self):
        value = struct.unpack('!h', bytes([self.advance(), self.advance()]))[0]
        self.stack.append(value)
    
    def instr_ldc(self):
        index = self.advance()
        entry = self.constant_pool[index - 1]
        if entry.tag == 8:  # String
            string = self.constant_pool[entry.value - 1].value
            self.stack.append(string)
        elif entry.tag in (3, 4):  # Integer, Float
            self.stack.append(entry.value)
        else:
            raise ValueError(f"Unsupported ldc type: {entry.tag}")
    
    def instr_ldc_w(self):
        index = self.advance(2)
        entry = self.constant_pool[index - 1]
        if entry.tag == 8:  # String
            string = self.constant_pool[entry.value - 1].value
            self.stack.append(string)
        elif entry.tag in (3, 4):  # Integer, Float
            self.stack.append(entry.value)
        else:
            raise ValueError(f"Unsupported ldc_w type: {entry.tag}")
    
    def instr_iload(self):
        index = self.advance()
        self.stack.append(self.locals[index])
    
    def instr_lload(self):
        index = self.advance()
        self.stack.append(self.locals[index])
    
    def instr_fload(self):
        index = self.advance()
        self.stack.append(self.locals[index])
    
    def instr_dload(self):
        index = self.advance()
        self.stack.append(self.locals[index])
    
    def instr_aload(self):
        index = self.advance()
        self.stack.append(self.locals[index])
    
    def instr_iload_n(self):
        opcode = self.code[self.pc - 1]
        index = opcode - 26
        self.stack.append(self.locals[index])
    
    def instr_lload_n(self):
        opcode = self.code[self.pc - 1]
        index = opcode - 30
        self.stack.append(self.locals[index])
    
    def instr_fload_n(self):
        opcode = self.code[self.pc - 1]
        index = opcode - 34
        self.stack.append(self.locals[index])
    
    def instr_dload_n(self):
        opcode = self.code[self.pc - 1]
        index = opcode - 38
        self.stack.append(self.locals[index])
    
    def instr_aload_n(self):
        opcode = self.code[self.pc - 1]
        index = opcode - 42
        self.stack.append(self.locals[index])
    
    def instr_istore(self):
        index = self.advance()
        self.locals[index] = self.stack.pop()
    
    def instr_lstore(self):
        index = self.advance()
        self.locals[index] = self.stack.pop()
    
    def instr_fstore(self):
        index = self.advance()
        self.locals[index] = self.stack.pop()
    
    def instr_dstore(self):
        index = self.advance()
        self.locals[index] = self.stack.pop()
    
    def instr_astore(self):
        index = self.advance()
        self.locals[index] = self.stack.pop()
    
    def instr_istore_n(self):
        opcode = self.code[self.pc - 1]
        index = opcode - 59
        self.locals[index] = self.stack.pop()
    
    def instr_lstore_n(self):
        opcode = self.code[self.pc - 1]
        index = opcode - 63
        self.locals[index] = self.stack.pop()
    
    def instr_fstore_n(self):
        opcode = self.code[self.pc - 1]
        index = opcode - 67
        self.locals[index] = self.stack.pop()
    
    def instr_dstore_n(self):
        opcode = self.code[self.pc - 1]
        index = opcode - 71
        self.locals[index] = self.stack.pop()
    
    def instr_astore_n(self):
        opcode = self.code[self.pc - 1]
        index = opcode - 75
        self.locals[index] = self.stack.pop()
    
    def instr_pop(self):
        self.stack.pop()
    
    def instr_pop2(self):
        self.stack.pop()
        self.stack.pop()
    
    def instr_dup(self):
        value = self.stack[-1]
        self.stack.append(value)
    
    # ========== Arithmetic Instructions ==========
    
    def instr_iadd(self):
        v2 = self.stack.pop()
        v1 = self.stack.pop()
        self.stack.append(v1 + v2)
    
    def instr_isub(self):
        v2 = self.stack.pop()
        v1 = self.stack.pop()
        self.stack.append(v1 - v2)
    
    def instr_imul(self):
        v2 = self.stack.pop()
        v1 = self.stack.pop()
        self.stack.append(v1 * v2)
    
    def instr_idiv(self):
        v2 = self.stack.pop()
        v1 = self.stack.pop()
        self.stack.append(v1 // v2)
    
    def instr_irem(self):
        v2 = self.stack.pop()
        v1 = self.stack.pop()
        self.stack.append(v1 % v2)
    
    # ========== Control Flow Instructions ==========
    
    def instr_ifeq(self):
        offset = struct.unpack('!h', bytes([self.advance(), self.advance()]))[0]
        value = self.stack.pop()
        if value == 0:
            self.pc = self.pc - 3 + offset
    
    def instr_ifne(self):
        offset = struct.unpack('!h', bytes([self.advance(), self.advance()]))[0]
        value = self.stack.pop()
        if value != 0:
            self.pc = self.pc - 3 + offset
    
    def instr_iflt(self):
        offset = struct.unpack('!h', bytes([self.advance(), self.advance()]))[0]
        value = self.stack.pop()
        if value < 0:
            self.pc = self.pc - 3 + offset
    
    def instr_ifge(self):
        offset = struct.unpack('!h', bytes([self.advance(), self.advance()]))[0]
        value = self.stack.pop()
        if value >= 0:
            self.pc = self.pc - 3 + offset
    
    def instr_ifgt(self):
        offset = struct.unpack('!h', bytes([self.advance(), self.advance()]))[0]
        value = self.stack.pop()
        if value > 0:
            self.pc = self.pc - 3 + offset
    
    def instr_ifle(self):
        offset = struct.unpack('!h', bytes([self.advance(), self.advance()]))[0]
        value = self.stack.pop()
        if value <= 0:
            self.pc = self.pc - 3 + offset
    
    def instr_if_icmpeq(self):
        offset = struct.unpack('!h', bytes([self.advance(), self.advance()]))[0]
        v2 = self.stack.pop()
        v1 = self.stack.pop()
        if v1 == v2:
            self.pc = self.pc - 3 + offset
    
    def instr_if_icmpne(self):
        offset = struct.unpack('!h', bytes([self.advance(), self.advance()]))[0]
        v2 = self.stack.pop()
        v1 = self.stack.pop()
        if v1 != v2:
            self.pc = self.pc - 3 + offset
    
    def instr_if_icmplt(self):
        offset = struct.unpack('!h', bytes([self.advance(), self.advance()]))[0]
        v2 = self.stack.pop()
        v1 = self.stack.pop()
        if v1 < v2:
            self.pc = self.pc - 3 + offset
    
    def instr_if_icmpge(self):
        offset = struct.unpack('!h', bytes([self.advance(), self.advance()]))[0]
        v2 = self.stack.pop()
        v1 = self.stack.pop()
        if v1 >= v2:
            self.pc = self.pc - 3 + offset
    
    def instr_if_icmpgt(self):
        offset = struct.unpack('!h', bytes([self.advance(), self.advance()]))[0]
        v2 = self.stack.pop()
        v1 = self.stack.pop()
        if v1 > v2:
            self.pc = self.pc - 3 + offset
    
    def instr_if_icmple(self):
        offset = struct.unpack('!h', bytes([self.advance(), self.advance()]))[0]
        v2 = self.stack.pop()
        v1 = self.stack.pop()
        if v1 <= v2:
            self.pc = self.pc - 3 + offset
    
    def instr_goto(self):
        offset = struct.unpack('!h', bytes([self.advance(), self.advance()]))[0]
        self.pc = self.pc - 3 + offset
    
    # ========== Return Instructions ==========
    
    def instr_ireturn(self):
        return self.stack.pop()
    
    def instr_areturn(self):
        return self.stack.pop()
    
    def instr_return(self):
        return None
    
    # ========== Field Instructions ==========
    
    def instr_getstatic(self):
        """Get static field value - check native registry first!"""
        index = self.advance(2)
        class_name, field_name = self._resolve_field_ref(index)
        
        # CHECK NATIVE FIRST
        if self.native_registry.has_native_static_field(class_name, field_name):
            value = self.native_registry.get_native_static_field(class_name, field_name)
            self.stack.append(value)
        else:
            # Custom class static field
            value = self.class_loader.resolve_field(class_name, field_name)
            if value is None:
                raise ValueError(f"Static field not found: {class_name}.{field_name}")
            self.stack.append(value)
    
    def instr_putstatic(self):
        """Put static field value"""
        index = self.advance(2)
        class_name, field_name = self._resolve_field_ref(index)
        value = self.stack.pop()
        
        # Store in class loader (works for both native and custom)
        self.class_loader.set_field(class_name, field_name, value)
    
    def instr_getfield(self):
        """Get instance field value"""
        index = self.advance(2)
        class_name, field_name = self._resolve_field_ref(index)
        obj = self.stack.pop()
        
        if obj is None:
            raise ValueError("NullPointerException in getfield")
        
        # Use object's get_field method (works for both JavaObject and NativeObject)
        if hasattr(obj, 'get_field'):
            value = obj.get_field(field_name)
        else:
            # Fallback for simple Python objects (strings, etc.)
            value = getattr(obj, field_name, None)
        
        self.stack.append(value)
    
    def instr_putfield(self):
        """Put instance field value"""
        index = self.advance(2)
        class_name, field_name = self._resolve_field_ref(index)
        value = self.stack.pop()
        obj = self.stack.pop()
        
        if obj is None:
            raise ValueError("NullPointerException in putfield")
        
        # Use object's set_field method (works for both JavaObject and NativeObject)
        if hasattr(obj, 'set_field'):
            obj.set_field(field_name, value)
        else:
            # Fallback
            setattr(obj, field_name, value)
    
    # ========== Method Invocation Instructions ==========
    
    def instr_invokevirtual(self):
        """Invoke instance method - check native first!"""
        index = self.advance(2)
        class_name, method_name, descriptor = self._resolve_method_ref(index)
        
        # Parse arguments from descriptor
        arg_count = self._count_args(descriptor)
        args = [self.stack.pop() for _ in range(arg_count)]
        args.reverse()
        obj = self.stack.pop()
        
        if obj is None:
            raise ValueError("NullPointerException in invokevirtual")
        
        # Determine actual class (polymorphism)
        if isinstance(obj, (JavaObject, NativeObject)):
            actual_class = obj.class_name
        else:
            actual_class = class_name
        
        # CHECK NATIVE FIRST
        if self.native_registry.has_native_method(actual_class, method_name):
            result = self.native_registry.invoke_native_method(
                actual_class, method_name, obj, args
            )
            # Push result if non-void
            if not descriptor.endswith(')V'):
                self.stack.append(result)
        else:
            # Custom bytecode method
            result = self._invoke_bytecode_method(
                actual_class, method_name, descriptor, obj, args
            )
            if not descriptor.endswith(')V'):
                self.stack.append(result)
    
    def instr_invokespecial(self):
        """Invoke constructor or superclass method - check native first!"""
        index = self.advance(2)
        class_name, method_name, descriptor = self._resolve_method_ref(index)
        
        arg_count = self._count_args(descriptor)
        args = [self.stack.pop() for _ in range(arg_count)]
        args.reverse()
        obj = self.stack.pop()
        
        if obj is None:
            raise ValueError("NullPointerException in invokespecial")
        
        # CHECK NATIVE FIRST
        if self.native_registry.has_native_method(class_name, method_name):
            result = self.native_registry.invoke_native_method(
                class_name, method_name, obj, args
            )
            if not descriptor.endswith(')V'):
                self.stack.append(result)
        else:
            # Custom bytecode method (constructor or super call)
            result = self._invoke_bytecode_method(
                class_name, method_name, descriptor, obj, args
            )
            if not descriptor.endswith(')V'):
                self.stack.append(result)
    
    def instr_invokestatic(self):
        """Invoke static method - check native first!"""
        index = self.advance(2)
        class_name, method_name, descriptor = self._resolve_method_ref(index)
        
        arg_count = self._count_args(descriptor)
        args = [self.stack.pop() for _ in range(arg_count)]
        args.reverse()
        
        # CHECK NATIVE FIRST
        if self.native_registry.has_native_method(class_name, method_name):
            result = self.native_registry.invoke_native_method(
                class_name, method_name, None, args
            )
            if not descriptor.endswith(')V'):
                self.stack.append(result)
        else:
            # Custom bytecode static method
            result = self._invoke_bytecode_method(
                class_name, method_name, descriptor, None, args
            )
            if not descriptor.endswith(')V'):
                self.stack.append(result)
    
    def instr_invokeinterface(self):
        """Invoke interface method - check native first!"""
        index = self.advance(2)
        count = self.advance()
        zero = self.advance()
        if zero != 0:
            raise ValueError("Invalid invokeinterface format")
        
        class_name, method_name, descriptor = self._resolve_method_ref(index)
        
        arg_count = self._count_args(descriptor)
        args = [self.stack.pop() for _ in range(arg_count)]
        args.reverse()
        obj = self.stack.pop()
        
        if obj is None:
            raise ValueError("NullPointerException in invokeinterface")
        
        # Determine actual class
        if isinstance(obj, (JavaObject, NativeObject)):
            actual_class = obj.class_name
        else:
            actual_class = class_name
        
        # CHECK NATIVE FIRST
        if self.native_registry.has_native_method(actual_class, method_name):
            result = self.native_registry.invoke_native_method(
                actual_class, method_name, obj, args
            )
            if not descriptor.endswith(')V'):
                self.stack.append(result)
        else:
            # Custom bytecode method
            result = self._invoke_bytecode_method(
                actual_class, method_name, descriptor, obj, args
            )
            if not descriptor.endswith(')V'):
                self.stack.append(result)
    
    def instr_new(self):
        """Create new object instance - use object factory!"""
        index = self.advance(2)
        class_index = self.constant_pool[index - 1].value
        class_name = self.constant_pool[class_index - 1].value
        
        # Use object factory - it checks native registry first
        obj = self.object_factory.create_object(class_name)
        self.stack.append(obj)
    
    # ========== Helper Methods ==========
    
    def _resolve_field_ref(self, index: int) -> tuple:
        """Resolve field reference from constant pool"""
        field_ref = self.constant_pool[index - 1]
        class_index = field_ref.value[0]
        class_pointer = self.constant_pool[class_index - 1]
        class_name = self.constant_pool[class_pointer.value - 1].value.replace('/', '.')
        
        name_and_type_index = field_ref.value[1]
        name_and_type = self.constant_pool[name_and_type_index - 1].value
        name_index = name_and_type[0]
        field_name = self.constant_pool[name_index - 1].value
        
        return class_name, field_name
    
    def _resolve_method_ref(self, index: int) -> tuple:
        """Resolve method reference from constant pool"""
        method_ref = self.constant_pool[index - 1]
        class_index = method_ref.value[0]
        class_pointer = self.constant_pool[class_index - 1]
        class_name = self.constant_pool[class_pointer.value - 1].value.replace('/', '.')
        
        name_and_type = self.constant_pool[method_ref.value[1] - 1].value
        method_name = self.constant_pool[name_and_type[0] - 1].value
        descriptor = self.constant_pool[name_and_type[1] - 1].value
        
        return class_name, method_name, descriptor
    
    def _count_args(self, descriptor: str) -> int:
        """Count arguments from method descriptor"""
        if not descriptor.startswith('('):
            return 0
        param_part = descriptor[1:descriptor.index(')')]
        if not param_part:
            return 0
        # Count reference types (end with ;)
        return param_part.count(';')
    
    def _invoke_bytecode_method(self, class_name: str, method_name: str, 
                                descriptor: str, obj: Optional[Any], 
                                args: list) -> Any:
        """Invoke a method defined in bytecode (not native)"""
        # Load the class and get method code
        code = self.class_loader.get_method_code(class_name, method_name)
        
        if not code:
            # Method not found - could be inherited or abstract
            raise ValueError(f"Method not found: {class_name}.{method_name}{descriptor}")
        
        # Create sub-interpreter for method execution
        class_file = self.class_loader.load_class(class_name)
        sub_interpreter = Interpreter(
            code[2], code[0], code[1], 
            class_file.constant_pool, 
            self.class_loader
        )
        
        # Set up locals: for instance methods, locals[0] = this
        if obj is not None:
            sub_interpreter.locals[0] = obj
            sub_interpreter.locals[1:len(args)+1] = args
        else:
            # Static method
            sub_interpreter.locals[:len(args)] = args
        
        # Execute method
        return sub_interpreter.run()
    
    def run(self) -> Optional[Any]:
        """Execute bytecode until return"""
        while self.pc < len(self.code):
            opcode = self.advance()
            
            if opcode not in self.instructions:
                raise ValueError(f"Unsupported opcode: {opcode} at pc={self.pc-1}")
            
            result = self.instructions[opcode]()
            
            # Check for return instructions
            if opcode in (172, 176, 177):  # ireturn, areturn, return
                return result
        
        return None
