from dataclasses import dataclass
from typing import List
from enum import Enum

class ILOCOp(Enum):
    LOADI = "loadI"
    LOAD = "load"
    STORE = "store"
    ADD = "add"
    SUB = "sub"
    MULT = "mult"
    DIV = "div"

@dataclass
class ILOCInstruction:
    op: ILOCOp
    operands: List[str]
    
    def __str__(self):
        if self.op == ILOCOp.LOADI:
            return f"{self.op.value} {self.operands[0]} => {self.operands[1]}"
        elif self.op in [ILOCOp.LOAD, ILOCOp.STORE]:
            return f"{self.op.value} {self.operands[0]} => {self.operands[1]}"
        else:
            return f"{self.op.value} {self.operands[0]}, {self.operands[1]} => {self.operands[2]}"
