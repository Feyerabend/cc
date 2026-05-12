"""
planning.py -- STRIPS-style forward-state-space planner.

STRIPS (Fikes & Nilsson, 1971) represents actions with three components:
  preconditions : facts that must hold for the action to be applicable
  add-list      : facts added to the state after the action
  delete-list   : facts removed from the state after the action

The *frame assumption*: everything not in the delete list remains unchanged.
This is the simplest formal answer to the frame problem.

Domain: blocks world.
A robot arm manipulates lettered blocks on a table.
The arm can hold at most one block.

State facts:
  ("on", X, Y)       -- block X is directly on top of block Y
  ("ontable", X)     -- block X is directly on the table
  ("clear", X)       -- nothing is on top of block X
  "handempty"        -- the arm holds nothing
  ("holding", X)     -- the arm is holding block X

Operators:
  pickup(X)          -- pick a clear block from the table
  putdown(X)         -- put the held block on the table
  stack(X, Y)        -- place the held block X on clear block Y
  unstack(X, Y)      -- pick block X off block Y (both must be clear / on Y)
"""

from collections import deque


State = frozenset  # immutable set of ground facts


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------

def applicable_actions(state: State, blocks: list[str]) -> list[tuple]:
    """Generate all ground actions applicable in state."""
    actions = []

    if "handempty" in state:
        for b in blocks:
            if ("ontable", b) in state and ("clear", b) in state:
                actions.append(("pickup", b))
            for other in blocks:
                if b != other and ("on", b, other) in state and ("clear", b) in state:
                    actions.append(("unstack", b, other))
    else:
        held = next(b for b in blocks if ("holding", b) in state)
        actions.append(("putdown", held))
        for other in blocks:
            if other != held and ("clear", other) in state:
                actions.append(("stack", held, other))

    return actions


def apply_action(state: State, action: tuple) -> State:
    """Return the new state after applying action (STRIPS semantics)."""
    s = set(state)
    op = action[0]

    if op == "pickup":
        _, x = action
        s -= {("clear", x), ("ontable", x), "handempty"}
        s.add(("holding", x))

    elif op == "putdown":
        _, x = action
        s.discard(("holding", x))
        s |= {("ontable", x), ("clear", x), "handempty"}

    elif op == "stack":
        _, x, y = action
        s -= {("holding", x), ("clear", y)}
        s |= {("on", x, y), ("clear", x), "handempty"}

    elif op == "unstack":
        _, x, y = action
        s -= {("on", x, y), ("clear", x), "handempty"}
        s |= {("holding", x), ("clear", y)}

    return frozenset(s)


# ---------------------------------------------------------------------------
# BFS planner
# ---------------------------------------------------------------------------

def plan(initial: State, goal: frozenset, blocks: list[str]) -> list | None:
    """
    BFS over the state space; returns a shortest action sequence reaching goal,
    or None if no solution exists.

    goal is a frozenset of facts that must all hold in the final state.
    Other facts in the final state are ignored (partial-state goal).
    """
    if goal.issubset(initial):
        return []

    queue = deque([(initial, [])])
    visited = {initial}

    while queue:
        state, actions = queue.popleft()
        for action in applicable_actions(state, blocks):
            new_state = apply_action(state, action)
            if new_state in visited:
                continue
            new_actions = actions + [action]
            if goal.issubset(new_state):
                return new_actions
            visited.add(new_state)
            queue.append((new_state, new_actions))

    return None


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def fmt_action(action: tuple) -> str:
    return f"{action[0]}({', '.join(action[1:])})"


def fmt_state(state: State) -> str:
    def key(f):
        return (f,) if isinstance(f, str) else f
    return "  " + "\n  ".join(str(f) for f in sorted(state, key=key))


def run_demo(title: str, initial: State, goal: frozenset, blocks: list[str]) -> None:
    print(f"=== {title} ===")
    print("Initial state:")
    print(fmt_state(initial))
    print("Goal:")
    print(fmt_state(goal))

    solution = plan(initial, goal, blocks)
    if solution:
        print(f"\nSolution ({len(solution)} steps):")
        state = initial
        for i, action in enumerate(solution, 1):
            state = apply_action(state, action)
            print(f"  {i}.  {fmt_action(action)}")
    else:
        print("No solution found.")
    print()


# ---------------------------------------------------------------------------
# Demonstrations
# ---------------------------------------------------------------------------

def demo_build_tower() -> None:
    """
    All three blocks on the table; build the tower C on B on A.

    Initial:                 Goal:
      A   B   C              C
     [table]               [B]
                           [A]
                          [table]
    """
    blocks = ["A", "B", "C"]
    initial = frozenset({
        ("ontable", "A"), ("clear", "A"),
        ("ontable", "B"), ("clear", "B"),
        ("ontable", "C"), ("clear", "C"),
        "handempty",
    })
    goal = frozenset({
        ("on", "B", "A"),
        ("on", "C", "B"),
    })
    run_demo("Build tower: C on B on A", initial, goal, blocks)


def demo_rearrange() -> None:
    """
    C is stacked on A; B is free.  Goal: A on B, C back on table.

    Initial:                 Goal:
      C                        A
     [A]   B                  [B]   C
     [table]                  [table]
    """
    blocks = ["A", "B", "C"]
    initial = frozenset({
        ("ontable", "A"),
        ("on",      "C", "A"), ("clear", "C"),
        ("ontable", "B"), ("clear", "B"),
        "handempty",
    })
    goal = frozenset({
        ("on",      "A", "B"),
        ("ontable", "C"),
    })
    run_demo("Rearrange: C on A, B free  ->  A on B, C on table", initial, goal, blocks)


def demo_reverse_stack() -> None:
    """
    Stack A on B on C (A on top); reverse to C on B on A.

    Initial:                 Goal:
      A                        C
     [B]                      [B]
     [C]                      [A]
    [table]                  [table]
    """
    blocks = ["A", "B", "C"]
    initial = frozenset({
        ("ontable", "C"),
        ("on",      "B", "C"),
        ("on",      "A", "B"), ("clear", "A"),
        "handempty",
    })
    goal = frozenset({
        ("ontable", "A"),
        ("on",      "B", "A"),
        ("on",      "C", "B"),
    })
    run_demo("Reverse stack: A on B on C  ->  C on B on A", initial, goal, blocks)


if __name__ == "__main__":
    demo_build_tower()
    demo_rearrange()
    demo_reverse_stack()
