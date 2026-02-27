# demo_green.asm
# -------------------------------------------------------
# GREEN THREAD DEMO
# Two cooperative threads share the CPU by calling YIELD.
# Each thread prints its own TID three times, yielding between prints.
#
# Illustrates:
#   - voluntary context switch  (YIELD syscall 20)
#   - re-entrant code           (both threads run identical thread_body)
#   - saved/restored registers  (t0/t1 per-thread counters survive yields)
#
# ⚠  Uses --mode green  (cooperative switching via YIELD - threads give up CPU voluntarily)
#    Run with --mode kernel to see the same code preempted by the timer instead.
#
# Assemble and run:
#   python3 asm_concurrent.py demo_green.asm demo_green.bin
#   python3 vm_concurrent.py  demo_green.bin --mode green  --trace
#   python3 vm_concurrent.py  demo_green.bin --mode kernel --quantum 3 --trace  # compare!
# -------------------------------------------------------

# -- Shared thread body -- (re-entrant: both threads jump here independently)
thread_body:
    li   t0, 0          # t0 = loop counter  (per-thread - lives in saved TCB)
    li   t1, 3          # t1 = limit

.loop:
    li   a7, 24         # syscall: get_tid  → a0 = our tid
    ecall
    li   a7, 1          # syscall: print_int (prints a0)
    ecall

    yield               # cooperative context switch
                        # scheduler saves {t0,t1,pc,...} then runs next thread

    addi t0, t0, 1      # counter++  (t0 restored correctly on resume)
    bne  t0, t1, .loop  # loop until 3 iterations

    thread.exit         # done

# -- Main -- (VM reads 'main' from demo_green.sym to find entry point)
main:
    li   a0, thread_body
    li   a1, 0
    li   a7, 21         # syscall: thread_create  → spawns tid 1
    ecall

    li   a0, thread_body
    li   a1, 0
    li   a7, 21         # spawns tid 2
    ecall

    thread.exit         # main exits; tid 1 and 2 run round-robin
