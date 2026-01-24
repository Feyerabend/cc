#!/usr/bin/env python3
"""
RISC-V RV32I Assembler
Assembles assembly code to binary machine code file
"""

import sys
import struct
from typing import List, Dict, Tuple
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
        op = self.opcode
        # Handle negative imm correctly with masks

        if op in ['ADD', 'SUB', 'AND', 'OR', 'XOR', 'SLL', 'SRL', 'SRA', 'SLT', 'SLTU', 
                  'MUL', 'MULH', 'MULHSU', 'MULHU', 'DIV', 'DIVU', 'REM', 'REMU']:
            # R-type
            return (self.funct7 << 25) | (self.rs2 << 20) | (self.rs1 << 15) | \
                   (self.funct3 << 12) | (self.rd << 7) | 0b0110011

        elif op in ['ADDI', 'ANDI', 'ORI', 'XORI', 'SLTI', 'SLTIU']:
            # I-type arithmetic
            imm12 = self.imm & 0xFFF
            return (imm12 << 20) | (self.rs1 << 15) | (self.funct3 << 12) | \
                   (self.rd << 7) | 0b0010011

        elif op in ['SLLI', 'SRLI', 'SRAI']:
            # I-type shifts
            shamt = self.imm & 0x1F
            upper = 0b0100000 if op == 'SRAI' else 0b0000000
            imm12 = (upper << 5) | shamt
            return (imm12 << 20) | (self.rs1 << 15) | (self.funct3 << 12) | \
                   (self.rd << 7) | 0b0010011

        elif op in ['LB', 'LH', 'LW', 'LBU', 'LHU']:
            # Loads (I-type)
            imm12 = self.imm & 0xFFF
            return (imm12 << 20) | (self.rs1 << 15) | (self.funct3 << 12) | \
                   (self.rd << 7) | 0b0000011

        elif op in ['SB', 'SH', 'SW']:
            # Stores (S-type)
            imm12 = self.imm & 0xFFF
            imm11_5 = (imm12 >> 5) & 0x7F
            imm4_0 = imm12 & 0x1F
            return (imm11_5 << 25) | (self.rs2 << 20) | (self.rs1 << 15) | \
                   (self.funct3 << 12) | (imm4_0 << 7) | 0b0100011

        elif op in ['BEQ', 'BNE', 'BLT', 'BGE', 'BLTU', 'BGEU']:
            # Branches (B-type)
            imm13 = self.imm & 0x1FFF
            imm12 = (imm13 >> 12) & 1
            imm11 = (imm13 >> 11) & 1
            imm10_5 = (imm13 >> 5) & 0x3F
            imm4_1 = (imm13 >> 1) & 0xF
            return (imm12 << 31) | (imm10_5 << 25) | (self.rs2 << 20) | (self.rs1 << 15) | \
                   (self.funct3 << 12) | (imm4_1 << 8) | (imm11 << 7) | 0b1100011

        elif op == 'JAL':
            # J-type
            imm21 = self.imm & 0x1FFFFF
            imm20 = (imm21 >> 20) & 1
            imm19_12 = (imm21 >> 12) & 0xFF
            imm11 = (imm21 >> 11) & 1
            imm10_1 = (imm21 >> 1) & 0x3FF
            return (imm20 << 31) | (imm10_1 << 21) | (imm11 << 20) | (imm19_12 << 12) | \
                   (self.rd << 7) | 0b1101111

        elif op == 'JALR':
            # I-type
            imm12 = self.imm & 0xFFF
            return (imm12 << 20) | (self.rs1 << 15) | (self.funct3 << 12) | \
                   (self.rd << 7) | 0b1100111

        elif op == 'LUI':
            # U-type
            imm20 = self.imm & 0xFFFFF
            return (imm20 << 12) | (self.rd << 7) | 0b0110111

        elif op == 'AUIPC':
            # U-type
            imm20 = self.imm & 0xFFFFF
            return (imm20 << 12) | (self.rd << 7) | 0b0010111

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
    
    def __init__(self):
        self.labels: Dict[str, int] = {}
        self.instructions: List[Instruction] = []
        self.source_map: List[int] = []  # Maps instruction index to source line
        
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
        
        # First pass: collect labels
        addr = 0
        for line_num, line in enumerate(lines):
            # Remove comments
            line = line.split('#')[0].strip()
            if not line:
                continue
            
            # Check for label
            if ':' in line:
                label = line.split(':')[0].strip()
                self.labels[label] = addr
                # Check if there's an instruction on the same line
                rest = line.split(':', 1)[1].strip() if ':' in line else ''
                if rest:
                    addr += 4
                    self.source_map.append(line_num)
            else:
                addr += 4
                self.source_map.append(line_num)
        
        # Second pass: assemble instructions
        addr = 0
        binary = b''
        for line in lines:
            line = line.split('#')[0].strip()
            if not line:
                continue
            
            # Skip label-only lines
            if ':' in line:
                rest = line.split(':', 1)[1].strip()
                if not rest:
                    continue
                line = rest
            
            instr = self.parse_instruction(line, addr)
            self.instructions.append(instr)
            word = instr.encode()
            binary += struct.pack('<I', word)
            addr += 4
        
        return binary
    
    def parse_instruction(self, line: str, addr: int) -> Instruction:
        """Parse a single instruction"""
        parts = line.replace(',', ' ').split()
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
        
        # M extension
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
            imm = self.sign_extend(self.parse_immediate(parts[3]), 12)
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
            if len(parts) > 2 and '(' in parts[2]:
                offset, base = self.parse_offset(parts[2])
            else:
                offset = 0
                base = self.parse_register(parts[2])
            imm = self.sign_extend(offset, 12)
            return Instruction(op, rd=rd, rs1=base, imm=imm, funct3=0b000)
        
        # LUI: lui rd, imm
        elif op == 'LUI':
            imm = self.parse_immediate(parts[2])
            return Instruction(op,
                               rd=self.parse_register(parts[1]),
                               imm=imm)
        
        # AUIPC: auipc rd, imm
        elif op == 'AUIPC':
            imm = self.parse_immediate(parts[2])
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
            imm = self.sign_extend(self.parse_immediate(parts[2]), 12)  # Assumes small imm
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


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python asm.py input.asm output.bin")
        sys.exit(1)
    
    with open(sys.argv[1], 'r') as f:
        source = f.read()
    
    asm = RISCVAssembler()
    binary = asm.assemble(source)
    
    with open(sys.argv[2], 'wb') as f:
        f.write(binary)
    
    print(f"Assembled {len(binary)//4} instructions to {sys.argv[2]}")
