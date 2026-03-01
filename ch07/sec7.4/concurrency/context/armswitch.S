.syntax unified
.thumb
.text

// Context structure offsets
.equ CTX_R4,  0
.equ CTX_R5,  4
.equ CTX_R6,  8
.equ CTX_R7,  12
.equ CTX_R8,  16
.equ CTX_R9,  20
.equ CTX_R10, 24
.equ CTX_R11, 28
.equ CTX_SP,  32
.equ CTX_LR,  36

// Function: context_switch
// Parameters: r0 = current task context pointer, r1 = next task context pointer
// This function saves the current context and restores the next context
.global context_switch
.type context_switch, %function
context_switch:
    // Save current context (callee-saved registers)
    str r4,  [r0, #CTX_R4]     // Save r4
    str r5,  [r0, #CTX_R5]     // Save r5
    str r6,  [r0, #CTX_R6]     // Save r6
    str r7,  [r0, #CTX_R7]     // Save r7
    str r8,  [r0, #CTX_R8]     // Save r8
    str r9,  [r0, #CTX_R9]     // Save r9
    str r10, [r0, #CTX_R10]    // Save r10
    str r11, [r0, #CTX_R11]    // Save r11
    
    // Save stack pointer and link register
    mov r2, sp
    str r2,  [r0, #CTX_SP]     // Save stack pointer
    str lr,  [r0, #CTX_LR]     // Save link register
    
    // Load next context (callee-saved registers)
    ldr r4,  [r1, #CTX_R4]     // Restore r4
    ldr r5,  [r1, #CTX_R5]     // Restore r5
    ldr r6,  [r1, #CTX_R6]     // Restore r6
    ldr r7,  [r1, #CTX_R7]     // Restore r7
    ldr r8,  [r1, #CTX_R8]     // Restore r8
    ldr r9,  [r1, #CTX_R9]     // Restore r9
    ldr r10, [r1, #CTX_R10]    // Restore r10
    ldr r11, [r1, #CTX_R11]    // Restore r11
    
    // Restore stack pointer and link register
    ldr r2,  [r1, #CTX_SP]     // Load stack pointer
    mov sp, r2                 // Restore stack pointer
    ldr lr,  [r1, #CTX_LR]     // Restore link register
    
    bx lr                      // Return to the new task

// Function: init_task_context
// Parameters: r0 = context pointer, r1 = stack pointer, r2 = task function address
// This function initializes a task context for first-time execution
.global init_task_context
.type init_task_context, %function
init_task_context:
    // Clear all general purpose registers in context
    movs r3, #0
    str r3, [r0, #CTX_R4]
    str r3, [r0, #CTX_R5]
    str r3, [r0, #CTX_R6]
    str r3, [r0, #CTX_R7]
    str r3, [r0, #CTX_R8]
    str r3, [r0, #CTX_R9]
    str r3, [r0, #CTX_R10]
    str r3, [r0, #CTX_R11]
    
    // Set up stack pointer and entry point
    str r1, [r0, #CTX_SP]      // Set stack pointer
    str r2, [r0, #CTX_LR]      // Set task function as return address
    
    bx lr                      // Return

// Example usage structure (C-style definition for reference):
/*
typedef struct {
    uint32_t r4, r5, r6, r7;      // Callee-saved registers
    uint32_t r8, r9, r10, r11;    // More callee-saved registers  
    uint32_t sp;                   // Stack pointer
    uint32_t lr;                   // Link register (return address)
} task_context_t;
*/