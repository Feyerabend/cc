
## The Setun and DSSP: A Conceptual Emulator

Connecting to the previous chapter on negative numbers, and an elegant solution
presented by the Soviet computer Setun and Setut-70, we here introduce a
simple emulator.

### Historical background

In 1956 a small group at Moscow State University, led by Nikolay Brusentsov,
set out to build a computer that was cheap, simple, and suitable for university
work. The decision they made was unusual: instead of the binary number system
that every other machine of the era used, they would use *balanced ternary*.
A number system whose digits are -1, 0, and +1.

The result, completed in 1958, was the *Setun*. It was the first working
balanced ternary computer ever built, and it turned out to be remarkably
practical. The machines ran reliably in climatic extremes from Yakutsk to
Ashkhabad; one unit at MSU operated for seventeen years and needed only three
element replacements in its entire life. About fifty were produced before
politics and the preference of Soviet planners for binary machines ended
production in 1965.

A decade later Brusentsov built the *Setun-70*, a second machine that
explored a different idea: a two-stack architecture designed explicitly for
structured programming. One stack held data operands; the other held return
addresses for procedure calls. The instruction set was 81 operations: 27
basic, 27 auxiliary, 27 user-programmable. All were encoded in 6-trit *trytes*,
the smallest addressable unit. Programs were written in reverse Polish notation
(the Soviets called it "Poliz"), which maps naturally onto a stack machine.
The Setun-70 inspired *DSSP*, a Dialogue System of Structured Programming that
was Brusentsov's maybe Forth-like language: a system in which a programmer
interactively defined new words from old ones at a terminal.

Donald Knuth later called balanced ternary "perhaps the most beautiful number
system", and Claude Shannon had analysed its advantages as early as 1950. That
a working computer was built on this foundation in 1958--by eight graduate
students and twelve technicians, in under two years--is genuinely remarkable.



### What this emulator is

This is not a faithful hardware reconstruction. The original Setun-70 opcode
table, the exact encoding of its 81 instructions, and the internal layout of
DSSP were never fully published in English. What we have is the paper by
Brusentsov and Ramil Alvarez (2011) and Knuth's notes, which describe the
architecture in broad strokes.

What this emulator *is* is an *illustration of the concepts*: a working
balanced ternary machine with a two-stack architecture, running a Forth-like
interpreter whose dictionary and outer interpreter loop live as tryte programs
inside the virtual machine itself. The spirit is authentic even where the
letter cannot be.



### How the layers fit together

```
-------------------------------------------------------
|                   DSSP Forth REPL                   |
|  : square dup * ;     7 square .     3 begin ...    |
-------------------------------------------------------
                         |  words looked up in
                         v
-------------------------------------------------------
|              Dictionary (in VM memory)              |
|  header: link | flags | namelen | name | body...    |
|  body: CALL CALL ... RET   (direct threading)       |
-------------------------------------------------------
                         |  compiled to / executed by
                         v
-------------------------------------------------------
|           Setun-70 virtual machine (C)              |
|  2187-tryte memory  *  data stack  *  return stack  |
|  81 opcodes  *  2-tryte addressing                  |
-------------------------------------------------------
                         |  built on
                         v
-------------------------------------------------------
|           Balanced ternary primitives (C)           |
|  trit_t  *  tryte_t  *  int_to_tryte  *  trit_add   |
-------------------------------------------------------
```

#### Layer 1: balanced ternary primitives

The foundation is a C implementation of balanced ternary arithmetic. A `trit`
is an `int8_t` holding -1, 0, or +1. A `tryte` is six trits packed into an
array, representing a value in the range -364 to +364. Conversion to and from
ordinary integers, addition, multiplication, and the uniquely ternary
operations--`sgn`, `abs`, `not` (negation of each trit), `and` (min),
`or` (max)--all live here.

#### Layer 2: the Setun-70 virtual machine

The VM has a flat memory of 2187 trytes (27 pages x 81 trytes--the Setun-70
used base-3 everywhere, and 3^7 = 2187). It has two stacks: a data stack and a
return stack, each 64 entries deep. The instruction set follows the paper's
broad description: arithmetic, comparisons, stack manipulation, memory load and
store, unconditional and conditional jumps (JZERO, JPOS, JNEG--one for each
possible sign of a balanced ternary value), CALL and RET.

All addresses are two trytes wide. A single tryte can only hold values up to
364, so addresses above that must be split as `lo = addr % 243` and
`hi = addr / 243`, with `addr = lo + hi x 243`. This turns out to be the
trickiest constraint in the whole project: every jump target, every compiled
CALL, every address pushed onto the data stack had to be treated as a two-part
value to avoid silent wrapping.

The VM is deliberately simple. Each call to `setun70_step()` decodes and
executes one instruction. The whole machine state--memory, both stacks, the
program counter--lives in a single `setun70_t` struct.

#### Layer 3: the dictionary and direct threading

DSSP uses *direct threading*. The Setun-70's own CALL and RET instructions
*are* the inner interpreter. A colon definition such as `: square dup * ;`
compiles to nothing more than:

```
CALL <dup>   CALL <*>   RET
```

where `<dup>` and `<*>` are the 2-tryte addresses of those primitives' bodies
in VM memory. There is no separate "next pointer" or interpreter loop to thread
through--the machine's natural subroutine mechanism handles it.

Primitive words (`+`, `dup`, `swap`, `if`, `begin`, ...) are written as short
native Setun-70 instruction sequences terminated by RET and stored directly in
VM memory at bootstrap time. The kernel--65 primitives plus the outer
interpreter loop--occupies about 1320 trytes, leaving roughly 860 trytes free
for user definitions.

A dictionary header looks like this in memory:

```
[ link_lo ][ link_hi ][ flags ][ namelen ][ name bytes... ]
                                                            ^ CFA starts here
```

`link_lo + link_hi x 243` is the address of the previous word, forming a
linked list. The CFA (code field address) is the first instruction of the word
body, immediately following the name.

#### Layer 4: the outer interpreter

The outer interpreter loop is itself a Setun-70 program living in VM memory.
It scans the input line token by token, looks each token up in the dictionary,
and either executes it (interpret mode) or compiles a CALL to it (compile mode
after `:`). If a token is not a word it tries to parse it as a number.

A small set of *host calls* (auxiliary opcodes 35-52) bridge the VM to C helper
functions for things that would be painful in pure Setun-70 code--scanning
whitespace, comparing strings for dictionary lookup, formatting output. These
play the role of system calls: the real Setun-70 had hardware I/O primitives
in its auxiliary slot; ours have string operations and formatted print.

#### The compiler words

Words like `if`, `then`, `else`, `begin`, `until` are *immediate*--they run at
compile time rather than being compiled themselves. `if` emits a JZERO
instruction with a zero placeholder for the jump address and leaves the address
of that placeholder on the data stack. `then` pops that address, reads the
current HERE (next free location), and patches the placeholder with the correct
target. `else` does both: it patches the `if` hole *and* emits a JUMP with its
own placeholder for `then` to patch.

All of this address arithmetic is done in two-tryte form throughout, which is
the main source of complexity in the compiler words.



### What balanced ternary actually gives you

The Setun's architecture makes some things genuinely nicer than binary:

*Sign is structural.* The sign of a number is just its most significant
non-zero trit. Negation is a single `NOT` pass (flip all trits: -1<-->+1,
0 stays 0). No two's complement, no sign extension, no separate sign bit.

*Three-way branches are natural.* JZERO, JPOS, and JNEG test the three
possible signs of a ternary value. Sorting and comparisons that need
less-than / equal / greater-than are handled with a single `sgn` and one
branch, not two.

*Ternary logic is symmetric.* The `and` and `or` operations on trits are
`min` and `max` respectively. They extend the two-valued boolean operators to
a natural three-valued logic where -1 is false, 0 is unknown, and +1 is true.

*Rounding is free.* Truncating the low-order trits of a balanced ternary
number rounds it to the nearest integer automatically, without any correction
step.

Balanced ternary never made it into mainstream computing, partly because
three-state electronic components were harder to build reliably than two-state
ones, and partly because the industry had already standardized on binary before
the advantages of ternary were fully understood. The Setun remains a curiosity
and an object lesson in the road not taken.



### Running the emulator

```sh
make dssp          # build the DSSP interpreter
./dssp             # run the test suite
./dssp -i          # interactive REPL
```

In the REPL:

```
| 3 4 + .
7  ok
| : square dup * ;
 ok
| 7 square .
49  ok
| 13 .t
+++  ok
| -7 .t
-+-  ok
```

`.t` prints a number in balanced ternary using `+`, `0`, and `-`. The number
13 is `+++ ` because 9 + 3 + 1 = 13; the number 7 is `+-+` because 9 - 3 + 1
= 7.

The `make setun` target builds a separate demo of the original Setun (1958)
architecture, showing the 18-trit word format, the index register, and simple
programs in the original 24-instruction set.



### What this is not

The opcode numbers are invented. The dictionary format is invented. The host
call mechanism is a pragmatic shortcut that the real hardware would have handled
differently. The 18-trit data stack items of the real Setun-70 are here
represented as 6-trit trytes, limiting integer range to ±364.

Most importantly: the real DSSP ran on *conventional binary microcomputers* as
a software system. What we built--a Forth whose interpreter loop lives as
native tryte code inside a balanced ternary VM--is a tribute to what DSSP
*could* have been if the Setun-70 had been developed further. Brusentsov's
vision was exactly this: a machine and language that grew together, each
shaped by the other. The administrative decisions that stopped the Setun-70's
development in the early 1970s ended that experiment before it fully matured.

This emulator is a small attempt to see what it might have looked like.
