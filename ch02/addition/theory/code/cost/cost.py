"""
Cost-Annotated Transition Systems and Resource Budgets
Theory of Virtual Machines, §11 (Resource Semantics).

A plain transition system records only *which* states are reachable.
A cost-annotated system also records *how expensive* each step is.

Definition (Cost-annotated transition system):
  T = ⟨S, s₀, →, W⟩  where W = (W, +, 0) is a cost monoid and
  each transition carries a weight:  s -w→ s'  (w ∈ W).
  Total cost of  s₀ -w₁→ s₁ -w₂→ … -wₙ→ sₙ  is  w₁ + … + wₙ.

Definition (Cost model):
  A cost model κ : Operations → W assigns a weight to each operation.

Definition (Cost-preserving compiler):
  C is cost-preserving w.r.t. κ_S, κ_T and constant c ∈ ℕ if
    cost_T(C(e)) ≤ c · cost_S(e)    for all e.

Definition (Resource budget):
  Budget B ∈ W for a guest: halt when accumulated cost > B.

─────────────────────────────────────────────────────────────────────────────
Machines in this file:

M_S : arithmetic small-step evaluator  (source, same language as simulation.py)
M_T : stack machine                    (target)
C   : left-to-right compiler           (same as simulation.py)

Cost monoids demonstrated:
  Time      = (ℕ, +, 0)        — counts steps
  TimeSpace = (ℕ², +, (0,0))   — counts (steps, max stack depth)

Cost models shown:
  κ_uniform : every M_T instruction costs 1
  κ_ops     : PUSH costs 0, arithmetic op costs 1  (charges only "real work")

Key results:
  Under κ_uniform: cost_T(C(e)) = 2·cost_S(e) + 1  (linear blowup, c = 3)
  Under κ_ops:     cost_T(C(e)) = cost_S(e)          (exact preservation, c = 1)
─────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations
from dataclasses import dataclass

# ─────────────────────────────────────────────────────────────────────────────
# Source language: arithmetic expressions
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Num:
    n: int
    def __repr__(self) -> str: return str(self.n)

@dataclass(frozen=True)
class BinOp:
    op: str
    left:  'Expr'
    right: 'Expr'
    def __repr__(self) -> str: return f'({self.left} {self.op} {self.right})'

Expr = Num | BinOp

def is_val(e: Expr) -> bool: return isinstance(e, Num)

def _arith(op: str, a: int, b: int) -> int:
    return {'+': a + b, '-': a - b, '*': a * b}[op]

def step_source(e: Expr) -> tuple[Expr, Expr] | None:
    """One M_S step.  Returns (e', redex) or None if e is a value."""
    if is_val(e): return None
    if isinstance(e, BinOp):
        if not is_val(e.left):
            r = step_source(e.left);  assert r
            new_left, redex = r
            return BinOp(e.op, new_left, e.right), redex
        if not is_val(e.right):
            r = step_source(e.right);  assert r
            new_right, redex = r
            return BinOp(e.op, e.left, new_right), redex
        return Num(_arith(e.op, e.left.n, e.right.n)), e
    raise RuntimeError(f'Stuck: {e!r}')

# ─────────────────────────────────────────────────────────────────────────────
# Target language: stack machine
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Push:
    val: int
    def __repr__(self) -> str: return f'PUSH {self.val}'

@dataclass(frozen=True)
class Oper:
    op: str
    def __repr__(self) -> str: return {'+': 'ADD', '-': 'SUB', '*': 'MUL'}[self.op]

Instr = Push | Oper

def compile(e: Expr) -> list[Instr]:
    if isinstance(e, Num):  return [Push(e.n)]
    if isinstance(e, BinOp): return compile(e.left) + compile(e.right) + [Oper(e.op)]
    raise TypeError

def target_step(stack: list[int], code: tuple[Instr, ...], pc: int
                ) -> tuple[list[int], int, Instr]:
    """Execute one M_T instruction.  Returns (new_stack, new_pc, instr_executed)."""
    instr = code[pc]
    stack = list(stack)
    if isinstance(instr, Push):
        stack.append(instr.val)
    elif isinstance(instr, Oper):
        b, a = stack.pop(), stack.pop()
        stack.append(_arith(instr.op, a, b))
    return stack, pc + 1, instr

# ─────────────────────────────────────────────────────────────────────────────
# Cost monoids  W = (W, +, 0)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Time:
    """(ℕ, +, 0) — counts transition steps."""
    steps: int = 0
    def __add__(self, other: 'Time | int') -> 'Time':
        n = other.steps if isinstance(other, Time) else other
        return Time(self.steps + n)
    def __le__(self, other: 'Time') -> bool: return self.steps <= other.steps
    def __repr__(self) -> str: return f'{self.steps} step{"s" if self.steps != 1 else ""}'

@dataclass(frozen=True)
class TimeSpace:
    """(ℕ², max-componentwise, (0,0)) — counts (steps, peak stack depth).
    Space dimension uses max rather than sum: live memory = peak occupancy."""
    steps: int = 0
    peak: int  = 0
    def __add__(self, other: 'TimeSpace') -> 'TimeSpace':
        return TimeSpace(self.steps + other.steps, max(self.peak, other.peak))
    def __repr__(self) -> str: return f'({self.steps} steps, depth≤{self.peak})'

# ─────────────────────────────────────────────────────────────────────────────
# Budget enforcement
# ─────────────────────────────────────────────────────────────────────────────

class BudgetExceeded(Exception):
    """
    Raised when accumulated cost exceeds the resource budget B.

    Formally: the machine halts or suspends a guest once cost(g) > B_g.
    In real systems this corresponds to CPU quota exhaustion, OOM kill,
    or I/O rate limiting.
    """
    def __init__(self, used: Time, budget: Time):
        self.used   = used
        self.budget = budget
        super().__init__(f'Budget exceeded: used {used}, budget {budget}')

# ─────────────────────────────────────────────────────────────────────────────
# Generic cost-annotated runner
# ─────────────────────────────────────────────────────────────────────────────

def run_source_with_cost(e: Expr, budget: Time | None = None
                         ) -> tuple[Expr, Time, list]:
    """
    Run M_S on e, annotating each step with cost 1 (uniform κ_S).
    Returns (final_val, total_cost, history).
    history entries: (state, redex, cumulative_cost)
    Raises BudgetExceeded if total > budget.
    """
    cost = Time(0)
    history: list = []
    while not is_val(e):
        r = step_source(e)
        assert r is not None
        e_new, redex = r
        cost = cost + 1
        if budget is not None and not (cost <= budget):
            raise BudgetExceeded(cost, budget)
        history.append((e, redex, cost))
        e = e_new
    return e, cost, history

def run_target_with_cost(code: tuple[Instr, ...],
                         kappa,
                         budget: Time | None = None
                         ) -> tuple[int, Time, list]:
    """
    Run M_T from ([], code, 0), weighting each instruction by κ(instr).
    Returns (result, total_cost, history).
    history entries: (instr, stack_before, stack_after, cumulative_cost)
    Raises BudgetExceeded if total > budget.
    """
    stack: list[int] = []
    pc = 0
    cost = Time(0)
    history: list = []
    while pc < len(code):
        old_stack = list(stack)
        stack, pc, instr = target_step(stack, code, pc)
        step_cost = kappa(instr)
        cost = cost + step_cost
        if budget is not None and not (cost <= budget):
            raise BudgetExceeded(cost, budget)
        history.append((instr, old_stack, list(stack), cost))
    return stack[0], cost, history

def run_target_with_cost_2d(code: tuple[Instr, ...]) -> tuple[int, TimeSpace]:
    """
    Run M_T tracking both time (steps) and space (peak stack depth).
    Every instruction costs 1 time unit; space cost = max len(stack).
    Returns (result, TimeSpace(total_steps, peak_depth)).
    """
    stack: list[int] = []
    pc = 0
    ts = TimeSpace(0, 0)
    while pc < len(code):
        stack, pc, _ = target_step(stack, code, pc)
        ts = ts + TimeSpace(1, len(stack))
    return stack[0], ts

# ─────────────────────────────────────────────────────────────────────────────
# Cost models κ : Instr → ℕ
# ─────────────────────────────────────────────────────────────────────────────

def kappa_uniform(instr: Instr) -> int:
    """Every instruction costs 1.  Models a flat machine where all ops take equal time."""
    return 1

def kappa_ops_only(instr: Instr) -> int:
    """
    PUSH costs 0; arithmetic op costs 1.
    Models a machine where data movement is free and only computation counts.
    Under this model cost_T(C(e)) = cost_S(e): exact cost preservation.
    """
    return 0 if isinstance(instr, Push) else 1

# ─────────────────────────────────────────────────────────────────────────────
# Demonstrations
# ─────────────────────────────────────────────────────────────────────────────

def _fmt(instrs) -> str:
    return '[' + ', '.join(repr(i) for i in instrs) + ']'

def demo_cost_trace(e: Expr) -> None:
    """Print the cost-annotated execution trace for source and target."""
    code = tuple(compile(e))
    print(f'\n  Expression: {e!r}')
    print(f'  Code:       {_fmt(code)}')

    _, src_cost, src_hist = run_source_with_cost(e)
    _, tgt_cost, tgt_hist = run_target_with_cost(code, kappa_uniform)

    print(f'\n  Source (κ_S = 1 per reduction):')
    for state, redex, c in src_hist:
        print(f'    {state!r}  →  [redex {redex!r}]   cumulative: {c}')

    print(f'\n  Target (κ_T = uniform, 1 per instruction):')
    for instr, sb, sa, c in tgt_hist:
        print(f'    {instr!r:<12}  {sb} → {sa}   cumulative: {c}')

    print(f'\n  cost_S = {src_cost},  cost_T (uniform) = {tgt_cost}')


def demo_budget(e: Expr, budget_steps: int) -> None:
    """Show budget enforcement: run target with a tight budget."""
    code = tuple(compile(e))
    budget = Time(budget_steps)
    print(f'\n  Expression: {e!r}')
    print(f'  Code:       {_fmt(code)}')
    print(f'  Budget:     {budget}')
    try:
        result, cost, _ = run_target_with_cost(code, kappa_uniform, budget=budget)
        print(f'  Result:     {result}   (total cost: {cost})  — within budget ✓')
    except BudgetExceeded as ex:
        print(f'  BudgetExceeded: {ex}  — guest halted ✗')


def demo_cost_preservation() -> None:
    """
    Measure cost_S(e) and cost_T(C(e)) for a range of expressions.

    Under κ_uniform:
      cost_T = 2·(#operators) + 1 = 2·cost_S + 1
      → cost_T ≤ 3·cost_S  (c = 3)

    Under κ_ops:
      cost_T = #operators = cost_S
      → cost_T = cost_S  (c = 1, exact preservation)
    """
    exprs = [
        BinOp('+', Num(1), Num(2)),
        BinOp('*', BinOp('+', Num(2), Num(3)), Num(4)),
        BinOp('-', BinOp('*', BinOp('+', Num(1), Num(2)), Num(3)),
                   BinOp('+', Num(4), Num(5))),
        BinOp('+', BinOp('*', Num(2), Num(3)),
                   BinOp('*', BinOp('+', Num(4), Num(5)), Num(6))),
    ]

    W = 66
    print()
    print('  ' + '─' * W)
    print(f'  {"Expression":<34}  {"cS":>4}  {"cT(unif)":>9}  {"ratio":>6}  '
          f'{"cT(ops)":>8}  {"ratio":>6}')
    print('  ' + '─' * W)

    for e in exprs:
        code = tuple(compile(e))
        _, cs, _ = run_source_with_cost(e)
        _, ct_u, _ = run_target_with_cost(code, kappa_uniform)
        _, ct_o, _ = run_target_with_cost(code, kappa_ops_only)
        ratio_u = ct_u.steps / cs.steps
        ratio_o = ct_o.steps / cs.steps if cs.steps > 0 else 0
        label = str(e)[:34]
        print(f'  {label:<34}  {cs.steps:>4}  {ct_u.steps:>9}  {ratio_u:>6.2f}'
              f'  {ct_o.steps:>8}  {ratio_o:>6.2f}')

    print('  ' + '─' * W)
    print('  Under κ_uniform: cost_T ≤ 3·cost_S  (c = 3, constant-factor bound)')
    print('  Under κ_ops:     cost_T = cost_S     (c = 1, exact cost preservation)')


def demo_time_space() -> None:
    """
    Two-dimensional cost: W = ℕ², monoid (ℕ×ℕ, (t+t', max(s,s')), (0,0)).

    Time dimension  = total number of M_T steps executed.
    Space dimension = peak stack depth (live memory at any step).
    """
    exprs = [
        BinOp('+', Num(1), Num(2)),
        BinOp('*', BinOp('+', Num(2), Num(3)), Num(4)),
        BinOp('+', BinOp('*', Num(1), Num(2)),
                   BinOp('*', Num(3), Num(4))),
    ]
    print()
    for e in exprs:
        code = tuple(compile(e))
        result, ts = run_target_with_cost_2d(code)
        print(f'  {e!r}')
        print(f'    code:   {_fmt(code)}')
        print(f'    result: {result}   cost: {ts}')
        print()


if __name__ == '__main__':
    print('Cost-Annotated Transition Systems and Resource Budgets')
    print('Theory of Virtual Machines, §11')

    # ── 1. Cost traces ─────────────────────────────────────────────────────
    print('\n' + '━' * 70)
    print('1. Cost-annotated execution traces')
    demo_cost_trace(BinOp('*', BinOp('+', Num(2), Num(3)), Num(4)))

    # ── 2. Budget enforcement ───────────────────────────────────────────────
    print('\n' + '━' * 70)
    print('2. Resource budgets  (Definition: halt when cost > B)')
    print()

    # 1+2 compiles to [PUSH 1, PUSH 2, ADD] — 3 steps → fits in budget 3
    demo_budget(BinOp('+', Num(1), Num(2)), budget_steps=3)
    # (1+2)*3 compiles to [PUSH 1, PUSH 2, ADD, PUSH 3, MUL] — 5 steps → exceeds budget 3
    demo_budget(BinOp('*', BinOp('+', Num(1), Num(2)), Num(3)), budget_steps=3)
    # same expression with a generous budget 10
    demo_budget(BinOp('*', BinOp('+', Num(1), Num(2)), Num(3)), budget_steps=10)

    # ── 3. Cost-preserving compilation ─────────────────────────────────────
    print('\n' + '━' * 70)
    print('3. Cost-preserving compilation  (Definition: cost_T ≤ c · cost_S)')
    demo_cost_preservation()

    # ── 4. Two-dimensional cost ─────────────────────────────────────────────
    print('\n' + '━' * 70)
    print('4. Two-dimensional cost  W = ℕ²  (time × peak stack depth)')
    print('   Space dimension = live-memory cost (Definition: size of live cells)')
    demo_time_space()
