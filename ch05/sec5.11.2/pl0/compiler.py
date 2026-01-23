from typing import List, Dict
from interpreter import Operation, Instruction, Interpreter

class Compiler:
    def __init__(self):
        self.symbol_table: Dict[str, int] = {}
        self.code: List[Instruction] = []
        self.current_address = 3  # starting after SL, DL, RA
    
    def compile(self, program: str) -> List[Instruction]:
        self.symbol_table.clear()
        self.code.clear()
        
        # parse
        lines = [line.strip() for line in program.split('\n') if line.strip() and not line.strip().startswith('//')]
        
        # 1st pass - collect variables
        var_count = 0
        for line in lines:
            if line.startswith('var '):
                var_name = line[4:].strip()
                self.symbol_table[var_name] = self.current_address + var_count
                var_count += 1
        
        # allocate space for variables
        if var_count > 0:
            self.code.append(Instruction(Operation.INT, 0, var_count))
        
        # 2nd pass - process assignments
        for line in lines:
            if '=' in line:
                var_name, expr = [part.strip() for part in line.split('=', 1)]
                
                if var_name not in self.symbol_table:
                    raise ValueError(f"Undeclared variable: {var_name}")
                
                # compile expression
                self._compile_expression(expr)
                
                # store result
                var_address = self.symbol_table[var_name]
                self.code.append(Instruction(Operation.STO, 0, var_address))
        
        # add return instruction
        self.code.append(Instruction(Operation.OPR, 0, 0))
        return self.code
    
    def _compile_expression(self, expr: str):

        if '+' in expr:
            parts = expr.split('+')
            self._compile_operand(parts[0].strip())
            self._compile_operand(parts[1].strip())
            self.code.append(Instruction(Operation.OPR, 0, 2))  # add
        else:
            self._compile_operand(expr.strip())
    
    def _compile_operand(self, operand: str):
        if operand.isdigit():
            # literal
            self.code.append(Instruction(Operation.LIT, 0, int(operand)))
        else:
            # variable
            if operand not in self.symbol_table:
                raise ValueError(f"Undeclared variable: {operand}")
            # push address of variable
            self.code.append(Instruction(Operation.LIT, 0, self.symbol_table[operand]))
            # dereference address
            self.code.append(Instruction(Operation.OPR, 0, 1))

def test_compiler_and_interpreter():
    program = """
    // Variable declaration
    var x
    var y
    
    // Assignments
    x = 3 + 5
    y = x + 2
    """
    
    compiler = Compiler()
    code = compiler.compile(program)
    
    print("Generated code:")
    for i, instr in enumerate(code):
        print(f"{i}: {instr.f.name} {instr.l} {instr.a}")
    
    interpreter = Interpreter(code)
    interpreter.run()

    # print results using symbol table
    symbol_table = compiler.symbol_table
    x_address = symbol_table['x']
    y_address = symbol_table['y']
    
    print("\nExecution results:")
    print(f"x = {interpreter.s[x_address]}")
    print(f"y = {interpreter.s[y_address]}")

if __name__ == "__main__":
    test_compiler_and_interpreter()
