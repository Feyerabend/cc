#!/usr/bin/env python3

from compiler_core import Plugin, ASTNode, CompilerContext, MessageCollector, Visitor
from compiler_core import BlockNode, NestedBlockNode, AssignNode, CallNode, ReadNode, WriteNode
from compiler_core import CompoundNode, IfNode, WhileNode, OperationNode, VariableNode, NumberNode
from typing import Dict, Any, List, Optional

class PerformanceProfilerPlugin(Plugin):
    """Analyzes performance characteristics and generates profiling reports"""
    
    def __init__(self):
        super().__init__(
            "performance_profiler", 
            "Analyzes execution time complexity and generates instrumented C code", 
            "1.0"
        )
        self.dependencies = ["static_analysis"]
        self.enabled = True  # Explicitly enable plugin
    
    def run(self, ast: ASTNode, context: CompilerContext, messages: MessageCollector) -> Dict[str, Any]:
        messages.debug("Starting performance_profiler plugin", source="PerformanceProfiler")
        profiler = PerformanceProfiler(messages)
        profile_data = profiler.analyze(ast)
        
        # Generate performance report
        report = self._generate_performance_report(profile_data)
        context.generated_outputs["perf_profile"] = report
        
        # Generate instrumented C code for runtime profiling
        instrumenter = CInstrumenter(messages)
        instrumented_c = instrumenter.generate_instrumented_code(ast, profile_data)
        context.generated_outputs["instr_c_code"] = instrumented_c
        
        messages.info(f"Performance analysis complete - estimated complexity: O({profile_data['time_complexity']})")
        
        messages.debug("Completed performance_profiler plugin", source="PerformanceProfiler")
        return profile_data
    
    def _generate_performance_report(self, profile_data: Dict[str, Any]) -> str:
        """Generate detailed performance report"""
        lines = [
            "Performance Analysis Report",
            "=" * 26,
            "",
            "Time Complexity Analysis:",
            f"  • Overall complexity: O({profile_data['time_complexity']})",
            f"  • Space complexity: O({profile_data['space_complexity']})",
            f"  • Estimated operations: {profile_data['operation_count']}",
            "",
            "Performance Hotspots:",
        ]
        
        for hotspot in profile_data['hotspots']:
            lines.append(f"  • {hotspot['type']}: {hotspot['description']} (weight: {hotspot['weight']})")
        
        lines.extend([
            "",
            "Optimization Recommendations:",
        ])
        
        for rec in profile_data['recommendations']:
            lines.append(f"  • {rec}")
        
        lines.extend([
            "",
            "Resource Usage:",
            f"  • Stack depth: {profile_data['max_stack_depth']}",
            f"  • Memory allocations: {profile_data['memory_operations']}",
            f"  • I/O operations: {profile_data['io_operations']}",
            f"  • Procedure calls: {profile_data['procedure_calls']}",
        ])
        
        return "\n".join(lines)

class PerformanceProfiler(Visitor):
    """Analyzes performance characteristics of PL/0 programs"""
    
    def __init__(self, messages: MessageCollector):
        self.messages = messages
        self.time_complexity = "1"  # Best case: constant time
        self.space_complexity = "1"
        self.operation_count = 0
        self.max_stack_depth = 0
        self.current_stack_depth = 0
        self.memory_operations = 0
        self.io_operations = 0
        self.procedure_calls = 0
        self.loop_nesting = 0
        self.max_loop_nesting = 0
        self.loop_complexities = []
        self.hotspots = []
        self.recommendations = []
        self.current_procedure = None
        self.procedure_complexities = {}
        self.in_loop = False
    
    def analyze(self, ast: ASTNode) -> Dict[str, Any]:
        """Perform performance analysis"""
        ast.accept(self)
        self._calculate_final_complexity()
        self._generate_recommendations()
        
        return {
            "time_complexity": self.time_complexity,
            "space_complexity": self.space_complexity,
            "operation_count": self.operation_count,
            "max_stack_depth": self.max_stack_depth,
            "memory_operations": self.memory_operations,
            "io_operations": self.io_operations,
            "procedure_calls": self.procedure_calls,
            "hotspots": self.hotspots,
            "recommendations": self.recommendations,
            "loop_analysis": {
                "max_nesting": self.max_loop_nesting,
                "complexities": self.loop_complexities
            }
        }
    
    def visit_block(self, node: BlockNode):
        self.current_stack_depth += 1
        self.max_stack_depth = max(self.max_stack_depth, self.current_stack_depth)
        self.memory_operations += len(node.variables)
        
        for proc_name, proc_body in node.procedures:
            old_procedure = self.current_procedure
            self.current_procedure = proc_name
            old_ops = self.operation_count
            proc_body.accept(self)
            proc_ops = self.operation_count - old_ops
            self.procedure_complexities[proc_name] = proc_ops
            if proc_ops > 100:
                self.hotspots.append({
                    "type": "Heavy Procedure",
                    "description": f"Procedure '{proc_name}' has {proc_ops} operations",
                    "weight": proc_ops
                })
            self.current_procedure = old_procedure
        
        node.statement.accept(self)
        self.current_stack_depth -= 1
    
    def visit_nested_block(self, node: NestedBlockNode):
        self.current_stack_depth += 1
        self.max_stack_depth = max(self.max_stack_depth, self.current_stack_depth)
        self.memory_operations += len(node.variables)
        for stmt in node.statements:
            stmt.accept(self)
        self.current_stack_depth -= 1
    
    def visit_assign(self, node: AssignNode):
        self.operation_count += 1
        expr_ops = self._count_expression_operations(node.expression)
        self.operation_count += expr_ops
        if self.in_loop and expr_ops > 5:
            self.hotspots.append({
                "type": "Complex Loop Assignment",
                "description": f"Assignment to '{node.var_name}' has {expr_ops} operations in loop",
                "weight": expr_ops * 10
            })
        node.expression.accept(self)
    
    def visit_call(self, node: CallNode):
        self.procedure_calls += 1
        self.operation_count += 10
        self.current_stack_depth += 1
        self.max_stack_depth = max(self.max_stack_depth, self.current_stack_depth)
        if self.in_loop:
            self.hotspots.append({
                "type": "Procedure Call in Loop",
                "description": f"Call to '{node.proc_name}' inside loop",
                "weight": 50
            })
        self.current_stack_depth -= 1
    
    def visit_read(self, node: ReadNode):
        self.io_operations += 1
        self.operation_count += 100
        if self.in_loop:
            self.hotspots.append({
                "type": "I/O in Loop",
                "description": f"Input operation for '{node.var_name}' in loop",
                "weight": 200
            })
    
    def visit_write(self, node: WriteNode):
        self.io_operations += 1
        self.operation_count += 50
        expr_ops = self._count_expression_operations(node.expression)
        self.operation_count += expr_ops
        if self.in_loop:
            self.hotspots.append({
                "type": "I/O in Loop",
                "description": f"Output operation in loop",
                "weight": 100
            })
        node.expression.accept(self)
    
    def visit_compound(self, node: CompoundNode):
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_if(self, node: IfNode):
        self.operation_count += 1
        cond_ops = self._count_expression_operations(node.condition)
        self.operation_count += cond_ops
        node.condition.accept(self)
        old_ops = self.operation_count
        node.then_statement.accept(self)
        branch_ops = self.operation_count - old_ops
        self.operation_count = old_ops + (branch_ops // 2)
    
    def visit_while(self, node: WhileNode):
        self.loop_nesting += 1
        self.max_loop_nesting = max(self.max_loop_nesting, self.loop_nesting)
        old_in_loop = self.in_loop
        self.in_loop = True
        estimated_iterations = self._estimate_loop_iterations(node.condition)
        self.operation_count += 1
        cond_ops = self._count_expression_operations(node.condition)
        old_ops = self.operation_count
        node.condition.accept(self)
        node.body.accept(self)
        body_ops = self.operation_count - old_ops - cond_ops
        total_loop_ops = (cond_ops + body_ops) * estimated_iterations
        self.operation_count = old_ops + total_loop_ops
        self.loop_complexities.append({
            "nesting_level": self.loop_nesting,
            "estimated_iterations": estimated_iterations,
            "body_operations": body_ops,
            "complexity": f"n^{self.loop_nesting}"
        })
        if estimated_iterations > 1000:
            self.hotspots.append({
                "type": "High Iteration Loop",
                "description": f"Loop with ~{estimated_iterations} iterations",
                "weight": estimated_iterations
            })
        self.in_loop = old_in_loop
        self.loop_nesting -= 1
    
    def visit_operation(self, node: OperationNode):
        self.operation_count += 1
        if node.operator == "/":
            self.operation_count += 4
        elif node.operator == "*":
            self.operation_count += 2
        node.left.accept(self)
        node.right.accept(self)
    
    def visit_variable(self, node: VariableNode):
        pass
    
    def visit_number(self, node: NumberNode):
        pass
    
    def _count_expression_operations(self, expr: ASTNode) -> int:
        if isinstance(expr, (NumberNode, VariableNode)):
            return 0
        elif isinstance(expr, OperationNode):
            ops = 1
            if expr.operator == "/":
                ops += 4
            elif expr.operator == "*":
                ops += 2
            return ops + self._count_expression_operations(expr.left) + self._count_expression_operations(expr.right)
        return 0
    
    def _estimate_loop_iterations(self, condition: ASTNode) -> int:
        if isinstance(condition, OperationNode) and isinstance(condition.right, NumberNode):
            return min(condition.right.value, 1000)
        return 10
    
    def _calculate_final_complexity(self):
        if self.max_loop_nesting == 0:
            self.time_complexity = "1"
        elif self.max_loop_nesting == 1:
            self.time_complexity = "n"
        else:
            self.time_complexity = f"n^{self.max_loop_nesting}"
        self.space_complexity = str(max(self.max_stack_depth, 1))
    
    def _generate_recommendations(self):
        if self.io_operations > 0:
            self.recommendations.append("Consider batching I/O operations to reduce system call overhead")
        if self.max_loop_nesting > 2:
            self.recommendations.append("Consider algorithm redesign to reduce nested loop complexity")
        if any(h["type"] == "Procedure Call in Loop" for h in self.hotspots):
            self.recommendations.append("Consider inlining procedures called within loops")
        if self.max_stack_depth > 10:
            self.recommendations.append("High stack usage detected - consider iterative algorithms")
        if self.operation_count > 10000:
            self.recommendations.append("High operation count - consider algorithmic optimizations")

class CInstrumenter(Visitor):
    """Generates instrumented C code for runtime profiling"""
    
    def __init__(self, messages: MessageCollector):
        self.messages = messages
        self.code = []
        self.indent_level = 0
        self.profile_points = 0
    
    def generate_instrumented_code(self, ast: ASTNode, profile_data: Dict[str, Any]) -> str:
        self.code = [
            "#include <stdio.h>",
            "#include <time.h>",
            "#include <sys/time.h>",
            "",
            "// Performance profiling variables",
            "static unsigned long operation_count = 0;",
            "static unsigned long procedure_calls = 0;",
            "static unsigned long io_operations = 0;",
            "static struct timeval start_time, end_time;",
            "",
            "// Profiling macros",
            "#define PROFILE_START() gettimeofday(&start_time, NULL)",
            "#define PROFILE_END() gettimeofday(&end_time, NULL)",
            "#define PROFILE_OP() operation_count++",
            "#define PROFILE_CALL() procedure_calls++",
            "#define PROFILE_IO() io_operations++",
            "",
            "void print_profile_results() {",
            "    double elapsed = (end_time.tv_sec - start_time.tv_sec) + ",
            "                     (end_time.tv_usec - start_time.tv_usec) / 1000000.0;",
            '    printf("\\n--- Performance Profile ---\\n");',
            '    printf("Execution time: %.6f seconds\\n", elapsed);',
            '    printf("Operations: %lu\\n", operation_count);',
            '    printf("Procedure calls: %lu\\n", procedure_calls);',
            '    printf("I/O operations: %lu\\n", io_operations);',
            '    printf("Ops/second: %.0f\\n", operation_count / elapsed);',
            "}",
            ""
        ]
        ast.accept(self)
        return "\n".join(self.code)
    
    def add_line(self, line: str):
        self.code.append("    " * self.indent_level + line)
        if line.strip() and "PROFILE_" in line:
            self.profile_points += 1
    
    def visit_block(self, node: BlockNode):
        for var in node.variables:
            self.add_line(f"int {var};")
        for proc_name, proc_body in node.procedures:
            self.add_line(f"void {proc_name}() {{")
            self.indent_level += 1
            self.add_line("PROFILE_CALL();")
            proc_body.accept(self)
            self.indent_level -= 1
            self.add_line("}")
        self.add_line("int main() {")
        self.indent_level += 1
        self.add_line("PROFILE_START();")
        node.statement.accept(self)
        self.add_line("PROFILE_END();")
        self.add_line("print_profile_results();")
        self.add_line("return 0;")
        self.indent_level -= 1
        self.add_line("}")
    
    def visit_nested_block(self, node: NestedBlockNode):
        for var in node.variables:
            self.add_line(f"int {var};")
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_assign(self, node: AssignNode):
        self.add_line("PROFILE_OP();")
        expr_code = node.expression.accept(self)
        self.add_line(f"{node.var_name} = {expr_code};")
    
    def visit_call(self, node: CallNode):
        self.add_line("PROFILE_CALL();")
        self.add_line(f"{node.proc_name}();")
    
    def visit_read(self, node: ReadNode):
        self.add_line("PROFILE_IO();")
        self.add_line(f"scanf(\"%d\", &{node.var_name});")
    
    def visit_write(self, node: WriteNode):
        self.add_line("PROFILE_IO();")
        expr_code = node.expression.accept(self)
        self.add_line(f"printf(\"%d\\n\", {expr_code});")
    
    def visit_compound(self, node: CompoundNode):
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_if(self, node: IfNode):
        self.add_line("PROFILE_OP();")
        cond_code = node.condition.accept(self)
        self.add_line(f"if ({cond_code}) {{")
        self.indent_level += 1
        node.then_statement.accept(self)
        self.indent_level -= 1
        self.add_line("}")
    
    def visit_while(self, node: WhileNode):
        self.add_line("PROFILE_OP();")
        cond_code = node.condition.accept(self)
        self.add_line(f"while ({cond_code}) {{")
        self.indent_level += 1
        node.body.accept(self)
        self.indent_level -= 1
        self.add_line("}")
    
    def visit_operation(self, node: OperationNode):
        left_code = node.left.accept(self)
        right_code = node.right.accept(self)
        return f"({left_code} {node.operator} {right_code})"
    
    def visit_variable(self, node: VariableNode):
        return node.name
    
    def visit_number(self, node: NumberNode):
        return str(node.value)