
## Pico 2W RTOS

A preemptive RTOS built from scratch for the Raspberry Pi Pico 2W (RP2350 / Cortex-M33),
with a live visual display that makes the scheduler's decisions visible in real time.

The basis for the implemention can be found at [RTOS](./../../../ch07/addition/rtosapi/).

__Security Analysis: Pico 2W RTOS__

- Target: RP2350 / Cortex-M33, Raspberry Pi Pico 2W
- Scope: bare-metal preemptive RTOS with USB CDC shell


### Premise

"Secure" means different things depending on who you are defending against.
Until the threat model is defined it is impossible to say whether a system
is secure: only whether it is hardened against a specific class of attacker.

| Adversary class | Primary concern |
|-----------------|-----------------|
| Buggy co-tenant task | Accidental memory corruption across task boundaries |
| Malicious co-tenant task | Deliberate read/write of another task's stack or globals |
| Malicious USB host | Shell commands used to crash, exfiltrate, or reprogramme |
| Physical attacker (JTAG / flash reader) | Firmware extraction, key recovery, reflash |
| Side-channel attacker | Power analysis, timing, EM emission |

This RTOS currently has no defences against *any* of these. The analysis below
works through what can be added, what stands in the way, and what would
remain uncertain.



### What Can Be Secured

#### 1. Memory isolation via MPU

The Cortex-M33 MPU provides 8 independently configurable regions with
arbitrary base/limit alignment (the ARMv8-M model, not the older
power-of-2-aligned M3/M4 model). Concretely achievable:


*Stack overflow guards (Phase 1)*

Place a no-access guard region at the bottom of each task's stack array.
A runaway stack pointer triggers a MemFault before it can corrupt the next
TCB in memory. The MemFault handler can identify the offending task, mark it
SUSPENDED, and display a fault overlay while other tasks keep running.


*Per-task stack write isolation (Phase 2)*

On every context switch, update the MPU so the incoming task has RW access to
its own stack and RO (or no access) to all other stacks. A dangling pointer
into another task's stack faults immediately rather than corrupting silently.


*Execute-Never on SRAM*

The MPU XN bit prevents shellcode execution from stack or heap regions.
Combined with RO flash, this eliminates a whole class of control-flow attacks.


*Peripheral lockdown*

Restrict which tasks can access which peripheral address ranges. For example,
only the display task should be able to write to SPI/DMA registers. All other
tasks attempting those writes fault immediately.

A workable region allocation with 4 tasks:

```
Region 0  flash                    RO, executable
Region 1  shared SRAM globals      RW, XN
Region 2  current task's stack     RW, XN  <-- updated on every context switch
Region 3  all other task stacks    RO or no-access, XN
Region 4  peripherals for task     RW (set per-task on switch)
Region 5  (free)
Region 6  (free)
Region 7  background / default     no-access (deny everything else)
```

The "single moving region" trick (region 2 always points at the current
task's stack) avoids needing one region per task, keeping the budget viable.


#### 2. Randomised stack canaries

The current canary is the fixed value `0xDEADBEEF`. An attacker who controls
an overflow can write `0xDEADBEEF` themselves and bypass detection entirely.

The RP2350 has a hardware **TRNG** at `0x40060000`. Drawing one random word at
`rtos_init()` and storing it as the session canary costs ~10 lines of code.
Adding a canary-integrity check inside `pendsv_switch()` — before restoring
the incoming task's frame — catches overflows before they reach the
instruction pointer. On Cortex-M33 this adds roughly 10 cycles per context
switch.

Additionally, GCC's `-fstack-protector-strong` flag inserts compiler-generated
canary checks at function boundaries. It is compatible with this RTOS, costs
nothing architecturally, and catches the majority of stack buffer overflows
automatically. It should be added to `CMakeLists.txt` immediately.



#### 3. Unprivileged thread mode

All tasks currently run in **privileged thread mode**, meaning they have
unrestricted write access to the SCB, NVIC, MPU control registers, and
SysTick. A buggy or malicious task could reconfigure interrupt priorities,
disable the watchdog, or disable the MPU itself.

Setting CONTROL bit 0 (`nPRIV = 1`) before returning to a task drops it into
unprivileged thread mode. Writes to system control registers from unprivileged
code cause a fault. Legitimate kernel operations (task_delay, mutex_lock, etc.)
go through an SVC (supervisor call) trap into privileged handler mode.

This is a meaningful isolation boundary even without TrustZone and with
modest implementation cost.



#### 4. TrustZone: the RP2350's strongest isolation primitive

The RP2350 implements the full ARMv8-M Security Extension. Two hardware worlds
exist with separate vector tables, stack pointers, MPU instances, and memory
attribution:

- *Secure world* - RTOS kernel, scheduler, canary logic, cryptographic keys,
  any secret material
- *Non-Secure world* - user tasks, shell, application code

Non-Secure code cannot read Secure memory or call Secure functions except
through explicitly defined Non-Secure Callable (NSC) gateway functions. This
is architecturally the strongest isolation boundary available on this chip.

In principle the RTOS kernel (PendSV handler, SysTick, TCBs, canaries) lives
in Secure world and tasks in Non-Secure world. Tasks make SVC/NSC calls to
block, yield, lock mutexes--they never touch kernel data directly.



#### 5. Per-task watchdog tokens

The hardware watchdog catches a total system lock-up. For finer-grained
detection each task registers a watchdog token and must call
`rtos_watchdog_kick(task_id)` within its expected period. SysTick checks all
tokens every tick; a task that has not kicked within its deadline is flagged,
marked SUSPENDED, and reported on the display. This catches infinite loops and
deadlocks per-task rather than waiting for a system-wide hard reset.



#### 6. Shell hardening

The shell currently has no authentication and minimal input validation.
Additions in rough priority order:

- Validate all numeric arguments (replace unchecked `atoi` with range-checked
  parsing)
- Rate-limit commands to prevent brute-force or input-flooding DoS
- Compile-time gate for unsafe commands via `#ifdef SHELL_UNSAFE_CMDS`
- Optional PIN or challenge-response before allowing destructive operations
- Fuzz the shell with a host-side fuzzer before shipping anything serious



#### 7. Core 1 stats isolation

Currently Core 1's display loop scans `tasks[ci].stack[]` directly to compute
the watermark and reads `tasks[ci].state` without going through any API. This
breaks any model where TCBs should be kernel-private. The fix is for Core 1 to
call `rtos_stats_get()` exclusively and never access `tasks[]` directly. This
is an architectural cleanup, not a performance issue.



### Real Obstacles

#### DMA bypasses the MPU entirely

This is a fundamental hardware constraint on Cortex-M. DMA controllers are
independent bus masters and are not subject to MPU access rules. A task that
can configure a DMA channel can instruct it to read or write any physical
address regardless of the task's own MPU permissions.

Mitigations:
- Use the MPU to deny tasks access to the DMA configuration registers
  (`DMA_BASE` at `0x50000000`), forcing all DMA setup through a kernel SVC
- Note that the RP2350 does not have an IOMPU or bus filter peripheral, so
  there is no hardware way to restrict where an already-programmed DMA
  transfer can reach

#### Interrupt handlers ignore the per-task MPU configuration

The MPU regions configured for "current task" apply in thread mode. When
SysTick or PendSV fires the CPU enters handler mode and the same MPU config
is still active--which may be wrong for handler context (e.g. handler mode
inheriting a task's restricted peripheral access). The practical solution is
to keep a separate "handler mode" MPU layout and switch to it on exception
entry, adding latency to every interrupt.

#### MPU region budget is tight

8 regions sounds generous until you count: flash, shared SRAM, peripheral
bank, task stacks (4 tasks, and growing), and a default deny-all background
region. You quickly face a choice between full per-task stack isolation and
per-task peripheral isolation. The "single moving region" trick handles stacks
at the cost of one reconfiguration per context switch; peripheral isolation
requires more careful allocation.

#### TrustZone without OTP fusing is not secure against reflash

Software-only TrustZone partitioning is useful for isolating buggy code but
not against an attacker who can reflash the firmware and define their own
Secure/Non-Secure boundary. To harden against physical attack the OTP must be
fused with a boot signing key.

*Critical risk*: once you write the OTP and enable secure boot, the board
will refuse to boot unsigned firmware permanently. If the signing key is lost
the board is bricked. This is appropriate for production hardware; it is
extremely dangerous on development boards without robust key management.

#### The compiler adds no protection by default

The current build has no `-fstack-protector`, no position-independent code,
no ASLR (not possible without an MMU). GCC's `-fstack-protector-strong` should
be added to `CMakeLists.txt` as a baseline. It is free in terms of
architecture and catches the majority of overflows without any RTOS changes.

#### No virtual address spaces

Without an MMU there is no address-space layout randomisation, no
copy-on-write, and no process isolation at the OS level. The MPU provides
access *control* but not address *translation* — all tasks see identical
physical addresses. An attacker who knows the memory layout (and on a fixed
embedded system with public firmware they will) can craft attacks that
technically respect MPU boundaries while still causing harm.



### What Would Still Be Uncertain

#### TRNG quality at cold boot

The RP2350's TRNG is a ring-oscillator design. Its entropy quality during the
first milliseconds after a cold power-on, before the oscillators have
stabilised, is not well-characterised in public documentation. Using the first
raw TRNG sample for a security-critical canary without startup conditioning
(discarding N initial samples, running a health test) could produce
predictable values. The right approach is to read and discard several samples,
run the TRNG's built-in health test, and only then use the output.

#### TrustZone partition correctness

Defining the Secure/Non-Secure boundary correctly is genuinely hard. A single
mistakenly-Secure function that accepts a Non-Secure pointer and dereferences
it without validating via the `TT` (Test Target) instruction becomes a
confused-deputy vulnerability--Non-Secure code feeds the Secure function a
pointer to Secure memory and the Secure function reads or corrupts it on their
behalf. Every NSC gateway function must be audited. This is painstaking and
error-prone and the consequences of a mistake are worse than having no
TrustZone at all.

#### Real-time guarantees under security overhead

MPU reconfiguration on every context switch adds latency. SVC-based privilege
escalation adds overhead per kernel call. MemFault handling competes with
SysTick under fault conditions. The interaction between hard real-time
deadlines and security overhead is system-specific and must be measured rather
than estimated. Worst-case interrupt latency figures will change.

#### The effective threat model for this hardware class

It is not obvious who the realistic adversary is for an educational embedded
RTOS. Spending engineering time on TrustZone and OTP fusing when the actual
risk is "task A accidentally corrupts task B's stack" is a misallocation.
Conversely, if this RTOS is used as the basis for a product that connects to
a network or handles user data, the threat model shifts dramatically. The
right security posture cannot be determined without answering: what is this
running, where is it deployed, and who can reach it?



### Practical Implementation Order

The following sequence gives the most security per engineering hour and risk.
Steps 1-4 are additive and low-risk. Step 5 is an architectural cleanup.
Steps 6-7 require significant effort and introduce real operational risk.

| Step | Change | Effort | Risk |
|------|--------|--------|------|
| 1 | Add `-fstack-protector-strong` to CMakeLists | Trivial | None |
| 2 | Randomise canary via RP2350 TRNG at boot | Low | Low |
| 3 | MPU stack overflow guard (Phase 1) | Medium | Low |
| 4 | Unprivileged thread mode via CONTROL.nPRIV + SVC gateway | Medium | Medium |
| 5 | Route Core 1 display through `rtos_stats_get()` only | Low | Low |
| 6 | MPU per-task stack isolation (Phase 2) + peripheral lockdown | High | Medium |
| 7 | TrustZone partitioning (only with clear production need) | Very high | High |

Steps 1 and 2 could be done in an afternoon. Steps 3-5 represent a solid
hardening sprint. Steps 6-7 are a separate project with their own design
phase.



### Summary

The three most impactful single changes, in order:

1. *`-fstack-protector-strong`* - free, catches the majority of buffer
   overflows at the compiler level, no RTOS changes required.

2. *Randomised canary + MPU stack guard* - together these make stack
   corruption detectable in hardware before it causes visible damage, with a
   clear fault report pointing to the offending task.

3. *Unprivileged thread mode* - prevents any task from reconfiguring the
   kernel's own hardware (NVIC, MPU, SysTick) and is the foundation on which
   TrustZone-level isolation is built if ever needed.

Everything else builds on these three.
A start: [SECURITY IMPLEMENTATION](./SECURITY_IMPLEMENTATION.md) ..
