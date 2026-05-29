## Exercises

### The Idea of a Virtual Machine

#### What a VM Is

1. *What does it mean to say that a virtual machine is an abstraction?*
   - What real things does it hide, and what does it make visible? Give a concrete example from everyday computing.

2. *Why would someone want to run programs on a machine that does not physically exist?*
   - Think about portability, isolation, and safety. What does a VM give you that running on real hardware does not?

3. *Explain what bytecode is and how it differs from source code and machine code.*
   - Where does bytecode sit in the chain from human-written program to hardware execution?

4. *What is the difference between an interpreter and a compiler?*
   - A VM typically uses one or both. Describe how each transforms a program and at what point that transformation happens.

5. *Why does the Java Virtual Machine matter for the history of computing?*
   - Research the original "write once, run anywhere" promise. What problem was it solving, and how well did it work?

6. *What is a process virtual machine, and how does it differ from a system virtual machine?*
   - Give one example of each. Which kind does this chapter focus on?

7. *In what sense is a VM a contract between a language and its implementation?*
   - Who are the two parties to this contract? What does each one promise?


#### Stacks and Registers

1. *What is a stack, and what are its two fundamental operations?*
   - Describe push and pop. What constraint do they impose on the order in which data is accessed?

2. *Trace the following sequence of stack operations by hand: push 3, push 7, push 2, pop, push 5, pop, pop.*
   - What is the final state of the stack? What values were popped?

3. *How does a stack-based VM evaluate the expression `(3 + 4) * 2`?*
   - Write out the bytecode instructions and trace the stack state after each one.

4. *What is a register, and how does a register-based machine differ from a stack-based one?*
   - Which design tends to produce more instructions? Which tends to produce simpler instructions?

5. *Why do real CPUs use registers rather than stacks for most operations?*
   - Consider speed, hardware complexity, and the difficulty of writing a compiler for each.

6. *What is the program counter (PC), and what role does it play in a VM?*
   - What happens to the PC during a normal instruction? During a jump? During a function call?

7. *Describe what happens to the call stack when a function calls another function.*
   - What is a stack frame? What does it contain, and when is it created and destroyed?

8. *What is a stack overflow? Give a concrete example of a program that would cause one.*
   - Is a stack overflow always a programming error, or can it indicate a design limitation of the VM?


#### Memory

1. *What is the difference between the stack and the heap in a VM?*
   - Which is used for local variables, and which for dynamically allocated objects?

2. *What is garbage collection, and why does a VM need it?*
   - What problem does it solve? What cost does it introduce?

3. *Describe the difference between the Harvard architecture and the von Neumann architecture.*
   - What does it mean for instructions and data to share the same memory space?

4. *What is a memory-mapped register? Give an example from embedded or systems programming.*
   - How is reading a memory-mapped register different from reading a regular variable?

5. *What happens when a VM tries to access memory it does not own?*
   - How do real operating systems detect this? What does a VM typically do instead?

6. *Why might a VM use a fixed-size stack rather than a dynamically growing one?*
   - What are the tradeoffs in safety, performance, and implementation complexity?


#### Execution Model

1. *What is the fetch-decode-execute cycle?*
   - Describe each step. How does this loop map onto a simple VM interpreter written in Python or C?

2. *What is an opcode? Give three examples from a simple instruction set.*
   - How does the VM know what to do when it encounters each opcode?

3. *What is an instruction set architecture (ISA)?*
   - Why do different VMs define different ISAs? What considerations shape those choices?

4. *What is the difference between a branching instruction and a jump instruction in a VM?*
   - How does conditional execution get compiled into bytecode?

5. *What does it mean for a VM to be Turing complete?*
   - What minimal set of operations is sufficient? Does every practical VM need all of them?

6. *How does a VM support function calls and returns at the bytecode level?*
   - What instructions are involved? What state must be saved and restored?
