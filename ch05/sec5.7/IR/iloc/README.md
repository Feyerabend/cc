
## ILOC

ILOC is best understood as a small, idealised programming language whose only purpose is to 
be used *inside* a compiler. It was created in an academic context, mainly by Keith Cooper
and Linda Torczon, to make the internal phases of a compiler easier to explain and easier
to implement in student projects. Real machine languages are full of historical accidents
and hardware constraints that hide the underlying compiler ideas. ILOC removes (almost) all
of that complexity and keeps only what is conceptually necessary.

When a real compiler translates a source program, it does not jump directly from an AST to machine code.
It gradually transforms the program into representations that look more and more like something
a machine could execute. ILOC sits exactly at the point where the program already looks like a
small assembly language, but still runs on an abstract machine that does not exist in hardware.
That is why it is called an intermediate representation. It is not data and it is not execution;
it is a formal program for a virtual processor designed for compiler reasoning.

Example:
```
a = b + c;
```

Could be represented as:
```
loadAI r_fp, b_offset => r1
loadAI r_fp, c_offset => r2
add r1, r2 => r3
storeAI r3, r_fp, a_offset
```

This virtual processor is intentionally simple. It is register based, with an unlimited number of
virtual registers. It has explicit load and store instructions for memory, and arithmetic instructions
that only operate on registers. There are no hidden side effects, no implicit flags, no special
registers, and no complicated instruction formats. Every data movement and every control-flow
decision is written explicitly in the code. That makes data-flow and control-flow analysis (almost)
mechanically straightforward.

A simple expression like 'a = b + c' becomes a short sequence that loads b and c from memory into
registers, adds the registers, and stores the result back. The important thing is not the exact syntax,
but that each step is explicit and uniform. Every instruction follows the same shape:
take some registers as input, produce a register as output, or branch to labels.
That regularity is what makes ILOC so useful for teaching.

ILOC is also a natural place to introduce SSA form. SSA is not a language of its own; it is a discipline
imposed on a language like ILOC. Instead of reusing the same register name for multiple assignments,
every computed value gets its own new name. This turns the program into a graph of value definitions
and uses, which makes optimisations like constant propagation, dead code elimination, and common
subexpression elimination almost algebraic. When people say "ILOC in SSA form," they mean ILOC
with this single-assignment property enforced.

To SSA:
```
r1 = loadAI r_fp, b_offset
r2 = loadAI r_fp, c_offset
r3 = add r1, r2
storeAI r3, r_fp, a_offset
```

In a compiler pipeline, ILOC usually comes after the AST and any higher-level intermediate forms
that still resemble the source language. The AST captures structure and syntax. ILOC captures computation
and control. Once the program is in ILOC, the compiler stops thinking in terms of language constructs
like loops, expressions, and variables, and starts thinking in terms of registers, memory operations,
jumps, and values. At that point the program already looks like assembly code for a very clean,
and very forgiving machine.

This is also why ILOC feels similar to [LLVM](./../llvm/) IR. Both are assembly-like, register-based,
and often SSA-based. The difference is not conceptual but practical. LLVM IR is designed to be the
backbone of a real industrial compiler infrastructure, with types, calling conventions, platform support,
and enormous engineering detail. ILOC is designed to be understood completely by a student in a few weeks.
It is what LLVM IR would look like if you stripped away everything that is not strictly necessary
for learning compiler theory.

So ILOC is not an intermediate step between "structured data" and "execution". It is a program
representation that defines an *abstract machine*. The compiler transforms source programs into
ILOC programs, transforms those programs many times, and finally transforms them into real machine
programs. In that sense ILOC is much closer to execution than to data:
it already is a form of executable code,
just for a machine that exists only in the mind of the compiler designer.


### Reference 

* Click, C., & Paleczny, M. (1995). A simple graph-based intermediate representation. In *Proceedings of the ACM SIGPLAN Workshop on Intermediate Representations* (pp. 35-49). Association for Computing Machinery. https://doi.org/10.1145/202530.202534

* Cooper, K. D., & Torczon, L. (2011). *Engineering a compiler* (2nd ed.). Morgan Kaufmann.
