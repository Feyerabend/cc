
## Designing Programming Languages: From Type Theory to Virtual Machine Code

*A Comprehensive Guide to Language Design with Emphasis on Type Systems*

### Part I: Foundations of Language Design

#### 1. The Design Philosophy

##### 1.1 What Makes a Good Language?

A well-designed programming language embodies several principles:

- *Clarity*: Semantics should be unambiguous
- *Expressiveness*: Complex ideas in simple terms
- *Safety*: Errors caught early (at compile time when possible)
- *Efficiency*: Predictable performance characteristics
- *Teachability*: Concepts build on each other logically

For educational purposes targeting a virtual machine, we add:

- *Transparency*: Students see how high-level constructs map to VM instructions
- *Minimalism*: Small language core exposes compilation fundamentals

##### 1.2 The Role of Type Systems

Type systems serve multiple purposes:

1. *Safety*: Prevent invalid operations at compile time
2. *Documentation*: Types communicate programmer intent
3. *Optimization*: Enable compiler to generate better code
4. *Abstraction*: Allow reasoning about code without running it

For VM compilation, types also:

- *Guide register allocation*: Different types have different storage needs
- *Determine calling conventions*: How data flows between functions
- *Enable static analysis*: Detect overflow, size mismatches

#### 2. Choosing Your Language Model

##### 2.1 Computation Model

We adopt a *pure, expression-oriented, strict evaluation* model:

```
Computation Style:
- Pure: No mutation, no side effects
- Expression-oriented: Everything returns a value
- Strict: Call-by-value evaluation
```

*Why this model?*

- Referential transparency simplifies reasoning
- Expressions compose naturally
- Strict evaluation has predictable execution order (crucial for VM)
- Maps cleanly to stack machine: evaluate, push, consume

##### 2.2 Core Language: A Minimal Calculus

We design a minimal language sufficient for teaching compilation:

```
Types:
τ ::= Int8      -- 8-bit integers
    | Int16     -- 16-bit integers
    | Int32     -- 32-bit integers
    | Bool      -- Boolean values

Expressions:
e ::= n                           -- Integer literals
    | true                        -- Boolean true
    | false                       -- Boolean false
    | x                           -- Variables
    | e + e                       -- Addition
    | e - e                       -- Subtraction
    | e * e                       -- Multiplication
    | e < e                       -- Comparison
    | e == e                      -- Equality
    | if e then e else e          -- Conditional
    | let x = e in e              -- Local binding
    | fn(x₁: τ₁, ..., xₙ: τₙ) -> τ { e }  -- Function definition
    | f(e₁, ..., eₙ)              -- Function call
```

This minimal calculus is:

- *Complete*: Can express all computations
- *Simple*: Few constructs to implement
- *Representative*: Shows key compilation challenges

#### 3. Formal Semantics

##### 3.1 Why Formalize Semantics?

Formal semantics provide:

- *Precise specification*: No ambiguity about behavior
- *Correctness proofs*: Verify compilation preserves meaning
- *Implementation guide*: Clear rules for interpreter/compiler
- *Testing oracle*: Generate correct test cases

##### 3.2 Big-Step Operational Semantics

Big-step semantics describe evaluation from expression to final value:

$$
e \downarrow v
$$

*Read as*: "Expression e evaluates to value v"

__Core Rules:__

*Literals:*

$$
\frac{}{n \downarrow n}
$$

$$
\frac{}{true \downarrow true}
$$

$$
\frac{}{false \downarrow false}
$$

*Addition:*

$$
\frac{e_1 \downarrow n_1 \quad e_2 \downarrow n_2}{e_1 + e_2 \downarrow n_1 + n_2}
$$

*Conditional (True):*

$$
\frac{c \downarrow true \quad t \downarrow v}{if \ c \ then \ t \ else \ f \downarrow v}
$$

*Conditional (False):*

$$
\frac{c \downarrow false \quad f \downarrow v}{if \ c \ then \ t \ else \ f \downarrow v}
$$

*Let Binding:*

$$
\frac{e_1 \downarrow v_1 \quad e_2[x \mapsto v_1] \downarrow v_2}{let \ x = e_1 \ in \ e_2 \downarrow v_2}
$$

Where `e[x ↦ v]` denotes capture-avoiding substitution.

##### 3.3 Small-Step Operational Semantics

Small-step semantics show individual computation steps:

$$
e \rightarrow e'
$$

*Read as*: "Expression e reduces to e' in one step"

__Core Reduction Rules:

*Addition (Left):*

$$
\frac{e_1 \rightarrow e_1'}{e_1 + e_2 \rightarrow e_1' + e_2}
$$

*Addition (Right):*

$$
\frac{e_2 \rightarrow e_2'}{v + e_2 \rightarrow v + e_2'}
$$

*Addition (Final):*

$$
\frac{}{n_1 + n_2 \rightarrow n_3}
$$

where n₃ = n₁ + n₂

*Let (Evaluate Binding):*

$$
\frac{e_1 \rightarrow e_1'}{let \ x = e_1 \ in \ e_2 \rightarrow let \ x = e_1' \ in \ e_2}
$$

*Let (Substitute):*

$$
\frac{}{let \ x = v \ in \ e \rightarrow e[x \mapsto v]}
$$

*Conditional (Reduce Condition):*

$$
\frac{c \rightarrow c'}{if \ c \ then \ t \ else \ f \rightarrow if \ c' \ then \ t \ else \ f}
$$

*Conditional (True):*

$$
\frac{}{if \ true \ then \ t \ else \ f \rightarrow t}
$$

*Conditional (False):*

$$
\frac{}{if \ false \ then \ t \ else \ f \rightarrow f}
$$

__Multi-Step Reduction:

$$
e \rightarrow^* e'
$$

Means: e reduces to e' in zero or more steps.

##### 3.4 Semantic Equivalence

Both semantics should agree:

$$
e \downarrow v \iff e \rightarrow^* v
$$

This equivalence is crucial for correctness:

- Big-step: Shows final result
- Small-step: Shows execution order (important for VM!)

### Part II: Type System Design

#### 4. Type System Foundations

##### 4.1 The Purpose of Types

Types classify values and expressions by their behavior:

```
Int8: Values fitting in one byte (0-255 or -128 to 127)
Int16: Values fitting in two bytes (-32768 to 32767)
Int32: Values fitting in four bytes (-2147483648 to 2147483647)
Bool: True or false values
```

Types enable:

- *Static verification*: Catch errors before running
- *Memory layout*: Know how much space to allocate
- *Instruction selection*: Choose appropriate VM instructions

##### 4.2 Typing Contexts

A typing context tracks variable types:

$$
\Gamma ::= \emptyset \quad | \quad \Gamma, x: \tau
$$

Example:

$$
\Gamma = \{x: Int32, y: Bool, z: Int16\}
$$

##### 4.3 Typing Judgment

The fundamental typing judgment:

$$
\Gamma \vdash e : \tau
$$

*Read as*: "Under context Γ, expression e has type τ"

##### 4.4 Type System Rules

__Literals:__

$$
\frac{}{\Gamma \vdash n : Int32}
$$

(Default: literals are Int32)

$$
\frac{}{\Gamma \vdash true : Bool}
$$

$$
\frac{}{\Gamma \vdash false : Bool}
$$

__Variables:__

$$
\frac{x: \tau \in \Gamma}{\Gamma \vdash x : \tau}
$$

__Addition:__

$$
\frac{\Gamma \vdash e_1 : Int32 \quad \Gamma \vdash e_2 : Int32}{\Gamma \vdash e_1 + e_2 : Int32}
$$

__Subtraction:__

$$
\frac{\Gamma \vdash e_1 : Int32 \quad \Gamma \vdash e_2 : Int32}{\Gamma \vdash e_1 - e_2 : Int32}
$$

__Comparison:__

$$
\frac{\Gamma \vdash e_1 : Int32 \quad \Gamma \vdash e_2 : Int32}{\Gamma \vdash e_1 < e_2 : Bool}
$$

__Conditional:__

$$
\frac{\Gamma \vdash c : Bool \quad \Gamma \vdash t : \tau \quad \Gamma \vdash f : \tau}{\Gamma \vdash if \ c \ then \ t \ else \ f : \tau}
$$

*Key constraint*: Both branches must have the *same type*.

__Let Binding:__

$$
\frac{\Gamma \vdash e_1 : \tau_1 \quad \Gamma, x: \tau_1 \vdash e_2 : \tau_2}{\Gamma \vdash let \ x = e_1 \ in \ e_2 : \tau_2}
$$

__Function Definition:__

$$
\frac{\Gamma, x_1: \tau_1, ..., x_n: \tau_n \vdash e : \tau}{\Gamma \vdash fn(x_1: \tau_1, ..., x_n: \tau_n) -> \tau \{ e \} : \tau_1 \to ... \to \tau_n \to \tau}
$$

__Function Application:__

$$
\frac{\Gamma \vdash f : \tau_1 \to ... \to \tau_n \to \tau \quad \Gamma \vdash e_1 : \tau_1 \quad ... \quad \Gamma \vdash e_n : \tau_n}{\Gamma \vdash f(e_1, ..., e_n) : \tau}
$$

##### 4.5 Type Soundness

The type system is *sound* if:

*Preservation*:

$$
If \ \Gamma \vdash e : \tau \ and \ e \to e', \ then \ \Gamma \vdash e' : \tau
$$

*Progress*:

$$
If \ \emptyset \vdash e : \tau, \ then \ either \ e \ is \ a \ value \ or \ e \to e'
$$

These properties guarantee:

- Well-typed programs don't get stuck
- Evaluation preserves types
- Runtime type errors are impossible

#### 5. Type Inference

##### 5.1 Why Type Inference?

Type inference allows omitting type annotations:

```
Instead of: let x: Int32 = 2 + 3 in x - 1
Programmer writes: let x = 2 + 3 in x - 1
```

Benefits:

- Less verbose code
- Flexibility during prototyping
- Types still verified at compile time

##### 5.2 Type Variables

Introduce type variables for unknown types:

```
τ ::= Int8 | Int16 | Int32 | Bool | α
```

Where α, β, γ are type variables.

##### 5.3 Substitutions

A substitution maps type variables to types:

$$
S = [\alpha \mapsto Int32, \beta \mapsto Bool]
$$

Applying substitution:

$$
S(\alpha) = Int32
$$

$$
S(Int32) = Int32
$$

$$
S(\alpha \to \beta) = Int32 \to Bool
$$

##### 5.4 Unification

Unification finds substitutions making types equal:

```
unify(τ₁, τ₂) = S such that S(τ₁) = S(τ₂)
```

__Unification Algorithm:

```
unify(α, τ) = [α ↦ τ] if α ∉ FV(τ)
unify(τ, α) = [α ↦ τ] if α ∉ FV(τ)
unify(Int32, Int32) = []
unify(Bool, Bool) = []
unify(τ₁ → τ₂, τ₃ → τ₄) = S₂ ∘ S₁
  where S₁ = unify(τ₁, τ₃)
        S₂ = unify(S₁(τ₂), S₁(τ₄))
unify(τ₁, τ₂) = fail (otherwise)
```

*Occurs check*: `α ∉ FV(τ)` prevents infinite types like `α = α → Int32`.

##### 5.5 Constraint Generation

Type inference generates constraints:

```python
def infer(expr, env, constraints):
    match expr:
        case Literal(n):
            return (Int32, constraints)
        case Var(x):
            if x in env:
                return (env[x], constraints)
            else:
                α = fresh_type_var()
                return (α, constraints)
        case Add(e1, e2):
            (τ1, c1) = infer(e1, env, constraints)
            (τ2, c2) = infer(e2, env, c1)
            c3 = c2 + [(τ1, Int32), (τ2, Int32)]
            return (Int32, c3)
        case If(cond, then_e, else_e):
            (τc, c1) = infer(cond, env, constraints)
            (τt, c2) = infer(then_e, env, c1)
            (τe, c3) = infer(else_e, env, c2)
            c4 = c3 + [(τc, Bool), (τt, τe)]
            return (τt, c4)
```

##### 5.6 Constraint Solving

After generating constraints, solve them:

```python
def solve(constraints):
    subst = {}
    for (τ1, τ2) in constraints:
        s = unify(apply_subst(τ1, subst), 
                  apply_subst(τ2, subst))
        subst = compose_subst(s, subst)
    return subst
```

### Part III: Intermediate Representation

#### 6. Why IR?

##### 6.1 Benefits of IR

An intermediate representation:

- *Separates concerns*: Frontend (parsing/typing) from backend (code gen)
- *Enables optimization*: Single representation for all optimizations
- *Supports multiple backends*: VM, native code, JavaScript, etc.
- *Simplifies compilation*: Each phase solves simpler problem

##### 6.2 Choosing an IR

Popular choices:

1. *Three-address code*: Simple, explicit temporaries
2. *Stack-based*: Natural for stack machines (our VM!)
3. *SSA (Static Single Assignment)*: Each variable assigned once
4. *CPS (Continuation-Passing Style)*: Makes control flow explicit

We'll use *three-address code* for its simplicity and clarity.

#### 7. Three-Address Code IR

##### 7.1 Structure

Three-address code limits operations to three operands:

```
t₁ = a + b
t₂ = t₁ * c
t₃ = t₂ - d
```

*Why three addresses?*

- Simple to analyze and optimize
- Maps well to both stack and register machines
- Easy to convert from AST

##### 7.2 IR Instructions

```
Instruction ::= t = n                    -- Load constant
              | t = x                    -- Copy variable
              | t = t₁ ⊕ t₂              -- Binary operation (⊕ ∈ {+, -, *, <, ==})
              | t = -t₁                  -- Unary operation
              | t = call f, t₁, ..., tₙ  -- Function call
              | ret t                    -- Return value
              | if t goto L              -- Conditional jump
              | goto L                   -- Unconditional jump
              | L:                       -- Label
              | t = param i              -- Get parameter i
```

##### 7.3 Translation from AST

__Literals:__

```
AST: 42
IR:  t₁ = 42
```

__Binary Operations:__

```
AST: e₁ + e₂
IR:  [code for e₁ → t₁]
     [code for e₂ → t₂]
     t₃ = t₁ + t₂
```

__Conditionals:__

```
AST: if c then t else f
IR:  [code for c → tc]
     if_false tc goto L_else
     [code for t → tt]
     t_result = tt
     goto L_end
     L_else:
     [code for f → tf]
     t_result = tf
     L_end:
```

__Let Bindings:__

```
AST: let x = e₁ in e₂
IR:  [code for e₁ → t₁]
     [code for e₂ with x mapped to t₁ → t₂]
```

__Function Definitions:__

```
AST: fn(x: Int32, y: Int32) -> Int32 { x + y }
IR:  function_name:
       t_x = param 0
       t_y = param 1
       t_result = t_x + t_y
       ret t_result
```

__Function Calls:__

```
AST: f(e₁, e₂)
IR:  [code for e₁ → t₁]
     [code for e₂ → t₂]
     t_result = call f, t₁, t₂
```

#### 8. IR Optimization

##### 8.1 Constant Folding

Evaluate constant expressions at compile time:

```
Before: t₁ = 2 + 3
After:  t₁ = 5
```

Algorithm:

```python
def constant_fold(instr):
    if instr.is_binary_op():
        if instr.left.is_const() and instr.right.is_const():
            result = eval_op(instr.op, instr.left, instr.right)
            return Const(result)
    return instr
```

##### 8.2 Constant Propagation

Replace variables with their constant values:

```
Before: t₁ = 5
        t₂ = t₁ + 3
After:  t₁ = 5
        t₂ = 5 + 3
        (then fold to: t₂ = 8)
```

##### 8.3 Dead Code Elimination

Remove unused computations:

```
Before: t₁ = 2 + 3  -- t₁ never used
        t₂ = 7 + 8
        ret t₂
After:  t₂ = 7 + 8
        ret t₂
```

##### 8.4 Common Subexpression Elimination

Reuse computed values:

```
Before: t₁ = x + y
        t₂ = x + y
        t₃ = t₁ * t₂
After:  t₁ = x + y
        t₂ = t₁
        t₃ = t₁ * t₁
```

##### 8.5 Tail Call Optimization

Convert recursive calls to loops:

```
Before: function loop(i, acc):
          if i > n:
            ret acc
          else:
            t₁ = i + 1
            t₂ = acc + i
            ret call loop, t₁, t₂
After:  function loop(i, acc):
          L_start:
          if i > n goto L_done
          i = i + 1
          acc = acc + i
          goto L_start
          L_done:
          ret acc
```

### Part IV: Virtual Machine Code Generation

#### 9. Target Virtual Machine

Our VM is a simple stack-based machine with these properties:

- *Stack-oriented*: Primary computation on operand stack
- *Typed instructions*: Separate instructions for different types
- *Simple memory model*: Globals, locals, and heap
- *Call stack*: Separate from operand stack

(See VM-SPECIFICATION.md for complete details)

#### 10. Code Generation Strategy

##### 10.1 Stack Machine Execution

Stack machines evaluate expressions by:

1. Push operands onto stack
2. Execute operation (pops operands, pushes result)
3. Top of stack contains result

Example:

```
Expression: (2 + 3) * 4
Stack evolution:
  []
  [2]           PUSH 2
  [2, 3]        PUSH 3
  [5]           ADD
  [5, 4]        PUSH 4
  [20]          MUL
```

##### 10.2 Translation Patterns

__Literals:__

```
Source: 42
IR:     t₁ = 42
VM:     PUSH_I32 42
```

__Binary Operations:__

```
Source: x + y
IR:     t₁ = x
        t₂ = y
        t₃ = t₁ + t₂
VM:     LOAD_LOCAL x_index
        LOAD_LOCAL y_index
        ADD_I32
```

__Conditionals:__

```
Source: if c then t else f
IR:     if_false tc goto L_else
        [then branch]
        goto L_end
        L_else:
        [else branch]
        L_end:
VM:     [evaluate c]
        JUMP_IF_FALSE L_else
        [then branch]
        JUMP L_end
        L_else:
        [else branch]
        L_end:
```

__Function Calls:__

```
Source: f(a, b, c)
IR:     t₁ = a
        t₂ = b
        t₃ = c
        t₄ = call f, t₁, t₂, t₃
VM:     LOAD_LOCAL a_index
        LOAD_LOCAL b_index
        LOAD_LOCAL c_index
        CALL f 3  ; 3 arguments
```

#### 11. Register/Local Allocation

##### 11.1 Local Variable Assignment

Map IR temporaries to VM local slots:

```python
def allocate_locals(ir_function):
    locals_map = {}
    next_slot = 0
    
    # Parameters get first slots
    for i, param in enumerate(ir_function.params):
        locals_map[param] = i
        next_slot = i + 1
    
    # Then temporaries
    for temp in ir_function.temporaries:
        if temp not in locals_map:
            locals_map[temp] = next_slot
            next_slot += 1
    
    return locals_map
```

##### 11.2 Stack Depth Analysis

Calculate maximum stack depth needed:

```python
def compute_stack_depth(instructions):
    max_depth = 0
    current_depth = 0
    
    for instr in instructions:
        match instr.opcode:
            case 'PUSH' | 'LOAD_LOCAL' | 'LOAD_GLOBAL':
                current_depth += 1
            case 'ADD' | 'SUB' | 'MUL' | 'LT' | 'EQ':
                current_depth -= 1  # Pops 2, pushes 1
            case 'CALL':
                current_depth -= instr.arg_count
                current_depth += 1  # Return value
            case 'RETURN':
                current_depth -= 1
        
        max_depth = max(max_depth, current_depth)
    
    return max_depth
```

#### 12. Complete Compilation Example

##### 12.1 Source Code

```
fn factorial(n: Int32) -> Int32 {
  if n <= 1 then
    1
  else
    n * factorial(n - 1)
}
```

##### 12.2 Type-Checked AST

```
fn factorial : Int32 → Int32
  if (<=) : Bool
    then 1 : Int32
    else (*) : Int32
      n : Int32
      call factorial : Int32
        (-) : Int32
```

##### 12.3 IR Generation

```
function factorial:
  t_n = param 0
  t_1 = 1
  t_cond = t_n <= t_1
  if_false t_cond goto L_else
  t_result = 1
  goto L_end
L_else:
  t_n_minus_1 = t_n - 1
  t_rec = call factorial, t_n_minus_1
  t_result = t_n * t_rec
L_end:
  ret t_result
```

##### 12.4 VM Code Generation

```
function factorial:
  ; Stack depth: 2, Locals: 5
  
  ; Load n and 1, compare
  LOAD_LOCAL 0      ; t_n
  PUSH_I32 1        ; t_1
  DUP               ; Keep 1 for later
  LOAD_LOCAL 0      ; t_n again
  SWAP              ; Order for LE
  LE_I32            ; t_cond
  
  ; Branch on condition
  JUMP_IF_FALSE L_else
  
  ; Then branch: return 1
  PUSH_I32 1
  RETURN
  
L_else:
  ; Else branch: n * factorial(n-1)
  LOAD_LOCAL 0      ; n
  PUSH_I32 1
  SUB_I32           ; n - 1
  CALL factorial 1  ; factorial(n-1)
  LOAD_LOCAL 0      ; n
  MUL_I32           ; n * factorial(n-1)
  RETURN

L_end:
  RETURN
```

#### 13. Advanced Topics

##### 13.1 Closures

Closures capture variables from enclosing scope:

```
fn make_adder(x: Int32) -> (Int32 -> Int32) {
  fn(y: Int32) -> Int32 { x + y }
}
```

*VM Implementation:*

```
; Closure object:
; [function_pointer, captured_vars...]

make_adder:
  LOAD_LOCAL 0      ; x
  LOAD_FUNC inner_fn
  MAKE_CLOSURE 1    ; 1 captured var
  RETURN

inner_fn:
  LOAD_CLOSURE 0    ; Get captured x
  LOAD_LOCAL 0      ; Get parameter y
  ADD_I32
  RETURN
```

##### 13.2 Garbage Collection

For heap-allocated data:

```
VM maintains:
- Heap: Allocate closures, arrays, records
- GC roots: Stack, globals, registers
- Mark-and-sweep or copying collector
```

Basic allocation:

```
ALLOC size      ; Allocate size bytes
                ; Returns pointer on stack
```

### Part V: Error Handling and Debugging

#### 14. Type Error Messages

##### 14.1 Error Location

Track source locations:

```python
class Expr:
    def __init__(self, kind, loc):
        self.kind = kind
        self.location = loc  # (file, line, column)
```

##### 14.2 Contextual Errors

Provide helpful error messages:

```
Error at line 10, column 5:
  if x then y else z
     ^
Type error: Condition must be Bool, got Int32

Note: 'x' was defined as Int32 at line 5
```

##### 14.3 Type Error Recovery

Continue checking after errors:

```python
def type_check_with_recovery(expr, env):
    try:
        return type_check(expr, env)
    except TypeError as e:
        report_error(e)
        return ErrorType()  # Placeholder to continue
```

#### 15. Runtime Debugging

##### 15.1 Debug Information

Emit debug info with VM code:

```
; Debug section
.debug
  function factorial 0
  local n 0 "n: Int32"
  line 1 0x0000
  line 2 0x0004
  line 5 0x0012
```

##### 15.2 Stack Traces

VM maintains call stack for errors:

```
Runtime Error: Division by zero
Stack trace:
  at divide (line 15)
  at calculate (line 23)
  at main (line 42)
```

### Part VI: Extensions and Future Directions

#### 16. Memory Management

##### 16.1 Stack Allocation

Simple, automatic:

```
fn example() -> Int32 {
  let x = 10 in
  let y = x + 5 in
  y * 2
}
```

*VM implementation:*

```
PUSH_I32 10       ; x on stack
DUP
PUSH_I32 5
ADD_I32           ; y on stack
PUSH_I32 2
MUL_I32
```

##### 16.2 Region-Based Memory

Group allocations by lifetime:

```
region r {
  let x = allocate_in_region<Int32>(r)
  ...
} -- All allocations in r freed here
```

##### 16.3 Linear Types

Enforce single ownership:

```
type Buffer = linear [Int8; 256]
fn use_buffer(b: Buffer) {
  // b must be used exactly once
}
```

#### 17. Concurrency

##### 17.1 Green Threads

Lightweight threads in VM:

```
VM maintains:
- Thread queue
- Per-thread stacks
- Scheduler
```

Instructions:

```
SPAWN func        ; Create new thread
YIELD             ; Switch to another thread
JOIN thread_id    ; Wait for thread
```

#### 18. Conclusion

##### 18.1 What We've Built

A complete language design including:

1. *Formal semantics*: Big-step and small-step
2. *Type system*: With inference and soundness
3. *Compilation pipeline*: From source to VM code
4. *IR*: Three-address code for optimization
5. *Backend*: Efficient VM code generation

##### 18.2 Key Lessons

*Type systems:*

- Catch errors early
- Guide compilation
- Enable optimization

*IRs:*

- Separate concerns
- Enable multiple backends
- Facilitate optimization

*VM target:*

- Portable across platforms
- Simpler than native code
- Excellent teaching platform

##### 18.3 Further Reading

*Type theory:*

- Pierce, B. C. (2002). *Types and Programming Languages*
- Harper, R. (2016). *Practical Foundations for Programming Languages*

*Compilation:*

- Appel, A. W. (1998). *Modern Compiler Implementation in ML*
- Cooper, K. D., & Torczon, L. (2011). *Engineering a Compiler*

*Virtual Machines:*

- Lindholm, T., et al. (2014). *The Java Virtual Machine Specification*
- Nystrom, R. (2021). *Crafting Interpreters*

##### 18.4 Next Steps

To extend this language:

1. *Add features*: Arrays, structs, strings
2. *Improve types*: Polymorphism, type classes
3. *Optimize*: Better stack usage, inlining
4. *Target more platforms*: JVM, WebAssembly, native code
5. *Add tools*: Debugger, profiler, IDE integration

## Appendix A: Quick Reference

### A.1 Type Rules Cheat Sheet

```
Literals:
  Γ ⊢ n : Int32
  Γ ⊢ true : Bool
  Γ ⊢ false : Bool

Variables:
  x: τ ∈ Γ
  ─────────
  Γ ⊢ x : τ

Arithmetic:
  Γ ⊢ e₁ : Int32    Γ ⊢ e₂ : Int32
  ──────────────────────────────────────
  Γ ⊢ e₁ ⊕ e₂ : Int32    (⊕ ∈ {+, -, *})

Comparison:
  Γ ⊢ e₁ : Int32    Γ ⊢ e₂ : Int32
  ───────────────────────────────────────
  Γ ⊢ e₁ ⊙ e₂ : Bool    (⊙ ∈ {<, <=, ==})

Conditional:
  Γ ⊢ c : Bool    Γ ⊢ t : τ    Γ ⊢ f : τ
  ───────────────────────────────────────
  Γ ⊢ if c then t else f : τ

Let:
  Γ ⊢ e₁ : τ₁    Γ, x: τ₁ ⊢ e₂ : τ₂
  ──────────────────────────────────
  Γ ⊢ let x = e₁ in e₂ : τ₂

Function:
  Γ, x: τ₁ ⊢ e : τ₂
  ───────────────────────────────────
  Γ ⊢ fn(x: τ₁) -> τ₂ { e } : τ₁ → τ₂

Application:
  Γ ⊢ f : τ₁ → τ₂    Γ ⊢ e : τ₁
  ──────────────────────────────
  Γ ⊢ f(e) : τ₂
```

### A.2 VM Instruction Reference

See [VM-SPECIFICATION.md](./VM-SPECIFICATION.md) for complete instruction set.

Common patterns:

```
Load constant:
  PUSH_I32 value

Arithmetic:
  [push left]
  [push right]
  ADD_I32 / SUB_I32 / MUL_I32

Comparison:
  [push left]
  [push right]
  LT_I32 / LE_I32 / EQ_I32

Conditional:
  [push condition]
  JUMP_IF_FALSE else_label
  [then code]
  JUMP end_label
  else_label:
  [else code]
  end_label:

Function call:
  [push arg1]
  [push arg2]
  ...
  CALL function arity
```

## Appendix B: Complete Example Program

### B.1 Source Code

```
fn sum_to_n(n: Int32) -> Int32 {
  let rec loop(i: Int32, acc: Int32) -> Int32 =
    if i > n then
      acc
    else
      loop(i + 1, acc + i)
  in
  loop(1, 0)
}

sum_to_n(10)  -- Should return 55
```

### B.2 Type-Checked AST

```
fn sum_to_n : Int32 → Int32
  fn loop : Int32 → Int32 → Int32
    if (>) : Bool
      then acc : Int32
      else loop
        (+) : Int32    -- i + 1
        (+) : Int32    -- acc + i
  loop(1, 0)
```

### B.3 IR

```
sum_to_n:
  t_n = param 0
  jmp loop_entry

loop:
  t_i = param 0
  t_acc = param 1
  
  t_cond = gt t_i, t_n
  br t_cond, L_done, L_continue
  
L_done:
  ret t_acc
  
L_continue:
  t_i_next = add t_i, 1
  t_acc_next = add t_acc, t_i
  t_result = call loop, t_i_next, t_acc_next
  ret t_result

loop_entry:
  t_init_i = 1
  t_init_acc = 0
  t_final = call loop, t_init_i, t_init_acc
  ret t_final

main:
  t_arg = 10
  t_result = call sum_to_n, t_arg
  ret t_result
```

### B.4 Optimized IR

After tail-call optimization:

```
sum_to_n:
  t_n = param 0
  t_i = 1
  t_acc = 0
  
loop:
  t_cond = gt t_i, t_n
  br t_cond, L_done, L_continue
  
L_done:
  ret t_acc
  
L_continue:
  t_i = add t_i, 1
  t_acc = add t_acc, t_i
  jmp loop
```

### B.5 VM Code

```
function sum_to_n:
  ; Locals: [n, i, acc]
  ; Stack depth: 3
  
  ; Initialize i = 1, acc = 0
  PUSH_I32 1
  STORE_LOCAL 1     ; i
  PUSH_I32 0
  STORE_LOCAL 2     ; acc
  
loop:
  ; Check i > n
  LOAD_LOCAL 1      ; i
  LOAD_LOCAL 0      ; n
  GT_I32
  JUMP_IF_TRUE done
  
  ; acc = acc + i
  LOAD_LOCAL 2      ; acc
  LOAD_LOCAL 1      ; i
  ADD_I32
  STORE_LOCAL 2     ; acc = acc + i
  
  ; i = i + 1
  LOAD_LOCAL 1      ; i
  PUSH_I32 1
  ADD_I32
  STORE_LOCAL 1     ; i = i + 1
  
  ; Continue loop
  JUMP loop
  
done:
  LOAD_LOCAL 2      ; Return acc
  RETURN

; Main program
function main:
  PUSH_I32 10
  CALL sum_to_n 1
  ; Result (55) on stack
  RETURN
```

### B.6 Execution Trace

```
Initial: n=10, i=1, acc=0
Iteration 1: i=1, acc=0 → acc = 0+1 = 1,  i = 2
Iteration 2: i=2, acc=1 → acc = 1+2 = 3,  i = 3
Iteration 3: i=3, acc=3 → acc = 3+3 = 6,  i = 4
Iteration 4: i=4, acc=6 → acc = 6+4 = 10, i = 5
Iteration 5: i=5, acc=10 → acc = 10+5 = 15, i = 6
Iteration 6: i=6, acc=15 → acc = 15+6 = 21, i = 7
Iteration 7: i=7, acc=21 → acc = 21+7 = 28, i = 8
Iteration 8: i=8, acc=28 → acc = 28+8 = 36, i = 9
Iteration 9: i=9, acc=36 → acc = 36+9 = 45, i = 10
Iteration 10: i=10, acc=45 → acc = 45+10 = 55, i = 11
Done: i=11 > n=10 → return 55
```
