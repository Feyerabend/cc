#
# RISC-V Cooperative Context Switch Demo
#
# Architecture:
#   Two tasks (Task A and Task B) run cooperatively. Each counts 0..2,
#   printing its step, then *yields* control back to the scheduler.
#   The scheduler saves the current task context and restores the next one.
#
# Context structure layout (10 words = 40 bytes each):
#   Offset  0: s0   (x8)   -+
#   Offset  4: s1   (x9)    │  callee-saved registers — persist across yields
#   Offset  8: s2   (x18)   │  s1 is used as the task loop counter
#   Offset 12: s3   (x19)   │
#   Offset 16: s4   (x20)   │
#   Offset 20: s5   (x21)   │
#   Offset 24: s6   (x22)   │
#   Offset 28: s7   (x23)  -+
#   Offset 32: sp   (x2)   -- stack pointer
#   Offset 36: ra   (x1)   -- resume address (the "saved PC")
#
# Memory layout (base pointer = s11, label 'data'):
#   [  0.. 39] ctx_scheduler (40 bytes)
#   [ 40.. 79] ctx_a         (40 bytes)
#   [ 80..119] ctx_b         (40 bytes)
#   [120..123] a_done        (4 bytes)
#   [124..127] b_done        (4 bytes)
#   [128..131] last_task     (4 bytes, 1=A 2=B)
#   [132..387] stack_a       (256 bytes, grows down)
#   [388..643] stack_b       (256 bytes, grows down)
#
# context_switch(a0=current_ctx_ptr, a1=next_ctx_ptr)
#   Mirrors switch.S (ARM): saves s0-s7+sp+ra into *a0,
#   issues YIELD ecall (VM shows banner), restores from *a1, returns.


.equ CTX_S0,  0
.equ CTX_S1,  4
.equ CTX_S2,  8
.equ CTX_S3,  12
.equ CTX_S4,  16
.equ CTX_S5,  20
.equ CTX_S6,  24
.equ CTX_S7,  28
.equ CTX_SP,  32
.equ CTX_RA,  36
.equ CTX_SIZE, 40

.equ OFF_CTX_SCHED,  0
.equ OFF_CTX_A,      40
.equ OFF_CTX_B,      80
.equ OFF_A_DONE,    120
.equ OFF_B_DONE,    124
.equ OFF_LAST,      128


# Start ..

_start:
    # Set up main/scheduler stack at top of memory (64KB VM)
    lui  sp, 16            # sp = 0x10000
    addi sp, sp, -4        # sp = 0xFFFC

    # s11 = global data base pointer (persists as callee-saved)
    la   s11, data

    # Initialise flags
    sw   zero, OFF_A_DONE(s11)
    sw   zero, OFF_B_DONE(s11)
    li   t0, 1
    sw   t0,  OFF_LAST(s11)       # last_task = 1 (start with A)

    # Initialise Task A context: dedicated stack + entry point
    la   t0, stack_a_top
    sw   t0, 72(s11)              # ctx_a.sp = OFF_CTX_A(40) + CTX_SP(32)
    la   t0, task_a_entry
    sw   t0, 76(s11)              # ctx_a.ra = OFF_CTX_A(40) + CTX_RA(36)

    # Initialise Task B context: dedicated stack + entry point
    la   t0, stack_b_top
    sw   t0, 112(s11)             # ctx_b.sp = OFF_CTX_B(80) + CTX_SP(32)
    la   t0, task_b_entry
    sw   t0, 116(s11)             # ctx_b.ra = OFF_CTX_B(80) + CTX_RA(36)

    la   a0, str_banner
    li   a7, 4
    ecall

    j    scheduler_start



#  context_switch(a0=current_ctx, a1=next_ctx)
#  RISC-V equivalent of the ARM switch.S context_switch function.

context_switch:
    # -- SAVE current context (callee-saved regs + sp + ra) --
    sw   s0,  CTX_S0(a0)
    sw   s1,  CTX_S1(a0)
    sw   s2,  CTX_S2(a0)
    sw   s3,  CTX_S3(a0)
    sw   s4,  CTX_S4(a0)
    sw   s5,  CTX_S5(a0)
    sw   s6,  CTX_S6(a0)
    sw   s7,  CTX_S7(a0)
    sw   sp,  CTX_SP(a0)
    sw   ra,  CTX_RA(a0)          # ra = the caller's return address = resume PC

    # -- VM ecall 64: print context-switch visualisation --
    # a0 = saved ctx ptr, a1 = next ctx ptr (both still set by caller)
    li   a7, 64
    ecall

    # -- RESTORE next context --
    lw   s0,  CTX_S0(a1)
    lw   s1,  CTX_S1(a1)
    lw   s2,  CTX_S2(a1)
    lw   s3,  CTX_S3(a1)
    lw   s4,  CTX_S4(a1)
    lw   s5,  CTX_S5(a1)
    lw   s6,  CTX_S6(a1)
    lw   s7,  CTX_S7(a1)
    lw   sp,  CTX_SP(a1)
    lw   ra,  CTX_RA(a1)          # ra = resume address of next task

    ret                           # jump to next task's resume point


#  scheduler_start  -- save scheduler context, then launch Task A

scheduler_start:
    la   ra, scheduler_resume     # after switch-in, land here
    addi a0, s11, OFF_CTX_SCHED
    addi a1, s11, OFF_CTX_A
    jal  ra, context_switch       # save scheduler, start Task A

# Scheduler resumes here whenever a task yields back
scheduler_resume:
    lw   t0, OFF_A_DONE(s11)
    lw   t1, OFF_B_DONE(s11)
    and  t2, t0, t1
    li   t3, 1
    beq  t2, t3, all_done         # both tasks done

    lw   t2, OFF_LAST(s11)        # which task ran last?
    beq  t2, t3, sched_was_a     # t3=1 → ran A → now try B

sched_was_b:
    # Last ran B; try to run A next
    beq  t0, t3, sched_was_b_b   # a_done? skip to B
    li   t4, 1
    sw   t4, OFF_LAST(s11)
    la   ra, scheduler_resume
    addi a0, s11, OFF_CTX_SCHED
    addi a1, s11, OFF_CTX_A
    jal  ra, context_switch
    j    scheduler_resume
sched_was_b_b:
    beq  t1, t3, all_done
    li   t4, 2
    sw   t4, OFF_LAST(s11)
    la   ra, scheduler_resume
    addi a0, s11, OFF_CTX_SCHED
    addi a1, s11, OFF_CTX_B
    jal  ra, context_switch
    j    scheduler_resume

sched_was_a:
    # Last ran A; try to run B next
    beq  t1, t3, sched_was_a_a   # b_done? skip to A
    li   t4, 2
    sw   t4, OFF_LAST(s11)
    la   ra, scheduler_resume
    addi a0, s11, OFF_CTX_SCHED
    addi a1, s11, OFF_CTX_B
    jal  ra, context_switch
    j    scheduler_resume
sched_was_a_a:
    beq  t0, t3, all_done
    li   t4, 1
    sw   t4, OFF_LAST(s11)
    la   ra, scheduler_resume
    addi a0, s11, OFF_CTX_SCHED
    addi a1, s11, OFF_CTX_A
    jal  ra, context_switch
    j    scheduler_resume



#  task_a_entry  -- Task A body
#  s1 = loop counter (persists across context saves/restores because it's callee-saved)

task_a_entry:
    li   s1, 0                    # i = 0

task_a_loop:
    li   t0, 3
    bge  s1, t0, task_a_done      # if i >= 3, task complete

    la   a0, str_task_a
    li   a7, 4
    ecall                         # print "Task A: "
    mv   a0, s1
    li   a7, 1
    ecall                         # print i
    la   a0, str_nl
    li   a7, 4
    ecall                         # print newline

    addi s1, s1, 1                # i++

    # YIELD: save Task A ctx, restore scheduler ctx
    la   ra, task_a_yield_ret     # resume point after next switch-in
    addi a0, s11, OFF_CTX_A
    addi a1, s11, OFF_CTX_SCHED
    jal  ra, context_switch
task_a_yield_ret:
    j    task_a_loop

task_a_done:
    la   a0, str_a_done
    li   a7, 4
    ecall
    li   t0, 1
    sw   t0, OFF_A_DONE(s11)      # a_done = 1
    la   ra, task_a_park
    addi a0, s11, OFF_CTX_A
    addi a1, s11, OFF_CTX_SCHED
    jal  ra, context_switch       # yield back; scheduler sees a_done=1
task_a_park:
    j    task_a_park              # unreachable; scheduler won't resume us



#  task_b_entry  -- Task B body (mirrors Task A)

task_b_entry:
    li   s1, 0

task_b_loop:
    li   t0, 3
    bge  s1, t0, task_b_done

    la   a0, str_task_b
    li   a7, 4
    ecall
    mv   a0, s1
    li   a7, 1
    ecall
    la   a0, str_nl
    li   a7, 4
    ecall

    addi s1, s1, 1

    la   ra, task_b_yield_ret
    addi a0, s11, OFF_CTX_B
    addi a1, s11, OFF_CTX_SCHED
    jal  ra, context_switch
task_b_yield_ret:
    j    task_b_loop

task_b_done:
    la   a0, str_b_done
    li   a7, 4
    ecall
    li   t0, 1
    sw   t0, OFF_B_DONE(s11)
    la   ra, task_b_park
    addi a0, s11, OFF_CTX_B
    addi a1, s11, OFF_CTX_SCHED
    jal  ra, context_switch
task_b_park:
    j    task_b_park



#  All is done

all_done:
    la   a0, str_all_done
    li   a7, 4
    ecall
    li   a7, 10
    ecall


#  String literals
str_banner:
    .asciz "* RISC-V Cooperative Context Switch Demo\n"
str_task_a:
    .asciz "Task A: "
str_task_b:
    .asciz "Task B: "
str_a_done:
    .asciz "Task A: Completed\n"
str_b_done:
    .asciz "Task B: Completed\n"
str_all_done:
    .asciz "All done\n"
str_nl:
    .asciz "\n"



#  Data section: 3 context blocks + flags + two task stacks

data:
    .space 40    # ctx_scheduler (OFF_CTX_SCHED = 0)
    .space 40    # ctx_a         (OFF_CTX_A     = 40)
    .space 40    # ctx_b         (OFF_CTX_B     = 80)
    .space 4     # a_done        (OFF_A_DONE    = 120)
    .space 4     # b_done        (OFF_B_DONE    = 124)
    .space 4     # last_task     (OFF_LAST       = 128)
stack_a:
    .space 256   # Task A stack (grows downward)
stack_a_top:
stack_b:
    .space 256   # Task B stack (grows downward)
stack_b_top:
