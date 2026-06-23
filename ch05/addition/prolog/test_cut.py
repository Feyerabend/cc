"""
Test suite for sprolog's cut (!) and variable handling.

Run:  python3 test_cut.py        (exits non-zero on any failure)

These tests pin down the semantics the cut fix is meant to provide:
  * backtracking without cut still enumerates all solutions;
  * a cut commits to the current clause — pruning the goals to its left, the
    remaining clauses of the predicate, AND the choice points of any rule called
    to its left (the case that was broken: a cut inside a called rule);
  * goals to the RIGHT of a cut still backtrack normally;
  * a cut at the top level of a query commits against the query;
  * query variables never collide with rule variables (the id-collision fix),
    for any variable name.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sprolog import PrologInterpreter, PrologParser   # noqa: E402

FAMILY = '''
    parent(john, bob).
    parent(bob, ann).
    parent(john, carol).
    parent(carol, dave).
    grandparent(X, Y) :- parent(X, Z), parent(Z, Y).
    first_gp(X, Y) :- grandparent(X, Y), !.
'''

# sprolog parses numeric literals as floats, so number bindings print as "1.0";
# the choice/cut tests use atoms (a, b, c) to keep expectations obvious, and the
# max test (which needs arithmetic) checks the float forms.
NUMS = '''
    p(a).
    p(b).
    p(c).
    q(X) :- p(X), !.
    after_cut(X, Y) :- p(X), !, p(Y).
    r(X) :- p(X), !.
    r(zzz).
    max(X, Y, X) :- X >= Y, !.
    max(X, Y, Y) :- X < Y.
'''


SIBLINGS = r'''
    parent(bob, alice).
    parent(bob, charlie).
    sibling(X, Y) :- parent(P, X), parent(P, Y), X \= Y.
'''


def interp(rules):
    p = PrologInterpreter()
    p.add_rules(rules)
    return p


def sols(p, q):
    """Ordered list of the single query variable's bindings (as strings)."""
    return [str(v) for s in p.query(q) for v in s.values()]


def pairs(p, q):
    return [tuple(str(v) for v in s.values()) for s in p.query(q)]


TESTS = []


def test(fn):
    TESTS.append(fn)
    return fn


@test
def t_backtracking_no_cut():
    assert sols(interp(NUMS), "p(X)") == ["a", "b", "c"]


@test
def t_cut_commits_first_solution():
    assert sols(interp(NUMS), "q(X)") == ["a"]


@test
def t_cut_prunes_sibling_clause():
    # the cut in r's first clause must also discard the alternative clause r(99)
    assert sols(interp(NUMS), "r(X)") == ["a"]


@test
def t_cut_through_called_rule():
    # the case that was broken: cut after a called rule prunes that rule's
    # remaining choice points (carol/dave), committing to the first grandparent
    p = interp(FAMILY)
    assert sols(p, "grandparent(john, W)") == ["ann", "dave"]   # no cut: both
    assert sols(p, "first_gp(john, W)") == ["ann"]              # cut: first only


@test
def t_goals_after_cut_still_backtrack():
    # after_cut(X, Y) :- p(X), !, p(Y).  Cut fixes X=1 but Y still ranges over all
    assert pairs(interp(NUMS), "after_cut(X, Y)") == [
        ("a", "a"), ("a", "b"), ("a", "c")]


@test
def t_query_level_cut():
    assert sols(interp(NUMS), "p(X), !") == ["a"]


@test
def t_max_uses_cut():
    p = interp(NUMS)
    assert sols(p, "max(5, 3, M)") == ["5.0"]
    assert sols(p, "max(3, 5, M)") == ["5.0"]
    assert sols(p, "max(4, 4, M)") == ["4.0"]   # exactly one solution, not two


@test
def t_query_variable_names_independent():
    # the id-collision fix: every query variable name must work from a fresh DB
    for v in ["W", "X", "Y", "Z", "Q", "Who", "Result"]:
        p = interp(FAMILY)
        assert sols(p, f"grandparent(john, {v})") == ["ann", "dave"], v


@test
def t_not_equal_builtin():
    p = interp("dummy(x).")
    assert len(list(p.query(r"a \= b"))) == 1     # distinct atoms: succeeds
    assert len(list(p.query(r"a \= a"))) == 0     # same atom: fails


@test
def t_fresh_variables_are_distinct():
    # Object-identity refactor: two independently parsed `X` are different
    # variables (standardizing apart, by construction). Within one parse, the
    # same name is the same variable.
    p1 = PrologParser(); p1.parse_goals("foo(X, X)")
    p2 = PrologParser(); p2.parse_goals("foo(X)")
    x1 = p1.variables["X"]
    x2 = p2.variables["X"]
    assert x1 is not x2 and x1 != x2          # distinct across parses
    assert hash(x1) != hash(x2)
    # ...but the two X's inside foo(X, X) are the SAME variable
    assert p1.variables["X"] is x1


@test
def t_sibling_uses_not_equal():
    # \= excludes self-siblinghood; this only works once query variables no longer
    # collide with the rule's X/Y/P (the variable-id fix).
    p = interp(SIBLINGS)
    assert sols(p, "sibling(alice, X)") == ["charlie"]      # not alice herself
    assert pairs(p, "sibling(X, Y)") == [
        ("alice", "charlie"), ("charlie", "alice")]


if __name__ == "__main__":
    passed = 0
    for t in TESTS:
        try:
            t()
            print(f"  ok    {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}  {e!r}")
    print(f"\n{passed}/{len(TESTS)} passed")
    sys.exit(0 if passed == len(TESTS) else 1)
