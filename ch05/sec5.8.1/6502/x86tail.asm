; Fibonacci (tail recursive) in x86 assembly
section .text
global _start

_start:
    ; Setup arguments: n = 10, accumulator a = 0, b = 1
    mov eax, 10  ; n
    mov ebx, 0   ; a (F(n-2))
    mov ecx, 1   ; b (F(n-1))
    call fibonacci_tail

    ; Exit
    mov eax, 1
    int 0x80

fibonacci_tail:
    ; Base case: if n == 0, return a
    cmp eax, 0
    je .done_a

    ; Base case: if n == 1, return b
    cmp eax, 1
    je .done_b

    ; Tail-recursive step:
    ; Update a = b, b = a + b, n = n - 1
    add ebx, ecx  ; a = a + b
    xchg ebx, ecx ; swap a and b (now a = b, b = a + b)
    dec eax       ; n = n - 1
    jmp fibonacci_tail ; tail call (no stack manipulation)

.done_a:
    mov eax, ebx ; return a
    ret

.done_b:
    mov eax, ecx ; return b
    ret
