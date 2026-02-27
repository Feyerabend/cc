# demo_mutex.asm
# --------------------------------------------------------------------------------------
# KERNEL THREAD + MUTEX + MEMORY BARRIER DEMO
#
# Two kernel threads both call inc_counter, which uses a mutex to protect
# a shared counter and a FENCE before the store to illustrate memory barriers.
#
# Illustrates:
#   - involuntary preemption    (kernel timer fires mid-function)
#   - re-entrant function       (inc_counter called from two threads simultaneously)
#   - mutex_lock / unlock       (syscalls 25/26 — only one thread in critical section)
#   - FENCE instruction         (memory barrier annotation in trace)
#   - context switch trace      (full register save/restore shown in output)
#
# ⚠  MUST use --mode kernel  (green threads won't preempt = no interleaving!)
#
# Run:
#   python3 asm_concurrent.py demo_mutex.asm demo_mutex.bin
#   python3 vm_concurrent.py  demo_mutex.bin --mode kernel --quantum 6 --trace
# --------------------------------------------------------------------------------------

.set COUNTER_ADDR,  0x100   # shared word: the counter
.set MUTEX_ADDR,    0x104   # shared word: mutex (0=free, 1=held)
.set ITERATIONS,    4       # each thread increments N times

# ------------------------------------------------------------
# inc_counter — re-entrant function (called from two threads)
#
# Increments COUNTER_ADDR once under mutex protection.
# RA must be saved on stack by caller (or push/pop here).
# ------------------------------------------------------------
inc_counter:
    push ra                 # save return address (addi sp,-4; sw ra,0(sp))

    li   t0, MUTEX_ADDR     # t0 = &mutex
    mutex.lock t0           # acquire mutex (mv a0,t0; li a7,25; ecall)
                            # <- if held, this thread BLOCKS until mutex is free
                            #   (context switch happens here if blocked!)

    # -- Critical section --
    li   t1, COUNTER_ADDR   # t1 = &counter
    lw   t2, 0(t1)          # t2 = *counter  (READ)

    fence                   # MEMORY BARRIER — ensure we see any prior stores
                            # (in a real SMP, prevents stale cached reads)

    addi t2, t2, 1          # t2 = t2 + 1

    sw   t2, 0(t1)          # *counter = t2  (WRITE)

    fence                   # MEMORY BARRIER — ensure our store is visible
                            # before we release the mutex

    li   t0, MUTEX_ADDR
    mutex.unlock t0         # release mutex (mv a0,t0; li a7,26; ecall)
    # -- End critical section --

    # Print the new counter value
    mv   a0, t2             # a0 = new counter value
    li   a7, 1
    ecall                   # prints counter

    pop  ra                 # restore return address (lw ra,0(sp); addi sp,+4)
    ret                     # return to caller

# ----------------------------------------------------------------------
# worker_body — thread entry point
#
# Calls inc_counter ITERATIONS times then exits.
# Both threads run this same function (re-entrant via separate stacks).
# ----------------------------------------------------------------------
worker_body:
    li   t3, 0              # t3 = loop counter
    li   t4, ITERATIONS     # t4 = limit

.worker_loop:
    call inc_counter        # jal ra, inc_counter
                            # <- may be preempted INSIDE inc_counter!
    addi t3, t3, 1
    bne  t3, t4, .worker_loop

    thread.exit

# -----------------------------------------------------
# main — spawns two worker threads then waits for both
# -----------------------------------------------------
main:
    # Zero the counter and mutex in shared memory
    li   t0, COUNTER_ADDR
    sw   zero, 0(t0)        # COUNTER = 0
    li   t0, MUTEX_ADDR
    sw   zero, 0(t0)        # MUTEX = free

    # Spawn worker 1
    li   a0, worker_body
    li   a1, 0
    thread.create s0        # s0 = tid of worker 1

    # Spawn worker 2
    li   a0, worker_body
    li   a1, 0
    thread.create s1        # s1 = tid of worker 2

    # Join both threads (wait for them to finish)
    thread.join s0
    thread.join s1

    # Print final counter value (should be 2 * ITERATIONS = 8)
    li   t1, COUNTER_ADDR
    lw   a0, 0(t1)
    li   a7, 1
    ecall

    # Exit
    li   a7, 10
    ecall
