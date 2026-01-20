; Fibonacci (tail recursive) for MOS 6502
; Calculates F(10) using tail recursion
; Result stored in memory location $0200
;
; Tail-recursive function: fib(n, a, b)
;   if n = 0: return a
;   if n = 1: return b
;   else: fib(n-1, b, a+b)

.org $8000

reset:
    ; Initialize: n=10, a=0, b=1
    lda #10         ; n = 10
    ldx #0          ; a = 0
    ldy #1          ; b = 1
    jsr fibonacci_tail
    
    ; Store result in $0200
    sta $0200
    
    ; Halt (infinite loop)
stop:
    jmp stop

; Tail-recursive Fibonacci
; Input:  A = n, X = a, Y = b
; Output: A = result
fibonacci_tail:
    ; Base case: n == 0? return a
    cmp #0
    beq return_a
    
    ; Base case: n == 1? return b
    cmp #1
    beq return_b
    
    ; Recursive: fib(n-1, b, a+b)
    ; Save n temporarily
    pha
    
    ; Calculate new_b = a + b
    txa             ; A = a
    sty $00         ; Save b in zero page
    clc
    adc $00         ; A = a + b
    tay             ; Y = new b = a + b
    
    ; Set new_a = old b
    lda $00
    tax             ; X = new a = old b
    
    ; Set new_n = n - 1
    pla
    sec
    sbc #1
    
    ; Tail call - jump instead of jsr/rts
    jmp fibonacci_tail

return_a:
    txa             ; Return a
    rts

return_b:
    tya             ; Return b
    rts

; Interrupt vectors
.org $FFFA
.word $0000      ; NMI vector
.word reset      ; Reset vector
.word $0000      ; IRQ vector
