#!/usr/bin/env python3

import re
import sys
import operator
from typing import Tuple, Optional, List, Callable # Union, Dict
from abc import ABC, abstractmethod


class TokenMatchStrategy(ABC):
    @abstractmethod
    def match(self, code: str) -> Tuple[bool, str, str, str]:
        pass

class RegexTokenMatchStrategy(TokenMatchStrategy):
    def __init__(self):
        self.token_patterns = re.compile(
            r"(?P<num>[0-9]+)|"
            r"(?P<op>[-+*/()<>=])|"
            r"(?P<ws>\s+)|"
            r"(?P<kw>begin|end\.|end|if|then|while|do|var|!|\?|call|procedure)|"
            r"(?P<id>[a-zA-Z]+)|"
            r"(?P<semi>;)|"
            r"(?P<asgn>:=)|"
            r"(?P<comma>,)"
        )
    
    def match(self, code: str) -> Tuple[bool, str, str, str]:
        match = self.token_patterns.match(code)
        if not match:
            return (False, "", "", code)
        
        token = code[:match.end()]
        kind = match.lastgroup
        remaining_code = code[match.end():]
        return (True, token, kind, remaining_code)


class TokenIterator:
    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = ""
        self.current_kind = ""
        self.has_next = True
    
    def next(self, expected: Optional[str] = None, when: Optional[str] = None) -> bool:
        if when and self.current_token != when:
            return False
        if expected and self.current_kind != expected:
            raise SyntaxError(f"Expected {expected} but got {self.current_kind}")
        
        return self.lexer.next_token(self)


class PL0Lexer:
    def __init__(self, code: str):
        self.code = code + ";"  # force termination
        self.token_strategy = RegexTokenMatchStrategy()
        self.iterator = TokenIterator(self)
        self.next_token(self.iterator)  # initialize
    
    def next_token(self, iterator: TokenIterator) -> bool:
        success, token, kind, remaining_code = self.token_strategy.match(self.code)
        
        if not success:
            raise SyntaxError("Unexpected character")
        
        iterator.current_token = token
        iterator.current_kind = kind
        self.code = remaining_code
        
        # skip whitespace
        if kind == "ws":
            return self.next_token(iterator)
        
        return True
    
    def get_iterator(self) -> TokenIterator:
        return self.iterator



class ASTNode(ABC):
    @abstractmethod
    def accept(self, visitor):
        pass

class BlockNode(ASTNode):
    def __init__(self, variables: List[str], procedures: List[Tuple[str, ASTNode]], statement: ASTNode):
        self.variables = variables
        self.procedures = procedures
        self.statement = statement
    
    def accept(self, visitor):
        return visitor.visit_block(self)

class AssignNode(ASTNode):
    def __init__(self, var_name: str, expression: ASTNode):
        self.var_name = var_name
        self.expression = expression
    
    def accept(self, visitor):
        return visitor.visit_assign(self)

class CallNode(ASTNode):
    def __init__(self, proc_name: str):
        self.proc_name = proc_name
    
    def accept(self, visitor):
        return visitor.visit_call(self)

class ReadNode(ASTNode):
    def __init__(self, var_name: str):
        self.var_name = var_name
    
    def accept(self, visitor):
        return visitor.visit_read(self)

class WriteNode(ASTNode):
    def __init__(self, expression: ASTNode):
        self.expression = expression
    
    def accept(self, visitor):
        return visitor.visit_write(self)

class CompoundNode(ASTNode):
    def __init__(self, statements: List[ASTNode]):
        self.statements = statements
    
    def accept(self, visitor):
        return visitor.visit_compound(self)

class IfNode(ASTNode):
    def __init__(self, condition: ASTNode, then_statement: ASTNode):
        self.condition = condition
        self.then_statement = then_statement
    
    def accept(self, visitor):
        return visitor.visit_if(self)

class WhileNode(ASTNode):
    def __init__(self, condition: ASTNode, body: ASTNode):
        self.condition = condition
        self.body = body
    
    def accept(self, visitor):
        return visitor.visit_while(self)

class OperationNode(ASTNode):
    def __init__(self, operator: str, left: ASTNode, right: ASTNode):
        self.operator = operator
        self.left = left
        self.right = right
    
    def accept(self, visitor):
        return visitor.visit_operation(self)

class VariableNode(ASTNode):
    def __init__(self, name: str):
        self.name = name
    
    def accept(self, visitor):
        return visitor.visit_variable(self)

class NumberNode(ASTNode):
    def __init__(self, value: int):
        self.value = value
    
    def accept(self, visitor):
        return visitor.visit_number(self)




class ASTBuilder:
    def __init__(self, lexer: PL0Lexer):
        self.iterator = lexer.get_iterator()
    
    def build(self) -> ASTNode:
        return self.build_block()
    
    def build_block(self) -> BlockNode:
        variables = []
        procedures = []
        
        #  variable declarations
        while self.iterator.next("kw", "var"):
            while not self.iterator.next("semi", ";"):
                variables.append(self.iterator.current_token)
                self.iterator.next("id")
                self.iterator.next("comma", ",")
        
        #  procedure declarations
        while self.iterator.next("kw", "procedure"):
            proc_name = self.iterator.current_token
            self.iterator.next("id")
            self.iterator.next("semi")
            proc_body = self.build_block()
            procedures.append((proc_name, proc_body))
            self.iterator.next("semi")
        
        #  'main' statement
        statement = self.build_statement()
        return BlockNode(variables, procedures, statement)

    def build_statement(self) -> ASTNode:
        if self.iterator.current_kind == "id":
            # assignment statement: <id> := <expr>
            var_name = self.iterator.current_token
            self.iterator.next("id")
            self.iterator.next("asgn")
            return AssignNode(var_name, self.build_expression())
        
        elif self.iterator.current_token == "call":
            # procedure call: call <id>
            self.iterator.next("kw")
            proc_name = self.iterator.current_token
            self.iterator.next("id")
            return CallNode(proc_name)
        
        elif self.iterator.current_token == "?":
            # input statement: ? <id>
            self.iterator.next("kw")
            var_name = self.iterator.current_token
            self.iterator.next("id")
            return ReadNode(var_name)
        
        elif self.iterator.current_token == "!":
            # output statement: ! <expr>
            self.iterator.next("kw")
            return WriteNode(self.build_expression())
        
        elif self.iterator.current_token == "begin":
            # compound statement: begin <stmt...> end
            self.iterator.next("kw")
            statements = []
            while self.iterator.current_token not in ("end", "end."):
                statements.append(self.build_statement())
                self.iterator.next("semi", ";")
            self.iterator.next("kw")
            return CompoundNode(statements)
        
        elif self.iterator.current_token == "if":
            # conditional statement
            self.iterator.next("kw")
            left_expr = self.build_expression()
            op = self.iterator.current_token
            self.iterator.next("op")
            condition = OperationNode(op, left_expr, self.build_expression())
            self.iterator.next("kw", "then")  # 'then'
            return IfNode(condition, self.build_statement())
        
        elif self.iterator.current_token == "while":
            # loop statement
            self.iterator.next("kw")
            left_expr = self.build_expression()
            op = self.iterator.current_token
            self.iterator.next("op")
            condition = OperationNode(op, left_expr, self.build_expression())
            self.iterator.next("kw", "do")  # 'do'
            return WhileNode(condition, self.build_statement())
    
    def build_expression(self, operators="+-", term_builder=None) -> ASTNode:
        if term_builder is None:
            term_builder = lambda: self.build_expression("*/", self.build_factor)
        
        left = term_builder()
        while self.iterator.current_token in operators:
            op = self.iterator.current_token
            self.iterator.next("op")
            right = term_builder()
            left = OperationNode(op, left, right)
        return left
    
    def build_factor(self) -> ASTNode:
        if self.iterator.current_kind == "id":
            name = self.iterator.current_token
            self.iterator.next("id")
            return VariableNode(name)
        elif self.iterator.current_kind == "num":
            value = int(self.iterator.current_token)
            self.iterator.next("num")
            return NumberNode(value)
        elif self.iterator.current_token == "(":
            self.iterator.next("op")
            expr = self.build_expression()
            self.iterator.next("op")
            return expr



class Scope:
    def __init__(self, parent=None, variables=None, procedures=None):
        self.parent = parent
        self.variables = variables or {}
        self.procedures = procedures or {}
    
    def find_variable(self, name: str, find_frame: bool = False):
        if name in self.variables:
            return self.variables if find_frame else self.variables[name]
        elif self.parent:
            return self.parent.find_variable(name, find_frame)
        raise NameError(f"Variable '{name}' not found")
    
    def find_procedure(self, name: str):
        if name in self.procedures:
            return (self.procedures[name], self)
        elif self.parent:
            return self.parent.find_procedure(name)
        raise NameError(f"Procedure '{name}' not found")

class Visitor(ABC):
    @abstractmethod
    def visit_block(self, node: BlockNode):
        pass
    
    @abstractmethod
    def visit_assign(self, node: AssignNode):
        pass
    
    @abstractmethod
    def visit_call(self, node: CallNode):
        pass
    
    @abstractmethod
    def visit_read(self, node: ReadNode):
        pass
    
    @abstractmethod
    def visit_write(self, node: WriteNode):
        pass
    
    @abstractmethod
    def visit_compound(self, node: CompoundNode):
        pass
    
    @abstractmethod
    def visit_if(self, node: IfNode):
        pass
    
    @abstractmethod
    def visit_while(self, node: WhileNode):
        pass
    
    @abstractmethod
    def visit_operation(self, node: OperationNode):
        pass
    
    @abstractmethod
    def visit_variable(self, node: VariableNode):
        pass
    
    @abstractmethod
    def visit_number(self, node: NumberNode):
        pass


class OperatorFactory:
    @staticmethod
    def get_operator(op_symbol: str) -> Callable:
        operators = {
            "+": operator.add,
            "-": operator.sub,
            "*": operator.mul,
            "/": operator.floordiv,
            "<": operator.lt,
            ">": operator.gt,
            "=": operator.eq
        }
        if op_symbol not in operators:
            raise ValueError(f"Unknown operator: {op_symbol}")
        return operators[op_symbol]

class Interpreter(Visitor):
    def __init__(self):
        self.scope = None
        
    def interpret(self, ast: ASTNode):
        self.scope = Scope()
        return ast.accept(self)
    
    def visit_block(self, node: BlockNode):
        new_scope = Scope(
            parent=self.scope,
            variables={var: 0 for var in node.variables},
            procedures={proc[0]: proc[1] for proc in node.procedures}
        )
        
        # save old scope and use new one
        old_scope = self.scope
        self.scope = new_scope
        
        # evaluate statement in new scope
        result = node.statement.accept(self)
        
        # restore old scope
        self.scope = old_scope
        return result
    
    def visit_assign(self, node: AssignNode):
        value = node.expression.accept(self)
        env = self.scope.find_variable(node.var_name, find_frame=True)
        env[node.var_name] = value
        return 0
    
    def visit_call(self, node: CallNode):
        proc_body, def_scope = self.scope.find_procedure(node.proc_name)
        
        # save old scope
        old_scope = self.scope
        
        # create new scope with procedure's definition scope as parent
        self.scope = Scope(parent=def_scope)
        
        # execute procedure
        result = proc_body.accept(self)
        
        # restore scope
        self.scope = old_scope
        
        return result
    
    def visit_read(self, node: ReadNode):
        env = self.scope.find_variable(node.var_name, find_frame=True)
        env[node.var_name] = int(input("> "))
        return 0
    
    def visit_write(self, node: WriteNode):
        value = node.expression.accept(self)
        print(value)
        return 0
    
    def visit_compound(self, node: CompoundNode):
        for statement in node.statements:
            statement.accept(self)
        return 0
    
    def visit_if(self, node: IfNode):
        if node.condition.accept(self):
            return node.then_statement.accept(self)
        return 0
    
    def visit_while(self, node: WhileNode):
        while node.condition.accept(self):
            node.body.accept(self)
        return 0
    
    def visit_operation(self, node: OperationNode):
        left_val = node.left.accept(self)
        right_val = node.right.accept(self)
        op_func = OperatorFactory.get_operator(node.operator)
        return op_func(left_val, right_val)
    
    def visit_variable(self, node: VariableNode):
        return self.scope.find_variable(node.name)
    
    def visit_number(self, node: NumberNode):
        return node.value



class PL0Interpreter:
    @staticmethod
    def run_file(filename: str):
        try:
            with open(filename, 'r') as file:
                code = file.read()
        except IOError as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
        
        # create lexer
        lexer = PL0Lexer(code)
        
        # build AST
        builder = ASTBuilder(lexer)
        ast = builder.build()
        
        # interpret AST
        interpreter = Interpreter()
        interpreter.interpret(ast)

def main():
    if len(sys.argv) != 2:
        print("Usage: pl0.py <filename>", file=sys.stderr)
        sys.exit(1)
    
    PL0Interpreter.run_file(sys.argv[1])

if __name__ == "__main__":
    main()

