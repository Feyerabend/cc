## Exercises

### Formal Methods, Types, and the Limits of Computation

#### Logic and Proof

1. *What is the difference between a proof and a test?*
   - What can a proof guarantee that testing cannot? What can testing find that a proof might miss?

2. *What is a formal specification? What does it specify, and what does it leave out?*
   - Give an example: what would a formal specification of a sorting function say?

3. *What is propositional logic? What are its basic connectives?*
   - Express "if it rains, the ground is wet" as a propositional formula.

4. *What is predicate logic (first-order logic)? How does it extend propositional logic?*
   - Give an example of a statement that requires predicate logic and cannot be expressed
     in propositional logic alone.

5. *What is a tautology? What is a contradiction?*
   - Give an example of each. How does a SAT solver relate to these concepts?

6. *What is Hoare logic?*
   - What does a Hoare triple `{P} C {Q}` mean? Give a simple example.

7. *What is the halting problem?*
   - State the problem informally. Why is it undecidable? What does this imply about
     the limits of automated program analysis?

8. *What is Rice's theorem?*
   - What does it say about the properties of programs that can be automatically checked?
     Give an example of a property that Rice's theorem says cannot be checked in general.


#### Type Theory

1. *What is a type system, and what problem does it solve?*
   - Give an example of a type error that a type system prevents.

2. *What is the Curry-Howard correspondence?*
   - Complete the analogy: types are to propositions as programs are to ______.
   - What does it mean to "type-check" a proof?

3. *What is a dependent type? Give a simple example.*
   - What can a dependent type express that a simple type cannot?
   - Give an example of a bug that dependent types would prevent.

4. *What is a linear type? What does "use exactly once" mean for a resource?*
   - Give two examples of resources in real programs that should be used exactly once.

5. *What is Homotopy Type Theory (HoTT)?*
   - What is an identity type? What does it mean for two values to be "identical" in HoTT?
   - What is the univalence axiom, informally?

6. *What is Martin-Löf Type Theory?*
   - What is a judgment in MLTT? How does it differ from a proposition?
   - Why is MLTT described as "constructive"?

7. *What is a proof assistant? Give three examples.*
   - What is the difference between an interactive proof assistant and an automated theorem prover?

8. *What is a certified program?*
   - What does it mean to extract a program from a proof? Why is the extracted program correct?


#### Formal Verification Tools

1. *What is an SMT solver? What does "satisfiability modulo theories" mean?*
   - Give an example of a problem that Z3 can solve. What does the solver output?

2. *What is symbolic execution?*
   - How does it differ from running a program on a concrete input?
   - What class of bugs does symbolic execution find well?

3. *What is model checking?*
   - What is a model? What is a property? What does the model checker do?
   - What is a counterexample trace?

4. *What is Computation Tree Logic (CTL)?*
   - What is the difference between the `AG` operator and the `EF` operator?
   - Express "the system is never in a deadlock state" as a CTL formula.

5. *What is Presburger arithmetic?*
   - What can it express? What can it not express?
   - Why is it useful for reasoning about array indices and loop bounds?

6. *What is a SAT solver? How does it relate to an SMT solver?*
   - What is the DPLL algorithm? What problem does it solve?

7. *What is formal verification of software? What has been formally verified in practice?*
   - Give two real-world examples. What properties were verified, and what tools were used?


#### Category Theory

1. *What is a category? What are its components?*
   - Give three examples of categories from mathematics and programming.

2. *What is a functor? What does it preserve?*
   - Give an example of a functor from programming. What does it map?

3. *What is a natural transformation?*
   - Informally, what does it mean for two functors to be "naturally" related?

4. *What is a monad? What two operations must it support?*
   - Give an example of a monad from programming. What structure does it impose on computations?

5. *What is the relationship between category theory and type theory?*
   - What does a type correspond to in categorical language?
   - What does a program (function) correspond to?

6. *Why do some argue that category theory is the "mathematics of mathematics"?*
   - What does it abstract over? What does this generality buy in programming language theory?
