# traffic.asm (essentially the same as state.asm with better output)
# Traffic Light State Machine with Jump Table Dispatch
# Demonstrates how embedded systems use jump tables for event-driven programming

.text
main:
    lui sp, 0x10
    
    # Init state machine
    li s0, 0            # s0 = current state (0=RED, 1=YELLOW, 2=GREEN)
    la s1, events       # s1 = pointer to event sequence
    la s2, state_names  # s2 = pointer to state name strings
    
    # Print header
    la a0, header
    li a7, 4
    ecall
    
state_loop:
    # Load next event
    lbu a0, 0(s1)
    addi s1, s1, 1
    
    # Check for end marker
    li t0, 255
    beq a0, t0, end_program
    
    # Print current state name
    la a0, state_prefix
    li a7, 4
    ecall
    
    # Print state (RED/YELLOW/GREEN)
    slli t0, s0, 2      # state * 4 (word size)
    add t0, s2, t0      # Add to base of state_names table
    lw a0, 0(t0)        # Load address of state name string
    li a7, 4
    ecall
    
    # Print " + Event "
    la a0, event_str
    li a7, 4
    ecall
    
    # Print event number
    lbu a0, -1(s1)      # Get event we just loaded
    li a7, 1
    ecall
    
    # Print " -> "
    la a0, arrow
    li a7, 4
    ecall
    
    # Save state
    addi sp, sp, -12
    sw s0, 0(sp)
    sw s1, 4(sp)
    sw s2, 8(sp)
    
    # Dispatch to state handler via jump table
    la t0, state_table
    slli s0, s0, 2
    add t0, t0, s0
    lw t0, 0(t0)
    
    # Get event from before s1 increment
    lbu a0, -1(s1)
    
    # Call state handler with event in a0
    jalr ra, t0, 0
    
    # a0 now contains next state
    mv s0, a0
    
    # Print new state name
    slli t0, s0, 2
    add t0, s2, t0
    lw a0, 0(t0)
    li a7, 4
    ecall
    
    # Print newline
    li a0, 10
    li a7, 11
    ecall
    
    # Restore s1 and s2
    lw s1, 4(sp)
    lw s2, 8(sp)
    addi sp, sp, 12
    
    # Continue
    j state_loop

end_program:
    # Print final state
    la a0, final_state_msg
    li a7, 4
    ecall
    
    slli t0, s0, 2
    add t0, s2, t0
    lw a0, 0(t0)
    li a7, 4
    ecall
    
    li a0, 10
    li a7, 11
    ecall
    
    # Exit
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
    li a0, 2            # RED -> GREEN (skip YELLOW)
    ret
red_emergency:
    li a0, 0            # Stay RED (already safe)
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
    li a0, 0            # Go to RED immediately
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
    li a0, 1            # Go to YELLOW first (safety)
    ret
green_reset:
    li a0, 0            # Go to RED
    ret

state_error:
    li a0, 0            # Default to RED on error
    ret



# ----------------------------------------

.data

# State dispatch table (jump table)
state_table:
    .word state_red     # State 0
    .word state_yellow  # State 1
    .word state_green   # State 2

# State name strings
red_str:
    .byte 82, 69, 68, 0     # "RED\0"
yellow_str:
    .byte 89, 69, 76, 76, 79, 87, 0  # "YELLOW\0"
green_str:
    .byte 71, 82, 69, 69, 78, 0      # "GREEN\0"

# State name table (array of pointers to strings)
state_names:
    .word red_str
    .word yellow_str
    .word green_str

# String constants
header:
    .byte 84, 114, 97, 102, 102, 105, 99, 32   # "Traffic "
    .byte 76, 105, 103, 104, 116, 32, 83, 116  # "Light St"
    .byte 97, 116, 101, 32, 77, 97, 99, 104    # "ate Mach"
    .byte 105, 110, 101, 10, 10, 0             # "ine\n\n\0"

state_prefix:
    .byte 32, 32, 0                            # "  \0"

event_str:
    .byte 32, 43, 32, 69, 118, 101, 110, 116  # " + Event"
    .byte 32, 0                                # " \0"

arrow:
    .byte 32, 45, 62, 32, 0                    # " -> \0"

final_state_msg:
    .byte 10, 70, 105, 110, 97, 108, 32        # "\nFinal "
    .byte 115, 116, 97, 116, 101, 58, 32, 0    # "state: \0"

# Event sequence to process
# Format: sequence of event codes, terminated by 255
# Events: 0=TIMER, 1=EMERGENCY, 2=RESET
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
