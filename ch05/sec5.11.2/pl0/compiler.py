from typing import List, Dict, Optional
from interpreter import Operation, Instruction, PL0Interpreter
import re

class Compiler:
    def __init__(self):
        self.symbol_table: Dict[str, int] = {}
        self.code: List[Instruction] = []
        self.current_address = 3  # starting after SL, DL, RA
    
    def compile(self, program: str) -> List[Instruction]:
        self.symbol_table.clear()
        self.code.clear()
        
        # parse
        lines = [line.strip() for line in program.split('\n') 
                if line.strip() and not line.strip().startswith('//')]
        
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
            if '=' in line and not line.startswith('var'):
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
        """Compile expressions with operator precedence"""
        expr = expr.strip()
        
        # Handle addition/subtraction (lowest precedence)
        for i in range(len(expr) - 1, -1, -1):
            if expr[i] in ['+', '-'] and self._not_in_parens(expr, i):
                left = expr[:i].strip()
                right = expr[i+1:].strip()
                op = expr[i]
                
                self._compile_expression(left)
                self._compile_expression(right)
                
                if op == '+':
                    self.code.append(Instruction(Operation.OPR, 0, 2))
                else:  # subtraction
                    self.code.append(Instruction(Operation.OPR, 0, 3))
                return
        
        # Handle multiplication/division (higher precedence)
        for i in range(len(expr) - 1, -1, -1):
            if expr[i] in ['*', '/'] and self._not_in_parens(expr, i):
                left = expr[:i].strip()
                right = expr[i+1:].strip()
                op = expr[i]
                
                self._compile_expression(left)
                self._compile_expression(right)
                
                if op == '*':
                    self.code.append(Instruction(Operation.OPR, 0, 4))
                else:  # division
                    self.code.append(Instruction(Operation.OPR, 0, 5))
                return
        
        # Handle comparison operators
        for op_str, op_code in [('<=', 10), ('>=', 11), ('>', 12), 
                                 ('<', 13), ('==', 8), ('!=', 9)]:
            if op_str in expr:
                parts = expr.split(op_str)
                if len(parts) == 2:
                    self._compile_expression(parts[0].strip())
                    self._compile_expression(parts[1].strip())
                    self.code.append(Instruction(Operation.OPR, 0, op_code))
                    return
        
        # Handle parentheses
        if expr.startswith('(') and expr.endswith(')'):
            self._compile_expression(expr[1:-1])
            return
        
        # Handle operands (literals or variables)
        self._compile_operand(expr)
    
    def _not_in_parens(self, expr: str, pos: int) -> bool:
        """Check if position is not inside parentheses"""
        depth = 0
        for i in range(pos):
            if expr[i] == '(':
                depth += 1
            elif expr[i] == ')':
                depth -= 1
        return depth == 0
    
    def _compile_operand(self, operand: str):
        operand = operand.strip()
        
        if operand.isdigit() or (operand.startswith('-') and operand[1:].isdigit()):
            # literal number
            self.code.append(Instruction(Operation.LIT, 0, int(operand)))
        elif operand in self.symbol_table:
            # variable - load its value
            var_address = self.symbol_table[operand]
            self.code.append(Instruction(Operation.LOD, 0, var_address))
        else:
            raise ValueError(f"Undeclared variable or invalid operand: {operand}")


def test_compiler_and_interpreter():
    program = """
    // Variable declaration
    var x
    var y
    var z
    
    // Assignments
    x = 3 + 5
    y = x + 2
    z = x * y - 1
    """
    
    compiler = Compiler()
    code = compiler.compile(program)
    
    print("Generated code:")
    for i, instr in enumerate(code):
        print(f"{i}: {instr.op.name} {instr.l} {instr.a}")
    
    interpreter = PL0Interpreter(code, stack_size=1000)
    interpreter.debug = False
    interpreter.run()

    # print results using symbol table
    symbol_table = compiler.symbol_table
    
    print("\nExecution results:")
    for var_name, address in sorted(symbol_table.items()):
        print(f"{var_name} = {interpreter.s[address]}")


def test_complex_expressions():
    program = """
    var a
    var b
    var c
    var result
    
    a = 10
    b = 5
    c = 2
    result = a * b - c * 3
    """
    
    print("\n" + "="*50)
    print("Testing complex expressions:")
    print("="*50)
    
    compiler = Compiler()
    code = compiler.compile(program)
    
    print("\nGenerated code:")
    for i, instr in enumerate(code):
        print(f"{i}: {instr.op.name} {instr.l} {instr.a}")
    
    interpreter = PL0Interpreter(code, stack_size=1000)
    interpreter.debug = False
    interpreter.run()
    
    print("\nExecution results:")
    for var_name, address in sorted(compiler.symbol_table.items()):
        print(f"{var_name} = {interpreter.s[address]}")
    print(f"Expected result: 10 * 5 - 2 * 3 = 50 - 6 = 44")


if __name__ == "__main__":
    test_compiler_and_interpreter()
    test_complex_expressions()
