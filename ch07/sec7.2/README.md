
## Type Systems: Formal Introduction

A *type system* classifies program expressions according to the kinds of values they compute,
ensuring certain correctness properties. Typing judgments are written as:

```math
\[
\Gamma \vdash e : \tau
\]
```

where:
```math
- \(\Gamma\) is the typing context (variables and their types)
- \(e\) is an expression
- \(\tau\) is the type
- \(\Gamma \vdash e : \tau\) reads: "under context \(\Gamma\), expression \(e\) has type \(\tau\)"
```


### Example: Variable Typing

```math
\[
\frac{x:\tau \in \Gamma}{\Gamma \vdash x : \tau} \quad (\text{Var})
\]
```

If a variable \(x\) has type \(\tau\) in the context, it is assigned type \(\tau\).



### Example: Addition

```math
\[
\frac{\Gamma \vdash e_1 : \text{Int} \quad \Gamma \vdash e_2 : \text{Int}}{\Gamma \vdash e_1 + e_2 : \text{Int}} \quad (\text{Add})
\]
```

If \(e_1\) and \(e_2\) are integers, then \(e_1 + e_2\) is also an integer.



### Simply-Typed Lambda Calculus

*Abstraction:*

```math
\[
\frac{\Gamma, x:\tau_1 \vdash e : \tau_2}{\Gamma \vdash (\lambda x.e) : \tau_1 \to \tau_2} \quad (\text{Abs})
\]
```

*Application:*

```math
\[
\frac{\Gamma \vdash e_1 : \tau_1 \to \tau_2 \quad \Gamma \vdash e_2 : \tau_1}{\Gamma \vdash e_1 \, e_2 : \tau_2} \quad (\text{App})
\]
```

These formal rules allow reasoning about programs rigorously
and form the foundation for modern type theory.  

