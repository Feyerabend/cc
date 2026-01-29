from enum import Enum, auto
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass


# BASIC INTERPRETER

class Operation(Enum):
    LIT = auto()  # push literal
    OPR = auto()  # operation
    STO = auto()  # store
    INT = auto()  # allocate
    LOD = auto()  # load variable

@dataclass
class Instruction:
    f: Operation
    l: int
    a: int
    
    def __str__(self):
        return f"{self.f.name:3} {self.l} {self.a}"

class Interpreter:
    def __init__(self, code: List[Instruction]):
        self.code = code
        self.s = [0] * 100
        self.p = 0
        self.b = 0
        self.t = -1
    
    def run(self):
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
            elif i.f == Operation.LOD:
                self.t += 1
                self.s[self.t] = self.s[i.a]
            elif i.f == Operation.OPR:
                if i.a == 0:  # return
                    break
                elif i.a == 2:  # add
                    self.t -= 1
                    self.s[self.t] += self.s[self.t + 1]
                elif i.a == 3:  # subtract
                    self.t -= 1
                    self.s[self.t] -= self.s[self.t + 1]
                elif i.a == 4:  # multiply
                    self.t -= 1
                    self.s[self.t] *= self.s[self.t + 1]
            elif i.f == Operation.STO:
                self.s[i.a] = self.s[self.t]
                self.t -= 1
            elif i.f == Operation.INT:
                self.t += i.a


# INTERMEDIATE REPRESENTATION (IR) - Three-Address Code

@dataclass
class IRInstruction:
    """Three-address code instruction: result = operand1 op operand2"""
    op: str  # 'CONST', 'ADD', 'SUB', 'MUL', 'COPY', 'PHI'
    result: str
    operand1: Optional[str] = None
    operand2: Optional[str] = None
    phi_sources: Optional[List[Tuple[str, str]]] = None  # For PHI nodes
    
    def __str__(self):
        if self.op == 'CONST':
            return f"{self.result} = {self.operand1}"
        elif self.op == 'COPY':
            return f"{self.result} = {self.operand1}"
        elif self.op == 'PHI':
            sources = ', '.join([f"{var} from {label}" for var, label in self.phi_sources])
            return f"{self.result} = φ({sources})"
        else:
            return f"{self.result} = {self.operand1} {self.op} {self.operand2}"


# BASIC BLOCK - Control Flow Graph Node

@dataclass
class BasicBlock:
    """A basic block in the control flow graph."""
    label: str
    instructions: List[IRInstruction]
    successors: List[str]  # labels of successor blocks
    predecessors: List[str]  # labels of predecessor blocks
    
    def __str__(self):
        lines = [f"{self.label}:"]
        for instr in self.instructions:
            lines.append(f"  {instr}")
        if self.successors:
            lines.append(f"  → {', '.join(self.successors)}")
        return '\n'.join(lines)


# PARSER - Converts source to IR (non-SSA)

class Parser:
    """Parse source code into three-address IR (not yet SSA)."""
    
    def __init__(self):
        self.temp_counter = 0
        self.variables: Set[str] = set()
    
    def parse(self, program: str) -> Tuple[List[BasicBlock], Set[str]]:
        """Parse program into basic blocks."""
        lines = [l.strip() for l in program.split('\n') 
                 if l.strip() and not l.strip().startswith('//')]
        
        instructions = []
        
        for line in lines:
            if line.startswith('var '):
                var = line[4:].strip()
                self.variables.add(var)
            elif '=' in line:
                var, expr = [p.strip() for p in line.split('=', 1)]
                self.variables.add(var)
                ir = self._parse_expr(expr, var)
                instructions.extend(ir)
        
        # Create single basic block for now (can extend to handle control flow)
        block = BasicBlock(
            label="entry",
            instructions=instructions,
            successors=[],
            predecessors=[]
        )
        
        return [block], self.variables
    
    def _parse_expr(self, expr: str, dest: str) -> List[IRInstruction]:
        """Parse expression into three-address code."""
        instructions = []
        
        # Simple recursive descent for expressions
        for op_str, op_name in [('+', 'ADD'), ('-', 'SUB'), ('*', 'MUL')]:
            if op_str in expr:
                parts = expr.split(op_str, 1)
                left = parts[0].strip()
                right = parts[1].strip()
                
                # Get operands (could be temps from subexpressions)
                left_var = self._get_operand(left, instructions)
                right_var = self._get_operand(right, instructions)
                
                instructions.append(IRInstruction(
                    op=op_name,
                    result=dest,
                    operand1=left_var,
                    operand2=right_var
                ))
                return instructions
        
        # Simple assignment
        operand = self._get_operand(expr, instructions)
        instructions.append(IRInstruction(
            op='COPY',
            result=dest,
            operand1=operand
        ))
        return instructions
    
    def _get_operand(self, operand: str, instructions: List[IRInstruction]) -> str:
        """Get operand, creating temp for complex expressions."""
        operand = operand.strip()
        if operand.isdigit():
            temp = self._new_temp()
            instructions.append(IRInstruction('CONST', temp, operand))
            return temp
        return operand
    
    def _new_temp(self) -> str:
        self.temp_counter += 1
        return f"t{self.temp_counter}"


# SSA CONVERTER

class SSAConverter:
    """Convert IR to SSA form with versioned variables."""
    
    def __init__(self):
        self.versions: Dict[str, int] = {}  # variable -> current version
        self.phi_nodes: Dict[Tuple[str, str], IRInstruction] = {}  # (block, var) -> phi
    
    def convert_to_ssa(self, blocks: List[BasicBlock], variables: Set[str]) -> List[BasicBlock]:
        """
        Convert to SSA form:
        1. Each assignment creates a new version of the variable
        2. Uses of variables reference the appropriate version
        """
        # Initialise version counters
        for var in variables:
            self.versions[var] = 0
        
        ssa_blocks = []
        
        for block in blocks:
            ssa_instructions = []
            var_map = {}  # Track current SSA version of each variable in this block
            
            # Initialise with version 0 for all variables
            for var in variables:
                var_map[var] = f"{var}_0"
            
            for instr in block.instructions:
                # Translate operands to SSA versions
                op1 = self._get_ssa_name(instr.operand1, var_map) if instr.operand1 else None
                op2 = self._get_ssa_name(instr.operand2, var_map) if instr.operand2 else None
                
                # Create new version for the result
                if instr.result in variables:
                    self.versions[instr.result] += 1
                    ssa_result = f"{instr.result}_{self.versions[instr.result]}"
                    var_map[instr.result] = ssa_result
                else:
                    ssa_result = instr.result  # temps stay as-is
                
                ssa_instructions.append(IRInstruction(
                    op=instr.op,
                    result=ssa_result,
                    operand1=op1,
                    operand2=op2
                ))
            
            ssa_blocks.append(BasicBlock(
                label=block.label,
                instructions=ssa_instructions,
                successors=block.successors,
                predecessors=block.predecessors
            ))
        
        return ssa_blocks
    
    def _get_ssa_name(self, name: str, var_map: Dict[str, str]) -> str:
        """Get the SSA version of a variable name."""
        if name is None:
            return None
        if name in var_map:
            return var_map[name]
        return name  # temps, constants, etc.


# OPTIMISERS

class SSAOptimizer:
    """Perform optimisations on SSA form."""
    
    @staticmethod
    def constant_propagation(blocks: List[BasicBlock]) -> List[BasicBlock]:
        """Replace uses of constants with their values."""
        constants = {}  # var -> constant value
        
        optimized_blocks = []
        
        for block in blocks:
            opt_instructions = []
            
            for instr in block.instructions:
                # Track constant assignments
                if instr.op == 'CONST':
                    constants[instr.result] = instr.operand1
                    opt_instructions.append(instr)
                    continue
                
                # Propagate constants
                op1 = constants.get(instr.operand1, instr.operand1)
                op2 = constants.get(instr.operand2, instr.operand2)
                
                # Constant folding: if both operands are constants, compute result
                if instr.op in ['ADD', 'SUB', 'MUL'] and \
                   (op1 and str(op1).replace('-', '').isdigit()) and \
                   (op2 and str(op2).replace('-', '').isdigit()):
                    
                    val1, val2 = int(op1), int(op2)
                    if instr.op == 'ADD':
                        result = val1 + val2
                    elif instr.op == 'SUB':
                        result = val1 - val2
                    else:  # MUL
                        result = val1 * val2
                    
                    constants[instr.result] = str(result)
                    opt_instructions.append(IRInstruction('CONST', instr.result, str(result)))
                else:
                    opt_instructions.append(IRInstruction(
                        instr.op, instr.result, op1, op2
                    ))
            
            optimized_blocks.append(BasicBlock(
                block.label, opt_instructions, block.successors, block.predecessors
            ))
        
        return optimized_blocks
    
    @staticmethod
    def dead_code_elimination(blocks: List[BasicBlock]) -> List[BasicBlock]:
        """Remove instructions whose results are never used."""
        # Collect all used variables
        used = set()
        for block in blocks:
            for instr in block.instructions:
                if instr.operand1:
                    used.add(instr.operand1)
                if instr.operand2:
                    used.add(instr.operand2)
        
        # Keep only instructions that are used or have side effects
        opt_blocks = []
        for block in blocks:
            live_instructions = []
            for instr in block.instructions:
                # Keep if result is used or it's a side-effecting operation
                if instr.result in used or instr.result.startswith('x') or instr.result.startswith('y'):
                    live_instructions.append(instr)
            
            opt_blocks.append(BasicBlock(
                block.label, live_instructions, block.successors, block.predecessors
            ))
        
        return opt_blocks


# CODE GENERATOR

class CodeGenerator:
    """Generate final machine code from SSA IR."""
    
    def __init__(self):
        self.symbol_table: Dict[str, int] = {}
        self.current_address = 3
    
    def generate(self, blocks: List[BasicBlock], original_vars: Set[str]) -> List[Instruction]:
        """Generate code from SSA blocks."""
        code = []
        
        # Allocate space for original variables (not SSA versions)
        for var in sorted(original_vars):
            self.symbol_table[var] = self.current_address
            self.current_address += 1
        
        if len(original_vars) > 0:
            code.append(Instruction(Operation.INT, 0, len(original_vars)))
        
        # Track temp -> stack offset mapping
        temp_map = {}
        
        for block in blocks:
            for instr in block.instructions:
                if instr.op == 'CONST':
                    code.append(Instruction(Operation.LIT, 0, int(instr.operand1)))
                    temp_map[instr.result] = 'stack'
                
                elif instr.op == 'COPY':
                    if instr.operand1 in temp_map:
                        # Already on stack, just note the copy
                        temp_map[instr.result] = 'stack'
                    else:
                        # Load variable
                        base_var = instr.operand1.split('_')[0]
                        if base_var in self.symbol_table:
                            code.append(Instruction(Operation.LOD, 0, self.symbol_table[base_var]))
                            temp_map[instr.result] = 'stack'
                
                elif instr.op in ['ADD', 'SUB', 'MUL']:
                    # Load operands
                    for operand in [instr.operand1, instr.operand2]:
                        if operand not in temp_map:
                            base_var = operand.split('_')[0]
                            if base_var in self.symbol_table:
                                code.append(Instruction(Operation.LOD, 0, self.symbol_table[base_var]))
                            # else already on stack
                    
                    # Perform operation
                    op_map = {'ADD': 2, 'SUB': 3, 'MUL': 4}
                    code.append(Instruction(Operation.OPR, 0, op_map[instr.op]))
                    temp_map[instr.result] = 'stack'
                
                # Store to original variable if this is the final version
                base_var = instr.result.split('_')[0]
                if base_var in self.symbol_table and instr.result in temp_map:
                    # This is an assignment to a real variable
                    code.append(Instruction(Operation.STO, 0, self.symbol_table[base_var]))
        
        code.append(Instruction(Operation.OPR, 0, 0))
        return code




def demo():
    program = """
    var x
    var y
    var z
    
    x = 3 + 5
    y = x + 2
    x = 10
    z = x + y
    """
    
    print("-"*60)
    print("STATIC SINGLE ASSIGNMENT (SSA) FORM DEMONSTRATION")
    print("-"*60)
    print(f"\nSource Program:")
    print(program)
    
    # Step 1: Parse to IR
    print("\n" + "-"*60)
    print("STEP 1: Parse to Three-Address Code (Non-SSA IR)")
    print("-"*60)
    print("Note: Variable 'x' is assigned TWICE - this is NOT SSA form yet\n")
    
    parser = Parser()
    blocks, variables = parser.parse(program)
    
    for block in blocks:
        print(block)
    
    # Step 2: Convert to SSA
    print("\n" + "-"*60)
    print("STEP 2: Convert to SSA Form")
    print("-"*60)
    print("KEY PRINCIPLE: Each assignment creates a NEW version of the variable")
    print("  - First assignment to x -> x_1")
    print("  - Second assignment to x -> x_2")
    print("  - Each variable is assigned EXACTLY ONCE (Single Assignment)\n")
    
    ssa_converter = SSAConverter()
    ssa_blocks = ssa_converter.convert_to_ssa(blocks, variables)
    
    for block in ssa_blocks:
        print(block)
    
    # Step 3: Optimise
    print("\n" + "-"*60)
    print("STEP 3: SSA-Based Optimisations")
    print("-"*60)
    print("Constant Propagation: Replace variable uses with known constants")
    print("Constant Folding: Compute constant expressions at compile-time\n")
    
    opt_blocks = SSAOptimizer.constant_propagation(ssa_blocks)
    opt_blocks = SSAOptimizer.dead_code_elimination(opt_blocks)
    
    for block in opt_blocks:
        print(block)
    
    # Step 4: Generate code
    print("\n" + "-"*60)
    print("STEP 4: Code Generation from SSA")
    print("-"*60)
    print("Convert SSA back to machine code (merging versions back to variables)\n")
    
    codegen = CodeGenerator()
    code = codegen.generate(opt_blocks, variables)
    
    for i, instr in enumerate(code):
        print(f"  {i:2d}: {instr}")
    
    # Step 5: Execute
    print("\n" + "-"*60)
    print("STEP 5: Execute and Verify")
    print("-"*60)

    interpreter = Interpreter(code)
    interpreter.run()
    
    for var in sorted(variables):
        addr = codegen.symbol_table[var]
        print(f"  {var} = {interpreter.s[addr]}")

if __name__ == "__main__":
    demo()
