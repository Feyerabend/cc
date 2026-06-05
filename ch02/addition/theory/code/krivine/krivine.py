"""
The Krivine Machine
Theory of Virtual Machines, §6.3.

The Krivine machine implements call-by-name evaluation of the untyped
lambda calculus.  Its state is the minimal triple (term, env, stack):

  State = ⟨t,  E,  π⟩

  t  : current term (the "code")
  E  : environment  — maps variables to closures (unevaluated thunks)
  π  : argument stack — each frame is a thunk ⟨t', E'⟩ to be applied later

A thunk ⟨t', E'⟩ is a (term, environment) pair; it is the call-by-name
representation of an unevaluated argument.

─────────────────────────────────────────────────────────────────────────────
Transition rules

  (Var)  ⟨x, E, π⟩      →  ⟨t, E', π⟩       if E(x) = ⟨t, E'⟩

  (App)  ⟨t₁ t₂, E, π⟩  →  ⟨t₁, E, ⟨t₂,E⟩·π⟩   push arg as thunk

  (Lam)  ⟨λx.t, E, ⟨t₀,E₀⟩·π⟩  →  ⟨t, E[x↦⟨t₀,E₀⟩], π⟩  bind and enter body

Terminal states (head normal form):
  ⟨λx.t, E, []⟩   — a lambda with empty stack (no argument to consume)
  ⟨n,    E, []⟩   — a numeral (for the extended language with integers)

─────────────────────────────────────────────────────────────────────────────
Call-by-name vs call-by-value

Under call-by-name, arguments are NEVER evaluated before being passed.
They are wrapped in a thunk and substituted lazily.  This has two
consequences:

  1. An unused argument is never evaluated.
     ⟨(λx.0) Ω, {}, []⟩  →*  ⟨0, …, []⟩   (Ω is pushed as a thunk, then
                                              discarded when the body `0`
                                              ignores x)

  2. A used argument may be evaluated MORE THAN ONCE.
     ⟨(λx. x+x) (2+3), {}, []⟩  — the thunk ⟨2+3⟩ is looked up twice for
                                     the two occurrences of x, so 2+3 is
                                     computed twice.

Call-by-need (Haskell's evaluation strategy) adds memoisation to fix (2)
without losing (1).  The Krivine machine shows call-by-name; adding an
indirection layer (a shared heap cell per thunk) gives call-by-need.

The CEK machine (cek.py) implements call-by-value: the argument (2+3) is
evaluated to 5 exactly once before the lambda body is entered.

─────────────────────────────────────────────────────────────────────────────
Language: call-by-name lambda calculus + integers + booleans + conditionals

  t ::= n | b | x | λx.t | t₁ t₂ | t₁ ⊕ t₂ | if t then t else t
"""

from __future__ import annotations
from dataclasses import dataclass

# ─────────────────────────────────────────────────────────────────────────────
# Terms
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Num:
    n: int
    def __repr__(self) -> str: return str(self.n)

@dataclass(frozen=True)
class Bool_:
    b: bool
    def __repr__(self) -> str: return 'true' if self.b else 'false'

@dataclass(frozen=True)
class Var:
    name: str
    def __repr__(self) -> str: return self.name

@dataclass(frozen=True)
class Lam:
    param: str
    body: 'Term'
    def __repr__(self) -> str: return f'(λ{self.param}. {self.body})'

@dataclass(frozen=True)
class App:
    fun: 'Term'
    arg: 'Term'
    def __repr__(self) -> str: return f'({self.fun} {self.arg})'

@dataclass(frozen=True)
class BinOp:
    op: str
    left: 'Term'
    right: 'Term'
    def __repr__(self) -> str: return f'({self.left} {self.op} {self.right})'

@dataclass(frozen=True)
class If:
    cond: 'Term'
    then_: 'Term'
    else_: 'Term'
    def __repr__(self) -> str:
        return f'(if {self.cond} then {self.then_} else {self.else_})'

Term = Num | Bool_ | Var | Lam | App | BinOp | If

# ─────────────────────────────────────────────────────────────────────────────
# Machine state
# ─────────────────────────────────────────────────────────────────────────────

class Env(dict):
    """Variable-to-thunk mapping.  Subclass of dict for repr."""
    def extend(self, name: str, thunk: 'Thunk') -> 'Env':
        new = Env(self)
        new[name] = thunk
        return new
    def __repr__(self) -> str:
        if not self: return '{}'
        parts = [f'{k}:⟨{v.term}⟩' for k, v in self.items()]
        return '{' + ', '.join(parts) + '}'

@dataclass
class Thunk:
    """
    An unevaluated argument closure: ⟨t, E⟩.
    Represents call-by-name suspension of term t in environment E.
    """
    term: Term
    env: Env
    def __repr__(self) -> str: return f'⟨{self.term}⟩'

@dataclass
class State:
    """Krivine machine state: ⟨term, env, stack⟩."""
    term: Term
    env: Env
    stack: list[Thunk]

    def is_final(self) -> bool:
        return not self.stack and isinstance(self.term, (Lam, Num, Bool_))

    def __repr__(self) -> str:
        π = '[' + ', '.join(repr(t) for t in self.stack) + ']'
        return f'⟨{self.term},  {self.env},  {π}⟩'

# ─────────────────────────────────────────────────────────────────────────────
# Transition function
# ─────────────────────────────────────────────────────────────────────────────

def _arith(op: str, a: int, b: int) -> int:
    return {'+': a + b, '-': a - b, '*': a * b}[op]

def _force_num(t: Term, env: Env, max_steps: int = 10_000) -> int:
    """
    Run the Krivine machine on ⟨t, env, []⟩ until it produces a Num,
    and return the integer.  Used to evaluate arguments of BinOp.

    Under call-by-name, this is 'demanding' the value of a thunk.
    Call-by-need would memoize this result; here we recompute each time.
    """
    s = State(t, env, [])
    for _ in range(max_steps):
        if s.is_final():
            break
        r = step(s)
        if r is None:
            break
        s = r
    if isinstance(s.term, Num):
        return s.term.n
    raise TypeError(f'Expected a number, got {s.term!r}')

def _force_bool(t: Term, env: Env) -> bool:
    """Force a term to a boolean value."""
    s = State(t, env, [])
    for _ in range(10_000):
        if s.is_final():
            break
        r = step(s)
        if r is None:
            break
        s = r
    if isinstance(s.term, Bool_):
        return s.term.b
    raise TypeError(f'Expected a boolean, got {s.term!r}')

def step(s: State) -> State | None:
    """
    One Krivine machine step.  Returns the next state, or None if s is final.

    The three core rules mirror the grammar structure:

      Var  : unfold the thunk stored in the environment
      App  : push the argument as a thunk (do NOT evaluate it)
      Lam  : consume the top thunk from the stack, extend env, enter body

    Extra rules handle the extended language (integers, booleans, if):
      Num/Bool_ + empty stack : final state
      BinOp : force both sub-terms to values, compute, continue
      If    : force the condition, branch
    """
    t, E, π = s.term, s.env, s.stack

    # ── Var: look up in environment ──────────────────────────────────────────
    if isinstance(t, Var):
        if t.name not in E:
            raise NameError(f'Unbound variable: {t.name!r}')
        thunk = E[t.name]
        return State(thunk.term, thunk.env, π)

    # ── App: push argument as thunk, evaluate the function ──────────────────
    if isinstance(t, App):
        new_thunk = Thunk(t.arg, E)
        return State(t.fun, E, [new_thunk] + π)

    # ── Lam + non-empty stack: β-reduction (call-by-name style) ─────────────
    if isinstance(t, Lam):
        if not π:
            return None   # head normal form: nothing to apply
        thunk = π[0]
        new_env = E.extend(t.param, thunk)
        return State(t.body, new_env, π[1:])

    # ── Num / Bool_: already a value ─────────────────────────────────────────
    if isinstance(t, (Num, Bool_)):
        if not π:
            return None   # final state
        raise TypeError(f'Applying a non-function {t!r} to {π[0]!r}')

    # ── BinOp: force both operands, compute result ───────────────────────────
    if isinstance(t, BinOp):
        a = _force_num(t.left,  E)
        b = _force_num(t.right, E)
        return State(Num(_arith(t.op, a, b)), E, π)

    # ── If: force condition, select branch ───────────────────────────────────
    if isinstance(t, If):
        cond = _force_bool(t.cond, E)
        branch = t.then_ if cond else t.else_
        return State(branch, E, π)

    raise RuntimeError(f'Unknown term: {t!r}')

# ─────────────────────────────────────────────────────────────────────────────
# Evaluator and tracer
# ─────────────────────────────────────────────────────────────────────────────

def inject(t: Term) -> State:
    """ι(t) = ⟨t, {}, []⟩ — the initial state."""
    return State(t, Env(), [])

def run(t: Term, debug: bool = False, max_steps: int = 10_000) -> Term:
    """
    Reduce t to head normal form.  Returns the terminal term (Lam or Num).
    With debug=True, prints each state and the rule that fired.
    """
    s = inject(t)
    rules = {Var: 'Var', App: 'App', Lam: 'Lam', Num: 'Num',
             Bool_: 'Bool', BinOp: 'BinOp', If: 'If'}
    for i in range(max_steps):
        if debug:
            rule = rules.get(type(s.term), '?')
            print(f'  {i:>3}  [{rule:<5}]  {s}')
        if s.is_final():
            if debug: print(f'       [Final]  {s.term!r}')
            return s.term
        r = step(s)
        if r is None:
            if debug: print(f'       [Final]  {s.term!r}')
            return s.term
        s = r
    raise RuntimeError(f'Timeout after {max_steps} steps on {t!r}')

# ─────────────────────────────────────────────────────────────────────────────
# Sugar
# ─────────────────────────────────────────────────────────────────────────────

def let(name: str, defn: Term, body: Term) -> Term:
    """let x = defn in body  ≡  (λx. body) defn"""
    return App(Lam(name, body), defn)

# ─────────────────────────────────────────────────────────────────────────────
# Demonstrations
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print('The Krivine Machine — call-by-name lambda calculus')
    print('Theory of Virtual Machines, §6.3')
    print()

    # ── 1. Identity ──────────────────────────────────────────────────────────
    print('── 1. Identity: (λx.x) 7 ──────────────────────────────────────────')
    e = App(Lam('x', Var('x')), Num(7))
    print(f'   {e!r}  →*  ', end='')
    print(run(e, debug=True))

    # ── 2. Constant: (λx.λy.x) 3 Ω — second arg never evaluated ─────────────
    print()
    print('── 2. Constant function: (λx.λy.x) 3 Ω ─────────────────────────────')
    print('   Ω diverges under CBV; under CBN the Krivine machine ignores it.')
    omega_body = App(Var('x'), Var('x'))
    omega = App(Lam('x', omega_body), Lam('x', omega_body))
    e = App(App(Lam('x', Lam('y', Var('x'))), Num(3)), omega)
    print(f'   expression: {e!r}')
    result = run(e, debug=True)
    print(f'   Result: {result!r}  (Ω was pushed as thunk ⟨Ω⟩, then discarded)')

    # ── 3. CBN evaluates arguments multiple times ─────────────────────────────
    print()
    print('── 3. Call-by-name evaluates a shared argument multiple times ────────')
    print('   (λx. x+x) (2+3):')
    print('   Under CBN, the thunk ⟨2+3⟩ is forced twice (once per x).')
    print('   Under CBV (see cek.py), 2+3 would be evaluated once before entry.')
    e = App(Lam('x', BinOp('+', Var('x'), Var('x'))), BinOp('+', Num(2), Num(3)))
    print(f'   expression: {e!r}')
    result = run(e, debug=True)
    print(f'   Result: {result!r}')

    # ── 4. Divergence under CBV, termination under CBN ───────────────────────
    print()
    print('── 4. (λx.0) Ω  →  0  under CBN ────────────────────────────────────')
    print('   Under CBV: evaluate Ω first → loops forever.')
    print('   Under CBN: push ⟨Ω⟩ as thunk; body 0 does not use x → done in 2 steps.')
    e = App(Lam('x', Num(0)), omega)
    print(f'   expression: {e!r}')
    result = run(e, debug=True)
    print(f'   Result: {result!r}')

    # ── 5. Church booleans (call-by-name style) ───────────────────────────────
    print()
    print('── 5. Nested application: (λf.λx. f x) (λy. y+1) 41 ───────────────')
    e = App(
        App(Lam('f', Lam('x', App(Var('f'), Var('x')))),
            Lam('y', BinOp('+', Var('y'), Num(1)))),
        Num(41))
    print(f'   expression: {e!r}')
    result = run(e, debug=True)
    print(f'   Result: {result!r}')

    # ── 6. Summary table ─────────────────────────────────────────────────────
    print()
    print('── 6. Summary: step counts ─────────────────────────────────────────')
    print()
    cases = [
        ('(λx.x) 7',
         App(Lam('x', Var('x')), Num(7))),
        ('(λx.λy.x) 3 42',
         App(App(Lam('x', Lam('y', Var('x'))), Num(3)), Num(42))),
        ('(λx. x+x) (2+3)',
         App(Lam('x', BinOp('+', Var('x'), Var('x'))), BinOp('+', Num(2), Num(3)))),
        ('(λf.λx. f x) (λy. y+1) 41',
         App(App(Lam('f', Lam('x', App(Var('f'), Var('x')))),
                 Lam('y', BinOp('+', Var('y'), Num(1)))),
             Num(41))),
    ]
    print(f'  {"Expression":<40}  {"steps":>5}  {"result"}')
    print('  ' + '─' * 60)
    for label, expr in cases:
        s = inject(expr)
        n = 0
        while not s.is_final():
            r = step(s)
            if r is None: break
            s = r
            n += 1
        print(f'  {label:<40}  {n:>5}  {s.term!r}')
