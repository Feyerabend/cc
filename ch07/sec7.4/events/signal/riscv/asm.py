#!/usr/bin/env python3
"""
RISC-V RV32IM Assembler
Assembles assembly code to binary machine code with enhanced jump table support
"""

import sys
import struct
import argparse
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Instruction:
    """Represents a decoded RISC-V instruction"""
    opcode: str
    rd: int = 0
    rs1: int = 0
    rs2: int = 0
    imm: int = 0
    funct3: int = 0
    funct7: int = 0

    def encode(self) -> int:
        """Encode instruction to 32-bit machine code"""
        op = self.opcode

        # R-type: ADD, SUB, AND, OR, XOR, SLL, SRL, SRA, SLT, SLTU, MUL, DIV, etc.
        if op in ['ADD', 'SUB', 'AND', 'OR', 'XOR', 'SLL', 'SRL', 'SRA', 'SLT', 'SLTU', 
                  'MUL', 'MULH', 'MULHSU', 'MULHU', 'DIV', 'DIVU', 'REM', 'REMU']:
            return (self.funct7 << 25) | (self.rs2 << 20) | (self.rs1 << 15) | \
                   (self.funct3 << 12) | (self.rd << 7) | 0b0110011

        # I-type arithmetic: ADDI, ANDI, ORI, XORI, SLTI, SLTIU
        elif op in ['ADDI', 'ANDI', 'ORI', 'XORI', 'SLTI', 'SLTIU']:
            imm12 = self.imm & 0xFFF
            return (imm12 << 20) | (self.rs1 << 15) | (self.funct3 << 12) | \
                   (self.rd << 7) | 0b0010011

        # I-type shifts: SLLI, SRLI, SRAI
        elif op in ['SLLI', 'SRLI', 'SRAI']:
            shamt = self.imm & 0x1F
            upper = 0b0100000 if op == 'SRAI' else 0b0000000
            imm12 = (upper << 5) | shamt
            return (imm12 << 20) | (self.rs1 << 15) | (self.funct3 << 12) | \
                   (self.rd << 7) | 0b0010011

        # I-type loads: LB, LH, LW, LBU, LHU
        elif op in ['LB', 'LH', 'LW', 'LBU', 'LHU']:
            imm12 = self.imm & 0xFFF
            return (imm12 << 20) | (self.rs1 << 15) | (self.funct3 << 12) | \
                   (self.rd << 7) | 0b0000011

        # S-type stores: SB, SH, SW
        elif op in ['SB', 'SH', 'SW']:
            imm12 = self.imm & 0xFFF
            imm11_5 = (imm12 >> 5) & 0x7F
            imm4_0 = imm12 & 0x1F
            return (imm11_5 << 25) | (self.rs2 << 20) | (self.rs1 << 15) | \
                   (self.funct3 << 12) | (imm4_0 << 7) | 0b0100011

        # B-type branches: BEQ, BNE, BLT, BGE, BLTU, BGEU
        elif op in ['BEQ', 'BNE', 'BLT', 'BGE', 'BLTU', 'BGEU']:
            imm13 = self.imm & 0x1FFF
            imm12 = (imm13 >> 12) & 1
            imm11 = (imm13 >> 11) & 1
            imm10_5 = (imm13 >> 5) & 0x3F
            imm4_1 = (imm13 >> 1) & 0xF
            return (imm12 << 31) | (imm10_5 << 25) | (self.rs2 << 20) | (self.rs1 << 15) | \
                   (self.funct3 << 12) | (imm4_1 << 8) | (imm11 << 7) | 0b1100011

        # J-type: JAL
        elif op == 'JAL':
            imm21 = self.imm & 0x1FFFFF
            imm20 = (imm21 >> 20) & 1
            imm19_12 = (imm21 >> 12) & 0xFF
            imm11 = (imm21 >> 11) & 1
            imm10_1 = (imm21 >> 1) & 0x3FF
            return (imm20 << 31) | (imm10_1 << 21) | (imm11 << 20) | (imm19_12 << 12) | \
                   (self.rd << 7) | 0b1101111

        # I-type: JALR
        elif op == 'JALR':
            imm12 = self.imm & 0xFFF
            return (imm12 << 20) | (self.rs1 << 15) | (self.funct3 << 12) | \
                   (self.rd << 7) | 0b1100111

        # U-type: LUI, AUIPC
        elif op == 'LUI':
            imm20 = self.imm & 0xFFFFF
            return (imm20 << 12) | (self.rd << 7) | 0b0110111

        elif op == 'AUIPC':
            imm20 = self.imm & 0xFFFFF
            return (imm20 << 12) | (self.rd << 7) | 0b0010111

        # System instructions
        elif op == 'ECALL':
            return 0x00000073

        elif op == 'EBREAK':
            return 0x00100073

        raise ValueError(f"Cannot encode instruction: {op}")


class RISCVAssembler:
    """Two-pass assembler for RISC-V assembly code"""
    
    # ABI register name mappings
    REG_MAP = {
        'zero': 0, 'ra': 1, 'sp': 2, 'gp': 3, 'tp': 4,
        't0': 5, 't1': 6, 't2': 7,
        's0': 8, 'fp': 8, 's1': 9,
        'a0': 10, 'a1': 11, 'a2': 12, 'a3': 13, 'a4': 14, 'a5': 15, 'a6': 16, 'a7': 17,
        's2': 18, 's3': 19, 's4': 20, 's5': 21, 's6': 22, 's7': 23,
        's8': 24, 's9': 25, 's10': 26, 's11': 27,
        't3': 28, 't4': 29, 't5': 30, 't6': 31
    }
    
    def __init__(self, verbose: bool = False):
        self.labels: Dict[str, int] = {}
        self.instructions: List[Instruction] = []
        self.source_map: List[Tuple[int, str]] = []  # Maps instruction index to (source line num, source text)
        self.verbose = verbose
        
    def parse_register(self, reg: str) -> int:
        """Parse register name (x0-x31 or ABI names)"""
        reg = reg.strip().lower().rstrip(',')
        
        if reg in self.REG_MAP:
            return self.REG_MAP[reg]
        
        if reg.startswith('x'):
            return int(reg[1:])
        
        raise ValueError(f"Invalid register: {reg}")
    
    def parse_immediate(self, imm: str) -> int:
        """Parse immediate value (decimal or hex, can be negative)"""
        imm = imm.strip().rstrip(',')
        if imm.startswith('0x') or imm.startswith('0X'):
            return int(imm, 16)
        return int(imm)
    
    def sign_extend(self, val: int, bits: int) -> int:
        """Sign extend a value"""
        mask = 1 << (bits - 1)
        if val & mask:
            return val | (~((1 << bits) - 1))
        return val
    
    def parse_offset(self, operand: str) -> Tuple[int, int]:
        """Parse offset(register) format -> (offset, register)"""
        operand = operand.strip().rstrip(',')
        if '(' in operand:
            parts = operand.split('(')
            offset_str = parts[0].strip() if parts[0] else '0'
            reg = parts[1].rstrip(')')
            return self.parse_immediate(offset_str), self.parse_register(reg)
        else:
            # Just a register, offset = 0
            return 0, self.parse_register(operand)
    
    def assemble(self, source: str) -> bytes:
        """Assemble RISC-V assembly code into binary"""
        lines = source.strip().split('\n')
        
        if self.verbose:
            print("=== First Pass: Label Collection ===")
        
        # First pass: collect labels and calculate addresses
        addr = 0
        for line_num, line in enumerate(lines, 1):
            original_line = line
            # Remove comments
            line = line.split('#')[0].strip()
            if not line:
                continue
            
            # Check for label
            if ':' in line:
                label_parts = line.split(':', 1)
                label = label_parts[0].strip()
                self.labels[label] = addr
                if self.verbose:
                    print(f"Label '{label}' @ 0x{addr:04x}")
                
                # Check if there's more on the line
                rest = label_parts[1].strip() if len(label_parts) > 1 else ''
                if rest:
                    # Process rest as instruction or directive
                    op = rest.split()[0].upper() if rest.split() else ''
                    if op == 'LA':
                        addr += 8  # LA expands to 2 instructions
                    elif rest.startswith('.'):
                        directive = rest.split()[0]
                        if directive == '.word':
                            addr += 4
                        elif directive == '.byte':
                            parts = rest.split()
                            if len(parts) > 1:
                                byte_str = ' '.join(parts[1:])
                                byte_values = [v.strip() for v in byte_str.split(',')]
                                addr += len(byte_values)
                        elif directive == '.space':
                            parts = rest.split()
                            if len(parts) > 1:
                                addr += int(parts[1], 0)
                    else:
                        addr += 4
            else:
                # No label, process line
                op = line.split()[0].upper() if line.split() else ''
                if op == 'LA':
                    addr += 8  # LA expands to 2 instructions
                elif line.startswith('.'):
                    directive = line.split()[0]
                    if directive == '.word':
                        addr += 4
                    elif directive == '.byte':
                        parts = line.split()
                        if len(parts) > 1:
                            byte_str = ' '.join(parts[1:])
                            byte_values = [v.strip() for v in byte_str.split(',')]
                            addr += len(byte_values)
                    elif directive == '.space':
                        parts = line.split()
                        if len(parts) > 1:
                            addr += int(parts[1], 0)
                else:
                    addr += 4
        
        if self.verbose:
            print(f"\n=== Second Pass: Code Generation ===")
        
        # Second pass: generate binary
        binary = b''
        addr = 0
        for line_num, line in enumerate(lines, 1):
            original_line = line
            # Remove comments
            line = line.split('#')[0].strip()
            if not line:
                continue
            
            # Strip label if present
            if ':' in line:
                parts = line.split(':', 1)
                line = parts[1].strip() if len(parts) > 1 else ''
                if not line:
                    continue
            
            # Handle directives
            if line.startswith('.'):
                parts = line.split()
                directive = parts[0]
                
                if directive == '.word':
                    # Data directive - store 32-bit word
                    if len(parts) < 2:
                        raise ValueError(f"Line {line_num}: .word requires an argument")
                    
                    value_str = parts[1]
                    if value_str in self.labels:
                        value = self.labels[value_str]
                    else:
                        value = self.parse_immediate(value_str)
                    
                    binary += struct.pack('<I', value & 0xFFFFFFFF)
                    self.source_map.append((line_num, original_line))
                    
                    if self.verbose:
                        print(f"0x{addr:04x}: .word {value_str} = 0x{value:08x}")
                    addr += 4
                
                elif directive == '.byte':
                    # Byte directive - store bytes
                    if len(parts) < 2:
                        raise ValueError(f"Line {line_num}: .byte requires at least one argument")
                    
                    # Parse comma-separated byte values
                    byte_str = ' '.join(parts[1:])
                    byte_values = [v.strip() for v in byte_str.split(',')]
                    
                    if self.verbose:
                        bytes_hex = ' '.join(f"{self.parse_immediate(v) & 0xFF:02x}" for v in byte_values)
                        print(f"0x{addr:04x}: .byte {byte_str:30s} => {bytes_hex}")
                    
                    for val_str in byte_values:
                        value = self.parse_immediate(val_str)
                        binary += struct.pack('B', value & 0xFF)
                        addr += 1
                    
                    self.source_map.append((line_num, original_line))
                
                elif directive == '.space':
                    # Reserve space - fill with zeros
                    if len(parts) < 2:
                        raise ValueError(f"Line {line_num}: .space requires size argument")
                    
                    size = self.parse_immediate(parts[1])
                    binary += b'\x00' * size
                    self.source_map.append((line_num, original_line))
                    
                    if self.verbose:
                        print(f"0x{addr:04x}: .space {size}")
                    addr += size
                
                elif directive == '.align':
                    # Align to boundary (no-op in binary, just for labels)
                    pass
                
                continue
            
            # Parse and encode instruction
            try:
                parts_check = line.split()
                if parts_check and parts_check[0].upper() == 'LA':
                    # LA pseudo-instruction: expands to AUIPC + ADDI
                    target = parts_check[2]
                    rd = self.parse_register(parts_check[1])
                    
                    if target not in self.labels:
                        raise ValueError(f"Label '{target}' not found for LA instruction")
                    
                    label_addr = self.labels[target]
                    offset = label_addr - addr
                    
                    # Upper 20 bits for AUIPC
                    hi = (offset + 0x800) >> 12  # Add 0x800 for proper rounding
                    # Lower 12 bits for ADDI
                    lo = offset & 0xFFF
                    if lo & 0x800:  # If bit 11 is set, it's a negative offset
                        lo = lo - 4096
                    
                    # Generate AUIPC
                    auipc = Instruction('AUIPC', rd=rd, imm=hi & 0xFFFFF)
                    word1 = auipc.encode()
                    binary += struct.pack('<I', word1)
                    
                    if self.verbose:
                        print(f"0x{addr:04x}: {line:40s} => 0x{word1:08x}")
                    
                    # Generate ADDI
                    addi = Instruction('ADDI', rd=rd, rs1=rd, imm=lo, funct3=0b000)
                    word2 = addi.encode()
                    binary += struct.pack('<I', word2)
                    
                    if self.verbose:
                        print(f"0x{addr+4:04x}: {'  (ADDI part of LA)':40s} => 0x{word2:08x}")
                    
                    self.source_map.append((line_num, original_line))
                    self.source_map.append((line_num, original_line))
                    addr += 8
                else:
                    instr = self.parse_instruction(line, addr)
                    word = instr.encode()
                    binary += struct.pack('<I', word)
                    self.source_map.append((line_num, original_line))
                    
                    if self.verbose:
                        print(f"0x{addr:04x}: {line:40s} => 0x{word:08x}")
                    
                    addr += 4
                    
            except Exception as e:
                raise ValueError(f"Line {line_num}: {e}") from e
        
        return binary
    
    def parse_instruction(self, line: str, addr: int) -> Instruction:
        """Parse a single instruction line"""
        parts = line.split()
        if not parts:
            raise ValueError("Empty instruction")
        
        op = parts[0].upper()
        
        # R-type: op rd, rs1, rs2
        if op == 'ADD':
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               rs1=self.parse_register(parts[2]),
                               rs2=self.parse_register(parts[3]),
                               funct3=0b000, funct7=0b0000000)
        elif op == 'SUB':
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               rs1=self.parse_register(parts[2]),
                               rs2=self.parse_register(parts[3]),
                               funct3=0b000, funct7=0b0100000)
        elif op == 'AND':
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               rs1=self.parse_register(parts[2]),
                               rs2=self.parse_register(parts[3]),
                               funct3=0b111, funct7=0b0000000)
        elif op == 'OR':
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               rs1=self.parse_register(parts[2]),
                               rs2=self.parse_register(parts[3]),
                               funct3=0b110, funct7=0b0000000)
        elif op == 'XOR':
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               rs1=self.parse_register(parts[2]),
                               rs2=self.parse_register(parts[3]),
                               funct3=0b100, funct7=0b0000000)
        elif op == 'SLL':
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               rs1=self.parse_register(parts[2]),
                               rs2=self.parse_register(parts[3]),
                               funct3=0b001, funct7=0b0000000)
        elif op == 'SRL':
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               rs1=self.parse_register(parts[2]),
                               rs2=self.parse_register(parts[3]),
                               funct3=0b101, funct7=0b0000000)
        elif op == 'SRA':
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               rs1=self.parse_register(parts[2]),
                               rs2=self.parse_register(parts[3]),
                               funct3=0b101, funct7=0b0100000)
        elif op == 'SLT':
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               rs1=self.parse_register(parts[2]),
                               rs2=self.parse_register(parts[3]),
                               funct3=0b010, funct7=0b0000000)
        elif op == 'SLTU':
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               rs1=self.parse_register(parts[2]),
                               rs2=self.parse_register(parts[3]),
                               funct3=0b011, funct7=0b0000000)
        
        # M extension (multiply/divide)
        elif op == 'MUL':
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               rs1=self.parse_register(parts[2]),
                               rs2=self.parse_register(parts[3]),
                               funct3=0b000, funct7=0b0000001)
        elif op == 'MULH':
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               rs1=self.parse_register(parts[2]),
                               rs2=self.parse_register(parts[3]),
                               funct3=0b001, funct7=0b0000001)
        elif op == 'MULHSU':
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               rs1=self.parse_register(parts[2]),
                               rs2=self.parse_register(parts[3]),
                               funct3=0b010, funct7=0b0000001)
        elif op == 'MULHU':
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               rs1=self.parse_register(parts[2]),
                               rs2=self.parse_register(parts[3]),
                               funct3=0b011, funct7=0b0000001)
        elif op == 'DIV':
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               rs1=self.parse_register(parts[2]),
                               rs2=self.parse_register(parts[3]),
                               funct3=0b100, funct7=0b0000001)
        elif op == 'DIVU':
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               rs1=self.parse_register(parts[2]),
                               rs2=self.parse_register(parts[3]),
                               funct3=0b101, funct7=0b0000001)
        elif op == 'REM':
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               rs1=self.parse_register(parts[2]),
                               rs2=self.parse_register(parts[3]),
                               funct3=0b110, funct7=0b0000001)
        elif op == 'REMU':
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               rs1=self.parse_register(parts[2]),
                               rs2=self.parse_register(parts[3]),
                               funct3=0b111, funct7=0b0000001)
        
        # I-type arithmetic: op rd, rs1, imm
        elif op == 'ADDI':
            imm = self.sign_extend(self.parse_immediate(parts[3]), 12)
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               rs1=self.parse_register(parts[2]),
                               imm=imm,
                               funct3=0b000)
        elif op == 'ANDI':
            imm = self.sign_extend(self.parse_immediate(parts[3]), 12)
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               rs1=self.parse_register(parts[2]),
                               imm=imm,
                               funct3=0b111)
        elif op == 'ORI':
            imm = self.sign_extend(self.parse_immediate(parts[3]), 12)
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               rs1=self.parse_register(parts[2]),
                               imm=imm,
                               funct3=0b110)
        elif op == 'XORI':
            imm = self.sign_extend(self.parse_immediate(parts[3]), 12)
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               rs1=self.parse_register(parts[2]),
                               imm=imm,
                               funct3=0b100)
        elif op == 'SLTI':
            imm = self.sign_extend(self.parse_immediate(parts[3]), 12)
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               rs1=self.parse_register(parts[2]),
                               imm=imm,
                               funct3=0b010)
        elif op == 'SLTIU':
            imm = self.parse_immediate(parts[3])  # Note: unsigned immediate
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               rs1=self.parse_register(parts[2]),
                               imm=imm,
                               funct3=0b011)
        
        # I-type shifts: op rd, rs1, shamt
        elif op == 'SLLI':
            shamt = self.parse_immediate(parts[3]) & 0x1F
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               rs1=self.parse_register(parts[2]),
                               imm=shamt,
                               funct3=0b001)
        elif op == 'SRLI':
            shamt = self.parse_immediate(parts[3]) & 0x1F
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               rs1=self.parse_register(parts[2]),
                               imm=shamt,
                               funct3=0b101)
        elif op == 'SRAI':
            shamt = self.parse_immediate(parts[3]) & 0x1F
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               rs1=self.parse_register(parts[2]),
                               imm=shamt,
                               funct3=0b101)
        
        # Load: op rd, offset(rs1)
        elif op == 'LB':
            offset, base = self.parse_offset(parts[2])
            imm = self.sign_extend(offset, 12)
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               rs1=base,
                               imm=imm,
                               funct3=0b000)
        elif op == 'LH':
            offset, base = self.parse_offset(parts[2])
            imm = self.sign_extend(offset, 12)
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               rs1=base,
                               imm=imm,
                               funct3=0b001)
        elif op == 'LW':
            offset, base = self.parse_offset(parts[2])
            imm = self.sign_extend(offset, 12)
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               rs1=base,
                               imm=imm,
                               funct3=0b010)
        elif op == 'LBU':
            offset, base = self.parse_offset(parts[2])
            imm = self.sign_extend(offset, 12)
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               rs1=base,
                               imm=imm,
                               funct3=0b100)
        elif op == 'LHU':
            offset, base = self.parse_offset(parts[2])
            imm = self.sign_extend(offset, 12)
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               rs1=base,
                               imm=imm,
                               funct3=0b101)
        
        # Store: op rs2, offset(rs1)
        elif op == 'SB':
            offset, base = self.parse_offset(parts[2])
            imm = self.sign_extend(offset, 12)
            return Instruction(op,
                               rs1=base,
                               rs2=self.parse_register(parts[1]),
                               imm=imm,
                               funct3=0b000)
        elif op == 'SH':
            offset, base = self.parse_offset(parts[2])
            imm = self.sign_extend(offset, 12)
            return Instruction(op,
                               rs1=base,
                               rs2=self.parse_register(parts[1]),
                               imm=imm,
                               funct3=0b001)
        elif op == 'SW':
            offset, base = self.parse_offset(parts[2])
            imm = self.sign_extend(offset, 12)
            return Instruction(op,
                               rs1=base,
                               rs2=self.parse_register(parts[1]),
                               imm=imm,
                               funct3=0b010)
        
        # Branch: op rs1, rs2, label
        elif op == 'BEQ':
            target = parts[3]
            if target in self.labels:
                offset = self.labels[target] - addr
            else:
                offset = self.parse_immediate(target)
            return Instruction(op,
                               rs1=self.parse_register(parts[1]),
                               rs2=self.parse_register(parts[2]),
                               imm=offset,
                               funct3=0b000)
        elif op == 'BNE':
            target = parts[3]
            if target in self.labels:
                offset = self.labels[target] - addr
            else:
                offset = self.parse_immediate(target)
            return Instruction(op,
                               rs1=self.parse_register(parts[1]),
                               rs2=self.parse_register(parts[2]),
                               imm=offset,
                               funct3=0b001)
        elif op == 'BLT':
            target = parts[3]
            if target in self.labels:
                offset = self.labels[target] - addr
            else:
                offset = self.parse_immediate(target)
            return Instruction(op,
                               rs1=self.parse_register(parts[1]),
                               rs2=self.parse_register(parts[2]),
                               imm=offset,
                               funct3=0b100)
        elif op == 'BGE':
            target = parts[3]
            if target in self.labels:
                offset = self.labels[target] - addr
            else:
                offset = self.parse_immediate(target)
            return Instruction(op,
                               rs1=self.parse_register(parts[1]),
                               rs2=self.parse_register(parts[2]),
                               imm=offset,
                               funct3=0b101)
        elif op == 'BLTU':
            target = parts[3]
            if target in self.labels:
                offset = self.labels[target] - addr
            else:
                offset = self.parse_immediate(target)
            return Instruction(op,
                               rs1=self.parse_register(parts[1]),
                               rs2=self.parse_register(parts[2]),
                               imm=offset,
                               funct3=0b110)
        elif op == 'BGEU':
            target = parts[3]
            if target in self.labels:
                offset = self.labels[target] - addr
            else:
                offset = self.parse_immediate(target)
            return Instruction(op,
                               rs1=self.parse_register(parts[1]),
                               rs2=self.parse_register(parts[2]),
                               imm=offset,
                               funct3=0b111)
        
        # JAL: jal rd, label or jal label (rd=ra)
        elif op == 'JAL':
            if len(parts) > 2:
                rd = self.parse_register(parts[1])
                target = parts[2]
            else:
                rd = 1  # ra
                target = parts[1]
            if target in self.labels:
                offset = self.labels[target] - addr
            else:
                offset = self.parse_immediate(target)
            return Instruction(op, rd=rd, imm=offset)
        
        # JALR: jalr rd, offset(rs1) or jalr rd, rs1
        elif op == 'JALR':
            rd = self.parse_register(parts[1])
            if len(parts) > 2:
                if '(' in parts[2]:
                    offset, base = self.parse_offset(parts[2])
                else:
                    offset = 0
                    base = self.parse_register(parts[2])
            else:
                offset = 0
                base = self.parse_register(parts[1])
            imm = self.sign_extend(offset, 12)
            return Instruction(op, rd=rd, rs1=base, imm=imm, funct3=0b000)
        
        # LUI: lui rd, imm
        elif op == 'LUI':
            imm_str = parts[2]
            if imm_str in self.labels:
                imm = (self.labels[imm_str] >> 12) & 0xFFFFF
            else:
                imm = self.parse_immediate(imm_str)
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               imm=imm)
        
        # AUIPC: auipc rd, imm
        elif op == 'AUIPC':
            imm_str = parts[2]
            if imm_str in self.labels:
                imm = ((self.labels[imm_str] - addr) >> 12) & 0xFFFFF
            else:
                imm = self.parse_immediate(imm_str)
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               imm=imm)
        
        # ECALL, EBREAK
        elif op == 'ECALL':
            return Instruction(op, funct3=0b000)
        elif op == 'EBREAK':
            return Instruction(op, funct3=0b000)
        
        # Pseudo-instructions
        elif op == 'NOP':
            return Instruction('ADDI', rd=0, rs1=0, imm=0, funct3=0b000)
        
        elif op == 'MV':
            return Instruction('ADDI',
                               rd=self.parse_register(parts[1]),
                               rs1=self.parse_register(parts[2]),
                               imm=0,
                               funct3=0b000)
        
        elif op == 'LI':
            imm_str = parts[2]
            if imm_str in self.labels:
                imm = self.sign_extend(self.labels[imm_str], 12)
            else:
                imm = self.sign_extend(self.parse_immediate(imm_str), 12)
            return Instruction('ADDI',
                               rd=self.parse_register(parts[1]),
                               rs1=0,
                               imm=imm,
                               funct3=0b000)
        
        elif op == 'J':
            target = parts[1]
            if target in self.labels:
                offset = self.labels[target] - addr
            else:
                offset = self.parse_immediate(target)
            return Instruction('JAL', rd=0, imm=offset)
        
        elif op == 'RET':
            return Instruction('JALR', rd=0, rs1=1, imm=0, funct3=0b000)
        
        raise ValueError(f"Unknown instruction: {op}")


def main():
    parser = argparse.ArgumentParser(description='RISC-V RV32IM Assembler')
    parser.add_argument('input', help='Input assembly file (.asm)')
    parser.add_argument('output', help='Output binary file (.bin)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('-d', '--dump', action='store_true', help='Dump hex and disassembly')
    
    args = parser.parse_args()
    
    # Read source
    with open(args.input, 'r') as f:
        source = f.read()
    
    # Assemble
    asm = RISCVAssembler(verbose=args.verbose)
    binary = asm.assemble(source)
    
    # Write output
    with open(args.output, 'wb') as f:
        f.write(binary)
    
    print(f"\n✓ Assembled {len(binary)//4} instructions ({len(binary)} bytes) to {args.output}")
    
    # Dump hex if requested
    if args.dump:
        print(f"\n=== Binary Dump ===")
        for i in range(0, len(binary), 16):
            hex_str = ' '.join(f'{b:02x}' for b in binary[i:i+16])
            print(f"0x{i:04x}: {hex_str}")


if __name__ == "__main__":
    main()
