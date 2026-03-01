
## RISC-V Cooperative Context Switch Demo

A self-contained cooperative context switch implementation in
*RISC-V RV32IM assembly*, assembled and executed by a custom Python toolchain.



### Files

| File | Purpose |
|------|---------|
| `switch.S` | RISC-V RV32IM assembly - two cooperating tasks + scheduler + `context_switch` |
| `asm.py` | Two-pass RISC-V assembler (RV32IM) - produces a flat binary |
| `vm.py` | RISC-V virtual machine - executes the binary, visualises context switches |


```bash
# 1. Assemble
python3 asm.py switch.S switch.bin

# 2. Run
python3 vm.py switch.bin

# Optional flags
python3 asm.py switch.S switch.bin -v       # verbose: show every instruction + address
python3 vm.py  switch.bin -t                # trace: print every instruction as it executes
python3 vm.py  switch.bin -r                # dump final register state
```



### What It Does

Two tasks (A and B) run cooperatively on a single CPU (the VM). Each task counts from 0 to 2,
printing its step, then *yields* control to a scheduler. The scheduler saves the current task's
context and restores the next one--a minimal but complete cooperative multitasking loop.

Every time `context_switch` runs, the VM intercepts a special `YIELD` ecall and prints the full
saved and restored register state, so you can see exactly what the CPU saves and where execution will resume.



### How It Works

#### Context Structure

Each task has a 40-byte *context block* in memory--the RISC-V equivalent of a minimal PCB
(Process Control Block):

```
Offset  0: s0  (x8)  -+
Offset  4: s1  (x9)   │  callee-saved general-purpose registers
Offset  8: s2  (x18)  │  (s1 is used as each task's loop counter)
Offset 12: s3  (x19)  │
Offset 16: s4  (x20)  │
Offset 20: s5  (x21)  │
Offset 24: s6  (x22)  │
Offset 28: s7  (x23) -+
Offset 32: sp  (x2)  -- stack pointer
Offset 36: ra  (x1)  -- resume address  (the "saved PC")
```

Why callee-saved registers? Because in the RISC-V calling convention `s0–s11` are the registers a
function *promises* to preserve. Saving only these--plus `sp` and `ra`--is sufficient for a cooperative
switch where tasks yield at known points.

#### `context_switch(a0, a1)`

This is the heart of the demo, the direct RISC-V equivalent of the ARM `context_switch` in `switch.S`:

```asm
context_switch:
    # SAVE current context
    sw   s0,  CTX_S0(a0)      # save callee-saved regs
    sw   s1,  CTX_S1(a0)
    ...
    sw   s7,  CTX_S7(a0)
    sw   sp,  CTX_SP(a0)      # save stack pointer
    sw   ra,  CTX_RA(a0)      # save return address - resume PC

    # VM visualisation ecall
    li   a7, 64
    ecall                     # VM prints the switch banner

    # RESTORE next context
    lw   s0,  CTX_S0(a1)      # restore callee-saved regs
    ...
    lw   s7,  CTX_S7(a1)
    lw   sp,  CTX_SP(a1)      # restore stack pointer
    lw   ra,  CTX_RA(a1)      # restore resume address

    ret                       # jump to restored ra -> next task
```

*ARM vs RISC-V comparison:*

| ARM Thumb (`switch.S`) | RISC-V (`switch.S`) |
|------------------------|---------------------|
| Saves `r4–r11` (callee-saved) | Saves `s0–s7` (callee-saved) |
| Saves `sp` via `mov r2, sp` | Saves `sp` directly with `sw sp` |
| Saves `lr` (link register) | Saves `ra` (return address) |
| Returns with `bx lr` | Returns with `ret` (= `jalr zero, ra`) |

#### Yield Pattern

A task yields by calling `context_switch` with itself as *current* and the
scheduler as *next*. The `ra` register is set to the resume label immediately
before the call, so after the next switch-in the task picks up exactly
where it left off:

```asm
    la   ra, task_a_yield_ret       # set resume point
    addi a0, s11, OFF_CTX_A         # current = Task A context block
    addi a1, s11, OFF_CTX_SCHED     # next    = scheduler context block
    jal  ra, context_switch         # yield (ra is overwritten by jal,
                                    # but ra was already saved above)
task_a_yield_ret:
    j    task_a_loop                # resume here after next switch-in
```

This is the assembly equivalent of `setjmp`/`longjmp` in the C version:
`setjmp(ctx_a)` -> save context, `longjmp(ctx_main, 1)` -> restore scheduler.

#### Scheduler

The scheduler holds its own context block (`ctx_scheduler`). Tasks yield
*to the scheduler*, and the scheduler switches *to the next task*--nothing
switches directly between tasks. This matches the C `switch.c` flow exactly:

```
Task A runs → context_switch(ctx_a, ctx_scheduler)
  -> scheduler_resume: sees last_task=A, switches to B
  -> context_switch(ctx_scheduler, ctx_b)
Task B runs → context_switch(ctx_b, ctx_scheduler)
  -> scheduler_resume: sees last_task=B, switches to A
  -> context_switch(ctx_scheduler, ctx_a)
  ...
```

#### Memory Layout

```
data (base = s11):
  [  0.. 39]  ctx_scheduler   <- scheduler's saved context
  [ 40.. 79]  ctx_a           <- Task A's saved context
  [ 80..119]  ctx_b           <- Task B's saved context
  [120..123]  a_done          <- flag: Task A finished?
  [124..127]  b_done          <- flag: Task B finished?
  [128..131]  last_task       <- 1=A or 2=B ran last
  [132..387]  stack_a         <- Task A's 256-byte stack (grows ↓)
  [388..643]  stack_b         <- Task B's 256-byte stack (grows ↓)
```



### VM

The VM (`vm.py`) has one ecall:

#### `ecall 64` - YIELD (context switch visualisation)

Called from inside `context_switch` with:
- `a0` = address of the *current* (saved) context block
- `a1` = address of the *next* (restored) context block

The VM reads both 40-byte blocks directly from its memory and prints 
 formatted banner showing all saved/restored registers and resume PCs.
 This makes the invisible act of context switching fully observable.

*Other ecalls used:*

| `a7` | Action |
|------|--------|
| `1` | Print integer (`a0` = value) |
| `4` | Print null-terminated string (`a0` = address) |
| `10` | Exit |
| `64` | YIELD - print context-switch banner |



### Relation to the C Version

The C `switch.c` uses `setjmp`/`longjmp` to simulate context switching:

| C (`switch.c`) | RISC-V (`switch.S`) |
|----------------|---------------------|
| `setjmp(ctx_a)` - saves registers into a `jmp_buf` | `context_switch`: `sw s0..s7, sp, ra` into context block |
| `longjmp(ctx_main, 1)` - restores scheduler registers | `context_switch`: `lw s0..s7, sp, ra` from scheduler ctx |
| Static `int i` persists across calls | `s1` persists because it's saved/restored in the context block |
| `ctx_main`, `ctx_a`, `ctx_b` - three `jmp_buf`s | `ctx_scheduler`, `ctx_a`, `ctx_b` - three 40-byte memory blocks |
| `last_task` global int | `OFF_LAST` word in the data block |
| `a_done`, `b_done` flags | `OFF_A_DONE`, `OFF_B_DONE` words in the data block |

The key difference: `setjmp`/`longjmp` save the *full* `jmp_buf` (which includes all non-volatile registers)
while the assembly version saves only the callee-saved subset--but the effect is identical for cooperative
switching where tasks yield at known safe points.



### Historical Notes

Context switching has a longer and stranger history than most programmers realise.
What follows is a roughly chronological account of how the idea evolved--from hardware
curiosities to the invisible foundation of every modern operating system.


__1950s: The Problem of Waiting__

Early computers were purely sequential: a program ran to completion, and then the next
one started. The bottleneck was obvious--a program waiting for a punched-card reader or
a magnetic drum was burning expensive CPU time doing nothing. The first instinct was not
to switch tasks but to batch them: jobs were queued on tape and run back-to-back by an
operator (or a simple monitor program). IBM's *GM-NAA I/O System* (1956), written for the
IBM 704 at General Motors, is one of the earliest examples of a resident monitor that
could load and run successive jobs automatically. No context switching yet--but the
pressure to stop wasting CPU cycles had been identified.


__Early 1960s: Interrupts and the First Switches__

The invention of the *hardware interrupt* was the prerequisite for true context switching.
An interrupt forces the CPU to stop what it is doing, save a minimal amount of state
(typically just the program counter and a status word, pushed onto a hardware stack or
into fixed registers), and jump to an interrupt handler. When the handler finishes,
the original state is restored and execution continues as if nothing happened.

The *Atlas computer* (Manchester / Ferranti, 1962) is often cited as the first machine
to implement something recognisable as an OS-managed context switch. Atlas had a one-level
store (the precursor to virtual memory), and its supervisor could suspend a user program,
handle a page fault or I/O completion, and resume the program - saving and restoring the
full register set in the process. The Atlas supervisor also introduced the idea of a
*base register* saved as part of the context, a concept that would echo through every
subsequent architecture.

Around the same time, *CTSS* (Compatible Time-Sharing System, MIT, 1961) running on a
modified IBM 7094 performed genuine preemptive context switches driven by a hardware clock.
A timer interrupt every ~200ms would save the current user's registers and swap in the
next user's job. This was the first widely used time-sharing system and the direct
ancestor of Multics and Unix.


__Mid 1960s: The Register File Problem__

As machines grew more capable they accumulated more registers, and saving them all on
every context switch became expensive. This tension produced two lasting design philosophies:

*The minimal-save approach* - only save what the calling convention says must be preserved
(callee-saved registers), and let the compiler guarantee the rest are dead at yield points.
This is exactly what `switch.S` does, and what `setjmp`/`longjmp` do in C. It works for
cooperative switching because the task itself chooses when to yield.

*The full-save approach* - save every register, because a preemptive interrupt can arrive
at any instruction. This is more expensive but unavoidable in a preemptive kernel.
The x86 `PUSHA` / `POPA` instructions (introduced with the 80186 in 1982) were a
hardware concession to this cost.

The *IBM System/360* (1964) took the full-save approach and made it explicit: the
architecture defined a 16-register general-purpose file, and the calling convention
required callers to save registers they needed before making a call. OS/360's task
dispatcher saved all 16 GPRs plus the PSW (program status word, containing the PC
and condition codes) into a fixed-format *TCB* (Task Control Block)--the direct ancestor
of today's `task_struct` in the Linux kernel.


__Late 1960s - Coroutines, Before the Name Was Common__

*Conway's coroutines* (Melvin Conway, 1963) articulated the cooperative model formally
for the first time. Conway described a pair of routines that could transfer control
to each other at arbitrary points - not by calling and returning in a stack discipline,
but by symmetrically saving state and resuming. He was implementing a compiler in which
the lexer and parser ran as coroutines. The word "coroutine" appeared in print here,
and the mechanism is exactly what this demo implements: two parties, each with its own
stack and saved registers, handing control back and forth without either being the "master."

Simula 67 (Nygaard and Dahl, Norway) introduced *coroutines as a first-class language
feature* for simulation. A Simula process had its own stack and could call `DETACH`
to yield and `RESUME` to restart another process--semantically identical to what our
scheduler does, but with the compiler generating the save/restore code automatically.


__1970s - Unix, Processes, and the Fork Heritage__

Unix (Thompson and Ritchie, Bell Labs, ~1969–1973) crystallised the *process model* that
dominates to this day. A process owns a register set, a stack, a heap, and a page table.
The kernel's context switch saves all the registers (on the kernel stack of the outgoing
process) and restores those of the incoming process. Crucially, Unix added `fork()`,
which copies a process's entire context--the first time "saving a context" was used to
*create* a new task rather than just suspend an existing one.

The early PDP-11 Unix context switch (in assembly, in `m40.s` and `m45.s`) is only about
30 lines long. It saves `r0–r5`, the stack pointer, and the PC (indirectly via the interrupt
mechanism), then restores those of the next process. The elegance of this small piece
of code--doing something conceptually profound in very few instructions--has made it a
favourite teaching example for 50 years.


__1970s–80s - Hardware Task Switching: The x86 Detour__

Intel's 286 (1982) and 386 (1985) introduced *hardware task switching* via the Task State
Segment (TSS). A single `JMP` or `CALL` to a task gate in the descriptor table would cause
the CPU to automatically save the entire register file of the current task into its TSS
and load the next task's registers from its TSS. No software save/restore loop needed.

This seemed like a good idea at the time. In practice, every major OS that targeted
x86-- the OS/2, Windows NT, Linux--chose *not* to use hardware task switching. The reasons
were: it saved too many registers (including FPU state, which is large and often unnecessary),
it was inflexible (you couldn't easily customise what gets saved), and it was surprisingly
slow on modern microarchitectures where a single `CPUID` or `WBINVD` could flush more
state than the hardware switch saved in software overhead. Linux has used software context
switching on x86 from the beginning. The TSS survives today only to hold the kernel stack
pointer for privilege-level transitions (syscalls / interrupts), not for task switching.


__1980s - Fibres, Green Threads, and the User-Space Renaissance__

As operating systems matured, a second wave of user-space cooperative switching emerged.
This time not because the OS was primitive but because kernel context switches were
*too expensive* for fine-grained concurrency.

*Smalltalk-80's* process model ran cooperative green threads entirely in the Smalltalk VM.
*C threads* libraries (like MIT's *C Threads* for Mach, ~1987) and later *GNU Pth*
implemented M:1 threading--many user-level threads multiplexed onto one kernel thread--using
`setjmp`/`longjmp` or direct assembly save/restore, exactly as in this demo.

The *SPARC register windows* (Sun Microsystems, 1987) were an architectural attempt to
make context switching cheaper by keeping multiple register frames on-chip and only spilling
to memory when they overflowed. The idea was clever but ultimately fell out of favour:
real workloads had deep enough call stacks that spills were frequent, and the hardware
complexity was hard to pipeline efficiently.


__1990s - Threads, SMP, and the Cost of Sharing__

The proliferation of *symmetric multi-processing (SMP)* hardware in the 1990s changed
context switching from a purely temporal problem to a spatial one. On a multi-CPU machine,
saving registers is not enough--you must also handle *cache coherency*. When a process
migrates from CPU 0 to CPU 1, its working set is cold on CPU 1's cache. The *TLB*
(Translation Lookaside Buffer) must also be flushed or tagged per-CPU, since the
virtual-to-physical mappings of the outgoing process are no longer valid.

Linux introduced *ASID tagging* (Address Space ID) for TLB entries in the early
2000s--borrowed from MIPS and Alpha architectures - which allows TLB entries to be
tagged with a per-process identifier so they don't need to be flushed on every switch.
This was a substantial speedup for context-switch-heavy workloads.

The debate about *kernel threads vs user threads* dominated most of the 1990s. Early
Linux (up to 2.4) had a notoriously expensive `clone()` + thread implementation.
The *NPTL* (Native POSIX Thread Library, Ulrich Drepper and Ingo Molnár, 2003) rewrote
Linux threading to make `clone()` fast and kernel-scheduled threads the norm--effectively
conceding that for preemptive, multi-CPU workloads, the kernel must be in the loop.


__2000s - The Async Revival: Cooperative Switching Comes Back__

The rise of high-concurrency network servers (the *C10K problem*, Dan Kegel, 1999)
brought cooperative switching back into fashion--not because kernel threads were wrong,
but because 10,000 kernel threads consume too much memory (each needs a kernel stack)
and too many context switches.

*libevent*, *libev*, and eventually *Node.js* (2009) popularised the *event loop* model:
a single thread, cooperative scheduling, explicit callbacks or `yield` points. This is
cooperative context switching without even saving registers--the program counter advances
through callbacks, and state lives in closures on the heap rather than in saved register files.

*Python generators* (`yield`, introduced in PEP 255, 2001) and later *Python coroutines*
(`async`/`await`, PEP 492, 2015) are cooperative context switches implemented by the
language runtime: the frame object (the Python equivalent of a saved register file) is
kept alive on the heap across yields. CPython's `YIELD_VALUE` bytecode is the conceptual
descendant of the `sw ra, CTX_RA(a0)` in this demo.


__2010s - Goroutines, Fibers, and the Scheduler Renaissance__

*Go's goroutines* (2009, production use from ~2012) refined the M:N threading model:
many goroutines multiplexed onto a pool of OS threads, with a sophisticated runtime scheduler.
Go's `goroutine` context switch is implemented in hand-written Plan 9 assembly (`asm_*.s`)
and saves only the goroutine's stack pointer and the program counter--the minimal cooperative
save--but the Go runtime can *preempt* goroutines at function call boundaries by inserting
stack-growth checks, giving it preemption without hardware interrupts.

*Windows Fibers* (since Windows NT 3.51) and *Boost.Context* / *Boost.Coroutine* (C++)
brought explicit stack-switching to user-space C++ development, each implementing the same
10–20 instruction save/restore loop in platform-specific assembly.

The *WebAssembly* stack-switching proposal (ongoing, ~2021–) is attempting to standardise
cooperative context switching at the bytecode level, so that languages compiled to Wasm
can implement their own coroutine or async runtimes without falling back to JavaScript promises.


__The Constant Underneath__

Across seven decades and dozens of architectures, the core act has not changed: save a program
counter and some registers somewhere safe, load a different set, and jump. The sophistication
has grown. TLB management, cache affinity, security boundaries (Spectre/Meltdown forced kernel
page-table isolation, *KPTI*, which made context switches measurably more expensive in 2018),
scheduling policies, fairness, real-time guarantees--but the 10-instruction loop at the centre
of `context_switch` would be recognisable to the engineers who wrote the Atlas supervisor in 1962.

That is what this demo is: the irreducible kernel of an idea that has been running,
in one form or another, on every general-purpose computer built in the last 60 years.



### Reference

- *ARM `armswitch.S`* - the original ARM Thumb version this was translated from; compares `r4–r11`/`lr` with RISC-V `s0–s7`/`ra`
- *C `switch.c`* - the high-level C simulation using `setjmp`/`longjmp`
- *RISC-V Calling Convention* - defines which registers are callee-saved (`s0–s11`) and why only those need saving
- *POSIX `ucontext.h`* (`makecontext`, `swapcontext`) - the standard Unix API for user-space context switching
- *`setjmp`/`longjmp`* - the portable C mechanism that inspired this demo
- *Melvin Conway, "Design of a Separable Transition-Diagram Compiler" (1963)* - the paper that named coroutines
- *The Unix Heritage Society (TUHS)* - early Unix source, including the original PDP-11 context switch in assembly
- *"The C10K Problem", Dan Kegel (1999)* - the paper that reignited interest in cooperative, event-driven concurrency


