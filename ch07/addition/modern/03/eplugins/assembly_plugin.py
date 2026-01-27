#!/usr/bin/env python3

from compiler_core import Plugin, ASTNode, CompilerContext, MessageCollector, Visitor
from compiler_core import BlockNode, NestedBlockNode, AssignNode, CallNode, ReadNode, WriteNode
from compiler_core import CompoundNode, IfNode, WhileNode, OperationNode, VariableNode, NumberNode
from typing import Dict, Any, Set, List


class AssemblyGeneratorPlugin(Plugin):
    def __init__(self):
        super().__init__(
            "assembly_generator",
            "Generates x86-64 assembly code from PL/0 AST",
            "1.0"
        )
        self.dependencies = ["static_analysis"]
        self.enabled = True
    
    def run(self, ast: ASTNode, context: CompilerContext, messages: MessageCollector) -> Dict[str, Any]:
        messages.debug("Starting assembly_generator plugin", source="AssemblyGenerator")
        
        # First run metrics analysis
        metrics_analyzer = CodeMetricsPlugin()
        metrics = metrics_analyzer.run(ast, context, messages)
        
        # Generate assembly code
        generator = AssemblyCodeGenerator(messages)
        asm_code = generator.generate(ast)
        
        # Store outputs
        context.generated_outputs["asm_code"] = asm_code
        context.generated_outputs["asm_metrics"] = generator.generate_metrics_report()
        
        messages.debug("Completed assembly_generator plugin", source="AssemblyGenerator")
        return {
            "instructions_generated": generator.instruction_count,
            "registers_used": len(generator.used_registers),
            "procedures_count": generator.procedure_count
        }

class CodeMetricsPlugin(Plugin):
    def __init__(self):
        super().__init__(
            "code_metrics",
            "Computes code quality metrics for PL/0 programs",
            "1.0"
        )
        self.dependencies = ["static_analysis", "statement_counter"]
        self.enabled = True
    
    def run(self, ast: ASTNode, context: CompilerContext, messages: MessageCollector) -> Dict[str, Any]:
        messages.debug("Starting code_metrics plugin", source="CodeMetrics")
        analyzer = MetricsAnalyzer(messages)
        metrics = analyzer.analyze(ast)
        context.generated_outputs["metrics_report"] = analyzer.generate_report()
        messages.debug("Completed code_metrics plugin", source="CodeMetrics")
        return metrics

class MetricsAnalyzer(Visitor):
    def __init__(self, messages: MessageCollector):
        self.messages = messages
        self.metrics = {
            "procedure_count": 0,
            "variable_usage": {},
            "statement_density": {},
            "complexity_scores": {}
        }
        self.current_procedure = None
        self.statement_count = 0
    
    def analyze(self, ast: ASTNode) -> Dict[str, Any]:
        ast.accept(self)
        return self.metrics
    
    def generate_report(self) -> str:
        lines = [
            "Code Metrics Report",
            "=" * 20,
            f"Total Procedures: {self.metrics['procedure_count']}",
            "Variable Usage:"
        ]
        for var, count in self.metrics["variable_usage"].items():
            lines.append(f"  • {var}: {count} uses")
        lines.append("Procedure Complexity:")
        for proc, score in self.metrics["complexity_scores"].items():
            lines.append(f"  • {proc}: {score} statements")
        return "\n".join(lines)
    
    def visit_block(self, node: BlockNode):
        self.metrics["procedure_count"] += len(node.procedures)
        for proc_name, proc_body in node.procedures:
            self.current_procedure = proc_name
            old_count = self.statement_count
            proc_body.accept(self)
            self.metrics["complexity_scores"][proc_name] = self.statement_count - old_count
            self.current_procedure = None
        node.statement.accept(self)
    
    def visit_nested_block(self, node: NestedBlockNode):
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_assign(self, node: AssignNode):
        self.statement_count += 1
        node.expression.accept(self)
    
    def visit_call(self, node: CallNode):
        self.statement_count += 1
    
    def visit_read(self, node: ReadNode):
        self.statement_count += 1
    
    def visit_write(self, node: WriteNode):
        self.statement_count += 1
        node.expression.accept(self)
    
    def visit_compound(self, node: CompoundNode):
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_if(self, node: IfNode):
        self.statement_count += 1
        node.condition.accept(self)
        node.then_statement.accept(self)
    
    def visit_while(self, node: WhileNode):
        self.statement_count += 1
        node.condition.accept(self)
        node.body.accept(self)
    
    def visit_operation(self, node: OperationNode):
        node.left.accept(self)
        node.right.accept(self)
    
    def visit_variable(self, node: VariableNode):
        self.metrics["variable_usage"][node.name] = self.metrics["variable_usage"].get(node.name, 0) + 1
    
    def visit_number(self, node: NumberNode):
        pass

class AssemblyCodeGenerator(Visitor):
    def __init__(self, messages: MessageCollector):
        self.messages = messages
        self.code = []
        self.instruction_count = 0
        self.procedure_count = 0
        self.used_registers = set()
        self.variable_offsets = {}  # Map variables to stack offsets
        self.current_offset = 0
        self.label_counter = 0
    
    def generate(self, ast: ASTNode) -> str:
        # Assembly header
        self.add_line(".section .data")
        self.add_line("format_int: .asciz \"%d\\n\"")
        self.add_line("scan_int: .asciz \"%d\"")
        self.add_line("")
        self.add_line(".section .text")
        self.add_line(".global _start")
        self.add_line("")
        self.add_line("_start:")
        
        # Set up stack frame
        self.add_line("    pushq %rbp")
        self.add_line("    movq %rsp, %rbp")
        
        # Generate code for AST
        ast.accept(self)
        
        # Program exit
        self.add_line("    # Program exit")
        self.add_line("    movq $60, %rax")
        self.add_line("    xorq %rdi, %rdi")
        self.add_line("    syscall")
        
        return "\n".join(self.code)
    
    def add_line(self, line: str):
        self.code.append(line)
        if line.strip() and not line.startswith("#") and not line.endswith(":"):
            self.instruction_count += 1
    
    def get_next_label(self) -> str:
        self.label_counter += 1
        return f"L{self.label_counter}"
    
    def allocate_variable(self, var_name: str) -> int:
        if var_name not in self.variable_offsets:
            self.current_offset -= 8  # 8 bytes for each variable
            self.variable_offsets[var_name] = self.current_offset
        return self.variable_offsets[var_name]
    
    def generate_metrics_report(self) -> str:
        lines = [
            "Assembly Generation Metrics",
            "=" * 30,
            f"Instructions Generated: {self.instruction_count}",
            f"Procedures: {self.procedure_count}",
            f"Registers Used: {len(self.used_registers)}",
            f"Variables Allocated: {len(self.variable_offsets)}",
            f"Stack Space Used: {abs(self.current_offset)} bytes"
        ]
        if self.used_registers:
            lines.append(f"Used Registers: {', '.join(sorted(self.used_registers))}")
        return "\n".join(lines)
    
    def visit_block(self, node: BlockNode):
        # Allocate space for variables
        for var in node.variables:
            self.allocate_variable(var)
        
        # Generate procedures
        for proc_name, proc_body in node.procedures:
            self.procedure_count += 1
            self.add_line(f"{proc_name}:")
            self.add_line("    pushq %rbp")
            self.add_line("    movq %rsp, %rbp")
            proc_body.accept(self)
            self.add_line("    popq %rbp")
            self.add_line("    ret")
            self.add_line("")
        
        # Generate main statement
        node.statement.accept(self)
    
    def visit_nested_block(self, node: NestedBlockNode):
        # Allocate space for local variables
        for var in node.variables:
            self.allocate_variable(var)
        
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_assign(self, node: AssignNode):
        # Generate code for expression
        self.add_line(f"    # Assignment: {node.var_name} = expression")
        node.expression.accept(self)
        
        # Store result in variable
        offset = self.variable_offsets[node.var_name]
        self.add_line(f"    movq %rax, {offset}(%rbp)")
        self.used_registers.add("rax")
    
    def visit_call(self, node: CallNode):
        self.add_line(f"    # Call procedure: {node.proc_name}")
        self.add_line(f"    call {node.proc_name}")
    
    def visit_read(self, node: ReadNode):
        self.add_line(f"    # Read input into {node.var_name}")
        offset = self.variable_offsets[node.var_name]
        
        # System call for reading integer
        self.add_line("    movq $0, %rax")  # sys_read
        self.add_line("    movq $0, %rdi")  # stdin
        self.add_line(f"    leaq {offset}(%rbp), %rsi")  # buffer
        self.add_line("    movq $8, %rdx")  # count
        self.add_line("    syscall")
        
        self.used_registers.update(["rax", "rdi", "rsi", "rdx"])
    
    def visit_write(self, node: WriteNode):
        self.add_line("    # Write expression result")
        node.expression.accept(self)
        
        # Print the value in %rax
        self.add_line("    movq %rax, %rsi")
        self.add_line("    movq $format_int, %rdi")
        self.add_line("    movq $0, %rax")
        self.add_line("    call printf")
        
        self.used_registers.update(["rax", "rdi", "rsi"])
    
    def visit_compound(self, node: CompoundNode):
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_if(self, node: IfNode):
        end_label = self.get_next_label()
        
        self.add_line("    # If statement")
        node.condition.accept(self)
        self.add_line("    testq %rax, %rax")
        self.add_line(f"    jz {end_label}")
        
        node.then_statement.accept(self)
        self.add_line(f"{end_label}:")
        
        self.used_registers.add("rax")
    
    def visit_while(self, node: WhileNode):
        loop_label = self.get_next_label()
        end_label = self.get_next_label()
        
        self.add_line("    # While loop")
        self.add_line(f"{loop_label}:")
        node.condition.accept(self)
        self.add_line("    testq %rax, %rax")
        self.add_line(f"    jz {end_label}")
        
        node.body.accept(self)
        self.add_line(f"    jmp {loop_label}")
        self.add_line(f"{end_label}:")
        
        self.used_registers.add("rax")
    
    def visit_operation(self, node: OperationNode):
        # Generate code for left operand
        node.left.accept(self)
        self.add_line("    pushq %rax")  # Save left operand
        
        # Generate code for right operand
        node.right.accept(self)
        self.add_line("    movq %rax, %rbx")  # Right operand in %rbx
        self.add_line("    popq %rax")       # Left operand back in %rax
        
        # Perform operation
        if node.operator == "+":
            self.add_line("    addq %rbx, %rax")
        elif node.operator == "-":
            self.add_line("    subq %rbx, %rax")
        elif node.operator == "*":
            self.add_line("    imulq %rbx, %rax")
        elif node.operator == "/":
            self.add_line("    cqto")  # Sign extend %rax to %rdx:%rax
            self.add_line("    idivq %rbx")
        elif node.operator == "=":
            self.add_line("    cmpq %rbx, %rax")
            self.add_line("    sete %al")
            self.add_line("    movzbq %al, %rax")
        elif node.operator == "<":
            self.add_line("    cmpq %rbx, %rax")
            self.add_line("    setl %al")
            self.add_line("    movzbq %al, %rax")
        elif node.operator == ">":
            self.add_line("    cmpq %rbx, %rax")
            self.add_line("    setg %al")
            self.add_line("    movzbq %al, %rax")
        elif node.operator == "<=":
            self.add_line("    cmpq %rbx, %rax")
            self.add_line("    setle %al")
            self.add_line("    movzbq %al, %rax")
        elif node.operator == ">=":
            self.add_line("    cmpq %rbx, %rax")
            self.add_line("    setge %al")
            self.add_line("    movzbq %al, %rax")
        
        self.used_registers.update(["rax", "rbx", "rdx"])
    
    def visit_variable(self, node: VariableNode):
        offset = self.variable_offsets[node.name]
        self.add_line(f"    movq {offset}(%rbp), %rax")
        self.used_registers.add("rax")
    
    def visit_number(self, node: NumberNode):
        self.add_line(f"    movq ${node.value}, %rax")
        self.used_registers.add("rax")