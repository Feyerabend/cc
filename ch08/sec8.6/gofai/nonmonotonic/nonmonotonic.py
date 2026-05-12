"""nonmonotonic.py -- defeasible reasoner illustrating Reiter-style default logic.

A default rule has the form:  prereq : M justif / conseq
Fire if prereq is believed and neg(justif) is NOT believed (i.e. the justification
is consistent with the current extension).  Normal defaults use justif == conseq.

Negation uses the 'not_' prefix convention:
    neg("flies_tweety")     == "not_flies_tweety"
    neg("not_flies_tweety") == "flies_tweety"
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Default:
    prereq: str
    justif: str
    conseq: str


def neg(fact: str) -> str:
    return fact[4:] if fact.startswith("not_") else f"not_{fact}"


class Reasoner:
    def __init__(self):
        self._facts: set[str] = set()
        self._hard: list[tuple[str, str]] = []
        self._defaults: list[Default] = []

    def assert_fact(self, *facts: str) -> "Reasoner":
        self._facts.update(facts)
        return self

    def add_rule(self, condition: str, consequence: str) -> "Reasoner":
        """Hard (monotonic) rule: condition -> consequence."""
        self._hard.append((condition, consequence))
        return self

    def add_default(self, prereq: str, justif: str, conseq: str) -> "Reasoner":
        """Default rule: prereq : M justif / conseq."""
        self._defaults.append(Default(prereq, justif, conseq))
        return self

    def extension(self) -> frozenset[str]:
        """Compute a grounded extension by saturating hard rules then defaults."""
        beliefs: set[str] = set(self._facts)
        # Saturate hard rules first
        changed = True
        while changed:
            changed = False
            for cond, concl in self._hard:
                if cond in beliefs and concl not in beliefs:
                    beliefs.add(concl)
                    changed = True
        # Saturate defaults (greedy, in registration order)
        changed = True
        while changed:
            changed = False
            for d in self._defaults:
                if d.prereq not in beliefs:
                    continue
                if neg(d.justif) in beliefs:   # blocked by its negation
                    continue
                if d.conseq not in beliefs:
                    beliefs.add(d.conseq)
                    changed = True
        return frozenset(beliefs)

    def query(self, fact: str) -> bool:
        return fact in self.extension()


# ---------------------------------------------------------------------------
# Demo 1: Tweety -- the canonical non-monotonic example
# ---------------------------------------------------------------------------

def tweety_demo() -> None:
    print("=== Tweety ===")
    r = Reasoner()

    # Normal default: Bird(x) : M Flies(x) / Flies(x)
    r.add_default("bird_tweety", "flies_tweety", "flies_tweety")

    # Hard rule: penguins don't fly
    r.add_rule("penguin_tweety", neg("flies_tweety"))

    r.assert_fact("bird_tweety")
    print(f"  bird only         -> flies? {r.query('flies_tweety')}")   # True

    r.assert_fact("penguin_tweety")
    print(f"  bird + penguin    -> flies? {r.query('flies_tweety')}")   # False
    print()


# ---------------------------------------------------------------------------
# Demo 2: Nixon diamond -- the multiple extensions problem
#
# Nixon is a Quaker (default: pacifist) and a Republican (default: non-pacifist).
# Two defaults compete with no priority between them.  The greedy algorithm
# picks the one registered first, producing different answers for r1 vs r2.
# Both are valid extensions; neither is more justified than the other.
# ---------------------------------------------------------------------------

def nixon_diamond() -> None:
    print("=== Nixon diamond (multiple extensions) ===")

    def make_kb() -> Reasoner:
        r = Reasoner()
        r.assert_fact("quaker_nixon", "republican_nixon")
        return r

    r1 = make_kb()
    r1.add_default("quaker_nixon",      "pacifist_nixon",     "pacifist_nixon")
    r1.add_default("republican_nixon",  "not_pacifist_nixon", "not_pacifist_nixon")

    r2 = make_kb()
    r2.add_default("republican_nixon",  "not_pacifist_nixon", "not_pacifist_nixon")
    r2.add_default("quaker_nixon",      "pacifist_nixon",     "pacifist_nixon")

    print(f"  quaker-first  -> pacifist? {r1.query('pacifist_nixon')}")      # True
    print(f"  republican-first -> pacifist? {r2.query('pacifist_nixon')}")   # False
    print("  (same facts, same defaults, different registration order -> "
          "different conclusions)")
    print()


# ---------------------------------------------------------------------------
# Demo 3: priority via specificity -- penguins override birds
#
# A more realistic KB uses an 'abnormal' predicate and specific overrides,
# so the priority is explicit in the rules rather than in registration order.
# ---------------------------------------------------------------------------

def specificity_demo() -> None:
    print("=== Specificity (explicit priority via abnormality) ===")
    r = Reasoner()

    # General default: birds fly unless abnormal
    r.add_default("bird_opus", "not_ab_opus", "flies_opus")

    # Specific override: penguins are abnormal w.r.t. flight
    r.add_rule("penguin_opus", "ab_opus")       # hard: penguin -> ab
    r.add_rule("penguin_opus", "bird_opus")     # hard: penguin -> bird (subtype)

    r.assert_fact("penguin_opus")
    ext = r.extension()
    print(f"  penguin(Opus) -> bird? {r.query('bird_opus')}")
    print(f"  penguin(Opus) -> ab?   {r.query('ab_opus')}")
    print(f"  penguin(Opus) -> flies? {r.query('flies_opus')}")   # False: ab blocks default
    print()


if __name__ == "__main__":
    tweety_demo()
    nixon_diamond()
    specificity_demo()
