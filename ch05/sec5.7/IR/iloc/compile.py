import sys
import os
from pathlib import Path

def run_pipeline(output_dir="build"):
    Path(output_dir).mkdir(exist_ok=True)
    
    print("=" * 70)
    print("COMPILATION PIPELINE")
    print("=" * 70)
    
    print("\n[1/3] AST → ILOC")
    from example_program import create_program_ast
    from ast_to_iloc import ILOCGenerator
    
    ast = create_program_ast()
    iloc_gen = ILOCGenerator()
    iloc_gen.generate(ast)
    
    iloc_file = f"{output_dir}/program.iloc"
    iloc_gen.save_to_file(iloc_file)
    print(f"  → {iloc_file}")
    
    print("\n[2/3] ILOC → RISC-V")
    from iloc_to_riscv import RISCVGenerator
    
    riscv_gen = RISCVGenerator()
    instructions = riscv_gen.load_iloc_file(iloc_file)
    asm_code = riscv_gen.generate(instructions)
    
    asm_file = f"{output_dir}/program.s"
    riscv_gen.save_to_file(asm_file, asm_code)
    print(f"  → {asm_file}")
    
    print("\n[3/3] RISC-V → Binary")
    from asm import RISCVAssembler
    
    with open(asm_file, 'r') as f:
        source = f.read()
    
    assembler = RISCVAssembler()
    binary = assembler.assemble(source)
    
    bin_file = f"{output_dir}/program.bin"
    with open(bin_file, 'wb') as f:
        f.write(binary)
    
    print(f"  → {bin_file}")
    
    print("\n" + "=" * 70)
    print("BUILD COMPLETE")
    print("=" * 70)
    print(f"\nExecute: python vm.py {bin_file}")
    print("=" * 70)
    
    return bin_file

if __name__ == "__main__":
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "build"
    run_pipeline(output_dir)
