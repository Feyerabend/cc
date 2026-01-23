
## Linkers and Loaders

*Linkers* and *loaders* are two separate but related tools in the
compilation pipeline that bridge the gap between compiled code and running programs.

The linker works at *compile/build time*, while the loader works at *run time*.


### The Pipeline

```
Source Code (.c, .asm)
        |
  Compiler/Assembler
        |
   Object Files (.o)        <- Relocatable, not executable
        |
      LINKER                <- Combines & resolves symbols
        |
 Executable (.exe, .bin)    <- Complete, but on disk
        |
      LOADER                <- Loads into memory
        |
   Running Process          <- Executing in RAM
```


### The Linker

#### What is a Linker?

A *linker* (also called a *link editor*) combines multiple object files
and libraries into a single executable file. It performs two main tasks:
1. *Symbol Resolution* - Connects references to definitions
2. *Relocation* - Assigns final memory addresses

#### Symbol Resolution

When you write code across multiple files, functions and variables
reference each other:

*File: main.c*
```c
extern int add(int, int);  // Declaration (reference)

int main() {
    return add(5, 3);      // Uses 'add' - but where is it?
}
```

*File: math.c*
```c
int add(int a, int b) {    // Definition
    return a + b;
}
```

After compilation, you have two object files:
- `main.o` - contains a reference to `add` (undefined symbol)
- `math.o` - contains the definition of `add` (defined symbol)

*The linker's job:* Find the definition of `add` in `math.o`
and resolve the reference in `main.o`.

#### Symbol Table

Each object file contains a *symbol table*:

Symbol Table for main.o:
```
┌─────────────┬──────────┬────────┬─────────┐
│ Symbol Name │ Address  │ Type   │ Binding │
├─────────────┼──────────┼────────┼─────────┤
│ main        │ 0x0000   │ FUNC   │ GLOBAL  │
│ add         │ UNDEF    │ FUNC   │ GLOBAL  │ < Undefined!
└─────────────┴──────────┴────────┴─────────┘
```

Symbol Table for math.o:
```
┌─────────────┬──────────┬────────┬─────────┐
│ Symbol Name │ Address  │ Type   │ Binding │
├─────────────┼──────────┼────────┼─────────┤
│ add         │ 0x0000   │ FUNC   │ GLOBAL  │ < Defined!
└─────────────┴──────────┴────────┴─────────┘
```

The linker builds a *global symbol table* by merging all symbol tables.


#### Relocation

Object files contain code with *temporary/relative addresses*.
The linker assigns *final absolute addresses*.


__Why is Relocation Needed?__

When the assembler creates `main.o`, it doesn't know:
- Where `math.o` will be placed in memory
- Where the final executable will be loaded
- The final address of `add()`

So it generates *relocatable code* with placeholders:

```assembly
# In main.o (before linking)
0x0000:  jal  ra, ????    # Call add - but where is it?
```

The assembler also creates a *relocation table*:

Relocation Table for main.o:
```
┌────────┬─────────┬─────────────────┬────────┐
│ Offset │ Symbol  │ Type            │ Addend │
├────────┼─────────┼─────────────────┼────────┤
│ 0x0000 │ add     │ R_RISCV_JAL     │ 0      │
└────────┴─────────┴─────────────────┴────────┘
```

This says: "At offset 0x0000, there's a JAL instruction that needs the address of `add`."


__The Relocation Process__

1. *Assign Section Addresses*
   ```
   main.o .text   → 0x00000000 - 0x000000FF
   math.o .text   → 0x00000100 - 0x000001FF
   main.o .data   → 0x00000200 - 0x000002FF
   math.o .data   → 0x00000300 - 0x000003FF
   ```

2. *Update Symbol Addresses*
   ```
   main: 0x00000000 (in main.o at 0x00000000)
   add:  0x00000100 (in math.o at 0x00000000 → relocated to 0x00000100)
   ```

3. *Apply Relocations*
   ```assembly
   # Before relocation
   0x0000:  jal  ra, 0x0000    # Placeholder
   
   # After relocation
   0x0000:  jal  ra, 0x0100    # Now points to add() at 0x00000100
   ```


#### Types of Relocation

Different instruction types need different relocation methods:

*PC-Relative (Branches, JAL)*
```
target_address = PC + offset
offset = symbol_address - current_PC
```

*Absolute (Data addresses)*
```
address = symbol_address
```

*High/Low (LUI + ADDI for 32-bit addresses)*
```
LUI  rd, %hi(symbol)      # Upper 20 bits
ADDI rd, rd, %lo(symbol)  # Lower 12 bits
```


#### Linker Algorithm (Simplified)

```
1. Read all object files
2. Create global symbol table
   - Merge all symbols
   - Check for duplicates (multiple definitions)
   - Check for undefined symbols
3. Assign addresses to sections
   - Layout all .text sections
   - Layout all .data sections
   - Apply alignment constraints
4. Apply all relocations
   - For each relocation entry:
     * Look up symbol address
     * Calculate new value
     * Patch the instruction/data
5. Write executable file
```



### The Loader

#### What is a Loader?

A *loader* is an operating system component that takes an executable
file from disk and prepares it for execution by:
1. *Loading* the program into memory
2. *Setting up* the execution environment
3. *Transferring control* to the program's entry point


#### Loading Process


__1. Parse Executable Format__

Modern executables aren't just raw code - they have structure:

*ELF (Executable and Linkable Format) - Linux/Unix*
```
┌─────────────────┐
│  ELF Header     │ < Magic number, entry point, architecture
├─────────────────┤
│ Program Headers │ < Describes segments to load
├─────────────────┤
│  .text section  │ < Code (read-only, executable)
├─────────────────┤
│  .rodata section│ < Constants (read-only)
├─────────────────┤
│  .data section  │ < Initialized data (read-write)
├─────────────────┤
│  .bss section   │ < Uninitialized data (zero-filled)
├─────────────────┤
│ Section Headers │ < Metadata about sections
└─────────────────┘
```

*PE (Portable Executable) - Windows*
```
┌─────────────────┐
│  DOS Header     │ < Backward compatibility
├─────────────────┤
│  PE Header      │ < PE signature, architecture
├─────────────────┤
│ Optional Header │ < Entry point, image base
├─────────────────┤
│ Section Table   │ < .text, .data, .rdata, etc.
├─────────────────┤
│  Sections       │ < Actual code and data
└─────────────────┘
```

__2. Allocate Memory__

The loader requests memory from the OS:

```
Virtual Memory Layout (typical):
┌─────────────────┐ 0xFFFFFFFF
│     Kernel      │ < OS code (protected)
├─────────────────┤ 0xC0000000
│      Stack      │ < Grows downward
│        |        │
├─────────────────┤
│       ...       │
│        ^        │
│        |        │
│      Heap       │ < Grows upward (malloc/new)
├─────────────────┤
│  .bss (zeros)   │ < Uninitialized data
├─────────────────┤
│  .data (init)   │ < Initialized data
├─────────────────┤
│ .rodata (const) │ < Read-only data
├─────────────────┤
│  .text (code)   │ < Executable code
└─────────────────┘ 0x00400000 (typical base)
```

*Memory Protection:* The loader sets permissions:
- `.text` > Read + Execute (R-X)
- `.rodata` > Read only (R--)
- `.data`, `.bss` > Read + Write (RW-)
- Stack, Heap > Read + Write (RW-)


__3. Copy Sections to Memory__

```c
// Pseudo-code for loading
for each section in executable:
    if section.type == LOAD:
        allocate_memory(section.virtual_address, section.size)
        copy_from_file(section.file_offset, section.virtual_address, section.file_size)
        if section.memory_size > section.file_size:
            zero_fill(section.virtual_address + section.file_size, 
                     section.memory_size - section.file_size)
        set_permissions(section.virtual_address, section.flags)
```

*Why memory_size > file_size?*
The `.bss` section (uninitialized globals) doesn't need to be stored in the file - just allocate zeros in memory.


__4. Dynamic Linking (Optional)__

If the program uses shared libraries (`.so`, `.dll`):

```
1. Load required shared libraries
2. Resolve symbols from libraries
3. Apply relocations (PLT/GOT)
4. Initialize libraries
```

*Example:*

Program uses printf() from libc.so:
```
┌─────────────┐      ┌─────────────┐
│  program    │      │  libc.so    │
│             │      │             │
│ call printf ├─────>│ printf code │
│             │      │             │
└─────────────┘      └─────────────┘
```

The loader:
1. Loads `libc.so` into memory
2. Finds `printf` in `libc.so`
3. Updates program's PLT (Procedure Linkage Table) to point to `printf`


__5. Setup Execution Environment__

*Stack Setup:*


```
High Address
┌──────────────┐
│  NULL        │ < Environment strings end
├──────────────┤
│  "PATH=..."  │ < Environment variables
├──────────────┤
│  NULL        │ < Arguments end
├──────────────┤
│  "arg2"      │ < Program arguments
│  "arg1"      │
│  "program"   │
├──────────────┤
│  envp        │ < Pointer to environment
│  argv        │ < Pointer to arguments
│  argc        │ < Argument count
└──────────────┘ < Stack pointer (SP)
Low Address
```

*Register Initialisation:*
```
PC (Program Counter) = entry_point (e.g., _start)
SP (Stack Pointer)   = top_of_stack
Other registers      = 0 or undefined
```

__6. Transfer Control__

```c
// Final step
jump_to_address(entry_point);  // Usually _start, not main!
```

The program starts running at the *entry point* (typically `_start`), which:
1. Calls global constructors (C++)
2. Initialises runtime environment
3. Calls `main(argc, argv)`
4. Calls `exit()` with main's return value



### Memory Alignment

*Alignment** means placing data at memory addresses that are multiples of a certain size.

```
Aligned (address divisible by 4):
Address:  0x1000  0x1004  0x1008  0x100C
         ┌───────┬───────┬───────┬───────┐
         │ int   │ int   │ int   │ int   │
         └───────┴───────┴───────┴───────┘
           Good    Good    Good    Good

Misaligned:
Address:  0x1001  0x1005  0x1009  0x100D
          ┌───────┬───────┬───────┬───────┐
          │ int   │ int   │ int   │ int   │
          └───────┴───────┴───────┴───────┘
            Bad     Bad     Bad     Bad
```

### Why Alignment Matters

*1. Hardware Requirements*
Many processors can't access misaligned data:
- RISC-V: Misaligned access causes exception (on some implementations)
- ARM: Misaligned access causes exception
- x86: Allows misaligned but slower (crosses cache lines)

*2. Performance*
```
Aligned 4-byte read (1 memory access):
Address 0x1000: ┌───────┐
                │ DATA  │ < One read
                └───────┘

Misaligned 4-byte read (2 memory accesses):
Address 0x1001: ───┬───────┬───
                   │ DATA  │
                   └───────┘
                   ^       ^
              Read 1    Read 2
              (0x1000)  (0x1004)
              Then merge the bytes!
```

*3. Atomicity*
Aligned accesses can be atomic (all-or-nothing), misaligned cannot.

#### Alignment Rules

Common alignment requirements:

| Data Type | Size | Alignment | Address Must Be |
|-----------|------|-----------|-----------------|
| char      | 1    | 1-byte    | Any             |
| short     | 2    | 2-byte    | Multiple of 2   |
| int       | 4    | 4-byte    | Multiple of 4   |
| long      | 8    | 8-byte    | Multiple of 8   |
| float     | 4    | 4-byte    | Multiple of 4   |
| double    | 8    | 8-byte    | Multiple of 8   |
| pointer   | 4/8  | 4/8-byte  | Multiple of 4/8 |

*Struct Alignment:*
```c
struct Example {
    char  a;   // 1 byte
    // 3 bytes padding
    int   b;   // 4 bytes (must be 4-byte aligned)
    char  c;   // 1 byte
    // 3 bytes padding (to make struct size multiple of 4)
};
// Total: 12 bytes (not 6!)
```

### Alignment in Linker/Loader

*Linker:*
```
.text section: align to 4 bytes (instructions are 4 bytes)
.data section: align to 8 bytes (for doubles/longs)
.bss section:  align to 8 bytes

Example:
.text ends at:   0x000001F3
Next section:    0x00000200 (rounded up to 8-byte boundary)
                 ^ 0x1F3 + 13 bytes padding = 0x200
```

*Loader:*
Page alignment (typically 4KB = 0x1000):
```
.text: 0x00400000 (page-aligned)
.data: 0x00401000 (page-aligned, even if .text is smaller)
```


