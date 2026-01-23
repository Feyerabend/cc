#!/usr/bin/env python3
"""
RISC-V Linker
Links multiple object files into a single executable
"""

import sys
import struct
import json
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict


@dataclass
class Symbol:
    """Symbol table entry"""
    name: str
    address: int
    section: str  # 'text' or 'data'
    is_global: bool


@dataclass
class Relocation:
    """Relocation entry"""
    offset: int          # Offset in section where relocation is needed
    symbol: str          # Symbol name to relocate
    type: str           # Relocation type: 'R_RISCV_JAL', 'R_RISCV_BRANCH', etc.
    addend: int = 0     # Additional offset


@dataclass
class ObjectFile:
    """Represents a relocatable object file"""
    filename: str
    text_section: bytes
    data_section: bytes
    symbols: List[Symbol]
    relocations: List[Relocation]


class RISCVLinker:
    """Links multiple object files into executable"""
    
    def __init__(self, base_addr: int = 0x0):
        self.base_addr = base_addr
        self.objects: List[ObjectFile] = []
        self.global_symbols: Dict[str, Tuple[int, str]] = {}  # name -> (address, section)
        self.text_offset = 0
        self.data_offset = 0
        
    def load_object(self, filename: str):
        """Load an object file"""
        with open(filename, 'rb') as f:
            # Read magic number
            magic = f.read(4)
            if magic != b'RVO1':  # RISC-V Object v1
                raise ValueError(f"Invalid object file: {filename}")
            
            # Read header
            text_size = struct.unpack('<I', f.read(4))[0]
            data_size = struct.unpack('<I', f.read(4))[0]
            sym_count = struct.unpack('<I', f.read(4))[0]
            reloc_count = struct.unpack('<I', f.read(4))[0]
            
            # Read sections
            text_section = f.read(text_size)
            data_section = f.read(data_size)
            
            # Read symbols
            symbols = []
            for _ in range(sym_count):
                name_len = struct.unpack('<I', f.read(4))[0]
                name = f.read(name_len).decode('utf-8')
                address = struct.unpack('<I', f.read(4))[0]
                section_len = struct.unpack('<I', f.read(4))[0]
                section = f.read(section_len).decode('utf-8')
                is_global = struct.unpack('B', f.read(1))[0] != 0
                symbols.append(Symbol(name, address, section, is_global))
            
            # Read relocations
            relocations = []
            for _ in range(reloc_count):
                offset = struct.unpack('<I', f.read(4))[0]
                sym_len = struct.unpack('<I', f.read(4))[0]
                symbol = f.read(sym_len).decode('utf-8')
                type_len = struct.unpack('<I', f.read(4))[0]
                reloc_type = f.read(type_len).decode('utf-8')
                addend = struct.unpack('<i', f.read(4))[0]
                relocations.append(Relocation(offset, symbol, reloc_type, addend))
            
            obj = ObjectFile(filename, text_section, data_section, symbols, relocations)
            self.objects.append(obj)
            
    def link(self) -> bytes:
        """Link all loaded object files"""
        # First pass: assign addresses to sections
        text_sections = []
        data_sections = []
        section_offsets = {}  # (filename, section) -> offset
        
        current_text = self.base_addr
        current_data = self.base_addr
        
        for obj in self.objects:
            section_offsets[(obj.filename, 'text')] = current_text
            text_sections.append((current_text, obj.text_section))
            current_text += len(obj.text_section)
            
        for obj in self.objects:
            section_offsets[(obj.filename, 'data')] = current_data + current_text - self.base_addr
            data_sections.append((current_data + current_text - self.base_addr, obj.data_section))
            current_data += len(obj.data_section)
        
        # Build global symbol table
        for obj in self.objects:
            for sym in obj.symbols:
                if sym.is_global:
                    base = section_offsets[(obj.filename, sym.section)]
                    addr = base + sym.address
                    if sym.name in self.global_symbols:
                        old_addr, _ = self.global_symbols[sym.name]
                        if old_addr != addr:
                            raise ValueError(f"Multiple definitions of symbol: {sym.name}")
                    self.global_symbols[sym.name] = (addr, sym.section)
        
        # Allocate output buffer
        total_size = current_text - self.base_addr + current_data
        output = bytearray(total_size)
        
        # Copy text sections
        for offset, text in text_sections:
            start = offset - self.base_addr
            output[start:start+len(text)] = text
            
        # Copy data sections
        for offset, data in data_sections:
            start = offset - self.base_addr
            output[start:start+len(data)] = data
        
        # Apply relocations
        for obj in self.objects:
            section_base = section_offsets[(obj.filename, 'text')]
            
            for reloc in obj.relocations:
                # Resolve symbol
                if reloc.symbol in self.global_symbols:
                    target_addr, _ = self.global_symbols[reloc.symbol]
                else:
                    # Check local symbols
                    found = False
                    for sym in obj.symbols:
                        if sym.name == reloc.symbol:
                            base = section_offsets[(obj.filename, sym.section)]
                            target_addr = base + sym.address
                            found = True
                            break
                    if not found:
                        raise ValueError(f"Undefined symbol: {reloc.symbol}")
                
                # Calculate relocation
                reloc_pos = section_base - self.base_addr + reloc.offset
                
                if reloc.type == 'R_RISCV_JAL':
                    # JAL instruction relocation
                    pc = section_base + reloc.offset
                    offset = target_addr - pc + reloc.addend
                    
                    # Read existing instruction
                    instr = struct.unpack_from('<I', output, reloc_pos)[0]
                    
                    # Encode offset into JAL format
                    imm21 = offset & 0x1FFFFF
                    imm20 = (imm21 >> 20) & 1
                    imm19_12 = (imm21 >> 12) & 0xFF
                    imm11 = (imm21 >> 11) & 1
                    imm10_1 = (imm21 >> 1) & 0x3FF
                    
                    new_instr = (imm20 << 31) | (imm10_1 << 21) | (imm11 << 20) | \
                                (imm19_12 << 12) | (instr & 0xFFF)
                    
                    struct.pack_into('<I', output, reloc_pos, new_instr)
                    
                elif reloc.type == 'R_RISCV_BRANCH':
                    # Branch instruction relocation
                    pc = section_base + reloc.offset
                    offset = target_addr - pc + reloc.addend
                    
                    instr = struct.unpack_from('<I', output, reloc_pos)[0]
                    
                    imm13 = offset & 0x1FFF
                    imm12 = (imm13 >> 12) & 1
                    imm11 = (imm13 >> 11) & 1
                    imm10_5 = (imm13 >> 5) & 0x3F
                    imm4_1 = (imm13 >> 1) & 0xF
                    
                    new_instr = (imm12 << 31) | (imm10_5 << 25) | (instr & 0x01FFF07F) | \
                                (imm4_1 << 8) | (imm11 << 7)
                    
                    struct.pack_into('<I', output, reloc_pos, new_instr)
                    
                elif reloc.type == 'R_RISCV_PCREL_HI20':
                    # AUIPC relocation (upper 20 bits)
                    pc = section_base + reloc.offset
                    offset = target_addr - pc + reloc.addend
                    upper = (offset + 0x800) >> 12  # Add 0x800 for proper rounding
                    
                    instr = struct.unpack_from('<I', output, reloc_pos)[0]
                    new_instr = ((upper & 0xFFFFF) << 12) | (instr & 0xFFF)
                    struct.pack_into('<I', output, reloc_pos, new_instr)
                    
                elif reloc.type == 'R_RISCV_PCREL_LO12_I':
                    # ADDI relocation (lower 12 bits)
                    # For this we need the PC of the paired AUIPC
                    # Simplified: just use the offset directly
                    offset = (target_addr + reloc.addend) & 0xFFF
                    
                    instr = struct.unpack_from('<I', output, reloc_pos)[0]
                    new_instr = (offset << 20) | (instr & 0xFFFFF)
                    struct.pack_into('<I', output, reloc_pos, new_instr)
        
        return bytes(output)


def main():
    if len(sys.argv) < 3:
        print("Usage: python linker.py output.bin input1.o input2.o ...")
        sys.exit(1)
    
    output_file = sys.argv[1]
    input_files = sys.argv[2:]
    
    linker = RISCVLinker()
    
    for obj_file in input_files:
        print(f"Loading {obj_file}...")
        linker.load_object(obj_file)
    
    print("Linking...")
    executable = linker.link()
    
    with open(output_file, 'wb') as f:
        f.write(executable)
    
    print(f"Linked {len(input_files)} object files into {output_file}")
    print(f"Executable size: {len(executable)} bytes")


if __name__ == "__main__":
    main()
