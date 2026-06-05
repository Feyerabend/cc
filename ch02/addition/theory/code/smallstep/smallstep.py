"""
Small-Step Semantics and Evaluation Contexts
Theory of Virtual Machines, §§2–5.

Language:
  e ::= n | b | e₁ ⊕ e₂ | if e then e₁ else e₂
  ⊕ ∈ {+, -, *, ==, <},  n ∈ ℤ,  b ∈ {true, false}

Three semantic styles for the same language, all shown to agree.

  §2    Abstract syntax     -- inductive set, structural induction
  §3.1  Denotational        ⟦e⟧ : Expr → ℤ ∪ 𝔹   (compositional)
  §3.2  Big-step            e ⇓ v                  (one derivation tree)
  §3.2  Small-step          e → e'                 (single reduction step)
  §3.4  Correspondence      e ⇓ v  ⟺  e →* v,  ⟦e⟧ = ⟦v⟧
  §4    Confluence          Church-Rosser: different orders converge
  §5    Evaluation contexts E[·]   (making the strategy explicit)
        Contextual rule     E[e] → E[e']  if  e → e'  by a base rule
"""

from __future__ import annotations
from dataclasses import dataclass

# ─────────────────────────────────────────────────────────────────────────────
# §2  Abstract syntax  (an inductive set)
# ─────────────────────────────────────────────────────────────────────────────
#
# The grammar  e ::= n | b | e₁ ⊕ e₂ | if e then e₁ else e₂
# defines Expr as the least set closed under the constructors below.
# Structural induction over this set is the principal proof technique.

@dataclass(frozen=True)
class Num:
    """Integer literal.  Also a value."""
    n: int
    def __repr__(self): return str(self.n)

@dataclass(frozen=True)
class Bool_:
    """Boolean literal.  Also a value."""
    b: bool
    def __repr__(self): return 'true' if self.b else 'false'

@dataclass(frozen=True)
class BinOp:
    """Binary operation: +, -, *, ==, <"""
    op:    str
    left:  'Expr'
    right: 'Expr'
    def __repr__(self): return f'({self.left} {self.op} {self.right})'

@dataclass(frozen=True)
class If:
    """Conditional."""
    cond:  'Expr'
    then_: 'Expr'
    else_: 'Expr'
    def __repr__(self): return f'if {self.cond} then {self.then_} else {self.else_}'

Expr = Num | Bool_ | BinOp | If

def is_val(e: Expr) -> bool:
    """Values are the irreducible normal forms: integers and booleans."""
    return isinstance(e, (Num, Bool_))

# ─────────────────────────────────────────────────────────────────────────────
# §3.1  Denotational semantics
# ─────────────────────────────────────────────────────────────────────────────
#
# ⟦·⟧ : Expr → ℤ ∪ 𝔹
#
# The key property: compositionality.  ⟦e⟧ is defined solely in terms of
# ⟦eᵢ⟧ for the immediate subexpressions eᵢ.  No notion of 'step' or
# 'intermediate state' appears.  For a language with recursion, the domain
# D would need to support least fixed points (Scott/Strachey domain theory);
# here, with no recursion, ordinary Python values suffice.

def denote(e: Expr) -> int | bool:
    """⟦e⟧  Compositional interpretation."""
    if isinstance(e, Num):   return e.n
    if isinstance(e, Bool_): return e.b
    if isinstance(e, BinOp):
        lv, rv = denote(e.left), denote(e.right)
        match e.op:
            case '+':  return lv + rv
            case '-':  return lv - rv
            case '*':  return lv * rv
            case '==': return lv == rv
            case '<':  return lv < rv
        raise ValueError(f'Unknown operator: {e.op!r}')
    if isinstance(e, If):
        return denote(e.then_) if denote(e.cond) else denote(e.else_)
    raise TypeError(f'Cannot denote: {e!r}')

# ─────────────────────────────────────────────────────────────────────────────
# §3.2  Big-step operational semantics  (natural semantics)
# ─────────────────────────────────────────────────────────────────────────────
#
# The relation  e ⇓ v  is defined by four inductive rules:
#
#   ─────  (Val)      n ⇓ n,  b ⇓ b
#   v ⇓ v
#
#   e₁ ⇓ n₁   e₂ ⇓ n₂   n₁ ⊕ n₂ = n
#   ────────────────────────────────── (Op)
#          e₁ ⊕ e₂ ⇓ n
#
#   e ⇓ true   e₁ ⇓ v                   e ⇓ false   e₂ ⇓ v
#   ──────────────────── (IfT)           ──────────────────── (IfF)
#   if e then e₁ else e₂ ⇓ v            if e then e₁ else e₂ ⇓ v
#
# Big-step semantics evaluates in one 'big' step to a value.  There is no
# notion of intermediate state: a derivation tree is the proof object.

def big_step(e: Expr) -> Num | Bool_:
    """e ⇓ v  Return the value v that e reduces to."""
    if isinstance(e, (Num, Bool_)):
        return e
    if isinstance(e, BinOp):
        lv = big_step(e.left)
        rv = big_step(e.right)
        return _apply(e.op, lv, rv)
    if isinstance(e, If):
        cv = big_step(e.cond)
        if not isinstance(cv, Bool_):
            raise TypeError(f'Condition must be boolean, got {cv!r}')
        return big_step(e.then_) if cv.b else big_step(e.else_)
    raise TypeError(f'Cannot big-step: {e!r}')

def _apply(op: str, lv: Expr, rv: Expr) -> Num | Bool_:
    if isinstance(lv, Num) and isinstance(rv, Num):
        match op:
            case '+':  return Num(lv.n + rv.n)
            case '-':  return Num(lv.n - rv.n)
            case '*':  return Num(lv.n * rv.n)
            case '==': return Bool_(lv.n == rv.n)
            case '<':  return Bool_(lv.n < rv.n)
    raise TypeError(f'Cannot apply {op!r} to {lv!r} and {rv!r}')

# ─────────────────────────────────────────────────────────────────────────────
# §3.2  Small-step operational semantics  (structural operational semantics)
# ─────────────────────────────────────────────────────────────────────────────
#
# The relation  e → e'  is defined by base rules applied at the outermost
# position.  These are the 'axioms'; congruence rules (applying inside
# subterms) are handled separately by evaluation contexts (§5).
#
# Base rules:
#
#   n₁ ⊕ n₂ = n
#   ─────────────  (β-Op)    where both n₁, n₂ are numeric values
#   n₁ ⊕ n₂ → n
#
#   ────────────────────────────────  (β-IfT)
#   if true then e₁ else e₂ → e₁
#
#   ─────────────────────────────────  (β-IfF)
#   if false then e₁ else e₂ → e₂

def step_base(e: Expr) -> Expr | None:
    """
    Try one base reduction at the top level.
    Returns the reduct, or None if no base rule applies.
    """
    if isinstance(e, BinOp) and is_val(e.left) and is_val(e.right):
        return _apply(e.op, e.left, e.right)
    if isinstance(e, If) and isinstance(e.cond, Bool_):
        return e.then_ if e.cond.b else e.else_
    return None

# ─────────────────────────────────────────────────────────────────────────────
# §5  Evaluation contexts  (making the reduction strategy explicit)
# ─────────────────────────────────────────────────────────────────────────────
#
# Grammar (left-to-right, call-by-value):
#
#   E ::= □                          the hole
#       | E ⊕ e                      evaluate left operand first
#       | v ⊕ E                      left is a value; evaluate right
#       | if E then e₁ else e₂       evaluate condition first
#
# Each production of the grammar becomes one constructor of the Context type.
# The field 'inner' is the sub-context that contains the hole.
#
# The key operations are:
#   plug(E, e)   -- fill the hole: E[e]
#   decompose(e) -- find (redex, E) such that E[redex] = e
#
# The contextual rule then gives a deterministic small-step:
#
#   e → e'  (base rule)
#   ────────────────────  (Context)
#   E[e] → E[e']

@dataclass(frozen=True)
class Hole:
    """□  The hole itself.  plug(Hole, e) = e."""

@dataclass(frozen=True)
class BinLeft:
    """
    E = inner[□] ⊕ right.

    Corresponds to the production  E ⊕ e  in the context grammar:
    the hole is somewhere inside the left operand.
    """
    op:    str
    right: Expr
    inner: 'Context'

@dataclass(frozen=True)
class BinRight:
    """
    E = left_val ⊕ inner[□].

    Corresponds to  v ⊕ E: left is already a value, hole is in the right.
    The left-is-a-value condition enforces left-to-right evaluation order.
    """
    op:       str
    left_val: Expr      # invariant: is_val(left_val)
    inner:    'Context'

@dataclass(frozen=True)
class IfCtx:
    """
    E = if inner[□] then then_ else else_.

    Corresponds to  if E then e else e: hole is in the condition.
    """
    then_: Expr
    else_: Expr
    inner: 'Context'

Context = Hole | BinLeft | BinRight | IfCtx

def show_ctx(ctx: Context) -> str:
    """
    Display a context as an expression with □ marking the hole.
    E.g. BinLeft('*', Num(4), Hole) shows as '(□ * 4)'.
    """
    if isinstance(ctx, Hole):     return '□'
    if isinstance(ctx, BinLeft):  return f'({show_ctx(ctx.inner)} {ctx.op} {ctx.right!r})'
    if isinstance(ctx, BinRight): return f'({ctx.left_val!r} {ctx.op} {show_ctx(ctx.inner)})'
    if isinstance(ctx, IfCtx):    return f'if {show_ctx(ctx.inner)} then {ctx.then_!r} else {ctx.else_!r}'
    raise TypeError(f'Unknown context: {ctx!r}')

def plug(ctx: Context, e: Expr) -> Expr:
    """
    E[e] -- fill the hole in ctx with e.

    Inductive on the context:
      □[e]              = e
      (inner ⊕ right)[e] = inner[e] ⊕ right
      (left ⊕ inner)[e] = left ⊕ inner[e]
      (if inner then t else f)[e] = if inner[e] then t else f
    """
    if isinstance(ctx, Hole):     return e
    if isinstance(ctx, BinLeft):  return BinOp(ctx.op, plug(ctx.inner, e), ctx.right)
    if isinstance(ctx, BinRight): return BinOp(ctx.op, ctx.left_val, plug(ctx.inner, e))
    if isinstance(ctx, IfCtx):    return If(plug(ctx.inner, e), ctx.then_, ctx.else_)
    raise TypeError(f'Unknown context: {ctx!r}')

def decompose(e: Expr) -> tuple[Expr, Context] | None:
    """
    Find the unique redex in e according to the evaluation context grammar.
    Returns (redex, E) such that plug(E, redex) = e.
    Returns None if e is already a value.

    This function *is* the evaluation context grammar: each branch
    corresponds to one production of the grammar.

      E ::= □               → redex = e, ctx = Hole (when e is reducible at top)
          | E ⊕ e           → recurse into left; wrap result in BinLeft
          | v ⊕ E           → left is a value; recurse into right; wrap in BinRight
          | if E then e else e → recurse into cond; wrap in IfCtx
    """
    if is_val(e):
        return None

    if isinstance(e, BinOp):
        if not is_val(e.left):                  # rule: E ⊕ e
            redex, ctx = decompose(e.left)      # type: ignore[misc]
            return redex, BinLeft(e.op, e.right, ctx)
        if not is_val(e.right):                 # rule: v ⊕ E
            redex, ctx = decompose(e.right)     # type: ignore[misc]
            return redex, BinRight(e.op, e.left, ctx)
        return e, Hole()                        # both values: e itself is the redex

    if isinstance(e, If):
        if not is_val(e.cond):                  # rule: if E then e else e
            redex, ctx = decompose(e.cond)      # type: ignore[misc]
            return redex, IfCtx(e.then_, e.else_, ctx)
        return e, Hole()                        # cond is a value: e is the redex

    raise RuntimeError(f'Cannot decompose: {e!r}')

def step(e: Expr) -> Expr | None:
    """
    One deterministic small step, implementing the contextual rule:

      e → e'  (base rule)
      ────────────────────  (Context)
      E[e] → E[e']

    1. Find the unique redex and its context via decompose.
    2. Reduce the redex with step_base.
    3. Plug the reduced term back into the context.
    """
    if is_val(e):
        return None
    redex, ctx = decompose(e)   # type: ignore[misc]
    reduced = step_base(redex)
    if reduced is None:
        raise RuntimeError(f'Redex {redex!r} not reducible by any base rule')
    return plug(ctx, reduced)

def reduce_star(e: Expr, verbose: bool = False) -> list[Expr]:
    """
    e →* v  The complete reduction sequence from e to its normal form.
    Returns [e₀, e₁, ..., v].
    """
    seq = [e]
    if verbose:
        print(f'    {e!r}')
    while not is_val(e):
        e2 = step(e)
        if e2 is None:
            break
        seq.append(e2)
        e = e2
        if verbose:
            print(f'  → {e!r}')
    return seq

# ─────────────────────────────────────────────────────────────────────────────
# §4  Confluence  (Church-Rosser)
# ─────────────────────────────────────────────────────────────────────────────
#
# A transition system is confluent if whenever s →* s₁ and s →* s₂,
# there exists s' such that s₁ →* s' and s₂ →* s'.
#
# For a side-effect-free deterministic language, confluence is trivially
# implied by determinism.  To make it non-trivial, we exhibit a
# non-deterministic reduction relation that can reduce either operand of
# a BinOp first.  The claim is that all paths still converge.

def step_any(e: Expr) -> list[Expr]:
    """
    All possible single-step reducts under an unrestricted (non-deterministic)
    strategy: either operand of a BinOp may be reduced first, regardless of
    whether the other is a value.

    Returns a list of distinct possible next states.
    """
    if is_val(e):
        return []

    results: list[Expr] = []

    if isinstance(e, BinOp):
        if is_val(e.left) and is_val(e.right):
            results.append(_apply(e.op, e.left, e.right))
        for l2 in step_any(e.left):
            results.append(BinOp(e.op, l2, e.right))
        for r2 in step_any(e.right):
            results.append(BinOp(e.op, e.left, r2))

    if isinstance(e, If):
        if isinstance(e.cond, Bool_):
            results.append(e.then_ if e.cond.b else e.else_)
        else:
            for c2 in step_any(e.cond):
                results.append(If(c2, e.then_, e.else_))

    # deduplicate (frozen dataclasses are hashable)
    return list(dict.fromkeys(results))

def normal_form(e: Expr, max_steps: int = 1000) -> Expr:
    """Reduce e to its normal form (deterministically)."""
    for _ in range(max_steps):
        e2 = step(e)
        if e2 is None:
            return e
        e = e2
    raise RuntimeError('max_steps exceeded')

# ─────────────────────────────────────────────────────────────────────────────
# §3.4  Correspondence theorems
# ─────────────────────────────────────────────────────────────────────────────

def check_correspondence(e: Expr) -> None:
    """
    Verify both correspondence theorems for expression e.

    Theorem 1 (big-step / small-step equivalence):
      e ⇓ v  ⟺  e →* v

    Theorem 2 (denotational / big-step agreement):
      ⟦e⟧ = ⟦v⟧  whenever  e ⇓ v

    These guarantee the three semantic styles are views of the same thing.
    """
    v_big   = big_step(e)
    v_small = reduce_star(e)[-1]
    d_expr  = denote(e)
    d_val   = denote(v_big)

    ok1 = (v_big == v_small)
    ok2 = (d_expr == d_val)
    print(f'    expr         {e!r}')
    print(f'    big-step     e ⇓ {v_big!r}')
    print(f'    small-step   e →* {v_small!r}  {"✓" if ok1 else "✗ FAIL"}')
    print(f'    denotational ⟦e⟧ = {d_expr!r},  ⟦v⟧ = {d_val!r}  {"✓" if ok2 else "✗ FAIL"}')


# ─────────────────────────────────────────────────────────────────────────────
# Examples
# ─────────────────────────────────────────────────────────────────────────────

SEP = '─' * 64

if __name__ == '__main__':
    print('Small-Step Semantics and Evaluation Contexts')
    print('Theory of Virtual Machines, §§2–5\n')

    # ── 1. Basic reduction sequence ───────────────────────────────────────
    #
    # (1 + 2) * (3 + 4)
    #
    # The evaluation context grammar forces left-to-right order:
    #   left operand (1+2) is not a value, so it is reduced first.
    #   Once it reaches 3, the right operand (3+4) is tackled.
    #   Finally the top-level * fires.

    print(SEP)
    print('1. Reduction sequence  (1 + 2) * (3 + 4)')
    print('   Left-to-right order enforced by context grammar E ⊕ e | v ⊕ E\n')
    e1 = BinOp('*', BinOp('+', Num(1), Num(2)), BinOp('+', Num(3), Num(4)))
    reduce_star(e1, verbose=True)

    # ── 2. Evaluation context decomposition (visible) ─────────────────────
    #
    # Show decompose() explicitly: the redex and the context E such that
    # E[redex] = e.  Each step is the contextual rule E[redex] → E[redex'].

    print(f'\n{SEP}')
    print('2. Evaluation context decomposition  (§5)')
    print('   decompose(e) = (redex, E)  such that  E[redex] = e\n')
    e2 = BinOp('+', BinOp('*', Num(2), Num(3)), BinOp('-', Num(7), Num(1)))
    current = e2
    step_n = 0
    while not is_val(current):
        redex, ctx = decompose(current)     # type: ignore[misc]
        reduced    = step_base(redex)
        next_e     = plug(ctx, reduced)     # type: ignore[arg-type]
        print(f'    step {step_n}')
        print(f'      e      = {current!r}')
        print(f'      redex  = {redex!r}')
        print(f'      E      = {show_ctx(ctx)}')
        print(f'      E[{reduced!r}] = {next_e!r}')
        current = next_e
        step_n += 1
    print(f'    value  = {current!r}')

    # ── 3. Conditional ────────────────────────────────────────────────────

    print(f'\n{SEP}')
    print('3. Conditional  if (2 < 3) then (10 - 1) else 99\n')
    e3 = If(BinOp('<', Num(2), Num(3)), BinOp('-', Num(10), Num(1)), Num(99))
    reduce_star(e3, verbose=True)

    # ── 4. Correspondence theorems  (§3.4) ───────────────────────────────

    print(f'\n{SEP}')
    print('4. Correspondence theorems  (§3.4)\n')
    print('   Theorem 1: e ⇓ v  ⟺  e →* v')
    print('   Theorem 2: ⟦e⟧ = ⟦v⟧  whenever  e ⇓ v\n')
    for ex in [
        BinOp('+', BinOp('*', Num(2), Num(3)), Num(4)),
        If(BinOp('==', Num(5), Num(5)), BinOp('-', Num(10), Num(3)), Num(99)),
        BinOp('*', BinOp('+', Num(1), Num(2)), BinOp('+', Num(3), Num(4))),
    ]:
        check_correspondence(ex)
        print()

    # ── 5. Confluence  (§4) ───────────────────────────────────────────────
    #
    # The non-deterministic step_any allows reducing either operand first.
    # For  (1 + 2) + (3 + 4), there are two possible first steps:
    #
    #   path A (left first):   3 + (3 + 4) →* 10
    #   path B (right first):  (1 + 2) + 7 →* 10
    #
    # Both converge: Church-Rosser property holds.

    print(SEP)
    print('5. Confluence  (§4 -- Church-Rosser)\n')
    print('   Non-deterministic strategy: either operand may be reduced first.')
    print('   Claim: all one-step reducts converge to the same normal form.\n')

    e5 = BinOp('+', BinOp('+', Num(1), Num(2)), BinOp('+', Num(3), Num(4)))
    first_steps = step_any(e5)
    print(f'    e = {e5!r}')
    print(f'    {len(first_steps)} possible first steps:\n')
    finals: set[Expr] = set()
    for i, e_next in enumerate(first_steps, 1):
        v = normal_form(e_next)
        finals.add(v)
        seq = reduce_star(e_next)
        path = ' → '.join(repr(s) for s in seq)
        print(f'    path {i}: {e5!r}')
        print(f'             → {path}')
    print()
    assert len(finals) == 1, f'Confluence violated: {finals}'
    print(f'    All paths reach {next(iter(finals))!r}  ✓  (Church-Rosser)\n')

    # ── 6. Three styles, one language ────────────────────────────────────
    #
    # Summary: all three semantics agree on every expression.

    print(SEP)
    print('6. Three styles, one language\n')
    print('   For each expression, denotational, big-step, and small-step')
    print('   all compute the same value.\n')
    examples = [
        BinOp('+', Num(1), BinOp('*', Num(2), Num(3))),
        If(BinOp('<', Num(10), Num(5)), Num(0), Num(1)),
        BinOp('*', BinOp('-', Num(8), Num(3)), BinOp('+', Num(1), Num(1))),
    ]
    for ex in examples:
        d  = denote(ex)
        b  = big_step(ex)
        s  = reduce_star(ex)[-1]
        ok = (d == b.n if isinstance(b, Num) else d == b.b) and (b == s)
        print(f'    {ex!r}')
        print(f'      ⟦e⟧ = {d!r},  e ⇓ {b!r},  e →* {s!r}   {"✓" if ok else "✗"}')
        print()

    print(SEP)
    print('All examples completed.')
