
## Classic GOFAI

This folder contains code demonstrations of the three paradigms that defined classical
symbolic AI: expert systems, state space search, and constraint satisfaction. For the
broader account of what GOFAI is, how it relates to connectionism, and where these
techniques fit in the history of AI, see the parent [README](../README.md).

Each file makes the core GOFAI commitment concrete: knowledge is hand-coded, reasoning
is explicit and traceable, and every conclusion has a justification that can be read and
checked. The knowledge acquisition bottleneck--the cost of encoding all that knowledge
by hand--is visible in the code itself.


### Expert Systems -- `expert.py`

A forward-chaining inference engine for animal classification. Rules are encoded as
explicit if-then conditions; the engine fires applicable rules from the current facts
until no new conclusions can be drawn. This is *data-driven* reasoning: start from what
is known, derive what follows.

Forward chaining is one of two directions. The other--backward chaining, starting from
a goal and working back to the supporting facts--is goal-directed and more efficient
when most conclusions are irrelevant to the question at hand. Prolog uses backward
chaining as its operational semantics.


### State Space Search -- `eight.py`

The 8-puzzle solved by three algorithms: *Breadth-First Search* (BFS), *Depth-First
Search* (DFS), and *A\** with the Manhattan distance heuristic. The puzzle is a clean
instance of the general GOFAI approach to problem solving: represent the problem as a
graph of states, define the operators that move between states, search for a path from
the initial state to the goal.

BFS guarantees the shortest solution but explores exhaustively. DFS uses less memory
but may find longer paths. A* uses a heuristic to guide the search toward the goal,
typically exploring far fewer states than either uninformed method. Comparing the three
on the same puzzle makes the trade-offs between completeness, optimality, and efficiency
concrete.


### Constraint Satisfaction -- `colour.html` and `nqueen.html`

Two interactive browser demos of *constraint satisfaction problems* (CSPs).

`colour.html` assigns colours to the regions of a map so that no two adjacent regions
share a colour--equivalent to vertex colouring in graph theory. `nqueen.html` places
n queens on an n×n chessboard so that no queen threatens another.

Both use backtracking search with constraint checking: assign a value, verify no
constraint is violated, proceed to the next variable; if a violation is found, undo
and try the next value. The visualisations make the search process--and the backtracking
steps--visible in real time.

CSPs are among the most practical GOFAI techniques still in daily use: scheduling,
configuration, resource allocation, and planning all reduce to constraint satisfaction
at some level.
