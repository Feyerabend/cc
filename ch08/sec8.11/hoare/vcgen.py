"""
Enhanced Hoare Logic AST Annotator

This implements formal verification annotations using Hoare Logic:
- Preconditions {P}: What must be true BEFORE a statement
- Postconditions {Q}: What must be true AFTER a statement  
- Invariants {I}: What remains true during loop iterations
This adds LOGICAL ASSERTIONS for program correctness verification.

This does NOT perform actual theorem proving, but sets up the
necessary annotations and verification conditions (VCs) for later proof.
Theorem proving can be integrated with tools like Z3 or Coq.
"""

from typing import Dict, Set, List, Any
from dataclasses import dataclass, field
from copy import deepcopy
import pprint


@dataclass
class VerificationContext:
    """Tracks program state for verification."""
    variables: Set[str] = field(default_factory=set)
    constants: Set[str] = field(default_factory=set)
    procedures: Dict[str, Dict] = field(default_factory=dict)
    assigned_vars: Set[str] = field(default_factory=set)
    type_info: Dict[str, str] = field(default_factory=dict)
    
    def copy(self):
        """Create a deep copy for branching contexts."""
        return VerificationContext(
            variables=self.variables.copy(),
            constants=self.constants.copy(),
            procedures=deepcopy(self.procedures),
            assigned_vars=self.assigned_vars.copy(),
            type_info=self.type_info.copy()
        )


class HoareLogicAnnotator:
    """
    Annotates AST with Hoare Logic assertions for formal verification.
    
    Hoare Triple: {P} S {Q}
    - P: Precondition (what must be true before S)
    - S: Statement/Program
    - Q: Postcondition (what is guaranteed after S)
    """
    
    def __init__(self):
        self.verification_conditions = []
    
    def annotate(self, node: Dict, context: VerificationContext = None) -> Dict:
        """Main annotation dispatcher."""
        if context is None:
            context = VerificationContext()
        
        node_type = node.get("type")
        handler = getattr(self, f"annotate_{node_type.lower()}", self.annotate_default)
        return handler(node, context)
    
    def annotate_program(self, node: Dict, context: VerificationContext) -> Dict:
        """Annotate entire program."""
        node["precondition"] = "⊤ (True - no initial constraints)"
        node["postcondition"] = "Program terminates correctly"
        
        # Process main block
        if node["children"]:
            self.annotate(node["children"][0], context)
        
        node["verification_conditions"] = self.verification_conditions
        return node
    
    def annotate_block(self, node: Dict, context: VerificationContext) -> Dict:
        """Annotate code block - compose postconditions."""
        # For blocks, the precondition of the first statement becomes block's precondition
        # The postcondition of the last statement becomes block's postcondition
        
        preconditions = []
        postconditions = []
        
        for child in node["children"]:
            self.annotate(child, context)
            if "precondition" in child:
                preconditions.append(child["precondition"])
            if "postcondition" in child:
                postconditions.append(child["postcondition"])
        
        node["precondition"] = preconditions[0] if preconditions else "⊤"
        node["postcondition"] = " ∧ ".join(postconditions) if postconditions else "⊤"
        
        return node
    
    def annotate_var_decl(self, node: Dict, context: VerificationContext) -> Dict:
        """Annotate variable declaration."""
        var_name = node["value"]
        context.variables.add(var_name)
        
        # Hoare logic for declaration
        node["precondition"] = "⊤"
        node["postcondition"] = f"∃{var_name} ∈ Variables ∧ {var_name} is uninitialized"
        node["weakest_precondition"] = "⊤"
        
        return node
    
    def annotate_const_decl(self, node: Dict, context: VerificationContext) -> Dict:
        """Annotate constant declaration."""
        const_name = node["value"]
        context.constants.add(const_name)
        
        node["precondition"] = "⊤"
        node["postcondition"] = f"{const_name} ∈ Constants ∧ {const_name} is immutable"
        
        return node
    
    def annotate_assignment(self, node: Dict, context: VerificationContext) -> Dict:
        """
        Annotate assignment using substitution axiom.
        
        Assignment Axiom: {P[E/x]} x := E {P}
        where P[E/x] means substitute E for x in P
        """
        var_name = node["value"]
        expr = node["children"][0] if node["children"] else {"type": "NUMBER", "value": 0}
        
        # Precondition: expression is well-formed and evaluable
        expr_str = self.format_expression(expr)
        
        if var_name not in context.variables:
            raise AssertionError(f"Variable '{var_name}' not declared (used before declaration)")
        
        # Precondition: All variables in expression must be defined
        expr_vars = self.extract_variables(expr)
        undefined_vars = expr_vars - context.assigned_vars - context.constants
        
        if undefined_vars:
            precond = f"⊥ (False - uninitialized vars: {undefined_vars})"
        else:
            precond = f"({expr_str}) is well-defined"
        
        # Postcondition: variable has the value of expression
        postcond = f"{var_name} = {expr_str}"
        
        # Weakest precondition (for backward reasoning)
        wp = f"WP({var_name} := {expr_str}, {postcond}) = {postcond}"
        
        node["precondition"] = precond
        node["postcondition"] = postcond
        node["weakest_precondition"] = wp
        
        context.assigned_vars.add(var_name)
        
        return node
    
    def annotate_while(self, node: Dict, context: VerificationContext) -> Dict:
        """
        Annotate while loop with invariant.
        
        While Rule: {I ∧ B} S {I}
                   ──────────────────
               {I} while B do S {I ∧ ¬B}
        
        where I is the loop invariant
        """
        condition = node["children"][0]
        body = node["children"][1]
        
        cond_str = self.format_condition(condition)
        
        # Infer loop invariant (simplified - real systems use abstract interpretation)
        invariant = self.infer_loop_invariant(condition, body, context)
        
        # Loop verification conditions
        # 1. Invariant holds on entry
        # 2. Invariant + condition implies invariant after body
        # 3. Invariant + ¬condition implies postcondition
        
        node["precondition"] = invariant
        node["invariant"] = invariant
        node["loop_condition"] = cond_str
        node["postcondition"] = f"({invariant}) ∧ ¬({cond_str})"
        
        # Generate verification condition
        vc = f"{{({invariant}) ∧ ({cond_str})}} body {{({invariant})}}"
        self.verification_conditions.append(vc)
        
        # Annotate loop body with invariant context
        loop_context = context.copy()
        self.annotate(body, loop_context)
        
        return node
    
    def annotate_if(self, node: Dict, context: VerificationContext) -> Dict:
        """
        Annotate if statement.
        
        If Rule: {P ∧ B} S1 {Q}    {P ∧ ¬B} S2 {Q}
                ─────────────────────────────────────
                   {P} if B then S1 else S2 {Q}
        """
        condition = node["children"][0]
        then_branch = node["children"][1]
        else_branch = node["children"][2] if len(node["children"]) > 2 else None
        
        cond_str = self.format_condition(condition)
        
        # Precondition: condition is well-defined
        node["precondition"] = f"({cond_str}) is well-defined"
        
        # Annotate branches with refined contexts
        then_context = context.copy()
        self.annotate(then_branch, then_context)
        
        if else_branch:
            else_context = context.copy()
            self.annotate(else_branch, else_context)
            
            # Postcondition is disjunction of branch postconditions
            then_post = then_branch.get("postcondition", "⊤")
            else_post = else_branch.get("postcondition", "⊤")
            node["postcondition"] = f"(({cond_str}) → ({then_post})) ∧ (¬({cond_str}) → ({else_post}))"
        else:
            then_post = then_branch.get("postcondition", "⊤")
            node["postcondition"] = f"({cond_str}) → ({then_post})"
        
        return node
    
    def annotate_proc_decl(self, node: Dict, context: VerificationContext) -> Dict:
        """Annotate procedure declaration with contract."""
        proc_name = node["value"]
        body = node["children"][0] if node["children"] else None
        
        # Procedure contract (requires/ensures)
        node["precondition"] = f"requires_{proc_name}()"
        node["postcondition"] = f"ensures_{proc_name}()"
        
        # Store procedure in context
        context.procedures[proc_name] = {
            "precondition": node["precondition"],
            "postcondition": node["postcondition"]
        }
        
        if body:
            proc_context = context.copy()
            self.annotate(body, proc_context)
            
            # Verify procedure satisfies its contract
            body_post = body.get("postcondition", "⊤")
            vc = f"{{requires_{proc_name}()}} body {{ensures_{proc_name}()}}"
            self.verification_conditions.append(vc)
        
        return node
    
    def annotate_call(self, node: Dict, context: VerificationContext) -> Dict:
        """Annotate procedure call."""
        proc_name = node["value"]
        
        if proc_name not in context.procedures:
            raise AssertionError(f"Procedure '{proc_name}' not declared")
        
        proc_contract = context.procedures[proc_name]
        
        # Use procedure's contract
        node["precondition"] = proc_contract["precondition"]
        node["postcondition"] = proc_contract["postcondition"]
        
        return node
    
    def annotate_default(self, node: Dict, context: VerificationContext) -> Dict:
        """Default handler for unknown node types."""
        return node
    
    # Helper methods
    
    def format_expression(self, expr: Dict) -> str:
        """Format expression into string."""
        expr_type = expr.get("type")
        
        if expr_type == "IDENTIFIER":
            return expr["value"]
        elif expr_type == "NUMBER":
            return str(expr["value"])
        elif expr_type == "OPERATOR":
            left = self.format_expression(expr["children"][0])
            right = self.format_expression(expr["children"][1])
            return f"({left} {expr['value']} {right})"
        return "?"
    
    def format_condition(self, cond: Dict) -> str:
        """Format condition into string."""
        left = self.format_expression(cond["children"][0])
        right = self.format_expression(cond["children"][1])
        op = cond["value"]
        return f"{left} {op} {right}"
    
    def extract_variables(self, expr: Dict) -> Set[str]:
        """Extract all variable names from expression."""
        vars_found = set()
        
        if expr.get("type") == "IDENTIFIER":
            vars_found.add(expr["value"])
        elif "children" in expr:
            for child in expr["children"]:
                vars_found.update(self.extract_variables(child))
        
        return vars_found
    
    def infer_loop_invariant(self, condition: Dict, body: Dict, context: VerificationContext) -> str:
        """
        Infer loop invariant (simplified heuristic).
        Real systems use abstract interpretation or user annotations.
        """
        cond_str = self.format_condition(condition)
        
        # Simple heuristic: invariant relates to loop variables and bounds
        left_var = condition["children"][0].get("value") if condition["children"][0].get("type") == "IDENTIFIER" else None
        
        if left_var:
            return f"{left_var} ≥ 0"  # Simple invariant for countdown loops
        
        return f"Invariant({cond_str})"






def create_example_ast():
    """Create example AST for verification."""
    return {
        "type": "PROGRAM",
        "value": "example",
        "children": [{
            "type": "BLOCK",
            "value": "main",
            "children": [
                {"type": "VAR_DECL", "value": "x"},
                {"type": "VAR_DECL", "value": "y"},
                {
                    "type": "ASSIGNMENT",
                    "value": "x",
                    "children": [{"type": "NUMBER", "value": 10}]
                },
                {
                    "type": "ASSIGNMENT",
                    "value": "y",
                    "children": [{"type": "NUMBER", "value": 0}]
                },
                {
                    "type": "WHILE",
                    "value": "loop",
                    "children": [
                        {
                            "type": "CONDITION",
                            "value": ">",
                            "children": [
                                {"type": "IDENTIFIER", "value": "x"},
                                {"type": "NUMBER", "value": 0}
                            ]
                        },
                        {
                            "type": "BLOCK",
                            "value": "body",
                            "children": [
                                {
                                    "type": "ASSIGNMENT",
                                    "value": "x",
                                    "children": [{
                                        "type": "OPERATOR",
                                        "value": "-",
                                        "children": [
                                            {"type": "IDENTIFIER", "value": "x"},
                                            {"type": "NUMBER", "value": 1}
                                        ]
                                    }]
                                },
                                {
                                    "type": "ASSIGNMENT",
                                    "value": "y",
                                    "children": [{
                                        "type": "OPERATOR",
                                        "value": "+",
                                        "children": [
                                            {"type": "IDENTIFIER", "value": "y"},
                                            {"type": "NUMBER", "value": 1}
                                        ]
                                    }]
                                }
                            ]
                        }
                    ]
                }
            ]
        }]
    }


print("\nHOARE LOGIC ANNOTATOR - Formal Verification of Programs")
print("-" * 60)

# Create and annotate AST
annotator = HoareLogicAnnotator()
example_ast = create_example_ast()
annotated = annotator.annotate(example_ast)

print("\n ANNOTATED AST WITH VERIFICATION CONDITIONS:\n")
pprint.pprint(annotated, width=100, compact=False)

print("\nVERIFICATION CONDITIONS TO (ULTIMATELY) PROVE:")
print("-" * 60)
for i, vc in enumerate(annotator.verification_conditions, 1):
    print(f"{i}. {vc}")


