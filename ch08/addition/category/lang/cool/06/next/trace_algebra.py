# trace_algebra.py

from codegen_core import CodeAlgebra
from codegen_state import CodeState
from ir import IRInstr


class TraceAlgebra(CodeAlgebra):
    """
    Code algebra that records a trace of IR execution.
    Used ONLY for testing correctness.
    """

    def __init__(self):
        self.state = CodeState()

    def begin(self):
        self.state.declarations.append("BEGIN")

    def emit(self, instr: IRInstr):
        self.state.statements.append(f"OP: {instr.op}")

    def end(self):
        self.state.statements.append("END")
