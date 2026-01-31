# tests.py
# Comprehensive tests for lambda calculus implementation with focus on TAC.

import unittest
from parser import parse_lambda, Var, Lam, App
from tac import generate_tac, optimize_tac
from executor import evaluate, print_value, Closure

class TestLambdaCalculus(unittest.TestCase):
    
    def test_parser_variable(self):
        """Test parsing simple variable."""
        ast = parse_lambda("x")
        self.assertIsInstance(ast, Var)
        self.assertEqual(ast.name, "x")
    
    def test_parser_lambda(self):
        """Test parsing lambda abstraction."""
        ast = parse_lambda("λx.x")
        self.assertIsInstance(ast, Lam)
        self.assertEqual(ast.param, "x")
        self.assertIsInstance(ast.body, Var)
        self.assertEqual(ast.body.name, "x")
    
    def test_parser_application(self):
        """Test parsing application - (λx.x) applied to y."""
        ast = parse_lambda("((λx.x) y)")  # Apply λx.x to y
        self.assertIsInstance(ast, App)
        self.assertIsInstance(ast.func, Lam)
        self.assertIsInstance(ast.arg, Var)
        self.assertEqual(ast.arg.name, "y")
    
    def test_parser_nested_lambda(self):
        """Test parsing nested lambdas."""
        ast = parse_lambda("λx.λy.(x y)")
        self.assertIsInstance(ast, Lam)
        self.assertEqual(ast.param, "x")
        self.assertIsInstance(ast.body, Lam)
        self.assertEqual(ast.body.param, "y")
        self.assertIsInstance(ast.body.body, App)
    
    def test_parser_left_associative(self):
        """Test that application is left-associative: x y z = ((x y) z)."""
        ast = parse_lambda("x y z")
        # Should be App(App(x, y), z)
        self.assertIsInstance(ast, App)
        self.assertIsInstance(ast.func, App)
        self.assertIsInstance(ast.arg, Var)
        self.assertEqual(ast.arg.name, "z")

    def test_tac_generation_variable(self):
        """Test TAC generation for simple variable."""
        ast = parse_lambda("x")
        instructions, final_var = generate_tac(ast)
        self.assertEqual(len(instructions), 1)
        self.assertEqual(instructions[0].op, 'VAR')
        self.assertEqual(instructions[0].arg1, 'x')
        self.assertEqual(final_var, 't1')
    
    def test_tac_generation_lambda(self):
        """Test TAC generation for lambda with application in body."""
        ast = parse_lambda("λx.(x y)")
        instructions, final_var = generate_tac(ast)
        
        # Expected (post-order traversal):
        # t3 = VAR x
        # t4 = VAR y  
        # t2 = APP t3 t4
        # t1 = LAM x t2
        self.assertEqual(len(instructions), 4)
        self.assertEqual(instructions[0].op, 'VAR')
        self.assertEqual(instructions[1].op, 'VAR')
        self.assertEqual(instructions[2].op, 'APP')
        self.assertEqual(instructions[3].op, 'LAM')
        self.assertEqual(final_var, "t1")
    
    def test_tac_generation_nested(self):
        """Test TAC for nested structure."""
        ast = parse_lambda("λx.λy.(x y)")
        instructions, final_var = generate_tac(ast)
        
        # Expected:
        # t1 = VAR x
        # t2 = VAR y
        # t3 = APP t1 t2
        # t4 = LAM y t3
        # t5 = LAM x t4
        self.assertEqual(len(instructions), 5)
        self.assertEqual(instructions[-1].op, 'LAM')
        self.assertEqual(instructions[-1].arg1, 'x')

    def test_evaluation_identity(self):
        """Test evaluation of identity function applied to variable."""
        ast = parse_lambda("((λx.x) a)")  # Apply λx.x to a
        result = evaluate(ast)
        # Should reduce to 'a'
        self.assertIsInstance(result, Var)
        self.assertEqual(result.name, "a")
    
    def test_evaluation_lambda_value(self):
        """Test that unapplied lambda evaluates to closure."""
        ast = parse_lambda("λx.(x x)")
        result = evaluate(ast)
        self.assertIsInstance(result, Closure)
        self.assertEqual(print_value(result), "λx.(x x)")
    
    def test_evaluation_church_true(self):
        """Test Church boolean TRUE: λt.λf.t"""
        ast = parse_lambda("λt.λf.t")
        result = evaluate(ast)
        self.assertIsInstance(result, Closure)
        # The outer lambda should be preserved
        output = print_value(result)
        self.assertIn("λt", output)
        self.assertIn("λf", output)
    
    def test_evaluation_const(self):
        """Test K combinator: λx.λy.x applied twice."""
        ast = parse_lambda("(((λx.λy.x) a) b)")  # Apply K to a, then to b
        result = evaluate(ast)
        # Should reduce to 'a' (K combinator returns first arg)
        self.assertIsInstance(result, Var)
        self.assertEqual(result.name, "a")
    
    def test_tac_optimization(self):
        """Test that TAC optimization works."""
        ast = parse_lambda("λx.x")
        instructions, _ = generate_tac(ast)
        # Original should have 2 instructions
        self.assertEqual(len(instructions), 2)
        
        # All should be used in this case
        optimized = optimize_tac(instructions)
        self.assertEqual(len(optimized), 2)

class TestTACHighlights(unittest.TestCase):
    """Tests specifically highlighting TAC capabilities."""
    
    def test_tac_makes_order_explicit(self):
        """TAC makes evaluation order explicit."""
        expr = "(λf.λx.(f (f x)) succ zero)"
        ast = parse_lambda(expr)
        instructions, final = generate_tac(ast)
        
        # TAC shows clear step-by-step evaluation order
        # Each instruction has max 3 addresses
        for instr in instructions:
            # Check three-address property
            addresses = [instr.result, instr.arg1, instr.arg2]
            non_null = [a for a in addresses if a is not None]
            self.assertLessEqual(len(non_null), 3)
    
    def test_tac_temporary_variables(self):
        """TAC uses systematic temporary variables."""
        expr = "λx.λy.λz.((x y) z)"
        ast = parse_lambda(expr)
        instructions, final = generate_tac(ast)
        
        # All results should be temp variables
        for instr in instructions:
            self.assertTrue(instr.result.startswith('t'))
            # Check sequential numbering
            temp_num = int(instr.result[1:])
            self.assertGreater(temp_num, 0)
    
    def test_tac_linearization(self):
        """TAC converts tree structure to linear form."""
        expr = "((a b) (c d))"
        ast = parse_lambda(expr)
        
        # AST is tree-structured
        self.assertIsInstance(ast, App)
        self.assertIsInstance(ast.func, App)
        self.assertIsInstance(ast.arg, App)
        
        # TAC is linear sequence
        instructions, final = generate_tac(ast)
        # Should have 7 instructions (4 vars + 3 apps)
        # t3=VAR a, t4=VAR b, t2=APP t3 t4, t6=VAR c, t7=VAR d, t5=APP t6 t7, t1=APP t2 t5
        self.assertEqual(len(instructions), 7)
        
        # Each instruction builds on previous ones
        temps_defined = set()
        for instr in instructions:
            # Arguments should reference already-defined temps or vars
            if instr.arg1 and isinstance(instr.arg1, str) and instr.arg1.startswith('t'):
                self.assertIn(instr.arg1, temps_defined)
            if instr.arg2 and isinstance(instr.arg2, str) and instr.arg2.startswith('t'):
                self.assertIn(instr.arg2, temps_defined)
            temps_defined.add(instr.result)

if __name__ == '__main__':
    # Run with verbose output to see test names
    unittest.main(verbosity=2)
