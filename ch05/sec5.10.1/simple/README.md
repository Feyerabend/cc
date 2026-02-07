
## Assembly Code Optimisation Comparison

### Function: `constant_computation()`

#### Without Optimisation (-O0)
```assembly
constant_computation:
    pushq   %rbp
    movq    %rsp, %rbp
    movl    $10, -16(%rbp)      ## Store a = 10
    movl    $20, -12(%rbp)      ## Store b = 20
    movl    $30, -8(%rbp)       ## Store c = 30
    movl    -16(%rbp), %edx     ## Load a
    movl    -12(%rbp), %eax     ## Load b
    addl    %edx, %eax          ## a + b
    imull   -8(%rbp), %eax      ## (a + b) * c
    subl    $15, %eax           ## - 15
    movl    %eax, -4(%rbp)      ## Store result
    movl    -4(%rbp), %eax      ## Load result for return
    popq    %rbp
    ret
```
*Lines: ~13 | Stack operations: Many | Computations: Runtime*

#### With Optimisation (-O3)
```assembly
constant_computation:
    movl    $885, %eax          ## Pre-computed: (10+20)*30-15 = 885
    ret
```
*Lines: 2 | Stack operations: None | Computations: Compile-time*

*Optimisation: CONSTANT FOLDING*
- Entire computation done at compile-time
- 13 instructions -> 2 instructions (85% reduction!)
- No memory access, no arithmetic operations at runtime



### Function: `array_sum()`

#### Without Optimisation (-O0)
```assembly
array_sum:
    pushq   %rbp
    movq    %rsp, %rbp
    movl    %edi, -20(%rbp)     ## Store parameter n
    movl    $0, -8(%rbp)        ## sum = 0
    movl    $0, -4(%rbp)        ## i = 0
.L3:
    movl    -4(%rbp), %eax      ## Load i
    cmpl    -20(%rbp), %eax     ## Compare i with n
    jge     .L2                 ## Exit if i >= n
    movl    -4(%rbp), %eax      ## Load i
    addl    %eax, -8(%rbp)      ## sum += i
    addl    $1, -4(%rbp)        ## i++
    jmp     .L3                 ## Loop back
.L2:
    movl    -8(%rbp), %eax      ## Return sum
    popq    %rbp
    ret
```
*Lines: ~16 | Each iteration: 6-7 instructions*

#### With Optimisation (-O3)
```assembly
array_sum:
    testl   %edi, %edi          ## Test if n <= 0
    jle     .L4
    leal    -1(%rdi), %eax      ## n - 1
    leal    -2(%rdi), %edx      ## n - 2
    imulq   %rax, %rdx          ## (n-1) * (n-2)
    shrq    %rdx                ## Divide by 2
    leal    -1(%rdi,%rdx), %eax ## Final calculation
    ret
.L4:
    xorl    %eax, %eax          ## Return 0
    ret
```
*Lines: ~10 | Loop: ELIMINATED! Formula: n*(n-1)/2*

*Optimisations:*
1. *STRENGTH REDUCTION*: Loop converted to mathematical formula
2. *LOOP ELIMINATION*: No iteration at runtime
3. *CONSTANT PROPAGATION*: Uses closed-form solution



### Real-World Impact Example

```c
// This code:
int x = 5 * 1024;  // Common pattern: multiply by power of 2

// -O0 generates:
movl    $5, %eax
imull   $1024, %eax    ## Slow multiplication

// -O3 generates:
movl    $5120, %eax    ## Pre-computed OR
sall    $10, %eax      ## Shift left by 10 (x * 2^10)
```

*Performance difference:*
- Multiplication: ~3-4 CPU cycles
- Shift: ~1 CPU cycle
- Pre-computed constant: 0 cycles at runtime!



### Key Takeaways

| Optimisation Level | Code Size | Runtime Speed | Use Case |
|--------------------|-----------|---------------|----------|
| *-O0* | Largest | Slowest | Debugging |
| *-O1* | Medium | Faster | Quick builds |
| *-O2* | Smaller | Fast | Production default |
| *-O3* | Smallest† | Fastest | Performance-critical |

† May be larger due to inlining and unrolling

### Techniques Demonstrated

1. *Constant Folding* - Compute at compile-time
2. *Dead Code Elimination* - Remove unused variables
3. *Strength Reduction* - Replace expensive ops with cheap ones
4. *Loop Optimisation* - Unroll, eliminate, or simplify
5. *Register Allocation* - Keep values in CPU registers
6. *Instruction Scheduling* - Reorder for better pipelining

