"""
CEK Machine for Lambda Calculus
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Union



@dataclass(frozen=True)
class Var:
    name: str
    def __repr__(self): return self.name

@dataclass(frozen=True)
class Lam:
    param: str
    body: Any
    def __repr__(self): return f"λ{self.param}.{self.body}"

@dataclass(frozen=True)
class App:
    fun: Any
    arg: Any
    def __repr__(self): return f"({self.fun} {self.arg})"

Term = Union[Var, Lam, App]



@dataclass(frozen=True)
class Closure:
    param: str
    body: Term
    env: Dict[str, 'Value']
    def __repr__(self): return f"<λ{self.param}.{self.body}>"

Value = Closure



class Kont:
    pass

@dataclass
class Halt(Kont):
    def __repr__(self): return "Halt"

@dataclass
class Arg(Kont):
    arg_term: Term
    env: Dict[str, Value]
    next: Kont
    def __repr__(self): return f"Arg[{self.arg_term}, {self.next}]"

@dataclass
class Fun(Kont):
    fun_val: Value
    next: Kont
    def __repr__(self): return f"Fun[{self.fun_val}, {self.next}]"



@dataclass
class State:
    control: Term
    env: Dict[str, Value]
    kont: Kont
    def __repr__(self):
        env_str = {k: str(v) for k, v in self.env.items()}
        return f"⟨{self.control} | {env_str} | {self.kont}⟩"



def eval_step(state: Union[State, Value]) -> Union[State, Value]:
    if isinstance(state, Value):
        return state

    c, e, k = state.control, state.env, state.kont

    if isinstance(c, Var):
        return apply_kont(k, e[c.name])

    elif isinstance(c, Lam):
        return apply_kont(k, Closure(c.param, c.body, e.copy()))

    elif isinstance(c, App):
        return State(c.fun, e.copy(), Arg(c.arg, e.copy(), k))

    raise ValueError(f"Unknown term: {c}")

def apply_kont(k: Kont, val: Value) -> Union[State, Value]:
    if isinstance(k, Halt):
        return val
    elif isinstance(k, Arg):
        return State(k.arg_term, k.env, Fun(val, k.next))
    elif isinstance(k, Fun):
        if not isinstance(k.fun_val, Closure):
            raise ValueError("Not a function")
        new_env = k.fun_val.env.copy()
        new_env[k.fun_val.param] = val
        return State(k.fun_val.body, new_env, k.next)
    raise ValueError(f"Unknown kont: {k}")

def run(term: Term, max_steps: int = 10000) -> Value:
    current = State(term, {}, Halt())
    steps = 0
    while not isinstance(current, Value):
        if steps >= max_steps:
            raise RuntimeError("Divergence detected")
        current = eval_step(current)
        steps += 1
    return current

def trace(term: Term, label: str = "", max_steps: int = 20):
    print(f"\n=== {label} ===")
    current = State(term, {}, Halt())
    history = [current]
    steps = 0
    while not isinstance(current, Value) and steps < max_steps:
        current = eval_step(current)
        history.append(current)
        steps += 1

    for i, s in enumerate(history):
        if isinstance(s, Value):
            print(f"{i:2d}: Result: {s}")
        else:
            print(f"{i:2d}: {s}")

    if isinstance(current, Value):
        print(f"Pretty: {pretty_value(current)}")



def unfold_apps(term: Term) -> List[Term]:
    """Unfold left-associated applications: (((f a) b) c) → [f, a, b, c]"""
    apps = []
    current = term
    while isinstance(current, App):
        apps.append(current.arg)
        current = current.fun
    apps.append(current)
    apps.reverse()
    return apps

def is_church_numeral(closure: Closure) -> int | None:
    if closure.param != 'f':
        return None
    body = closure.body
    if not isinstance(body, Lam) or body.param != 'x':
        return None

    # Try to count f applications in body
    apps = unfold_apps(body.body)
    if len(apps) < 2:
        return None
    f_apps = apps[:-1]
    x = apps[-1]

    if not (isinstance(x, Var) and x.name == 'x'):
        return None
    if not all(isinstance(a, Var) and a.name == 'f' for a in f_apps):
        return None

    return len(f_apps)

def is_church_bool(closure: Closure) -> str | None:
    if closure.param != 't':
        return None
    body = closure.body
    if not isinstance(body, Lam) or body.param != 'f':
        return None
    if isinstance(body.body, Var):
        name = body.body.name
        if name == 't':
            return "True"
        if name == 'f':
            return "False"
    return None

def pretty_value(val: Value) -> str:
    n = is_church_numeral(val)
    if n is not None:
        if n == 0:
            return "Church 0: λf.λx.x"
        apps = "f(" * n + "x" + ")" * n
        return f"Church {n}: λf.λx.{apps}"

    b = is_church_bool(val)
    if b is not None:
        return f"Church Boolean: {b}"

    return str(val)



# Church numerals
Zero = Lam("f", Lam("x", Var("x")))
One = Lam("f", Lam("x", App(Var("f"), Var("x"))))
Two = Lam("f", Lam("x", App(Var("f"), App(Var("f"), Var("x")))))
Three = Lam("f", Lam("x", App(Var("f"), App(Var("f"), App(Var("f"), Var("x"))))))
Four = Lam("f", Lam("x", App(Var("f"), App(Var("f"), App(Var("f"), App(Var("f"), Var("x")))))))

Succ = Lam("n", Lam("f", Lam("x", App(Var("f"), App(App(Var("n"), Var("f")), Var("x"))))))
Add = Lam("m", Lam("n", Lam("f", Lam("x", App(App(Var("m"), Var("f")), App(App(Var("n"), Var("f")), Var("x")))))))
Mul = Lam("m", Lam("n", Lam("f", Lam("x", App(App(Var("m"), App(Var("n"), Var("f"))), Var("x"))))))

# Booleans
ChurchTrue = Lam("t", Lam("f", Var("t")))
ChurchFalse = Lam("t", Lam("f", Var("f")))
And = Lam("a", Lam("b", App(App(Var("a"), Var("b")), ChurchFalse)))

# Pairs
Pair = Lam("a", Lam("b", Lam("c", App(App(Var("c"), Var("a")), Var("b")))))
Car = Lam("p", App(Var("p"), ChurchTrue))
Cdr = Lam("p", App(Var("p"), ChurchFalse))


# examples
ex1 = App(Lam("x", App(Var("x"), Var("x"))), Lam("y", Var("y")))
ex2 = App(Succ, One)
ex3 = App(App(Add, Two), One)
ex4 = App(App(Mul, Two), Two)
ex5 = App(App(And, ChurchTrue), ChurchFalse)
ex6 = App(Car, App(App(Pair, One), Two))
ex7 = App(Cdr, App(App(Pair, Three), Four))

Omega = App(Lam("x", App(Var("x"), Var("x"))), Lam("x", App(Var("x"), Var("x"))))

if __name__ == "__main__":
    trace(ex1, "Example 1: (λx.xx)(λy.y) → identity", max_steps=30)
    trace(ex2, "Example 2: succ 1 → 2", max_steps=30)
    trace(ex3, "Example 3: 2 + 1 → 3", max_steps=30)
    trace(ex4, "Example 4: 2 × 2 → 4", max_steps=30)
    trace(ex5, "Example 5: True ∧ False → False", max_steps=30)
    trace(ex6, "Example 6: car(pair(1, 2)) → 1", max_steps=30)
    trace(ex7, "Example 7: cdr(pair(3, 4)) → 4", max_steps=30)

    print("\nDivergence demo:")
    trace(Omega, "Omega: (λx.xx)(λx.xx) – should loop", max_steps=15)
