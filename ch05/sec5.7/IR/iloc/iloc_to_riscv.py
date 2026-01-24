from iloc_ir import ILOCInstruction, ILOCOp
from typing import List, Dict
import sys

class RISCVGenerator:
    def __init__(self):
        self.code: List[str] = []
        self.reg_map: Dict[str, str] = {}
        self.mem_map: Dict[str, int] = {}
        self.next_riscv_reg = 10
        self.next_mem_offset = 0
        self.data_segment_base = 0x2000
        
    def get_riscv_reg(self, iloc_reg: str) -> str:
        if iloc_reg not in self.reg_map:
            if self.next_riscv_reg <= 17:
                a_num = self.next_riscv_reg - 10
                self.reg_map[iloc_reg] = f"a{a_num}"
            elif self.next_riscv_reg <= 20:
                t_num = self.next_riscv_reg - 18
                self.reg_map[iloc_reg] = f"t{t_num}"
            else:
                s_num = self.next_riscv_reg - 18
                self.reg_map[iloc_reg] = f"s{s_num}"
            self.next_riscv_reg += 1
        return self.reg_map[iloc_reg]
    
    def get_mem_offset(self, loc: str) -> int:
        if loc not in self.mem_map:
            self.mem_map[loc] = self.next_mem_offset
            self.next_mem_offset += 4
        return self.mem_map[loc]
    
    def load_iloc_file(self, filename: str) -> List[ILOCInstruction]:
        instructions = []
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if ':' in line:
                    line = line.split(':', 1)[1].strip()
                
                if '=>' in line:
                    parts = line.split('=>')
                    left = parts[0].strip().split()
                    dest = parts[1].strip()
                    
                    op_str = left[0]
                    op = ILOCOp(op_str)
                    
                    if op == ILOCOp.LOADI:
                        operands = [left[1], dest]
                    elif op in [ILOCOp.LOAD, ILOCOp.STORE]:
                        operands = [left[1], dest]
                    else:
                        operands = [left[1].rstrip(','), left[2], dest]
                    
                    instructions.append(ILOCInstruction(op, operands))
        
        return instructions
    
    def generate(self, instructions: List[ILOCInstruction]) -> str:
        self.code = []
        
        self.code.append("# RISC-V assembly from ILOC")
        self.code.append("")
        self.code.append("lui s0, 0x2")
        self.code.append("")
        
        for instr in instructions:
            if instr.op == ILOCOp.LOADI:
                const, dest = instr.operands
                dest_reg = self.get_riscv_reg(dest)
                val = int(const)
                
                if -2048 <= val <= 2047:
                    self.code.append(f"addi {dest_reg}, zero, {val}")
                else:
                    upper = (val >> 12) & 0xFFFFF
                    lower = val & 0xFFF
                    if lower & 0x800:
                        upper += 1
                        lower = lower - 4096
                    self.code.append(f"lui {dest_reg}, {upper}")
                    if lower != 0:
                        self.code.append(f"addi {dest_reg}, {dest_reg}, {lower}")
            
            elif instr.op == ILOCOp.LOAD:
                src, dest = instr.operands
                dest_reg = self.get_riscv_reg(dest)
                offset = self.get_mem_offset(src)
                self.code.append(f"lw {dest_reg}, {offset}(s0)")
            
            elif instr.op == ILOCOp.STORE:
                src, dest = instr.operands
                src_reg = self.get_riscv_reg(src)
                offset = self.get_mem_offset(dest)
                self.code.append(f"sw {src_reg}, {offset}(s0)")
            
            elif instr.op == ILOCOp.ADD:
                src1, src2, dest = instr.operands
                self.code.append(f"add {self.get_riscv_reg(dest)}, {self.get_riscv_reg(src1)}, {self.get_riscv_reg(src2)}")
            
            elif instr.op == ILOCOp.SUB:
                src1, src2, dest = instr.operands
                self.code.append(f"sub {self.get_riscv_reg(dest)}, {self.get_riscv_reg(src1)}, {self.get_riscv_reg(src2)}")
            
            elif instr.op == ILOCOp.MULT:
                src1, src2, dest = instr.operands
                self.code.append(f"mul {self.get_riscv_reg(dest)}, {self.get_riscv_reg(src1)}, {self.get_riscv_reg(src2)}")
            
            elif instr.op == ILOCOp.DIV:
                src1, src2, dest = instr.operands
                self.code.append(f"div {self.get_riscv_reg(dest)}, {self.get_riscv_reg(src1)}, {self.get_riscv_reg(src2)}")
        
        self.code.append("")
        self.code.append("# Print results")
        for var, offset in sorted(self.mem_map.items(), key=lambda x: x[1]):
            var_name = var.replace('@', '')
            self.code.append(f"lw a0, {offset}(s0)")
            self.code.append(f"li a7, 1")
            self.code.append(f"ecall")
            self.code.append(f"li a0, 10")
            self.code.append(f"li a7, 11")
            self.code.append(f"ecall")
        
        self.code.append("")
        self.code.append("li a7, 10")
        self.code.append("ecall")
        
        return '\n'.join(self.code)
    
    def save_to_file(self, filename: str, asm_code: str):
        with open(filename, 'w') as f:
            f.write("# RISC-V assembly\n")
            f.write(f"# Registers:\n")
            for iloc_reg, riscv_reg in sorted(self.reg_map.items()):
                f.write(f"#   {iloc_reg} -> {riscv_reg}\n")
            f.write(f"#\n")
            f.write(f"# Memory (base 0x{self.data_segment_base:05x}):\n")
            for var, offset in sorted(self.mem_map.items(), key=lambda x: x[1]):
                var_name = var.replace('@', '')
                addr = self.data_segment_base + offset
                f.write(f"#   {var_name} @ 0x{addr:05x} (offset {offset})\n")
            f.write("#\n\n")
            f.write(asm_code)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python iloc_to_riscv.py <input.iloc> <output.s>")
        sys.exit(1)
    
    generator = RISCVGenerator()
    instructions = generator.load_iloc_file(sys.argv[1])
    asm_code = generator.generate(instructions)
    generator.save_to_file(sys.argv[2], asm_code)
    print(f"Generated {len(generator.code)} lines of RISC-V assembly -> {sys.argv[2]}")
