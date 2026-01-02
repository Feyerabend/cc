# codegen_driver.py

from ir import IRProgram
from codegen_core import CodeAlgebra


def generate(ir: IRProgram, algebra: CodeAlgebra):
    algebra.begin()
    for instr in ir.instructions:
        algebra.emit(instr)
    algebra.end()
    return algebra
