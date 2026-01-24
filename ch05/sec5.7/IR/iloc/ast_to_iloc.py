from ast_nodes import ASTNode, NodeType
from iloc_ir import ILOCInstruction, ILOCOp
from typing import List, Dict
import json
import sys

class ILOCGenerator:
    def __init__(self):
        self.instructions: List[ILOCInstruction] = []
        self.temp_counter = 0
        self.var_locations: Dict[str, str] = {}
        
    def new_temp(self) -> str:
        reg = f"r{self.temp_counter}"
        self.temp_counter += 1
        return reg
    
    def get_var_loc(self, var_name: str) -> str:
        if var_name not in self.var_locations:
            self.var_locations[var_name] = f"@{var_name}"
        return self.var_locations[var_name]
    
    def generate(self, node: ASTNode) -> str:
        if node.node_type == NodeType.NUMBER:
            reg = self.new_temp()
            self.instructions.append(
                ILOCInstruction(ILOCOp.LOADI, [str(node.value), reg])
            )
            return reg
        
        elif node.node_type == NodeType.VARIABLE:
            loc = self.get_var_loc(node.value)
            reg = self.new_temp()
            self.instructions.append(
                ILOCInstruction(ILOCOp.LOAD, [loc, reg])
            )
            return reg
        
        elif node.node_type == NodeType.BINOP:
            left_reg = self.generate(node.left)
            right_reg = self.generate(node.right)
            result_reg = self.new_temp()
            
            op_map = {
                '+': ILOCOp.ADD,
                '-': ILOCOp.SUB,
                '*': ILOCOp.MULT,
                '/': ILOCOp.DIV
            }
            op = op_map[node.value]
            
            self.instructions.append(
                ILOCInstruction(op, [left_reg, right_reg, result_reg])
            )
            return result_reg
        
        elif node.node_type == NodeType.ASSIGN:
            value_reg = self.generate(node.right)
            loc = self.get_var_loc(node.left.value)
            self.instructions.append(
                ILOCInstruction(ILOCOp.STORE, [value_reg, loc])
            )
            return value_reg
        
        elif node.node_type == NodeType.PROGRAM:
            last_reg = None
            for child in node.children:
                last_reg = self.generate(child)
            return last_reg
    
    def save_to_file(self, filename: str):
        with open(filename, 'w') as f:
            f.write(f"# ILOC code\n")
            f.write(f"# Instructions: {len(self.instructions)}\n")
            f.write(f"# Registers: {self.temp_counter}\n")
            f.write(f"#\n")
            f.write(f"# Variables:\n")
            for var, loc in sorted(self.var_locations.items()):
                f.write(f"#   {loc} = {var}\n")
            f.write("#\n\n")
            
            for i, instr in enumerate(self.instructions):
                f.write(f"{i:3}: {instr}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ast_to_iloc.py <output.iloc>")
        sys.exit(1)
    
    from example_program import create_program_ast
    
    ast = create_program_ast()
    generator = ILOCGenerator()
    generator.generate(ast)
    generator.save_to_file(sys.argv[1])
    print(f"Generated {len(generator.instructions)} ILOC instructions -> {sys.argv[1]}")
