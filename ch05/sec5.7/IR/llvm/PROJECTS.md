
## Projects on a RISC-V Emulator and LLVM

### Deepening RISC-V Knowledge: Hands-On Projects and Study Paths

Building on the RISC-V compilation pipeline from [ILOC](./../iloc/) and the new LLVM IR generator
in `llvm.py`, which showcases another intermediate representation for code transformation,
there are plenty of ways to expand your understanding of RISC-V beyond software simulations.
The focus here shifts to practical learning through reading key resources, examining
real implementations, and hands-on experimentation—especially on hardware like the
previous hands-on Raspberry Pi Pico 2, which features the RP2350 microcontroller with dual RISC-V
Hazard3 cores (optional alongside ARM). These projects emphasise progressive skill-building,
starting from theoretical study and moving to tangible builds, while clarifying concepts
like instruction set architecture (ISA), pipelining, and hardware-software integration.
Each idea includes suggestions for tying back to your existing codebase, such as using
LLVM IR as a backend alternative.


#### Guided Reading and Analysis: Dissecting the RISC-V Specification

Kick off with a structured study of the official RISC-V International documentation,
beginning with the unprivileged ISA spec (available as a free PDF) to grasp core instructions,
privilege levels, and extensions like the M (multiply/divide) used in your VM.
Dedicate time to examining sample code snippets in the spec, then cross-reference them
with your pipeline's ILOC-to-RISC-V translation in `iloc_to_riscv.py`--rewrite a few TAC
instructions from `llvm.py`'s output into RISC-V manually to see differences in expressiveness.
To deepen, read "The RISC-V Reader" book for historical context and comparisons to other ISAs
like x86 or ARM, annotating how LLVM IR's typed, SSA form could map to RISC-V's register-based
model. This project clarifies why RISC-V's modularity (e.g., base RV32I plus extensions)
makes it adaptable, and you could extend it by creating a personal cheat sheet or blog post
summarizing key opcodes, testable via your assembler in asm.py.

* Patterson, D. A., & Waterman, A. (2017). *The RISC-V reader: An open architecture atlas*. Strawberry Canyon LLC.


#### Emulator Enhancement: Building a Cycle-Accurate Simulator

Dive into studying open-source RISC-V emulators like QEMU or Spike (from the RISC-V foundation)
by downloading their code and running your compiled binaries from the pipeline through them,
comparing outputs to your custom VM in `vm.py`. Examine their handling of interrupts and memory
models, then *upgrade* your VM to be cycle-accurate—track clock cycles per instruction based
on a simple 5-stage pipeline model from textbooks like "Computer Organization and Design".
Integrate LLVM by compiling `llvm.py`'s IR output with the LLVM toolchain (install Clang/LLVM
locally) to generate RISC-V binaries, then debug discrepancies in emulation. This hands-on
examination reveals performance nuances, such as branch prediction impacts, and clarifies
emulation pitfalls like endianness, making your software toolchain more robust for real hardware testing.

* Patterson, D. A., & Hennessy, J. L. (2004). *Computer organization and design: The hardware/software interface* (3rd ed.). Elsevier.


#### Hardware Exploration: Implementing a Basic RISC-V Core in Verilog

For a hardware-focused study, examine open RISC-V core designs like the [SERV](https://github.com/olofk/serv)
(world's smallest RISC-V core) or [Ibex](https://github.com/lowRISC/ibex), reading their Verilog/VHDL source
to understand datapath elements like ALU and register file. Use tools like Verilator for simulation,
synthesizing a minimal core and running a simple program (e.g., from the AST examples) to observe waveforms
in GTKWave. To connect to software, generate machine code via your pipeline or LLVM, then load it into the
simulated core. This project demystifies how RISC-V instructions execute at the gate level, highlighting
differences from high-level IRs like in `llvm.py`, and prepares you for FPGA prototyping--start with a
cheap board like the TinyFPGA to test, clarifying concepts like hazards and forwarding through iterative
debugging.


#### Raspberry Pi Pico 2 Integration: Bare-Metal RISC-V Programming

Leverage the RPi Pico 2's switchable RISC-V cores by studying the RP2350 datasheet and SDK docs from
Raspberry Pi, focusing on enabling Hazard3 mode via fuses or bootloaders. Start with a simple bare-metal
project: port your compilation pipeline's output to run directly on the Pico, using the Pico SDK to
handle UART output instead of 'ecalls' in the VM. Compile LLVM IR from `llvm.py` to RISC-V ELF with
'llc' (LLVM's codegen tool), then flash it via OpenOCD. Experiment by adding peripherals like GPIO
blinking tied to computation results (e.g., light an LED based on 'z' from `sample_complex`),
examining assembly in a debugger like gdb. This real-hardware trial clarifies RISC-V's efficiency
in embedded scenarios, contrasting with simulated runs, and you could extend it to measure power
consumption with a multimeter for optimisation insights.


#### Benchmarking Suite: Performance Study Across Implementations

Create a test suite by studying benchmarks like CoreMark or Dhrystone, adapted for RISC-V—read
their specs and implement a few in your mini-language from earlier project ideas, generating
code via AST-to-ILOC/LLVM paths. Run them on your VM, QEMU, and Pico 2 hardware, analysing metrics
like instructions per cycle (IPC) with tools like perf or custom counters. Examine optimisations
by applying TAC passes from `llvm.py` (e.g., constant folding) and re-testing. This comparative
study highlights RISC-V's strengths in scalability, clarifying why it's popular in IoT (like on Pico),
and results in a reusable framework for evaluating future extensions, such as vector instructions
for machine learning workloads.


#### Community-Driven Extension: Contributing to Open RISC-V Projects

Wrap up with active learning by examining repositories like the RISC-V software ecosystem here on GitHub,
such as porting a library (e.g., a simple math lib) to run on Pico 2. Read forums like the RISC-V
subreddit or Discord for discussions on implementations, then propose a patch--perhaps adding LLVM
backend support for a custom extension in your pipeline. Document your findings in a study log,
tying back to hardware by testing on Pico with real sensors (e.g., temperature computation triggering
outputs). This project fosters collaborative knowledge, clarifying open-source dynamics in ISA
development, and positions you to explore advanced topics like custom instructions for acceleration.


