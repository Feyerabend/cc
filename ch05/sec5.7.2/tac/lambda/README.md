
## Lambda Calculus and TAC

The lambda calculus is a small but expressive formal system for describing
computation using only function abstraction and function application. It was
introduced by Alonzo Church in the 1930s as part of his work on the foundations
of mathematics, and it was later shown to be computationally equivalent to
Turing machines. Despite having very few syntactic constructs, the lambda
calculus can express all computable functions.

In programming language theory, the lambda calculus serves as a foundational
model for understanding functions as first-class values. Concepts such as
*variable binding*, *substitution*, and *lexical scoping* are defined precisely
within the lambda calculus and later reappear in concrete programming
languages. The core semantics of many functional languages can be described
almost directly as variants of the lambda calculus with additional features
such as data types, recursion, and control constructs.

The influence of the lambda calculus is not limited to purely functional
languages. Modern imperative and object-oriented languages adopt lambda-based
ideas through *anonymous functions*, *closures*, and *higher-order functions*.
From a compiler perspective, lambda calculus provides a clean intermediate model
for reasoning about program transformations, evaluation strategies, and
correctness. Many compiler IRs and optimisation techniques can be understood
as structured extensions or translations of lambda-calculus-based semantics.

Here we introduce the lambda calculus primarily to demonstrate concepts beyond
conventional parsing of imperative languages. But it also serves to show how
lambda expressions can be represented, analysed, and ultimately transformed into
executable form.


