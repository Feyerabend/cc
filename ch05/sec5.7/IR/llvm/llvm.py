"""
AST to LLVM IR Generator
Demonstrates: AST -> Three-Address Code (TAC) -> LLVM IR
"""

from typing import List, Optional, Dict



class ASTNode:
    def __init__(self, kind: str, value=None, children: List['ASTNode'] = None):
        self.kind = kind
        self.value = value
        self.children = children if children else []
    
    def __repr__(self, level=0):
        indent = "  " * level
        result = f"{indent}ASTNode(kind={self.kind}"
        if self.value is not None:
            result += f", value={self.value}"
        result += ")"
        
        if self.children:
            result += " {\n"
            for child in self.children:
                result += child.__repr__(level + 1) + "\n"
            result += f"{indent}}}"
        
        return result



class TACGenerator:
    """
    Generates Three-Address Code (TAC) from AST
    TAC is an intermediate representation where each instruction has at most 3 operands
    Example: t1 = a + b
    """
    
    def __init__(self):
        self.instructions: List[str] = []
        self.temp_counter = 0
        self.variables: Dict[str, str] = {}  # Track variable types/info
    
    def new_temp(self) -> str:
        self.temp_counter += 1
        return f"t{self.temp_counter}"
    
    def generate(self, node: ASTNode) -> Optional[str]:
        """
        Generate TAC for an AST node
        Returns the result variable/temporary for expressions
        """
        
        # Program: process all children
        if node.kind == "PROGRAM":
            for child in node.children:
                self.generate(child)
            return None
        
        # Assignment: var = expr
        elif node.kind == "ASSIGN":
            var_name = node.children[0].value
            expr_result = self.generate(node.children[1])
            self.instructions.append(f"{var_name} = {expr_result}")
            self.variables[var_name] = "i32"  # Track variable
            return None
        
        # Binary operations
        elif node.kind in {"PLUS", "MINUS", "TIMES", "DIVIDE"}:
            left = self.generate(node.children[0])
            right = self.generate(node.children[1])
            temp = self.new_temp()
            
            op_map = {
                "PLUS": "+",
                "MINUS": "-",
                "TIMES": "*",
                "DIVIDE": "/"
            }
            
            self.instructions.append(f"{temp} = {left} {op_map[node.kind]} {right}")
            return temp
        
        # Leaf nodes
        elif node.kind == "NUMBER":
            return str(node.value)
        
        elif node.kind == "IDENTIFIER":
            return node.value
        
        else:
            raise ValueError(f"Unknown AST node kind: {node.kind}")
    
    def get_instructions(self) -> List[str]:
        return self.instructions
    
    def display(self):
        print("\n Three-Address Code (TAC) ")
        for i, instr in enumerate(self.instructions, 1):
            print(f"  {i}. {instr}")



class LLVMIRGenerator:
    """
    Generates LLVM IR from Three-Address Code
    LLVM IR is a low-level intermediate representation used by LLVM compiler
    """
    
    def __init__(self, tac_instructions: List[str], variables: Dict[str, str]):
        self.tac = tac_instructions
        self.variables = variables
        self.ir: List[str] = []
        self.allocated_vars: set = set()
    
    def generate(self):
        # Function header
        self.ir.append("define i32 @main() {")
        self.ir.append("entry:")
        
        # Allocate stack space for variables (not temporaries)
        for var in self.variables:
            self.ir.append(f"  %{var}_ptr = alloca i32")
            self.allocated_vars.add(var)
        
        # Translate each TAC instruction
        for instruction in self.tac:
            self._translate_instruction(instruction)
        
        # Return 0
        self.ir.append("  ret i32 0")
        self.ir.append("}")
    
    def _translate_instruction(self, instruction: str):
        parts = instruction.split(" = ", 1)
        if len(parts) != 2:
            return
        
        lhs = parts[0].strip()
        rhs = parts[1].strip()
        
        # Check if RHS is a simple constant
        if rhs.isdigit() or (rhs.startswith('-') and rhs[1:].isdigit()):
            # Simple assignment: var = constant
            if lhs in self.variables:
                self.ir.append(f"  store i32 {rhs}, i32* %{lhs}_ptr")
            else:
                # Temporary: just use SSA form
                self.ir.append(f"  %{lhs} = add i32 0, {rhs}")
        
        # Check if RHS is a simple variable
        elif rhs in self.variables:
            # var1 = var2
            loaded = self._load_variable(rhs)
            if lhs in self.variables:
                self.ir.append(f"  store i32 %{loaded}, i32* %{lhs}_ptr")
            else:
                self.ir.append(f"  %{lhs} = add i32 0, %{loaded}")
        
        # Check if RHS is an expression (e.g., "a + b")
        else:
            self._translate_expression(lhs, rhs)
    
    # Translate an expression (e.g., "a + b") to LLVM IR
    def _translate_expression(self, lhs: str, rhs: str):
        tokens = rhs.split()
        if len(tokens) != 3:
            return
        
        left_operand, operator, right_operand = tokens
        
        # Load operands
        left_val = self._get_operand(left_operand)
        right_val = self._get_operand(right_operand)
        
        # Generate operation
        op_map = {
            "+": "add",
            "-": "sub",
            "*": "mul",
            "/": "sdiv"  # signed division
        }
        
        if operator in op_map:
            llvm_op = op_map[operator]
            
            if lhs in self.variables:
                # Store to variable
                temp = f"{lhs}_calc"
                self.ir.append(f"  %{temp} = {llvm_op} i32 {left_val}, {right_val}")
                self.ir.append(f"  store i32 %{temp}, i32* %{lhs}_ptr")
            else:
                # Store to temporary
                self.ir.append(f"  %{lhs} = {llvm_op} i32 {left_val}, {right_val}")
    
    def _get_operand(self, operand: str) -> str:
        # If it's a number, return as-is
        if operand.isdigit() or (operand.startswith('-') and operand[1:].isdigit()):
            return operand
        
        # If it's a variable, load it
        if operand in self.variables:
            return f"%{self._load_variable(operand)}"
        
        # Otherwise it's a temporary
        return f"%{operand}"
    
    def _load_variable(self, var_name: str) -> str:
        load_temp = f"{var_name}_load"
        self.ir.append(f"  %{load_temp} = load i32, i32* %{var_name}_ptr")
        return load_temp
    
    def get_ir(self) -> List[str]:
        return self.ir
    
    def display(self):
        print("\n LLVM IR Code ")
        for line in self.ir:
            print(line)



class SimpleCompiler:
    def __init__(self, ast: ASTNode):
        self.ast = ast
        self.tac_gen = TACGenerator()
        self.llvm_gen = None
    
    def compile(self):
        print("-"*40)
        print("COMPILER PIPELINE DEMONSTRATION")
        print("-"*40)
        
        # Step 1: Display AST
        print("\n Input: Abstract Syntax Tree (AST) ")
        print(self.ast)
        
        # Step 2: Generate TAC
        self.tac_gen.generate(self.ast)
        self.tac_gen.display()
        
        # Step 3: Generate LLVM IR
        self.llvm_gen = LLVMIRGenerator(
            self.tac_gen.get_instructions(),
            self.tac_gen.variables
        )
        self.llvm_gen.generate()
        self.llvm_gen.display()



def sample_simple():
    print("\n" + "-"*40)
    print("SAMPLE 1: Simple Arithmetic (x = 10 + 5)")
    print("-"*40)
    
    ast = ASTNode(kind="PROGRAM", children=[
        ASTNode(kind="ASSIGN", children=[
            ASTNode(kind="IDENTIFIER", value="x"),
            ASTNode(kind="PLUS", children=[
                ASTNode(kind="NUMBER", value=10),
                ASTNode(kind="NUMBER", value=5)
            ])
        ])
    ])
    
    compiler = SimpleCompiler(ast)
    compiler.compile()

def sample_complex():
    print("\n" + "-"*40)
    print("SAMPLE 2: Complex Expression")
    print("z = (x + y) - (5 * (7 + 9)) / 2")
    print("-"*40)
    
    ast = ASTNode(kind="PROGRAM", children=[
        ASTNode(kind="ASSIGN", children=[
            ASTNode(kind="IDENTIFIER", value="x"),
            ASTNode(kind="NUMBER", value=2025)
        ]),
        ASTNode(kind="ASSIGN", children=[
            ASTNode(kind="IDENTIFIER", value="y"),
            ASTNode(kind="NUMBER", value=1477)
        ]),
        ASTNode(kind="ASSIGN", children=[
            ASTNode(kind="IDENTIFIER", value="z"),
            ASTNode(kind="MINUS", children=[
                ASTNode(kind="PLUS", children=[
                    ASTNode(kind="IDENTIFIER", value="x"),
                    ASTNode(kind="IDENTIFIER", value="y")
                ]),
                ASTNode(kind="DIVIDE", children=[
                    ASTNode(kind="TIMES", children=[
                        ASTNode(kind="NUMBER", value=5),
                        ASTNode(kind="PLUS", children=[
                            ASTNode(kind="NUMBER", value=7),
                            ASTNode(kind="NUMBER", value=9)
                        ])
                    ]),
                    ASTNode(kind="NUMBER", value=2)
                ])
            ])
        ])
    ])
    
    compiler = SimpleCompiler(ast)
    compiler.compile()

def sample_multiple_ops():
    print("\n" + "-"*40)
    print("SAMPLE 3: Multiple Operations")
    print("a = 100")
    print("b = 200") 
    print("c = a * b")
    print("d = c / 10")
    print("-"*40)
    
    ast = ASTNode(kind="PROGRAM", children=[
        ASTNode(kind="ASSIGN", children=[
            ASTNode(kind="IDENTIFIER", value="a"),
            ASTNode(kind="NUMBER", value=100)
        ]),
        ASTNode(kind="ASSIGN", children=[
            ASTNode(kind="IDENTIFIER", value="b"),
            ASTNode(kind="NUMBER", value=200)
        ]),
        ASTNode(kind="ASSIGN", children=[
            ASTNode(kind="IDENTIFIER", value="c"),
            ASTNode(kind="TIMES", children=[
                ASTNode(kind="IDENTIFIER", value="a"),
                ASTNode(kind="IDENTIFIER", value="b")
            ])
        ]),
        ASTNode(kind="ASSIGN", children=[
            ASTNode(kind="IDENTIFIER", value="d"),
            ASTNode(kind="DIVIDE", children=[
                ASTNode(kind="IDENTIFIER", value="c"),
                ASTNode(kind="NUMBER", value=10)
            ])
        ])
    ])
    
    compiler = SimpleCompiler(ast)
    compiler.compile()



if __name__ == "__main__":
    sample_simple()
    sample_complex()
    sample_multiple_ops()
