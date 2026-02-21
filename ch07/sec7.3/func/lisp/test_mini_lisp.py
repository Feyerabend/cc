#!/usr/bin/env python3
"""
Test runner for Mini-Lisp interpreter
Loads the mini-lisp interpreter into the host Python-based Lisp interpreter
"""

import sys
import os


from lisp import Lisp, LispError

def main():
    print("=" * 60)
    print("Mini-Lisp in Lisp - Test Runner")
    print("=" * 60)
    print()
    
    # Create the host Lisp interpreter
    lisp = Lisp()
    
    # Load the mini-lisp interpreter
    print("Loading mini-lisp.l into host interpreter..")
    print()
    
    try:
        with open('mini-lisp.l', 'r') as f:
            mini_lisp_code = f.read()
        
        # Run the mini-lisp code in the host interpreter
        lisp.run(mini_lisp_code)
        print()
        
        print("=" * 60)
        print("Running automated tests..")
        print("=" * 60)
        print()
        
        # Run the test suite
        lisp.run("(test-mini-lisp)")
        
        print()
        print("=" * 60)
        print("Testing recursion protection..")
        print("=" * 60)
        print()
        
        # Test recursion limit
        lisp.run("(test-recursion-limit)")
        
        print()
        print("=" * 60)
        print("Running examples..")
        print("=" * 60)
        print()
        
        # Run fibonacci example
        lisp.run("(run-example 'fibonacci example-fibonacci)")
        
        # Run sum-list example
        lisp.run("(run-example 'sum-list example-sum-list)")
        
        print()
        print("=" * 60)
        print("Interactive examples:")
        print("=" * 60)
        print()
        
        # Show some interactive examples
        print(">>> Defining a function in mini-lisp:")
        print("(mini-eval '(define triple (lambda (x) (* x 3))) global-mini-env)")
        result = lisp.run("(mini-eval '(define triple (lambda (x) (* x 3))) global-mini-env)")
        print(f"Result: {lisp.formatter.format(result)}")
        print()
        
        print(">>> Calling the function:")
        print("(mini-eval '(triple 7) global-mini-env)")
        result = lisp.run("(mini-eval '(triple 7) global-mini-env)")
        print(f"Result: {lisp.formatter.format(result)}")
        print()
        
        print(">>> Complex expression with nested functions:")
        print("(mini-eval '((lambda (x y) (+ (* x x) (* y y))) 3 4) global-mini-env)")
        result = lisp.run("(mini-eval '((lambda (x y) (+ (* x x) (* y y))) 3 4) global-mini-env)")
        print(f"Result: {lisp.formatter.format(result)}")
        print()
        
        print("=" * 60)
        print("SUCCESS! Mini-Lisp is running inside the host Lisp!")
        print("=" * 60)
        print()
        print("You now have a Lisp interpreter written in Lisp,")
        print("running in a Lisp interpreter written in Python!")
        print()
        
    except LispError as e:
        print(f"Error: {e}")
        return 1
    except FileNotFoundError as e:
        print(f"Error: Could not find file: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
