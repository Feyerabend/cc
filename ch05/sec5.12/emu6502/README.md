
## 6502 Emulator with Monitor

Another approach to building a compiler is to start from the bottom up, using a
simple emulator as the foundation. This project uses a MOS 6502 CPU emulator
with a built-in interactive monitor for debugging.

From this base, implement an assembler and any additional tools you find useful,
and then develop a compiler that emits 6502 assembly code at target. Be mindful
of the constraints and architectural limitations of the MOS 6502 CPU to ensure
that the generated assembly is correct and executable.

```bash
gcc -o emu6502 main.c fake6502.c -std=c99
```

```bash
# Start in monitor mode (default)
./emu6502 program.bin

# Run immediately without monitor
./emu6502 -r program.bin

# Run with instruction trace
./emu6502 -t program.bin

# Limit execution cycles
./emu6502 -c 10000 program.bin
```


### Monitor Commands

Once in the monitor, you can use these commands:

Execution Control:
- *s, step* - Execute one instruction and show next
- *c, continue* - Continue execution until breakpoint or BRK
- *r, run* - Same as continue

Breakpoints:
- *b* - List all breakpoints
- *b <addr>* - Set breakpoint at address (hex)
- *bc <addr>* - Clear breakpoint at address

Inspection:
- *d [addr] [count]* - Disassemble from address (default: PC, 10 lines)
- *m [start] [end]* - Dump memory range (hex addresses)
- *reg* - Display CPU registers and flags

Modification:
- *w <addr> <value>* - Write byte to memory (both in hex)

Other:
- *t* - Toggle trace mode on/off
- *reset* - Reset CPU to initial state
- *q, quit* - Exit emulator
- *h, help, ?* - Show help


### Monitor Features

__Address Markers:__
- `>` - Marks the current PC (Program Counter)
- `*` - Marks a breakpoint location

__Register Display:__
Shows all registers and processor flags:
```
PC=$0800  SP=$FD  A=$00  X=$00  Y=$00  P=$24 [nv--dizc]
```
Uppercase flags are set (1), lowercase are clear (0):
- N = Negative
- V = Overflow
- D = Decimal mode
- I = Interrupt disable
- Z = Zero
- C = Carry

__Disassembly Format__
```
$0800: A9 42     LDA #$42
```
Shows: address, hex bytes, mnemonic, operands


### Example Session

```
monitor> d          # Disassemble at PC
> $0800: A9 00     LDA #$00        
  $0802: 8D 01 F0  STA $F001       
  $0805: 00        BRK             

monitor> b 802      # Set breakpoint at $0802
Breakpoint 1 set at $0802

monitor> s          # Step one instruction
$0800: A9 00     LDA #$00
PC=$0802  SP=$FD  A=$00  X=$00  Y=$00  P=$26 [nv--diZc]

monitor> c          # Continue to breakpoint
Continuing execution...

Breakpoint hit at $0802

monitor> reg        # Show registers
PC=$0802  SP=$FD  A=$00  X=$00  Y=$00  P=$26 [nv--diZc]

monitor> m 0 ff     # Dump zero page
0000: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
...

monitor> q          # Quit
Exiting...
```


### Memory Map

- `$0000-$00FF`: Zero page (runtime temps at $00F0-$00FF)
- `$0100-$01FF`: Stack
- `$0200-$03FF`: Variables
- `$0400-$07FF`: Arrays
- `$0800-$EFFF`: Program code (loads here by default)
- `$F000-$F0FF`: I/O area
  - `$F001`: Console output (write a byte to print)
  - `$F002`: Console input status
  - `$F003`: Console input data


### Integration with Assembler/Compiler

This emulator is designed to work with:
1. *Assembler* - Takes assembly source and produces binary `.bin` files
2. *Compiler* - Takes high-level source, produces assembly
3. *Emulator* - Runs the binary output with full debugging

Workflow:
```
source.bas -> [compiler] -> source.asm -> [assembler] -> program.bin -> [emulator]
```

The monitor allows you to:
- Step through the assembled/compiled code
- Set breakpoints at specific addresses
- Inspect variables in memory
- Debug logic errors
- Verify correct compilation


### Tips

- All addresses and values are in *hexadecimal*
- Use `d` to see what's about to execute
- Use `b` to set breakpoints at interesting code locations
- Use `m` to watch variable memory regions
- BRK instruction ($00) automatically enters monitor mode
- Trace mode (`t` command) shows every instruction executed
