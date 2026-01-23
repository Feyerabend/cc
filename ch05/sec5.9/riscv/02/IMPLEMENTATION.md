
## Linker and Loader Example


### Object File Format

*Structure:*
```
┌───────────────────────────────────┐
│ Magic Number: "RVO1" (4 bytes)    │
├───────────────────────────────────┤
│ Header:                           │
│   - Text section size (4 bytes)   │
│   - Data section size (4 bytes)   │
│   - Symbol count (4 bytes)        │
│   - Relocation count (4 bytes)    │
├───────────────────────────────────┤
│ Text Section (code bytes)         │
├───────────────────────────────────┤
│ Data Section (initialized data)   │
├───────────────────────────────────┤
│ Symbol Table:                     │
│   For each symbol:                │
│     - Name length + name          │
│     - Address (4 bytes)           │
│     - Section ('text' or 'data')  │
│     - Is global? (1 byte)         │
├───────────────────────────────────┤
│ Relocation Table:                 │
│   For each relocation:            │
│     - Offset (4 bytes)            │
│     - Symbol name                 │
│     - Type (R_RISCV_JAL, etc.)    │
│     - Addend (4 bytes)            │
└───────────────────────────────────┘
```


### Linker (`linker.py`)

1. *Load Object Files*
   ```python
   def load_object(self, filename: str):
       # Read magic number
       # Read header (sizes, counts)
       # Read text/data sections
       # Read symbol table
       # Read relocation table
   ```

2. *Assign Addresses* (Two-pass)
   ```python
   # First pass: layout sections
   current_addr = 0x00000000
   
   # All .text sections sequentially
   for obj in objects:
       section_offsets[obj, 'text'] = current_addr
       current_addr += len(obj.text_section)
   
   # Then all .data sections
   for obj in objects:
       section_offsets[obj, 'data'] = current_addr
       current_addr += len(obj.data_section)
   ```

3. *Build Global Symbol Table*
   ```python
   for obj in objects:
       for symbol in obj.symbols:
           if symbol.is_global:
               base = section_offsets[obj, symbol.section]
               final_address = base + symbol.address
               global_symbols[symbol.name] = final_address
   ```

4. *Apply Relocations*
   ```python
   for relocation in obj.relocations:
       target_addr = global_symbols[relocation.symbol]
       
       if relocation.type == 'R_RISCV_JAL':
           # PC-relative jump
           offset = target_addr - current_PC
           # Encode offset into JAL instruction
           patch_instruction(offset)
       
       elif relocation.type == 'R_RISCV_BRANCH':
           # PC-relative branch
           offset = target_addr - current_PC
           # Encode offset into branch instruction
           patch_instruction(offset)
   ```

*Example Link Process:*

Input files:
```
main.o:
  .text: 16 bytes (4 instructions)
  symbols: _start (global, text, 0x0)
  relocations: JAL to add_numbers at offset 8

math.o:
  .text: 8 bytes (2 instructions)
  symbols: add_numbers (global, text, 0x0)
```

After linking:
```
Final layout:
  0x00000000 - 0x0000000F: main.o .text
  0x00000010 - 0x00000017: math.o .text

Symbol table:
  _start:       0x00000000
  add_numbers:  0x00000010

Relocation at offset 8:
  Before: jal ra, 0x00000000  (placeholder)
  After:  jal ra, 0x00000010  (points to add_numbers)
  Offset: 0x00000010 - 0x00000008 = 0x00000008
```


### Loader (in `vm.py`)

*What it does:*

```python
def load_program(self, filename: str):
    """Load binary program into memory at address 0"""
    with open(filename, 'rb') as f:
        program = f.read()
    
    # Validate alignment (4-byte instructions)
    if len(program) % 4 != 0:
        raise ValueError("Binary size not multiple of 4 bytes")
    
    # Load into memory at address 0
    self.memory[0:len(program)] = program
    
    # Set up execution environment
    self.pc = 0              # Start at address 0
    self.regs = [0] * 32     # Clear registers
    self.running = True
```

*Simplifications:*

1. *No Executable Format Parsing* - We load raw binary
   - Real: Parse ELF/PE headers
   - Ours: Just copy bytes

2. *Fixed Load Address* - Always at 0x00000000
   - Real: Virtual address from program header
   - Ours: Hardcoded to 0

3. *No Memory Protection* - All memory is RWX
   - Real: Set page permissions (R-X, RW-, etc.)
   - Ours: bytearray (all accessible)

4. *No Dynamic Linking* - All symbols resolved at link time
   - Real: Load shared libraries, resolve at runtime
   - Ours: Static linking only

5. *No Stack/Heap Setup* - Program manages its own memory
   - Real: OS allocates stack, sets SP
   - Ours: Program must set up SP manually if needed

6. *Immediate Execution* - No _start → main dance
   - Real: _start sets up environment, calls main
   - Ours: PC points to first instruction


### Alignment

*Linker Alignment:*
```python
# We don't enforce alignment between sections currently
# In a production linker, you'd do:

text_size = sum(len(obj.text) for obj in objects)
text_size_aligned = (text_size + 7) & ~7  # Round up to 8 bytes

data_offset = text_size_aligned  # Data starts at aligned address
```

*Instruction Alignment:*
```python
# We validate 4-byte alignment
if len(program) % 4 != 0:
    raise ValueError("Binary size not multiple of 4 bytes")

# VM checks PC alignment
if self.pc % 4 != 0:
    raise ValueError("PC not aligned")
```

*RISC-V requires 4-byte instruction alignment* -
all instructions are exactly 32 bits and must start at addresses divisible by 4.


### Summary

| Feature | Real Linker/Loader | This Implementation |
|---------|--------------------|---------------------|
| Object format | ELF, COFF, Mach-O | Custom "RVO1" |
| Sections | .text, .data, .bss, .rodata, etc. | .text, .data only |
| Alignment | Page-aligned (4KB), type-aligned | 4-byte for instructions |
| Relocation types | 20+ types | 3 types (JAL, BRANCH, PCREL) |
| Symbol resolution | Global, local, weak, strong | Global only |
| Memory layout | Virtual memory, protection | Flat bytearray |
| Dynamic linking | Shared libraries, PLT/GOT | Static only |
| Entry point | Configurable (_start) | Always 0x00000000 |



