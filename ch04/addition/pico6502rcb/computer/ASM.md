
## 6502 Assembler Manual


### Overview

This is a two-pass assembler for the MOS 6502 processor,
supporting all standard instructions, addressing modes,
and common assembler directives.

 
### Command Line Usage

```bash
python asm.py <input.asm> [output.bin] [-v]
```

*Arguments:*
- `input.asm` - Source assembly file (required)
- `output.bin` - Output binary file (default: `a.bin`)
- `-v` - Verbose mode, shows symbol table and addresses

*Examples:*
```bash
## Basic assembly
python asm.py program.asm

## Custom output file
python asm.py program.asm game.bin

## Verbose mode for debugging
python asm.py program.asm program.bin -v
```


### Syntax

#### Comments
```asm
; This is a comment - everything after semicolon is ignored
LDA #$42    ; Load accumulator with $42
```

#### Numbers

The assembler supports multiple number formats:

```asm
LDA #42         ; Decimal: 42
LDA #$2A        ; Hexadecimal: $2A (preferred)
LDA #0x2A       ; Hexadecimal: 0x2A (alternative)
LDA #%00101010  ; Binary: %00101010
LDA #-5         ; Negative decimal: -5
```

#### Labels

Labels mark locations in code or data:

```asm
start:          ; Label at current address
    LDA #$00
    JMP start   ; Jump to label

loop:           ; Another label
    INX
    BNE loop    ; Branch to loop
```

*Rules:*
- Must start with letter or underscore
- Can contain letters, numbers, underscores
- Case-sensitive
- End with colon `:`

#### Constants (EQU)

Define constant values:

```asm
SCREEN_RAM = $0400
COLOR_RAM = $D800
MAX_VALUE = 255

    LDA #MAX_VALUE
    STA SCREEN_RAM
```

*Note:* Constants are evaluated immediately and don't represent addresses.


### Addressing Modes

#### Implied
No operand needed:
```asm
NOP         ; No operation
CLC         ; Clear carry
RTS         ; Return from subroutine
```

#### Accumulator
Operates on accumulator register:
```asm
ASL A       ; Shift accumulator left
ROR A       ; Rotate accumulator right
```

#### Immediate
Literal value (prefixed with `#`):
```asm
LDA #$42    ; Load $42 into A
LDX #100    ; Load 100 into X
CMP #'A'    ; Compare with ASCII 'A'
```

#### Zero Page
First 256 bytes of memory (`$00-$FF`):
```asm
LDA $80     ; Load from zero page $80
STA $42     ; Store to zero page $42
```

#### Zero Page, X/Y
Zero page with X or Y offset:
```asm
LDA $80,X   ; Load from ($80 + X)
STY $42,X   ; Store Y to ($42 + X)
LDX $50,Y   ; Load from ($50 + Y) into X
```

#### Absolute
Full 16-bit address:
```asm
LDA $8000   ; Load from $8000
JMP $C000   ; Jump to $C000
STA $D020   ; Store to $D020
```

#### Absolute, X/Y
Absolute address with X or Y offset:
```asm
LDA $8000,X ; Load from ($8000 + X)
STA $0400,Y ; Store to ($0400 + Y)
```

#### Indirect
Jump through address (JMP only):
```asm
JMP ($FFFC) ; Jump to address stored at $FFFC
```

#### Indexed Indirect (Indirect, X)
Zero page pointer with X offset:
```asm
LDA ($80,X) ; Load from address at (($80 + X) & $FF)
```

#### Indirect Indexed (Indirect, Y)
Zero page pointer with Y added to result:
```asm
LDA ($80),Y ; Load from (address at $80) + Y
STA ($42),Y ; Store to (address at $42) + Y
```

#### Relative (Branches)
Automatic for branch instructions:
```asm
BEQ label   ; Branch if equal
BNE loop    ; Branch if not equal
BCC start   ; Branch if carry clear
```

*Note:* Branches can only reach -128 to +127 bytes from the instruction following the branch.


### Directives

#### .org - Set Origin Address

Set the assembly address:

```asm
.org $8000      ; Start assembling at $8000

start:
    LDA #$00    ; This will be at $8000
```

Multiple `.org` directives can be used:

```asm
.org $8000
    ; Code here

.org $C000
    ; More code at different location
```

#### .byte - Define Bytes

Define one or more bytes:

```asm
.byte $01           ; Single byte
.byte $42, $43, $44 ; Multiple bytes
.byte 10, 20, 30    ; Decimal values
.byte %11110000     ; Binary value
```

Can use expressions:
```asm
value = 100
.byte value + 5     ; Stores 105
```

#### .word - Define Words (16-bit)

Define 16-bit values (little-endian):

```asm
.word $1234         ; Stores $34, $12
.word $ABCD, $5678  ; Multiple words
.word start         ; Address of label
```

#### .asc - ASCII String

Define ASCII text:

```asm
.asc "HELLO"        ; Stores: $48, $45, $4C, $4C, $4F
.asc "WORLD"        ; Single or double quotes

; With null terminator
message:
    .asc "Hello, World!"
    .byte $00       ; Null terminator
```


### Instructions

#### Load/Store
```asm
LDA #$42    ; Load A with immediate
LDX $80     ; Load X from zero page
LDY $8000   ; Load Y from absolute
STA $0400   ; Store A to address
STX $50     ; Store X
STY $D000   ; Store Y
```

#### Transfer
```asm
TAX         ; Transfer A to X
TAY         ; Transfer A to Y
TXA         ; Transfer X to A
TYA         ; Transfer Y to A
TSX         ; Transfer SP to X
TXS         ; Transfer X to SP
```

#### Stack
```asm
PHA         ; Push A to stack
PHP         ; Push processor status
PLA         ; Pull A from stack
PLP         ; Pull processor status
```

#### Increment/Decrement
```asm
INC $80     ; Increment memory
DEC $1000   ; Decrement memory
INX         ; Increment X
INY         ; Increment Y
DEX         ; Decrement X
DEY         ; Decrement Y
```

#### Arithmetic
```asm
ADC #$05    ; Add with carry
SBC #$10    ; Subtract with carry (borrow)
```

#### Logic
```asm
AND #$0F    ; Logical AND
ORA #$80    ; Logical OR
EOR #$FF    ; Exclusive OR
```

#### Shift/Rotate
```asm
ASL A       ; Arithmetic shift left
LSR $80     ; Logical shift right
ROL $1000   ; Rotate left
ROR A       ; Rotate right
```

#### Compare
```asm
CMP #$42    ; Compare A
CPX $80     ; Compare X
CPY #100    ; Compare Y
```

#### Branches
```asm
BCC label   ; Branch if carry clear
BCS label   ; Branch if carry set
BEQ label   ; Branch if equal (Z=1)
BNE label   ; Branch if not equal (Z=0)
BMI label   ; Branch if minus (N=1)
BPL label   ; Branch if plus (N=0)
BVC label   ; Branch if overflow clear
BVS label   ; Branch if overflow set
```

#### Jumps/Calls
```asm
JMP $8000   ; Jump to address
JMP ($FFFC) ; Jump indirect
JSR routine ; Jump to subroutine
RTS         ; Return from subroutine
```

#### Status Flags
```asm
CLC         ; Clear carry
SEC         ; Set carry
CLD         ; Clear decimal mode
SED         ; Set decimal mode
CLI         ; Clear interrupt disable
SEI         ; Set interrupt disable
CLV         ; Clear overflow
```

#### System
```asm
BRK         ; Break (software interrupt)
RTI         ; Return from interrupt
NOP         ; No operation
BIT $80     ; Bit test
```


### Expressions

Expressions can be used anywhere a number is expected:

#### Operators
```asm
value = 100
double = value * 2      ; Multiplication
half = value / 2        ; Division
remainder = value % 3   ; Modulo
offset = value + 10     ; Addition
result = value - 5      ; Subtraction
```

*Precedence:* `*`, `/`, `%` have higher precedence than `+`, `-`

#### Parentheses
```asm
result = (10 + 5) * 2   ; = 30
result = 10 + 5 * 2     ; = 20
```

#### Program Counter (*)
Use `*` to reference current address:
```asm
here = *                ; Current address
    LDA #$00
    JMP * + 5           ; Skip forward 5 bytes
```

#### Combining
```asm
BASE = $8000
OFFSET = $100
TABLE = BASE + OFFSET   ; $8100

    LDA TABLE + 5       ; Load from $8105
```

### Complete Example

```asm
; Simple 6502 program
; Fills screen with pattern

.org $8000

; Constants
SCREEN = $0400
COLOR = $D800
BORDER = $D020

; Variables in zero page
counter = $20
color = $21

start:
    ; Init
    LDA #$00
    STA counter
    LDA #$01
    STA color
    
    ; Set border color
    LDA #$06        ; Blue
    STA BORDER
    
    ; Main loop
loop:
    LDX counter
    LDA pattern,X
    STA SCREEN,X    ; Write to screen
    LDA color
    STA COLOR,X     ; Write color
    
    ; Next iteration
    INC counter
    BNE loop        ; Loop until counter wraps
    
    ; Done
    JMP start

; Data
pattern:
    .asc "HELLO WORLD!"
    .byte $00

; Vectors
.org $FFFC
    .word start     ; Reset vector
```


### Tips and Best Practices

#### 1. Use Zero Page
Zero page instructions are faster and use less memory:
```asm
; Good - zero page
LDA $80     ; 2 bytes, 3 cycles

; Slower - absolute
LDA $0080   ; 3 bytes, 4 cycles
```

#### 2. Label Everything
Makes code readable and maintainable:
```asm
; Bad
    JMP $8042

; Good
    JMP init_screen
```

#### 3. Use Constants
Avoid magic numbers:
```asm
; Bad
    LDA #$06
    STA $D020

; Good
COLOR_BLUE = $06
VIC_BORDER = $D020
    LDA #COLOR_BLUE
    STA VIC_BORDER
```

#### 4. Comment Your Code
Explain what, not how:
```asm
; Bad comment
    LDA #$00    ; Load A with 0

; Good comment
    LDA #$00    ; Initialize loop counter
```

#### 5. Organize Memory Layout
Document your memory map:
```asm
; Zero Page Variables
; $20-$2F: Game state
; $30-$3F: Sprite data
; $40-$4F: Temp storage

player_x = $20
player_y = $21
score = $22
```

#### 6. Branch Range
Remember branches are limited to ±127 bytes:
```asm
; If target is too far, use JMP
    BEQ far_away    ; Error if > 127 bytes

; Solution:
    BNE skip
    JMP far_away
skip:
```


### Error Messages

#### "Undefined symbol 'name'"
- Using a label that doesn't exist
- Check spelling and case

#### "Branch offset N out of range"
- Branch target is too far (> 127 bytes)
- Use JMP instead or reorganize code

#### "Invalid addressing mode 'X' for 'Y'"
- Instruction doesn't support that mode
- Check instruction reference

#### "Parse error"
- Syntax error in source
- Check for typos, missing commas, etc.


### Integration with C64-Style System

For the Pico Display Pack project:

```asm
; Memory map
SCREEN_RAM = $0400      ; 40x30 characters
COLOR_RAM = $D800       ; Color for each char
VIC_BORDER = $D000      ; Border color
VIC_BG = $D001          ; Background color
BUTTONS = $DC00         ; Button state

; Example: Write colored text
.org $8000

    ; Set colors
    LDA #$06
    STA VIC_BORDER
    LDA #$00
    STA VIC_BG
    
    ; Write text
    LDX #$00
write_loop:
    LDA message,X
    BEQ done
    STA SCREEN_RAM,X
    LDA #$01            ; White
    STA COLOR_RAM,X
    INX
    JMP write_loop
    
done:
    JMP done            ; Halt

message:
    .asc "HELLO!"
    .byte $00
```

### Building Workflow

Complete build process:

```bash
## 1. Write assembly
nano program.asm

## 2. Assemble
python asm.py program.asm program.bin -v

## 3. Convert to C header
python bin2header.py program.bin rom.h rom_data

## 4. Include in C code
## In main.c: #include "rom.h"

## 5. Build for Pico
cd build
cmake ..
make

## 6. Upload to Pico
## Copy .uf2 file to Pico
```

### Reference Tables

#### 6502 Registers
| Register | Name | Size | Description |
|----------|------|------|-------------|
| A | Accumulator | 8-bit | Primary math/logic register |
| X | Index X | 8-bit | Counter/index register |
| Y | Index Y | 8-bit | Counter/index register |
| SP | Stack Pointer | 8-bit | Points to stack (page 1) |
| PC | Program Counter | 16-bit | Current instruction address |
| P | Status Flags | 8-bit | Processor status |

#### Status Flags (P Register)
| Bit | Flag | Name | Set When |
|-----|------|------|----------|
| 7 | N | Negative | Result bit 7 = 1 |
| 6 | V | Overflow | Signed overflow |
| 5 | - | Unused | Always 1 |
| 4 | B | Break | BRK executed |
| 3 | D | Decimal | Decimal mode active |
| 2 | I | Interrupt | Interrupts disabled |
| 1 | Z | Zero | Result = 0 |
| 0 | C | Carry | Carry/borrow occurred |

#### C64 Color Palette
| Value | Color | Hex |
|-------|-------|-----|
| $00 | Black | #000000 |
| $01 | White | #FFFFFF |
| $02 | Red | #880000 |
| $03 | Cyan | #AAFFEE |
| $04 | Purple | #CC44CC |
| $05 | Green | #00CC55 |
| $06 | Blue | #0000AA |
| $07 | Yellow | #EEEE77 |
| $08 | Orange | #DD8855 |
| $09 | Brown | #664400 |
| $0A | Light Red | #FF7777 |
| $0B | Dark Grey | #333333 |
| $0C | Grey | #777777 |
| $0D | Light Green | #AAFF66 |
| $0E | Light Blue | #0088FF |
| $0F | Light Grey | #BBBBBB |


### Additional Resources

- *MOS 6502 Datasheet*: Complete instruction reference
- *6502.org*: Community and documentation
- *Visual 6502*: Interactive circuit simulator
- *C64 Programming*: Additional C64-specific info

