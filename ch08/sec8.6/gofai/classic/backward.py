"""
backward.py -- backward chaining inference engine (goal-directed reasoning).

Contrasts with expert.py (forward chaining): instead of deriving every possible
conclusion from known facts, we start from a goal and work backwards through rules
to the supporting facts. This is goal-directed, top-down reasoning.

This is the operational semantics of Prolog: SLD resolution over Horn clauses.
Each clause is either a fact (empty body) or a rule (head :- body).

Variables follow Prolog convention: uppercase strings, e.g. "X", "Y", "Parent".

prove() is a generator that yields all satisfying substitutions, enabling full
depth-first backtracking: if a chosen resolution path later fails, the prover
retreats and tries the next matching clause. Without this, a query like
ancestor(tom, jim) would fail when the first intermediate binding (bob -> ann)
leads nowhere, missing the correct path (bob -> pat -> jim).
"""

from dataclasses import dataclass, field
from typing import Iterator, Optional


# ---------------------------------------------------------------------------
# Representation
# ---------------------------------------------------------------------------

Atom = tuple[str, ...]
Subst = dict[str, str | tuple]


@dataclass(frozen=True)
class Clause:
    head: Atom
    body: tuple[Atom, ...] = field(default_factory=tuple)

    @staticmethod
    def fact(*args: str) -> "Clause":
        return Clause(head=args)

    @staticmethod
    def rule(head: Atom, *body: Atom) -> "Clause":
        return Clause(head=head, body=body)


def is_var(term: str) -> bool:
    return isinstance(term, str) and term[0].isupper()


def apply_subst(term, subst: Subst):
    if isinstance(term, str):
        if is_var(term) and term in subst:
            return apply_subst(subst[term], subst)
        return term
    return tuple(apply_subst(t, subst) for t in term)


def unify(t1, t2, subst: Subst) -> Optional[Subst]:
    """Return extended substitution unifying t1 and t2, or None on failure."""
    t1 = apply_subst(t1, subst)
    t2 = apply_subst(t2, subst)
    if t1 == t2:
        return subst
    if isinstance(t1, str) and is_var(t1):
        return {**subst, t1: t2}
    if isinstance(t2, str) and is_var(t2):
        return {**subst, t2: t1}
    if isinstance(t1, tuple) and isinstance(t2, tuple) and len(t1) == len(t2):
        for a, b in zip(t1, t2):
            subst = unify(a, b, subst)
            if subst is None:
                return None
        return subst
    return None


# ---------------------------------------------------------------------------
# Inference engine
# ---------------------------------------------------------------------------

_counter = [0]


def _fresh(clause: Clause) -> Clause:
    """Rename all variables with a unique suffix to prevent capture."""
    _counter[0] += 1
    tag = _counter[0]

    def rename(term):
        if isinstance(term, str):
            return f"{term}_{tag}" if is_var(term) else term
        return tuple(rename(t) for t in term)

    return Clause(
        head=rename(clause.head),
        body=tuple(rename(atom) for atom in clause.body),
    )


def prove(goal: Atom, kb: list[Clause],
          subst: Optional[Subst] = None, depth: int = 0) -> Iterator[Subst]:
    """
    Backward chaining generator: yields all substitutions satisfying goal.

    For each clause whose head unifies with the goal, recursively proves
    the clause body. Yields every successful proof, enabling backtracking:
    if a later goal in a conjunction fails, the caller can request the next
    solution here, which tries the next matching clause.
    """
    if subst is None:
        subst = {}
    if depth > 30:
        return

    for clause in kb:
        fresh = _fresh(clause)
        s = unify(goal, fresh.head, subst)
        if s is None:
            continue
        yield from _prove_all(list(fresh.body), kb, s, depth + 1)


def _prove_all(goals: list[Atom], kb: list[Clause],
               subst: Subst, depth: int) -> Iterator[Subst]:
    if not goals:
        yield subst
        return
    for s in prove(goals[0], kb, subst, depth):
        yield from _prove_all(goals[1:], kb, s, depth)


def query(goal: Atom, kb: list[Clause]) -> bool:
    return next(prove(goal, kb), None) is not None


# ---------------------------------------------------------------------------
# Knowledge base: family relationships
# ---------------------------------------------------------------------------

def family_kb() -> list[Clause]:
    """
    parent(Parent, Child) facts plus ancestor rules.

    Family tree:
        tom
       /   \\
     bob   liz
    /   \\
  ann   pat
          \\
          jim
    """
    F = Clause.fact
    R = Clause.rule

    return [
        # Facts
        F("parent", "tom", "bob"),
        F("parent", "tom", "liz"),
        F("parent", "bob", "ann"),
        F("parent", "bob", "pat"),
        F("parent", "pat", "jim"),

        # ancestor(X, Y) :- parent(X, Y).
        R(("ancestor", "X", "Y"),
          ("parent",   "X", "Y")),

        # ancestor(X, Y) :- parent(X, Z), ancestor(Z, Y).
        R(("ancestor", "X", "Y"),
          ("parent",   "X", "Z"),
          ("ancestor", "Z", "Y")),
    ]


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def demo() -> None:
    kb = family_kb()
    print("Backward chaining -- family relationships")
    print()
    print("  Knowledge base:")
    print("    parent(tom, bob)    parent(tom, liz)")
    print("    parent(bob, ann)    parent(bob, pat)    parent(pat, jim)")
    print()
    print("  Rules:")
    print("    ancestor(X, Y) :- parent(X, Y)")
    print("    ancestor(X, Y) :- parent(X, Z), ancestor(Z, Y)")
    print()

    cases = [
        # (description,           goal tuple,                  expected)
        ("parent(tom, bob)     ", ("parent",   "tom", "bob"),  True),
        ("parent(tom, jim)     ", ("parent",   "tom", "jim"),  False),
        ("ancestor(tom, ann)   ", ("ancestor", "tom", "ann"),  True),   # tom->bob->ann
        ("ancestor(tom, jim)   ", ("ancestor", "tom", "jim"),  True),   # tom->bob->pat->jim
        ("ancestor(bob, liz)   ", ("ancestor", "bob", "liz"),  False),  # different branch
        ("ancestor(pat, tom)   ", ("ancestor", "pat", "tom"),  False),  # reversed
    ]

    for label, goal, expected in cases:
        result = query(goal, kb)
        status = "ok" if result == expected else "FAIL"
        print(f"  {label}  -> {str(result):<5}  [{status}]")


if __name__ == "__main__":
    demo()
