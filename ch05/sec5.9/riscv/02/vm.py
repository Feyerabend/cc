#!/usr/bin/env python3
"""
RISC-V RV32I Virtual Machine
Loads and executes binary machine code file
"""

import sys
import struct
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


class RISCVVM:
    """RISC-V Virtual Machine (RV32I + M extension)"""
    
    def __init__(self, mem_size: int = 65536):
        self.regs = [0] * 32  # 32 general-purpose registers, stored as unsigned 0-2**32-1
        self.pc = 0           # Program counter
        self.memory = bytearray(mem_size)  # Main memory
        self.running = True
        self.output = []
        
    def reset(self):
        """Reset VM state"""
        self.regs = [0] * 32
        self.pc = 0
        self.memory = bytearray(len(self.memory))
        self.running = True
        self.output = []
    
    def load_program(self, filename: str):
        """Load binary program into memory at address 0"""
        with open(filename, 'rb') as f:
            program = f.read()
        if len(program) % 4 != 0:
            raise ValueError("Binary size not multiple of 4 bytes")
        self.memory[0:len(program)] = program
    
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
            raise ValueError(f"Memory access out of bounds: {addr}")
        
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
            raise ValueError(f"Memory access out of bounds: {addr}")
        
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

        if opcode == 0b0110011:  # R-type
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
            elif funct7 == 0b0000001:
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

        elif opcode == 0b0010011:  # I-type (arith/shifts)
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

        elif opcode == 0b0000011:  # Loads
            imm = word >> 20
            imm = self.sign_extend(imm, 12)
            if funct3 == 0b000: op = 'LB'
            elif funct3 == 0b001: op = 'LH'
            elif funct3 == 0b010: op = 'LW'
            elif funct3 == 0b100: op = 'LBU'
            elif funct3 == 0b101: op = 'LHU'
            else: raise ValueError("Unknown load funct3")
            return Instruction(op, rd=rd, rs1=rs1, imm=imm, funct3=funct3)

        elif opcode == 0b0100011:  # Stores
            imm = ((word >> 25) & 0x7F) << 5 | ((word >> 7) & 0x1F)
            imm = self.sign_extend(imm, 12)
            if funct3 == 0b000: op = 'SB'
            elif funct3 == 0b001: op = 'SH'
            elif funct3 == 0b010: op = 'SW'
            else: raise ValueError("Unknown store funct3")
            return Instruction(op, rs1=rs1, rs2=rs2, imm=imm, funct3=funct3)

        elif opcode == 0b1100011:  # Branches
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

        elif opcode == 0b1101111:  # JAL
            imm = ((word >> 31) & 1) << 20 | ((word >> 12) & 0xFF) << 12 | \
                  ((word >> 20) & 1) << 11 | ((word >> 21) & 0x3FF) << 1
            imm = self.sign_extend(imm, 21)
            return Instruction('JAL', rd=rd, imm=imm)

        elif opcode == 0b1100111:  # JALR
            imm = word >> 20
            imm = self.sign_extend(imm, 12)
            if funct3 != 0b000:
                raise ValueError("Invalid JALR funct3")
            return Instruction('JALR', rd=rd, rs1=rs1, imm=imm, funct3=0b000)

        elif opcode == 0b0110111:  # LUI
            imm = (word >> 12) & 0xFFFFF
            return Instruction('LUI', rd=rd, imm=imm)

        elif opcode == 0b0010111:  # AUIPC
            imm = (word >> 12) & 0xFFFFF
            return Instruction('AUIPC', rd=rd, imm=imm)

        elif opcode == 0b1110011:  # SYSTEM
            imm12 = word >> 20
            if funct3 == 0b000 and rd == 0 and rs1 == 0:
                if imm12 == 0: op = 'ECALL'
                elif imm12 == 1: op = 'EBREAK'
                else: raise ValueError("Unknown system imm")
            else:
                raise ValueError("Unknown system instruction")
            return Instruction(op, funct3=0b000)

        raise ValueError(f"Unknown opcode: {bin(opcode)}")
    
    def execute(self, debug: bool = False):
        """Execute program loaded in memory"""
        self.running = True
        
        max_cycles = 100000
        cycles = 0
        
        while self.running and cycles < max_cycles and self.pc < len(self.memory):
            if self.pc % 4 != 0:
                raise ValueError("PC not aligned")
            instr_word = struct.unpack_from('<I', self.memory, self.pc)[0]
            instr = self.decode(instr_word)
            
            if debug:
                print(f"PC={self.pc:04x} {instr.opcode} ", end='')
            
            self.execute_instruction(instr)
            
            if debug:
                self.print_regs()
            
            cycles += 1
        
        if cycles >= max_cycles:
            print(f"Warning: Max cycles ({max_cycles}) reached")
    
    def execute_instruction(self, instr: Instruction):
        """Execute a single instruction"""
        op = instr.opcode
        
        # x0 always 0
        self.regs[0] = 0
        
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
            shift = self.regs[instr.rs2] & 0x1F
            self.regs[instr.rd] = (self.regs[instr.rs1] << shift) & 0xFFFFFFFF
            self.pc += 4
        elif op == 'SRL':
            shift = self.regs[instr.rs2] & 0x1F
            self.regs[instr.rd] = (self.unsigned(self.regs[instr.rs1]) >> shift) & 0xFFFFFFFF
            self.pc += 4
        elif op == 'SRA':
            shift = self.regs[instr.rs2] & 0x1F
            self.regs[instr.rd] = (self.signed(self.regs[instr.rs1]) >> shift) & 0xFFFFFFFF
            self.pc += 4
        elif op == 'SLT':
            self.regs[instr.rd] = 1 if self.signed(self.regs[instr.rs1]) < self.signed(self.regs[instr.rs2]) else 0
            self.pc += 4
        elif op == 'SLTU':
            self.regs[instr.rd] = 1 if self.unsigned(self.regs[instr.rs1]) < self.unsigned(self.regs[instr.rs2]) else 0
            self.pc += 4
        
        # M extension
        elif op == 'MUL':
            prod = self.signed(self.regs[instr.rs1]) * self.signed(self.regs[instr.rs2])
            self.regs[instr.rd] = prod & 0xFFFFFFFF
            self.pc += 4
        elif op == 'MULH':
            prod = self.signed(self.regs[instr.rs1]) * self.signed(self.regs[instr.rs2])
            self.regs[instr.rd] = (prod >> 32) & 0xFFFFFFFF
            self.pc += 4
        elif op == 'MULHSU':
            prod = self.signed(self.regs[instr.rs1]) * self.unsigned(self.regs[instr.rs2])
            self.regs[instr.rd] = (prod >> 32) & 0xFFFFFFFF
            self.pc += 4
        elif op == 'MULHU':
            prod = self.unsigned(self.regs[instr.rs1]) * self.unsigned(self.regs[instr.rs2])
            self.regs[instr.rd] = (prod >> 32) & 0xFFFFFFFF
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
            self.regs[instr.rd] = self.read_mem(addr, 4) & 0xFFFFFFFF
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
            self.pc = (self.pc + instr.imm) & 0xFFFFFFFF
        elif op == 'JALR':
            temp = (self.pc + 4) & 0xFFFFFFFF
            self.pc = (self.regs[instr.rs1] + instr.imm) & 0xFFFFFFFE
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
            print("EBREAK encountered")
            self.running = False
        
        else:
            raise ValueError(f"Unknown opcode: {op}")
        
        # x0 is hardwired to 0
        self.regs[0] = 0
    
    def handle_syscall(self):
        """Handle system calls (simplified)"""
        syscall_num = self.regs[17]  # a7
        
        if syscall_num == 1:  # Print integer
            val = self.signed(self.regs[10])  # a0
            print(val)
            self.output.append(str(val))
        elif syscall_num == 4:  # Print string
            addr = self.regs[10]  # a0
            chars = []
            while True:
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
    
    def print_regs(self):
        """Print register state"""
        names = ['zero', 'ra', 'sp', 'gp', 'tp', 't0', 't1', 't2',
                's0', 's1', 'a0', 'a1', 'a2', 'a3', 'a4', 'a5',
                'a6', 'a7', 's2', 's3', 's4', 's5', 's6', 's7',
                's8', 's9', 's10', 's11', 't3', 't4', 't5', 't6']
        
        for i in range(0, 32, 4):
            line = []
            for j in range(4):
                if i + j < 32:
                    val = self.signed(self.regs[i + j])
                    line.append(f"{names[i+j]:4s}={val:6d}")
            print("  ".join(line))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python vm.py program.bin [-d for debug]")
        sys.exit(1)
    
    debug = len(sys.argv) > 2 and sys.argv[2] == '-d'
    
    vm = RISCVVM()
    vm.load_program(sys.argv[1])
    vm.execute(debug=debug)
