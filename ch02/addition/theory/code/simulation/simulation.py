"""
Simulation Relations and Compiler Correctness
Theory of Virtual Machines, §9.2–9.3.

This file makes the compiler correctness theorem concrete.

  Theorem 9.3 (Compiler correctness, operational form):
    Let C : E_S → E_T be a compiler, M_S and M_T the abstract machines.
    If there exists a simulation R of M_S by M_T such that
        ⟨ι_S(e),  ι_T(C(e))⟩ ∈ R   for all e ∈ E_S,
    then C is semantically correct: running C(e) on M_T gives the same
    answer as running e on M_S.

We exhibit:
  - M_S : arithmetic small-step evaluator (§5, evaluation contexts)
  - M_T : a simple stack machine
  - C   : standard left-to-right compilation
  - R   : a structural simulation relation on (M_S-state, M_T-state) pairs

─────────────────────────────────────────────────────────────────────────────
Language and machines

Source language:
  e ::= n  |  e₁ ⊕ e₂        (n ∈ ℤ, ⊕ ∈ {+, −, ×})

Source machine M_S — left-to-right small-step via evaluation contexts:
  E ::= □  |  E ⊕ e  |  v ⊕ E
  Rule: E[v₁ ⊕ v₂] →_S E[n]   where n = v₁ ⊕ v₂

Target machine M_T — stack machine:
  States: (stack : list[int],  code : tuple[Instr],  pc : int)
  Instructions: PUSH n  |  ADD  |  SUB  |  MUL

Compiler C : Expr → list[Instr]:
  C(n)         = [PUSH n]
  C(e₁ ⊕ e₂)  = C(e₁) ++ C(e₂) ++ [OP ⊕]

─────────────────────────────────────────────────────────────────────────────
Simulation relation R ⊆ States_S × States_T

  (e, (stack, code, pc)) ∈ R
    iff
  compile_stack(stack) ++ code[pc:] = C(e)

where  compile_stack([v₁,…,vₖ]) = [PUSH v₁,…,PUSH vₖ]
       (v₁ at the stack bottom, vₖ at the top).

Reading: the partial results already on the stack — reconstituted as
PUSH instructions — together with the remaining code, exactly reproduce
C(e).  This is the compiler invariant.

Initial states:  ι_S(e) = e,   ι_T(C(e)) = ([], tuple(C(e)), 0)
  R holds:  compile_stack([]) ++ C(e) = C(e)  ✓

Simulation condition (Def. 9.2, clause 2):
  For every source step e →_S e',
  there exist one or more target steps landing in ts' with (e', ts') ∈ R.
  The target takes exactly len(C(redex)) steps per source step —
  the number of instructions needed to reduce the redex.
─────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations
from dataclasses import dataclass

# ─────────────────────────────────────────────────────────────────────────────
# Source language
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Num:
    n: int
    def __repr__(self) -> str: return str(self.n)

@dataclass(frozen=True)
class BinOp:
    op: str          # '+', '-', '*'
    left: 'Expr'
    right: 'Expr'
    def __repr__(self) -> str: return f'({self.left} {self.op} {self.right})'

Expr = Num | BinOp

def is_val(e: Expr) -> bool:
    return isinstance(e, Num)

def _arith(op: str, a: int, b: int) -> int:
    if op == '+': return a + b
    if op == '-': return a - b
    if op == '*': return a * b
    raise ValueError(f'Unknown op: {op!r}')

# ─────────────────────────────────────────────────────────────────────────────
# Source machine M_S: left-to-right small-step
# ─────────────────────────────────────────────────────────────────────────────

def step_source(e: Expr) -> tuple[Expr, Expr] | None:
    """
    One step of M_S.  Returns (e', redex) with e →_S e', or None if e is a value.

    The redex is the unique sub-expression reduced by the evaluation context.
    Evaluation order: left operand before right (E ⊕ e  before  v ⊕ E).
    """
    if is_val(e):
        return None
    if isinstance(e, BinOp):
        if not is_val(e.left):
            r = step_source(e.left)
            assert r is not None
            new_left, redex = r
            return BinOp(e.op, new_left, e.right), redex
        if not is_val(e.right):
            r = step_source(e.right)
            assert r is not None
            new_right, redex = r
            return BinOp(e.op, e.left, new_right), redex
        # Both operands are values: this BinOp is the redex.
        return Num(_arith(e.op, e.left.n, e.right.n)), e
    raise RuntimeError(f'Stuck: {e!r}')

def reduce_source(e: Expr) -> Num:
    """Reduce e →_S* v, returning the final value."""
    while not is_val(e):
        r = step_source(e)
        assert r is not None
        e, _ = r
    assert isinstance(e, Num)
    return e

# ─────────────────────────────────────────────────────────────────────────────
# Target machine M_T: stack machine
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Push:
    val: int
    def __repr__(self) -> str: return f'PUSH {self.val}'

@dataclass(frozen=True)
class Oper:
    op: str          # '+', '-', '*'
    def __repr__(self) -> str:
        return {'+': 'ADD', '-': 'SUB', '*': 'MUL'}[self.op]

Instr = Push | Oper

def target_step(stack: list[int], code: tuple[Instr, ...], pc: int
                ) -> tuple[list[int], int]:
    """Execute one M_T instruction.  Returns (new_stack, new_pc)."""
    stack = list(stack)   # copy; code and pc are immutable
    instr = code[pc]
    if isinstance(instr, Push):
        stack.append(instr.val)
    elif isinstance(instr, Oper):
        b = stack.pop()
        a = stack.pop()
        stack.append(_arith(instr.op, a, b))
    return stack, pc + 1

def reduce_target(code: tuple[Instr, ...]) -> int:
    """Run M_T from ([], code, 0) to completion; return top of stack."""
    stack: list[int] = []
    pc = 0
    while pc < len(code):
        stack, pc = target_step(stack, code, pc)
    return stack[0]

# ─────────────────────────────────────────────────────────────────────────────
# Compiler C : Expr → list[Instr]
# ─────────────────────────────────────────────────────────────────────────────

def compile(e: Expr) -> list[Instr]:
    """
    C(n)         = [PUSH n]
    C(e₁ ⊕ e₂)  = C(e₁) ++ C(e₂) ++ [OP ⊕]

    Left operand compiled first, matching the source evaluation order.
    """
    if isinstance(e, Num):
        return [Push(e.n)]
    if isinstance(e, BinOp):
        return compile(e.left) + compile(e.right) + [Oper(e.op)]
    raise TypeError(f'Cannot compile: {e!r}')

# ─────────────────────────────────────────────────────────────────────────────
# Simulation relation R
# ─────────────────────────────────────────────────────────────────────────────

def compile_stack(stack: list[int]) -> list[Instr]:
    """
    Reconstruct the stack as PUSH instructions, bottom first.
    compile_stack([v₁,…,vₖ]) = [PUSH v₁,…,PUSH vₖ]
    """
    return [Push(v) for v in stack]

def in_R(e: Expr, stack: list[int], code: tuple[Instr, ...], pc: int) -> bool:
    """
    (e, (stack, code, pc)) ∈ R
      iff
    compile_stack(stack) ++ code[pc:] = C(e)
    """
    return compile_stack(stack) + list(code[pc:]) == compile(e)

# ─────────────────────────────────────────────────────────────────────────────
# Lockstep simulation runner
# ─────────────────────────────────────────────────────────────────────────────

def advance_to_R(e_new: Expr, stack: list[int], code: tuple[Instr, ...], pc: int,
                 max_steps: int = 200) -> tuple[list[int], int, list]:
    """
    Run M_T from (stack, code, pc) until R holds with e_new.
    Returns (new_stack, new_pc, steps_log).

    Each entry in steps_log is (instr, stack_before, stack_after).

    By the simulation theorem, this terminates: the target reaches a
    state in R with e_new after exactly len(C(redex)) ≤ max_steps steps.
    """
    stack = list(stack)
    steps_log: list = []
    for _ in range(max_steps):
        if in_R(e_new, stack, code, pc):
            return stack, pc, steps_log
        assert pc < len(code), (
            f'Target ran off end of code before reaching R with {e_new!r}')
        instr = code[pc]
        old_stack = list(stack)
        stack, pc = target_step(stack, code, pc)
        steps_log.append((instr, old_stack, list(stack)))
    if in_R(e_new, stack, code, pc):
        return stack, pc, steps_log
    raise RuntimeError(
        f'advance_to_R: no state in R with {e_new!r} after {max_steps} steps')

# ─────────────────────────────────────────────────────────────────────────────
# Pretty-printing helpers
# ─────────────────────────────────────────────────────────────────────────────

def _fmt(instrs: list[Instr]) -> str:
    return '[' + ', '.join(repr(i) for i in instrs) + ']'

def _fmt_state(stack: list[int], code: tuple[Instr, ...], pc: int) -> str:
    remaining = list(code[pc:])
    return f'stack={stack}  code[{pc}:]={_fmt(remaining)}'

# ─────────────────────────────────────────────────────────────────────────────
# simulate: the main demonstration function
# ─────────────────────────────────────────────────────────────────────────────

def simulate(e: Expr) -> None:
    """
    Run M_S and M_T in lockstep on expression e, logging the simulation.

    At each source step e →_S e':
      - Find the redex (the subterm that fires).
      - Advance M_T until R holds for (e', new_target_state).
      - Verify R explicitly.

    Demonstrates Definition 9.2 (simulation) concretely:
      ∀ e →_S e',  ∃ ts →_T^+ ts',  (e', ts') ∈ R.
    """
    code: tuple[Instr, ...] = tuple(compile(e))
    stack: list[int] = []
    pc: int = 0

    W = 62
    print()
    print('  ' + '━' * W)
    print(f'  Expression  {e!r}')
    print(f'  Code        {_fmt(list(code))}')
    print()

    # Initial states must be in R (Definition 9.2, clause 1).
    assert in_R(e, stack, code, pc), 'Initial states not in R — compiler bug'
    lhs = compile_stack(stack) + list(code[pc:])
    print(f'  Initial R:  {_fmt(lhs)} = C({e!r})  ✓')
    print()

    step_n = 1
    while not is_val(e):
        r = step_source(e)
        assert r is not None
        e_new, redex = r

        print('  ' + '─' * W)
        print(f'  Source step {step_n}: {e!r}')
        print(f'    →  {e_new!r}     [redex = {redex!r}]')
        print()

        stack_before = list(stack)
        pc_before = pc
        stack, pc, log = advance_to_R(e_new, stack, code, pc)

        print(f'  Target steps ({len(log)} instruction(s)):')
        for instr, s_before, s_after in log:
            print(f'    {repr(instr):<12}  {s_before} → {s_after}')
        if not log:
            print(f'    (no steps needed — R already holds)')

        assert in_R(e_new, stack, code, pc)
        lhs = compile_stack(stack) + list(code[pc:])
        rhs = compile(e_new)
        print()
        print(f'  R holds:')
        print(f'    compile_stack({stack}) ++ code[{pc}:]')
        print(f'    = {_fmt(lhs)}')
        print(f'    = C({e_new!r})  ✓')
        print()

        e = e_new
        step_n += 1

    print('  ' + '─' * W)
    assert isinstance(e, Num) and stack == [e.n]
    print(f'  Final: source = {e!r},  target stack = {stack}  ✓')

# ─────────────────────────────────────────────────────────────────────────────
# Semantic preservation check (Theorem 9.3, consequence)
# ─────────────────────────────────────────────────────────────────────────────

def check_preservation(e: Expr) -> None:
    """
    Verify ⟦C(e)⟧_T = ⟦e⟧_S directly (the conclusion of Theorem 9.3).
    The simulation proof above gives the _reason_ this holds; this is
    just the observable outcome.
    """
    src = reduce_source(e).n
    tgt = reduce_target(tuple(compile(e)))
    status = '✓' if src == tgt else '✗'
    print(f'  {e!r}')
    print(f'    ⟦e⟧_S  = {src}')
    print(f'    ⟦C(e)⟧_T = {tgt}    {status}')
    assert src == tgt, f'Preservation failed for {e!r}'

# ─────────────────────────────────────────────────────────────────────────────
# Demonstrations
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print('Simulation Relations and Compiler Correctness')
    print('Theory of Virtual Machines, §9.2–9.3')

    # ── Example 1: (2+3)*4 ────────────────────────────────────────────────
    # Source reduces left-to-right:  (2+3)*4 → 5*4 → 20
    # Each source step consumes len(C(redex)) target steps.
    simulate(BinOp('*', BinOp('+', Num(2), Num(3)), Num(4)))

    # ── Example 2: (1+2)*(3+4) ────────────────────────────────────────────
    # Three source steps; second step leaves two partial values on the stack.
    simulate(BinOp('*', BinOp('+', Num(1), Num(2)), BinOp('+', Num(3), Num(4))))

    # ── Example 3: ((10-3)*2) - (1+1) ────────────────────────────────────
    # Deeper nesting; R must account for the stack growing across levels.
    simulate(
        BinOp('-',
              BinOp('*', BinOp('-', Num(10), Num(3)), Num(2)),
              BinOp('+', Num(1), Num(1))))

    # ── Semantic preservation summary ─────────────────────────────────────
    print()
    print('  ' + '━' * 62)
    print('  Semantic preservation  ⟦C(e)⟧_T = ⟦e⟧_S  (Theorem 9.3)')
    print()

    tests = [
        BinOp('+', Num(1), Num(2)),
        BinOp('*', BinOp('+', Num(2), Num(3)), Num(4)),
        BinOp('-', BinOp('*', Num(5), Num(5)), BinOp('+', Num(10), Num(5))),
        BinOp('*', BinOp('-', Num(7), Num(3)), BinOp('+', Num(2), Num(1))),
    ]
    for e in tests:
        check_preservation(e)
