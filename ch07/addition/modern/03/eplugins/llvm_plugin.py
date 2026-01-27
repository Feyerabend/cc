#!/usr/bin/env python3

from compiler_core import Plugin, ASTNode, CompilerContext, MessageCollector, Visitor
from compiler_core import BlockNode, NestedBlockNode, AssignNode, CallNode, ReadNode, WriteNode
from compiler_core import CompoundNode, IfNode, WhileNode, OperationNode, VariableNode, NumberNode
from typing import Dict, Any, List, Optional


# do not work out of the box!
# should maybe roll from TAC instead of AST
class LLVMGeneratorPlugin(Plugin):
    def __init__(self):
        super().__init__(
            "llvm_generator",
            "Generates LLVM IR code from the AST",
            "1.0"
        )
        self.dependencies = ["static_analysis"]  # Ensure variables are checked first
        self.enabled = True
    
    def run(self, ast: ASTNode, context: CompilerContext, messages: MessageCollector) -> Dict[str, Any]:
        messages.debug("Starting llvm_generator plugin", source="LLVMGenerator")
        generator = LLVMCodeGenerator(messages)
        llvm_code = generator.generate(ast)
        
        # Store the generated code in context
        context.generated_outputs["llvm_code"] = llvm_code
        
        messages.debug("Completed llvm_generator plugin", source="LLVMGenerator")
        return {
            "generated": True,
            "lines": len(llvm_code.split('\n'))
        }

class LLVMCodeGenerator(Visitor):
    def __init__(self, messages: MessageCollector):
        self.messages = messages
        self.code = []
        self.temp_counter = 0
        self.label_counter = 0
        self.variable_types = {}  # Track variable types (all i32 for PL/0)
        self.current_function = "main"
        self.variable_scopes = [{}]  # Stack of variable scopes
        self.procedure_signatures = {}  # Track procedure parameters if needed
    
    def generate(self, ast: ASTNode) -> str:
        # Initialize LLVM IR with basic setup
        self.code.append("; ModuleID = 'pl0_program'")
        self.code.append("source_filename = \"pl0_program\"")
        self.code.append("target triple = \"x86_64-unknown-linux-gnu\"")
        self.code.append("")
        
        # Declare standard I/O functions
        self.code.append("declare i32 @printf(i8*, ...)")
        self.code.append("declare i32 @scanf(i8*, ...)")
        
        # String constants for I/O
        self.code.append("@.str.output = private unnamed_addr constant [4 x i8] c\"%d\\0A\\00\", align 1")
        self.code.append("@.str.input = private unnamed_addr constant [3 x i8] c\"%d\\00\", align 1")
        self.code.append("")
        
        # Generate procedures first, then main
        self._generate_procedures_first_pass(ast)
        
        # Start main function
        self.code.append("define i32 @main() {")
        self.code.append("entry:")
        ast.accept(self)
        self.code.append("    ret i32 0")
        self.code.append("}")
        
        return "\n".join(self.code)
    
    def _generate_procedures_first_pass(self, node: ASTNode):
        """First pass to generate all procedure definitions before main"""
        if isinstance(node, BlockNode):
            for proc_name, proc_body in node.procedures:
                self._generate_procedure(proc_name, proc_body)
    
    def _generate_procedure(self, proc_name: str, proc_body: ASTNode):
        """Generate a single procedure definition"""
        old_function = self.current_function
        old_temp_counter = self.temp_counter
        old_label_counter = self.label_counter
        
        self.current_function = proc_name
        self.temp_counter = 0
        self.label_counter = 0
        
        self.code.append(f"define void @{proc_name}() {{")
        self.code.append("entry:")
        
        # Push new scope for procedure
        self.variable_scopes.append({})
        
        proc_body.accept(self)
        
        # Pop procedure scope
        self.variable_scopes.pop()
        
        self.code.append("    ret void")
        self.code.append("}")
        self.code.append("")
        
        # Restore state
        self.current_function = old_function
        self.temp_counter = old_temp_counter
        self.label_counter = old_label_counter
    
    def add_line(self, line: str):
        self.code.append("    " + line)
    
    def add_label(self, label: str):
        self.code.append(f"{label}:")
    
    def new_temp(self) -> str:
        temp = f"%t{self.temp_counter}"
        self.temp_counter += 1
        return temp
    
    def new_label(self) -> str:
        label = f"L{self.label_counter}"
        self.label_counter += 1
        return label
    
    def declare_variable(self, var_name: str):
        """Declare a variable in the current scope"""
        self.variable_types[var_name] = "i32"
        self.variable_scopes[-1][var_name] = f"%{var_name}"
        self.add_line(f"%{var_name} = alloca i32, align 4")
    
    def get_variable_ref(self, var_name: str) -> str:
        """Get the LLVM reference for a variable"""
        # Search scopes from innermost to outermost
        for scope in reversed(self.variable_scopes):
            if var_name in scope:
                return scope[var_name]
        return f"%{var_name}"  # Fallback
    
    def visit_block(self, node: BlockNode):
        # Declare variables in current scope
        for var in node.variables:
            self.declare_variable(var)
        
        # Note: Procedures are already generated in first pass
        # Just visit the main statement
        if node.statement:
            node.statement.accept(self)
    
    def visit_nested_block(self, node: NestedBlockNode):
        # Push new scope for nested block
        self.variable_scopes.append({})
        
        # Declare variables in nested block
        for var in node.variables:
            self.declare_variable(var)
        
        # Execute statements
        for stmt in node.statements:
            stmt.accept(self)
        
        # Pop scope
        self.variable_scopes.pop()
    
    def visit_assign(self, node: AssignNode):
        expr_result = node.expression.accept(self)
        var_ref = self.get_variable_ref(node.var_name)
        self.add_line(f"store i32 {expr_result}, i32* {var_ref}, align 4")
    
    def visit_call(self, node: CallNode):
        self.add_line(f"call void @{node.proc_name}()")
    
    def visit_read(self, node: ReadNode):
        # Read input using scanf
        var_ref = self.get_variable_ref(node.var_name)
        temp = self.new_temp()
        self.add_line(f"{temp} = call i32 (i8*, ...) @scanf(i8* getelementptr inbounds ([3 x i8], [3 x i8]* @.str.input, i32 0, i32 0), i32* {var_ref})")
    
    def visit_write(self, node: WriteNode):
        expr_result = node.expression.accept(self)
        # Print output using printf
        temp = self.new_temp()
        self.add_line(f"{temp} = call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([4 x i8], [4 x i8]* @.str.output, i32 0, i32 0), i32 {expr_result})")
    
    def visit_compound(self, node: CompoundNode):
        for stmt in node.statements:
            if stmt:  # Guard against None statements
                stmt.accept(self)
    
    def visit_if(self, node: IfNode):
        # Generate condition
        cond_result = node.condition.accept(self)
        
        # Convert i32 to i1 if necessary (assuming arithmetic comparisons return i32)
        if not cond_result.startswith('%') or 'icmp' not in self.code[-1]:
            cond_temp = self.new_temp()
            self.add_line(f"{cond_temp} = icmp ne i32 {cond_result}, 0")
            cond_result = cond_temp
        
        then_label = self.new_label()
        end_label = self.new_label()
        
        self.add_line(f"br i1 {cond_result}, label %{then_label}, label %{end_label}")
        
        self.add_label(then_label)
        if node.then_statement:
            node.then_statement.accept(self)
        self.add_line(f"br label %{end_label}")
        
        self.add_label(end_label)
    
    def visit_while(self, node: WhileNode):
        start_label = self.new_label()
        body_label = self.new_label()
        end_label = self.new_label()
        
        self.add_line(f"br label %{start_label}")
        
        self.add_label(start_label)
        cond_result = node.condition.accept(self)
        
        # Convert i32 to i1 if necessary
        if not cond_result.startswith('%') or 'icmp' not in self.code[-1]:
            cond_temp = self.new_temp()
            self.add_line(f"{cond_temp} = icmp ne i32 {cond_result}, 0")
            cond_result = cond_temp
        
        self.add_line(f"br i1 {cond_result}, label %{body_label}, label %{end_label}")
        
        self.add_label(body_label)
        if node.body:
            node.body.accept(self)
        self.add_line(f"br label %{start_label}")
        
        self.add_label(end_label)
    
    def visit_operation(self, node: OperationNode):
        left_result = node.left.accept(self)
        right_result = node.right.accept(self)
        temp = self.new_temp()
        
        # Handle different operator types
        if node.operator in ["+", "-", "*", "/"]:
            # Arithmetic operations
            op_map = {
                "+": "add nsw",  # nsw = no signed wrap
                "-": "sub nsw",
                "*": "mul nsw",
                "/": "sdiv"      # signed division
            }
            llvm_op = op_map[node.operator]
            self.add_line(f"{temp} = {llvm_op} i32 {left_result}, {right_result}")
            
        elif node.operator in ["=", "<>", "<", ">", "<=", ">="]:
            # Comparison operations - return i1
            op_map = {
                "=": "icmp eq",
                "<>": "icmp ne",  # not equal
                "<": "icmp slt",  # signed less than
                ">": "icmp sgt",  # signed greater than
                "<=": "icmp sle", # signed less than or equal
                ">=": "icmp sge"  # signed greater than or equal
            }
            llvm_op = op_map[node.operator]
            self.add_line(f"{temp} = {llvm_op} i32 {left_result}, {right_result}")
            
        else:
            self.messages.error(f"Unsupported operator: {node.operator}", source="LLVMGenerator")
            # Return a safe default
            self.add_line(f"{temp} = add i32 0, 0  ; ERROR: unsupported operator {node.operator}")
        
        return temp
    
    def visit_variable(self, node: VariableNode):
        var_ref = self.get_variable_ref(node.name)
        temp = self.new_temp()
        self.add_line(f"{temp} = load i32, i32* {var_ref}, align 4")
        return temp
    
    def visit_number(self, node: NumberNode):
        return str(node.value)
