"""
verify_rate_limiter.py

Symbolic verification of a token bucket rate limiter using Z3.

A token bucket is one of the most common rate-limiting algorithms in
networking, operating systems, and APIs (Linux tc, nginx, AWS API Gateway,
Envoy proxy, etc.). The rules are:

  - The bucket holds at most CAPACITY tokens.
  - At the start of each tick, REFILL tokens are added (capped at CAPACITY).
  - Each incoming request consumes one token if available; otherwise it is
    rejected.

This file demonstrates three things:

  1. Prove that the correct implementation satisfies its safety properties
     for ALL possible request sequences simultaneously — not just for one
     test case.

  2. Introduce a real bug (missing the capacity cap on refill) and show Z3
     automatically producing a counterexample trace that witnesses the
     violation.

  3. Introduce a second real bug (serving before refilling) and show Z3
     proving that this change in order causes requests to be wrongly
     rejected at tick 0 when the bucket starts empty.

This is essentially what bounded model checkers like CBMC, CPAchecker, and
KLEE do internally: they translate a program into SMT constraints and hand
them to a solver like Z3. Here we write the constraints directly so the
connection is transparent.
"""

from z3 import *


CAPACITY      = 4   # maximum tokens the bucket can hold
REFILL        = 2   # tokens added at the start of each tick
TICKS         = 5   # number of ticks to analyse (the loop unroll depth)
SAFETY_BOUND  = CAPACITY + TICKS * REFILL


def build_limiter(initial_tokens=CAPACITY,
                  buggy_no_cap=False,
                  buggy_serve_first=False):
    """
    Return (Solver, tokens, request, accepted) encoding TICKS ticks of the
    token bucket limiter as Z3 integer constraints.

    Each request[t] is a fully symbolic variable (0 or 1), so the solver
    reasons over all 2^TICKS possible request patterns at once — this is
    the central point of the exercise.

    initial_tokens    — starting token level (normally CAPACITY)
    buggy_no_cap      — omit the cap after refilling (tokens can exceed CAPACITY)
    buggy_serve_first — consume a token before refilling instead of after
    """
    tokens   = [Int(f'tokens_{t}')  for t in range(TICKS + 1)]
    request  = [Int(f'request_{t}') for t in range(TICKS)]
    accepted = [Int(f'accepted_{t}') for t in range(TICKS)]

    s = Solver()
    s.add(tokens[0] == initial_tokens)

    for t in range(TICKS):
        s.add(Or(request[t] == 0, request[t] == 1))

        if buggy_serve_first:
            # BUG: consume a token first, then refill
            can_accept  = And(request[t] == 1, tokens[t] > 0)
            tokens_mid  = If(can_accept, tokens[t] - 1, tokens[t])
            if buggy_no_cap:
                tokens_next = tokens_mid + REFILL
            else:
                tokens_next = If(tokens_mid + REFILL > CAPACITY,
                                 CAPACITY, tokens_mid + REFILL)
        else:
            # Correct order: refill first, then serve
            if buggy_no_cap:
                # BUG: refill without capping at CAPACITY
                refilled = tokens[t] + REFILL
            else:
                refilled = If(tokens[t] + REFILL > CAPACITY,
                              CAPACITY, tokens[t] + REFILL)
            can_accept  = And(request[t] == 1, refilled > 0)
            tokens_next = If(can_accept, refilled - 1, refilled)

        s.add(accepted[t]   == If(can_accept, 1, 0))
        s.add(tokens[t + 1] == tokens_next)

    return s, tokens, request, accepted


def check_property(label, s, prop_expr):
    """
    Verify prop_expr universally by adding Not(prop_expr) to a push/pop
    frame and checking for unsat.  The model is captured inside the frame
    while it is still available, then the frame is discarded so s is
    unmodified on return.

    Returns (holds: bool, model_or_None).
    """
    s.push()
    s.add(Not(prop_expr))
    result = s.check()
    model  = s.model() if result == sat else None
    s.pop()

    print(f"  {label}")
    if result == unsat:
        print(f"    PASS — Z3 proved no execution violates this property.")
        return True, None
    elif result == sat:
        print(f"    FAIL — Z3 found a counterexample.")
        return False, model
    else:
        print(f"    UNKNOWN — Z3 could not decide.")
        return None, None


def print_trace(model, tokens, request, accepted):
    print(f"    {'tick':>4}  {'tokens_before':>13}  {'request':>7}  "
          f"{'accepted':>8}  {'tokens_after':>12}")
    print(f"    {'-' * 52}")
    for t in range(TICKS):
        print(f"    {t:>4}  "
              f"{str(model.evaluate(tokens[t])):>13}  "
              f"{str(model.evaluate(request[t])):>7}  "
              f"{str(model.evaluate(accepted[t])):>8}  "
              f"{str(model.evaluate(tokens[t + 1])):>12}")


print("=" * 64)
print("  Token Bucket Rate Limiter — Symbolic Verification via Z3")
print("=" * 64)
print(f"\n  CAPACITY={CAPACITY}, REFILL={REFILL}, TICKS={TICKS}")
print(f"  Safety bound: accepted <= {SAFETY_BOUND}  "
      f"(= CAPACITY + TICKS * REFILL)")
print(f"  Capacity invariant: tokens always in [0, {CAPACITY}]")


# PART 1: Correct implementation — four properties all hold
print("\n\nPart 1: Correct implementation (bucket starts full)")
print("-" * 48)

s1, tok1, req1, acc1 = build_limiter()
total1 = Sum(acc1)

check_property("accepted <= SAFETY_BOUND",
               s1, total1 <= SAFETY_BOUND)

check_property(f"tokens always <= {CAPACITY}  (capacity invariant)",
               s1, And(*[tok1[t] <= CAPACITY for t in range(TICKS + 1)]))

check_property("tokens always >= 0  (no negative tokens)",
               s1, And(*[tok1[t] >= 0 for t in range(TICKS + 1)]))

check_property("if all requests arrive, at least one is accepted  (liveness)",
               s1, Implies(
                   And(*[req1[t] == 1 for t in range(TICKS)]),
                   total1 >= 1))


# PART 2: Bug — refill without the capacity cap
print("\n\nPart 2: Buggy implementation — refill without capacity cap")
print("-" * 48)
print("  Bug: tokens[t+1] = tokens[t] + REFILL  (no min with CAPACITY)")
print("  Tokens accumulate without bound when there are no requests,")
print("  then can be discharged in a burst that exceeds the intended limit.")
print("  Claim: tokens always <= CAPACITY.  Expect Z3 to refute this.\n")

s2, tok2, req2, acc2 = build_limiter(buggy_no_cap=True)

holds, model = check_property(
    f"tokens always <= {CAPACITY}  (capacity invariant)",
    s2, And(*[tok2[t] <= CAPACITY for t in range(TICKS + 1)]))

if not holds and model is not None:
    print()
    print("  Counterexample trace (Z3 chose zero requests so tokens grow freely):")
    print_trace(model, tok2, req2, acc2)
    for t in range(TICKS + 1):
        val = model.evaluate(tok2[t]).as_long()
        if val > CAPACITY:
            print(f"\n  First violation at tick {t}: "
                  f"tokens = {val} > CAPACITY ({CAPACITY}).")
            print(f"  The uncapped refill added {REFILL} unconditionally each tick.")
            break


# PART 3: Bug — serve before refill
print("\n\nPart 3: Buggy implementation — serve before refill (empty initial bucket)")
print("-" * 48)
print("  Bug: consume a token first, then refill instead of refill-then-serve.")
print("  With a full initial bucket both orderings accept the same requests.")
print("  With an EMPTY initial bucket the difference appears immediately:")
print("  the correct limiter refills first and can accept tick-0 requests;")
print("  the buggy one sees tokens=0 at tick 0 and rejects them.\n")

sc, tok_c, req_c, acc_c = build_limiter(initial_tokens=0)
sb, tok_b, req_b, acc_b = build_limiter(initial_tokens=0, buggy_serve_first=True)

# Check: is there any sequence where the correct limiter accepts at tick t
# but the buggy one rejects, given they share the same request variables?
# We do this with a combined solver.
s_cmp = Solver()
s_cmp.add(sc.assertions())

# Add the buggy constraints with renamed variables so both live in one solver
for assertion in sb.assertions():
    s_cmp.add(assertion)

# The two sets of token/accepted variables are independent; share request variables.
# Actually build_limiter uses different names already (tok_c vs tok_b etc.).
# We need to share the request variables. Rebuild with a shared request array.
shared_request = [Int(f'req_shared_{t}') for t in range(TICKS)]

s_cmp2 = Solver()
for t in range(TICKS):
    s_cmp2.add(Or(shared_request[t] == 0, shared_request[t] == 1))

# Correct path
tc = [Int(f'tc_{t}') for t in range(TICKS + 1)]
ac = [Int(f'ac_{t}') for t in range(TICKS)]
s_cmp2.add(tc[0] == 0)
for t in range(TICKS):
    refilled = If(tc[t] + REFILL > CAPACITY, CAPACITY, tc[t] + REFILL)
    can      = And(shared_request[t] == 1, refilled > 0)
    s_cmp2.add(ac[t]     == If(can, 1, 0))
    s_cmp2.add(tc[t + 1] == If(can, refilled - 1, refilled))

# Buggy serve-first path
tb = [Int(f'tb_{t}') for t in range(TICKS + 1)]
ab = [Int(f'ab_{t}') for t in range(TICKS)]
s_cmp2.add(tb[0] == 0)
for t in range(TICKS):
    can_b      = And(shared_request[t] == 1, tb[t] > 0)
    mid_b      = If(can_b, tb[t] - 1, tb[t])
    refilled_b = If(mid_b + REFILL > CAPACITY, CAPACITY, mid_b + REFILL)
    s_cmp2.add(ab[t]     == If(can_b, 1, 0))
    s_cmp2.add(tb[t + 1] == refilled_b)

# Ask: does any tick exist where correct accepts but buggy rejects?
unfair = Or(*[And(ac[t] == 1, ab[t] == 0) for t in range(TICKS)])

print("  Checking: correct and serve-first limiter always agree on accepted requests.")
print("  (Expect Z3 to find a case where serve-first wrongly rejects.)\n")

s_cmp2.push()
s_cmp2.add(unfair)
result = s_cmp2.check()
model3 = s_cmp2.model() if result == sat else None
s_cmp2.pop()

if result == sat and model3 is not None:
    print(f"  FAIL — Z3 found a divergence:\n")
    print(f"    {'tick':>4}  {'request':>7}  {'correct_tokens':>14}  "
          f"{'correct_acc':>11}  {'buggy_tokens':>12}  {'buggy_acc':>9}")
    print(f"    {'-' * 62}")
    for t in range(TICKS):
        print(f"    {t:>4}  "
              f"{str(model3.evaluate(shared_request[t])):>7}  "
              f"{str(model3.evaluate(tc[t])):>14}  "
              f"{str(model3.evaluate(ac[t])):>11}  "
              f"{str(model3.evaluate(tb[t])):>12}  "
              f"{str(model3.evaluate(ab[t])):>9}")
    for t in range(TICKS):
        if (model3.evaluate(ac[t]).as_long() == 1 and
                model3.evaluate(ab[t]).as_long() == 0):
            print(f"\n  At tick {t}: correct limiter refilled to "
                  f"{min(0 + REFILL, CAPACITY)} first and accepted the request.")
            print(f"  Serve-first saw tokens=0 and rejected it before refilling.")
            break
elif result == unsat:
    print("  PASS — both implementations agree on all sequences (unexpected).")


# PART 4: Scope of the proof
print("\n\nPart 4: What the symbolic proof covers")
print("-" * 48)
print(f"  There are 2^{TICKS} = {2**TICKS} possible request sequences over {TICKS} ticks.")
print(f"  Z3 proves (or refutes) each property over ALL {2**TICKS} sequences")
print(f"  in a single solver call by treating each request bit as a symbolic")
print(f"  unknown rather than a concrete value.")
print()
print(f"  For comparison:")
print(f"    TICKS=20 -> 2^20 = {2**20:>10,} sequences")
print(f"    TICKS=30 -> 2^30 = {2**30:>10,} sequences")
print(f"    TICKS=64 -> 2^64 = {2**64:>10,} sequences  (exhaustive testing hopeless)")
print()
print(f"  Z3's symbolic reasoning scales to these sizes because it never")
print(f"  enumerates sequences — it manipulates the constraints algebraically.")
print()

# Manually confirm one concrete trace
print(f"  Manual check for requests = [1, 1, 0, 1, 1] (bucket starts full):")
print(f"  {'tick':>4}  {'tokens_before':>13}  {'request':>7}  "
      f"{'accepted':>8}  {'tokens_after':>12}")
print(f"  {'-' * 52}")
tks = CAPACITY
reqs = [1, 1, 0, 1, 1]
total_manual = 0
for t in range(TICKS):
    refilled = min(tks + REFILL, CAPACITY)
    acc = 1 if (reqs[t] == 1 and refilled > 0) else 0
    tks_next = refilled - acc
    total_manual += acc
    print(f"  {t:>4}  {tks:>13}  {reqs[t]:>7}  {acc:>8}  {tks_next:>12}")
    tks = tks_next
print(f"\n  Total accepted = {total_manual}  (bound = {SAFETY_BOUND})")
print(f"\n  The Part 1 proof guarantees this holds for all {2**TICKS} patterns.")
