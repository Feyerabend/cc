"""
Test suite for mprolog's cut (!) — the cut added to the iterative, explicit-stack
solver. Run:  python3 test_mprolog_cut.py   (exits non-zero on any failure)

mprolog implements cut by tagging each clause body's '!' with the choice-point
stack height at which the clause was selected (a barrier), and truncating the
stack back to that height when the cut fires. This prunes the clause's
next-clause choice point and the choice points of its earlier body goals —
including those created inside a called rule — exactly like sprolog's cut, but in
the list-collecting iterative engine.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mprolog as M   # noqa: E402

DB_RULES = [
    "p(a).", "p(b).", "p(c).",
    "q(X) :- p(X), !.",
    "after_cut(X, Y) :- p(X), !, p(Y).",
    "r(X) :- p(X), !.", "r(zzz).",
    "parent(john, bob).", "parent(bob, ann).",
    "parent(john, carol).", "parent(carol, dave).",
    "grandparent(X, Y) :- parent(X, Z), parent(Z, Y).",
    "first_gp(X, Y) :- grandparent(X, Y), !.",
]
# Note: mprolog has no arithmetic-comparison builtins (>=, <, ...), so the
# classic max/3-with-cut example isn't expressible here; cut itself is exercised
# by the rules above.


def make_db():
    db = M.initialize_database()
    for rule in DB_RULES:
        head, body = M.parse_input(rule, is_interactive=False)["clause"]
        db.add_clause(head, body)
    return db


def ask(db, query):
    goals = M.parse_input("?- " + query, is_interactive=False)["goals"]
    sols = M.solve(goals, M.Environment(), db)
    return [M.format_solution(s, goals) for s in sols]


TESTS = []


def test(fn):
    TESTS.append(fn)
    return fn


@test
def t_backtracking_no_cut():
    assert ask(make_db(), "p(X).") == ["X = a", "X = b", "X = c"]


@test
def t_cut_commits_first_solution():
    assert ask(make_db(), "q(X).") == ["X = a"]


@test
def t_cut_prunes_sibling_clause():
    # the cut in r's first clause must also discard the alternative clause r(zzz)
    assert ask(make_db(), "r(X).") == ["X = a"]


@test
def t_cut_through_called_rule():
    db = make_db()
    assert ask(db, "grandparent(john, W).") == ["W = ann", "W = dave"]   # no cut
    assert ask(db, "first_gp(john, W).") == ["W = ann"]                  # cut: first


@test
def t_goals_after_cut_still_backtrack():
    # cut fixes X = a, but Y still ranges over all of p
    assert ask(make_db(), "after_cut(X, Y).") == [
        "X = a, Y = a", "X = a, Y = b", "X = a, Y = c"]


@test
def t_query_level_cut():
    assert ask(make_db(), "p(X), !.") == ["X = a"]


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
