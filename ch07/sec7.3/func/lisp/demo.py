#!/usr/bin/env python3
"""
Quick Demo of Mini-Lisp
Run this for a quick demonstration of the mini-lisp interpreter
"""

import sys

from lisp import Lisp

def print_section(title):
    print()
    print("-" * 60)
    print(f"  {title}")
    print("\n\n")

def demo():
    lisp = Lisp()
    
    print_section("Loading Mini-Lisp Interpreter")
    with open('mini-lisp.l', 'r') as f:
        lisp.run(f.read())
    
    print_section("Demo 1: Simple Arithmetic")
    print("Expression: (mini-eval '(+ 10 20 30) global-mini-env)")
    result = lisp.run("(mini-eval '(+ 10 20 30) global-mini-env)")
    print(f"Result: {lisp.formatter.format(result)}")
    
    print_section("Demo 2: Define a Variable")
    print("Expression: (mini-eval '(define pi 3.14159) global-mini-env)")
    result = lisp.run("(mini-eval '(define pi 3.14159) global-mini-env)")
    print(f"Defined: {lisp.formatter.format(result)}")
    print()
    print("Expression: (mini-eval 'pi global-mini-env)")
    result = lisp.run("(mini-eval 'pi global-mini-env)")
    print(f"Value: {lisp.formatter.format(result)}")
    
    print_section("Demo 3: Lambda Functions")
    print("Expression: (mini-eval '(define square (lambda (x) (* x x))) global-mini-env)")
    result = lisp.run("(mini-eval '(define square (lambda (x) (* x x))) global-mini-env)")
    print(f"Defined: {lisp.formatter.format(result)}")
    print()
    print("Expression: (mini-eval '(square 12) global-mini-env)")
    result = lisp.run("(mini-eval '(square 12) global-mini-env)")
    print(f"Result: {lisp.formatter.format(result)}")
    
    print_section("Demo 4: Conditional Logic")
    print("Expression: (mini-eval '(if (> 10 5) \"bigger\" \"smaller\") global-mini-env)")
    result = lisp.run("(mini-eval '(if (> 10 5) \"bigger\" \"smaller\") global-mini-env)")
    print(f"Result: {lisp.formatter.format(result)}")
    
    print_section("Demo 5: Anonymous Functions")
    print("Expression: (mini-eval '((lambda (a b) (+ a b)) 7 8) global-mini-env)")
    result = lisp.run("(mini-eval '((lambda (a b) (+ a b)) 7 8) global-mini-env)")
    print(f"Result: {lisp.formatter.format(result)}")
    
    print_section("Demo 6: List Operations")
    print("Expression: (mini-eval '(car (cons 42 (cons 99 (quote ())))) global-mini-env)")
    result = lisp.run("(mini-eval '(car (cons 42 (cons 99 (quote ())))) global-mini-env)")
    print(f"Result: {lisp.formatter.format(result)}")
    
    print_section("Demo 7: Nested Expressions")
    print("Expression: (mini-eval '(+ (* 2 3) (* 4 5)) global-mini-env)")
    result = lisp.run("(mini-eval '(+ (* 2 3) (* 4 5)) global-mini-env)")
    print(f"Result: {lisp.formatter.format(result)}")
    
    print_section("Demo 8: Higher-Order Functions")
    print("Expression: (mini-eval '(define apply-twice (lambda (f x) (f (f x)))) global-mini-env)")
    lisp.run("(mini-eval '(define apply-twice (lambda (f x) (f (f x)))) global-mini-env)")
    print()
    print("Expression: (mini-eval '(define inc (lambda (n) (+ n 1))) global-mini-env)")
    lisp.run("(mini-eval '(define inc (lambda (n) (+ n 1))) global-mini-env)")
    print()
    print("Expression: (mini-eval '(apply-twice inc 10) global-mini-env)")
    result = lisp.run("(mini-eval '(apply-twice inc 10) global-mini-env)")
    print(f"Result: {lisp.formatter.format(result)}")
    
    print_section("Demo Complete!")
    print("This is a Lisp interpreter written in Lisp ..")
    print("running inside a Lisp interpreter ..")
    print("written in Python.")
    print()

if __name__ == '__main__':
    demo()
