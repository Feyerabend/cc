import struct
from typing import List, Any
from jvm_interpreter.constants.jvm_constants import ACCESS_FLAGS, OPCODES
from jvm_interpreter.models.class_file_models import ConstantPoolEntry, ClassFile


def decode_flags(flags: int, context: str) -> List[str]:
    names = []
    for mask, name in ACCESS_FLAGS[context].items():
        if flags & mask:
            names.append(name)
    return names or ["<none>"]

def format_constant(cp: List[ConstantPoolEntry], value: Any) -> str:
    if isinstance(value, int):
        entry = cp[value - 1]
        if entry.tag == 1:
            return f'"{entry.value}"'
        if entry.tag == 7:
            return f"Class #{value} -> {format_constant(cp, entry.value)}"
        if entry.tag == 8:
            return f"String #{value} -> {format_constant(cp, entry.value)}"
        return str(entry.value)
    elif isinstance(value, tuple):
        parts = [format_constant(cp, idx) for idx in value]
        return f"({', '.join(parts)})"
    return str(value)

def disassemble_code(code: bytes, cp: List[ConstantPoolEntry]) -> str:
    lines = []
    pc = 0
    code_bytes = list(code)
    while pc < len(code_bytes):
        opcode = code_bytes[pc]
        if opcode not in OPCODES:
            lines.append(f"{pc:4d}: <unknown opcode {opcode}>")
            pc += 1
            continue
        opname, oplen = OPCODES[opcode]
        if oplen == -1:
            lines.append(f"{pc:4d}: {opname} <complex instruction>")
            pc += 1
            continue
        args = code_bytes[pc + 1:pc + oplen]
        arg_str = ""
        if args:
            if opcode in (18, 19, 178, 179, 180, 181, 182, 183, 184, 185, 187): #187, 189, 192, 193):
                index = (args[0] << 8) | args[1] if len(args) > 1 else args[0]
                arg_str = f" #{index} -> {format_constant(cp, index)}"
            elif opcode in (153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 167):
                offset = struct.unpack('!h', bytes(args))[0]
                arg_str = f" {offset} -> pc={pc + offset}"
            else:
                arg_str = " " + " ".join(f"{b:02x}" for b in args)
        lines.append(f"{pc:4d}: {opname}{arg_str}")
        pc += oplen
    return "\n".join(lines)

def print_class_info(cf: ClassFile):
    try:
        from jvm_interpreter.models.class_file_models import CodeAttribute, AttributeInfo
        print("Imported CodeAttribute in print_class_info:", CodeAttribute)
        print("Imported AttributeInfo in print_class_info:", AttributeInfo)
    except ImportError as e:
        print(f"Failed to import CodeAttribute or AttributeInfo: {e}")
        raise
    
    local_code_attribute = CodeAttribute
    print("Assigned local_code_attribute:", local_code_attribute)

    print("Class File Info:")
    print(f"  Header: {cf.header}")
    print(f"  Access: {cf.access} {decode_flags(cf.access.value, 'class')}")
    print(f"  This: {cf.this_class}")
    print(f"  Super: {cf.super_class}")
    print("\nConstant Pool:")
    for i, entry in enumerate(cf.constant_pool, 1):
        print(f"  #{i:3} {entry}")
        if entry.tag in (7, 8, 9, 10, 11, 12, 15, 18):
            print(f"      -> {format_constant(cf.constant_pool, entry.value)}")
    if cf.interfaces:
        print("\nInterfaces:")
        for i in cf.interfaces:
            print(f"  - {i}")
    if cf.fields:
        print("\nFields:")
        for f in cf.fields:
            print(f"  {f}")
            print(f"    Flags: {decode_flags(f.access.value, 'field')}")
#    if cf.methods:
#        print("\nMethods:")
#        for m in cf.methods:
#            print(f"  {m}")
#            print(f"    Flags: {decode_flags(m.access.value, 'method')}")
#            try:
#                for a in m.attributes:
#                    try:
#                       print(f"    Inspecting attribute object: {a}")
#                        print(f"    Has name attribute: {hasattr(a, 'name')}")
#                        name = getattr(a, 'name', '<no name>')
#                        print(f"    Attribute name: {name}")
#                    except Exception as e:
#                        print(f"Error accessing attribute name: {str(e)}")
#                        raise
#                    print(f"    Processing attribute: {name}")
#                    print(f"    Namespace check: local_code_attribute={local_code_attribute}")
#                    print(f"    Attribute type: {type(a)}")
#                    try: # Need this try?
#                        is_code_attribute = (type(a) is local_code_attribute)
#                        print(f"    Is CodeAttribute: {is_code_attribute}")
#                        if is_code_attribute:
#                            print(f"    {a}")
#                            print("    Disassembled Code:")
#                            print(disassemble_code(a.code, cf.constant_pool))
#                        else:
#                            print(f"    {a}")
#                    except Exception as e:
#                        print(f"Inner error processing attribute {name}: {str(e)}")
#                        raise
#            except Exception as e:
#                print(f"Outer error processing method {m.name}: {str(e)}")
#                raise

    if cf.methods:
        print("\nMethods:")
        for m in cf.methods:
            print(f"  {m}")
            print(f"    Flags: {decode_flags(m.access.value, 'method')}")
            for a in m.attributes:
                if isinstance(a, CodeAttribute):
                    print(f"    {a}")
                    print("    Disassembled Code:")
                    print(disassemble_code(a.code, cf.constant_pool))
                else:
                    print(f"    {a}")

#    if cf.attributes:
#        print("\nAttributes:")
#        for a in cf.attributes:
#            print(f"  {a}")
#            if hasattr(a, 'name'):
#                print(f"    Name: {a.name}")
#            else:
#                print("    <no name attribute>")
#            if hasattr(a, 'value'):
#                print(f"    Value: {a.value}")
#            else:
#                print("    <no value attribute>")

    if cf.attributes:
        print("\nAttributes:")
        for a in cf.attributes:
            print(f"  {a}")
            if hasattr(a, 'name'):
                print(f"    Name: {a.name}")
            else:
                print("    <no name attribute>")
            if a.name == 'SourceFile' and len(a.data) == 2:
                import struct
                index = struct.unpack('!H', a.data)[0]
                source = cf.constant_pool[index - 1].value
                print(f"    Source file: {source}")
            elif hasattr(a, 'data'):
                print(f"    Data: {a.data}")
            else:
                print("    <no data attribute>")
    print("\nEnd of Class File Info")

