from ast_nodes import *

class CodeGenerator:
    def __init__(self, ast):
        self.ast = ast
        self.instructions = []
        self.label_counter = 0
    
    def generate(self):
        self.visit(self.ast)
        return self.instructions
    
    def new_label(self):
        label = f"L{self.label_counter}"
        self.label_counter += 1
        return label
    
    def emit(self, instruction):
        self.instructions.append(instruction)
    
    def visit(self, node):
        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name, self.generic_visit)
        return method(node)
    
    def generic_visit(self, node):
        raise Exception(f"No visit method for {type(node).__name__}")
    
    def visit_Program(self, node):
        for statement in node.statements:
            self.visit(statement)
        self.emit("HALT")
    
    def visit_LetStatement(self, node):
        self.visit(node.expression)
        self.emit(f"STORE {node.identifier}")
    
    def visit_AssignStatement(self, node):
        self.visit(node.expression)
        self.emit(f"STORE {node.identifier}")
    
    def visit_PrintStatement(self, node):
        self.visit(node.expression)
        self.emit("PRINT")
    
    def visit_InputStatement(self, node):
        self.emit("INPUT")
        self.emit(f"STORE {node.identifier}")
    
    def visit_IfStatement(self, node):
        else_label = self.new_label()
        end_label = self.new_label()
        
        self.visit(node.condition)
        self.emit(f"JZ {else_label}")
        self.visit(node.then_block)
        self.emit(f"JMP {end_label}")
        self.emit(f"{else_label}:")
        if node.else_block:
            self.visit(node.else_block)
        self.emit(f"{end_label}:")
    
    def visit_WhileStatement(self, node):
        start_label = self.new_label()
        end_label = self.new_label()
        
        self.emit(f"{start_label}:")
        self.visit(node.condition)
        self.emit(f"JZ {end_label}")
        self.visit(node.body)
        self.emit(f"JMP {start_label}")
        self.emit(f"{end_label}:")
    
    def visit_Block(self, node):
        for statement in node.statements:
            self.visit(statement)
    
    def visit_BinaryOp(self, node):
        self.visit(node.left)
        self.visit(node.right)
        
        op_map = {
            "PLUS": "ADD",
            "MINUS": "SUB",
            "TIMES": "MUL",
            "DIVIDE": "DIV",
            "MOD": "MOD",
            "EQ": "EQ",
            "NE": "NE",
            "LT": "LT",
            "GT": "GT",
            "LE": "LE",
            "GE": "GE"
        }
        self.emit(op_map[node.op])
    
    def visit_UnaryOp(self, node):
        self.visit(node.operand)
        if node.op == "MINUS":
            self.emit("NEG")
    
    def visit_NumberLiteral(self, node):
        self.emit(f"PUSH {node.value}")
    
    def visit_StringLiteral(self, node):
        self.emit(f'PUSH "{node.value}"')
    
    def visit_Identifier(self, node):
        self.emit(f"LOAD {node.name}")

if __name__ == "__main__":
    from lexer import tokenize
    from parser import Parser
    
    code = '''
let x = 10;
let y = 20;
if x < y {
    print("x is smaller");
}
'''
    tokens = tokenize(code)
    parser = Parser(tokens)
    ast = parser.parse()
    
    generator = CodeGenerator(ast)
    instructions = generator.generate()
    
    print("Generated code:")
    for i, instr in enumerate(instructions):
        print(f"{i:3}: {instr}")
