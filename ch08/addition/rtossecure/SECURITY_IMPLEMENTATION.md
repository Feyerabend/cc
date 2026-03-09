
## Security Implementation: Stack Protection

Target: RP2350 / Cortex-M33, Raspberry Pi Pico 2W
RTOS: bare-metal preemptive, SysTick + PendSV context switch

The following implementation assume you are familiar with
[RTOS](./../../../ch07/addition/rtosapi/). 


### What Was Added

Two complementary protection layers were implemented.  They defend against
the same class of bug--a local array written past its end--but at different
granularities and from different directions.

#### Layer 1: Compiler-level canary (GCC `-fstack-protector-strong`)

GCC inserts a secret word ("canary") between a function's local variables
and its saved return address whenever the function has any local buffer or
any address-of a local variable is taken.  Before the function returns, the
compiler checks that the canary still matches its original value.  If the
canary has been overwritten it calls `__stack_chk_fail()`.

**What it catches:** A buffer overflow that grows toward the return address
within a single function call on the currently-running task's stack.  This
is the most common exploitable stack overflow pattern.

**What it does NOT catch:** An overflow that only corrupts another task's
stack (no canary crosses task boundaries at the function level).

The canary value (`__stack_chk_guard`) is drawn from the RP2350 hardware
TRNG at boot.  An attacker cannot predict or reproduce it across power
cycles.

#### Layer 2: Per-task bottom-of-stack guard (RTOS-level)

The RTOS fills every task's stack array with `0xDEADBEEF` at creation, then
writes the random session canary into `stack[0]`--the lowest-address word,
the first word a downward-growing stack would overrun.

`pendsv_switch()`: the C bridge called on every context switch--checks
the guard word of the task it is saving before selecting the next task.
If the guard has been overwritten:

1. The fault is recorded in `rtos_last_fault` (task index, name, tick).
2. The offending task is marked `TASK_SUSPENDED`.
3. The scheduler skips it and runs a healthy task instead.
4. The display renders a red fault banner within ~50 ms.

**What it catches:** Any overflow that reaches the bottom of a task's 256-
word stack, regardless of which function caused it.  This is a deeper,
cross-function check at every task boundary.

**What it does NOT catch:** An overflow that stays within the task's stack
and only corrupts data higher up (not `stack[0]`).



### The Session Canary

Both layers share one random value drawn at `rtos_init()`:

```c
uint32_t rng = get_rand_32();         // RP2350 hardware TRNG
__stack_chk_guard   = rng;            // Layer 1   GCC reads this symbol
session_stack_guard = rng;            // Layer 2   written to task stack[0]
```

`get_rand_32()` (Pico SDK) discards initial samples, runs the TRNG health
test, and returns a conditioned 32-bit random word--addressing the cold-boot
entropy concern noted in SECURITY.md.

Pathological values (`0x00000000` and `0xDEADBEEF`) are explicitly excluded
so the guard is always distinguishable from an uninitialised or canary slot.



### Fault Handling

When a violation is detected (`pendsv_switch` guard check **or**
`__stack_chk_fail`):

| Field | Value recorded |
|---|---|
| `rtos_last_fault.active` | `true` |
| `rtos_last_fault.task_index` | index of the offending task |
| `rtos_last_fault.task_name` | pointer to TCB name string |
| `rtos_last_fault.tick` | `tick_count` at time of detection |

The offending task is permanently suspended.  All other tasks continue
running.  Core 1's display loop polls `rtos_last_fault.active` every frame
(~50 ms) and renders a red banner over the timeline area showing the task
name and tick.



### Testing with `fault_test`

The shell command `fault_test [task_index]` deliberately corrupts the guard
word of the named task by XOR-ing it with `0xBAD00BAD`:

```
> fault_test 1
Corrupting stack[0] of task 1 (Counter) ...
Done. Fault detected on next context switch from that task.
Check the display - a red banner will appear.
```

Because the guard is checked when a task is SWITCHED OUT (not when it is
switched in), the fault triggers on the next PendSV after the Counter task
runs.  At 1 ms SysTick rate this is essentially immediate.



### Watermark Scan

The stack high-watermark is computed by scanning from `stack[1]` upward
(not `stack[0]`) because `stack[0]` now holds the guard, not a canary word.
The reported usable depth is `TASK_STACK_SIZE - 1` (255 words).



### What These Layers Do Not Cover

| Threat | Status |
|--------|--------|
| Overflow within a function that stays above `stack[0]` | Layer 1 catches return-address corruption; silent data corruption still possible |
| Heap or global buffer overflow | Not detected (no heap; globals have no guard) |
| DMA writing to arbitrary addresses | Not detected (DMA bypasses MPU) |
| Malicious task reading another task's stack | Not prevented (no MPU, all tasks privileged) |
| Physical attacker reflashing firmware | Not prevented (OTP not fused) |

These are accurately described in [README.md](./README.md).
The two layers implemented here are the lowest-risk, highest-value
hardening steps for an educational RTOS: they catch the bugs most
likely to occur in practice with no architectural disruption and
~10 cycles of overhead per context switch.



### Files Changed

| File | Change |
|------|--------|
| `CMakeLists.txt` | Added `-fstack-protector-strong`; added `pico_rand` link library |
| `rtos.h` | Added `rtos_fault_t` struct and `rtos_last_fault` extern |
| `rtos.c` | TRNG canary init in `rtos_init()`; guard write in `task_stack_init()`; guard check in `pendsv_switch()`; `__stack_chk_fail()` implementation; watermark scan starts at index 1 |
| `main.c` | `stack_peak_words()` starts scan at index 1; fault overlay rendered after `draw_timeline()` |
| `rtos_shell.c` | `fault_test` command registered at `shell_init()` |


