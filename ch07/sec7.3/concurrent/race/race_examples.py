"""
race_examples.py
================
Four examples illustrating shared-counter concurrency bugs and fixes
using the ToyVM from vm.py.

  Example 1 - Raw race condition      (no sync, lost updates)
  Example 2 - Fixed with LOCK         (mutex guards critical section)
  Example 3 - Fixed with SEMAPHORE(1) (binary semaphore, same effect)
  Example 4 - Fixed with ATOMIC       (indivisible AtomicCounter)

Run:
    python race_examples.py
"""

from vm import ToyVM


# ─── worker instruction sets ──────────────────────────────────────────────────

def make_worker_unsafe(n):
    """Increment global 'counter_value' n times without any synchronisation.

    PC  instruction
    0   PUSH 0
    1   STORE i
    2   LOAD i           ← loop head
    3   PUSH n
    4   SUB              → i - n
    5   JUMP_IF 17       → exit if i >= n
    6   LOAD counter_value
    7   PUSH 1
    8   ADD              ← read-modify-write split across 3 instructions: RACE HERE
    9   GLOBAL_STORE counter_value
    10  PUSH 1
    11  SLEEP            → force context-switch opportunity
    12  LOAD i
    13  PUSH 1
    14  ADD
    15  STORE i
    16  JUMP 2
    17  NOP              ← exit
    """
    return [
        ("PUSH", 0),                         #  0
        ("STORE", "i"),                      #  1
        ("LOAD", "i"),                       #  2
        ("PUSH", n),                         #  3
        ("SUB",),                            #  4
        ("JUMP_IF", 17),                     #  5
        ("LOAD", "counter_value"),           #  6
        ("PUSH", 1),                         #  7
        ("ADD",),                            #  8
        ("GLOBAL_STORE", "counter_value"),   #  9
        ("PUSH", 1),                         # 10
        ("SLEEP",),                          # 11
        ("LOAD", "i"),                       # 12
        ("PUSH", 1),                         # 13
        ("ADD",),                            # 14
        ("STORE", "i"),                      # 15
        ("JUMP", 2),                         # 16
        ("NOP",),                            # 17
    ]


def make_worker_locked(n):
    """Same loop protected by a mutex stored in global 'the_lock'.

    PC  instruction
    0   PUSH 0
    1   STORE i
    2   LOAD i           ← loop head
    3   PUSH n
    4   SUB
    5   JUMP_IF 21       → exit
    6   LOAD the_lock    ← acquire mutex
    7   LOCK_ACQUIRE
    8   LOAD counter_value   ← critical section
    9   PUSH 1
    10  ADD
    11  GLOBAL_STORE counter_value
    12  LOAD the_lock    ← release mutex
    13  LOCK_RELEASE
    14  PUSH 1
    15  SLEEP
    16  LOAD i
    17  PUSH 1
    18  ADD
    19  STORE i
    20  JUMP 2
    21  NOP
    """
    return [
        ("PUSH", 0),                         #  0
        ("STORE", "i"),                      #  1
        ("LOAD", "i"),                       #  2
        ("PUSH", n),                         #  3
        ("SUB",),                            #  4
        ("JUMP_IF", 21),                     #  5
        ("LOAD", "the_lock"),                #  6
        ("LOCK_ACQUIRE",),                   #  7
        ("LOAD", "counter_value"),           #  8
        ("PUSH", 1),                         #  9
        ("ADD",),                            # 10
        ("GLOBAL_STORE", "counter_value"),   # 11
        ("LOAD", "the_lock"),                # 12
        ("LOCK_RELEASE",),                   # 13
        ("PUSH", 1),                         # 14
        ("SLEEP",),                          # 15
        ("LOAD", "i"),                       # 16
        ("PUSH", 1),                         # 17
        ("ADD",),                            # 18
        ("STORE", "i"),                      # 19
        ("JUMP", 2),                         # 20
        ("NOP",),                            # 21
    ]


def make_worker_semaphore(n):
    """Same loop protected by a binary semaphore stored in global 'the_sem'."""
    return [
        ("PUSH", 0),                         #  0
        ("STORE", "i"),                      #  1
        ("LOAD", "i"),                       #  2
        ("PUSH", n),                         #  3
        ("SUB",),                            #  4
        ("JUMP_IF", 21),                     #  5
        ("LOAD", "the_sem"),                 #  6
        ("SEMAPHORE_ACQUIRE",),              #  7
        ("LOAD", "counter_value"),           #  8
        ("PUSH", 1),                         #  9
        ("ADD",),                            # 10
        ("GLOBAL_STORE", "counter_value"),   # 11
        ("LOAD", "the_sem"),                 # 12
        ("SEMAPHORE_RELEASE",),              # 13
        ("PUSH", 1),                         # 14
        ("SLEEP",),                          # 15
        ("LOAD", "i"),                       # 16
        ("PUSH", 1),                         # 17
        ("ADD",),                            # 18
        ("STORE", "i"),                      # 19
        ("JUMP", 2),                         # 20
        ("NOP",),                            # 21
    ]


def make_worker_atomic(n):
    """Loop using ATOMIC_INCREMENT on global 'the_atomic' — no lock needed.

    PC  instruction
    0   PUSH 0
    1   STORE i
    2   LOAD i           ← loop head
    3   PUSH n
    4   SUB
    5   JUMP_IF 14       → exit
    6   LOAD the_atomic
    7   ATOMIC_INCREMENT → single indivisible step; pushes new value
    8   POP              (discard return value)
    9   LOAD i
    10  PUSH 1
    11  ADD
    12  STORE i
    13  JUMP 2
    14  NOP
    """
    return [
        ("PUSH", 0),                         #  0
        ("STORE", "i"),                      #  1
        ("LOAD", "i"),                       #  2
        ("PUSH", n),                         #  3
        ("SUB",),                            #  4
        ("JUMP_IF", 14),                     #  5
        ("LOAD", "the_atomic"),              #  6
        ("ATOMIC_INCREMENT",),               #  7
        ("POP",),                            #  8
        ("LOAD", "i"),                       #  9
        ("PUSH", 1),                         # 10
        ("ADD",),                            # 11
        ("STORE", "i"),                      # 12
        ("JUMP", 2),                         # 13
        ("NOP",),                            # 14
    ]


# ─── report helper ───────────────────────────────────────────────────────────

def report_instructions(expected):
    """
    Return a list of instructions that:
      - assumes the counter value is on the stack
      - prints it
      - prints CORRECT or WRONG

    JUMP_IF in vm.py fires when top-of-stack >= 0, then does pc = target - 1.
    After the instruction step() does pc += 1 → effective jump to `target`.

    Layout (indices relative to where these are appended):
      +0  DUP
      +1  PRINT "Final counter value: {}"
      +2  PUSH expected
      +3  SUB                     → counter - expected
      +4  JUMP_IF base+8          → if >=0 (i.e. ==expected) jump to CORRECT
      +5  PRINT "WRONG..."
      +6  JUMP base+9             → jump past CORRECT to POP
      +7  ← gap (target of JUMP_IF is +8, but we define it per absolute index)
      ...

    Caller must pass `base` = the absolute index of the DUP instruction.
    """
    # We don't use this helper; we inline the report block in each example
    # to keep the PC arithmetic explicit and reviewable.
    raise NotImplementedError


# ─── examples ────────────────────────────────────────────────────────────────

def example_1_race_condition(n=20, debug=False):
    """
    Two unsynchronised workers race on a shared counter.

    Main thread layout:
     0  PUSH 0
     1  GLOBAL_STORE counter_value
     2  PUSH 0
     3  THREAD_CREATE [worker]    → stack: [name0]
     4  DUP
     5  GLOBAL_STORE t0
     6  POP
     7  PUSH 0
     8  THREAD_CREATE [worker]    → stack: [name1]
     9  DUP
    10  GLOBAL_STORE t1
    11  POP
    12  LOAD t0
    13  THREAD_JOIN
    14  LOAD t1
    15  THREAD_JOIN
    16  LOAD counter_value
    17  DUP
    18  PRINT "Final counter value: {}"
    19  PUSH expected
    20  SUB                        → counter - expected
    21  JUMP_IF 24                 → if >=0 → CORRECT (index 24)
    22  PRINT "WRONG..."
    23  JUMP 25                    → skip to POP
    24  PRINT "CORRECT..."
    25  POP
    """
    worker = make_worker_unsafe(n)
    expected = n * 2

    main = [
        ("PUSH", 0),                          #  0
        ("GLOBAL_STORE", "counter_value"),    #  1
        ("PUSH", 0),                          #  2
        ("THREAD_CREATE", [worker]),          #  3
        ("DUP",),                             #  4
        ("GLOBAL_STORE", "t0"),               #  5
        ("POP",),                             #  6
        ("PUSH", 0),                          #  7
        ("THREAD_CREATE", [worker]),          #  8
        ("DUP",),                             #  9
        ("GLOBAL_STORE", "t1"),               # 10
        ("POP",),                             # 11
        ("LOAD", "t0"),                       # 12
        ("THREAD_JOIN",),                     # 13
        ("LOAD", "t1"),                       # 14
        ("THREAD_JOIN",),                     # 15
        ("LOAD", "counter_value"),            # 16
        ("DUP",),                             # 17
        ("PRINT", "Final counter value: {}"), # 18
        ("PUSH", expected),                   # 19
        ("SUB",),                             # 20
        ("JUMP_IF", 24),                      # 21 → PC 24 if >=0
        ("PRINT", f"WRONG  — race condition! Expected {expected}, got less."), # 22
        ("JUMP", 25),                         # 23 → PC 25
        ("PRINT", "CORRECT — lucky, no interleaving this run!"), # 24
        ("POP",),                             # 25
    ]

    print("\n" + "="*60)
    print("  Example 1: Raw Race Condition (no synchronisation)")
    print("="*60)
    vm = ToyVM()
    vm.scheduler_type = "random"   # random scheduler makes the race visible
    vm.create_thread(main, "main", priority=1)
    vm.run(debug=debug)


def example_2_lock_fix(n=20, debug=False):
    """
    Workers protect the counter with a mutex.

    Extra setup in main (before spawning workers):
      LOCK_CREATE  → stack: [lock_name]
      DUP
      GLOBAL_STORE the_lock
      POP
    """
    worker = make_worker_locked(n)
    expected = n * 2

    main = [
        ("PUSH", 0),                          #  0
        ("GLOBAL_STORE", "counter_value"),    #  1
        ("LOCK_CREATE",),                     #  2  → [lock_name]
        ("DUP",),                             #  3
        ("GLOBAL_STORE", "the_lock"),         #  4
        ("POP",),                             #  5
        ("PUSH", 0),                          #  6
        ("THREAD_CREATE", [worker]),          #  7
        ("DUP",),                             #  8
        ("GLOBAL_STORE", "t0"),               #  9
        ("POP",),                             # 10
        ("PUSH", 0),                          # 11
        ("THREAD_CREATE", [worker]),          # 12
        ("DUP",),                             # 13
        ("GLOBAL_STORE", "t1"),               # 14
        ("POP",),                             # 15
        ("LOAD", "t0"),                       # 16
        ("THREAD_JOIN",),                     # 17
        ("LOAD", "t1"),                       # 18
        ("THREAD_JOIN",),                     # 19
        ("LOAD", "counter_value"),            # 20
        ("DUP",),                             # 21
        ("PRINT", "Final counter value: {}"), # 22
        ("PUSH", expected),                   # 23
        ("SUB",),                             # 24
        ("JUMP_IF", 28),                      # 25 → 28 if >=0
        ("PRINT", f"WRONG  — unexpected! Expected {expected}."), # 26
        ("JUMP", 29),                         # 27
        ("PRINT", "CORRECT — mutex prevented the race condition!"), # 28
        ("POP",),                             # 29
    ]

    print("\n" + "="*60)
    print("  Example 2: Fixed with LOCK (mutex)")
    print("="*60)
    vm = ToyVM()
    vm.create_thread(main, "main", priority=1)
    vm.run(debug=debug)


def example_3_semaphore_fix(n=20, debug=False):
    """
    Workers protect the counter with a binary semaphore (initial count = 1).
    A semaphore(1) behaves like a mutex for mutual exclusion.
    """
    worker = make_worker_semaphore(n)
    expected = n * 2

    main = [
        ("PUSH", 0),                          #  0
        ("GLOBAL_STORE", "counter_value"),    #  1
        ("PUSH", 1),                          #  2  initial permits = 1
        ("SEMAPHORE_CREATE",),               #  3  → [sem_name]
        ("DUP",),                             #  4
        ("GLOBAL_STORE", "the_sem"),          #  5
        ("POP",),                             #  6
        ("PUSH", 0),                          #  7
        ("THREAD_CREATE", [worker]),          #  8
        ("DUP",),                             #  9
        ("GLOBAL_STORE", "t0"),               # 10
        ("POP",),                             # 11
        ("PUSH", 0),                          # 12
        ("THREAD_CREATE", [worker]),          # 13
        ("DUP",),                             # 14
        ("GLOBAL_STORE", "t1"),               # 15
        ("POP",),                             # 16
        ("LOAD", "t0"),                       # 17
        ("THREAD_JOIN",),                     # 18
        ("LOAD", "t1"),                       # 19
        ("THREAD_JOIN",),                     # 20
        ("LOAD", "counter_value"),            # 21
        ("DUP",),                             # 22
        ("PRINT", "Final counter value: {}"), # 23
        ("PUSH", expected),                   # 24
        ("SUB",),                             # 25
        ("JUMP_IF", 29),                      # 26 → 29 if >=0
        ("PRINT", f"WRONG  — unexpected! Expected {expected}."), # 27
        ("JUMP", 30),                         # 28
        ("PRINT", "CORRECT — semaphore(1) prevented the race condition!"), # 29
        ("POP",),                             # 30
    ]

    print("\n" + "="*60)
    print("  Example 3: Fixed with SEMAPHORE(1) (binary semaphore)")
    print("="*60)
    vm = ToyVM()
    vm.create_thread(main, "main", priority=1)
    vm.run(debug=debug)


def example_4_atomic_fix(n=20, debug=False):
    """
    Workers use ATOMIC_INCREMENT — a single, indivisible VM instruction.
    No explicit lock is needed because the VM guarantees the operation
    completes without any scheduler interleaving.
    """
    worker = make_worker_atomic(n)
    expected = n * 2

    main = [
        ("PUSH", 0),                          #  0  initial value
        ("ATOMIC_CREATE",),                   #  1  → [counter_name]
        ("DUP",),                             #  2
        ("GLOBAL_STORE", "the_atomic"),       #  3
        ("POP",),                             #  4
        ("PUSH", 0),                          #  5
        ("THREAD_CREATE", [worker]),          #  6
        ("DUP",),                             #  7
        ("GLOBAL_STORE", "t0"),               #  8
        ("POP",),                             #  9
        ("PUSH", 0),                          # 10
        ("THREAD_CREATE", [worker]),          # 11
        ("DUP",),                             # 12
        ("GLOBAL_STORE", "t1"),               # 13
        ("POP",),                             # 14
        ("LOAD", "t0"),                       # 15
        ("THREAD_JOIN",),                     # 16
        ("LOAD", "t1"),                       # 17
        ("THREAD_JOIN",),                     # 18
        ("LOAD", "the_atomic"),               # 19
        ("ATOMIC_GET",),                      # 20  → [int_value]
        ("DUP",),                             # 21
        ("PRINT", "Final counter value: {}"), # 22
        ("PUSH", expected),                   # 23
        ("SUB",),                             # 24
        ("JUMP_IF", 28),                      # 25 → 28 if >=0
        ("PRINT", f"WRONG  — unexpected! Expected {expected}."), # 26
        ("JUMP", 29),                         # 27
        ("PRINT", "CORRECT — ATOMIC_INCREMENT prevented the race condition!"), # 28
        ("POP",),                             # 29
    ]

    print("\n" + "="*60)
    print("  Example 4: Fixed with ATOMIC_INCREMENT")
    print("="*60)
    vm = ToyVM()
    vm.create_thread(main, "main", priority=1)
    vm.run(debug=debug)


# ─── entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    N = 20      # loop iterations per worker; raise to see more frequent races in Ex 1
    DEBUG = False

    print("""
ToyVM Concurrency Demo
======================
Two worker threads each increment a shared counter N={N} times.

Without synchronisation the round-robin scheduler interleaves
the read-modify-write at the individual instruction level, causing
"lost updates" — the final counter is less than 2*N.

The three fixed examples show the standard remedies available in the VM:
  • LOCK     — mutual exclusion via mutex
  • SEMAPHORE(1) — binary semaphore (morally equivalent to a mutex)
  • ATOMIC_INCREMENT — indivisible operation, no lock needed
""".format(N=N))

    example_1_race_condition(n=N, debug=DEBUG)
    example_2_lock_fix(n=N, debug=DEBUG)
    example_3_semaphore_fix(n=N, debug=DEBUG)
    example_4_atomic_fix(n=N, debug=DEBUG)
