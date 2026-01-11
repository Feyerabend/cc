"""
6502 Assembler
Supports standard 6502 mnemonics, addressing modes, and some common assembler directives.
"""

import pyparsing as pp
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


# CONSTANTS AND TABLES

# Addressing modes for each opcode (0x00-0xFF)
ADDR_MODES = [
    'imp', 'indx', 'imp', 'indx', 'zp', 'zp', 'zp', 'zp', 'imp', 'imm', 'acc', 'imm', 'abso', 'abso', 'abso', 'abso',
    'rel', 'indy', 'imp', 'indy', 'zpx', 'zpx', 'zpx', 'zpx', 'imp', 'absy', 'imp', 'absy', 'absx', 'absx', 'absx', 'absx',
    'abso', 'indx', 'imp', 'indx', 'zp', 'zp', 'zp', 'zp', 'imp', 'imm', 'acc', 'imm', 'abso', 'abso', 'abso', 'abso',
    'rel', 'indy', 'imp', 'indy', 'zpx', 'zpx', 'zpx', 'zpx', 'imp', 'absy', 'imp', 'absy', 'absx', 'absx', 'absx', 'absx',
    'imp', 'indx', 'imp', 'indx', 'zp', 'zp', 'zp', 'zp', 'imp', 'imm', 'acc', 'imm', 'abso', 'abso', 'abso', 'abso',
    'rel', 'indy', 'imp', 'indy', 'zpx', 'zpx', 'zpx', 'zpx', 'imp', 'absy', 'imp', 'absy', 'absx', 'absx', 'absx', 'absx',
    'imp', 'indx', 'imp', 'indx', 'zp', 'zp', 'zp', 'zp', 'imp', 'imm', 'acc', 'imm', 'ind', 'abso', 'abso', 'abso',
    'rel', 'indy', 'imp', 'indy', 'zpx', 'zpx', 'zpx', 'zpx', 'imp', 'absy', 'imp', 'absy', 'absx', 'absx', 'absx', 'absx',
    'imm', 'indx', 'imm', 'indx', 'zp', 'zp', 'zp', 'zp', 'imp', 'imm', 'imp', 'imm', 'abso', 'abso', 'abso', 'abso',
    'rel', 'indy', 'imp', 'indy', 'zpx', 'zpx', 'zpy', 'zpy', 'imp', 'absy', 'imp', 'absy', 'absx', 'absx', 'absy', 'absy',
    'imm', 'indx', 'imm', 'indx', 'zp', 'zp', 'zp', 'zp', 'imp', 'imm', 'imp', 'imm', 'abso', 'abso', 'abso', 'abso',
    'rel', 'indy', 'imp', 'indy', 'zpx', 'zpx', 'zpy', 'zpy', 'imp', 'absy', 'imp', 'absy', 'absx', 'absx', 'absy', 'absy',
    'imm', 'indx', 'imm', 'indx', 'zp', 'zp', 'zp', 'zp', 'imp', 'imm', 'imp', 'imm', 'abso', 'abso', 'abso', 'abso',
    'rel', 'indy', 'imp', 'indy', 'zpx', 'zpx', 'zpx', 'zpx', 'imp', 'absy', 'imp', 'absy', 'absx', 'absx', 'absx', 'absx',
    'imm', 'indx', 'imm', 'indx', 'zp', 'zp', 'zp', 'zp', 'imp', 'imm', 'imp', 'imm', 'abso', 'abso', 'abso', 'abso',
    'rel', 'indy', 'imp', 'indy', 'zpx', 'zpx', 'zpx', 'zpx', 'imp', 'absy', 'imp', 'absy', 'absx', 'absx', 'absx', 'absx'
]

# Mnemonics for each opcode (0x00-0xFF)
MNEMONICS = [
    'brk', 'ora', 'jam', 'slo', 'nop', 'ora', 'asl', 'slo', 'php', 'ora', 'asl', 'anc', 'nop', 'ora', 'asl', 'slo',
    'bpl', 'ora', 'jam', 'slo', 'nop', 'ora', 'asl', 'slo', 'clc', 'ora', 'nop', 'slo', 'nop', 'ora', 'asl', 'slo',
    'jsr', 'and', 'jam', 'rla', 'bit', 'and', 'rol', 'rla', 'plp', 'and', 'rol', 'anc', 'bit', 'and', 'rol', 'rla',
    'bmi', 'and', 'jam', 'rla', 'nop', 'and', 'rol', 'rla', 'sec', 'and', 'nop', 'rla', 'nop', 'and', 'rol', 'rla',
    'rti', 'eor', 'jam', 'sre', 'nop', 'eor', 'lsr', 'sre', 'pha', 'eor', 'lsr', 'alr', 'jmp', 'eor', 'lsr', 'sre',
    'bvc', 'eor', 'jam', 'sre', 'nop', 'eor', 'lsr', 'sre', 'cli', 'eor', 'nop', 'sre', 'nop', 'eor', 'lsr', 'sre',
    'rts', 'adc', 'jam', 'rra', 'nop', 'adc', 'ror', 'rra', 'pla', 'adc', 'ror', 'arr', 'jmp', 'adc', 'ror', 'rra',
    'bvs', 'adc', 'jam', 'rra', 'nop', 'adc', 'ror', 'rra', 'sei', 'adc', 'nop', 'rra', 'nop', 'adc', 'ror', 'rra',
    'nop', 'sta', 'nop', 'sax', 'sty', 'sta', 'stx', 'sax', 'dey', 'nop', 'txa', 'ane', 'sty', 'sta', 'stx', 'sax',
    'bcc', 'sta', 'jam', 'sha', 'sty', 'sta', 'stx', 'sax', 'tya', 'sta', 'txs', 'tas', 'shy', 'sta', 'shx', 'sha',
    'ldy', 'lda', 'ldx', 'lax', 'ldy', 'lda', 'ldx', 'lax', 'tay', 'lda', 'tax', 'lxa', 'ldy', 'lda', 'ldx', 'lax',
    'bcs', 'lda', 'jam', 'lax', 'ldy', 'lda', 'ldx', 'lax', 'clv', 'lda', 'tsx', 'las', 'ldy', 'lda', 'ldx', 'lax',
    'cpy', 'cmp', 'nop', 'dcp', 'cpy', 'cmp', 'dec', 'dcp', 'iny', 'cmp', 'dex', 'sbx', 'cpy', 'cmp', 'dec', 'dcp',
    'bne', 'cmp', 'jam', 'dcp', 'nop', 'cmp', 'dec', 'dcp', 'cld', 'cmp', 'nop', 'dcp', 'nop', 'cmp', 'dec', 'dcp',
    'cpx', 'sbc', 'nop', 'isc', 'cpx', 'sbc', 'inc', 'isc', 'inx', 'sbc', 'nop', 'sbc', 'cpx', 'sbc', 'inc', 'isc',
    'beq', 'sbc', 'jam', 'isc', 'nop', 'sbc', 'inc', 'isc', 'sed', 'sbc', 'nop', 'isc', 'nop', 'sbc', 'inc', 'isc'
]

# Build opcode lookup table: opcodes[mnemonic][mode] -> opcode_byte
OPCODES: Dict[str, Dict[str, int]] = {}
for i in range(256):
    mnem = MNEMONICS[i]
    mode = ADDR_MODES[i]
    if mnem not in OPCODES:
        OPCODES[mnem] = {}
    OPCODES[mnem][mode] = i

# Branch instructions (use relative addressing)
BRANCH_MNEMONICS = {'bcc', 'bcs', 'beq', 'bmi', 'bne', 'bpl', 'bvc', 'bvs'}

# Accumulator-mode instructions
ACCUMULATOR_MNEMONICS = {'asl', 'lsr', 'rol', 'ror'}


# DATA STRUCTURES

class AddrMode(Enum):
    """Addressing modes"""
    IMPLIED = 'imp'
    ACCUMULATOR = 'acc'
    IMMEDIATE = 'imm'
    ZEROPAGE = 'zp'
    ZEROPAGE_X = 'zpx'
    ZEROPAGE_Y = 'zpy'
    ABSOLUTE = 'abso'
    ABSOLUTE_X = 'absx'
    ABSOLUTE_Y = 'absy'
    INDIRECT = 'ind'
    INDIRECT_X = 'indx'
    INDIRECT_Y = 'indy'
    RELATIVE = 'rel'

@dataclass
class Expression:
    """Represents an evaluated or unevaluated expression"""
    value: Optional[int] = None
    ast: Any = None
    
    def is_resolved(self) -> bool:
        return self.value is not None

@dataclass
class Operand:
    """Represents an instruction operand"""
    mode: AddrMode
    expr: Expression
    
@dataclass
class Instruction:
    """Represents a 6502 instruction"""
    mnemonic: str
    operand: Optional[Operand]
    line_num: int
    
@dataclass
class Directive:
    """Represents an assembler directive"""
    name: str
    args: List[Any]
    line_num: int

@dataclass
class Label:
    """Represents a label definition"""
    name: str
    value: Optional[int]  # None for forward references
    line_num: int

@dataclass
class Line:
    """Represents a line of assembly"""
    label: Optional[Label]
    statement: Optional[Any]  # Instruction, Directive, or None
    line_num: int
    source: str


# EXPRESSIONS

class ExpressionEvaluator:
    """Evaluates arithmetic expressions with symbols"""
    
    def __init__(self, symbols: Dict[str, int], pc: int, line_num: int):
        self.symbols = symbols
        self.pc = pc
        self.line_num = line_num
    
    def evaluate(self, ast: Any, allow_unresolved: bool = False) -> Optional[int]:
        """
        Evaluate an expression AST.
        
        AST formats:
        - int: literal value
        - str: symbol or '*' for PC
        - list: [operand] or [left, op, right] or [left, [[op, right], ...]]
        """
        # Handle ParseResults
        if isinstance(ast, pp.ParseResults):
            ast = ast.asList()
        
        # Literal integer
        if isinstance(ast, int):
            return ast
        
        # Symbol or PC
        if isinstance(ast, str):
            if ast == '':
                raise ValueError(f"Line {self.line_num}: Empty symbol")
            if ast == '*':
                return self.pc
            if ast in self.symbols:
                return self.symbols[ast]
            if allow_unresolved:
                return None
            raise KeyError(f"Line {self.line_num}: Undefined symbol '{ast}'")
        
        # List - various formats
        if isinstance(ast, list):
            if len(ast) == 0:
                raise ValueError(f"Line {self.line_num}: Empty expression")
            
            # Single element: unwrap
            if len(ast) == 1:
                return self.evaluate(ast[0], allow_unresolved)
            
            # Three elements: [left, op, right] (simple binary)
            if len(ast) == 3 and isinstance(ast[1], str):
                return self._eval_binary(ast[0], ast[1], ast[2], allow_unresolved)
            
            # Two elements: [left, [[op, right], ...]] (infixNotation format)
            if len(ast) == 2 and isinstance(ast[1], list):
                result = self.evaluate(ast[0], allow_unresolved)
                if result is None and allow_unresolved:
                    return None
                
                for op_pair in ast[1]:
                    if isinstance(op_pair, list) and len(op_pair) == 2:
                        op, right_ast = op_pair
                        right = self.evaluate(right_ast, allow_unresolved)
                        if right is None and allow_unresolved:
                            return None
                        result = self._apply_op(result, op, right)
                
                return result
            
            # Unknown format
            raise ValueError(f"Line {self.line_num}: Unexpected expression structure: {ast}")
        
        raise ValueError(f"Line {self.line_num}: Invalid expression type: {type(ast)}")
    
    def _eval_binary(self, left_ast: Any, op: str, right_ast: Any, allow_unresolved: bool) -> Optional[int]:
        """Evaluate a binary operation"""
        left = self.evaluate(left_ast, allow_unresolved)
        if left is None and allow_unresolved:
            return None
        
        right = self.evaluate(right_ast, allow_unresolved)
        if right is None and allow_unresolved:
            return None
        
        return self._apply_op(left, op, right)
    
    def _apply_op(self, left: int, op: str, right: int) -> int:
        """Apply a binary operator"""
        if op == '+':
            return left + right
        elif op == '-':
            return left - right
        elif op == '*':
            return left * right
        elif op == '/':
            return left // right
        elif op == '%':
            return left % right
        else:
            raise ValueError(f"Line {self.line_num}: Unknown operator '{op}'")


# PARSE

class Parser:
    """Parses 6502 assembly source"""
    
    def __init__(self):
        self._build_grammar()
    
    def _build_grammar(self):
        """Build pyparsing grammar"""
        pp.ParserElement.setDefaultWhitespaceChars(' \t')
        
        # Numbers: $FF, 0xFF, %1010, 123, -5
        hex_num = pp.Combine(pp.Literal('$') + pp.Word(pp.hexnums))
        hex_num.setParseAction(lambda t: int(t[0][1:], 16))
        
        hex_num2 = pp.Combine(pp.Literal('0x') + pp.Word(pp.hexnums))
        hex_num2.setParseAction(lambda t: int(t[0][2:], 16))
        
        bin_num = pp.Combine(pp.Literal('%') + pp.Word('01'))
        bin_num.setParseAction(lambda t: int(t[0][1:], 2))
        
        dec_num = pp.Combine(pp.Optional(pp.Literal('-')) + pp.Word(pp.nums))
        dec_num.setParseAction(lambda t: int(t[0]))
        
        number = hex_num | hex_num2 | bin_num | dec_num
        
        # Symbol
        symbol = pp.Word(pp.alphas + '_', pp.alphanums + '_')
        
        # Expression (recursive)
        expr = pp.Forward()
        atom = number | symbol | pp.Literal('*') | pp.Group('(' + expr + ')')
        
        expr <<= pp.infixNotation(atom, [
            (pp.oneOf('* / %'), 2, pp.opAssoc.LEFT),
            (pp.oneOf('+ -'), 2, pp.opAssoc.LEFT),
        ])
        
        # Operands
        imm = pp.Suppress('#') + expr
        indx = pp.Suppress('(') + expr + pp.Suppress(',') + pp.CaselessLiteral('x') + pp.Suppress(')')
        indy = pp.Suppress('(') + expr + pp.Suppress(')') + pp.Suppress(',') + pp.CaselessLiteral('y')
        ind = pp.Suppress('(') + expr + pp.Suppress(')')
        commax = expr + pp.Suppress(',') + pp.CaselessLiteral('x')
        commay = expr + pp.Suppress(',') + pp.CaselessLiteral('y')
        acc_op = pp.CaselessLiteral('a')
        plain = expr
        
        # Tag operands for identification
        imm = imm('imm')
        indx = indx('indx')
        indy = indy('indy')
        ind = ind('ind')
        commax = commax('commax')
        commay = commay('commay')
        acc_op = acc_op('acc')
        plain = plain('plain')
        
        operand = imm | indx | indy | ind | commax | commay | acc_op | plain
        
        # Instruction
        mnem = pp.oneOf(list(OPCODES.keys()), caseless=True)
        instruction = pp.Group(mnem('mnem') + pp.Optional(operand))('instr')
        
        # Directives
        dir_org = pp.Suppress('.') + pp.Suppress(pp.CaselessLiteral('org')) + expr
        dir_org = dir_org('org')
        
        dir_byte = pp.Suppress('.') + pp.Suppress(pp.CaselessLiteral('byte')) + pp.delimitedList(expr)
        dir_byte = dir_byte('byte')
        
        dir_word = pp.Suppress('.') + pp.Suppress(pp.CaselessLiteral('word')) + pp.delimitedList(expr)
        dir_word = dir_word('word')
        
        dir_asc = pp.Suppress('.') + pp.Suppress(pp.CaselessLiteral('asc')) + pp.quotedString.setParseAction(pp.removeQuotes)
        dir_asc = dir_asc('asc')
        
        # Label and EQU
        label = pp.Word(pp.alphas + '_', pp.alphanums + '_')
        equ = label('label') + pp.Suppress('=') + expr('equ_val')
        label_def = label('label') + pp.Suppress(':')
        
        # Commands
        command = dir_org | dir_byte | dir_word | dir_asc | instruction
        
        # Full line
        line = pp.Optional(equ | label_def) + pp.Optional(command) + pp.StringEnd()
        
        self.line_parser = line
        self.expr_parser = expr
    
    def parse_line(self, source: str, line_num: int) -> Line:
        """Parse a single line of assembly"""
        # Strip comments
        source = source.split(';', 1)[0].strip()
        
        # Empty line
        if not source:
            return Line(None, None, line_num, source)
        
        try:
            result = self.line_parser.parseString(source, parseAll=True)
        except pp.ParseException as e:
            raise ValueError(f"Line {line_num}: Parse error: {e}")
        
        label = None
        statement = None
        
        # Extract label or EQU
        if 'equ_val' in result:
            # This is an EQU (label = value)
            label = Label(result['label'], None, line_num)
            statement = Directive('equ', [result['equ_val']], line_num)
        elif 'label' in result:
            # This is a label definition
            label = Label(result['label'], None, line_num)
        
        # Extract statement (directive or instruction)
        if 'org' in result:
            statement = Directive('org', [result['org']], line_num)
        elif 'byte' in result:
            statement = Directive('byte', list(result['byte']), line_num)
        elif 'word' in result:
            statement = Directive('word', list(result['word']), line_num)
        elif 'asc' in result:
            statement = Directive('asc', [result['asc']], line_num)
        elif 'instr' in result:
            instr = result['instr']
            mnem = instr['mnem'].lower()
            operand = self._parse_operand(instr)
            statement = Instruction(mnem, operand, line_num)
        
        return Line(label, statement, line_num, source)
    
    def _parse_operand(self, instr: pp.ParseResults) -> Optional[Operand]:
        """Parse instruction operand"""
        if 'imm' in instr:
            return Operand(AddrMode.IMMEDIATE, Expression(ast=instr['imm']))
        elif 'indx' in instr:
            return Operand(AddrMode.INDIRECT_X, Expression(ast=instr['indx'][0]))
        elif 'indy' in instr:
            return Operand(AddrMode.INDIRECT_Y, Expression(ast=instr['indy'][0]))
        elif 'ind' in instr:
            return Operand(AddrMode.INDIRECT, Expression(ast=instr['ind']))
        elif 'commax' in instr:
            return Operand(AddrMode.ABSOLUTE_X, Expression(ast=instr['commax'][0]))
        elif 'commay' in instr:
            return Operand(AddrMode.ABSOLUTE_Y, Expression(ast=instr['commay'][0]))
        elif 'acc' in instr:
            return Operand(AddrMode.ACCUMULATOR, Expression(value=0))
        elif 'plain' in instr:
            return Operand(AddrMode.ABSOLUTE, Expression(ast=instr['plain']))
        else:
            return None


# ASSEMBLER

class Assembler:
    """Two-pass 6502 assembler"""
    
    def __init__(self, verbose: bool = False):
        self.parser = Parser()
        self.verbose = verbose
        self.symbols: Dict[str, int] = {}
        self.memory: Dict[int, int] = {}
        self.address = 0
    
    def assemble(self, source: str) -> bytes:
        """Assemble source code to binary"""
        lines = source.splitlines()
        parsed_lines = []
        
        # Parse all lines
        for line_num, line in enumerate(lines, 1):
            parsed = self.parser.parse_line(line, line_num)
            parsed_lines.append(parsed)
        
        # Pass 1: Build symbol table and calculate addresses
        self._pass1(parsed_lines)
        
        # Pass 2: Generate code
        self._pass2(parsed_lines)
        
        # Convert memory dict to bytes
        return self._memory_to_bytes()
    
    def _pass1(self, lines: List[Line]):
        """Pass 1: Build symbol table"""
        self.address = 0
        self.symbols = {}
        
        for line in lines:
            # Handle .org directive BEFORE processing labels
            if isinstance(line.statement, Directive) and line.statement.name == 'org':
                evaluator = ExpressionEvaluator(self.symbols, self.address, line.line_num)
                self.address = evaluator.evaluate(line.statement.args[0])
                if self.verbose:
                    print(f"Pass1 L{line.line_num}: .org ${self.address:04X}")
                continue
            
            if line.label:
                if isinstance(line.statement, Directive) and line.statement.name == 'equ':
                    # EQU: evaluate immediately
                    evaluator = ExpressionEvaluator(self.symbols, self.address, line.line_num)
                    value = evaluator.evaluate(line.statement.args[0])
                    self.symbols[line.label.name] = value
                    if self.verbose:
                        print(f"Pass1 L{line.line_num}: {line.label.name} = ${value:04X}")
                else:
                    # Label: assign current address
                    self.symbols[line.label.name] = self.address
                    if self.verbose:
                        print(f"Pass1 L{line.line_num}: {line.label.name}: @ ${self.address:04X}")
            
            # Update address based on statement (skip org and equ)
            if line.statement:
                if isinstance(line.statement, Directive) and line.statement.name in ['org', 'equ']:
                    continue
                self.address += self._statement_size(line.statement, line.line_num)
    
    def _statement_size(self, stmt: Any, line_num: int) -> int:
        """Calculate size of a statement (does NOT modify address)"""
        if isinstance(stmt, Directive):
            if stmt.name == 'org':
                # .org doesn't contribute to size, it changes address
                # This should not be called for .org (handled separately in pass1)
                return 0
            elif stmt.name == 'byte':
                return len(stmt.args)
            elif stmt.name == 'word':
                return len(stmt.args) * 2
            elif stmt.name == 'asc':
                return len(stmt.args[0])
            elif stmt.name == 'equ':
                return 0
        
        elif isinstance(stmt, Instruction):
            return self._instruction_size(stmt, line_num)
        
        return 0
    
    def _instruction_size(self, instr: Instruction, line_num: int) -> int:
        """Calculate size of an instruction"""
        if instr.operand is None:
            return 1  # Implied or accumulator
        
        mode = instr.operand.mode
        
        if mode == AddrMode.ACCUMULATOR:
            return 1
        elif mode in [AddrMode.IMMEDIATE, AddrMode.INDIRECT_X, AddrMode.INDIRECT_Y]:
            return 2
        elif mode == AddrMode.INDIRECT:
            return 3
        elif mode in [AddrMode.ABSOLUTE_X, AddrMode.ABSOLUTE_Y, AddrMode.ABSOLUTE]:
            # May be zero page - need to evaluate
            evaluator = ExpressionEvaluator(self.symbols, self.address, line_num)
            value = evaluator.evaluate(instr.operand.expr.ast, allow_unresolved=True)
            
            # If branch, always 2 bytes (relative)
            if instr.mnemonic in BRANCH_MNEMONICS:
                return 2
            
            # Check if zero page
            if value is not None and 0 <= value < 256 and mode == AddrMode.ABSOLUTE:
                return 2  # Zero page
            
            # Default to absolute
            return 3 if value is None or value >= 256 else 2
        
        return 2  # Default
    
    def _pass2(self, lines: List[Line]):
        """Pass 2: Generate code"""
        self.address = 0
        self.memory = {}
        
        for line in lines:
            if line.statement:
                self._generate_statement(line.statement, line.line_num)
    
    def _generate_statement(self, stmt: Any, line_num: int):
        """Generate code for a statement"""
        if isinstance(stmt, Directive):
            self._generate_directive(stmt, line_num)
        elif isinstance(stmt, Instruction):
            self._generate_instruction(stmt, line_num)
    
    def _generate_directive(self, directive: Directive, line_num: int):
        """Generate code for a directive"""
        evaluator = ExpressionEvaluator(self.symbols, self.address, line_num)
        
        if directive.name == 'org':
            self.address = evaluator.evaluate(directive.args[0])
        
        elif directive.name == 'byte':
            for arg in directive.args:
                value = evaluator.evaluate(arg)
                self.memory[self.address] = value & 0xFF
                self.address += 1
        
        elif directive.name == 'word':
            for arg in directive.args:
                value = evaluator.evaluate(arg)
                self.memory[self.address] = value & 0xFF
                self.memory[self.address + 1] = (value >> 8) & 0xFF
                self.address += 2
        
        elif directive.name == 'asc':
            text = directive.args[0]
            # Handle if text is wrapped in ParseResults or other container
            if hasattr(text, '__iter__') and not isinstance(text, str):
                text = text[0] if len(text) > 0 else ""
            # Now iterate over each character
            for char in str(text):
                self.memory[self.address] = ord(char)
                self.address += 1
        
        elif directive.name == 'equ':
            pass  # Already handled in pass 1
    
    def _generate_instruction(self, instr: Instruction, line_num: int):
        """Generate code for an instruction"""
        pc = self.address
        evaluator = ExpressionEvaluator(self.symbols, pc, line_num)
        
        # Determine addressing mode
        if instr.operand is None:
            # Implied or accumulator
            if instr.mnemonic in ACCUMULATOR_MNEMONICS:
                mode_str = 'acc'
            else:
                mode_str = 'imp'
            self._emit_opcode(instr.mnemonic, mode_str, line_num)
            self.address += 1
        
        elif instr.operand.mode == AddrMode.ACCUMULATOR:
            self._emit_opcode(instr.mnemonic, 'acc', line_num)
            self.address += 1
        
        elif instr.operand.mode == AddrMode.IMMEDIATE:
            value = evaluator.evaluate(instr.operand.expr.ast)
            self._emit_opcode(instr.mnemonic, 'imm', line_num)
            self.memory[self.address + 1] = value & 0xFF
            self.address += 2
        
        elif instr.operand.mode == AddrMode.INDIRECT_X:
            value = evaluator.evaluate(instr.operand.expr.ast)
            self._emit_opcode(instr.mnemonic, 'indx', line_num)
            self.memory[self.address + 1] = value & 0xFF
            self.address += 2
        
        elif instr.operand.mode == AddrMode.INDIRECT_Y:
            value = evaluator.evaluate(instr.operand.expr.ast)
            self._emit_opcode(instr.mnemonic, 'indy', line_num)
            self.memory[self.address + 1] = value & 0xFF
            self.address += 2
        
        elif instr.operand.mode == AddrMode.INDIRECT:
            value = evaluator.evaluate(instr.operand.expr.ast)
            self._emit_opcode(instr.mnemonic, 'ind', line_num)
            self.memory[self.address + 1] = value & 0xFF
            self.memory[self.address + 2] = (value >> 8) & 0xFF
            self.address += 3
        
        elif instr.operand.mode == AddrMode.ABSOLUTE_X:
            value = evaluator.evaluate(instr.operand.expr.ast)
            is_zp = 0 <= value < 256
            mode_str = 'zpx' if is_zp else 'absx'
            self._emit_opcode(instr.mnemonic, mode_str, line_num)
            if is_zp:
                self.memory[self.address + 1] = value & 0xFF
                self.address += 2
            else:
                self.memory[self.address + 1] = value & 0xFF
                self.memory[self.address + 2] = (value >> 8) & 0xFF
                self.address += 3
        
        elif instr.operand.mode == AddrMode.ABSOLUTE_Y:
            value = evaluator.evaluate(instr.operand.expr.ast)
            is_zp = 0 <= value < 256
            mode_str = 'zpy' if is_zp else 'absy'
            self._emit_opcode(instr.mnemonic, mode_str, line_num)
            if is_zp:
                self.memory[self.address + 1] = value & 0xFF
                self.address += 2
            else:
                self.memory[self.address + 1] = value & 0xFF
                self.memory[self.address + 2] = (value >> 8) & 0xFF
                self.address += 3
        
        elif instr.operand.mode == AddrMode.ABSOLUTE:
            value = evaluator.evaluate(instr.operand.expr.ast)
            is_branch = instr.mnemonic in BRANCH_MNEMONICS
            is_zp = 0 <= value < 256
            
            if is_branch:
                # Relative addressing
                self._emit_opcode(instr.mnemonic, 'rel', line_num)
                offset = value - (pc + 2)
                if not -128 <= offset <= 127:
                    raise ValueError(f"Line {line_num}: Branch offset {offset} out of range")
                self.memory[self.address + 1] = offset & 0xFF
                self.address += 2
            elif is_zp:
                # Zero page
                self._emit_opcode(instr.mnemonic, 'zp', line_num)
                self.memory[self.address + 1] = value & 0xFF
                self.address += 2
            else:
                # Absolute
                self._emit_opcode(instr.mnemonic, 'abso', line_num)
                self.memory[self.address + 1] = value & 0xFF
                self.memory[self.address + 2] = (value >> 8) & 0xFF
                self.address += 3
    
    def _emit_opcode(self, mnemonic: str, mode: str, line_num: int):
        """Emit an opcode byte"""
        if mode not in OPCODES[mnemonic]:
            raise ValueError(f"Line {line_num}: Invalid addressing mode '{mode}' for '{mnemonic}'")
        
        opcode = OPCODES[mnemonic][mode]
        self.memory[self.address] = opcode
    
    def _memory_to_bytes(self) -> bytes:
        """Convert memory dictionary to contiguous bytes"""
        if not self.memory:
            return b''
        
        min_addr = min(self.memory.keys())
        max_addr = max(self.memory.keys())
        size = max_addr - min_addr + 1
        
        data = bytearray(size)
        for addr, value in self.memory.items():
            data[addr - min_addr] = value & 0xFF
        
        return bytes(data)


# ENTRY POINT FOR ASSEMBLER

def assemble(source: str, verbose: bool = False) -> bytes:
    """Assemble 6502 source code - main API"""
    assembler = Assembler(verbose=verbose)
    return assembler.assemble(source)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python asm.py <input.asm> [output.bin] [-v]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = 'a.bin'
    verbose = False
    
    for arg in sys.argv[2:]:
        if arg == '-v':
            verbose = True
        else:
            output_file = arg
    
    try:
        with open(input_file, 'r') as f:
            source = f.read()
        
        bin_data = assemble(source, verbose=verbose)
        
        with open(output_file, 'wb') as f:
            f.write(bin_data)
        
        print(f"Assembled {len(bin_data)} bytes to {output_file}")
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
