
## Fuzz and Mutate Testers

> Once I remember discussing testing approaches, and my preference was formal verification rather than conventional testing. The reply was that we could always do "grobian testning", which was very much akin to what we would now call fuzzing or mutation testing. The Swedish term "grobian testning" translates to "rough testing" or "crude testing" in English. It implies an informal, coarse, and imprecise approach--essentially quick-and-dirty tests to catch obvious issues rather than detailed, rigorous testing.

> This exchange took place in the mid-1980s, when we did not yet have formal definitions of, or at least were not aware of, established testing frameworks. My reply at the time was: "Well, that would only show the presence of errors, not their absence."

The common concepts of the C and Python code:
- Stack machine with bytecode (each instruction is a single byte, some followed by immediate operand bytes).
- Opcodes:
    - 0x01 PUSH <int32> — push 32-bit signed immediate
    - 0x02 ADD — pop a,b push (a+b)
    - 0x03 SUB — pop a,b push (a-b)
    - 0x04 MUL — pop a,b push (a*b)
    - 0x05 DIV — pop a,b push (a/b) with division-by-zero handled
    - 0x06 DUP — duplicate top
    - 0x07 POP — pop and discard
    - 0x08 HALT — stop and return success
    - 0x09 PRINT — pop and print value (to collect outputs)
    - 0x0A JZ <offset8> — pop top, if zero jump forward by offset
    - 0x0B JNZ <offset8> — pop top, if non-zero jump forward by offset
    - 0xFF INVALID — treated as an invalid opcode (VM will report crash)
- VM checks for stack underflow/overflow and invalid memory access and returns error codes instead of crashing.
  Fuzzer looks for non-success return codes and unexpected behaviours.

Testing strategies:

- *Fuzz*: generate random bytecode of varying lengths and run it; record crashes, hangs (fixed instruction limit),
  and unusual outputs.

- *Mutation*: start from a small hand-written seed program, create mutations (bit flips, random opcode replacement,
  byte insertion/deletion), run mutated programs and compare outputs or error codes to the seed. Track whether
  mutation is detected (i.e., an invariant broken)--here the basic invariant is determinism (same program -->
  same output) and sanity (no undefined behaviour). You can extend with stronger oracles.


### 1. Fuzz Testing (a.k.a. "Fuzzing")

*Idea*:
Fuzz testing means feeding a program with lots of random, unexpected, or malformed inputs to see if it crashes,
hangs, or behaves incorrectly. It’s a way to shake the box and see what falls out.

Why it can be useful:
- Finds edge cases you didn’t think of.
- Reveals crashes due to bad input validation.
- Works without needing deep knowledge of the program’s internals.

How it works:
1. Decide what "input" means for your program. For our VM, input = the bytecode program it will run.
2. Generate many random inputs.
    - Could be truly random bytes.
    - Could be "semi-random" but valid-looking instructions.
3. Run the program with each input.
4. Watch for:
    - Crashes (segfault, exceptions, fatal errors)
    - Infinite loops (timeout)
    - Unexpected outputs (compared to known-correct behaviour)

Example with our VM:
- Generate a random sequence of opcodes like:

```
0x01 00 00 00 05 0x02 0x09 0x08
```
(Push 5, add something random, print, halt)

- See if the VM:
- Returns an error (invalid opcode, division by zero)
- Hangs (loop forever)
- Produces weird output

In short: *Fuzzing is like throwing random junk at your program and seeing what breaks.*



### 2. Mutation Testing

*Idea*:
Mutation testing starts with a valid, working input (a "seed"), then makes small changes
("mutations") to create new inputs. You run the program with these mutated inputs to see
if the behaviour changes unexpectedly.

Why it’s useful:
- Checks that your program really handles small changes safely.
- Can systematically explore variations without full randomness.
- Often used to test test suites--if your tests don’t catch the mutant’s bad behaviour,
  they might be too weak.

How it works:
1. Start with a seed input that you know works.
    - For our VM: a bytecode program that prints 35 and halts.
2. Create mutations:
    - Flip a random bit in the program.
    - Replace one opcode with another.
    - Insert or delete a byte.
3. Run the mutated program.
4. Compare results to the seed’s results:
    - If it crashes, that’s interesting.
    - If it gives a different result without crashing, maybe that’s expected (but maybe not!).
    - If it does something dangerous, that’s a bug.

Example with our VM:
- Seed program:

```
PUSH 3
PUSH 4
ADD
PUSH 5
MUL
PRINT
HALT
```

- Mutation:
- Flip a bit in the ADD opcode, turning it into DIV.
- Now maybe we get division by zero — the VM should handle it safely.
- Mutation testing lets us explore small input changes instead of starting from complete randomness.

In short: *Mutation testing is like starting from something good and poking it a bit to see if it still works.*


### Difference Table

| Feature            | Fuzz Testing                           | Mutation Testing                       |
|--------------------|----------------------------------------|----------------------------------------|
| Input source       | Fully random or semi-random            | Start from known-good input (seed)     |
| Goal               | Explore *all sorts* of weird behaviour | See if small changes cause failures    |
| Typical output     | Crash reports, hangs, unexpected runs  | Behaviour diffs from original seed     |
| Exploration style  | Wide, chaotic coverage                 | Focused, systematic variations         |
| Good for ..        | Finding "unknown unknowns"             | Testing robustness & test coverage     |
