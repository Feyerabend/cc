"""
A Prolog interpreter with cut (!) support.

Usage:
    prolog = PrologInterpreter()
    prolog.add_rules('''
        parent(john, bob).
        grandparent(X, Y) :- parent(X, Z), parent(Z, Y).
    ''')
    
    for solution in prolog.query("grandparent(X, bob)"):
        print(prolog.format_solution(solution))
"""

import re
from typing import Any, Dict, List, Iterator, Optional, Tuple, Set
from dataclasses import dataclass


class Variable:
    """A logical variable, identified by OBJECT IDENTITY.

    Each Variable() is a brand-new, globally unique variable: the `id` is drawn
    from one ever-increasing class counter (never reused) and is used only for
    display and as a stable dict/set key. Two distinct Variable objects are never
    equal — even if they share a name — so a freshly parsed query variable can
    never collide with a freshly renamed clause variable. This makes
    "standardizing apart" a structural guarantee rather than something to get
    right with matching counters.
    """
    _counter = 0

    def __init__(self, name: str):
        self.name = name
        Variable._counter += 1
        self.id = Variable._counter

    def __repr__(self):
        return f"{self.name}_{self.id}"

    def __eq__(self, other):
        return self is other          # object identity

    def __hash__(self):
        return id(self)


class Term:
    """Represents a Prolog term (atom or compound term)."""
    
    def __init__(self, functor: str, args: List[Any] = None):
        self.functor = functor
        self.args = args or []
    
    def __repr__(self):
        if not self.args:
            return self.functor
        args_str = ', '.join(repr(arg) for arg in self.args)
        return f"{self.functor}({args_str})"
    
    def __eq__(self, other):
        if not isinstance(other, Term):
            return False
        return (self.functor == other.functor and 
                len(self.args) == len(other.args) and
                all(a == b for a, b in zip(self.args, other.args)))
    
    def __hash__(self):
        return hash(self.functor)


@dataclass
class Clause:
    """Represents a Prolog clause (fact or rule)."""
    head: Term
    body: List[Term]
    
    def __repr__(self):
        if not self.body:
            return f"{self.head}."
        body_str = ', '.join(repr(goal) for goal in self.body)
        return f"{self.head} :- {body_str}."


class CutException(Exception):
    """Raised to implement the cut (!) operator.

    Carries the *barrier* — the id of the clause activation the cut commits to —
    so it is caught only at that clause's selection loop and propagates through
    the choice points of any called rules in between. (Without a barrier a cut
    was caught at the innermost clause loop, so it could not prune choice points
    created inside a called rule.)
    """
    def __init__(self, barrier=None):
        self.barrier = barrier
        super().__init__()


class Cut:
    """A cut goal tagged with the barrier of the clause body it occurs in."""
    __slots__ = ("barrier",)

    def __init__(self, barrier: int):
        self.barrier = barrier

    def __repr__(self):
        return "!"


class PrologParser:
    """Parses Prolog syntax into internal representation."""
    
    def __init__(self):
        self.variables: Dict[str, Variable] = {}

    def parse_program(self, text: str) -> List[Clause]:
        """Parse multiple clauses from text."""
        clauses = []
        clause_strs = re.split(r'\.\s*(?=\n|$)', text.strip())
        
        for clause_str in clause_strs:
            clause_str = clause_str.strip()
            if not clause_str or clause_str.startswith('%'):
                continue
            try:
                self.variables = {}
                clause = self.parse_clause(clause_str)
                if clause:
                    clauses.append(clause)
            except Exception as e:
                print(f"Warning: Failed to parse clause: {e}")
        
        return clauses
    
    def parse_clause(self, text: str) -> Optional[Clause]:
        """Parse a single clause."""
        text = text.strip().rstrip('.')
        if not text:
            return None
        
        # Find :- at depth 0
        depth = 0
        split_pos = -1
        for i in range(len(text) - 1):
            if text[i] in '([':
                depth += 1
            elif text[i] in ')]':
                depth -= 1
            elif depth == 0 and text[i:i+2] == ':-':
                split_pos = i
                break
        
        if split_pos != -1:
            head_str = text[:split_pos].strip()
            body_str = text[split_pos+2:].strip()
            head = self.parse_term(head_str)
            body = self.parse_goals(body_str)
            return Clause(head, body)
        else:
            head = self.parse_term(text)
            return Clause(head, [])
    
    def parse_goals(self, text: str) -> List[Term]:
        """Parse comma-separated goals."""
        if not text.strip():
            return []
        
        goals = []
        depth = 0
        current = []
        
        for char in text:
            if char in '([':
                depth += 1
                current.append(char)
            elif char in ')]':
                depth -= 1
                current.append(char)
            elif char == ',' and depth == 0:
                goal_str = ''.join(current).strip()
                if goal_str:
                    goals.append(self.parse_term(goal_str))
                current = []
            else:
                current.append(char)
        
        goal_str = ''.join(current).strip()
        if goal_str:
            goals.append(self.parse_term(goal_str))
        
        return goals
    
    def parse_term(self, text: str) -> Any:
        """Parse a single term with proper operator precedence."""

        text = text.strip()
        text = re.sub(r'\s+', '', text) # maybe? remove all whitespace for easier parsing

        if not text:
            raise ValueError("Empty term")
        
        # Handle cut
        if text == '!':
            return Term('!')
        
        # Handle lists
        if text.startswith('[') and text.endswith(']'):
            return self.parse_list(text[1:-1])

        # Handle variables
        if re.match(r'^[A-Z_][a-zA-Z0-9_]*$', text):
            return self._get_or_create_variable(text)

        # Handle numbers
        if self._is_number(text):
            return float(text)

        # Handle parenthesised expressions
        if text.startswith('(') and text.endswith(')'):
            return self.parse_term(text[1:-1])

        # Handle unary minus ~ as negative number
        if text.startswith('-'):
            rest = text[1:]
            if rest:
                subterm = self.parse_term(rest)
                return Term('-', [subterm])

        # Parse operators in order of INCREASING precedence
        # Lower precedence should be tried first
        
        # Level 1: is, \= (lowest precedence)
        for op in ['is', '\\=']:
            result = self._try_parse_infix(text, op)
            if result:
                return result
        
        # Level 2: Comparison operators
        for op in ['>=', '=<', '>', '<']:
            result = self._try_parse_infix(text, op)
            if result:
                return result
        
        # Level 3: Addition/Subtraction
        # IMPORTANT: Check + and - separately and find RIGHTMOST match
        result = self._try_parse_infix(text, '+')
        if result:
            return result
        result = self._try_parse_infix(text, '-')
        if result:
            return result
        
        # Level 4: Multiplication/Division (highest precedence)
        result = self._try_parse_infix(text, '*')
        if result:
            return result
        result = self._try_parse_infix(text, '/')
        if result:
            return result

        # Handle compound terms
        match = re.match(r'^(\w+)\((.*)\)$', text)
        if match:
            functor = match.group(1)
            args_str = match.group(2)
            args = self.parse_args(args_str)
            return Term(functor, args)
        
        # Simple atom
        return Term(text)
    
    def _try_parse_infix(self, text: str, op: str) -> Optional[Term]:
        """Try to parse text as an infix operator expression.
        For left-associative operators, we want the RIGHTMOST occurrence."""
        depth = 0
        positions = []
        
        i = 0
        while i < len(text):
            if text[i] in '([':
                depth += 1
            elif text[i] in ')]':
                depth -= 1
            elif depth == 0 and text[i:i+len(op)] == op:
                # Special handling for minus sign
                if op == '-':
                    # Check if this could be a negative number
                    if i == 0:
                        # At start, it's a negative number
                        i += 1
                        continue
                    before = text[:i].rstrip()
                    if before and before[-1] not in '(,+-*/':
                        # This is subtraction
                        positions.append(i)
                else:
                    positions.append(i)
            
            i += 1
        
        # Take the RIGHTMOST occurrence for left-associativity
        if positions:
            pos = positions[-1]
            left = text[:pos].strip()
            right = text[pos+len(op):].strip()
            if left and right:
                return Term(op, [self.parse_term(left), self.parse_term(right)])
        
        return None
    
    def _is_number(self, text: str) -> bool:
        """Check if text is a number."""
        try:
            float(text)
            return True
        except ValueError:
            return False
    
    def parse_args(self, text: str) -> List[Any]:
        """Parse comma-separated arguments."""
        if not text.strip():
            return []
        
        args = []
        depth = 0
        current = []
        
        for char in text:
            if char in '([':
                depth += 1
                current.append(char)
            elif char in ')]':
                depth -= 1
                current.append(char)
            elif char == ',' and depth == 0:
                arg_str = ''.join(current).strip()
                if arg_str:
                    args.append(self.parse_term(arg_str))
                current = []
            else:
                current.append(char)
        
        arg_str = ''.join(current).strip()
        if arg_str:
            args.append(self.parse_term(arg_str))
        
        return args
    
    def parse_list(self, text: str) -> Term:
        """Parse list into cons cells."""
        text = text.strip()
        
        if not text:
            return Term('[]')
        
        # Find | at depth 0
        depth = 0
        pipe_pos = -1
        for i, char in enumerate(text):
            if char in '([':
                depth += 1
            elif char in ')]':
                depth -= 1
            elif char == '|' and depth == 0:
                pipe_pos = i
                break
        
        if pipe_pos != -1:
            head_str = text[:pipe_pos]
            tail_str = text[pipe_pos+1:]
            heads = self.parse_args(head_str)
            tail = self.parse_term(tail_str)
            
            result = tail
            for head in reversed(heads):
                result = Term('.', [head, result])
            return result
        
        elements = self.parse_args(text)
        result = Term('[]')
        for elem in reversed(elements):
            result = Term('.', [elem, result])
        return result
    
    def _get_or_create_variable(self, name: str) -> Variable:
        """Get or create a variable (one per name within a single clause/query)."""
        if name not in self.variables:
            self.variables[name] = Variable(name)
        return self.variables[name]


class PrologInterpreter:
    """Main Prolog interpreter."""
    
    def __init__(self):
        self.clauses: List[Clause] = []
        self._barrier = 0

    def _new_barrier(self) -> int:
        """A fresh, unique id for one clause activation (a cut barrier)."""
        self._barrier += 1
        return self._barrier
    
    def add_rules(self, text: str):
        """Add rules from text."""
        parser = PrologParser()
        new_clauses = parser.parse_program(text)
        self.clauses.extend(new_clauses)
    
    def query(self, query_str: str) -> Iterator[Dict[Variable, Any]]:
        """Execute a query."""
        parser = PrologParser()
        goals = parser.parse_goals(query_str)
        query_vars = parser.variables

        # A cut at the top level of a query commits against the query itself.
        qbarrier = self._new_barrier()
        goals = [Cut(qbarrier) if (isinstance(g, Term) and g.functor == '!')
                 else g for g in goals]

        def solutions():
            try:
                yield from self._solve(goals, {})
            except CutException as cut:
                if cut.barrier != qbarrier:
                    raise

        for solution in solutions():
            filtered = {var: self._walk(var, solution)
                        for var in query_vars.values()}
            yield filtered
    
    def _solve(self, goals: List[Term], subst: Dict) -> Iterator[Dict]:
        """Solve goals with substitution."""
        if not goals:
            yield subst
            return
        
        goal = goals[0]
        remaining = goals[1:]
        
        # Handle cut: first produce all solutions of the goals to its right,
        # then prune by raising up to its own clause barrier.
        if isinstance(goal, Cut):
            for solution in self._solve(remaining, subst):
                yield solution
            raise CutException(goal.barrier)

        # Try built-ins
        builtin_result = self._try_builtin(goal, subst, remaining)
        if builtin_result is not None:
            yield from builtin_result    # cuts in `remaining` propagate naturally
            return

        # Try clauses
        for clause in self.clauses:
            fresh_clause = self._rename_clause(clause)
            new_subst = self._unify(goal, fresh_clause.head, subst.copy())

            if new_subst is not None:
                # One activation of this clause = one cut barrier. Tag the cuts
                # in its body with that barrier so a `!` commits to THIS clause.
                barrier = self._new_barrier()
                body = [Cut(barrier) if (isinstance(g, Term) and g.functor == '!')
                        else g for g in fresh_clause.body]
                new_goals = body + remaining

                try:
                    yield from self._solve(new_goals, new_subst)
                except CutException as cut:
                    if cut.barrier == barrier:
                        return            # the cut commits to this clause: stop
                    raise                 # belongs to an outer clause: propagate
    
    def _try_builtin(self, goal: Term, subst: Dict, remaining: List[Term]) -> Optional[Iterator[Dict]]:
        """Handle built-in predicates."""
        if not isinstance(goal, Term):
            return None
        
        # Comparison
        if goal.functor in ['>', '<', '>=', '=<'] and len(goal.args) == 2:
            left = self._eval_arith(goal.args[0], subst)
            right = self._eval_arith(goal.args[1], subst)
            
            if left is None or right is None:
                return iter([])
            
            result = False
            if goal.functor == '>':
                result = left > right
            elif goal.functor == '<':
                result = left < right
            elif goal.functor == '>=':
                result = left >= right
            elif goal.functor == '=<':
                result = left <= right
            
            return self._solve(remaining, subst) if result else iter([])
        
        # Arithmetic evaluation
        if goal.functor == 'is' and len(goal.args) == 2:
            value = self._eval_arith(goal.args[1], subst)
            if value is not None:
                new_subst = self._unify(goal.args[0], value, subst.copy())
                if new_subst is not None:
                    return self._solve(remaining, new_subst)
            return iter([])
        
        # Inequality
        if goal.functor == '\\=' and len(goal.args) == 2:
            left = self._walk(goal.args[0], subst)
            right = self._walk(goal.args[1], subst)
            if self._unify(left, right, {}) is None:
                return self._solve(remaining, subst)
            return iter([])
        
        return None
    
    def _eval_arith(self, expr: Any, subst: Dict) -> Optional[Any]:
        """Evaluate arithmetic expression."""
        expr = self._walk(expr, subst)
        
        if isinstance(expr, (int, float)):
            return expr
        
        if isinstance(expr, Term):
            if expr.functor == '+' and len(expr.args) == 2:
                left = self._eval_arith(expr.args[0], subst)
                right = self._eval_arith(expr.args[1], subst)
                if left is not None and right is not None:
                    return left + right
            elif expr.functor == '-' and len(expr.args) == 2:
                left = self._eval_arith(expr.args[0], subst)
                right = self._eval_arith(expr.args[1], subst)
                if left is not None and right is not None:
                    return left - right
            elif expr.functor == '*' and len(expr.args) == 2:
                left = self._eval_arith(expr.args[0], subst)
                right = self._eval_arith(expr.args[1], subst)
                if left is not None and right is not None:
                    return left * right
            elif expr.functor == '/' and len(expr.args) == 2:
                left = self._eval_arith(expr.args[0], subst)
                right = self._eval_arith(expr.args[1], subst)
                if left is not None and right is not None and right != 0:
                    return left / right
            elif expr.functor == '-' and len(expr.args) == 1: # Unary minus
                val = self._eval_arith(expr.args[0], subst)
                if val is not None:
                    return -val
        
        return None
    
    def _rename_clause(self, clause: Clause) -> Clause:
        """Rename variables in a clause."""
        mapping = {}
        
        def rename(term):
            if isinstance(term, Variable):
                if term not in mapping:
                    mapping[term] = Variable(term.name)   # a fresh, unique variable
                return mapping[term]
            elif isinstance(term, Term):
                new_args = []
                for arg in term.args:
                    new_args.append(rename(arg))
                return Term(term.functor, new_args)
            else:
                return term
        
        new_head = rename(clause.head)
        new_body = []
        for goal in clause.body:
            new_body.append(rename(goal))
        return Clause(new_head, new_body)
    
    def _unify(self, x: Any, y: Any, subst: Dict) -> Optional[Dict]:
        """Unify two terms."""
        x = self._walk(x, subst)
        y = self._walk(y, subst)
        
        if self._terms_equal(x, y):
            return subst
        
        if isinstance(x, Variable):
            if self._occurs_check(x, y, subst):
                return None
            subst[x] = y
            return subst
        
        if isinstance(y, Variable):
            if self._occurs_check(y, x, subst):
                return None
            subst[y] = x
            return subst
        
        if isinstance(x, Term) and isinstance(y, Term):
            if x.functor != y.functor or len(x.args) != len(y.args):
                return None
            
            for x_arg, y_arg in zip(x.args, y.args):
                subst = self._unify(x_arg, y_arg, subst)
                if subst is None:
                    return None
            return subst
        
        return None
    
    def _terms_equal(self, x: Any, y: Any) -> bool:
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            return float(x) == float(y)
        if type(x) != type(y):
            return False

        if isinstance(x, Variable):
            return x.id == y.id
        elif isinstance(x, Term):
            if x.functor != y.functor or len(x.args) != len(y.args):
                return False
            return all(self._terms_equal(a, b) for a, b in zip(x.args, y.args))
        else:
            return x == y
    
#    def _walk(self, term: Any, subst: Dict) -> Any:
#        """Follow variable bindings."""
#        seen = set()
#        while isinstance(term, Variable):
#            if term.id in seen:
#                break
#            if term not in subst:
#                break
#            seen.add(term.id)
#            term = subst[term]
#        return term


    def _walk(self, term: Any, subst: Dict, seen: Optional[Set[int]] = None) -> Any:
        if seen is None:
            seen = set()
        
        if isinstance(term, Variable):
            if term.id in seen:
                return term  # Cycle detected
            seen.add(term.id)
            if term in subst:
                return self._walk(subst[term], subst, seen)
            return term
        
        elif isinstance(term, Term):
            new_args = [self._walk(arg, subst, seen) for arg in term.args]
            return Term(term.functor, new_args)
        
        else:
            return term







    def _occurs_check(self, var: Variable, term: Any, subst: Dict) -> bool:
        """Occurs check."""
        term = self._walk(term, subst)
        
        if isinstance(term, Variable) and var.id == term.id:
            return True
        
        if isinstance(term, Term):
            return any(self._occurs_check(var, arg, subst) for arg in term.args)
        
        return False
    
    def format_solution(self, solution: Dict[Variable, Any]) -> str:
        """Format solution."""
        if not solution:
            return "true"
        
        parts = []
        for var, val in sorted(solution.items(), key=lambda x: x[0].name):
            parts.append(f"{var.name} = {self._format_term(val)}")
        return ", ".join(parts)
    
    def _format_term(self, term: Any) -> str:
        """Format term for display."""
        if isinstance(term, Variable):
            return str(term)
        elif isinstance(term, Term):
            if term.functor == '[]':
                return '[]'
            elif term.functor == '.':
                elements = []
                current = term
                seen = set()
                
                while isinstance(current, Term) and current.functor == '.':
                    if id(current) in seen:
                        return '[...]'
                    seen.add(id(current))
                    elements.append(self._format_term(current.args[0]))
                    current = current.args[1]
                
                if isinstance(current, Term) and current.functor == '[]':
                    return f"[{', '.join(elements)}]"
                else:
                    return f"[{', '.join(elements)}|{self._format_term(current)}]"
            elif not term.args:
                return term.functor
            else:
                args = ', '.join(self._format_term(arg) for arg in term.args)
                return f"{term.functor}({args})"
        elif isinstance(term, float):
            if term == int(term):
                return str(int(term))
            return str(term)
        else:
            return str(term)


# Example usage
if __name__ == "__main__":
    prolog = PrologInterpreter()
    
    # Family tree example
    print("=" * 60)
    print("Family Tree Example")
    print("=" * 60)
    
    prolog.add_rules(r'''
        parent(john, bob).
        parent(mary, bob).
        parent(bob, alice).
        parent(bob, charlie).

        grandparent(X, Y) :- parent(X, Z), parent(Z, Y).
        sibling(X, Y) :- parent(P, X), parent(P, Y), X \= Y.
    ''')
    
    print("\nQuery: grandparent(X, alice)")
    for solution in prolog.query("grandparent(X, alice)"):
        print(f"  {prolog.format_solution(solution)}")
    
    print("\nQuery: parent(bob, X)")
    for solution in prolog.query("parent(bob, X)"):
        print(f"  {prolog.format_solution(solution)}")

    print("\nQuery: sibling(alice, X)   (uses \\=)")
    for solution in prolog.query("sibling(alice, X)"):
        print(f"  {prolog.format_solution(solution)}")

    # List example
    print("\n" + "=" * 60)
    print("List Processing Example")
    print("=" * 60)
    
    prolog.add_rules('''
        append([], L, L).
        append([H|T], L, [H|R]) :- append(T, L, R).
        
        member(X, [X|_]).
        member(X, [_|T]) :- member(X, T).
    ''')
    
    print("\nQuery: append([1,2], [3,4], X)")
    for solution in prolog.query("append([1,2], [3,4], X)"):
        print(f"  {prolog.format_solution(solution)}")
    
    print("\nQuery: member(X, [a,b,c])")
    for solution in prolog.query("member(X, [a,b,c])"):
        print(f"  {prolog.format_solution(solution)}")
    
    print("\nQuery: append(X, Y, [1,2,3])")
    count = 0
    for solution in prolog.query("append(X, Y, [1,2,3])"):
        print(f"  {prolog.format_solution(solution)}")
        count += 1
        if count >= 5:
            break
    
    # Cut example
    print("\n" + "=" * 60)
    print("Cut (!) Example")
    print("=" * 60)
    
    prolog.add_rules('''
        max(X, Y, X) :- X >= Y, !.
        max(X, Y, Y).
    ''')
    
    print("\nQuery: max(5, 3, Z)")
    for solution in prolog.query("max(5, 3, Z)"):
        print(f"  {prolog.format_solution(solution)}")
    
    print("\nQuery: max(2, 7, Z)")
    for solution in prolog.query("max(2, 7, Z)"):
        print(f"  {prolog.format_solution(solution)}")
    
    # Arithmetic example
    print("\n" + "=" * 60)
    print("Arithmetic Example")
    print("=" * 60)
    
    prolog.add_rules('''
        factorial(0, 1) :- !.
        factorial(N, F) :- N > 0, N1 is N - 1, factorial(N1, F1), F is F1 * N.
    ''')
    
    print("\nQuery: factorial(5, F)")
    for solution in prolog.query("factorial(5, F)"):
        print(f"  {prolog.format_solution(solution)}")
    
    # Negative number test
    print("\n" + "=" * 60)
    print("Negative Number Test")
    print("=" * 60)
    
    prolog.add_rules('''
        test_neg(X, Y) :- Y is X + -5.
    ''')
    
    print("\nQuery: test_neg(10, Y)")
    for solution in prolog.query("test_neg(10, Y)"):
        print(f"  {prolog.format_solution(solution)}")

