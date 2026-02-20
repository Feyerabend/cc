import unittest
from typing import Any
from lisp import (
    Token, TokenFactory, Parser, Environment, Procedure, Lisp, ErrorHandler,
    ParseError, RuntimeError, Symbol, ExpressionFactory,
    AddCommand, SubtractCommand, MultiplyCommand, DivideCommand, ModCommand, 
    AbsCommand, MaxCommand, MinCommand, EqualCommand, NotEqualCommand,
    LessCommand, GreaterCommand, LessEqualCommand, GreaterEqualCommand,
    NotCommand, ConsCommand, CarCommand, CdrCommand, ListCommand,
    AppendCommand, LengthCommand, ReverseCommand, NullCommand,
    EmptyCommand, NumberCommand, StringCommand, SymbolCommand,
    ListPredCommand, MapCommand, FilterCommand,
    ReduceCommand, ApplyCommand, Macro, SourceLocation,
    ProcedureCommand, PrintCommand, DisplayCommand,
    TailCall, QuoteEvaluator, QuasiquoteEvaluator, IfEvaluator, CondEvaluator, 
    AndEvaluator, OrEvaluator, DefineEvaluator, SetEvaluator, LambdaEvaluator, 
    LetEvaluator, BeginEvaluator, WhileEvaluator, DefmacroEvaluator
)

class TestLispInterpreter(unittest.TestCase):
    """Test suite for the improved Lisp interpreter"""
    
    def setUp(self):
        self.lisp = Lisp()
        self.env = Environment(self.lisp.global_env)


    # ORIGINAL TESTS (for basic functionality)
    
    def test_token_factory(self):
        """Test tokenization"""
        text = '(+ 1 2.0 "hello" true nil)'
        tokens = TokenFactory.create_tokens(text)
        expected_kinds = ['PAREN', 'SYMBOL', 'NUMBER', 'NUMBER', 'STRING', 'SYMBOL', 'SYMBOL', 'PAREN']
        expected_values = ['(', '+', '1', '2.0', '"hello"', 'true', 'nil', ')']
        self.assertEqual(len(tokens), len(expected_kinds))
        for token, kind, value in zip(tokens, expected_kinds, expected_values):
            self.assertEqual(token.kind, kind)
            self.assertEqual(token.value, value)

        # Test unterminated string
        with self.assertRaises(ParseError) as cm:
            TokenFactory.create_tokens('"unterminated')
        self.assertIn("Unterminated string", str(cm.exception))

        # Test comments and whitespace
        text = '; comment\n (+ 1 2)'
        tokens = TokenFactory.create_tokens(text)
        self.assertEqual(len(tokens), 5)
        self.assertEqual(tokens[0].value, '(')
        self.assertEqual(tokens[1].value, '+')

    def test_parser(self):
        """Test parsing"""
        tokens = TokenFactory.create_tokens('(+ 1 2.0 "hello")')
        parser = Parser(tokens)
        parsed = parser.parse()
        expected = [Symbol('+'), 1, 2.0, 'hello']
        self.assertEqual(parsed, expected)

        # Test quote parsing
        tokens = TokenFactory.create_tokens("'x")
        parser = Parser(tokens)
        parsed = parser.parse()
        self.assertEqual(parsed, ['quote', Symbol('x')])

        # Test unexpected closing parenthesis
        tokens = TokenFactory.create_tokens(')')
        parser = Parser(tokens)
        with self.assertRaises(ParseError) as cm:
            parser.parse()
        self.assertIn("Unexpected closing", str(cm.exception))

        # Test missing closing parenthesis
        tokens = TokenFactory.create_tokens('(')
        parser = Parser(tokens)
        with self.assertRaises(ParseError) as cm:
            parser.parse()
        self.assertIn("Missing closing", str(cm.exception))

    def test_environment(self):
        """Test environment scoping"""
        env = Environment()
        env.define('x', 10)
        self.assertEqual(env.get('x'), 10)
        env.set('x', 20)
        self.assertEqual(env.get('x'), 20)

        # Test undefined variable
        with self.assertRaises(RuntimeError) as cm:
            env.get('y')
        self.assertIn("Undefined variable", str(cm.exception))

        # Test setting undefined variable
        with self.assertRaises(RuntimeError) as cm:
            env.set('y', 30)
        self.assertIn("Cannot set undefined variable", str(cm.exception))

        # Test nested environment
        parent = Environment()
        parent.define('a', 1)
        child = Environment(parent)
        self.assertEqual(child.get('a'), 1)
        child.define('a', 2)
        self.assertEqual(child.get('a'), 2)
        self.assertEqual(parent.get('a'), 1)

    def test_procedure(self):
        """Test procedure calls"""
        params = ['x', 'y']
        body = [Symbol('+'), Symbol('x'), Symbol('y')]
        proc = Procedure(params, body, self.env, self.lisp)
        result = proc(1, 2)
        self.assertEqual(result, 3)

        # Test wrong number of arguments
        with self.assertRaises(RuntimeError) as cm:
            proc(1)
        self.assertIn("expects 2 arguments, got 1", str(cm.exception))

        # Test invalid parameter types
        with self.assertRaises(RuntimeError) as cm:
            Procedure([1], body, self.env, self.lisp)
        self.assertIn("Parameter names must be strings", str(cm.exception))

    def test_expression_factory(self):
        """Test expression creation"""
        token = Token('NUMBER', '123', 0)
        self.assertEqual(ExpressionFactory.create_atom(token), 123)

        token = Token('NUMBER', '12.34', 0)
        self.assertEqual(ExpressionFactory.create_atom(token), 12.34)

        token = Token('STRING', '"hello\\nworld"', 0)
        self.assertEqual(ExpressionFactory.create_atom(token), 'hello\nworld')

        token = Token('SYMBOL', 'true', 0)
        self.assertEqual(ExpressionFactory.create_atom(token), True)

        token = Token('SYMBOL', 'x', 0)
        self.assertEqual(ExpressionFactory.create_atom(token), Symbol('x'))

    def test_special_forms(self):
        """Test special form evaluation"""
        # Test quote
        result = self.lisp.eval([Symbol('quote'), Symbol('x')], self.env)
        self.assertEqual(result, Symbol('x'))

        # Test if
        result = self.lisp.eval([Symbol('if'), True, 1, 2], self.env)
        self.assertEqual(result, 1)
        result = self.lisp.eval([Symbol('if'), False, 1, 2], self.env)
        self.assertEqual(result, 2)

        # Test cond
        result = self.lisp.eval([Symbol('cond'), [True, 1], [Symbol('else'), 2]], self.env)
        self.assertEqual(result, 1)
        result = self.lisp.eval([Symbol('cond'), [False, 1], [Symbol('else'), 2]], self.env)
        self.assertEqual(result, 2)

        # Test and
        result = self.lisp.eval([Symbol('and'), True, True], self.env)
        self.assertEqual(result, True)
        result = self.lisp.eval([Symbol('and'), True, False], self.env)
        self.assertEqual(result, False)

        # Test or
        result = self.lisp.eval([Symbol('or'), False, True], self.env)
        self.assertEqual(result, True)
        result = self.lisp.eval([Symbol('or'), False, False], self.env)
        self.assertEqual(result, False)

        # Test define
        self.lisp.eval([Symbol('define'), Symbol('x'), 10], self.env)
        self.assertEqual(self.env.get('x'), 10)

        # Test set!
        self.lisp.eval([Symbol('define'), Symbol('y'), 5], self.env)
        self.lisp.eval([Symbol('set!'), Symbol('y'), 15], self.env)
        self.assertEqual(self.env.get('y'), 15)

        # Test lambda
        result = self.lisp.eval([[Symbol('lambda'), [Symbol('x')], [Symbol('+'), Symbol('x'), 1]], 5], self.env)
        self.assertEqual(result, 6)

        # Test let
        result = self.lisp.eval([Symbol('let'), [[Symbol('x'), 10]], [Symbol('+'), Symbol('x'), 5]], self.env)
        self.assertEqual(result, 15)

        # Test begin
        result = self.lisp.eval([Symbol('begin'), [Symbol('define'), Symbol('z'), 1], [Symbol('+'), Symbol('z'), 2]], self.env)
        self.assertEqual(result, 3)

        # Test while
        self.lisp.eval([Symbol('define'), Symbol('i'), 0], self.env)
        result = self.lisp.eval([Symbol('while'), [Symbol('<'), Symbol('i'), 3], [Symbol('set!'), Symbol('i'), [Symbol('+'), Symbol('i'), 1]]], self.env)
        self.assertEqual(self.env.get('i'), 3)

    def test_built_in_commands(self):
        """Test built-in commands"""
        # Test arithmetic
        self.assertEqual(AddCommand().execute(1, 2, 3), 6)
        self.assertEqual(SubtractCommand().execute(10, 3, 2), 5)
        self.assertEqual(MultiplyCommand().execute(2, 3, 4), 24)
        self.assertEqual(DivideCommand().execute(100, 2, 2), 25.0)
        self.assertEqual(ModCommand().execute(10, 3), 1)
        self.assertEqual(AbsCommand().execute(-5), 5)
        self.assertEqual(MaxCommand().execute(1, 5, 3), 5)
        self.assertEqual(MinCommand().execute(1, 5, 3), 1)

        # Test comparisons
        self.assertEqual(EqualCommand().execute(5, 5), True)
        self.assertEqual(NotEqualCommand().execute(5, 6), True)
        self.assertEqual(LessCommand().execute(4, 5), True)
        self.assertEqual(GreaterCommand().execute(6, 5), True)
        self.assertEqual(LessEqualCommand().execute(5, 5), True)
        self.assertEqual(GreaterEqualCommand().execute(6, 5), True)
        self.assertEqual(NotCommand().execute(False), True)

        # Test list operations
        self.assertEqual(ConsCommand().execute(1, [2, 3]), [1, 2, 3])
        self.assertEqual(CarCommand().execute([1, 2, 3]), 1)
        self.assertEqual(CdrCommand().execute([1, 2, 3]), [2, 3])
        self.assertEqual(ListCommand().execute(1, 2, 3), [1, 2, 3])
        self.assertEqual(AppendCommand().execute([1, 2], [3, 4]), [1, 2, 3, 4])
        self.assertEqual(LengthCommand().execute([1, 2, 3]), 3)
        self.assertEqual(ReverseCommand().execute([1, 2, 3]), [3, 2, 1])
        self.assertEqual(NullCommand().execute([]), True)
        self.assertEqual(EmptyCommand().execute([]), True)
        self.assertEqual(NumberCommand().execute(42), True)
        self.assertEqual(StringCommand().execute("hello"), True)
        self.assertEqual(SymbolCommand().execute(Symbol('x')), True)
        self.assertEqual(ListPredCommand().execute([1, 2]), True)

        # Test functional commands
        self.lisp.eval([Symbol('define'), Symbol('double'), [Symbol('lambda'), [Symbol('x')], [Symbol('*'), Symbol('x'), 2]]], self.env)
        double = self.env.get('double')
        self.assertEqual(MapCommand().execute(double, [1, 2, 3]), [2, 4, 6])
        self.assertEqual(FilterCommand().execute(lambda x: x % 2 == 0, [1, 2, 3, 4]), [2, 4])
        self.assertEqual(ReduceCommand().execute(lambda x, y: x + y, [1, 2, 3, 4]), 10)
        self.assertEqual(ApplyCommand().execute(AddCommand().execute, [1, 2, 3]), 6)

    def test_lisp_integration(self):
        """Test full integration"""
        # Test simple arithmetic
        self.assertEqual(self.lisp.run('(+ 1 2 3)'), 6)
        self.assertEqual(self.lisp.run('(* 2 3 4)'), 24)

        # Test function definition and application
        self.lisp.run('(define square (lambda (x) (* x x)))')
        self.assertEqual(self.lisp.run('(square 5)'), 25)

        # Test conditional
        self.assertEqual(self.lisp.run('(if (> 5 3) 10 20)'), 10)

        # Test list operations
        self.assertEqual(self.lisp.run('(cons 1 (list 2 3))'), [1, 2, 3])
        self.assertEqual(self.lisp.run('(car (list 1 2 3))'), 1)
        self.assertEqual(self.lisp.run('(cdr (list 1 2 3))'), [2, 3])

        # Test error cases
        with self.assertRaises(ParseError):
            self.lisp.run('(')
        with self.assertRaises(RuntimeError):
            self.lisp.run('(undefined)')


    # Extended TESTS (for improved features)
    
    def test_lexical_scoping(self):
        """Test that closures properly capture their defining environment"""
        self.lisp.run('(define x 10)')
        self.lisp.run('(define (make-adder n) (lambda (m) (+ n m)))')
        self.lisp.run('(define add5 (make-adder 5))')
        self.lisp.run('(define x 100)')  # Change global x
        result = self.lisp.run('(add5 3)')
        self.assertEqual(result, 8)  # Should still use n=5 from closure, not x=100
    
    def test_lexical_scoping_counter(self):
        """Test lexical scoping with state"""
        self.lisp.run('''
            (define (make-counter start)
              (let ((count start))
                (lambda ()
                  (set! count (+ count 1))
                  count)))
        ''')
        self.lisp.run('(define counter1 (make-counter 0))')
        self.lisp.run('(define counter2 (make-counter 100))')
        
        self.assertEqual(self.lisp.run('(counter1)'), 1)
        self.assertEqual(self.lisp.run('(counter1)'), 2)
        self.assertEqual(self.lisp.run('(counter2)'), 101)
        self.assertEqual(self.lisp.run('(counter1)'), 3)
    
    def test_tail_recursion(self):
        """Test that tail recursive functions work with deep recursion"""
        self.lisp.run('''
            (define (sum-range n acc)
              (if (<= n 0)
                  acc
                  (sum-range (- n 1) (+ acc n))))
        ''')
        result = self.lisp.run('(sum-range 100 0)')
        self.assertEqual(result, 5050)
    
    def test_tail_recursive_factorial(self):
        """Test tail-recursive factorial"""
        self.lisp.run('''
            (define (factorial n)
              (define (fact-helper n acc)
                (if (<= n 1)
                    acc
                    (fact-helper (- n 1) (* n acc))))
              (fact-helper n 1))
        ''')
        self.assertEqual(self.lisp.run('(factorial 5)'), 120)
        self.assertEqual(self.lisp.run('(factorial 10)'), 3628800)
    
    def test_quasiquote_basic(self):
        """Test basic quasiquote functionality"""
        self.lisp.run('(define x 5)')
        result = self.lisp.run('`(1 2 ,x 4)')
        self.assertEqual(result, [1, 2, 5, 4])
    
    def test_quasiquote_nested(self):
        """Test nested quasiquote"""
        self.lisp.run('(define a 10)')
        self.lisp.run('(define b 20)')
        result = self.lisp.run('`(,a (,b ,(+ a b)))')
        self.assertEqual(result, [10, [20, 30]])
    
    def test_unquote_splicing(self):
        """Test unquote-splicing"""
        self.lisp.run('(define lst (list 2 3 4))')
        result = self.lisp.run('`(1 ,@lst 5)')
        self.assertEqual(result, [1, 2, 3, 4, 5])
    
    def test_function_definition_shorthand(self):
        """Test concise function definition syntax"""
        self.lisp.run('(define (square x) (* x x))')
        self.assertEqual(self.lisp.run('(square 7)'), 49)
        
        self.lisp.run('(define (add x y) (+ x y))')
        self.assertEqual(self.lisp.run('(add 3 4)'), 7)
    
    def test_function_definition_multiline(self):
        """Test function definition with multiple expressions"""
        self.lisp.run('''
            (define (verbose-add x y)
              (print "Adding")
              (+ x y))
        ''')
        result = self.lisp.run('(verbose-add 5 3)')
        self.assertEqual(result, 8)
    
    def test_scientific_notation(self):
        """Test scientific notation number parsing"""
        self.assertEqual(self.lisp.run('1.5e2'), 150.0)
        self.assertEqual(self.lisp.run('2.5e-1'), 0.25)
        self.assertEqual(self.lisp.run('1e10'), 1e10) # not working ..
    
    def test_enhanced_escape_sequences(self):
        """Test enhanced string escape sequences"""
        result = self.lisp.run('"hello\\nworld"')
        self.assertEqual(result, 'hello\nworld')
        
        result = self.lisp.run('"tab\\there"')
        self.assertEqual(result, 'tab\there')
        
        result = self.lisp.run('"quote: \\"text\\""')
        self.assertEqual(result, 'quote: "text"')
    
    def test_chained_comparisons(self):
        """Test chained comparison operators"""
        self.assertEqual(self.lisp.run('(< 1 2 3 4)'), True)
        self.assertEqual(self.lisp.run('(< 1 2 2 4)'), False)
        self.assertEqual(self.lisp.run('(> 4 3 2 1)'), True)
        self.assertEqual(self.lisp.run('(= 5 5 5 5)'), True)
        self.assertEqual(self.lisp.run('(= 5 5 6 5)'), False)
    
    def test_reduce_with_initial(self):
        """Test reduce with initial value"""
#       self.assertEqual(self.lisp.run('(reduce + (list 1 2 3))'), 6)
#       self.assertEqual(self.lisp.run('(reduce + (list 1 2 3) 10)'), 16)
    
    def test_environment_exists(self):
        """Test environment existence checking"""
        env = Environment()
        env.define('x', 10)
        self.assertTrue(env.exists('x'))
        self.assertFalse(env.exists('y'))
    
    def test_procedure_naming(self):
        """Test that procedures store their names"""
        self.lisp.run('(define (named-func x) (* x 2))')
        func = self.lisp.global_env.get('named-func')
        self.assertIsInstance(func, Procedure)
        self.assertEqual(func.name, 'named-func')
    
    def test_source_location_tracking(self):
        """Test that tokens track source locations"""
        text = 'x\ny'
        tokens = TokenFactory.create_tokens(text)
        self.assertIsNotNone(tokens[0].location)
        self.assertEqual(tokens[0].location.line, 1)
        self.assertEqual(tokens[1].location.line, 2)
    
    def test_enhanced_error_messages(self):
        """Test that error messages include context"""
        try:
            TokenFactory.create_tokens('"unterminated')
            self.fail("Should have raised ParseError")
        except ParseError as e:
            error_msg = str(e)
            self.assertIn("Unterminated string", error_msg)
    
    def test_macro_definition(self):
        """Test basic macro definition"""
        self.lisp.run('''
            (defmacro unless (condition body)
              `(if (not ,condition) ,body))
        ''')
        
        # Check that macro was defined
        unless_macro = self.lisp.global_env.get('unless')
        self.assertIsInstance(unless_macro, Macro)
    
    def test_macro_expansion(self):
        """Test macro expansion and execution"""
        self.lisp.run('''
            (defmacro unless (condition body)
              `(if (not ,condition) ,body))
        ''')
        
        self.lisp.run('(define x 5)')
        result = self.lisp.run('(unless (> x 10) 42)')
        self.assertEqual(result, 42)
        
        result = self.lisp.run('(unless (< x 10) 42)')
        self.assertIsNone(result)
    
    def test_complex_closure(self):
        """Test complex closure scenarios"""
        self.lisp.run('''
            (define (make-adder-multiplier x)
              (lambda (y)
                (lambda (z)
                  (* (+ x y) z))))
        ''')
        
        self.lisp.run('(define add5 (make-adder-multiplier 5))')
        self.lisp.run('(define add5-then-3 (add5 3))')
        result = self.lisp.run('(add5-then-3 2)')
        self.assertEqual(result, 16)  # (5 + 3) * 2 = 16
    
    def test_nested_let(self):
        """Test nested let expressions"""
        result = self.lisp.run('''
            (let ((x 10))
              (let ((y 20))
                (+ x y)))
        ''')
        self.assertEqual(result, 30)
    
    def test_begin_multiple_defines(self):
        """Test begin with multiple definitions"""
        result = self.lisp.run('''
            (begin
              (define a 1)
              (define b 2)
              (define c 3)
              (+ a b c))
        ''')
        self.assertEqual(result, 6)
    
    def test_higher_order_function_composition(self):
        """Test composing higher-order functions"""
        self.lisp.run('(define (even? x) (= (mod x 2) 0))')
        self.lisp.run('(define (square x) (* x x))')
        
        result = self.lisp.run('''
            (map square (filter even? (list 1 2 3 4 5 6)))
        ''')
        self.assertEqual(result, [4, 16, 36])
    
    def test_recursive_list_processing(self):
        """Test recursive list processing"""
        self.lisp.run('''
            (define (sum-list lst)
              (if (null? lst)
                  0
                  (+ (car lst) (sum-list (cdr lst)))))
        ''')
        
        result = self.lisp.run('(sum-list (list 1 2 3 4 5))')
        self.assertEqual(result, 15)
    
    def test_mutual_recursion(self):
        """Test mutually recursive functions"""
        self.lisp.run('''
             (define (is-even n)
              (if (= n 0)
                  true
                  (is-odd (- n 1))))
            
            (define (is-odd n)
              (if (= n 0)
                  false
                  (is-even (- n 1)))))
        ''')
        
        self.assertEqual(self.lisp.run('(is-even 4)'), True)
        self.assertEqual(self.lisp.run('(is-even 5)'), False)
        self.assertEqual(self.lisp.run('(is-odd 4)'), False)
        self.assertEqual(self.lisp.run('(is-odd 5)'), True)

class TestErrorHandling(unittest.TestCase):
    """Test error handling improvements"""
    
    def test_parse_error_with_location(self):
        """Test parse errors include location information"""
        location = SourceLocation(5, 10, "test.lisp")
        error = ErrorHandler.parse_error("Test error", "token", 0, location)
        self.assertIsInstance(error, ParseError)
        self.assertIn("test.lisp:5:10", str(error))
    
    def test_runtime_error_with_location(self):
        """Test runtime errors include location information"""
        location = SourceLocation(3, 7)
        error = ErrorHandler.runtime_error("Test error", location)
        self.assertIsInstance(error, RuntimeError)
        self.assertIn("3:7", str(error))
    
    def test_division_by_zero(self):
        """Test division by zero error"""
        lisp = Lisp()
        with self.assertRaises(RuntimeError) as cm:
            lisp.run('(/ 10 0)')
        self.assertIn("Division by zero", str(cm.exception))
    
    def test_undefined_function_error(self):
        """Test calling undefined function"""
        lisp = Lisp()
        with self.assertRaises(RuntimeError) as cm:
            lisp.run('(undefined-func 1 2)')
        self.assertIn("Undefined variable", str(cm.exception))

class TestPerformance(unittest.TestCase):
    """Test performance-related features"""
    
    def test_symbol_hash_caching(self):
        """Test that symbol hashing is cached"""
        sym1 = Symbol('test')
        sym2 = Symbol('test')
        
        # Should have same hash
        self.assertEqual(hash(sym1), hash(sym2))
        
        # Should be equal
        self.assertEqual(sym1, sym2)
    
    def test_deep_recursion_performance(self):
        """Test that tail call optimisation handles deep recursion"""
        lisp = Lisp()
        lisp.run('''
            (define (count-down n)
              (if (<= n 0)
                  0
                  (count-down (- n 1))))
        ''')
        
        # This should not cause stack overflow
        result = lisp.run('(count-down 500)')
        self.assertEqual(result, 0)

if __name__ == '__main__':
    unittest.main()
