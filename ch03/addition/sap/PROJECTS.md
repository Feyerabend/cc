
## Projects

These projects build on each other, so you can progress sequentially.
The codebase is self-contained, so you can compile it with something like
`gcc sap_vm.c sap_vm_samples.c sap_vm_debug.c sap_vm_debug_support.c sap_vm_test.c -o sap_vm_test`
(adjust for your setup) to run tests or the debugger.


### Beginner Projects: Understanding and Documentation

These focus on exploring the code without major changes, helping you grasp
the "what's happening" in the VM.

1. *Project: Run and Document the Sample Programs*
   - *What*: Compile and run the existing sample programs (e.g., Fibonacci, factorial)
     using the built-in debugger, then create a simple document explaining what each
     one does, step by step.
   - *Why*: This builds familiarity with the VM's behavior without coding. It helps you
     understand core concepts like opcodes (e.g., LDA for load accumulator), addressing
     modes (e.g., immediate vs. direct), and how instructions execute in a loop
     or with conditions.
   - *How*:
     - Compile the debugger: `gcc sap_vm*.c -o sap_vm_debug`.
     - Run it: `./sap_vm_debug`.
     - In the debugger prompt (`sap-vm>`), type `load fib` (or another sample like
       `fact` or `arith`), then `disasm` to see the disassembled code, `run` to execute,
       and `state` to check the final accumulator value.
     - Document in a Markdown file or notebook: For each sample, list the instructions
       (from `disasm`), explain what they do (e.g., "LDA loads a value into the accumulator;
       here it initializes n=10 for Fibonacci"), and note the output (e.g., "F(10) = 55").
       Include screenshots of debugger output.
     - Bonus: Use `trace on` before running to log each instruction's execution and explain
       flags (zero, negative, etc.) in your doc.
     - Time estimate: 1-2 hours. Tools: Text editor, terminal.

2. *Project: Map the Codebase Architecture*
   - *What*: Create a visual or written diagram/document explaining the overall structure of
     the codebase, including how files interact
     (e.g., sap_vm.c handles core execution, sap_vm_debug.c provides the CLI).
   - *Why*: This demystifies the "big picture"--why the VM has separate structs for CPU and
     flags, how memory is managed (1024 words), and how errors are handled--before diving into modifications.
   - *How*:
     - Read through the headers (sap_vm.h, sap_vm_config.h) first to note key defines
       (e.g., MEMORY_SIZE=1024) and enums (opcodes like OP_ADD).
     - Sketch a flowchart:
       Start with vm_init() -> vm_step() loop -> opcode handling in vm_step() -> flag updates.
     - Use tools like Draw.io or plain text to map functions: e.g., "vm_encode_instruction()
       packs opcode/mode/operand into 16 bits; vm_decode_instruction() unpacks them."
     - Explain key flows, like how resolve_operand() handles different addressing modes
       (e.g., indirect fetches a pointer first).
     - Output: A PDF or README addition with your diagram and notes.
     - Time estimate: 2-4 hours. Tools: Diagramming software.


### Intermediate Projects: Individual Code Improvements

These involve modifying the code to fix issues, add features, or optimise,
building your C programming skills.

3. *Project: Add Basic Input/Output Instructions*
   - *What*: Extend the VM with new opcodes for I/O (e.g., OP_IN for reading from stdin,
     OP_OUT for printing to stdout), then update a sample program to use them
     (e.g., modify the counting demo to print each number).
   - *Why*: The current VM lacks I/O, limiting interactivity. This teaches you how to
     extend an instruction set, handle side effects, and test changes--why opcodes are
     masked (OPCODE_MASK) and how to avoid breaking existing code.
   - *How*:
     - In sap_vm.h, add OP_IN and OP_OUT to opcode_t (after OP_RTS).
     - In sap_vm.c, update vm_step(): Add cases for the new opcodes. For OP_IN,
       use scanf() to read into the accumulator; for OP_OUT, printf() the accumulator.
     - Update opcode_to_string() and vm_encode_instruction() to support them.
     - Modify sap_vm_samples.c's load_counting_demo(): Insert OP_OUT after incrementing the counter.
     - Test: Compile, load the sample, run, and verify output. Use the tests in sap_vm_test.c
       as a template to add your own assert() for I/O.
     - Handle errors: e.g., if scanf fails, set VM_ERROR.
     - Time estimate: 4-6 hours. Tools: C compiler, debugger.

4. *Project: Optimise Memory Access and Add Profiling*
   - *What*: Profile the VM's performance (e.g., count memory reads/writes per opcode),
     then optimise slow paths (e.g., indirect addressing in resolve_operand()).
   - *Why*: The VM uses simple arrays for memory, but real VMs optimize for speed.
     This helps you understand performance bottlenecks (why indirect mode is slower)
     and how to measure them, improving code efficiency.
   - *How*:
     - Add counters to sap_vm_t (e.g., uint64_t mem_reads, mem_writes).
     - In vm_read_memory() and vm_write_memory(), increment counters.
     - After running (in vm_run()), print stats: "Memory reads: X, writes: Y".
     - Optimise: Cache frequent accesses (e.g., for indexed mode, precompute
       if possible) or inline small functions.
     - Test with samples: Run Fibonacci before/after, compare cycle_count
       (already tracked).
     - Use code_execution tool (if you have Python access) to benchmark:
       Write a script to time multiple runs.
     - Time estimate: 6-8 hours. Tools: Compiler with -O2 flag, timer functions (e.g., clock()).


### Advanced Projects: Group Collaboration and LLM Integration

These scale to teams (e.g., via GitHub) and incorporate AI tools like LLMs
(e.g., Grok, ChatGPT) for generation or analysis.

5. *Project: Group-Developed Assembler*
   - *What*: As a group (2-4 people), build a simple assembler that converts
     text assembly (e.g., "LDA #42") to binary for the VM, integrating it with the debugger.
   - *Why*: The VM loads programs manually (via vm_encode_instruction());
     an assembler makes it programmable. Group work teaches collaboration
     (why divide tasks: one for parser, one for linker), version control,
     and real-world tooling.
   - *How*:
     - Divide roles: You handle parsing (strtok() for opcodes/modes), another
       person encodes (using vm_encode_instruction()), a third integrates with vm_load_program().
     - Use Git: Fork the codebase, add a new file (sap_assembler.c) with a main()
       that reads .asm files and outputs .bin.
     - Support labels (e.g., "LOOP: JMP LOOP") by resolving addresses in a second pass.
     - Test: Write group tests, assemble a sample, load/run in debugger.
     - Collaborate: Use Discord/Slack for discussions; merge PRs.
     - Time estimate: 10-15 hours per person over a week. Tools: GitHub, assembler
       syntax reference (from opcode_to_string()).

6. *Project: LLM-Assisted Program Generation and Debugging*
   - *What*: Use an LLM (e.g., query me or another AI) to generate assembly programs
     for the VM (e.g., "Write code to sort an array"), then debug and run them.
     Extend to auto-debug errors.
   - *Why*: LLMs excel at code generation but need human oversight. This explores
     AI-human collaboration: why LLMs might misuse addressing modes, how to prompt
     effectively, and integrating AI into workflows for complex tasks like optimisation.
   - *How*:
     - Prompt an LLM: "Generate SAP VM assembly for bubble sort on array at 0x100 (size 10).
       Use opcodes like LDA, CMP, JZ."
     - Manually assemble (or use your assembler from Project 5) and load into the VM.
     - Debug: If it fails (e.g., overflow), use the debugger's trace/breakpoints, then
       re-prompt the LLM: "Fix this error: [paste VM error]".
     - Advanced twist: Add a script (Python) to interface: Run VM via subprocess,
       feed output to LLM for auto-fixes.
     - Group variant: One person generates, another debugs, third tests.
     - Time estimate: 8-12 hours. Tools: LLM API/interface, Python for automation.

7. *Project: Advanced VM Extensions with Hardware Simulation*
   - *What*: Extend the VM to simulate peripherals (e.g., a simple display or interrupts),
     then build a mini-game (e.g., Tic-Tac-Toe) using assembly. Use LLMs for game logic ideas.
   - *Why*: This pushes boundaries: Why add interrupts (for async events)? It combines
     low-level systems (VM) with high-level apps, teaching emulation (how real CPUs handle I/O)
     and creative problem-solving.
   - *How*:
     - Add opcodes: e.g., OP_INT for interrupts; map memory regions to "devices"
       (e.g., write to 0xFFF prints a char).
     - Use LLM: "Suggest assembly for Tic-Tac-Toe board check in SAP VM."
     - Implement: Update vm_step() for new logic, add handler structs.
     - Group/LLM: Collaborate on game features; use AI to generate boilerplate code.
     - Test: Run in debugger, add benchmarks for interrupt overhead.
     - Time estimate: 15-20+ hours. Tools: Extended compiler flags (-g for debugging),
       Valgrind for leaks.

