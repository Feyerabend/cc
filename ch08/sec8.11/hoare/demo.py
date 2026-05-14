"""
COMPILER INTEGRATION EXAMPLE: Hoare Logic in Action

This demonstrates how Hoare Logic verification integrates into a
realistic compiler pipeline for a simple language.

Pipeline Stages:
1. Lexical Analysis (Tokenization)
2. Parsing (AST Construction)
3. Type Checking
4. Hoare Logic Annotation & VC Generation <-- WE ARE HERE
5. Optimisation (with correctness proofs)
6. Code Generation

This example focuses on stage 4 and shows how it enables safer stage 5.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum


class OptimizationType(Enum):
    """Types of optimisations compiler can perform."""
    CONSTANT_FOLDING = "constant_folding"
    DEAD_CODE_ELIMINATION = "dead_code_elimination"
    LOOP_INVARIANT_CODE_MOTION = "loop_invariant_code_motion" # LICM
    STRENGTH_REDUCTION = "strength_reduction"


@dataclass
class OptimizationOpportunity:
    """Represents a potential optimisation with verification."""
    type: OptimizationType
    location: str
    original_code: str
    optimized_code: str
    verification_condition: str
    safe_to_apply: bool
    proof_sketch: Optional[str] = None


class VerifyingCompiler:
    """
    A compiler that uses Hoare Logic to verify optimisations are correct.
    
    This is a simplified model of how production compilers like GCC, LLVM,
    or Rust's compiler use formal methods to ensure transformations preserve
    program semantics.
    """
    
    def __init__(self):
        self.optimizations_applied = []
        self.optimizations_rejected = []
    
    def analyze_and_optimize(self, ast: Dict) -> Dict:
        """
        Main compilation pipeline with verification.
        
        For each optimisation opportunity:
        1. Generate verification condition
        2. Attempt to prove VC
        3. Only apply optimisation if proven safe
        """

        print("\nVERIFYING COMPILER PIPELINE\n")
        
        # Stage 1: Find optimisation opportunities
        opportunities = self.find_optimization_opportunities(ast)
        
        print(f"\nFound {len(opportunities)} optimisation opportunities")
        print()
        
        # Stage 2: Verify and apply safe optimisations
        for i, opt in enumerate(opportunities, 1):
            print(f"Optimisation #{i}: {opt.type.value}")
            print(f"  Location: {opt.location}")
            print(f"  Original: {opt.original_code}")
            print(f"  Optimised: {opt.optimized_code}")
            print(f"  VC: {opt.verification_condition}")
            
            # Attempt to prove
            proven, proof = self.verify_optimization(opt, ast)
            
            if proven:
                print(f"    PROVEN SAFE - Applying optimisation")
                print(f"  Proof: {proof}")
                self.optimizations_applied.append(opt)
                self.apply_optimization(ast, opt)
            else:
                print(f"    CANNOT PROVE - Skipping optimisation")
                print(f"  Reason: {proof}")
                self.optimizations_rejected.append(opt)
            
            print()
        
        # Stage 3: Generate optimised code
        print("\nOPTIMISATION SUMMARY\n")
        print(f"Applied: {len(self.optimizations_applied)}")
        print(f"Rejected: {len(self.optimizations_rejected)}")
        print()
        
        return ast
    
    def find_optimization_opportunities(self, ast: Dict) -> List[OptimizationOpportunity]:
        """
        Scan AST for optimisation opportunities.
        
        In real compilers, this involves:
        - Data flow analysis
        - Control flow analysis  
        - Alias analysis
        - Value numbering
        """
        opportunities = []
        
        # Example 1: Constant Folding
        # Pattern: x = 2 + 3  →  x = 5
        opportunities.append(OptimizationOpportunity(
            type=OptimizationType.CONSTANT_FOLDING,
            location="line 10",
            original_code="x = 2 + 3",
            optimized_code="x = 5",
            verification_condition="{⊤} x := 5 {x = 5} ≡ {⊤} x := 2 + 3 {x = 5}",
            safe_to_apply=True,
            proof_sketch="Arithmetic evaluation: 2 + 3 = 5"
        ))
        
        # Example 2: Dead Code Elimination
        # Pattern: if (false) { ... }  →  (removed)
        opportunities.append(OptimizationOpportunity(
            type=OptimizationType.DEAD_CODE_ELIMINATION,
            location="line 15-18",
            original_code="if (x > 100) { y = expensive() } // x is always 50",
            optimized_code="// removed",
            verification_condition="{x = 50} ∧ (x > 100) = ⊥ (unreachable)",
            safe_to_apply=True,
            proof_sketch="From context: x = 50. Therefore x > 100 is false."
        ))
        
        # Example 3: Loop Invariant Code Motion
        # Pattern: hoist loop-invariant computation
        opportunities.append(OptimizationOpportunity(
            type=OptimizationType.LOOP_INVARIANT_CODE_MOTION,
            location="line 25-30",
            original_code="""
while (i < n) {
    limit = n * 2;  // invariant: doesn't depend on i
    a[i] = limit;
    i++;
}""",
            optimized_code="""
limit = n * 2;
while (i < n) {
    a[i] = limit;
    i++;
}""",
            verification_condition="""
Invariant I = (limit = n * 2 ∧ ∀j<i: a[j] = n*2)
{I ∧ i < n} a[i] := limit; i++ {I} 
is equivalent before and after optimization
""",
            safe_to_apply=True,
            proof_sketch="limit = n*2 is independent of loop variable i"
        ))
        
        # Example 4: Strength Reduction (potentially unsafe)
        # Pattern: i * 2  →  i << 1  (bitshift)
        opportunities.append(OptimizationOpportunity(
            type=OptimizationType.STRENGTH_REDUCTION,
            location="line 35",
            original_code="y = x * 2",
            optimized_code="y = x << 1",
            verification_condition="""
{x ∈ Int ∧ -2^30 ≤ x ≤ 2^30} y := x << 1 {y = x * 2}
Requires: no overflow
""",
            safe_to_apply=False,  # Need to prove no overflow
            proof_sketch="Cannot prove x is bounded - may overflow on shift"
        ))
        
        return opportunities
    
    def verify_optimization(self, opt: OptimizationOpportunity, ast: Dict) -> tuple[bool, str]:
        """
        Verify an optimisation using Hoare Logic.
        
        Returns: (proven: bool, explanation: str)
        
        In a real compiler, this would invoke:
        - SMT solver (Z3, CVC4)
        - Abstract interpretation
        - Constraint-based analysis
        """
        # Simplified verification - in practice, call SMT solver
        
        if opt.type == OptimizationType.CONSTANT_FOLDING:
            # Always safe: arithmetic is deterministic
            return True, "Constant evaluation is pure"
        
        elif opt.type == OptimizationType.DEAD_CODE_ELIMINATION:
            # Safe if condition is provably false
            if "⊥" in opt.verification_condition:
                return True, "Condition is contradictory"
            return False, "Cannot prove unreachability"
        
        elif opt.type == OptimizationType.LOOP_INVARIANT_CODE_MOTION:
            # Safe if expression is loop-invariant
            if "independent of loop variable" in opt.proof_sketch:
                return True, "Expression invariant over loop iterations"
            return False, "Expression may depend on loop state"
        
        elif opt.type == OptimizationType.STRENGTH_REDUCTION:
            # Requires bounded arithmetic
            if "overflow" in opt.proof_sketch and "Cannot prove" in opt.proof_sketch:
                return False, "Possible overflow - not safe"
            return True, "Arithmetic within bounds"
        
        return False, "Unknown optimization type"
    
    def apply_optimization(self, ast: Dict, opt: OptimizationOpportunity):
        """
        Apply the optimisation to the AST.
        
        In real compilers, this modifies the intermediate representation (IR).
        """
        # In practice: transform AST nodes
        pass


def demonstrate_compiler_pipeline():
    """
    Demonstrate how Hoare Logic enables safe compiler optimisations.
    """
    
    # Simplified AST for demonstration
    example_program = {
        "type": "PROGRAM",
        "statements": [
            {"type": "ASSIGNMENT", "var": "x", "expr": "2 + 3"},
            {"type": "ASSIGNMENT", "var": "y", "expr": "50"},
            {"type": "IF", "condition": "y > 100", "body": "expensive_call()"},
            {"type": "WHILE", "condition": "i < n", "body": [
                {"type": "ASSIGNMENT", "var": "limit", "expr": "n * 2"},
                {"type": "ASSIGNMENT", "var": "a[i]", "expr": "limit"},
                {"type": "ASSIGNMENT", "var": "i", "expr": "i + 1"}
            ]},
            {"type": "ASSIGNMENT", "var": "result", "expr": "x * 2"}
        ]
    }
    
    # Run verifying compiler
    compiler = VerifyingCompiler()
    optimized_ast = compiler.analyze_and_optimize(example_program)
    
    # Show results
    print("\nDETAILED RESULTS\n")
    
    print("\n  SAFE OPTIMISATIONS APPLIED:")
    for opt in compiler.optimizations_applied:
        print(f"  - {opt.type.value} at {opt.location}")
    
    print("\n  UNSAFE OPTIMISATIONS REJECTED:")
    for opt in compiler.optimizations_rejected:
        print(f"  - {opt.type.value} at {opt.location}")
        print(f"    Reason: {opt.proof_sketch}")
    
    print("\nNOTE: Hoare Logic enables aggressive optimisation")
    print("while maintaining correctness guarantees!\n")


# Additional Example: Bounds Check Elimination

class BoundsCheckEliminator:
    """
    Demonstrate how Hoare Logic eliminates redundant array bounds checks.
    
    This is critical for performance in safe languages like Java, C#, Rust.
    """
    
    @staticmethod
    def analyze_array_access(code_snippet: str):
        """
        Show how compiler proves bounds checks are unnecessary.
        """
        print("\nBOUNDS CHECK ELIMINATION EXAMPLE\n")
        
        print("\nOriginal Code:")
        print(code_snippet)
        
        print("\nCompiler Analysis (Hoare Logic):")
        print("-" * 70)
        
        # Example: Simple array iteration
        print("""
Loop invariant: I = (0 ≤ i < n ∧ n = len(arr))

{I ∧ i < n}               // Precondition
x = arr[i];               // Array access
{I ∧ x = arr[i]}          // Postcondition

Verification Condition:
  (0 ≤ i < n) ∧ (i < n) → (0 ≤ i < len(arr))
  
Simplifies to: 0 ≤ i < n → 0 ≤ i < n  ✓ (trivially true)

CONCLUSION: Bounds check is redundant!
Compiler can eliminate runtime check, generating faster code.
        """)
        
        print("Generated Code (optimised):\n")
        print("""
// Bounds check eliminated!
mov rax, [arr + i*8]  ; Direct memory access, no check
        """)
        
        print("\nPerformance Impact:")
        print("  - Eliminated 2 comparisons + 1 branch per iteration")
        print("  - In 1M iteration loop: ~50% faster\n")


if __name__ == "__main__":
    print("""
    HOARE LOGIC IN COMPILERS: A PRACTICAL DEMONSTRATION

    This shows how modern compilers use formal verification to:
       1. Safely optimise code
       2. Eliminate redundant checks
       3. Guarantee correctness of transformations
    """)
    
    # Run main demo
    demonstrate_compiler_pipeline()
    
    # Run bounds check elimination demo
    BoundsCheckEliminator.analyze_array_access("""
for (int i = 0; i < n; i++) {
    x = arr[i];  // Is bounds check needed?
    process(x);
}
    """)
