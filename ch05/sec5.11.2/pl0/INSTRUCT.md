
## PL/0 Instruction Set

The instruction set for PL/0 as represented by the FCT class defines a small virtual machine.
Each mnemonic corresponds to a specific operation that the virtual machine can execute.

There are numerous variations of instruction sets for PL/0, tailored to different purposes.
Typically, however, they are optimised to remain compact and encompass only the essential
core instructions.


### Example of Full Instruction Set for PL/0

__1. LIT (Load Literal)__
- Purpose: Push a literal value onto the stack.
- Format: `lit <value>`
- Example: lit 5 (pushes the integer 5 onto the stack).

__2. OPR (Operation)__
- Purpose: Perform arithmetic or logical operations or other stack-based operations.
- Format: `opr <operation_code>`
- Common operation codes:
    * 0: Return from procedure.
    * 1: Negate (unary -).
    * 2: Addition (+).
    * 3: Subtraction (-).
    * 4: Multiplication (*).
    * 5: Division (/).
    * 6: Odd check (x % 2).
    * 7: Modulo.
    * 8: Equality check (==).
    * 9: Not equal (!=).
    * 10: Less than (<).
    * 11: Greater than (>).
    * 12: Less than or equal (<=).
    * 13: Greater than or equal (>=).
    * 14: Logical AND.
    * 15: Logical OR.

__3. LOD (Load)__
- Purpose: Load a value from a specific memory address into the stack.
- Format: `lod <level>, <address>`
- Example: lod 1, 3 (load the value from level 1, address 3 into the stack).

__4. STO (Store)__
- Purpose: Store the top value from the stack into a specific memory address.
- Format: `sto <level>, <address>`
- Example: sto 0, 5 (store the top stack value into level 0, address 5).

__5. CAL (Call Procedure)__
- Purpose: Call a procedure by jumping to a specific address and saving the return context.
- Format: `cal <level>, <address>`
- Example: cal 0, 10 (call the procedure at level 0, address 10).

__6. INT (Increment Stack Pointer)__
- Purpose: Allocate space on the stack for variables.
- Format: `int <size>`
- Example: int 3 (allocate 3 slots on the stack).

__7. JMP (Jump)__
- Purpose: Unconditional jump to a specific instruction.
- Format: `jmp <address>`
- Example: jmp 15 (jump to instruction at address 15).

__8. JPC (Jump on Condition)__
- Purpose: Conditional jump based on the top stack value (0 = false, non-zero = true).
- Format: `jpc <address>`
- Example: jpc 20 (jump to address 20 if the top stack value is false).

__9. HLT (Halt)__
- Purpose: Stop the program.
- Format: `hlt`
- Example: hlt (end program execution).

This instruction set is simple yet sufficient for a small educational programming language like PL/0.
It demonstrates basic principles of virtual machine design and operation.

In short:
* Stack-based Architecture: All operations (LIT, OPR, etc.) interact with the stack.
* Procedural Support: Instructions like CAL, LOD, and STO enable function calls and scoped variable management.
* Control Flow: Instructions like JMP, JPC, and HLT manage program flow and termination.

