from typing import List, Tuple, Any

class Header:
    def __init__(self, magic: int, minor: int, major: int):
        self.magic = magic
        self.minor = minor
        self.major = major

    def __str__(self) -> str:
        return f"version: {self.major}.{self.minor} (magic: 0x{self.magic:08X})"

class ConstantPoolEntry:
    def __init__(self, tag: int, value: Any):
        self.tag = tag
        self.value = value

    def __str__(self) -> str:
        from jvm_interpreter.constants.jvm_constants import TAG_TEXT
        tag_name = TAG_TEXT.get(self.tag, 'UNKNOWN')
        return f"{tag_name:>15}:  {self.value}"

class AccessFlags:
    def __init__(self, value: int):
        self.value = value

    def __str__(self) -> str:
        return f"flags: 0x{self.value:04X}"

class ClassReference:
    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return f"class name: {self.name}"

class AttributeInfo:
    def __init__(self, name: str, data: bytes):
        self.name = name
        self.data = data

    def __str__(self) -> str:
        return f"Attribute: {self.name} ({len(self.data)} bytes)"

class CodeAttribute(AttributeInfo):
    def __init__(self, name: str, max_stack: int, max_locals: int, code: bytes, exceptions: List[Tuple], attributes: List['AttributeInfo']):
        super().__init__(name, None)
        self.max_stack = max_stack
        self.max_locals = max_locals
        self.code = code
        self.exceptions = exceptions
        self.attributes = attributes

    def __str__(self) -> str:
        return f"Code: stack={self.max_stack}, locals={self.max_locals}, code_len={len(self.code)}"

class Member:
    def __init__(self, access: AccessFlags, name: str, descriptor: str, attributes: List[AttributeInfo]):
        self.access = access
        self.name = name
        self.descriptor = descriptor
        self.attributes = attributes

    def __str__(self) -> str:
        return f"Member: 0x{self.access.value:04X} {self.name} {self.descriptor}"

#class ClassFile:
#    def __init__(self, header: Header, cp: List[ConstantPoolEntry], access: AccessFlags,
#                 this_class: ClassReference, super_class: ClassReference, interfaces: List[ClassReference],
#                 fields: List[Member], methods: List[Member]):
#        self.header = header
#        self.constant_pool = cp
#        self.access = access
#        self.this_class = this_class
#        self.super_class = super_class
#        self.interfaces = interfaces
#        self.fields = fields
#        self.methods = methods

class ClassFile:
    def __init__(self, header: Header, cp: List[ConstantPoolEntry], access: AccessFlags,
                 this_class: ClassReference, super_class: ClassReference, interfaces: List[ClassReference],
                 fields: List[Member], methods: List[Member], attributes: List[AttributeInfo]):
        self.header = header
        self.constant_pool = cp
        self.access = access
        self.this_class = this_class
        self.super_class = super_class
        self.interfaces = interfaces
        self.fields = fields
        self.methods = methods
        self.attributes = attributes  # Added attributes parameter (signature changd)
