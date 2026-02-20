# Designing Programming Languages: From Type Theory to 6502 Assembly

**A Comprehensive Guide to Language Design with Emphasis on Type Systems**

## Part I: Foundations of Language Design

### 1. The Design Philosophy

#### 1.1 What Makes a Good Language?

A well-designed programming language embodies several principles:

- **Clarity**: Semantics should be unambiguous
- **Expressiveness**: Complex ideas in simple terms
- **Safety**: Errors caught early (at compile time when possible)
- **Efficiency**: Predictable performance characteristics
- **Teachability**: Concepts build on each other logically

For educational purposes targeting 6502 assembly, we add:

- **Transparency**: Students see how high-level constructs map to machine code
- **Minimalism**: Small language core exposes compilation fundamentals

#### 1.2 The Role of Type Systems

Type systems serve multiple purposes:

1. **Safety**: Prevent invalid operations at compile time
2. **Documentation**: Types communicate programmer intent
3. **Optimization**: Enable compiler to generate better code
4. **Abstraction**: Allow reasoning about code without running it

For 6502 compilation, types also:

- **Guide register allocation**: Different types have different storage needs
- **Determine calling conventions**: How data flows between functions
- **Enable static analysis**: Detect overflow, size mismatches

### 2. Choosing Your Language Model

#### 2.1 Computation Model

We adopt a **pure, expression-oriented, strict evaluation** model:

```
Computation Style:
- Pure: No mutation, no side effects
- Expression-oriented: Everything returns a value
- Strict: Call-by-value evaluation
```

**Why this model?**

- Referential transparency simplifies reasoning
- Expressions compose naturally
- Strict evaluation has predictable execution order (crucial for 6502)
- Maps cleanly to assembly: evaluate, store, use

#### 2.2 Core Language: A Minimal Calculus

We design a minimal language sufficient for teaching compilation:

```
Types:
τ ::= Int8 -- 8-bit integers (fits in 6502 accumulator)
    | Int16 -- 16-bit integers (common size)
    | Bool -- Boolean values

Expressions:
e ::= n -- Integer literals
    | true -- Boolean true
    | false -- Boolean false
    | x -- Variables
    | e + e -- Addition
    | e - e -- Subtraction
    | e * e -- Multiplication
    | e < e -- Comparison
    | e == e -- Equality
    | if e then e else e -- Conditional
    | let x = e in e -- Local binding
    | fn(x₁: τ₁, ..., xₙ: τₙ) -> τ { e } -- Function definition
    | f(e₁, ..., eₙ) -- Function call
```

This minimal calculus is:

- **Complete**: Can express all computations
- **Simple**: Few constructs to implement
- **Representative**: Shows key compilation challenges

### 3. Formal Semantics

#### 3.1 Why Formalize Semantics?

Formal semantics provide:

- **Precise specification**: No ambiguity about behavior
- **Correctness proofs**: Verify compilation preserves meaning
- **Implementation guide**: Clear rules for interpreter/compiler
- **Testing oracle**: Generate correct test cases

#### 3.2 Big-Step Operational Semantics

Big-step semantics describe evaluation from expression to final value:

$$
e \downarrow v
$$

**Read as**: "Expression e evaluates to value v"

##### Core Rules:

**Literals:**

$$
\frac{}{n \downarrow n}
$$

$$
\frac{}{true \downarrow true}
$$

$$
\frac{}{false \downarrow false}
$$

**Addition:**

$$
\frac{e_1 \downarrow n_1 \quad e_2 \downarrow n_2}{e_1 + e_2 \downarrow n_1 + n_2}
$$

**Conditional (True):**

$$
\frac{c \downarrow true \quad t \downarrow v}{if \ c \ then \ t \ else \ f \downarrow v}
$$

**Conditional (False):**

$$
\frac{c \downarrow false \quad f \downarrow v}{if \ c \ then \ t \ else \ f \downarrow v}
$$

**Let Binding:**

$$
\frac{e_1 \downarrow v_1 \quad e_2[x \mapsto v_1] \downarrow v_2}{let \ x = e_1 \ in \ e_2 \downarrow v_2}
$$

Where `e[x ↦ v]` denotes capture-avoiding substitution.

#### 3.3 Small-Step Operational Semantics

Small-step semantics show individual computation steps:

$$
e \rightarrow e'
$$

**Read as**: "Expression e reduces to e' in one step"

##### Core Reduction Rules:

**Addition (Left):**

$$
\frac{e_1 \rightarrow e_1'}{e_1 + e_2 \rightarrow e_1' + e_2}
$$

**Addition (Right):**

$$
\frac{e_2 \rightarrow e_2'}{v + e_2 \rightarrow v + e_2'}
$$

**Addition (Final):**

$$
\frac{}{n_1 + n_2 \rightarrow n_3}
$$

where n₃ = n₁ + n₂

**Let (Evaluate Binding):**

$$
\frac{e_1 \rightarrow e_1'}{let \ x = e_1 \ in \ e_2 \rightarrow let \ x = e_1' \ in \ e_2}
$$

**Let (Substitute):**

$$
\frac{}{let \ x = v \ in \ e \rightarrow e[x \mapsto v]}
$$

**Conditional (Reduce Condition):**

$$
\frac{c \rightarrow c'}{if \ c \ then \ t \ else \ f \rightarrow if \ c' \ then \ t \ else \ f}
$$

**Conditional (True):**

$$
\frac{}{if \ true \ then \ t \ else \ f \rightarrow t}
$$

**Conditional (False):**

$$
\frac{}{if \ false \ then \ t \ else \ f \rightarrow f}
$$

##### Multi-Step Reduction:

$$
e \rightarrow^* e'
$$

Means: e reduces to e' in zero or more steps.

#### 3.4 Semantic Equivalence

Both semantics should agree:

$$
e \downarrow v \iff e \rightarrow^* v
$$

This equivalence is crucial for correctness:

- Big-step: Shows final result
- Small-step: Shows execution order (important for 6502!)

## Part II: Type System Design

### 4. Type System Foundations

#### 4.1 The Purpose of Types

Types classify values and expressions by their behavior:

```
Int8: Values fitting in one byte (0-255 or -128 to 127)
Int16: Values fitting in two bytes (-32768 to 32767)
Bool: True or false values
```

Types enable:

- **Static verification**: Catch errors before running
- **Memory layout**: Know how much space to allocate
- **Instruction selection**: Choose appropriate 6502 instructions

#### 4.2 Typing Contexts

A typing context tracks variable types:

$$
\Gamma ::= \emptyset \quad | \quad \Gamma, x: \tau
$$

Example:

$$
\Gamma = \{x: Int16, y: Bool, z: Int8\}
$$

#### 4.3 Typing Judgment

The fundamental typing judgment:

$$
\Gamma \vdash e : \tau
$$

**Read as**: "Under context Γ, expression e has type τ"

#### 4.4 Type System Rules

##### Literals:

$$
\frac{}{\Gamma \vdash n : Int16}
$$

(Default: literals are Int16)

$$
\frac{}{\Gamma \vdash true : Bool}
$$

$$
\frac{}{\Gamma \vdash false : Bool}
$$

##### Variables:

$$
\frac{x: \tau \in \Gamma}{\Gamma \vdash x : \tau}
$$

##### Addition:

$$
\frac{\Gamma \vdash e_1 : Int16 \quad \Gamma \vdash e_2 : Int16}{\Gamma \vdash e_1 + e_2 : Int16}
$$

##### Subtraction:

$$
\frac{\Gamma \vdash e_1 : Int16 \quad \Gamma \vdash e_2 : Int16}{\Gamma \vdash e_1 - e_2 : Int16}
$$

##### Comparison:

$$
\frac{\Gamma \vdash e_1 : Int16 \quad \Gamma \vdash e_2 : Int16}{\Gamma \vdash e_1 < e_2 : Bool}
$$

##### Conditional:

$$
\frac{\Gamma \vdash c : Bool \quad \Gamma \vdash t : \tau \quad \Gamma \vdash f : \tau}{\Gamma \vdash if \ c \ then \ t \ else \ f : \tau}
$$

**Key constraint**: Both branches must have the *same type*.

##### Let Binding:

$$
\frac{\Gamma \vdash e_1 : \tau_1 \quad \Gamma, x: \tau_1 \vdash e_2 : \tau_2}{\Gamma \vdash let \ x = e_1 \ in \ e_2 : \tau_2}
$$

##### Function Definition:

$$
\frac{\Gamma, x_1: \tau_1, ..., x_n: \tau_n \vdash e : \tau}{\Gamma \vdash fn(x_1: \tau_1, ..., x_n: \tau_n) -> \tau \{ e \} : \tau_1 \to ... \to \tau_n \to \tau}
$$

##### Function Application:

$$
\frac{\Gamma \vdash f : \tau_1 \to ... \to \tau_n \to \tau \quad \Gamma \vdash e_1 : \tau_1 \quad ... \quad \Gamma \vdash e_n : \tau_n}{\Gamma \vdash f(e_1, ..., e_n) : \tau}
$$

#### 4.5 Type Soundness

The type system is **sound** if:

**Preservation**:

$$
If \ \Gamma \vdash e : \tau \ and \ e \to e', \ then \ \Gamma \vdash e' : \tau
$$

**Progress**:

$$
If \ \emptyset \vdash e : \tau, \ then \ either \ e \ is \ a \ value \ or \ e \to e'
$$

These properties guarantee:

- Well-typed programs don't get stuck
- Evaluation preserves types
- Runtime type errors are impossible

### 5. Type Inference

#### 5.1 Why Type Inference?

Type inference allows omitting type annotations:

```
Instead of: let x: Int16 = 2 + 3 in x - 1
Programmer writes: let x = 2 + 3 in x - 1
```

Benefits:

- Less verbose code
- Flexibility during prototyping
- Types still verified at compile time

#### 5.2 Type Variables

Introduce type variables for unknown types:

```
τ ::= Int8 | Int16 | Bool | α
```

Where α, β, γ are type variables.

#### 5.3 Substitutions

A substitution maps type variables to types:

$$
S = [\alpha \mapsto Int16, \beta \mapsto Bool]
$$

Applying substitution:

$$
S(\alpha) = Int16
$$

$$
S(Int16) = Int16
$$

$$
S(\alpha \to \beta) = Int16 \to Bool
$$

#### 5.4 Unification

Unification finds substitutions making types equal:

```
unify(τ₁, τ₂) = S such that S(τ₁) = S(τ₂)
```

**Examples:**

```
unify(Int16, Int16) = ∅ (already equal)
unify(α, Int16) = [α ↦ Int16]
unify(α, α) = ∅
unify(Int16, Bool) = fail (incompatible)
unify(α → β, Int16 → Bool) = [α ↦ Int16, β ↦ Bool]
```

##### Unification Algorithm:

```
unify(τ₁, τ₂):
  case (τ₁, τ₂):
    (τ, τ) → ∅
    (α, τ) → [α ↦ τ] if α ∉ FV(τ) -- occurs check
    (τ, α) → [α ↦ τ] if α ∉ FV(τ)
    (τ₁ → τ₁', τ₂ → τ₂') →
      S₁ = unify(τ₁, τ₂)
      S₂ = unify(S₁(τ₁'), S₁(τ₂'))
      S₂ ∘ S₁
    _ → fail
```

The **occurs check** prevents infinite types like `α = α → Int16`.

#### 5.5 Inference Algorithm (Hindley-Milner)

The inference judgment:

$$
\Gamma \vdash e \Rightarrow (\tau, S)
$$

**Read as**: "Under Γ, expression e infers type τ with substitution S"

##### Inference Rules:

**Integer Literal:**

$$
\frac{}{\Gamma \vdash n \Rightarrow (Int16, \emptyset)}
$$

**Variable:**

$$
\frac{x: \tau \in \Gamma}{\Gamma \vdash x \Rightarrow (\tau, \emptyset)}
$$

**Addition:**

$$
\frac{\Gamma \vdash e_1 \Rightarrow (\tau_1, S_1) \quad S_1(\Gamma) \vdash e_2 \Rightarrow (\tau_2, S_2) \quad S_3 = unify(S_2(\tau_1), Int16) \quad S_4 = unify(S_3(S_2(\tau_2)), Int16)}{\Gamma \vdash e_1 + e_2 \Rightarrow (Int16, S_4 \circ S_3 \circ S_2 \circ S_1)}
$$

**Conditional:**

$$
\frac{\Gamma \vdash c \Rightarrow (\tau_c, S_1) \quad S_2 = unify(\tau_c, Bool) \quad S_2(S_1(\Gamma)) \vdash t \Rightarrow (\tau_t, S_3) \quad S_3(S_2(S_1(\Gamma))) \vdash f \Rightarrow (\tau_f, S_4) \quad S_5 = unify(S_4(\tau_t), \tau_f)}{\Gamma \vdash if \ c \ then \ t \ else \ f \Rightarrow (S_5(\tau_f), S_5 \circ S_4 \circ S_3 \circ S_2 \circ S_1)}
$$

**Let Binding (with Generalization):**

$$
\frac{\Gamma \vdash e_1 \Rightarrow (\tau_1, S_1) \quad \tau_1' = generalize(S_1(\Gamma), \tau_1) \quad S_1(\Gamma), x: \tau_1' \vdash e_2 \Rightarrow (\tau_2, S_2)}{\Gamma \vdash let \ x = e_1 \ in \ e_2 \Rightarrow (\tau_2, S_2 \circ S_1)}
$$

Where `generalize(Γ, τ)` introduces universal quantification for type variables not in Γ.

#### 5.6 Example: Type Inference in Action

**Program:**

```
let x = 2 + 3 in
if x < 10 then x - 1 else x + 1
```

**Inference Steps:**

1. **Infer `2 + 3`:**

   - `2 ⇒ (Int16, ∅)`

   - `3 ⇒ (Int16, ∅)`

   - `2 + 3 ⇒ (Int16, ∅)`

2. **Bind x:**

   - `x: Int16`

3. **Infer `x < 10`:**

   - `x ⇒ (Int16, ∅)`

   - `10 ⇒ (Int16, ∅)`

   - `x < 10 ⇒ (Bool, ∅)`

4. **Infer then branch `x - 1`:**

   - `x ⇒ (Int16, ∅)`

   - `1 ⇒ (Int16, ∅)`

   - `x - 1 ⇒ (Int16, ∅)`

5. **Infer else branch `x + 1`:**

   - `x + 1 ⇒ (Int16, ∅)`

6. **Unify branches:**

   - `unify(Int16, Int16) = ∅`

7. **Final type:**

   - Entire expression: `Int16`

## Part III: From High-Level to Machine Code

### 6. Intermediate Representation (IR)

#### 6.1 Why an IR?

An Intermediate Representation bridges high-level language and machine code:

**High-level code:**

```
let x = a + b in x - 1
```

**Too abstract** for direct translation to assembly:

- Nested expressions
- Implicit control flow
- Named variables

**IR makes explicit:**

- Evaluation order
- Temporary storage
- Control flow graph

#### 6.2 IR Design

Our IR is a **three-address code** with explicit temporaries:

```
Instruction ::= t = op a, b -- Binary operation
              | t = op a -- Unary operation
              | t = a -- Move/copy
              | br t, L₁, L₂ -- Conditional branch
              | jmp L -- Unconditional jump
              | L: -- Label definition
              | ret t -- Return value
              | call t, f, a₁, ..., aₙ -- Function call

Operand ::= t -- Temporary
          | n -- Literal
          | L -- Label

Operator ::= add | sub | mul -- Arithmetic
           | lt | le | eq -- Comparison
           | neg | not -- Unary
```

#### 6.3 IR Semantics

IR execution uses a **store** mapping temporaries to values:

$$
\sigma : Temp \to Value
$$

##### Operational Semantics:

**Binary Operation:**

$$
\frac{\sigma(a) = v_1 \quad \sigma(b) = v_2 \quad v = op(v_1, v_2)}{(t = op \ a, b, \sigma) \to \sigma[t \mapsto v]}
$$

**Conditional Branch:**

$$
\frac{\sigma(t) = true}{(br \ t, L_1, L_2, \sigma) \to L_1}
$$

$$
\frac{\sigma(t) = false}{(br \ t, L_1, L_2, \sigma) \to L_2}
$$

**Return:**

$$
\frac{\sigma(t) = v}{(ret \ t, \sigma) \downarrow v}
$$

#### 6.4 Example: Lowering to IR

**Source:**

```
let x = 2 + 3 in
if x < 10 then x - 1 else x + 1
```

**IR:**

```
t1 = add 2, 3 ; Compute 2 + 3
t2 = lt t1, 10 ; Test t1 < 10
br t2, L_then, L_else ; Branch on result
L_then:
  t3 = sub t1, 1 ; Compute x - 1
  ret t3 ; Return result
L_else:
  t4 = add t1, 1 ; Compute x + 1
  ret t4 ; Return result
```

**Key transformations:**

- `let x = ...` → temporary `t1`
- Nested conditional → explicit branches and labels
- Each operation → separate instruction

### 7. Lowering: From AST to IR

#### 7.1 Lowering Strategy

Lowering transforms abstract syntax trees to IR through recursive descent:

```
lower : Expr → IR
```

Each expression type has a lowering rule.

#### 7.2 Lowering Rules

### Literals:

```
lower(n) =
  t = fresh_temp()
  emit(t = n)
  return t
```

### Variables:

```
lower(x) =
  return lookup(x) -- Return temporary for x
```

### Binary Operations:

```
lower(e₁ + e₂) =
  t₁ = lower(e₁)
  t₂ = lower(e₂)
  t = fresh_temp()
  emit(t = add t₁, t₂)
  return t
```

### Conditionals:

```
lower(if c then t else f) =
  L_then = fresh_label()
  L_else = fresh_label()
  L_end = fresh_label()
 
  tc = lower(c)
  emit(br tc, L_then, L_else)
 
  emit(L_then:)
  tt = lower(t)
  result = fresh_temp()
  emit(result = tt)
  emit(jmp L_end)
 
  emit(L_else:)
  tf = lower(f)
  emit(result = tf)
  emit(jmp L_end)
 
  emit(L_end:)
  return result
```

### Let Bindings:

```
lower(let x = e₁ in e₂) =
  t₁ = lower(e₁)
  env' = env[x ↦ t₁] -- Bind x to t₁
  with env':
    t₂ = lower(e₂)
  return t₂
```

#### 7.3 Lowering Correctness

**Theorem (Semantic Preservation):**

$$
e \downarrow v \iff lower(e) \downarrow v
$$

**Proof sketch:**

1. By structural induction on e
2. Show each lowering rule preserves semantics
3. Use IR semantics to show equivalence

### 8. Backend: Targeting 6502

#### 8.1 6502 Architecture Overview

The 6502 processor has:

**Registers:**

- `A` (Accumulator): 8-bit, primary arithmetic register
- `X`, `Y` (Index): 8-bit, addressing and loops
- `SP` (Stack Pointer): 8-bit, points to stack (page $01)
- `PC` (Program Counter): 16-bit
- `P` (Status): 8-bit flags (N, V, Z, C, etc.)

**Memory:**

- 64KB address space ($0000-$FFFF)
- Zero page ($0000-$00FF): Fast access
- Stack ($0100-$01FF): Fixed location

**Key constraints:**

- No direct register-to-register operations
- Most operations through accumulator
- 8-bit accumulator (16-bit requires multi-instruction sequences)
- Limited registers (heavy memory use)

#### 8.2 Calling Convention

We define a simple calling convention:

**Arguments:**

- First 2 arguments in zero page ($00-$01 for arg1, $02-$03 for arg2)
- Additional arguments on stack

**Return value:**

- 8-bit: In accumulator (A)
- 16-bit: Low byte in A, high byte in X

**Caller-save:**

- Caller preserves X, Y if needed

**Callee-save:**

- Callee preserves zero page arguments

#### 8.3 Temporary Allocation

IR temporaries map to:

1. **Zero page** ($10-$FF): Fast access, limited space
2. **Stack**: Slower, more space
3. **Registers** (A, X, Y): When possible

**Allocation strategy:**

```
- Hot temporaries → Zero page
- Live range analysis → Register allocation
- Spilled temporaries → Stack
```

#### 8.4 IR to 6502 Translation

##### Binary Addition (Int8):

**IR:**

```
t3 = add t1, t2
```

**6502:**

```assembly
LDA t1 ; Load first operand into A
CLC ; Clear carry flag
ADC t2 ; Add second operand with carry
STA t3 ; Store result
```

##### Binary Addition (Int16):

**IR:**

```
t3 = add t1, t2
```

**6502:**

```assembly
; Add low bytes
LDA t1_lo
CLC
ADC t2_lo
STA t3_lo
; Add high bytes with carry
LDA t1_hi
ADC t2_hi
STA t3_hi
```

##### Subtraction (Int8):

**IR:**

```
t3 = sub t1, t2
```

**6502:**

```assembly
LDA t1 ; Load first operand
SEC ; Set carry (for borrow)
SBC t2 ; Subtract second operand
STA t3 ; Store result
```

##### Comparison (Int8):

**IR:**

```
t2 = lt t1, 10
```

**6502:**

```assembly
LDA t1 ; Load operand
CMP #10 ; Compare with 10
BCC is_less ; Branch if carry clear (less than)
LDA #0 ; False
JMP done
is_less:
LDA #1 ; True
done:
STA t2
```

##### Conditional Branch:

**IR:**

```
br t1, L_then, L_else
```

**6502:**

```assembly
LDA t1 ; Load condition
BEQ L_else ; Branch if zero (false)
JMP L_then ; Jump to then
```

##### Function Call:

**IR:**

```
t3 = call func, t1, t2
```

**6502:**

```assembly
; Pass arguments
LDA t1
STA $00 ; First arg in zero page
LDA t2
STA $01 ; Second arg in zero page
; Call function
JSR func
; Get result
STA t3 ; Result in A
```

#### 8.5 Complete Example

**Source:**

```
let x = 5 in x + 3
```

**IR:**

```
t1 = 5
t2 = add t1, 3
ret t2
```

**6502 Assembly:**

```assembly
; t1 = 5
LDA #5
STA t1
; t2 = add t1, 3
LDA t1
CLC
ADC #3
STA t2
; ret t2
LDA t2
RTS
```

**Memory layout:**

```
$10: t1 (zero page)
$11: t2 (zero page)
```

### 9. Optimization Opportunities

#### 9.1 Peephole Optimization

Replace instruction sequences with more efficient equivalents:

**Constant Folding:**

```
Before:
  LDA #2
  CLC
  ADC #3
  STA t1
After:
  LDA #5
  STA t1
```

**Dead Store Elimination:**

```
Before:
  LDA #5
  STA t1
  LDA #10
  STA t1 ; Previous store is dead
After:
  LDA #10
  STA t1
```

**Redundant Load Elimination:**

```
Before:
  LDA t1
  STA t2
  LDA t1 ; Redundant
After:
  LDA t1
  STA t2
```

#### 9.2 Register Allocation

**Live range analysis:**

- Track where temporaries are live
- Allocate registers to non-overlapping temporaries

**Example:**

```
t1 = 5 ; t1 live: [1-3]
t2 = t1 + 3 ; t2 live: [2-4]
t3 = t2 * 2 ; t3 live: [3-5]
ret t3
```

Both t1 and t3 can share the same register/memory location.

#### 9.3 Strength Reduction

Replace expensive operations with cheaper equivalents:

**Multiply by power of 2:**

```
Before:
  t2 = mul t1, 4
After:
  t2 = t1 << 2 ; Left shift by 2
```

**6502:**

```assembly
; Multiply by 4 using shifts
LDA t1
ASL A ; Shift left (×2)
ASL A ; Shift left (×4)
STA t2
```

## Part IV: Advanced Type System Features

### 10. Polymorphism

#### 10.1 Parametric Polymorphism

Allow functions to work with multiple types:

**Example:**

```
fn identity<T>(x: T) -> T {
  x
}
identity<Int16>(5) -- Returns 5: Int16
identity<Bool>(true) -- Returns true: Bool
```

**Type:**

```
identity : ∀T. T → T
```

**Implementation strategy:**

- **Monomorphization**: Generate separate code for each type
- **Boxing**: Uniform representation (pointer to value)

For 6502 with limited resources, monomorphization is preferred.

#### 10.2 Ad-hoc Polymorphism (Overloading)

Different implementations based on type:

**Example:**

```
fn print(x: Int16) { ... } -- Print integer
fn print(x: Bool) { ... } -- Print boolean
```

**Implementation:**

- Resolve at compile time based on argument types
- Generate separate functions with mangled names

### 11. Algebraic Data Types

#### 11.1 Sum Types (Tagged Unions)

```
type Option<T> = None | Some(T)
type Result<T, E> = Ok(T) | Err(E)
```

**Memory layout for 6502:**

```
Option<Int16>:
  [tag: 1 byte][value: 2 bytes]
 
  tag = 0: None
  tag = 1: Some, value contains Int16
```

#### 11.2 Pattern Matching

```
match opt:
  None -> 0
  Some(x) -> x + 1
```

**Lowering to IR:**

```
t1 = load_tag opt
br_eq t1, 0, L_none, L_some
L_none:
  t_result = 0
  jmp L_end
L_some:
  t2 = load_value opt
  t3 = add t2, 1
  t_result = t3
  jmp L_end
L_end:
  ret t_result
```

**6502 implementation:**

```assembly
; Check tag
LDA opt_tag
BEQ L_none
; Some case
LDA opt_value
CLC
ADC #1
JMP L_end
L_none:
LDA #0
L_end:
; Result in A
```

### 12. Dependent Types (Advanced)

#### 12.1 Introduction

Dependent types allow types to depend on values:

```
Vector<T, n> -- Vector of type T with length n
```

**Example:**

```
fn concat<T, m, n>(v1: Vector<T, m>, v2: Vector<T, n>)
  -> Vector<T, m + n>
```

The return type *depends on* the input lengths.

#### 12.2 Benefits

- Encode invariants in types
- Prove correctness at compile time
- Eliminate runtime checks

**Example:** Array access without bounds checking:

```
fn get<T, n>(arr: Vector<T, n>, i: Nat<i < n>) -> T
```

Type system guarantees `i < n`, so no runtime check needed!

#### 12.3 Implementation Challenges

For 6502 compilation:

- Type checking more complex (may need SMT solvers)
- Runtime representation may need size information
- Monomorphization generates many code variants

**Practical approach:**

- Use dependent types for safety
- Erase to simple types at runtime
- Generate assertions for debugging builds

## Part V: Practical Implementation

### 13. Compiler Pipeline

#### 13.1 Complete Pipeline

```
Source Code
    ↓
Lexer -- Tokenization
    ↓
Parser -- Syntax analysis → AST
    ↓
Type Checker -- Type inference & checking
    ↓
Desugarer -- Simplify syntax
    ↓
Lowering -- AST → IR
    ↓
Optimizer -- IR transformations
    ↓
Backend -- IR → 6502 assembly
    ↓
Assembler -- Assembly → Machine code
    ↓
Machine Code
```

#### 13.2 Worked Example: Full Compilation

##### Input Program:

```
fn factorial(n: Int16) -> Int16 {
  if n <= 1 then
    1
  else
    n * factorial(n - 1)
}
factorial(5)
```

##### Step 1: Type Checking

```
factorial: Int16 → Int16
Type checking factorial:
  Γ = {n: Int16}
 
  Check condition: n <= 1
    Γ ⊢ n : Int16 ✓
    Γ ⊢ 1 : Int16 ✓
    Γ ⊢ n <= 1 : Bool ✓
 
  Check then branch: 1
    Γ ⊢ 1 : Int16 ✓
 
  Check else branch: n * factorial(n - 1)
    Γ ⊢ n : Int16 ✓
    Γ ⊢ n - 1 : Int16 ✓
    Γ ⊢ factorial(n - 1) : Int16 ✓
    Γ ⊢ n * factorial(n - 1) : Int16 ✓
 
  Both branches: Int16 ✓
 
Result: Well-typed ✓
```

##### Step 2: Lowering to IR

```
factorial:
  t1 = param 0 ; Get argument n
  t2 = le t1, 1 ; n <= 1
  br t2, L_base, L_recursive
L_base:
  t3 = 1
  ret t3
L_recursive:
  t4 = sub t1, 1 ; n - 1
  t5 = call factorial, t4 ; factorial(n - 1)
  t6 = mul t1, t5 ; n * factorial(n - 1)
  ret t6
main:
  t10 = 5
  t11 = call factorial, t10
  ret t11
```

##### Step 3: 6502 Code Generation

```assembly
; factorial function
factorial:
    ; Save argument to zero page
    STA $10 ; n in $10
   
    ; Check n <= 1
    LDA $10
    CMP #2 ; Compare with 2
    BCS recursive ; Branch if >= 2
   
base_case:
    LDA #1
    RTS
   
recursive:
    ; Compute n - 1
    LDA $10
    SEC
    SBC #1
   
    ; Recursive call
    JSR factorial ; Result in A
   
    ; Multiply n * result
    STA $11 ; Save factorial(n-1)
    LDA $10 ; Load n
    JSR multiply ; n * $11 → A
   
    RTS
; Multiply routine (A * $11 → A)
multiply:
    LDX #8 ; 8-bit multiply
    LDY #0 ; Result accumulator
mul_loop:
    LSR A ; Shift multiplier right
    BCC mul_skip ; Skip if bit is 0
    TYA
    CLC
    ADC $11
    TAY
mul_skip:
    ASL $11 ; Shift multiplicand left
    DEX
    BNE mul_loop
    TYA ; Move result to A
    RTS
; Main program
main:
    LDA #5 ; Argument
    JSR factorial ; Call factorial(5)
    ; Result (120) in A
```

#### 13.3 Testing the Compiler

##### Unit Tests:

```
Test Type Inference:
  Input: "let x = 5 in x + 3"
  Expected: Int16
 
Test Lowering:
  Input: "if true then 1 else 2"
  Expected IR:
    br true, L1, L2
    L1: ret 1
    L2: ret 2
```

##### Integration Tests:

```
Test Complete Compilation:
  Input: factorial(5)
  Expected: 120
 
  Method:
    1. Compile to 6502
    2. Run in emulator
    3. Check result
```

##### Property-Based Tests:

```
Property: Type Preservation
  ∀ expression e:
    if e is well-typed,
    then lower(e) has equivalent semantics
   
Property: Optimization Correctness
  ∀ IR program p:
    optimize(p) produces same result as p
```

### 14. Error Handling

#### 14.1 Type Errors

Clear error messages are crucial:

**Bad:**

```
Error: Type mismatch
```

**Good:**

```
Error: Type mismatch in conditional
  at line 3, column 5:
    if x then 1 else false
       ^
  Expected: Bool
  Got: Int16
 
  Note: The condition of 'if' must be a boolean expression
```

#### 14.2 Error Recovery

Continue type checking after errors to find more issues:

```
Technique: Substitute error type
  When e has type error, continue with fresh type variable α
 
Example:
  Input: if x then 1 else false
 
  After error in condition:
    Assume x: Bool (error recovery)
    Continue to find error in branches (Int16 vs Bool)
```

## Part VI: Extensions and Future Directions

### 15. Memory Management

#### 15.1 Stack Allocation

Simple but limited:

```
fn example() -> Int16 {
  let x = 10 in ; x on stack
  let y = x + 5 in ; y on stack
  y * 2
}
```

**6502 implementation:**

```assembly
; Allocate stack space
TSX
DEX
STX $100,X ; Push x
DEX
STX $100,X ; Push y
; Compute...
; Deallocate
INX
INX
```

#### 15.2 Region-Based Memory Management

Group allocations by lifetime:

```
region r {
  let x = allocate_in_region<Int16>(r)
  ...
} -- All allocations in r freed here
```

**Advantages:**

- Predictable performance
- No garbage collection overhead
- Suitable for embedded systems (6502)

#### 15.3 Linear Types

Enforce single ownership:

```
type Buffer = linear [Int8; 256]
fn use_buffer(b: Buffer) {
  // b must be used exactly once
  // Cannot be copied or dropped
}
```

**Implementation:**

- Track usage at compile time
- Ensure no aliasing
- No runtime overhead

### 16. Concurrency

#### 16.1 Cooperative Multitasking

For 6502 without OS:

```
type Task = () -> Bool -- Returns true if done
scheduler : [Task] -> ()
```

**Implementation:**

```assembly
scheduler:
    LDX #0 ; Task index
loop:
    JSR task_table,X ; Call task
    BEQ task_done ; If done, remove
    INX
    CPX task_count
    BNE loop
    JMP loop
   
task_done:
    ; Remove task from list
    ...
```

### 17. Conclusion

#### 17.1 What We've Built

A complete language design including:

1. **Formal semantics**: Big-step and small-step
2. **Type system**: With inference and soundness
3. **Compilation pipeline**: From source to 6502
4. **IR**: Three-address code for optimization
5. **Backend**: Efficient 6502 code generation

#### 17.2 Key Lessons

**Type systems:**

- Catch errors early
- Guide compilation
- Enable optimization

**IRs:**

- Separate concerns
- Enable multiple backends
- Facilitate optimization

**6502 target:**

- Forces understanding of constraints
- Shows compilation challenges
- Excellent teaching platform

#### 17.3 Further Reading

**Type theory:**

- Pierce, B. C. (2002). *Types and Programming Languages*
- Harper, R. (2016). *Practical Foundations for Programming Languages*

**Compilation:**

- Appel, A. W. (1998). *Modern Compiler Implementation in ML*
- Cooper, K. D., & Torczon, L. (2011). *Engineering a Compiler*

**6502:**

- Leventhal, L. A. (1979). *6502 Assembly Language Programming*
- The MOS 6502 Manual

#### 17.4 Next Steps

To extend this language:

1. **Add features**: Arrays, structs, strings
2. **Improve types**: Polymorphism, type classes
3. **Optimize**: Better register allocation, inlining
4. **Target more architectures**: x86, ARM, RISC-V
5. **Add tools**: Debugger, profiler, IDE integration

# Appendix A: Quick Reference

## A.1 Type Rules Cheat Sheet

```
Literals:
  Γ ⊢ n : Int16
  Γ ⊢ true : Bool
  Γ ⊢ false : Bool
Variables:
  x: τ ∈ Γ
  ──────────
  Γ ⊢ x : τ
Arithmetic:
  Γ ⊢ e₁ : Int16 Γ ⊢ e₂ : Int16
  ─────────────────────────────────
  Γ ⊢ e₁ ⊕ e₂ : Int16 (⊕ ∈ {+, -, *})
Comparison:
  Γ ⊢ e₁ : Int16 Γ ⊢ e₂ : Int16
  ─────────────────────────────────
  Γ ⊢ e₁ ⊙ e₂ : Bool (⊙ ∈ {<, <=, ==})
Conditional:
  Γ ⊢ c : Bool Γ ⊢ t : τ Γ ⊢ f : τ
  ────────────────────────────────────────
  Γ ⊢ if c then t else f : τ
Let:
  Γ ⊢ e₁ : τ₁ Γ, x: τ₁ ⊢ e₂ : τ₂
  ────────────────────────────────────
  Γ ⊢ let x = e₁ in e₂ : τ₂
Function:
  Γ, x: τ₁ ⊢ e : τ₂
  ─────────────────────────────────
  Γ ⊢ fn(x: τ₁) -> τ₂ { e } : τ₁ → τ₂
Application:
  Γ ⊢ f : τ₁ → τ₂ Γ ⊢ e : τ₁
  ──────────────────────────────
  Γ ⊢ f(e) : τ₂
```

## A.2 6502 Instruction Reference

```
Load/Store:
  LDA #n Load immediate
  LDA addr Load from memory
  STA addr Store to memory
  LDX #n Load X register
  LDY #n Load Y register
Arithmetic:
  CLC Clear carry
  ADC #n Add with carry
  SEC Set carry
  SBC #n Subtract with carry
Comparison:
  CMP #n Compare accumulator
  CPX #n Compare X
  CPY #n Compare Y
Branches:
  BEQ label Branch if equal (Z=1)
  BNE label Branch if not equal (Z=0)
  BCC label Branch if carry clear
  BCS label Branch if carry set
  BMI label Branch if minus (N=1)
  BPL label Branch if plus (N=0)
Jumps:
  JMP label Unconditional jump
  JSR label Jump to subroutine
  RTS Return from subroutine
Stack:
  PHA Push accumulator
  PLA Pull accumulator
  PHP Push status
  PLP Pull status
Shifts:
  ASL A Arithmetic shift left
  LSR A Logical shift right
  ROL A Rotate left through carry
  ROR A Rotate right through carry
```

## A.3 Common Patterns

### 16-bit Addition:

```assembly
; Add (addr1) + (addr2) -> (result)
LDA addr1_lo
CLC
ADC addr2_lo
STA result_lo
LDA addr1_hi
ADC addr2_hi
STA result_hi
```

### 16-bit Comparison:

```assembly
; Compare (addr1) < (addr2)
LDA addr1_hi
CMP addr2_hi
BCC less_than ; High byte less
BNE not_less ; High bytes differ
; High bytes equal, check low
LDA addr1_lo
CMP addr2_lo
BCC less_than
not_less:
; addr1 >= addr2
JMP done
less_than:
; addr1 < addr2
```

### Loop:

```assembly
; for i = 0 to n-1
LDX #0
loop:
; Loop body here
INX
CPX #n
BNE loop
```

# Appendix B: Complete Example Program

## B.1 Source Code

```
fn sum_to_n(n: Int16) -> Int16 {
  let rec loop(i: Int16, acc: Int16) -> Int16 =
    if i > n then
      acc
    else
      loop(i + 1, acc + i)
  in
  loop(1, 0)
}
sum_to_n(10) -- Should return 55
```

## B.2 Type-Checked AST

```
fn sum_to_n : Int16 → Int16
  fn loop : Int16 → Int16 → Int16
    if (>) : Bool
      then acc : Int16
      else loop
        (+) : Int16 -- i + 1
        (+) : Int16 -- acc + i
  loop(1, 0)
```

## B.3 IR

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

## B.4 Optimized IR

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

## B.5 6502 Assembly

```assembly
; sum_to_n(n) -> sum from 1 to n
sum_to_n:
    ; n in A
    STA $10 ; Store n
   
    ; Initialize i = 1, acc = 0
    LDA #1
    STA $11 ; i
    LDA #0
    STA $12 ; acc
   
loop:
    ; Check i > n
    LDA $11
    CMP $10
    BEQ done ; i == n, done
    BCS done ; i > n, done
   
    ; acc = acc + i
    LDA $12
    CLC
    ADC $11
    STA $12
   
    ; i = i + 1
    INC $11
   
    ; Continue loop
    JMP loop
   
done:
    LDA $12 ; Return acc
    RTS
; Main program
main:
    LDA #10
    JSR sum_to_n
    ; Result (55) in A
```

## B.6 Execution Trace

```
Iteration 1: i=1, acc=0 → acc = 0+1 = 1
Iteration 2: i=2, acc=1 → acc = 1+2 = 3
Iteration 3: i=3, acc=3 → acc = 3+3 = 6
Iteration 4: i=4, acc=6 → acc = 6+4 = 10
Iteration 5: i=5, acc=10 → acc = 10+5 = 15
Iteration 6: i=6, acc=15 → acc = 15+6 = 21
Iteration 7: i=7, acc=21 → acc = 21+7 = 28
Iteration 8: i=8, acc=28 → acc = 28+8 = 36
Iteration 9: i=9, acc=36 → acc = 36+9 = 45
Iteration 10: i=10, acc=45 → acc = 45+10 = 55
Done: i=11, n=10 → return 55
```