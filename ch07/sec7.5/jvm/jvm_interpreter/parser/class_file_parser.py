from email import header
import struct
import io
from typing import List
from jvm_interpreter.models.class_file_models import (
    Header, ConstantPoolEntry, AccessFlags, ClassReference,
    AttributeInfo, CodeAttribute, Member, ClassFile
)

def parse_header(f: io.BufferedReader) -> Header:
    magic = struct.unpack('!I', f.read(4))[0]
    minor, major = struct.unpack('!HH', f.read(4))
    return Header(magic, minor, major)

def parse_constant_pool(f: io.BufferedReader) -> List[ConstantPoolEntry]:
    constant_pool = []
    count = struct.unpack("!H", f.read(2))[0]
    i = 1
    while i < count:
        tag = struct.unpack("!B", f.read(1))[0]
        if tag == 1:  # UTF8
            length = struct.unpack("!H", f.read(2))[0]
            value = f.read(length).decode('utf-8')
            constant_pool.append(ConstantPoolEntry(tag, value))
        elif tag in (3, 4):  # Integer, Float
            value = struct.unpack("!i" if tag == 3 else "!f", f.read(4))[0]
            constant_pool.append(ConstantPoolEntry(tag, value))
        elif tag in (5, 6):  # Long, Double
            value = struct.unpack("!q" if tag == 5 else "!d", f.read(8))[0]
            constant_pool.append(ConstantPoolEntry(tag, value))
            i += 1
        elif tag in (7, 8, 16):  # Class, String, MethodType
            index = struct.unpack("!H", f.read(2))[0]
            constant_pool.append(ConstantPoolEntry(tag, index))
        elif tag in (9, 10, 11, 12):  # Fieldref, Methodref, InterfaceMethodref, NameAndType
            idx1, idx2 = struct.unpack("!HH", f.read(4))
            constant_pool.append(ConstantPoolEntry(tag, (idx1, idx2)))
        elif tag == 15:  # MethodHandle
            kind, index = struct.unpack("!BH", f.read(3))
            constant_pool.append(ConstantPoolEntry(tag, (kind, index)))
        elif tag == 18:  # InvokeDynamic
            bootstrap, name_type = struct.unpack("!HH", f.read(4))
            constant_pool.append(ConstantPoolEntry(tag, (bootstrap, name_type)))
        else:
            raise ValueError(f"Unsupported constant pool tag: {tag}")
        i += 1
    return constant_pool

def parse_access_flags(f: io.BufferedReader) -> AccessFlags:
    return AccessFlags(struct.unpack('!H', f.read(2))[0])

def parse_class_reference(f: io.BufferedReader, cp: List[ConstantPoolEntry], ref_type: str) -> ClassReference:
    index = struct.unpack('!H', f.read(2))[0]
    class_info = cp[index - 1]
    name_entry = cp[class_info.value - 1]
    return ClassReference(name_entry.value)

def parse_interfaces(f: io.BufferedReader, cp: List[ConstantPoolEntry]) -> List[ClassReference]:
    count = struct.unpack("!H", f.read(2))[0]
    return [parse_class_reference(f, cp, "interface") for _ in range(count)]

def parse_attribute(f: io.BufferedReader, cp: List[ConstantPoolEntry]) -> AttributeInfo:
    name_index = struct.unpack("!H", f.read(2))[0]
    length = struct.unpack("!I", f.read(4))[0]
    name = cp[name_index - 1].value
    if name == 'Code':
        max_stack = struct.unpack("!H", f.read(2))[0]
        max_locals = struct.unpack("!H", f.read(2))[0]
        code_length = struct.unpack("!I", f.read(4))[0]
        code = f.read(code_length)
        exceptions = [struct.unpack("!HHHH", f.read(8)) for _ in range(struct.unpack("!H", f.read(2))[0])]
        attributes = [parse_attribute(f, cp) for _ in range(struct.unpack("!H", f.read(2))[0])]
        return CodeAttribute(name, max_stack, max_locals, code, exceptions, attributes)
    return AttributeInfo(name, f.read(length))

def parse_members(f: io.BufferedReader, cp: List[ConstantPoolEntry], member_type: str) -> List[Member]:
    count = struct.unpack("!H", f.read(2))[0]
    members = []
    for _ in range(count):
        access = parse_access_flags(f)
        name_index = struct.unpack("!H", f.read(2))[0]
        desc_index = struct.unpack("!H", f.read(2))[0]
        name = cp[name_index - 1].value
        descriptor = cp[desc_index - 1].value
        attributes = [parse_attribute(f, cp) for _ in range(struct.unpack("!H", f.read(2))[0])]
        members.append(Member(access, name, descriptor, attributes))
    return members

def parse_class_file(filename: str) -> ClassFile:
    with open(filename, 'rb') as f:
        header = parse_header(f)
        cp = parse_constant_pool(f)
        access = parse_access_flags(f)
        this_class = parse_class_reference(f, cp, "this")
        super_class = parse_class_reference(f, cp, "super")
        interfaces = parse_interfaces(f, cp)
        fields = parse_members(f, cp, "field")
        methods = parse_members(f, cp, "method")
        #return ClassFile(header, cp, access, this_class, super_class, interfaces, fields, methods)
        attributes = [parse_attribute(f, cp) for _ in range(struct.unpack("!H", f.read(2))[0])]
        return ClassFile(header, cp, access, this_class, super_class, interfaces, fields, methods, attributes) # added attributes
    
