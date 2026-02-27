# state_machine.asm
# Demonstrates jump table for state machine implementation
# Common in embedded systems, protocol handlers, and UI event loops

.text
main:
    lui sp, 0x10
    
    # Init state machine
    li s0, 0            # s0 = current state (start in IDLE)
    la s1, events       # s1 = pointer to event sequence
    
state_loop:
    # Load next event
    lbu a0, 0(s1)
    addi s1, s1, 1
    
    # Check for end marker
    li t0, 255
    beq a0, t0, end_program
    
    # Print current state
    mv a0, s0
    li a7, 1
    ecall
    li a0, 32           # space
    li a7, 11
    ecall
    
    # Save state
    addi sp, sp, -8
    sw s0, 0(sp)
    sw s1, 4(sp)
    
    # Dispatch to state handler via jump table
    la t0, state_table
    slli s0, s0, 2
    add t0, t0, s0
    lw t0, 0(t0)
    
    # Call state handler with event in a0
    jalr ra, t0, 0
    
    # a0 now contains next state
    mv s0, a0
    
    # Restore s1 (event pointer)
    lw s1, 4(sp)
    addi sp, sp, 8
    
    # Continue
    j state_loop

end_program:
    li a0, 10
    li a7, 11
    ecall
    li a7, 10
    ecall

# ----------------------------------------
# State Machine: Traffic Light Controller
# States: 0=RED, 1=YELLOW, 2=GREEN
# Events: 0=TIMER, 1=EMERGENCY, 2=RESET
# ----------------------------------------

# State 0: RED
state_red:
    # Event in a0
    beq a0, zero, red_timer
    li t0, 1
    beq a0, t0, red_emergency
    li t0, 2
    beq a0, t0, red_reset
    j state_error

red_timer:
    li a0, 2            # RED -> GREEN
    ret
red_emergency:
    li a0, 0            # Stay RED
    ret
red_reset:
    li a0, 0            # Stay RED
    ret

# State 1: YELLOW
state_yellow:
    beq a0, zero, yellow_timer
    li t0, 1
    beq a0, t0, yellow_emergency
    li t0, 2
    beq a0, t0, yellow_reset
    j state_error

yellow_timer:
    li a0, 0            # YELLOW -> RED
    ret
yellow_emergency:
    li a0, 0            # Go to RED
    ret
yellow_reset:
    li a0, 0            # Go to RED
    ret

# State 2: GREEN
state_green:
    beq a0, zero, green_timer
    li t0, 1
    beq a0, t0, green_emergency
    li t0, 2
    beq a0, t0, green_reset
    j state_error

green_timer:
    li a0, 1            # GREEN -> YELLOW
    ret
green_emergency:
    li a0, 1            # Go to YELLOW first
    ret
green_reset:
    li a0, 0            # Go to RED
    ret

state_error:
    li a0, 0            # Default to RED
    ret


# ----

.data

# State dispatch table
state_table:
    .word state_red     # State 0
    .word state_yellow  # State 1
    .word state_green   # State 2

# Event sequence to process
# Format: sequence of event codes, terminated by 255
events:
    .byte 0             # TIMER: RED -> GREEN
    .byte 0             # TIMER: GREEN -> YELLOW
    .byte 0             # TIMER: YELLOW -> RED
    .byte 0             # TIMER: RED -> GREEN
    .byte 1             # EMERGENCY: GREEN -> YELLOW
    .byte 0             # TIMER: YELLOW -> RED
    .byte 2             # RESET: RED -> RED
    .byte 0             # TIMER: RED -> GREEN
    .byte 255           # END
