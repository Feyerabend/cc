"""
Mini-Prolog Interpreter
A more complete Prolog interpreter
with iterative algorithms (faster),
and some comprehensive tests
"""
import sys
import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass


# Parser Combinators (Simple Implementation)
class ParseError(Exception):
    """Exception raised when parsing fails"""
    pass

def item(input: str) -> Tuple[str, str]:
    """Consume one character from input"""
    if not input:
        raise ParseError("Unexpected end of input")
    return input[0], input[1:]

def satisfy(pred):
    """Parse a character satisfying a predicate"""
    def parser(input: str):
        ch, rest = item(input)
        if pred(ch):
            return ch, rest
        raise ParseError(f"Unexpected character: {ch!r}")
    return parser

def literal(ch: str):
    """Parse a specific character"""
    return satisfy(lambda x: x == ch)

def one_of(chars: str):
    """Parse any character from a set"""
    return satisfy(lambda x: x in chars)

def seq(*parsers):
    """Parse a sequence of parsers"""
    def parser(input: str):
        results = []
        rest = input
        for p in parsers:
            res, rest = p(rest)
            results.append(res)
        return results, rest
    return parser

def choice(*parsers):
    """Try parsers in order until one succeeds"""
    def parser(input: str):
        for p in parsers:
            try:
                return p(input)
            except ParseError:
                pass
        raise ParseError("No parser matched")
    return parser

def many(parser):
    """Parse zero or more occurrences"""
    def p(input: str):
        results = []
        rest = input
        while True:
            try:
                res, rest = parser(rest)
                results.append(res)
            except ParseError:
                return results, rest
    return p

def many1(parser):
    """Parse one or more occurrences"""
    def p(input: str):
        res, rest = parser(input)
        more, rest = many(parser)(rest)
        return [res] + more, rest
    return p

def fmap(f, parser):
    """Apply function to parser result"""
    def p(input: str):
        res, rest = parser(input)
        return f(res), rest
    return p

def bind(parser, f):
    """Monadic bind for parser combinators"""
    def p(input: str):
        res, rest = parser(input)
        return f(res)(rest)
    return p

def ws():
    """Parse whitespace"""
    return many(one_of(" \t\n\r"))

def token(parser):
    """Parse with leading whitespace"""
    return bind(ws(), lambda _: parser)

def symbol(s: str):
    """Parse a symbol (string with whitespace)"""
    return token(seq(*[literal(c) for c in s]))

def parens(parser):
    """Parse parenthesized content"""
    return bind(symbol("("),
                lambda _: bind(parser,
                               lambda res: bind(symbol(")"),
                                                lambda _: parse_result(res))))

def parse_result(value: Any):
    """Return a parser that always succeeds with given value"""
    def p(input: str):
        return value, input
    return p

def sep_by(parser, separator):
    """Parse items separated by a separator"""
    def p(input: str):
        results = []
        rest = input
        try:
            first, rest = parser(rest)
            results.append(first)
        except ParseError:
            return [], input
        while True:
            try:
                _, rest = separator(rest)
                item, rest = parser(rest)
                results.append(item)
            except ParseError:
                return results, rest
    return p


# Term Representations (Data Classes)
class Term:
    """Base class for all Prolog terms"""
    pass

class Atom(Term):
    """Atomic term (constant)"""
    def __init__(self, name: str):
        self.name = name
   
    def __repr__(self):
        return "[]" if self.name == "[]" else self.name
   
    def __eq__(self, other):
        return isinstance(other, Atom) and self.name == other.name
   
    def __hash__(self):
        return hash(('Atom', self.name))

class Variable(Term):
    """Variable term"""
    def __init__(self, name: str):
        self.name = name
   
    def __repr__(self):
        return self.name
   
    def __eq__(self, other):
        return isinstance(other, Variable) and self.name == other.name

    def __hash__(self):
        return hash(('Variable', self.name))

class Cut(Term):
    """The cut goal '!', tagged with the choice-point stack height it commits to.

    A Cut is produced during solving: solve() tags each clause body's '!' with
    the stack height at which that clause was selected. It appears only in goal
    lists, never in stored clauses or in unification, so renaming and unification
    never see it.
    """
    def __init__(self, barrier: int):
        self.barrier = barrier

    def __repr__(self):
        return "!"

class Compound(Term):
    """Compound term with functor and arguments"""
    def __init__(self, functor: str, args: List[Term]):
        self.functor = functor
        self.args = tuple(args) if isinstance(args, list) else args
   
    def __repr__(self):
        if not self.args:
            return self.functor
        args_str = ', '.join(map(repr, self.args))
        return f"{self.functor}({args_str})"
   
    def __eq__(self, other):
        return (isinstance(other, Compound) and
                self.functor == other.functor and
                self.args == other.args)
   
    def __hash__(self):
        return hash(('Compound', self.functor, self.args))

class ListTerm(Term):
    """List term [elements | tail]"""
    def __init__(self, elements: List[Term], tail: Term = None):
        self.elements = tuple(elements) if isinstance(elements, list) else elements
        self.tail = tail if tail is not None else Atom("[]")
   
    def __repr__(self):
        elts = ', '.join(map(repr, self.elements))
        if isinstance(self.tail, Atom) and self.tail.name == "[]":
            return f"[{elts}]" if elts else "[]"
        else:
            return f"[{elts} | {repr(self.tail)}]"
   
    def __eq__(self, other):
        return (isinstance(other, ListTerm) and
                self.elements == other.elements and
                self.tail == other.tail)
   
    def __hash__(self):
        return hash(('ListTerm', self.elements, self.tail))


# Term Parsers (Using Parser Combinators)
def parse_atom():
    """Parse an atom (lowercase identifier or special symbols)"""
    def parser(input: str):
        # Handle special atoms
        if input.startswith("[]"):
            return Atom("[]"), input[2:]
       
        first_res, rest = satisfy(lambda c: c.islower() or c == '_')(input)
        rest_chars = []
        temp = rest
        while temp:
            try:
                ch, temp2 = satisfy(lambda c: c.isalnum() or c == '_')(temp)
                rest_chars.append(ch)
                temp = temp2
            except ParseError:
                break
        return Atom(first_res + ''.join(rest_chars)), temp
    return parser

def parse_variable():
    """Parse a variable (uppercase identifier)"""
    def parser(input: str):
        first_res, rest = satisfy(lambda c: c.isupper())(input)
        rest_chars = []
        temp = rest
        while temp:
            try:
                ch, temp2 = satisfy(lambda c: c.isalnum() or c == '_')(temp)
                rest_chars.append(ch)
                temp = temp2
            except ParseError:
                break
        return Variable(first_res + ''.join(rest_chars)), temp
    return parser

def parse_number():
    """Parse a number as an atom"""
    digits = many1(satisfy(str.isdigit))
    return fmap(lambda ds: Atom(''.join(ds)), digits)

def parse_list():
    """Parse a list [elements] or [elements | tail]"""
    def content():
        elts = sep_by(parse_term(), symbol(","))
        tail_opt = choice(
            bind(symbol("|"), lambda _: parse_term()),
            parse_result(Atom("[]"))
        )
        return bind(elts, lambda es: bind(tail_opt, lambda t: parse_result(ListTerm(es, t))))
    def normalize(res):
        if isinstance(res, ListTerm) and len(res.elements) == 0 and isinstance(res.tail, Atom) and res.tail.name == "[]":
            return Atom("[]")
        return res
    return bind(symbol("["), lambda _: bind(content(), lambda res: bind(symbol("]"), lambda _: parse_result(normalize(res)))))

def parse_compound():
    """Parse a compound term functor(args)"""
    def parser(input: str):
        functor_res, rest = parse_atom()(input)
        rest = rest.lstrip(' \t\n\r')
        if not rest.startswith('('):
            raise ParseError("Not a compound term")
        args_res, rest2 = parens(sep_by(parse_term(), symbol(",")))(rest)
        return Compound(functor_res.name, args_res), rest2
    return parser

def parse_cut():
    """Parse the cut operator '!' (kept as Atom('!'); tagged with a barrier at
    solve time)."""
    return fmap(lambda _: Atom('!'), token(literal('!')))

def parse_primary():
    """Parse primary terms without infix operators"""
    return token(choice(
        parse_cut(),
        parse_list(),
        parse_number(),
        parse_compound(),
        parse_variable(),
        parse_atom()
    ))

def parse_unification():
    """Parse infix unification A = B"""
    return bind(parse_primary(), lambda l: bind(token(literal("=")), lambda _: bind(parse_primary(), lambda r: parse_result(Compound("=", [l, r])))))

def parse_term():
    """Parse any term, including unification"""
    return choice(
        parse_unification(),
        parse_primary()
    )

def parse_goals():
    """Parse a comma-separated list of goals"""
    return sep_by(parse_term(), symbol(","))

def parse_clause():
    """Parse a clause: head :- body. or head."""
    head = parse_term()
    rule = bind(symbol(":-"), lambda _: bind(parse_goals(), lambda body: bind(symbol("."), lambda _: parse_result(body))))
    fact = bind(symbol("."), lambda _: parse_result([]))
    return token(bind(head, lambda h: bind(choice(rule, fact), lambda b: parse_result((h, b)))))

def parse_query():
    """Parse a query: ?- goals."""
    return token(bind(symbol("?-"), lambda _: bind(parse_goals(), lambda gs: bind(symbol("."), lambda _: parse_result(gs)))))

def has_variables(term: Term) -> bool:
    """Check if a term contains any variables"""
    if isinstance(term, Variable):
        return True
    elif isinstance(term, Compound):
        return any(has_variables(arg) for arg in term.args)
    elif isinstance(term, ListTerm):
        return any(has_variables(elem) for elem in term.elements) or has_variables(term.tail)
    return False

def parse_input(line: str, is_interactive=False):
    """Parse user input (query or clause)"""
    line = re.sub(r"%.*", "", line) # Remove comments
    line = line.strip()
    if not line:
        raise ParseError("Empty input")
   
    if line.startswith("?-"):
        goals, rest = parse_query()(line)
        if rest.strip():
            raise ParseError("Extra characters after query")
        return {"type": "query", "goals": goals}
    elif ":-" in line:
        # It's a rule
        clause, rest = parse_clause()(line)
        if rest.strip():
            raise ParseError("Extra characters after clause")
        return {"type": "clause", "clause": clause}
    elif is_interactive:
        # In interactive mode: check if it contains variables
        # If no variables, it's a fact; if it has variables, it's a query
        line_no_dot = line.rstrip(".")
        goals, rest = parse_goals()(line_no_dot)
        if rest.strip():
            raise ParseError("Extra characters after goals")
        
        # Check if any goal has variables
        has_vars = any(has_variables(goal) for goal in goals)
        
        if has_vars:
            # Has variables -> query
            return {"type": "query", "goals": goals}
        else:
            # No variables -> fact
            if len(goals) == 1:
                return {"type": "clause", "clause": (goals[0], [])}
            else:
                raise ParseError("Multiple facts must be entered separately")
    else:
        # Non-interactive: parse as clause (fact)
        clause, rest = parse_clause()(line)
        if rest.strip():
            raise ParseError("Extra characters after clause")
        return {"type": "clause", "clause": clause}


# Environment and Substitution (Iterative Implementation)
class Environment:
    """Environment stores variable bindings"""
   
    def __init__(self, bindings=None):
        self.bindings: Dict[Variable, Term] = bindings or {}
    def bind(self, var: Variable, term: Term) -> 'Environment':
        """Create new environment with additional binding"""
        new_bindings = self.bindings.copy()
        new_bindings[var] = term
        return Environment(new_bindings)
    def lookup(self, var: Variable) -> Term:
        """Lookup variable, following chains"""
        seen = set()
        current = var
        while current in self.bindings:
            var_id = id(current)
            if var_id in seen:
                return var # Avoid infinite loops
            seen.add(var_id)
            val = self.bindings[current]
            if not isinstance(val, Variable):
                return val
            current = val
        return current


# Core Operations (All Iterative Implementations)
def substitute(term: Term, env: Environment) -> Term:
    """Substitute variables in term using environment (iterative)"""
    if isinstance(term, Atom):
        return term
   
    if isinstance(term, Variable):
        result = env.lookup(term)
        # Recursively substitute if we got another term
        if result != term and not isinstance(result, Atom):
            return substitute(result, env)
        return result
   
    stack = [term]
    result_map = {}
    processing = set()
   
    while stack:
        current = stack[-1]
        current_id = id(current)
       
        if current_id in result_map:
            stack.pop()
            continue
       
        if current_id in processing:
            stack.pop()
            processing.remove(current_id)
           
            if isinstance(current, Compound):
                new_args = tuple(result_map[id(arg)] for arg in current.args)
                result_map[current_id] = Compound(current.functor, new_args)
            elif isinstance(current, ListTerm):
                new_elements = list(result_map[id(elem)] for elem in current.elements)
                new_tail = result_map[id(current.tail)]
                
                # Recursively flatten ListTerms
                final_elements = []
                for elem in new_elements:
                    # Recursively substitute each element
                    subst_elem = substitute(elem, env) if isinstance(elem, (Variable, Compound, ListTerm)) else elem
                    final_elements.append(subst_elem)
                
                # Recursively substitute and flatten tail
                subst_tail = substitute(new_tail, env) if isinstance(new_tail, (Variable, Compound, ListTerm)) else new_tail
                
                # Flatten if tail is also a ListTerm
                if isinstance(subst_tail, ListTerm):
                    final_elements.extend(subst_tail.elements)
                    result_map[current_id] = ListTerm(final_elements, subst_tail.tail)
                else:
                    result_map[current_id] = ListTerm(final_elements, subst_tail)
            continue
       
        if isinstance(current, Variable):
            looked_up = env.lookup(current)
            if looked_up != current:
                result_map[current_id] = substitute(looked_up, env)
            else:
                result_map[current_id] = current
            stack.pop()
        elif isinstance(current, Atom):
            result_map[current_id] = current
            stack.pop()
        elif isinstance(current, Compound):
            processing.add(current_id)
            for arg in reversed(current.args):
                if id(arg) not in result_map:
                    stack.append(arg)
        elif isinstance(current, ListTerm):
            processing.add(current_id)
            if id(current.tail) not in result_map:
                stack.append(current.tail)
            for elem in reversed(current.elements):
                if id(elem) not in result_map:
                    stack.append(elem)
   
    return result_map.get(id(term), term)


def rename_variables(term: Term, suffix: str) -> Term:
    """Rename all variables in term by adding suffix (iterative)"""
    stack = [term]
    result_map = {}
    processing = set()
    var_mapping = {} # Map old var to new var
   
    while stack:
        current = stack[-1]
        current_id = id(current)
       
        if current_id in result_map:
            stack.pop()
            continue
       
        if current_id in processing:
            stack.pop()
            processing.remove(current_id)
           
            if isinstance(current, Compound):
                new_args = tuple(result_map[id(arg)] for arg in current.args)
                result_map[current_id] = Compound(current.functor, new_args)
            elif isinstance(current, ListTerm):
                new_elements = tuple(result_map[id(elem)] for elem in current.elements)
                new_tail = result_map[id(current.tail)]
                result_map[current_id] = ListTerm(new_elements, new_tail)
            continue
       
        if isinstance(current, Variable):
            # Use variable equality, not id
            var_key = current.name
            if var_key not in var_mapping:
                var_mapping[var_key] = Variable(current.name + suffix)
            result_map[current_id] = var_mapping[var_key]
            stack.pop()
        elif isinstance(current, Atom):
            result_map[current_id] = current
            stack.pop()
        elif isinstance(current, Compound):
            processing.add(current_id)
            for arg in reversed(current.args):
                if id(arg) not in result_map:
                    stack.append(arg)
        elif isinstance(current, ListTerm):
            processing.add(current_id)
            if id(current.tail) not in result_map:
                stack.append(current.tail)
            for elem in reversed(current.elements):
                if id(elem) not in result_map:
                    stack.append(elem)
   
    return result_map.get(id(term), term)


def occurs_check(var: Variable, term: Term, env: Environment) -> bool:
    """Check if variable occurs in term (prevents infinite structures)"""
    stack = [term]
    visited = set()
   
    while stack:
        current = stack.pop()
        current_id = id(current)
       
        if current_id in visited:
            continue
        visited.add(current_id)
       
        if isinstance(current, Variable):
            looked_up = env.lookup(current)
            if looked_up == var:
                return True
            if looked_up != current:
                stack.append(looked_up)
        elif isinstance(current, Compound):
            stack.extend(current.args)
        elif isinstance(current, ListTerm):
            stack.extend(current.elements)
            stack.append(current.tail)
   
    return False


def unify(a: Term, b: Term, env: Environment) -> Optional[Environment]:
    """Unify two terms (iterative algorithm)"""
    stack = [(a, b)]
   
    while stack:
        x, y = stack.pop()
       
        x_sub = substitute(x, env)
        y_sub = substitute(y, env)
       
        # Normalize empty lists to atoms
        if isinstance(x_sub, ListTerm) and len(x_sub.elements) == 0 and x_sub.tail == Atom("[]"):
            x_sub = Atom("[]")
        if isinstance(y_sub, ListTerm) and len(y_sub.elements) == 0 and y_sub.tail == Atom("[]"):
            y_sub = Atom("[]")
       
        if x_sub is y_sub or x_sub == y_sub:
            continue
           
        if isinstance(x_sub, Variable):
            if occurs_check(x_sub, y_sub, env):
                return None
            env = env.bind(x_sub, y_sub)
            continue
           
        if isinstance(y_sub, Variable):
            if occurs_check(y_sub, x_sub, env):
                return None
            env = env.bind(y_sub, x_sub)
            continue
       
        if type(x_sub) != type(y_sub):
            return None
       
        if isinstance(x_sub, Atom):
            if x_sub.name != y_sub.name:
                return None
            continue
       
        if isinstance(x_sub, Compound):
            if x_sub.functor != y_sub.functor or len(x_sub.args) != len(y_sub.args):
                return None
            for arg_x, arg_y in zip(x_sub.args, y_sub.args):
                stack.append((arg_x, arg_y))
            continue
       
        if isinstance(x_sub, ListTerm):
            min_len = min(len(x_sub.elements), len(y_sub.elements))
            for i in range(min_len):
                stack.append((x_sub.elements[i], y_sub.elements[i]))
            if len(x_sub.elements) > len(y_sub.elements):
                remaining = ListTerm(x_sub.elements[min_len:], x_sub.tail)
                stack.append((y_sub.tail, remaining))
            elif len(y_sub.elements) > len(x_sub.elements):
                remaining = ListTerm(y_sub.elements[min_len:], y_sub.tail)
                stack.append((x_sub.tail, remaining))
            else:
                stack.append((x_sub.tail, y_sub.tail))
            continue
   
    return env


# Database (Clause Storage)
class Database:
    """Stores Prolog clauses"""
   
    def __init__(self):
        self.clauses: List[Tuple[Term, List[Term]]] = []
        self.clause_counter = 0
    def add_clause(self, head: Term, body: List[Term]):
        """Add a clause to the database"""
        self.clauses.append((head, body))


# Built-in Predicates (Handling)
def handle_builtin(goal: Compound, env: Environment, db: Database) -> List[Environment]:
    """Handle built-in predicates"""
    f = goal.functor
    args = goal.args
   
    # Control predicates
    if f == "true":
        return [env]
   
    if f == "fail":
        return []
   
    # Unification
    if f == "=" and len(args) == 2:
        new_env = unify(args[0], args[1], env)
        return [new_env] if new_env else []
   
    # I/O predicates
    if f == "write" and len(args) >= 1:
        for arg in args:
            print(substitute(arg, env), end="")
        return [env]
   
    if f == "nl":
        print()
        return [env]
   
    return []


# Solver (Iterative with Stack-Based Backtracking)
def _is_cut(goal: Term) -> bool:
    """True for an untagged cut goal, the Atom '!' produced by the parser."""
    return isinstance(goal, Atom) and goal.name == '!'


def solve(goals: List[Term], env: Environment, db: Database, max_solutions=None) -> List[Environment]:
    """
    Solve goals using iterative depth-first search with backtracking.
    Returns list of solution environments.
    """
    solutions = []
    # A cut at the top level of the query commits against the query itself
    # (barrier 0 — discard every choice point of the whole search).
    goals = [Cut(0) if _is_cut(g) else g for g in goals]
    stack = [(list(goals), env, 0)] # (goals, environment, next_clause_index)

    while stack and (max_solutions is None or len(solutions) < max_solutions):
        current_goals, current_env, clause_idx = stack.pop()

        # Success: no more goals
        if not current_goals:
            solutions.append(current_env)
            continue

        goal = current_goals[0]
        rest_goals = current_goals[1:]

        # Cut: discard every choice point created since its clause was entered
        # (truncate the choice-point stack back to the cut's barrier), then carry
        # on with the goals to its right.
        if isinstance(goal, Cut):
            del stack[goal.barrier:]
            stack.append((rest_goals, current_env, 0))
            continue

        # Handle built-in predicates (both Atom and Compound forms)
        if isinstance(goal, Atom) and goal.name in {"true", "fail"}:
            if goal.name == "true":
                stack.append((rest_goals, current_env, 0))
            # fail just doesn't add anything to stack
            continue

        if isinstance(goal, Compound) and goal.functor in {"true", "fail", "=", "write", "nl"}:
            result_envs = handle_builtin(goal, current_env, db)
            for new_env in result_envs:
                stack.append((rest_goals, new_env, 0))
            continue

        # Try to unify with database clauses
        for i in range(clause_idx, len(db.clauses)):
            head, body = db.clauses[i]

            # Rename variables to avoid conflicts
            suffix = f"_{db.clause_counter}"
            db.clause_counter += 1
            renamed_head = rename_variables(head, suffix)
            renamed_body = [rename_variables(g, suffix) for g in body]

            # Try to unify
            new_env = unify(goal, renamed_head, current_env)
            if new_env:
                # This clause was selected with the choice-point stack at this
                # height; a '!' in its body commits back to here, discarding the
                # next-clause choice point below and any choice points its earlier
                # body goals create.
                barrier = len(stack)
                tagged_body = [Cut(barrier) if _is_cut(g) else g
                               for g in renamed_body]
                # Add choice point for next clause
                if i + 1 < len(db.clauses):
                    stack.append((current_goals, current_env, i + 1))
                # Continue with this clause's body
                stack.append((tagged_body + rest_goals, new_env, 0))
                break
   
    return solutions


# Init Database (Standard Predicates)
def initialize_database() -> Database:
    """Initialise database with standard predicates"""
    db = Database()
   
    # Common predicates
    predicates = [
        # Unification
        (Compound("=", [Variable("X"), Variable("X")]), []),
       
        # List operations: append
        (Compound("append", [Atom("[]"), Variable("L"), Variable("L")]), []),
        (Compound("append", [
            ListTerm([Variable("H")], Variable("T")),
            Variable("L"),
            ListTerm([Variable("H")], Variable("R"))
        ]), [Compound("append", [Variable("T"), Variable("L"), Variable("R")])]),
       
        # List operations: member
        (Compound("member", [Variable("X"), ListTerm([Variable("X")], Variable("_"))]), []),
        (Compound("member", [Variable("X"), ListTerm([Variable("_")], Variable("Y"))]),
         [Compound("member", [Variable("X"), Variable("Y")])]),
       
        # List operations: last
        (Compound("last", [ListTerm([Variable("X")], Atom("[]")), Variable("X")]), []),
        (Compound("last", [ListTerm([Variable("_")], Variable("T")), Variable("X")]),
         [Compound("last", [Variable("T"), Variable("X")])]),
    ]
   
    for head, body in predicates:
        db.add_clause(head, body)
   
    return db


# Format Solutions (Display)
def format_solution(env: Environment, original_goals: List[Term]) -> str:
    """Format a solution environment for display"""
    # Collect original variables from goals
    original_vars = {}
    
    def collect_vars(term, var_dict):
        if isinstance(term, Variable) and not term.name.startswith("_"):
            var_dict[term] = term.name
        elif isinstance(term, Compound):
            for arg in term.args:
                collect_vars(arg, var_dict)
        elif isinstance(term, ListTerm):
            for elem in term.elements:
                collect_vars(elem, var_dict)
            collect_vars(term.tail, var_dict)
    
    for goal in original_goals:
        collect_vars(goal, original_vars)
   
    bindings = {}
    for var, var_name in original_vars.items():
        final_val = substitute(var, env)
        # Only show if it's bound to something other than itself
        if final_val != var:
            bindings[var_name] = final_val
   
    if not bindings:
        return "true"
   
    parts = [f"{name} = {val}" for name, val in sorted(bindings.items())]
    return ", ".join(parts)


# Tests
def run_tests():
    """Run comprehensive tests"""
    print("-" * 50)
    print("RUNNING TESTS")
    print("-" * 50)
   
    db = initialize_database()
   
    tests = [
        # Basic facts
        ("fact", "parent(tom, bob).", None, True),
        ("fact", "parent(bob, ann).", None, True),
        ("fact", "parent(bob, pat).", None, True),
       
        # Query facts
        ("query", "?- parent(tom, bob).", [{}], True),
        ("query", "?- parent(bob, X).", [{"X": "ann"}, {"X": "pat"}], True),
        ("query", "?- parent(tom, ann).", [], False),
       
        # Rules
        ("fact", "grandparent(X, Z) :- parent(X, Y), parent(Y, Z).", None, True),
        ("query", "?- grandparent(tom, ann).", [{}], True),
        ("query", "?- grandparent(tom, X).", [{"X": "ann"}, {"X": "pat"}], True),
       
        # List operations
        ("query", "?- append([1, 2], [3, 4], X).", [{"X": "[1, 2, 3, 4]"}], True),
        ("query", "?- append(X, [3, 4], [1, 2, 3, 4]).", [{"X": "[1, 2]"}], True),
        ("query", "?- member(2, [1, 2, 3]).", [{}], True),
        ("query", "?- member(X, [a, b, c]).", [{"X": "a"}, {"X": "b"}, {"X": "c"}], True),
        ("query", "?- last([1, 2, 3], X).", [{"X": "3"}], True),
       
        # Unification
        ("query", "?- X = 5.", [{"X": "5"}], True),
        ("query", "?- f(X, b) = f(a, Y).", [{"X": "a", "Y": "b"}], True),
    ]
   
    passed = 0
    failed = 0
   
    for i, test in enumerate(tests):
        test_type, input_str, expected, should_pass = test
       
        try:
            parsed = parse_input(input_str, is_interactive=False)
           
            if test_type == "fact":
                head, body = parsed["clause"]
                db.add_clause(head, body)
                if should_pass:
                    print(f"✓ Test {i+1}: Added clause")
                    passed += 1
                else:
                    print(f"✗ Test {i+1}: Should have failed but passed")
                    failed += 1
           
            elif test_type == "query":
                goals = parsed["goals"]
                solutions = solve(goals, Environment(), db)
               
                if should_pass and solutions:
                    print(f"✓ Test {i+1}: {input_str}")
                    for sol in solutions[:3]: # Show first 3 solutions
                        print(f" → {format_solution(sol, goals)}")
                    passed += 1
                elif not should_pass and not solutions:
                    print(f"✓ Test {i+1}: Correctly failed: {input_str}")
                    passed += 1
                else:
                    print(f"✗ Test {i+1}: Unexpected result for {input_str}")
                    print(f" Expected {expected}, got {len(solutions)} solutions")
                    failed += 1
       
        except Exception as e:
            if not should_pass:
                print(f"✓ Test {i+1}: Correctly failed with error")
                passed += 1
            else:
                print(f"✗ Test {i+1}: Error: {e}")
                failed += 1
   
    print("-" * 50)
    print(f"Tests passed: {passed}/{passed + failed}")
    print("-" * 50)
    return passed == len(tests)


# REPL
def main():
    """Main REPL loop"""
    # Run tests first
    if "--test" in sys.argv:
        run_tests()
        return
   
    db = initialize_database()
   
    print("-" * 50)
    print("Mini-Prolog Interpreter")
    print("-" * 50)
    print("Commands:")
    print(" fact.             Add fact (no variables)")
    print(" query.            Query (has variables)")
    print(" head :- body.     Add rule")
    print(" quit.             Exit")
    print(" show.             Show database")
    print("-" * 50)
    print("\nExamples:")
    print(" parent(tom, bob).        <- Adds fact (no variables)")
    print(" parent(tom, X).          <- Query (has variable X)")
    print(" append([1,2], [3,4], X). <- Query")
    print("-" * 50)
   
    while True:
        try:
            sys.stdout.write("\n?- ")
            sys.stdout.flush()
            line = sys.stdin.readline()
           
            if not line:
                break
           
            line = line.strip()
            if not line:
                continue
           
            if line in ["quit.", "exit.", "q."]:
                print("\nBye!")
                break
            
            if line == "show.":
                print(f"Database has {len(db.clauses)} clauses:")
                for i, (head, body) in enumerate(db.clauses):
                    if body:
                        print(f"  {i}: {head} :- {', '.join(map(str, body))}.")
                    else:
                        print(f"  {i}: {head}.")
                continue
           
            # Parse input
            parsed = parse_input(line, is_interactive=True)
            
            if parsed["type"] == "query":
                goals = parsed["goals"]
                solutions = solve(goals, Environment(), db)
               
                if not solutions:
                    print("false.")
                else:
                    for i, sol_env in enumerate(solutions):
                        result = format_solution(sol_env, goals)
                        print(result, end="")
                       
                        if i < len(solutions) - 1:
                            sys.stdout.write(" ;")
                            sys.stdout.flush()
                            response = sys.stdin.readline().strip()
                            if response != ";":
                                print()
                                break
                            print()
                        else:
                            print(".")
           
            elif parsed["type"] == "clause":
                head, body = parsed["clause"]
                db.add_clause(head, body)
                print("true.")
            
            else:
                print(f"Unknown parse type: {parsed['type']}")
       
        except ParseError as e:
            print(f"Syntax error: {e}")
        except KeyboardInterrupt:
            print("\nInterrupted")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()

