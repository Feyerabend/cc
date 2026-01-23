from enum import Enum, auto
from typing import List

class Operation(Enum):
    LIT = auto()  # push literal
    OPR = auto()  # operation
    STO = auto()  # store
    INT = auto()  # allocate

class Instruction:
    def __init__(self, f: Operation, l: int, a: int):
        self.f = f
        self.l = l
        self.a = a

class Interpreter:
    def __init__(self, code: List[Instruction]):
        self.code = code
        self.s = [0] * 100  # larger stack
        self.p = 0  # program counter
        self.b = 0  # base pointer
        self.t = -1 # stack pointer
    
    def run(self):
        # init stack frame
        self.t = 2
        self.s[0] = 0  # SL
        self.s[1] = 0  # DL
        self.s[2] = 0  # RA
        
        while self.p < len(self.code):
            i = self.code[self.p]
            self.p += 1
            
            if i.f == Operation.LIT:
                self.t += 1
                self.s[self.t] = i.a
            
            elif i.f == Operation.OPR:
                if i.a == 0:  # return
                    break
                elif i.a == 1:  # load (dereference)
                    self.s[self.t] = self.s[self.s[self.t]]
                elif i.a == 2:  # add
                    self.t -= 1
                    self.s[self.t] += self.s[self.t + 1]
            
            elif i.f == Operation.STO:
                self.s[i.a] = self.s[self.t]
                self.t -= 1
            
            elif i.f == Operation.INT:
                self.t += i.a

def test():
    # x = 3 + 5
    code = [
        Instruction(Operation.INT, 0, 1),  # allocate 1 variable
        Instruction(Operation.LIT, 0, 3),
        Instruction(Operation.LIT, 0, 5),
        Instruction(Operation.OPR, 0, 2),  # add
        Instruction(Operation.STO, 0, 3),  # store at address 3
        Instruction(Operation.OPR, 0, 0)   # return
    ]
    
    interpreter = Interpreter(code)
    interpreter.run()
    print(f"Result at address 3: {interpreter.s[3]}")

if __name__ == "__main__":
    test()
