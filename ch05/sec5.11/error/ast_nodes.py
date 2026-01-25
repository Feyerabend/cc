class ASTNode:
    pass

class Program(ASTNode):
    def __init__(self, statements):
        self.statements = statements
    
    def __repr__(self):
        return f"Program({self.statements})"

class LetStatement(ASTNode):
    def __init__(self, identifier, expression):
        self.identifier = identifier
        self.expression = expression
    
    def __repr__(self):
        return f"Let({self.identifier}, {self.expression})"

class AssignStatement(ASTNode):
    def __init__(self, identifier, expression):
        self.identifier = identifier
        self.expression = expression
    
    def __repr__(self):
        return f"Assign({self.identifier}, {self.expression})"

class PrintStatement(ASTNode):
    def __init__(self, expression):
        self.expression = expression
    
    def __repr__(self):
        return f"Print({self.expression})"

class InputStatement(ASTNode):
    def __init__(self, identifier):
        self.identifier = identifier
    
    def __repr__(self):
        return f"Input({self.identifier})"

class IfStatement(ASTNode):
    def __init__(self, condition, then_block, else_block=None):
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block
    
    def __repr__(self):
        return f"If({self.condition}, {self.then_block}, {self.else_block})"

class WhileStatement(ASTNode):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body
    
    def __repr__(self):
        return f"While({self.condition}, {self.body})"

class Block(ASTNode):
    def __init__(self, statements):
        self.statements = statements
    
    def __repr__(self):
        return f"Block({self.statements})"

class BinaryOp(ASTNode):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right
    
    def __repr__(self):
        return f"BinOp({self.op}, {self.left}, {self.right})"

class UnaryOp(ASTNode):
    def __init__(self, op, operand):
        self.op = op
        self.operand = operand
    
    def __repr__(self):
        return f"UnaryOp({self.op}, {self.operand})"

class NumberLiteral(ASTNode):
    def __init__(self, value):
        self.value = value
    
    def __repr__(self):
        return f"Number({self.value})"

class StringLiteral(ASTNode):
    def __init__(self, value):
        self.value = value
    
    def __repr__(self):
        return f"String({self.value!r})"

class Identifier(ASTNode):
    def __init__(self, name):
        self.name = name
    
    def __repr__(self):
        return f"Identifier({self.name})"
