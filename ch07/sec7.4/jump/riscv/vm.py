#!/usr/bin/env python3
"""
RISC-V RV32IM Virtual Machine
Executes binary machine code with enhanced debugging for jump tables
"""

import sys
import struct
import argparse
from dataclasses import dataclass
from typing import Optional, List


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


class RISCVVM:
    """RISC-V Virtual Machine (RV32IM - Base + Multiply/Divide)"""
    
    # ABI register names for display
    REG_NAMES = [
        'zero', 'ra', 'sp', 'gp', 'tp', 't0', 't1', 't2',
        's0', 's1', 'a0', 'a1', 'a2', 'a3', 'a4', 'a5',
        'a6', 'a7', 's2', 's3', 's4', 's5', 's6', 's7',
        's8', 's9', 's10', 's11', 't3', 't4', 't5', 't6'
    ]
    
    def __init__(self, mem_size: int = 65536, debug: bool = False, trace: bool = False):
        self.regs = [0] * 32  # 32 general-purpose registers
        self.pc = 0           # Program counter
        self.memory = bytearray(mem_size)  # Main memory
        self.running = True
        self.output = []
        self.debug = debug
        self.trace = trace
        self.instruction_count = 0
        self.breakpoints = set()
        
    def reset(self):
        """Reset VM state"""
        self.regs = [0] * 32
        self.pc = 0
        self.memory = bytearray(len(self.memory))
        self.running = True
        self.output = []
        self.instruction_count = 0
    
    def load_program(self, filename: str):
        """Load binary program into memory at address 0"""
        with open(filename, 'rb') as f:
            program = f.read()
        # No longer require multiple of 4 - can have data bytes
        self.memory[0:len(program)] = program
        
        if self.debug:
            print(f"Loaded {len(program)} bytes into memory")
    
    def signed(self, val: int) -> int:
        """Interpret 32-bit unsigned as signed"""
        val = val & 0xFFFFFFFF
        if val & 0x80000000:
            return val - 0x100000000
        return val
    
    def unsigned(self, val: int) -> int:
        """Interpret as 32-bit unsigned"""
        return val & 0xFFFFFFFF
    
    def sign_extend(self, val: int, bits: int) -> int:
        """Sign extend a value"""
        mask = 1 << (bits - 1)
        if val & mask:
            return val | (~((1 << bits) - 1))
        return val
    
    def read_mem(self, addr: int, size: int, signed: bool = False) -> int:
        """Read from memory (size in bytes: 1, 2, or 4)"""
        addr = addr & 0xFFFFFFFF
        if addr < 0 or addr + size > len(self.memory):
            raise ValueError(f"Memory access out of bounds: 0x{addr:08x}")
        
        if size == 1:
            val = self.memory[addr]
            if signed:
                val = self.sign_extend(val, 8)
        elif size == 2:
            val = struct.unpack_from('<H', self.memory, addr)[0]
            if signed:
                val = self.sign_extend(val, 16)
        else:  # size == 4
            val = struct.unpack_from('<I', self.memory, addr)[0]
        
        return val
    
    def write_mem(self, addr: int, val: int, size: int):
        """Write to memory (size in bytes: 1, 2, or 4)"""
        addr = addr & 0xFFFFFFFF
        if addr < 0 or addr + size > len(self.memory):
            raise ValueError(f"Memory access out of bounds: 0x{addr:08x}")
        
        if size == 1:
            self.memory[addr] = val & 0xFF
        elif size == 2:
            struct.pack_into('<H', self.memory, addr, val & 0xFFFF)
        else:  # size == 4
            struct.pack_into('<I', self.memory, addr, val & 0xFFFFFFFF)
    
    def decode(self, word: int) -> Instruction:
        """Decode 32-bit instruction word to Instruction"""
        opcode = word & 0x7F
        rd = (word >> 7) & 0x1F
        funct3 = (word >> 12) & 0x7
        rs1 = (word >> 15) & 0x1F
        rs2 = (word >> 20) & 0x1F
        funct7 = (word >> 25) & 0x7F

        # R-type instructions
        if opcode == 0b0110011:
            if funct7 == 0b0000000:
                if funct3 == 0b000: op = 'ADD'
                elif funct3 == 0b100: op = 'XOR'
                elif funct3 == 0b110: op = 'OR'
                elif funct3 == 0b111: op = 'AND'
                elif funct3 == 0b001: op = 'SLL'
                elif funct3 == 0b101: op = 'SRL'
                elif funct3 == 0b010: op = 'SLT'
                elif funct3 == 0b011: op = 'SLTU'
                else: raise ValueError("Unknown R-type funct3")
            elif funct7 == 0b0100000:
                if funct3 == 0b000: op = 'SUB'
                elif funct3 == 0b101: op = 'SRA'
                else: raise ValueError("Unknown R-type funct3")
            elif funct7 == 0b0000001:  # M extension
                if funct3 == 0b000: op = 'MUL'
                elif funct3 == 0b001: op = 'MULH'
                elif funct3 == 0b010: op = 'MULHSU'
                elif funct3 == 0b011: op = 'MULHU'
                elif funct3 == 0b100: op = 'DIV'
                elif funct3 == 0b101: op = 'DIVU'
                elif funct3 == 0b110: op = 'REM'
                elif funct3 == 0b111: op = 'REMU'
                else: raise ValueError("Unknown M funct3")
            else:
                raise ValueError("Unknown R-type funct7")
            return Instruction(op, rd=rd, rs1=rs1, rs2=rs2, funct3=funct3, funct7=funct7)

        # I-type arithmetic/shifts
        elif opcode == 0b0010011:
            imm = word >> 20
            imm = self.sign_extend(imm, 12)
            if funct3 == 0b000: op = 'ADDI'
            elif funct3 == 0b100: op = 'XORI'
            elif funct3 == 0b110: op = 'ORI'
            elif funct3 == 0b111: op = 'ANDI'
            elif funct3 == 0b010: op = 'SLTI'
            elif funct3 == 0b011: op = 'SLTIU'
            elif funct3 == 0b001:
                op = 'SLLI'
                imm = imm & 0x1F
            elif funct3 == 0b101:
                shamt = imm & 0x1F
                if (word >> 25) == 0b0000000:
                    op = 'SRLI'
                    imm = shamt
                elif (word >> 25) == 0b0100000:
                    op = 'SRAI'
                    imm = shamt
                else:
                    raise ValueError("Unknown shift funct7")
            else:
                raise ValueError("Unknown I-type funct3")
            return Instruction(op, rd=rd, rs1=rs1, imm=imm, funct3=funct3)

        # Loads
        elif opcode == 0b0000011:
            imm = word >> 20
            imm = self.sign_extend(imm, 12)
            if funct3 == 0b000: op = 'LB'
            elif funct3 == 0b001: op = 'LH'
            elif funct3 == 0b010: op = 'LW'
            elif funct3 == 0b100: op = 'LBU'
            elif funct3 == 0b101: op = 'LHU'
            else: raise ValueError("Unknown load funct3")
            return Instruction(op, rd=rd, rs1=rs1, imm=imm, funct3=funct3)

        # Stores
        elif opcode == 0b0100011:
            imm = ((word >> 25) & 0x7F) << 5 | ((word >> 7) & 0x1F)
            imm = self.sign_extend(imm, 12)
            if funct3 == 0b000: op = 'SB'
            elif funct3 == 0b001: op = 'SH'
            elif funct3 == 0b010: op = 'SW'
            else: raise ValueError("Unknown store funct3")
            return Instruction(op, rs1=rs1, rs2=rs2, imm=imm, funct3=funct3)

        # Branches
        elif opcode == 0b1100011:
            imm = ((word >> 31) & 1) << 12 | ((word >> 7) & 1) << 11 | \
                  ((word >> 25) & 0x3F) << 5 | ((word >> 8) & 0xF) << 1
            imm = self.sign_extend(imm, 13)
            if funct3 == 0b000: op = 'BEQ'
            elif funct3 == 0b001: op = 'BNE'
            elif funct3 == 0b100: op = 'BLT'
            elif funct3 == 0b101: op = 'BGE'
            elif funct3 == 0b110: op = 'BLTU'
            elif funct3 == 0b111: op = 'BGEU'
            else: raise ValueError("Unknown branch funct3")
            return Instruction(op, rs1=rs1, rs2=rs2, imm=imm, funct3=funct3)

        # JAL
        elif opcode == 0b1101111:
            imm = ((word >> 31) & 1) << 20 | ((word >> 12) & 0xFF) << 12 | \
                  ((word >> 20) & 1) << 11 | ((word >> 21) & 0x3FF) << 1
            imm = self.sign_extend(imm, 21)
            return Instruction('JAL', rd=rd, imm=imm)

        # JALR
        elif opcode == 0b1100111:
            imm = word >> 20
            imm = self.sign_extend(imm, 12)
            if funct3 != 0b000:
                raise ValueError("Invalid JALR funct3")
            return Instruction('JALR', rd=rd, rs1=rs1, imm=imm, funct3=funct3)

        # LUI
        elif opcode == 0b0110111:
            imm = word >> 12
            return Instruction('LUI', rd=rd, imm=imm)

        # AUIPC
        elif opcode == 0b0010111:
            imm = word >> 12
            return Instruction('AUIPC', rd=rd, imm=imm)

        # System instructions
        elif opcode == 0b1110011:
            if word == 0x00000073:
                return Instruction('ECALL')
            elif word == 0x00100073:
                return Instruction('EBREAK')
            else:
                raise ValueError("Unknown system instruction")

        raise ValueError(f"Unknown opcode: 0b{opcode:07b}")
    
    def format_instruction(self, instr: Instruction, addr: int) -> str:
        """Format instruction for display"""
        op = instr.opcode
        
        # R-type
        if op in ['ADD', 'SUB', 'AND', 'OR', 'XOR', 'SLL', 'SRL', 'SRA', 'SLT', 'SLTU',
                  'MUL', 'MULH', 'MULHSU', 'MULHU', 'DIV', 'DIVU', 'REM', 'REMU']:
            return f"{op:6s} {self.REG_NAMES[instr.rd]}, {self.REG_NAMES[instr.rs1]}, {self.REG_NAMES[instr.rs2]}"
        
        # I-type arithmetic
        elif op in ['ADDI', 'ANDI', 'ORI', 'XORI', 'SLTI', 'SLTIU', 'SLLI', 'SRLI', 'SRAI']:
            return f"{op:6s} {self.REG_NAMES[instr.rd]}, {self.REG_NAMES[instr.rs1]}, {instr.imm}"
        
        # Loads
        elif op in ['LB', 'LH', 'LW', 'LBU', 'LHU']:
            return f"{op:6s} {self.REG_NAMES[instr.rd]}, {instr.imm}({self.REG_NAMES[instr.rs1]})"
        
        # Stores
        elif op in ['SB', 'SH', 'SW']:
            return f"{op:6s} {self.REG_NAMES[instr.rs2]}, {instr.imm}({self.REG_NAMES[instr.rs1]})"
        
        # Branches
        elif op in ['BEQ', 'BNE', 'BLT', 'BGE', 'BLTU', 'BGEU']:
            target = (addr + instr.imm) & 0xFFFFFFFF
            return f"{op:6s} {self.REG_NAMES[instr.rs1]}, {self.REG_NAMES[instr.rs2]}, 0x{target:x}"
        
        # JAL
        elif op == 'JAL':
            target = (addr + instr.imm) & 0xFFFFFFFF
            return f"{op:6s} {self.REG_NAMES[instr.rd]}, 0x{target:x}"
        
        # JALR
        elif op == 'JALR':
            return f"{op:6s} {self.REG_NAMES[instr.rd]}, {instr.imm}({self.REG_NAMES[instr.rs1]})"
        
        # LUI/AUIPC
        elif op in ['LUI', 'AUIPC']:
            return f"{op:6s} {self.REG_NAMES[instr.rd]}, 0x{instr.imm:x}"
        
        # System
        elif op in ['ECALL', 'EBREAK']:
            return f"{op:6s}"
        
        return f"{op:6s} (unknown format)"
    
    def execute(self):
        """Execute loaded program"""
        if self.debug:
            print("\n=== Execution Started ===")
        
        while self.running and self.pc < len(self.memory):
            # Check breakpoint
            if self.pc in self.breakpoints:
                print(f"\nBreakpoint hit at 0x{self.pc:04x}")
                self.print_regs()
                input("Press Enter to continue...")
            
            # Fetch
            word = self.read_mem(self.pc, 4)
            
            # Decode
            try:
                instr = self.decode(word)
            except Exception as e:
                print(f"Error decoding at PC=0x{self.pc:04x}: {e}")
                self.running = False
                break
            
            # Trace
            if self.trace:
                print(f"0x{self.pc:04x}: {word:08x}  {self.format_instruction(instr, self.pc)}")
            
            # Execute
            try:
                self.execute_instruction(instr)
                self.instruction_count += 1
            except Exception as e:
                print(f"Error executing at PC=0x{self.pc:04x}: {e}")
                print(f"Instruction: {self.format_instruction(instr, self.pc)}")
                self.running = False
                break
        
        if self.debug:
            print(f"\n=== Execution Completed ===")
            print(f"Instructions executed: {self.instruction_count}")
            print(f"Final PC: 0x{self.pc:04x}")
    
    def execute_instruction(self, instr: Instruction):
        """Execute a single instruction"""
        op = instr.opcode
        
        # R-type ALU operations
        if op == 'ADD':
            self.regs[instr.rd] = (self.regs[instr.rs1] + self.regs[instr.rs2]) & 0xFFFFFFFF
            self.pc += 4
        elif op == 'SUB':
            self.regs[instr.rd] = (self.regs[instr.rs1] - self.regs[instr.rs2]) & 0xFFFFFFFF
            self.pc += 4
        elif op == 'AND':
            self.regs[instr.rd] = (self.regs[instr.rs1] & self.regs[instr.rs2]) & 0xFFFFFFFF
            self.pc += 4
        elif op == 'OR':
            self.regs[instr.rd] = (self.regs[instr.rs1] | self.regs[instr.rs2]) & 0xFFFFFFFF
            self.pc += 4
        elif op == 'XOR':
            self.regs[instr.rd] = (self.regs[instr.rs1] ^ self.regs[instr.rs2]) & 0xFFFFFFFF
            self.pc += 4
        elif op == 'SLL':
            shamt = self.regs[instr.rs2] & 0x1F
            self.regs[instr.rd] = (self.regs[instr.rs1] << shamt) & 0xFFFFFFFF
            self.pc += 4
        elif op == 'SRL':
            shamt = self.regs[instr.rs2] & 0x1F
            self.regs[instr.rd] = (self.unsigned(self.regs[instr.rs1]) >> shamt) & 0xFFFFFFFF
            self.pc += 4
        elif op == 'SRA':
            shamt = self.regs[instr.rs2] & 0x1F
            self.regs[instr.rd] = (self.signed(self.regs[instr.rs1]) >> shamt) & 0xFFFFFFFF
            self.pc += 4
        elif op == 'SLT':
            self.regs[instr.rd] = 1 if self.signed(self.regs[instr.rs1]) < self.signed(self.regs[instr.rs2]) else 0
            self.pc += 4
        elif op == 'SLTU':
            self.regs[instr.rd] = 1 if self.unsigned(self.regs[instr.rs1]) < self.unsigned(self.regs[instr.rs2]) else 0
            self.pc += 4
        
        # M extension
        elif op == 'MUL':
            rs1 = self.signed(self.regs[instr.rs1])
            rs2 = self.signed(self.regs[instr.rs2])
            self.regs[instr.rd] = (rs1 * rs2) & 0xFFFFFFFF
            self.pc += 4
        elif op == 'MULH':
            rs1 = self.signed(self.regs[instr.rs1])
            rs2 = self.signed(self.regs[instr.rs2])
            result = rs1 * rs2
            self.regs[instr.rd] = (result >> 32) & 0xFFFFFFFF
            self.pc += 4
        elif op == 'MULHSU':
            rs1 = self.signed(self.regs[instr.rs1])
            rs2 = self.unsigned(self.regs[instr.rs2])
            result = rs1 * rs2
            self.regs[instr.rd] = (result >> 32) & 0xFFFFFFFF
            self.pc += 4
        elif op == 'MULHU':
            rs1 = self.unsigned(self.regs[instr.rs1])
            rs2 = self.unsigned(self.regs[instr.rs2])
            result = rs1 * rs2
            self.regs[instr.rd] = (result >> 32) & 0xFFFFFFFF
            self.pc += 4
        elif op == 'DIV':
            rs1 = self.signed(self.regs[instr.rs1])
            rs2 = self.signed(self.regs[instr.rs2])
            if rs2 == 0:
                self.regs[instr.rd] = 0xFFFFFFFF
            elif rs1 == -0x80000000 and rs2 == -1:
                self.regs[instr.rd] = 0x80000000 & 0xFFFFFFFF
            else:
                self.regs[instr.rd] = (rs1 // rs2) & 0xFFFFFFFF
            self.pc += 4
        elif op == 'DIVU':
            rs1 = self.unsigned(self.regs[instr.rs1])
            rs2 = self.unsigned(self.regs[instr.rs2])
            self.regs[instr.rd] = (rs1 // rs2 if rs2 != 0 else 0xFFFFFFFF) & 0xFFFFFFFF
            self.pc += 4
        elif op == 'REM':
            rs1 = self.signed(self.regs[instr.rs1])
            rs2 = self.signed(self.regs[instr.rs2])
            if rs2 == 0:
                self.regs[instr.rd] = rs1 & 0xFFFFFFFF
            elif rs1 == -0x80000000 and rs2 == -1:
                self.regs[instr.rd] = 0
            else:
                self.regs[instr.rd] = (rs1 % rs2) & 0xFFFFFFFF
            self.pc += 4
        elif op == 'REMU':
            rs1 = self.unsigned(self.regs[instr.rs1])
            rs2 = self.unsigned(self.regs[instr.rs2])
            self.regs[instr.rd] = (rs1 % rs2 if rs2 != 0 else rs1) & 0xFFFFFFFF
            self.pc += 4
        
        # I-type ALU operations
        elif op == 'ADDI':
            self.regs[instr.rd] = (self.regs[instr.rs1] + instr.imm) & 0xFFFFFFFF
            self.pc += 4
        elif op == 'ANDI':
            self.regs[instr.rd] = (self.regs[instr.rs1] & instr.imm) & 0xFFFFFFFF
            self.pc += 4
        elif op == 'ORI':
            self.regs[instr.rd] = (self.regs[instr.rs1] | instr.imm) & 0xFFFFFFFF
            self.pc += 4
        elif op == 'XORI':
            self.regs[instr.rd] = (self.regs[instr.rs1] ^ instr.imm) & 0xFFFFFFFF
            self.pc += 4
        elif op == 'SLTI':
            self.regs[instr.rd] = 1 if self.signed(self.regs[instr.rs1]) < self.signed(instr.imm) else 0
            self.pc += 4
        elif op == 'SLTIU':
            self.regs[instr.rd] = 1 if self.unsigned(self.regs[instr.rs1]) < self.unsigned(instr.imm) else 0
            self.pc += 4
        elif op == 'SLLI':
            self.regs[instr.rd] = (self.regs[instr.rs1] << instr.imm) & 0xFFFFFFFF
            self.pc += 4
        elif op == 'SRLI':
            self.regs[instr.rd] = (self.unsigned(self.regs[instr.rs1]) >> instr.imm) & 0xFFFFFFFF
            self.pc += 4
        elif op == 'SRAI':
            self.regs[instr.rd] = (self.signed(self.regs[instr.rs1]) >> instr.imm) & 0xFFFFFFFF
            self.pc += 4
        
        # Load operations
        elif op == 'LB':
            addr = (self.regs[instr.rs1] + instr.imm) & 0xFFFFFFFF
            self.regs[instr.rd] = self.read_mem(addr, 1, signed=True) & 0xFFFFFFFF
            self.pc += 4
        elif op == 'LH':
            addr = (self.regs[instr.rs1] + instr.imm) & 0xFFFFFFFF
            self.regs[instr.rd] = self.read_mem(addr, 2, signed=True) & 0xFFFFFFFF
            self.pc += 4
        elif op == 'LW':
            addr = (self.regs[instr.rs1] + instr.imm) & 0xFFFFFFFF
            val = self.read_mem(addr, 4)
            self.regs[instr.rd] = val & 0xFFFFFFFF
            
            if self.trace:
                print(f"         LW: addr=0x{addr:08x} -> val=0x{val:08x}")
            self.pc += 4
        elif op == 'LBU':
            addr = (self.regs[instr.rs1] + instr.imm) & 0xFFFFFFFF
            self.regs[instr.rd] = self.read_mem(addr, 1, signed=False) & 0xFFFFFFFF
            self.pc += 4
        elif op == 'LHU':
            addr = (self.regs[instr.rs1] + instr.imm) & 0xFFFFFFFF
            self.regs[instr.rd] = self.read_mem(addr, 2, signed=False) & 0xFFFFFFFF
            self.pc += 4
        
        # Store operations
        elif op == 'SB':
            addr = (self.regs[instr.rs1] + instr.imm) & 0xFFFFFFFF
            self.write_mem(addr, self.regs[instr.rs2], 1)
            self.pc += 4
        elif op == 'SH':
            addr = (self.regs[instr.rs1] + instr.imm) & 0xFFFFFFFF
            self.write_mem(addr, self.regs[instr.rs2], 2)
            self.pc += 4
        elif op == 'SW':
            addr = (self.regs[instr.rs1] + instr.imm) & 0xFFFFFFFF
            self.write_mem(addr, self.regs[instr.rs2], 4)
            self.pc += 4
        
        # Branch operations
        elif op == 'BEQ':
            if self.regs[instr.rs1] == self.regs[instr.rs2]:
                self.pc = (self.pc + instr.imm) & 0xFFFFFFFF
            else:
                self.pc += 4
        elif op == 'BNE':
            if self.regs[instr.rs1] != self.regs[instr.rs2]:
                self.pc = (self.pc + instr.imm) & 0xFFFFFFFF
            else:
                self.pc += 4
        elif op == 'BLT':
            if self.signed(self.regs[instr.rs1]) < self.signed(self.regs[instr.rs2]):
                self.pc = (self.pc + instr.imm) & 0xFFFFFFFF
            else:
                self.pc += 4
        elif op == 'BGE':
            if self.signed(self.regs[instr.rs1]) >= self.signed(self.regs[instr.rs2]):
                self.pc = (self.pc + instr.imm) & 0xFFFFFFFF
            else:
                self.pc += 4
        elif op == 'BLTU':
            if self.unsigned(self.regs[instr.rs1]) < self.unsigned(self.regs[instr.rs2]):
                self.pc = (self.pc + instr.imm) & 0xFFFFFFFF
            else:
                self.pc += 4
        elif op == 'BGEU':
            if self.unsigned(self.regs[instr.rs1]) >= self.unsigned(self.regs[instr.rs2]):
                self.pc = (self.pc + instr.imm) & 0xFFFFFFFF
            else:
                self.pc += 4
        
        # Jump operations
        elif op == 'JAL':
            self.regs[instr.rd] = (self.pc + 4) & 0xFFFFFFFF
            target = (self.pc + instr.imm) & 0xFFFFFFFF
            
            if self.trace:
                print(f"         JAL: jumping to 0x{target:08x}, saving PC+4=0x{self.pc+4:08x} to {self.REG_NAMES[instr.rd]}")
            
            self.pc = target
        elif op == 'JALR':
            temp = (self.pc + 4) & 0xFFFFFFFF
            target = (self.regs[instr.rs1] + instr.imm) & 0xFFFFFFFE
            
            if self.trace:
                print(f"         JALR: jumping to 0x{target:08x}, saving PC+4=0x{temp:08x} to {self.REG_NAMES[instr.rd]}")
            
            self.pc = target
            self.regs[instr.rd] = temp
        
        # Upper immediate
        elif op == 'LUI':
            self.regs[instr.rd] = (instr.imm << 12) & 0xFFFFFFFF
            self.pc += 4
        elif op == 'AUIPC':
            self.regs[instr.rd] = (self.pc + (instr.imm << 12)) & 0xFFFFFFFF
            self.pc += 4
        
        # System calls
        elif op == 'ECALL':
            self.handle_syscall()
            self.pc += 4
        elif op == 'EBREAK':
            if self.debug:
                print("EBREAK encountered")
            self.running = False
        
        else:
            raise ValueError(f"Unknown opcode: {op}")
        
        # x0 is hardwired to 0
        self.regs[0] = 0
    
    def handle_syscall(self):
        """Handle system calls (RISC-V Linux ABI)"""
        syscall_num = self.regs[17]  # a7
        
        if syscall_num == 1:  # Print integer
            val = self.signed(self.regs[10])  # a0
            print(val)
            self.output.append(str(val))
        elif syscall_num == 4:  # Print string
            addr = self.regs[10]  # a0
            chars = []
            while addr < len(self.memory):
                ch = self.memory[addr]
                if ch == 0:
                    break
                chars.append(chr(ch))
                addr = (addr + 1) & 0xFFFFFFFF
            text = ''.join(chars)
            print(text, end='')
            self.output.append(text)
        elif syscall_num == 10:  # Exit
            self.running = False
        elif syscall_num == 11:  # Print character
            ch = chr(self.regs[10] & 0xFF)
            print(ch, end='')
            self.output.append(ch)
        else:
            if self.debug:
                print(f"Unknown syscall: {syscall_num}")
    
    def print_regs(self):
        """Print register state in a compact format"""
        print("\n=== Register State ===")
        for i in range(0, 32, 4):
            line = []
            for j in range(4):
                if i + j < 32:
                    val = self.regs[i + j]
                    name = self.REG_NAMES[i + j]
                    line.append(f"{name:4s}=0x{val:08x}")
            print("  ".join(line))
        print()
    
    def dump_memory(self, start: int, length: int):
        """Dump memory region"""
        print(f"\n=== Memory Dump [0x{start:04x} - 0x{start+length:04x}] ===")
        for i in range(start, start + length, 16):
            hex_vals = ' '.join(f'{self.memory[j]:02x}' for j in range(i, min(i+16, start+length)))
            ascii_vals = ''.join(chr(self.memory[j]) if 32 <= self.memory[j] < 127 else '.' 
                                 for j in range(i, min(i+16, start+length)))
            print(f"0x{i:04x}: {hex_vals:47s}  {ascii_vals}")
        print()


def main():
    parser = argparse.ArgumentParser(description='RISC-V RV32IM Virtual Machine')
    parser.add_argument('binary', help='Binary file to execute')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('-t', '--trace', action='store_true', help='Trace instruction execution')
    parser.add_argument('-r', '--regs', action='store_true', help='Print final register state')
    parser.add_argument('-m', '--memdump', help='Dump memory region (format: start:length in hex)')
    
    args = parser.parse_args()
    
    # Create VM
    vm = RISCVVM(debug=args.debug, trace=args.trace)
    
    # Load program
    vm.load_program(args.binary)
    
    # Execute
    try:
        vm.execute()
    except KeyboardInterrupt:
        print("\n\nExecution interrupted by user")
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
    
    # Print registers if requested
    if args.regs or args.debug:
        vm.print_regs()
    
    # Memory dump if requested
    if args.memdump:
        parts = args.memdump.split(':')
        start = int(parts[0], 16)
        length = int(parts[1], 16) if len(parts) > 1 else 64
        vm.dump_memory(start, length)


if __name__ == "__main__":
    main()
