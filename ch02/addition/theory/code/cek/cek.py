"""
CEK Machine -- call-by-value lambda calculus + integers + booleans + conditionals.

Felleisen & Friedman (1986).  State is a triple <C, E, K>:

  C  Control      -- the expression currently being evaluated
  E  Environment  -- finite map from variable names to values
  K  Kontinuation -- first-class representation of remaining computation

Compared with the SECD machine, the CEK machine collapses the Stack (S)
and Dump (D) into a single first-class Kontinuation (K).  This makes
control operators like call/cc straightforward to add -- capturing the
current continuation is just capturing the current K value.

Derivation note (theory doc, §6.4):
  The CEK machine is obtained from a call-by-value reduction semantics
  by two meaning-preserving transformations:

    1. Replace substitution with environments.
       Instead of beta-reducing (λx. e) v to e[v/x], we extend the
       environment with x ↦ v and continue evaluating e.

    2. Defunctionalise the evaluation context.
       The grammar of evaluation contexts

         E ::= □ | E e | v E | E op e | v op E | if E then e else e

       becomes an algebraic data type -- one constructor per production.
       Each constructor IS a continuation frame; the full K is a list of
       frames, i.e. a composed evaluation context.

  Each transition of the CEK machine implements one step of the
  contextual reduction rule  E[e] → E[e'].

Correspondence table:

  Evaluation context        Continuation constructor
  ─────────────────────     ────────────────────────
  □ e₂  (eval operator)     EvalArg(e₂, env, rest)
  v □   (eval argument)     Apply(v, rest)
  □ op e₂                   OpRight(op, e₂, env, rest)
  v₁ op □                   OpApply(op, v₁, rest)
  if □ then e₂ else e₃      Branch(e₂, e₃, env, rest)
"""

from __future__ import annotations
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Expressions  (abstract syntax of the source language)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Var:
    """Variable reference."""
    name: str
    def __repr__(self): return self.name

@dataclass(frozen=True)
class Lam:
    """Lambda abstraction  λparam. body"""
    param: str
    body: 'Expr'
    def __repr__(self): return f'λ{self.param}. {self.body}'

@dataclass(frozen=True)
class App:
    """Function application  (func arg)"""
    func: 'Expr'
    arg:  'Expr'
    def __repr__(self): return f'({self.func} {self.arg})'

@dataclass(frozen=True)
class Num:
    """Integer literal."""
    val: int
    def __repr__(self): return str(self.val)

@dataclass(frozen=True)
class Bool_:
    """Boolean literal."""
    val: bool
    def __repr__(self): return 'true' if self.val else 'false'

@dataclass(frozen=True)
class BinOp:
    """Binary arithmetic or comparison:  left op right"""
    op:    str
    left:  'Expr'
    right: 'Expr'
    def __repr__(self): return f'({self.left} {self.op} {self.right})'

@dataclass(frozen=True)
class If:
    """Conditional  if cond then then_ else else_"""
    cond:  'Expr'
    then_: 'Expr'
    else_: 'Expr'
    def __repr__(self): return f'if {self.cond} then {self.then_} else {self.else_}'

@dataclass(frozen=True)
class Letrec:
    """
    Recursive binding.

      letrec name = defn in body

    Requires defn to be a Lam (the value restriction for call-by-value
    letrec).  Implemented by creating a cyclic environment: the closure
    for defn holds a reference to an environment that already contains
    name mapped to that same closure.
    """
    name: str
    defn: 'Expr'   # must be a Lam
    body: 'Expr'
    def __repr__(self): return f'letrec {self.name} = {self.defn} in {self.body}'

Expr = Var | Lam | App | Num | Bool_ | BinOp | If | Letrec

# ---------------------------------------------------------------------------
# Values  (closed, fully evaluated results)
# ---------------------------------------------------------------------------

@dataclass
class NumVal:
    n: int
    def __repr__(self): return str(self.n)

@dataclass
class BoolVal:
    b: bool
    def __repr__(self): return 'true' if self.b else 'false'

@dataclass
class Closure:
    """A lambda paired with the environment that was current when it was created."""
    param: str
    body:  Expr
    env:   'Env'
    def __repr__(self): return f'<λ{self.param}. {self.body}>'

Value = NumVal | BoolVal | Closure

def _is_value(x: object) -> bool:
    return isinstance(x, (NumVal, BoolVal, Closure))

# ---------------------------------------------------------------------------
# Environments
# ---------------------------------------------------------------------------

class Env(dict):
    """
    A finite map from variable names to values.
    extend() returns a fresh copy with one additional binding.

    In the letrec case the env is mutated once during construction to
    create a self-referential closure; after that it is treated as
    immutable.
    """
    def extend(self, name: str, val: Value) -> 'Env':
        new = Env(self)
        new[name] = val
        return new

    def __repr__(self):
        if not self:
            return '{}'
        return '{' + ', '.join(f'{k}={v!r}' for k, v in self.items()) + '}'

# ---------------------------------------------------------------------------
# Kontinuations  (defunctionalised evaluation contexts)
# ---------------------------------------------------------------------------

@dataclass
class Done:
    """The empty continuation: the whole expression has been reduced to a value."""
    def __repr__(self): return '•'

@dataclass
class EvalArg:
    """
    Context  □ arg_expr  (evaluating the operator of an application).
    Once the operator is a value, switch to evaluating arg_expr.
    """
    arg_expr: Expr
    env:      Env
    rest:     'Kont'
    def __repr__(self): return f'EvalArg({self.arg_expr!r}) ▷ {self.rest!r}'

@dataclass
class Apply:
    """
    Context  func_val □  (evaluating the argument of an application).
    Once the argument is a value, apply func_val to it.
    """
    func_val: Value
    rest:     'Kont'
    def __repr__(self): return f'Apply({self.func_val!r}) ▷ {self.rest!r}'

@dataclass
class OpRight:
    """
    Context  □ op right_expr  (evaluating the left operand of a binary op).
    Once the left operand is a value, switch to evaluating right_expr.
    """
    op:         str
    right_expr: Expr
    env:        Env
    rest:       'Kont'
    def __repr__(self): return f'OpRight({self.op} {self.right_expr!r}) ▷ {self.rest!r}'

@dataclass
class OpApply:
    """
    Context  left_val op □  (evaluating the right operand of a binary op).
    Once the right operand is a value, compute the result.
    """
    op:       str
    left_val: Value
    rest:     'Kont'
    def __repr__(self): return f'OpApply({self.left_val!r} {self.op}) ▷ {self.rest!r}'

@dataclass
class Branch:
    """
    Context  if □ then then_ else else_  (evaluating the condition).
    Once the condition is a value, select the appropriate branch.
    """
    then_: Expr
    else_: Expr
    env:   Env
    rest:  'Kont'
    def __repr__(self): return f'Branch(if ?) ▷ {self.rest!r}'

Kont = Done | EvalArg | Apply | OpRight | OpApply | Branch

# ---------------------------------------------------------------------------
# Machine state
# ---------------------------------------------------------------------------

@dataclass
class State:
    """
    A CEK state <C, E, K>.

    When ctrl holds an expression, the machine is in 'eval' mode.
    When ctrl holds a value, the machine is in 'return' mode and
    the next transition is determined by the head of the continuation.
    """
    ctrl: 'Expr | Value'
    env:  Env
    kont: Kont

    def is_final(self) -> bool:
        return isinstance(self.kont, Done) and _is_value(self.ctrl)

    def __repr__(self):
        # Show whether the machine is in eval mode (ctrl is an expression)
        # or return mode (ctrl is a value awaiting the continuation).
        # This makes literal-promotion steps (Num 2 → NumVal 2) visible.
        mode = 'return' if _is_value(self.ctrl) else 'eval  '
        return (f'[{mode}] C = {self.ctrl!r}\n'
                f'          E = {self.env!r}\n'
                f'          K = {self.kont!r}')

# ---------------------------------------------------------------------------
# Binary operator table
# ---------------------------------------------------------------------------

_OPS: dict[str, object] = {
    '+':  lambda a, b: NumVal(a.n + b.n),
    '-':  lambda a, b: NumVal(a.n - b.n),
    '*':  lambda a, b: NumVal(a.n * b.n),
    '==': lambda a, b: BoolVal(a.n == b.n),
    '<':  lambda a, b: BoolVal(a.n < b.n),
}

def _apply_op(op: str, lv: Value, rv: Value) -> Value:
    if op not in _OPS:
        raise ValueError(f"Unknown operator: {op!r}")
    if not isinstance(lv, NumVal) or not isinstance(rv, NumVal):
        raise TypeError(f"{op!r} requires numeric operands, got {lv!r} and {rv!r}")
    return _OPS[op](lv, rv)  # type: ignore[operator]

# ---------------------------------------------------------------------------
# The transition function -- one step of the CEK machine
# ---------------------------------------------------------------------------

def step(s: State) -> State:
    c, e, k = s.ctrl, s.env, s.kont

    # ── Eval mode: c is an expression ─────────────────────────────────────

    if isinstance(c, Var):
        # Look up the variable in the environment.
        if c.name not in e:
            raise NameError(f"Unbound variable: {c.name!r}")
        return State(e[c.name], e, k)

    if isinstance(c, Num):
        return State(NumVal(c.val), e, k)

    if isinstance(c, Bool_):
        return State(BoolVal(c.val), e, k)

    if isinstance(c, Lam):
        # A lambda with no free variables relative to the current env
        # is a value: pair it with the env to form a closure.
        return State(Closure(c.param, c.body, e), e, k)

    if isinstance(c, App):
        # Evaluate the operator first; push EvalArg to remember to
        # evaluate the argument and then apply the result.
        return State(c.func, e, EvalArg(c.arg, e, k))

    if isinstance(c, BinOp):
        # Evaluate the left operand first.
        return State(c.left, e, OpRight(c.op, c.right, e, k))

    if isinstance(c, If):
        # Evaluate the condition first.
        return State(c.cond, e, Branch(c.then_, c.else_, e, k))

    if isinstance(c, Letrec):
        # Create a recursive environment by:
        #   1. allocating a fresh env extending the current one,
        #   2. building a closure that references that env,
        #   3. installing the closure into the env under `name`.
        # Step 3 makes the env self-referential, giving the closure
        # access to itself when it later looks up `name`.
        if not isinstance(c.defn, Lam):
            raise ValueError(
                f"letrec definition must be a Lam, got {type(c.defn).__name__}")
        new_env = Env(e)
        clos = Closure(c.defn.param, c.defn.body, new_env)
        new_env[c.name] = clos          # cyclic: clos.env contains clos
        return State(c.body, new_env, k)

    # ── Return mode: c is a value; consult the continuation ───────────────

    if _is_value(c):
        v = c

        if isinstance(k, EvalArg):
            # Operator is done; now evaluate the argument.
            # Push Apply to remember to apply the operator once the
            # argument is a value.
            return State(k.arg_expr, k.env, Apply(v, k.rest))

        if isinstance(k, Apply):
            # Argument is done; apply the function.
            fn = k.func_val
            if not isinstance(fn, Closure):
                raise TypeError(f"Application of non-function: {fn!r}")
            # Beta-reduction via environment extension (no substitution).
            new_env = fn.env.extend(fn.param, v)
            return State(fn.body, new_env, k.rest)

        if isinstance(k, OpRight):
            # Left operand is done; evaluate the right.
            return State(k.right_expr, k.env, OpApply(k.op, v, k.rest))

        if isinstance(k, OpApply):
            # Both operands are values; compute the result.
            return State(_apply_op(k.op, k.left_val, v), e, k.rest)

        if isinstance(k, Branch):
            # Condition is done; select the branch.
            if not isinstance(v, BoolVal):
                raise TypeError(f"Condition must be boolean, got {v!r}")
            branch = k.then_ if v.b else k.else_
            return State(branch, k.env, k.rest)

        if isinstance(k, Done):
            raise RuntimeError("step() called on a final state")

    raise RuntimeError(f"Stuck state: ctrl={c!r}, kont={k!r}")

# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def inject(expr: Expr) -> State:
    """The initial state for evaluating expr: empty environment, empty continuation."""
    return State(expr, Env(), Done())

def run(expr: Expr, debug: bool = False, max_steps: int = 10_000) -> Value:
    """Evaluate expr to a value.  Set debug=True to print each state."""
    s = inject(expr)
    n = 0
    while not s.is_final():
        if debug:
            print(f'  [{n:3d}] {s}')
        s = step(s)
        n += 1
        if n > max_steps:
            raise RuntimeError(f'Exceeded {max_steps} steps')
    if debug:
        print(f'  [{n:3d}] {s}  ← final')
    return s.ctrl

# ---------------------------------------------------------------------------
# Syntactic sugar (not needed by the machine, but useful in examples)
# ---------------------------------------------------------------------------

def let(name: str, defn: Expr, body: Expr) -> App:
    """let x = e₁ in e₂  is sugar for  (λx. e₂) e₁"""
    return App(Lam(name, body), defn)

# ---------------------------------------------------------------------------
# Examples
# ---------------------------------------------------------------------------

def _check(label: str, expr: Expr, expected, debug: bool = False) -> None:
    print(f'\n{"─" * 60}')
    print(f'  {label}')
    if debug:
        print(f'  expr: {expr!r}')
        print()
    result = run(expr, debug=debug)
    ok = (
        (isinstance(result, NumVal)  and result.n == expected) or
        (isinstance(result, BoolVal) and result.b == expected)
    )
    mark = '✓' if ok else '✗'
    print(f'  {mark}  result: {result!r}  (expected {expected})')


if __name__ == '__main__':

    print('CEK Machine -- call-by-value lambda calculus')
    print('Theory of Virtual Machines, §6.2\n')

    # ── 1. Numerals and arithmetic ─────────────────────────────────────────
    #
    # The continuation K grows as we descend into subexpressions, then
    # shrinks as values return.  For  (2 + 3) * 4:
    #
    #   K = •
    #   K = OpRight(* 4) ▷ •          (descend into left of *)
    #   K = OpRight(+ 3) ▷ OpRight(* 4) ▷ •   (descend into left of +)
    #   ...                                     (2 returns, 3 evaluates, + fires)
    #   K = OpRight(* 4) ▷ •           (5 returns)
    #   K = OpApply(5 *) ▷ •           (descend into right of *)
    #   K = •                          (4 returns, * fires → 20)

    _check('(2 + 3) * 4 = 20',
           BinOp('*', BinOp('+', Num(2), Num(3)), Num(4)),
           expected=20)

    # ── 2. Trace of K growing and shrinking ───────────────────────────────

    print(f'\n{"─" * 60}')
    print('  Trace: K grows and shrinks while evaluating (2 + 3) * 4')
    print()
    run(BinOp('*', BinOp('+', Num(2), Num(3)), Num(4)), debug=True)

    # ── 3. Identity function ───────────────────────────────────────────────
    #
    # (λx. x) 7
    #
    # Step sequence:
    #   <App(λx.x, 7), {}, •>
    #   <λx.x, {}, EvalArg(7) ▷ •>        -- push EvalArg
    #   <Closure(x,x,{}), {}, EvalArg(7) ▷ •>
    #   <7, {}, Apply(Closure) ▷ •>        -- switch to evaluating argument
    #   <NumVal(7), {}, Apply(Closure) ▷ •>
    #   <Var x, {x=7}, •>                 -- beta: extend env, pop Apply
    #   <NumVal(7), {x=7}, •>             -- look up x
    #                                     -- final

    _check('Identity  (λx. x) 7 = 7',
           App(Lam('x', Var('x')), Num(7)),
           expected=7)

    # ── 4. Constant function: demonstrates that the argument is discarded ──
    #
    # (λx. λy. x) 1 2

    _check('Constant  (λx. λy. x) 1 2 = 1',
           App(App(Lam('x', Lam('y', Var('x'))), Num(1)), Num(2)),
           expected=1)

    # ── 5. Call-by-value argument evaluation ──────────────────────────────
    #
    # The argument is fully evaluated before the function is applied.
    # Here the argument is  2 * 3, which reduces to 6 before the
    # lambda body  x + 1  is entered.

    _check('Call-by-value order  (λx. x + 1)(2 * 3) = 7',
           App(Lam('x', BinOp('+', Var('x'), Num(1))),
               BinOp('*', Num(2), Num(3))),
           expected=7)

    # ── 6. Conditional ────────────────────────────────────────────────────

    _check('Conditional  if 3 < 5 then 10 else 20 = 10',
           If(BinOp('<', Num(3), Num(5)), Num(10), Num(20)),
           expected=10)

    # ── 7. Higher-order: function composition ─────────────────────────────
    #
    # compose = λf. λg. λx. f (g x)
    # (compose double inc) 5  =  double (inc 5)  =  double 6  =  12
    #
    # The closure for `f` carries the environment {f=double} into the
    # body.  When `g x` is computed, `g` resolves to `inc` from a
    # different environment frame.  This is the standard closure behaviour
    # that makes higher-order functions work without substitution.

    compose = Lam('f', Lam('g', Lam('x',
                  App(Var('f'), App(Var('g'), Var('x'))))))
    double  = Lam('x', BinOp('*', Var('x'), Num(2)))
    inc     = Lam('x', BinOp('+', Var('x'), Num(1)))

    _check('Composition  (double ∘ inc) 5 = 12',
           App(App(App(compose, double), inc), Num(5)),
           expected=12)

    # ── 8. let sugar ──────────────────────────────────────────────────────
    #
    # let x = 3 + 4 in x * x  =  49
    # Desugars to  (λx. x * x)(3 + 4).

    _check('let  (let x = 3 + 4 in x * x) = 49',
           let('x', BinOp('+', Num(3), Num(4)),
               BinOp('*', Var('x'), Var('x'))),
           expected=49)

    # ── 9. Recursion via letrec ───────────────────────────────────────────
    #
    # letrec fact = λn. if n == 0 then 1 else n * fact(n − 1)
    # in fact 6  =  720
    #
    # The recursive call to `fact` inside the body looks up `fact` in
    # the closure's environment.  That environment was made self-referential
    # during Letrec processing: new_env['fact'] = Closure(..., new_env).
    # So each recursive application finds `fact` bound to the same closure.

    fact_body = Lam('n',
        If(BinOp('==', Var('n'), Num(0)),
           Num(1),
           BinOp('*', Var('n'),
                 App(Var('fact'), BinOp('-', Var('n'), Num(1))))))

    _check('Recursion  fact 6 = 720',
           Letrec('fact', fact_body, App(Var('fact'), Num(6))),
           expected=720)

    # ── 10. Mutual closure: church-style boolean ───────────────────────────
    #
    # Church true  = λt. λf. t
    # Church false = λt. λf. f
    # church_if b t e  =  b t e  (just application)
    #
    # This illustrates that K can hold multiple pending applications.

    church_true  = Lam('t', Lam('f', Var('t')))
    church_false = Lam('t', Lam('f', Var('f')))

    # (church_true 10 20) should give 10
    _check('Church true  (λt.λf.t) 10 20 = 10',
           App(App(church_true, Num(10)), Num(20)),
           expected=10)

    # (church_false 10 20) should give 20
    _check('Church false (λt.λf.f) 10 20 = 20',
           App(App(church_false, Num(10)), Num(20)),
           expected=20)

    print(f'\n{"─" * 60}')
    print('  All examples completed.')
