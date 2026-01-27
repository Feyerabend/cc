#!/usr/bin/env python3

from compiler_core import Plugin, ASTNode, CompilerContext, MessageCollector, Visitor
from compiler_core import BlockNode, NestedBlockNode, AssignNode, CallNode, ReadNode, WriteNode
from compiler_core import CompoundNode, IfNode, WhileNode, OperationNode, VariableNode, NumberNode
from typing import Dict, Any, Set, List, Optional


class CFGGeneratorPlugin(Plugin):
    def __init__(self):
        super().__init__(
            "cfg_generator",
            "Generates a control flow graph for the PL/0 program",
            "1.0"
        )
        self.dependencies = ["static_analysis"]
        self.enabled = True
    
    def run(self, ast: ASTNode, context: CompilerContext, messages: MessageCollector) -> Dict[str, Any]:
        messages.debug("Starting cfg_generator plugin", source="CFGGenerator")
        cfg_builder = CFGBuilder(messages)
        cfg_data = cfg_builder.build(ast)
        cfg_dot = cfg_builder.generate_dot()
        cfg_mermaid = cfg_builder.generate_mermaid()
        
        # Store outputs in context
        context.generated_outputs["cfg_dot"] = cfg_dot
        context.generated_outputs["cfg_mermaid"] = cfg_mermaid
        context.generated_outputs["cfg_report"] = cfg_builder.generate_report()
        context.generated_outputs["cfg_analysis"] = cfg_builder.generate_detailed_analysis()
        
        messages.debug("Completed cfg_generator plugin", source="CFGGenerator")
        return {
            "basic_blocks": cfg_data["block_count"],
            "edges": cfg_data["edge_count"],
            "cyclomatic_complexity": cfg_data["cyclomatic_complexity"],
            "procedures": cfg_data["procedure_count"]
        }


class CFGBlock:
    """Represents a basic block in the CFG"""
    def __init__(self, block_id: str):
        self.id = block_id
        self.statements = []
        self.predecessors = set()
        self.successors = set()
        self.is_entry = False
        self.is_exit = False
        self.procedure_name = None
    
    def add_statement(self, stmt_type: str, details: str = ""):
        self.statements.append({"type": stmt_type, "details": details})
    
    def add_successor(self, block_id: str):
        self.successors.add(block_id)
    
    def add_predecessor(self, block_id: str):
        self.predecessors.add(block_id)


class CFGBuilder(Visitor):
    def __init__(self, messages: MessageCollector):
        self.messages = messages
        self.blocks = {}  # Dict of block_id -> CFGBlock
        self.edges = []   # List of (src, dst) tuples
        self.current_block = None
        self.label_counter = 0
        self.procedure_count = 0
        self.current_procedure = None
        self.entry_blocks = []  # Track entry points
        self.exit_blocks = []   # Track exit points
    
    def build(self, ast: ASTNode) -> Dict[str, Any]:
        # Create initial entry block
        self.current_block = self.create_block("entry")
        self.current_block.is_entry = True
        self.entry_blocks.append(self.current_block.id)
        
        # Build CFG by traversing AST
        ast.accept(self)
        
        # Mark current block as exit if it has no successors
        if self.current_block and not self.current_block.successors:
            self.current_block.is_exit = True
            self.exit_blocks.append(self.current_block.id)
        
        # Calculate cyclomatic complexity: E - N + 2P (P = number of connected components)
        cyclomatic_complexity = len(self.edges) - len(self.blocks) + 2 * max(1, self.procedure_count + 1)
        
        return {
            "block_count": len(self.blocks),
            "edge_count": len(self.edges),
            "cyclomatic_complexity": cyclomatic_complexity,
            "procedure_count": self.procedure_count
        }
    
    def create_block(self, suffix: str = None) -> CFGBlock:
        """Create a new basic block"""
        if suffix:
            block_id = f"{suffix}_{self.label_counter}"
        else:
            block_id = f"BB{self.label_counter}"
        self.label_counter += 1
        
        block = CFGBlock(block_id)
        if self.current_procedure:
            block.procedure_name = self.current_procedure
        
        self.blocks[block_id] = block
        return block
    
    def add_edge(self, src_block: CFGBlock, dst_block: CFGBlock):
        """Add an edge between two blocks"""
        edge = (src_block.id, dst_block.id)
        if edge not in self.edges:
            self.edges.append(edge)
            src_block.add_successor(dst_block.id)
            dst_block.add_predecessor(src_block.id)
    
    def end_current_block(self) -> CFGBlock:
        """End the current block and return it"""
        old_block = self.current_block
        self.current_block = None
        return old_block
    
    def generate_dot(self) -> str:
        """Generate DOT format for Graphviz"""
        lines = ["digraph CFG {"]
        lines.append("    rankdir=TB;")
        lines.append("    node [shape=box, style=filled];")
        
        # Add nodes
        for block in self.blocks.values():
            color = "lightblue"
            if block.is_entry:
                color = "lightgreen"
            elif block.is_exit:
                color = "lightcoral"
            elif block.procedure_name:
                color = "lightyellow"
            
            label_parts = [block.id]
            if block.procedure_name:
                label_parts.append(f"({block.procedure_name})")
            
            # Add statement summary
            if block.statements:
                stmt_summary = "\\n".join([f"{s['type']}: {s['details']}" for s in block.statements[:3]])
                if len(block.statements) > 3:
                    stmt_summary += f"\\n... +{len(block.statements)-3} more"
                label_parts.append(stmt_summary)
            
            label = "\\n".join(label_parts)
            lines.append(f'    {block.id} [label="{label}", fillcolor={color}];')
        
        # Add edges
        for src, dst in self.edges:
            lines.append(f"    {src} -> {dst};")
        
        lines.append("}")
        return "\n".join(lines)
    
    def generate_mermaid(self) -> str:
        """Generate Mermaid flowchart format"""
        lines = ["flowchart TD"]
        
        # Add nodes
        for block in self.blocks.values():
            shape_start, shape_end = "[]", ""
            if block.is_entry:
                shape_start, shape_end = "(", ")"
            elif block.is_exit:
                shape_start, shape_end = "((", "))"
            
            label = block.id
            if block.procedure_name:
                label += f"<br/>{block.procedure_name}"
            if block.statements:
                label += f"<br/>{len(block.statements)} statements"
            
            lines.append(f"    {block.id}{shape_start}\"{label}\"{shape_end}")
        
        # Add edges
        for src, dst in self.edges:
            lines.append(f"    {src} --> {dst}")
        
        return "\n".join(lines)
    
    def generate_report(self) -> str:
        """Generate a summary report"""
        lines = [
            "Control Flow Graph Report",
            "=" * 25,
            f"Basic Blocks: {len(self.blocks)}",
            f"Edges: {len(self.edges)}",
            f"Procedures: {self.procedure_count}",
            f"Entry Points: {len(self.entry_blocks)}",
            f"Exit Points: {len(self.exit_blocks)}",
            f"Cyclomatic Complexity: {len(self.edges) - len(self.blocks) + 2 * max(1, self.procedure_count + 1)}",
            "",
            "Block Statistics:"
        ]
        
        # Add block statistics
        for block in self.blocks.values():
            block_info = f"  • {block.id}: {len(block.statements)} statements"
            if block.procedure_name:
                block_info += f" (in {block.procedure_name})"
            if block.is_entry:
                block_info += " [ENTRY]"
            if block.is_exit:
                block_info += " [EXIT]"
            lines.append(block_info)
        
        return "\n".join(lines)
    
    def generate_detailed_analysis(self) -> str:
        """Generate detailed CFG analysis"""
        lines = [
            "Detailed CFG Analysis",
            "=" * 20,
            "",
            "Block Details:"
        ]
        
        for block in self.blocks.values():
            lines.append(f"Block {block.id}:")
            lines.append(f"  Predecessors: {list(block.predecessors) if block.predecessors else 'None'}")
            lines.append(f"  Successors: {list(block.successors) if block.successors else 'None'}")
            if block.procedure_name:
                lines.append(f"  Procedure: {block.procedure_name}")
            lines.append(f"  Statements ({len(block.statements)}):")
            for stmt in block.statements:
                lines.append(f"    - {stmt['type']}: {stmt['details']}")
            lines.append("")
        
        return "\n".join(lines)
    
    # Visitor methods
    def visit_block(self, node: BlockNode):
        """Handle program blocks with procedures"""
        # Add variable declarations to current block
        if node.variables:
            self.current_block.add_statement("VAR_DECL", f"Variables: {', '.join(node.variables)}")
        
        # Handle procedures - each gets its own CFG subgraph
        for proc_name, proc_body in node.procedures:
            self.procedure_count += 1
            old_procedure = self.current_procedure
            self.current_procedure = proc_name
            
            # Create procedure entry block
            proc_entry = self.create_block(f"proc_{proc_name}_entry")
            proc_entry.is_entry = True
            proc_entry.procedure_name = proc_name
            proc_entry.add_statement("PROC_START", f"Procedure {proc_name}")
            self.entry_blocks.append(proc_entry.id)
            
            # Process procedure body
            old_current = self.current_block
            self.current_block = proc_entry
            proc_body.accept(self)
            
            # Mark procedure exit
            if self.current_block and not self.current_block.successors:
                self.current_block.is_exit = True
                self.current_block.add_statement("PROC_END", f"End of {proc_name}")
                self.exit_blocks.append(self.current_block.id)
            
            # Restore context
            self.current_block = old_current
            self.current_procedure = old_procedure
        
        # Handle main statement
        node.statement.accept(self)
    
    def visit_nested_block(self, node: NestedBlockNode):
        """Handle nested blocks with local variables"""
        if node.variables:
            self.current_block.add_statement("LOCAL_VAR", f"Local vars: {', '.join(node.variables)}")
        
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_assign(self, node: AssignNode):
        """Handle assignment statements"""
        self.current_block.add_statement("ASSIGN", f"{node.var_name} := expression")
        node.expression.accept(self)
    
    def visit_call(self, node: CallNode):
        """Handle procedure calls"""
        self.current_block.add_statement("CALL", f"call {node.proc_name}")
    
    def visit_read(self, node: ReadNode):
        """Handle read statements"""
        self.current_block.add_statement("READ", f"read {node.var_name}")
    
    def visit_write(self, node: WriteNode):
        """Handle write statements"""
        self.current_block.add_statement("WRITE", "write expression")
        node.expression.accept(self)
    
    def visit_compound(self, node: CompoundNode):
        """Handle compound statements"""
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_if(self, node: IfNode):
        """Handle if statements - creates branching in CFG"""
        # Current block ends with the condition
        condition_block = self.current_block
        condition_block.add_statement("IF_COND", "if condition")
        
        # Create then block
        then_block = self.create_block("then")
        self.add_edge(condition_block, then_block)
        
        # Create merge block (where control flow rejoins)
        merge_block = self.create_block("merge")
        self.add_edge(condition_block, merge_block)  # False branch goes directly to merge
        
        # Process then statement
        self.current_block = then_block
        node.then_statement.accept(self)
        
        # Connect then block to merge block
        if self.current_block:  # Then block might have been ended by nested control flow
            self.add_edge(self.current_block, merge_block)
        
        # Continue with merge block
        self.current_block = merge_block
        
        # Process condition expression (for completeness)
        node.condition.accept(self)
    
    def visit_while(self, node: WhileNode):
        """Handle while loops - creates cycles in CFG"""
        # End current block before loop
        pre_loop_block = self.end_current_block()
        
        # Create loop header (condition block)
        loop_header = self.create_block("while_header")
        loop_header.add_statement("WHILE_COND", "while condition")
        if pre_loop_block:
            self.add_edge(pre_loop_block, loop_header)
        
        # Create loop body block
        loop_body = self.create_block("while_body")
        self.add_edge(loop_header, loop_body)
        
        # Create exit block
        loop_exit = self.create_block("while_exit")
        self.add_edge(loop_header, loop_exit)  # Condition false -> exit
        
        # Process loop body
        self.current_block = loop_body
        node.body.accept(self)
        
        # Connect body back to header (creates the loop)
        if self.current_block:
            self.add_edge(self.current_block, loop_header)
        
        # Continue with exit block
        self.current_block = loop_exit
        
        # Process condition expression
        node.condition.accept(self)
    
    def visit_operation(self, node: OperationNode):
        """Handle operations - these don't affect control flow directly"""
        node.left.accept(self)
        node.right.accept(self)
    
    def visit_variable(self, node: VariableNode):
        """Handle variable references - no control flow impact"""
        pass
    
    def visit_number(self, node: NumberNode):
        """Handle number literals - no control flow impact"""
        pass