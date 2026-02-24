"""
atomic_demo.py
==============
Demonstrates atomic counters using the ToyVM (toyvm.py).

Two experiments run back-to-back:

  1. UNSAFE    two threads increment a shared global using three separate
               instructions (LOAD / ADD / GLOBAL_STORE).  Because those
               are three steps, the scheduler can interleave them and
               "lose" increments → final value is typically < 100.

  2. SAFE      same setup, but each increment is a single ATOMIC_INCREMENT
               instruction.  The VM executes it as one indivisible step,
               so every increment is counted → final value is always 100.

Usage:
    python atomic_demo.py        # toyvm.py must be in the same directory
"""

from vm import ToyVM



# Experiment 1 – UNSAFE: plain read-modify-write (race condition)

def run_unsafe_counter():
    """
    Each of two worker threads loops 50 times and increments the shared
    global 'counter_value' with three separate instructions:

        LOAD  counter_value    ← read               (step A)
        PUSH 1 / ADD           ← compute new value  (step B)
        GLOBAL_STORE           ← write back         (step C)

    The scheduler may switch threads between any two of those steps.
    When it switches between A and C both threads hold the same stale
    value, both write stale+1, and one increment silently disappears.
    """
    vm = ToyVM()

    # Worker
    # PC  0- 1  i = 0
    # PC  2- 5  loop guard  (exit to PC 15 when i >= 50)
    # PC  6- 9  UNSAFE three-step increment
    # PC 10-13  i += 1
    # PC 14     jump back to loop guard
    # PC 15     NOP (loop exit label)
    worker_unsafe = [
        ("PUSH", 0),                        # PC  0   i = 0
        ("STORE", "i"),                     # PC  1

        ("LOAD", "i"),                      # PC  2   loop guard
        ("PUSH", 50),                       # PC  3
        ("SUB",),                           # PC  4   i - 50
        ("JUMP_IF", 15),                    # PC  5   exit if (i - 50) >= 0

        ("LOAD", "counter_value"),          # PC  6   ← READ   (race window opens here)
        ("PUSH", 1),                        # PC  7
        ("ADD",),                           # PC  8   ← COMPUTE
        ("GLOBAL_STORE", "counter_value"),  # PC  9   ← WRITE  (race window closes here)

        ("LOAD", "i"),                      # PC 10
        ("PUSH", 1),                        # PC 11
        ("ADD",),                           # PC 12
        ("STORE", "i"),                     # PC 13

        ("JUMP", 2),                        # PC 14   back to loop guard
        ("NOP",),                           # PC 15   exit
    ]

    # Main
    # PC  0- 1  counter_value = 0
    # PC  2- 5  spawn thread-0 and thread-1
    # PC  6- 9  join both threads
    # PC 10-12  load and print final counter value
    # PC 13-19  check correctness, print verdict
    #
    # JUMP_IF semantics: pops TOS; jumps when TOS >= 0.
    # After (counter - 100): jumps when counter >= 100 (correct result).
    # Falls through to the failure message only when counter < 100.
    # JUMP_IF 17 at PC 15 → lands at PC 17 (the JUMP instruction).
    # JUMP 18   at PC 17 → skips the failure message, lands at PC 18.
    main_unsafe = [
        ("PUSH", 0),                              # PC  0   counter_value = 0
        ("GLOBAL_STORE", "counter_value"),        # PC  1

        ("PUSH", 0),                              # PC  2   spawn thread-0
        ("THREAD_CREATE", [worker_unsafe]),       # PC  3
        ("PUSH", 0),                              # PC  4   spawn thread-1
        ("THREAD_CREATE", [worker_unsafe]),       # PC  5

        ("LOAD", "thread-0"),                     # PC  6
        ("THREAD_JOIN",),                         # PC  7
        ("LOAD", "thread-1"),                     # PC  8
        ("THREAD_JOIN",),                         # PC  9

        ("LOAD", "counter_value"),                # PC 10
        ("DUP",),                                 # PC 11   keep copy for PRINT
        ("PRINT", "UNSAFE final counter = {}"),   # PC 12   (prints TOS; doesn't pop)

        ("PUSH", 100),                            # PC 13
        ("SUB",),                                 # PC 14   counter - 100
        ("JUMP_IF", 17),                          # PC 15   jump to PC 17 if counter >= 100
        ("PRINT", "  ✗ Race condition – increments were lost"), # PC 16  (failure)
        ("JUMP", 18),                             # PC 17   skip success message
        ("PRINT", "  ✓ No race this run (lucky scheduling)"),   # PC 18  (success)
        ("POP",),                                 # PC 19   clean stack
    ]

    vm.create_thread(main_unsafe, "main", priority=1)
    print("\n─── UNSAFE (read-modify-write, race condition) ───")
    vm.run(debug=False)

    # Python-side summary (independent of in-VM branch logic)
    final = vm.globals.get("counter_value", "?")
    expected = 100
    if isinstance(final, int):
        lost = expected - final
        verdict = "✓ no race this run (lucky)" if lost == 0 else f"✗ lost {lost} increment(s)"
        print(f"    Expected {expected},  got {final}  →  {verdict}")



# Experiment 2 – SAFE: ATOMIC_INCREMENT (no race condition)

def run_safe_counter():
    """
    Same two workers, same 50 iterations each, but each increment is a
    single ATOMIC_INCREMENT instruction instead of three separate steps.

    From the scheduler's perspective ATOMIC_INCREMENT is one atomic step 
    no other thread can be scheduled between the internal read and write.
    Every increment lands, giving exactly 100 every single run.
    """
    vm = ToyVM()

    # Worker
    # PC  0- 1  i = 0
    # PC  2- 5  loop guard  (exit to PC 14 when i >= 50)
    # PC  6- 8  ATOMIC_INCREMENT  (one indivisible step)
    # PC  9-12  i += 1
    # PC 13     jump back to loop guard
    # PC 14     NOP (loop exit label)
    worker_safe = [
        ("PUSH", 0),                        # PC  0   i = 0
        ("STORE", "i"),                     # PC  1

        ("LOAD", "i"),                      # PC  2   loop guard
        ("PUSH", 50),                       # PC  3
        ("SUB",),                           # PC  4   i - 50
        ("JUMP_IF", 14),                    # PC  5   exit if (i - 50) >= 0

        ("LOAD", "atomic_ctr"),             # PC  6   push counter handle onto stack
        ("ATOMIC_INCREMENT",),              # PC  7   ← ONE indivisible read-add-write
        ("POP",),                           # PC  8   discard returned new value

        ("LOAD", "i"),                      # PC  9
        ("PUSH", 1),                        # PC 10
        ("ADD",),                           # PC 11
        ("STORE", "i"),                     # PC 12

        ("JUMP", 2),                        # PC 13   back to loop guard
        ("NOP",),                           # PC 14   exit
    ]

    # Main
    # PC  0- 2  create atomic counter, store handle globally
    # PC  3- 6  spawn thread-0 and thread-1
    # PC  7-10  join both threads
    # PC 11-14  read final value via ATOMIC_GET, print
    # PC 15-21  check correctness, print verdict
    #
    # JUMP_IF 19 at PC 17: jumps to PC 19 (the JUMP instruction) when correct.
    # JUMP 20    at PC 19: jumps to PC 20 (the success PRINT).
    # Failure path: falls through PC 17 → executes PC 18 (failure PRINT).
    main_safe = [
        ("PUSH", 0),                              # PC  0   initial counter value
        ("ATOMIC_CREATE",),                       # PC  1   creates counter, pushes handle
        ("GLOBAL_STORE", "atomic_ctr"),           # PC  2   store handle globally

        ("PUSH", 0),                              # PC  3   spawn thread-0
        ("THREAD_CREATE", [worker_safe]),         # PC  4
        ("PUSH", 0),                              # PC  5   spawn thread-1
        ("THREAD_CREATE", [worker_safe]),         # PC  6

        ("LOAD", "thread-0"),                     # PC  7
        ("THREAD_JOIN",),                         # PC  8
        ("LOAD", "thread-1"),                     # PC  9
        ("THREAD_JOIN",),                         # PC 10

        ("LOAD", "atomic_ctr"),                   # PC 11
        ("ATOMIC_GET",),                          # PC 12   read final value
        ("DUP",),                                 # PC 13   keep copy for PRINT
        ("PRINT", "SAFE   final counter = {}"),   # PC 14   (prints TOS; doesn't pop)

        ("PUSH", 100),                            # PC 15
        ("SUB",),                                 # PC 16   counter - 100
        ("JUMP_IF", 19),                          # PC 17   jump to PC 19 if counter >= 100
        ("PRINT", "  ✗ BUG – atomic counter gave wrong result"), # PC 18  (failure)
        ("JUMP", 20),                             # PC 19   skip to PC 20 (success)
        ("PRINT", "  ✓ Correct – all 100 increments recorded"),  # PC 20  (success)
        ("POP",),                                 # PC 21   clean stack
    ]

    vm.create_thread(main_safe, "main", priority=1)
    print("\n─── SAFE (ATOMIC_INCREMENT, no race condition) ───")
    vm.run(debug=False)

    # Python-side summary
    handle = vm.globals.get("atomic_ctr")
    final = vm.atomic_counters[handle].get() if handle and handle in vm.atomic_counters else "?"
    expected = 100
    if isinstance(final, int):
        verdict = "✓ all increments recorded" if final == expected else f"✗ unexpected result"
        print(f"    Expected {expected},  got {final}  →  {verdict}")



# Entry point

if __name__ == "__main__":
    print("  ToyVM: Atomic Counter Demo")
    print("  2 threads x 50 increments = 100 expected\n\n")

    run_unsafe_counter()
    run_safe_counter()

    print()
    print()
    print("  NOTE")
    print()
    print("  UNSAFE  LOAD + ADD + GLOBAL_STORE = 3 instructions.")
    print("  The scheduler can switch threads between any two of them,")
    print("  causing both threads to read the same stale value and")
    print("  both write stale+1  →  one increment silently disappears.")
    print()
    print("  SAFE    ATOMIC_INCREMENT = 1 indivisible instruction.")
    print("  No thread can interleave inside the read-add-write cycle,")
    print("  so every increment is always counted correctly.")
    print()

