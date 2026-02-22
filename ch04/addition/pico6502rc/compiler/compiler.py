"""
PL/0 to 6502 Compiler with I/O Extensions
Compiles PL/0 source code to 6502 assembly with hardware I/O support.
Designed to be extensible for language enhancements.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum, auto
import argparse
import traceback


# PARSER COMBINATOR LIBRARY

class ParseResult:
    """Result of a parse attempt"""
    def __init__(self, success: bool, value=None, rest: str = "", error: str = ""):
        self.success = success
        self.value = value
        self.rest = rest
        self.error = error
    
    def __repr__(self):
        if self.success:
            return f"Success({self.value}, rest={repr(self.rest[:20])}...)"
        return f"Failure({self.error})"


class Parser:
    """Base parser combinator class"""
    
    def __init__(self, parse_fn):
        self.parse_fn = parse_fn
    
    def parse(self, input_str: str) -> ParseResult:
        """Execute the parser"""
        return self.parse_fn(input_str)
    
    def map(self, fn):
        """Transform successful parse results"""
        def mapped(input_str):
            result = self.parse(input_str)
            if result.success:
                return ParseResult(True, fn(result.value), result.rest)
            return result
        return Parser(mapped)
    
    def bind(self, fn):
        """Monadic bind - chain parsers based on results"""
        def bound(input_str):
            result = self.parse(input_str)
            if result.success:
                next_parser = fn(result.value)
                return next_parser.parse(result.rest)
            return result
        return Parser(bound)
    
    def then(self, other):
        """Sequential composition - run this then other, keep other's result"""
        return self.bind(lambda _: other)
    
    def skip(self, other):
        """Sequential composition - run this then other, keep this result"""
        return self.bind(lambda x: other.map(lambda _: x))
    
    def or_else(self, other):
        """Alternative - try this, if fails try other"""
        def alternative(input_str):
            result = self.parse(input_str)
            if result.success:
                return result
            return other.parse(input_str)
        return Parser(alternative)
    
    def many(self):
        """Zero or more repetitions"""
        def many_parse(input_str):
            values = []
            current = input_str
            while True:
                result = self.parse(current)
                if not result.success:
                    break
                values.append(result.value)
                current = result.rest
            return ParseResult(True, values, current)
        return Parser(many_parse)
    
    def many1(self):
        """One or more repetitions"""
        return self.bind(lambda first: self.many().map(lambda rest: [first] + rest))
    
    def optional(self):
        """Optional parser - returns None if fails"""
        return self.map(lambda x: x).or_else(success(None))
    
    def sep_by(self, separator):
        """Parse list separated by separator"""
        def sep_parse(input_str):
            first_result = self.parse(input_str)
            if not first_result.success:
                return ParseResult(True, [], input_str)
            
            values = [first_result.value]
            current = first_result.rest
            
            while True:
                sep_result = separator.parse(current)
                if not sep_result.success:
                    break
                
                val_result = self.parse(sep_result.rest)
                if not val_result.success:
                    break
                
                values.append(val_result.value)
                current = val_result.rest
            
            return ParseResult(True, values, current)
        return Parser(sep_parse)


# Primitive parsers
def success(value):
    """Always succeeds with given value"""
    return Parser(lambda input_str: ParseResult(True, value, input_str))


def failure(error):
    """Always fails with error message"""
    return Parser(lambda input_str: ParseResult(False, error=error))


def char(c):
    """Parse a specific character"""
    def parse_char(input_str):
        if input_str and input_str[0] == c:
            return ParseResult(True, c, input_str[1:])
        return ParseResult(False, error=f"Expected '{c}'")
    return Parser(parse_char)


def string(s):
    """Parse a specific string"""
    def parse_string(input_str):
        if input_str.startswith(s):
            return ParseResult(True, s, input_str[len(s):])
        return ParseResult(False, error=f"Expected '{s}'")
    return Parser(parse_string)


def regex(pattern):
    """Parse using regex pattern"""
    import re
    compiled = re.compile(pattern)
    
    def parse_regex(input_str):
        match = compiled.match(input_str)
        if match:
            return ParseResult(True, match.group(0), input_str[match.end():])
        return ParseResult(False, error=f"Expected pattern {pattern}")
    return Parser(parse_regex)


def whitespace():
    """Parse whitespace"""
    return regex(r'\s*')


def token(parser):
    """Parse and skip trailing whitespace"""
    return parser.skip(whitespace())


def keyword(kw):
    """Parse keyword (case-insensitive, followed by non-alphanumeric)"""
    def parse_kw(input_str):
        if input_str.lower().startswith(kw.lower()):
            end = len(kw)
            # Check not followed by alphanumeric
            if end < len(input_str) and input_str[end].isalnum():
                return ParseResult(False, error=f"Expected keyword '{kw}'")
            return ParseResult(True, kw.upper(), input_str[end:])
        return ParseResult(False, error=f"Expected keyword '{kw}'")
    return token(Parser(parse_kw))


def symbol(s):
    """Parse symbol and skip whitespace"""
    return token(string(s))


# AST NODES

@dataclass
class ASTNode:
    """Base class for AST nodes"""
    pass


@dataclass
class NumberNode(ASTNode):
    value: int


@dataclass
class IdentNode(ASTNode):
    name: str


@dataclass
class BinOpNode(ASTNode):
    op: str
    left: ASTNode
    right: ASTNode


@dataclass
class UnaryOpNode(ASTNode):
    op: str
    expr: ASTNode


@dataclass
class ConditionNode(ASTNode):
    op: str
    left: ASTNode
    right: ASTNode


@dataclass
class AssignmentNode(ASTNode):
    name: str
    expr: ASTNode


@dataclass
class CallNode(ASTNode):
    name: str


@dataclass
class BeginNode(ASTNode):
    statements: List[ASTNode]


@dataclass
class IfNode(ASTNode):
    condition: ConditionNode
    then_stmt: ASTNode


@dataclass
class WhileNode(ASTNode):
    condition: ConditionNode
    body: ASTNode


@dataclass
class ReadNode(ASTNode):
    """Read from memory address into variable"""
    variable: str
    address: ASTNode


@dataclass
class WriteNode(ASTNode):
    """Write expression to memory address"""
    address: ASTNode
    expr: ASTNode


@dataclass
class OutNode(ASTNode):
    """Output value (PRINT-like)"""
    expr: ASTNode


@dataclass
class InNode(ASTNode):
    """Input value (READ-like)"""
    variable: str


@dataclass
class PlotNode(ASTNode):
    x: ASTNode
    y: ASTNode
    color: ASTNode


@dataclass
class LineNode(ASTNode):
    x1: ASTNode
    y1: ASTNode
    x2: ASTNode
    y2: ASTNode
    color: ASTNode


@dataclass
class RectNode(ASTNode):
    x: ASTNode
    y: ASTNode
    w: ASTNode
    h: ASTNode
    color: ASTNode


@dataclass
class ClrGfxNode(ASTNode):
    pass


@dataclass
class ProcedureNode(ASTNode):
    name: str
    block: 'BlockNode'


@dataclass
class BlockNode(ASTNode):
    constants: List[Tuple[str, int]]
    variables: List[str]
    procedures: List[ProcedureNode]
    statement: ASTNode


@dataclass
class ProgramNode(ASTNode):
    block: BlockNode


# PL/0 PARSER WITH I/O EXTENSIONS

class PL0Parser:
    """Parser for PL/0 language with I/O extensions"""
    
    def __init__(self):
        self.build_parser()
    
    def build_parser(self):
        """Build the PL/0 parser using combinators"""
        
        # Forward declarations for recursive grammar
        expression = Parser(lambda s: self.expression.parse(s))
        statement = Parser(lambda s: self.statement.parse(s))
        block = Parser(lambda s: self.block.parse(s))
        condition = Parser(lambda s: self.condition.parse(s))
        
        # Number (supports hex with $)
        hex_number = token(regex(r'\$[0-9A-Fa-f]+').map(lambda s: int(s[1:], 16)))
        dec_number = token(regex(r'\d+').map(lambda s: int(s)))
        number = (hex_number.or_else(dec_number)).map(NumberNode)
        
        # Identifier
        ident = token(regex(r'[a-zA-Z][a-zA-Z0-9_]*'))
        
        # Factor: number | ident | '(' expression ')'
        def make_factor():
            parens = symbol('(').then(expression).skip(symbol(')'))
            return number.or_else(ident.map(IdentNode)).or_else(parens)
        
        factor = Parser(lambda s: make_factor().parse(s))
        
        # Term: factor (('*' | '/') factor)*
        def make_term():
            def combine_ops(first, ops):
                result = first
                for op, right in ops:
                    result = BinOpNode(op, result, right)
                return result
            
            mul_div = symbol('*').or_else(symbol('/'))
            op_factor = mul_div.bind(lambda op: factor.map(lambda f: (op, f)))
            
            return factor.bind(lambda first: 
                op_factor.many().map(lambda ops: combine_ops(first, ops))
            )
        
        term = Parser(lambda s: make_term().parse(s))
        
        # Expression: ['+' | '-'] term (('+' | '-') term)*
        def make_expression():
            def combine_ops(first, ops):
                result = first
                for op, right in ops:
                    result = BinOpNode(op, result, right)
                return result
            
            plus_minus = symbol('+').or_else(symbol('-'))
            sign = plus_minus.optional()
            op_term = plus_minus.bind(lambda op: term.map(lambda t: (op, t)))
            
            return sign.bind(lambda s:
                term.bind(lambda first:
                    op_term.many().map(lambda ops:
                        combine_ops(
                            UnaryOpNode('-', first) if s == '-' else first,
                            ops
                        )
                    )
                )
            )
        
        self.expression = make_expression()
        
        # Condition: expression ('=' | '#' | '<' | '<=' | '>' | '>=') expression
        def make_condition():
            comp_ops = (symbol('<=').or_else(symbol('>='))
                       .or_else(symbol('='))
                       .or_else(symbol('#'))
                       .or_else(symbol('<'))
                       .or_else(symbol('>')))
            
            return expression.bind(lambda left:
                comp_ops.bind(lambda op:
                    expression.map(lambda right:
                        ConditionNode(op, left, right)
                    )
                )
            )
        
        self.condition = make_condition()
        
        # Statement types
        # Assignment: ident ':=' expression
        assignment = ident.bind(lambda name:
            symbol(':=').then(expression).map(lambda expr:
                AssignmentNode(name, expr)
            )
        )
        
        # Call: 'CALL' ident
        call_stmt = keyword('CALL').then(ident).map(CallNode)
        
        # READ statement: READ variable FROM address
        read_stmt = keyword('READ').then(
            ident.bind(lambda var:
                keyword('FROM').then(expression).map(lambda addr:
                    ReadNode(var, addr)
                )
            )
        )
        
        # WRITE statement: WRITE expression TO address
        write_stmt = keyword('WRITE').then(
            expression.bind(lambda expr:
                keyword('TO').then(expression).map(lambda addr:
                    WriteNode(addr, expr)
                )
            )
        )
        
        # OUT statement: OUT expression (output to screen/debug)
        out_stmt = keyword('OUT').then(expression).map(OutNode)
        
        # IN statement: IN variable (input from buttons/keyboard)
        in_stmt = keyword('IN').then(ident).map(InNode)

        # PLOT statement: PLOT expr , expr , expr
        plot_stmt = keyword('PLOT').then(
            expression.bind(lambda x:
                symbol(',').then(expression).bind(lambda y:
                    symbol(',').then(expression).map(lambda color:
                        PlotNode(x, y, color)
                    )
                )
            )
        )

        # LINE statement: LINE expr , expr , expr , expr , expr
        line_stmt = keyword('LINE').then(
            expression.bind(lambda x1:
                symbol(',').then(expression).bind(lambda y1:
                    symbol(',').then(expression).bind(lambda x2:
                        symbol(',').then(expression).bind(lambda y2:
                            symbol(',').then(expression).map(lambda color:
                                LineNode(x1, y1, x2, y2, color)
                            )
                        )
                    )
                )
            )
        )

        # RECT statement: RECT expr , expr , expr , expr , expr
        rect_stmt = keyword('RECT').then(
            expression.bind(lambda x:
                symbol(',').then(expression).bind(lambda y:
                    symbol(',').then(expression).bind(lambda w:
                        symbol(',').then(expression).bind(lambda h:
                            symbol(',').then(expression).map(lambda color:
                                RectNode(x, y, w, h, color)
                            )
                        )
                    )
                )
            )
        )

        # CLRGFX statement
        clrgfx_stmt = keyword('CLRGFX').map(lambda _: ClrGfxNode())

        # Begin: 'BEGIN' statement (';' statement)* 'END'
        def make_begin():
            return keyword('BEGIN').then(
                statement.sep_by(symbol(';'))
            ).skip(keyword('END')).map(BeginNode)
        
        begin_stmt = Parser(lambda s: make_begin().parse(s))
        
        # If: 'IF' condition 'THEN' statement
        if_stmt = keyword('IF').then(
            condition.bind(lambda cond:
                keyword('THEN').then(statement).map(lambda stmt:
                    IfNode(cond, stmt)
                )
            )
        )
        
        # While: 'WHILE' condition 'DO' statement
        while_stmt = keyword('WHILE').then(
            condition.bind(lambda cond:
                keyword('DO').then(statement).map(lambda stmt:
                    WhileNode(cond, stmt)
                )
            )
        )
        
        # Empty statement
        empty_stmt = success(None)
        
        # Statement: assignment | call | read | write | plot | line | rect | clrgfx | out | in | begin | if | while | empty
        self.statement = (assignment
                         .or_else(call_stmt)
                         .or_else(read_stmt)
                         .or_else(write_stmt)
                         .or_else(plot_stmt)
                         .or_else(line_stmt)
                         .or_else(rect_stmt)
                         .or_else(clrgfx_stmt)
                         .or_else(out_stmt)
                         .or_else(in_stmt)
                         .or_else(begin_stmt)
                         .or_else(if_stmt)
                         .or_else(while_stmt)
                         .or_else(empty_stmt))
        
        # Const declaration: 'CONST' ident '=' number (',' ident '=' number)* ';'
        const_decl = keyword('CONST').then(
            ident.bind(lambda name:
                symbol('=').then(
                    token(regex(r'\$[0-9A-Fa-f]+|\d+')).map(
                        lambda v: int(v[1:], 16) if v.startswith('$') else int(v)
                    )
                ).map(lambda val: (name, val))
            ).sep_by(symbol(','))
        ).skip(symbol(';'))
        
        # Var declaration: 'VAR' ident (',' ident)* ';'
        var_decl = keyword('VAR').then(
            ident.sep_by(symbol(','))
        ).skip(symbol(';'))
        
        # Procedure declaration: 'PROCEDURE' ident ';' block ';'
        proc_decl = keyword('PROCEDURE').then(
            ident.bind(lambda name:
                symbol(';').then(block).skip(symbol(';')).map(lambda blk:
                    ProcedureNode(name, blk)
                )
            )
        )
        
        # Block
        def make_block():
            return (const_decl.optional().bind(lambda consts:
                var_decl.optional().bind(lambda vars:
                    proc_decl.many().bind(lambda procs:
                        statement.map(lambda stmt:
                            BlockNode(
                                consts or [],
                                vars or [],
                                procs,
                                stmt
                            )
                        )
                    )
                )
            ))
        
        self.block = make_block()
        
        # Program: block '.'
        self.program = whitespace().then(
            block.skip(symbol('.')).map(ProgramNode)
        )
    
    def parse(self, source: str) -> ProgramNode:
        """Parse PL/0 source code"""
        result = self.program.parse(source)
        if not result.success:
            raise SyntaxError(f"Parse error: {result.error}")
        if result.rest.strip():
            raise SyntaxError(f"Unexpected input after program: {result.rest[:50]}")
        return result.value


# CODE GENERATOR (6502 Assembly) WITH I/O SUPPORT

class CodeGenerator:
    """Generates 6502 assembly from PL/0 AST with I/O support"""
    
    def __init__(self):
        self.code: List[str] = []
        self.label_counter = 0
        self.variables: Dict[str, int] = {}  # name -> zero page address
        self.constants: Dict[str, int] = {}
        self.procedures: Dict[str, str] = {}  # name -> label
        self.var_counter = 0x20  # Start of zero page for variables (avoid $00-$1F)
        self.in_procedure = False
        
        # Hardware addresses (C64-style memory map)
        self.hw_constants = {
            'SCREEN': 0x0400,
            'COLOR': 0xD800,
            'BORDER': 0xD000,
            'BGCOLOR': 0xD001,
            'CURSOR_X': 0xD002,
            'CURSOR_Y': 0xD003,
            'BUTTONS': 0xDC00,
            # GFX registers
            'GFX_X':     0xD010,
            'GFX_Y':     0xD012,
            'GFX_COLOR': 0xD013,
            'GFX_CMD':   0xD014,
            'GFX_X2':    0xD015,
            'GFX_Y2':    0xD017,
            # Block character codes
            'BLOCK':     128,
            'BLOCK_TOP': 129,
            'BLOCK_BOT': 130,
            'BLOCK_L':   131,
            'BLOCK_R':   132,
            'BLOCK_UL':  133,
            'BLOCK_UR':  134,
            'BLOCK_LL':  135,
            'BLOCK_LR':  136,
            'BLOCK_H':   137,
            'BLOCK_V':   138,
            'BLOCK_X':   139,
            'BLOCK_BS':  140,
            'BLOCK_FS':  141,
            'BLOCK_CHK': 142,
            'BLOCK_DOT': 143,
        }
    
    def new_label(self, prefix='L') -> str:
        """Generate a unique label"""
        label = f"{prefix}{self.label_counter}"
        self.label_counter += 1
        return label
    
    def emit(self, line: str):
        """Emit a line of assembly"""
        self.code.append(line)
    
    def compile(self, ast: ProgramNode) -> str:
        """Compile AST to 6502 assembly"""
        self.emit("; PL/0 to 6502 Assembly with I/O Extensions")
        self.emit("; Generated code")
        self.emit("")
        self.emit("        .org $8000")
        self.emit("")
        
        # Define hardware constants
        self.emit("; Hardware registers")
        for name, addr in self.hw_constants.items():
            self.emit(f"{name}    = ${addr:04X}")
        self.emit("")

        # Jump over any procedure bodies to the main program entry point.
        # Procedures are emitted first by compile_block; without this JMP the
        # CPU would fall into the first procedure on reset instead of main.
        self.emit("        JMP main_start  ; Skip procedures, jump to main code")
        self.emit("")

        # Compile main block
        self.compile_block(ast.block, is_main=True)
        
        self.emit("")
        self.emit("halt:")
        self.emit("        JMP halt        ; Halt")
        self.emit("")
        
        # Emit runtime library
        self.emit_multiply_routine()
        self.emit_divide_routine()
        self.emit_screen_output_routine()
        
        return '\n'.join(self.code)
    
    def compile_block(self, block: BlockNode, is_main=False):
        """Compile a block"""
        # Save current context
        old_vars = dict(self.variables)
        old_consts = dict(self.constants)
        old_procs = dict(self.procedures)
        
        # Register constants
        for name, value in block.constants:
            self.constants[name] = value
        
        # Register variables
        for var_name in block.variables:
            if var_name not in self.variables:
                self.variables[var_name] = self.var_counter
                self.var_counter += 2  # 16-bit values
        
        # Compile procedures
        for proc in block.procedures:
            proc_label = self.new_label(f"proc_{proc.name}_")
            self.procedures[proc.name] = proc_label
        
        # Emit procedure definitions
        for proc in block.procedures:
            proc_label = self.procedures[proc.name]
            self.emit(f"{proc_label}:")
            old_in_proc = self.in_procedure
            self.in_procedure = True
            self.compile_block(proc.block)
            self.in_procedure = old_in_proc
            self.emit("        RTS")
            self.emit("")
        
        # Compile main statement
        if block.statement:
            if is_main:
                self.emit("main_start:")
            self.compile_statement(block.statement)
        
        # Restore context if not main
        if not is_main:
            self.variables = old_vars
            self.constants = old_consts
            self.procedures = old_procs
    
    def compile_statement(self, stmt: ASTNode):
        """Compile a statement"""
        if stmt is None:
            return
        
        if isinstance(stmt, AssignmentNode):
            self.compile_expression(stmt.expr)
            addr = self.get_variable_address(stmt.name)
            self.emit(f"        STA ${addr:02X}       ; {stmt.name} = (low byte)")
            self.emit(f"        STX ${addr+1:02X}       ; {stmt.name} = (high byte)")
        
        elif isinstance(stmt, CallNode):
            proc_label = self.procedures.get(stmt.name)
            if not proc_label:
                raise NameError(f"Undefined procedure: {stmt.name}")
            self.emit(f"        JSR {proc_label}    ; CALL {stmt.name}")
        
        elif isinstance(stmt, ReadNode):
            # READ variable FROM address
            self.compile_expression(stmt.address)
            self.emit("        STA $FE         ; Address low")
            self.emit("        STX $FF         ; Address high")
            self.emit("        LDY #$00")
            self.emit("        LDA ($FE),Y     ; Read from address")
            self.emit("        LDX #$00        ; High byte = 0")
            addr = self.get_variable_address(stmt.variable)
            self.emit(f"        STA ${addr:02X}       ; Store to {stmt.variable}")
            self.emit(f"        STX ${addr+1:02X}")
        
        elif isinstance(stmt, WriteNode):
            # WRITE expression TO address
            self.compile_expression(stmt.expr)
            self.emit("        PHA             ; Save value low")
            self.emit("        TXA")
            self.emit("        PHA             ; Save value high")
            self.compile_expression(stmt.address)
            self.emit("        STA $FE         ; Address low")
            self.emit("        STX $FF         ; Address high")
            self.emit("        PLA")
            self.emit("        TAX             ; Restore value high")
            self.emit("        PLA             ; Restore value low")
            self.emit("        LDY #$00")
            self.emit("        STA ($FE),Y     ; Write to address")
        
        elif isinstance(stmt, OutNode):
            # OUT expression - write to screen (simplified)
            self.compile_expression(stmt.expr)
            self.emit("        JSR screen_out  ; Output to screen")
        
        elif isinstance(stmt, InNode):
            # IN variable - read buttons
            addr = self.get_variable_address(stmt.variable)
            self.emit(f"        LDA BUTTONS     ; Read buttons")
            self.emit("        LDX #$00")
            self.emit(f"        STA ${addr:02X}       ; Store to {stmt.variable}")
            self.emit(f"        STX ${addr+1:02X}")
        
        elif isinstance(stmt, PlotNode):
            self.compile_expression(stmt.x)
            self.emit("        STA $D010       ; GFX_X low")
            self.emit("        STX $D011       ; GFX_X high")
            self.compile_expression(stmt.y)
            self.emit("        STA $D012       ; GFX_Y")
            self.compile_expression(stmt.color)
            self.emit("        STA $D013       ; GFX_COLOR")
            self.emit("        LDA #$01")
            self.emit("        STA $D014       ; CMD: PLOT")

        elif isinstance(stmt, LineNode):
            self.compile_expression(stmt.x1)
            self.emit("        STA $D010       ; GFX_X low")
            self.emit("        STX $D011       ; GFX_X high")
            self.compile_expression(stmt.y1)
            self.emit("        STA $D012       ; GFX_Y")
            self.compile_expression(stmt.color)
            self.emit("        STA $D013       ; GFX_COLOR")
            self.compile_expression(stmt.x2)
            self.emit("        STA $D015       ; GFX_X2 low")
            self.emit("        STX $D016       ; GFX_X2 high")
            self.compile_expression(stmt.y2)
            self.emit("        STA $D017       ; GFX_Y2")
            self.emit("        LDA #$03")
            self.emit("        STA $D014       ; CMD: LINE")

        elif isinstance(stmt, RectNode):
            self.compile_expression(stmt.x)
            self.emit("        STA $D010       ; GFX_X low")
            self.emit("        STX $D011       ; GFX_X high")
            self.compile_expression(stmt.y)
            self.emit("        STA $D012       ; GFX_Y")
            self.compile_expression(stmt.color)
            self.emit("        STA $D013       ; GFX_COLOR")
            self.compile_expression(stmt.w)
            self.emit("        STA $D015       ; GFX_X2 (width) low")
            self.emit("        STX $D016       ; GFX_X2 (width) high")
            self.compile_expression(stmt.h)
            self.emit("        STA $D017       ; GFX_Y2 (height)")
            self.emit("        LDA #$04")
            self.emit("        STA $D014       ; CMD: RECT")

        elif isinstance(stmt, ClrGfxNode):
            self.emit("        LDA #$02")
            self.emit("        STA $D014       ; CMD: CLRGFX")

        elif isinstance(stmt, BeginNode):
            for s in stmt.statements:
                if s is not None:
                    self.compile_statement(s)
        
        elif isinstance(stmt, IfNode):
            end_label = self.new_label('if_end_')
            self.compile_condition(stmt.condition, end_label)
            self.compile_statement(stmt.then_stmt)
            self.emit(f"{end_label}:")
        
        elif isinstance(stmt, WhileNode):
            start_label = self.new_label('while_start_')
            end_label = self.new_label('while_end_')
            self.emit(f"{start_label}:")
            self.compile_condition(stmt.condition, end_label)
            self.compile_statement(stmt.body)
            self.emit(f"        JMP {start_label}")
            self.emit(f"{end_label}:")
    
    def compile_expression(self, expr: ASTNode):
        """Compile expression, result in A (low) and X (high)"""
        if isinstance(expr, NumberNode):
            val = expr.value
            self.emit(f"        LDA #${val & 0xFF:02X}")
            self.emit(f"        LDX #${(val >> 8) & 0xFF:02X}")
        
        elif isinstance(expr, IdentNode):
            # Check if it's a hardware constant
            if expr.name in self.hw_constants:
                val = self.hw_constants[expr.name]
                self.emit(f"        LDA #${val & 0xFF:02X}    ; {expr.name}")
                self.emit(f"        LDX #${(val >> 8) & 0xFF:02X}")
            elif expr.name in self.constants:
                val = self.constants[expr.name]
                self.emit(f"        LDA #${val & 0xFF:02X}    ; const {expr.name}")
                self.emit(f"        LDX #${(val >> 8) & 0xFF:02X}")
            else:
                addr = self.get_variable_address(expr.name)
                self.emit(f"        LDA ${addr:02X}       ; {expr.name} (low)")
                self.emit(f"        LDX ${addr+1:02X}       ; {expr.name} (high)")
        
        elif isinstance(expr, UnaryOpNode):
            self.compile_expression(expr.expr)
            if expr.op == '-':
                # Negate: two's complement
                self.emit("        EOR #$FF        ; Negate")
                self.emit("        CLC")
                self.emit("        ADC #$01")
                self.emit("        PHA")
                self.emit("        TXA")
                self.emit("        EOR #$FF")
                self.emit("        ADC #$00")
                self.emit("        TAX")
                self.emit("        PLA")
        
        elif isinstance(expr, BinOpNode):
            # Compile left
            self.compile_expression(expr.left)
            # Save left on stack
            self.emit("        PHA             ; Save left (low)")
            self.emit("        TXA")
            self.emit("        PHA             ; Save left (high)")
            # Compile right
            self.compile_expression(expr.right)
            
            if expr.op == '+':
                # Add
                self.emit("        STA $FE         ; right (low) -> temp")
                self.emit("        STX $FF         ; right (high) -> temp")
                self.emit("        PLA             ; Restore left (high)")
                self.emit("        TAX")
                self.emit("        PLA             ; Restore left (low)")
                self.emit("        CLC")
                self.emit("        ADC $FE         ; Add low bytes")
                self.emit("        PHA")
                self.emit("        TXA")
                self.emit("        ADC $FF         ; Add high bytes with carry")
                self.emit("        TAX")
                self.emit("        PLA")
            
            elif expr.op == '-':
                # Subtract
                self.emit("        STA $FE         ; right (low) -> temp")
                self.emit("        STX $FF         ; right (high) -> temp")
                self.emit("        PLA             ; Restore left (high)")
                self.emit("        TAX")
                self.emit("        PLA             ; Restore left (low)")
                self.emit("        SEC")
                self.emit("        SBC $FE         ; Subtract low bytes")
                self.emit("        PHA")
                self.emit("        TXA")
                self.emit("        SBC $FF         ; Subtract high bytes")
                self.emit("        TAX")
                self.emit("        PLA")
            
            elif expr.op == '*':
                # Multiply - call routine
                self.emit("        JSR multiply    ; Multiply")
            
            elif expr.op == '/':
                # Divide - call routine
                self.emit("        JSR divide      ; Divide")
    
    def compile_condition(self, cond: ConditionNode, false_label: str):
        """Compile condition, branch to false_label if false"""
        # Compile left
        self.compile_expression(cond.left)
        self.emit("        PHA             ; Save left (low)")
        self.emit("        TXA")
        self.emit("        PHA             ; Save left (high)")
        
        # Compile right
        self.compile_expression(cond.right)
        self.emit("        STA $FE         ; right (low)")
        self.emit("        STX $FF         ; right (high)")
        self.emit("        PLA             ; left (high)")
        self.emit("        TAX")
        self.emit("        PLA             ; left (low)")
        
        # Compare based on operator
        if cond.op == '=':
            self.emit("        CMP $FE")
            self.emit(f"        BNE {false_label}")
            self.emit("        CPX $FF")
            self.emit(f"        BNE {false_label}")
        
        elif cond.op == '#':
            true_label = self.new_label('cond_true_')
            self.emit("        CMP $FE")
            self.emit(f"        BNE {true_label}")
            self.emit("        CPX $FF")
            self.emit(f"        BEQ {false_label}")
            self.emit(f"{true_label}:")
        
        elif cond.op == '<':
            self.emit("        CMP $FE")
            self.emit("        TXA")
            self.emit("        SBC $FF")
            self.emit(f"        BCS {false_label}   ; Branch if left >= right")
        
        elif cond.op == '<=':
            self.emit("        CMP $FE")
            self.emit("        TXA")
            self.emit("        SBC $FF")
            true_label = self.new_label('cond_true_')
            self.emit(f"        BCC {true_label}    ; left < right")
            self.emit(f"        BNE {false_label}   ; left > right")
            self.emit(f"{true_label}:")
        
        elif cond.op == '>':
            # left > right
            self.emit("        CMP $FE")
            self.emit("        TXA")
            self.emit("        SBC $FF")
            self.emit(f"        BCC {false_label}   ; left < right")
            self.emit(f"        BEQ {false_label}   ; left = right")
        
        elif cond.op == '>=':
            # left >= right means NOT (left < right)
            self.emit("        CMP $FE")
            self.emit("        TXA")
            self.emit("        SBC $FF")
            self.emit(f"        BCC {false_label}   ; left < right")
    
    def get_variable_address(self, name: str) -> int:
        """Get zero page address for variable"""
        if name not in self.variables:
            raise NameError(f"Undefined variable: {name}")
        return self.variables[name]
    
    def emit_multiply_routine(self):
        """Emit 16-bit multiply routine (A:X * $FE:$FF -> A:X)"""
        self.emit("; 16-bit multiply: (A:X) * ($FE:$FF) -> (A:X)")
        self.emit("multiply:")
        self.emit("        STA $F0         ; multiplicand low")
        self.emit("        STX $F1         ; multiplicand high")
        self.emit("        LDA #$00")
        self.emit("        STA $F2         ; result low")
        self.emit("        STA $F3         ; result high")
        self.emit("        LDX #$10        ; 16 bits")
        self.emit("mul_loop:")
        self.emit("        LSR $F1         ; Shift multiplicand right")
        self.emit("        ROR $F0")
        self.emit("        BCC mul_skip")
        self.emit("        CLC")
        self.emit("        LDA $F2")
        self.emit("        ADC $FE")
        self.emit("        STA $F2")
        self.emit("        LDA $F3")
        self.emit("        ADC $FF")
        self.emit("        STA $F3")
        self.emit("mul_skip:")
        self.emit("        ASL $FE         ; Shift multiplier left")
        self.emit("        ROL $FF")
        self.emit("        DEX")
        self.emit("        BNE mul_loop")
        self.emit("        LDA $F2")
        self.emit("        LDX $F3")
        self.emit("        RTS")
        self.emit("")
    
    def emit_divide_routine(self):
        """Emit 16-bit divide routine (A:X / $FE:$FF -> A:X)"""
        self.emit("; 16-bit divide: (A:X) / ($FE:$FF) -> (A:X)")
        self.emit("divide:")
        self.emit("        STA $F0         ; dividend low")
        self.emit("        STX $F1         ; dividend high")
        self.emit("        LDA #$00")
        self.emit("        STA $F2         ; result low")
        self.emit("        STA $F3         ; result high")
        self.emit("        LDX #$10        ; 16 bits")
        self.emit("div_loop:")
        self.emit("        ASL $F0         ; Shift dividend left")
        self.emit("        ROL $F1")
        self.emit("        ROL $F2")
        self.emit("        ROL $F3")
        self.emit("        LDA $F2")
        self.emit("        SEC")
        self.emit("        SBC $FE")
        self.emit("        TAY")
        self.emit("        LDA $F3")
        self.emit("        SBC $FF")
        self.emit("        BCC div_skip")
        self.emit("        STA $F3")
        self.emit("        STY $F2")
        self.emit("        INC $F0")
        self.emit("div_skip:")
        self.emit("        DEX")
        self.emit("        BNE div_loop")
        self.emit("        LDA $F0")
        self.emit("        LDX $F1")
        self.emit("        RTS")
        self.emit("")
    
    def emit_screen_output_routine(self):
        """Emit screen output routine for OUT statement"""
        self.emit("; Screen output: Write value in A:X to screen")
        self.emit("screen_out:")
        self.emit("        PHA             ; Save value")
        self.emit("        LDA $D002       ; Get cursor X")
        self.emit("        CLC")
        self.emit("        ADC #$01        ; Increment")
        self.emit("        CMP #$28        ; 40 columns?")
        self.emit("        BNE so_no_wrap")
        self.emit("        LDA #$00        ; Wrap to 0")
        self.emit("        PHA")
        self.emit("        LDA $D003       ; Increment Y")
        self.emit("        CLC")
        self.emit("        ADC #$01")
        self.emit("        CMP #$1E        ; 30 rows?")
        self.emit("        BNE so_save_y")
        self.emit("        LDA #$00        ; Wrap")
        self.emit("so_save_y:")
        self.emit("        STA $D003")
        self.emit("        PLA")
        self.emit("so_no_wrap:")
        self.emit("        STA $D002       ; Save cursor X")
        self.emit("        PLA             ; Restore value")
        self.emit("        LDX $D003       ; Y position")
        self.emit("        LDY $D002       ; X position")
        self.emit("        ; Calculate screen offset")
        self.emit("        RTS")
        self.emit("")


# MAIN COMPILER INTERFACE

def compile_pl0(source: str) -> str:
    """Compile PL/0 source to 6502 assembly"""
    parser = PL0Parser()
    ast = parser.parse(source)
    
    generator = CodeGenerator()
    assembly = generator.compile(ast)
    
    return assembly



# COMMAND-LINE INTERFACE

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="PL/0 to 6502 Compiler with I/O Extensions",
        epilog="Example: python compiler.py <source.pl0> <program.asm>"
    )
    parser.add_argument("input_file", help="Path to the PL/0 source file")
    parser.add_argument("output_file", nargs="?", help="Path to the output assembly file (optional; prints to stdout if omitted)")

    args = parser.parse_args()

    try:
        with open(args.input_file, "r") as f:
            source = f.read()

        assembly = compile_pl0(source)

        if args.output_file:
            with open(args.output_file, "w") as f:
                f.write(assembly)
            print(f"Compilation successful! Assembly saved to '{args.output_file}'")
        else:
            print(assembly)
            print("\nCompilation successful!")

    except FileNotFoundError:
        print(f"Error: Input file '{args.input_file}' not found.")
    except SyntaxError as e:
        print(f"Syntax error: {e}")
    except NameError as e:
        print(f"Semantic error: {e}")
    except Exception as e:
        print(f"Unexpected error during compilation: {e}")
        traceback.print_exc()

