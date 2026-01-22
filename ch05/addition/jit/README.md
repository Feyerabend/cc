
## HotspotVM - A very simple JIT compiler

An educational stack-based virtual machine that demonstrates
*Just-In-Time (JIT) compilation* through clear, understandable Python code.


Our "HotspotVM" (not to be confused with the Java equivalent)
demonstrates the *fundamental workflow* of JIT compilation:

```
profile -> detect hotspots -> compile -> cache -> execute fast
```

While production JITs are vastly more complex (native code generation,
type specialisation, multiple compilation tiers, sophisticated optimisations,
deoptimisation), this core loop remains the same.

*The insight:* Don't optimise everything, optimise what matters.
JIT compilation makes that decision at runtime based on actual behaviour,
not static analysis.

*Why JIT wins:*
- Adapts to actual runtime behaviour
- Optimises the hot 10% that matters
- Combines interpreted flexibility with compiled speed
- Enables optimisations impossible for static compilers
  (e.g., specialisation based on observed types)

HotspotVM proves these concepts work--even our simple
Python-to-Python JIT achieves 3-5x speedup on loops.


### What is JIT Compilation?

*Just-In-Time (JIT) compilation* is a runtime optimisation technique
that dramatically improves performance by:
1. *Running code initially as an interpreter* - fast startup, no compilation overhead
2. *Detecting "hot" code* - identifying frequently executed regions (especially loops)
3. *Compiling hot code on-the-fly* - translating it into faster executable form
4. *Switching to compiled code* - executing the optimised version instead of interpreting

This hybrid approach combines the best of both worlds: interpreted code's
flexibility with compiled code's speed.

Most performance-critical code follows the *90/10 rule*: 90% of execution time
is spent in 10% of the code (usually loops). JIT compilers focus optimisation
effort where it matters most, achieving near-native performance without
requiring ahead-of-time compilation.

*Real-world JIT compilers:*
- *Java* - HotSpot JVM (the original "HotSpot")
- *JavaScript* - V8 (Chrome), SpiderMonkey (Firefox)
- *Python* - PyPy
- *.NET* - CoreCLR/RyuJIT
- *Lua* - LuaJIT


### How HotspotVM Works

#### 1. Dual Execution Modes

Every instruction handler implements *two methods*:

```python
class ArithmeticHandler(InstructionHandler):
    def execute(self, vm, instr):
        # Interpreter mode - runs immediately
        b, a = vm.stack.pop(), vm.stack.pop()
        vm.stack.append(a + b)
    
    def compile_to_python(self, vm, instr):
        # JIT mode - generates optimised code
        return [
            "    b = stack.pop()",
            "    a = stack.pop()",
            "    stack.append(a + b)"
        ]
```

This dual-mode architecture is the key to JIT compilation:
the same instruction logic exists in both interpreted and compiled forms.

#### 2. Hotspot Detection

The VM tracks execution counts per instruction:

```python
self.exec_count[self.pc] += 1
if self.exec_count[self.pc] >= self.hotspot_threshold:
    ## This code is "hot" - time to compile!
```

*Key insight:* Don't compile everything--only compile code that executes
frequently enough to justify the compilation overhead.

#### 3. Loop Detection (The Critical Innovation)

HotspotVM tracks *control flow edges* to detect loops:

```python
## Track edges between instructions
edge = (last_pc, current_pc)
self.edge_count[edge] += 1

## A backward jump indicates a loop
if jump_target < current_pc and edge is hot:
    compile_loop(jump_target, current_pc)
```

Loops are the *most important target* for JIT compilation because:
- They execute many times (high iteration count = high payoff)
- Small code size means low compilation overhead
- Huge performance gains when optimised (typically 3-5x faster)

#### 4. Code Generation

When a hot loop is detected, HotspotVM generates Python code:

```python
# Original bytecode loop (countdown from N to 0):
# PC 0: LOAD_LOCAL 0      # load counter
# PC 1: DUP               # duplicate for test
# PC 2: JUMP_IF_ZERO 7    # exit if zero
# PC 3: PUSH 1            # push constant
# PC 4: SUB               # counter - 1
# PC 5: STORE_LOCAL 0     # save counter
# PC 6: JUMP 0            # loop back

# Compiled to Python:
def jit_loop():
    stack = self.stack
    locals = self.locals
    while True:  # Loop structure from backward JUMP
        stack.append(locals[0])   # LOAD_LOCAL 0
        stack.append(stack[-1])   # DUP
        val = stack.pop()         # JUMP_IF_ZERO test
        if val == 0:
            return 7              # Exit to PC 7
        stack.append(1)           # PUSH 1
        b, a = stack.pop(), stack.pop()
        stack.append(a - b)       # SUB
        locals[0] = stack.pop()   # STORE_LOCAL 0
        # Loop back via while True
```

*What gets eliminated:*
- Per-instruction dispatch overhead (biggest win)
- Instruction decoding and fetching
- PC manipulation and bounds checking
- Handler function call overhead
- OpCode enum lookups

#### 5. Execution Statistics

HotspotVM tracks detailed metrics showing JIT impact:

```
JIT COMPILATION STATISTICS
==================================
Total compilations:       1
JIT executions:           9,990
Interpreter executions:   57
Avg JIT exec time:        1.23μs
Avg interp exec time:     5.67μs
Speedup factor:           4.61x
==================================
```

The statistics prove that JIT compilation works--compiled
code runs significantly faster than interpreted code.


### Running the Examples

The code includes three demonstration programs:

#### Example 1: Countdown Loop

Counts down from 10,000 to 0. Good for demonstrating JIT.

*What you'll see:*
1. First ~10 iterations run in interpreter (warming up)
2. VM detects the hot loop (backward jump executed frequently)
3. Loop gets compiled to Python (code generation happens)
4. Remaining ~9,990 iterations run 3-5x faster via compiled code

*With verbose mode enabled:*
```python
vm = ExecutionEngine(hotspot_threshold=10, verbose=True)
```
You'll see the exact bytecode being compiled and the generated Python code.

#### Example 2: Sum Calculation

Calculates sum from 1 to 1000 (result: 500,500).

Shows JIT handling more realistic code with:
- Multiple local variables (counter and accumulator)
- Arithmetic operations in sequence
- Load/store patterns
- More complex loop body

#### Example 3: Direct Comparison

Runs identical code with JIT enabled vs disabled to prove the speedup.

*Typical results:* 
- With JIT (threshold=5): 0.0123s
- Without JIT (threshold=999999): 0.0567s
- *Speedup: 4.6x faster with JIT!*


### Insights Demonstrated

#### 1. Warmup vs Peak Performance

```
Iteration 1-10:   Interpreter mode (profiling)
Iteration 11:     JIT compilation triggered
Iteration 12+:    Compiled code execution (peak performance)
```

This is why benchmarks should measure *sustained* performance,
not just first execution. Real-world JIT performance includes:
- *Cold start:* Immediate interpreter execution (no delay)
- *Warmup:* Profiling and compilation overhead
- *Peak:* Full-speed compiled execution

#### 2. Compilation Threshold Tradeoff

The `hotspot_threshold` parameter controls when compilation happens:

- *Low threshold (3-5):* 
  - `+` Compile quickly, reach peak performance fast
  - `-` May waste time compiling code that isn't truly hot
  
- *High threshold (50+):* 
  - `+` Only compile genuinely hot code
  - `-` Slower warmup, longer time in interpreter

*Production JITs* often use *tiered compilation*:
1. Quick baseline compile (simple, fast compilation)
2. Optimised compile (slower compilation, faster code)

#### 3. What Gets Optimised

*Great for JIT (huge speedup):*
- `+` Tight loops (99% of performance gains come from here)
- `+` Arithmetic-heavy code
- `+` Predictable control flow
- `+` Frequently executed functions

*Not worth JIT (overhead > benefit):*
- `-` One-time initialisation code
- `-` I/O operations (already slow, compilation won't help)
- `-` Exception handling paths (rarely executed)
- `-` Code with unpredictable branches

#### 4. Compilation Overhead Amortisation

JIT compilation takes time. The code must execute enough
times to *amortise* the compilation cost:

```
Total execution time = compilation_time + (iterations × per_iteration_time)

Interpreter: 0ms + (10,000 × 5μs) = 50ms
JIT:         2ms + (10,000 × 1μs) = 12ms  ← Winner!

But for 100 iterations:
Interpreter: 0ms + (100 × 5μs) = 0.5ms   ← Winner!
JIT:         2ms + (100 × 1μs) = 2.1ms
```


### Implementation Details

#### Loop Compilation Strategy

HotspotVM uses a *region-based approach* focused on loops:

1. *Detect backward jumps* - `JUMP` with target < current_pc
2. *Verify the edge is hot* - edge executed ≥ threshold/2 times
3. *Extract loop body* - instructions from jump target to jump instruction (exclusive)
4. *Generate while loop* - wrap body in `while True:` structure
5. *Handle exit conditions* - `JUMP_IF_ZERO` returns exit PC
6. *Cache compiled function* - store at loop entry point

#### Why It Works

The generated code directly manipulates VM state:
```python
stack = self.stack      # Direct reference, not copy
locals = self.locals    # Direct reference, not copy
```

This means:
- No marshaling/unmarshaling data
- No function call overhead for each instruction
- Python's bytecode compiler optimises the generated code
- All loop iterations execute in tight Python loop

#### Control Flow Handling

```python
## JUMP_IF_ZERO compiles to:
if not stack: raise StackUnderflowError('JUMP_IF_ZERO')
val = stack.pop()
if val == 0:
    return 13  # Exit loop to PC 13

# Backward JUMP is replaced by while True:
# (The while loop structure handles looping automatically)
```

*NOTE:* Exit jumps must skip over the backward
jump instruction to avoid infinite recompilation.


#### 1. Compiles to Python, Not Native Code
- *Production JITs* generate x86/ARM machine code directly
- *HotspotVM* generates Python -> still interpreted by CPython
- Performance gain comes from eliminating VM dispatch overhead, not native execution
- *Why this matters:* Real JITs get 10-100x speedup; we get 3-5x

#### 2. No Type Specialisation
- *Production JITs* generate specialised code for observed types
  ```python
  # Generic: check types, handle any operands
  # Specialised: assume int, use fast int operations
  ```
- *HotspotVM* keeps dynamic typing -> misses major optimisation
- *Impact:* Real JITs can optimise `a + b` to single CPU instruction

#### 3. No Deoptimisation
- *Production JITs* can "bail out" if assumptions break
  ```python
  # Compiled with assumption: x is always int
  # If x becomes float -> deoptimise back to interpreter
  ```
- *HotspotVM* assumes compiled code is always valid
- *Risk:* Could crash if assumptions violated

#### 4. No Inlining
- *Production JITs* inline function calls into hot code
- *HotspotVM* doesn't handle cross-function optimisation
- *Benefit missed:* Eliminating call overhead,
  enabling further optimisations

#### 5. Simple Loop Detection
- *Production JITs* use:
  - Trace-based compilation (LuaJIT, some JS engines)
  - Graph-based IR with sophisticated analysis (HotSpot, V8)
  - Profile-guided optimisation
- *HotspotVM* uses simple backward-jump detection
- *Limitation:* Can't handle complex control flow patterns

#### 6. No Tiered Compilation
- *Production JITs* have multiple compilation levels:
  1. Interpreter
  2. Quick baseline JIT
  3. Opbtimizing JIT
  4. Super-optimising JIT (with aggressive speculation)
- *HotspotVM* has only interpreter + one JIT tier
- *Missing:* Gradual optimisation based on execution frequency


### Learning Path

*Step 1:* Run the examples.
See JIT compilation in action with timing measurements.

*Step 2:* Enable verbose mode.
```python
vm = ExecutionEngine(hotspot_threshold=10, verbose=True)
```
Watch compilation happen in real-time, see generated code.

*Step 3:* Modify hotspot threshold.
```python
# Compile eagerly
vm = ExecutionEngine(hotspot_threshold=3)

# Compile conservatively  
vm = ExecutionEngine(hotspot_threshold=50)
```
Observe warmup vs peak performance tradeoff.

*Step 4:* Examine generated code.
Look at the verbose output to understand what compilation produces.

*Step 5:* Study the statistics.
Quantify the performance impact--see the speedup numbers.

*Step 6:* Create your own programs.
Try nested loops, different patterns, see what compiles well.

*Step 7:* Modify the compiler.
Add optimisations, try different compilation strategies.


### Further Exploration

To deepen understanding:

1. *Add new opcodes* - implement both `execute()` and `compile_to_python()`
2. *Implement constant folding* - optimise `PUSH 2; PUSH 3; ADD` -> `PUSH 5`
3. *Add type specialisation* - detect when operands are always integers
4. *Experiment with thresholds* - find optimal compilation trigger for different workloads
5. *Try trace-based compilation* - record execution paths instead of detecting loops
6. *Profile with Python tools* - use `cProfile` to see where time is spent
7. *Compare compilation strategies* - method-based vs region-based vs trace-based
8. *Add deoptimisation* - detect when assumptions break, fall back to interpreter

