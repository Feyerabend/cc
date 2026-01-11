
## PL/0 with I/O Extensions

It can be hard to hand-assembly even a small computer as
ours. This is an idea of how you can go about building
something like a compiler for the computer. We will get
to compilers in the next chapter. You can return to this
later ..


### Table of Contents
1. [Introduction](#introduction)
2. [Basic Syntax](#basic-syntax)
3. [Variables and Constants](#variables-and-constants)
4. [Expressions and Operators](#expressions-and-operators)
5. [Control Flow](#control-flow)
6. [Procedures](#procedures)
7. [I/O Extensions](#io-extensions)
8. [Hardware Programming](#hardware-programming)
9. [Complete Examples](#complete-examples)
10. [Tips and Best Practices](#tips-and-best-practices)


### Introduction

PL/0 is a simple programming language designed for teaching compiler construction.
This extended version adds hardware I/O capabilities, making it perfect for programming
6502-based systems like the C64-style Pico emulator.


#### Program Structure

Every PL/0 program follows this structure:

```
[constants]
[variables]
[procedures]
statement
.
```

*Important*: Every program must end with a period (`.`)!

#### Your First Program

```pl0
BEGIN
    WRITE 1 TO $D000
END.
```

This simple program writes the value `1` to memory address `$D000` (the border color register).



### Basic Syntax

#### Comments

PL/0 doesn't have built-in comments in the standard, but you can document your code externally.

#### Numbers

PL/0 supports both decimal and hexadecimal numbers:

```pl0
123        ; Decimal
$FF        ; Hexadecimal (255 in decimal)
$D000      ; Hexadecimal address
```

#### Identifiers

Variable and procedure names:
- Must start with a letter
- Can contain letters, numbers, and underscores
- Case-sensitive

```pl0
VAR x, myVar, total_score, player1;
```



### Variables and Constants

#### Constants

Constants are defined once and cannot be changed:

```pl0
CONST PI = 314,           ; 3.14 * 100 (no floating point!)
      MAX = 100,
      BLUE = 6,
      SCREEN_ADDR = $0400;
```

*Note*: PL/0 only supports integers. To work with decimals, multiply by 10, 100, etc.

#### Variables

Variables must be declared before use:

```pl0
VAR x, y, z;              ; Declare three variables
VAR score;                ; Declare one variable
VAR player_x, player_y;   ; Declare two variables
```

#### Using Constants and Variables

```pl0
CONST MAX_SCORE = 9999;
VAR score, lives;

BEGIN
    score := 0;
    lives := 3;
    
    IF score > MAX_SCORE THEN
        score := MAX_SCORE
END.
```



### Expressions and Operators

#### Arithmetic Operators

```pl0
VAR a, b, result;

BEGIN
    a := 10;
    b := 5;
    
    result := a + b;      ; Addition: 15
    result := a - b;      ; Subtraction: 5
    result := a * b;      ; Multiplication: 50
    result := a / b       ; Division: 2 (integer division!)
END.
```

*Important*: Division is integer division (no remainder).

#### Operator Precedence

Just like math class:
1. `*` and `/` (multiplication and division)
2. `+` and `-` (addition and subtraction)

```pl0
result := 2 + 3 * 4      ; Result: 14 (not 20!)
result := (2 + 3) * 4    ; Result: 20
```

#### Unary Minus

```pl0
VAR x, y;
BEGIN
    x := 10;
    y := -x              ; y = -10
END.
```



### Control Flow

#### IF-THEN

Execute a statement only if a condition is true:

```pl0
VAR x;
BEGIN
    x := 5;
    
    IF x > 3 THEN
        WRITE 1 TO $D000
END.
```

*Note*: Standard PL/0 has no `ELSE` clause!

#### Comparison Operators

```pl0
=       ; Equal to
##       ; Not equal to
<       ; Less than
<=      ; Less than or equal to
>       ; Greater than
>=      ; Greater than or equal to
```

#### Simulating IF-ELSE

Use two IF statements:

```pl0
VAR x, y;
BEGIN
    x := 5;
    
    IF x > 3 THEN
        y := 1;
        
    IF x <= 3 THEN
        y := 0
END.
```

#### WHILE-DO

Repeat a statement while a condition is true:

```pl0
VAR i;
BEGIN
    i := 0;
    WHILE i < 10 DO
        i := i + 1
END.
```

#### FOR Loops (Simulated)

PL/0 doesn't have FOR loops, but you can simulate them:

```pl0
VAR i;
BEGIN
    i := 0;                    ; Initialize
    WHILE i < 10 DO            ; Condition
    BEGIN
        ; Loop body here
        i := i + 1             ; Increment
    END
END.
```

#### BEGIN-END Blocks

Use `BEGIN...END` to group multiple statements:

```pl0
VAR i;
BEGIN
    i := 0;
    WHILE i < 10 DO
    BEGIN
        WRITE i TO $0400 + i;
        WRITE 1 TO $D800 + i;
        i := i + 1
    END
END.
```

*Important*: Statements are separated by semicolons (`;`), not terminated by them!

```pl0
BEGIN
    x := 1;      ; Semicolon separates statements
    y := 2;      ; Semicolon separates statements
    z := 3       ; No semicolon before END!
END.
```



### Procedures

Procedures are reusable blocks of code (like functions, but without parameters or return values).

#### Defining a Procedure

```pl0
PROCEDURE sayHello;
BEGIN
    WRITE 72 TO $0400;     ; 'H'
    WRITE 73 TO $0401      ; 'I'
END;

BEGIN
    CALL sayHello
END.
```

#### Procedures with Local Variables

```pl0
VAR globalVar;

PROCEDURE increment;
VAR localVar;
BEGIN
    localVar := globalVar;
    localVar := localVar + 1;
    globalVar := localVar
END;

BEGIN
    globalVar := 5;
    CALL increment;        ; globalVar is now 6
    CALL increment         ; globalVar is now 7
END.
```

#### Nested Procedures

```pl0
PROCEDURE outer;
VAR x;

    PROCEDURE inner;
    BEGIN
        x := x + 1
    END;

BEGIN
    x := 0;
    CALL inner;
    CALL inner
END;

BEGIN
    CALL outer
END.
```



### I/O Extensions

Our enhanced PL/0 includes four I/O statements for hardware interaction.

#### READ variable FROM address

Read a byte from memory into a variable:

```pl0
VAR buttons;
BEGIN
    READ buttons FROM $DC00
END.
```

#### WRITE expression TO address

Write a value to a memory address:

```pl0
BEGIN
    WRITE 6 TO $D000;           ; Write literal
    WRITE myVar TO $D001;       ; Write variable
    WRITE x + y TO $D002        ; Write expression
END.
```

#### IN variable

Read button state (shorthand for `READ variable FROM $DC00`):

```pl0
VAR buttons;
BEGIN
    IN buttons;
    IF buttons ## 255 THEN
        WRITE 2 TO $D000
END.
```

#### OUT expression

Output a value to the screen (with automatic cursor advancement):

```pl0
VAR result;
BEGIN
    result := 42;
    OUT result
END.
```



### Hardware Programming

#### Memory Map

The system uses a C64-inspired memory layout:

| Address Range | Description |
|---------------|-------------|
| `$0000-$00FF` | Zero Page |
| `$0100-$01FF` | Stack |
| `$0400-$07AF` | Screen RAM (40×30 = 1200 chars) |
| `$D000-$D01F` | VIC-II Registers |
| `$D800-$DBAF` | Color RAM (40×30 = 1200 bytes) |
| `$DC00` | Button State |

#### Pre-defined Constants

These hardware addresses are built into the compiler:

```pl0
SCREEN      $0400    ; Screen RAM start
COLOR       $D800    ; Color RAM start
BORDER      $D000    ; Border color register
BGCOLOR     $D001    ; Background color register
CURSOR_X    $D002    ; Cursor X position
CURSOR_Y    $D003    ; Cursor Y position
BUTTONS     $DC00    ; Button state register
```

#### C64 Color Palette

```pl0
CONST BLACK = 0,
      WHITE = 1,
      RED = 2,
      CYAN = 3,
      PURPLE = 4,
      GREEN = 5,
      BLUE = 6,
      YELLOW = 7,
      ORANGE = 8,
      BROWN = 9,
      LIGHT_RED = 10,
      DARK_GREY = 11,
      GREY = 12,
      LIGHT_GREEN = 13,
      LIGHT_BLUE = 14,
      LIGHT_GREY = 15;
```

#### Setting Colors

```pl0
CONST BLUE = 6, CYAN = 3, WHITE = 1;

BEGIN
    WRITE BLUE TO BORDER;      ; Blue border
    WRITE CYAN TO BGCOLOR;     ; Cyan background
    WRITE WHITE TO COLOR       ; White text color
END.
```

#### Writing to Screen

The screen is 40 columns × 30 rows. Calculate position as: `row * 40 + column`

```pl0
VAR x, y, pos;
BEGIN
    x := 10;        ; Column 10
    y := 5;         ; Row 5
    pos := y * 40 + x;
    
    WRITE 65 TO SCREEN + pos;    ; Write 'A' (ASCII 65)
    WRITE 1 TO COLOR + pos       ; White color
END.
```

#### ASCII Character Codes

Common characters:
- Space: `32`
- `0-9`: `48-57`
- `A-Z`: `65-90`
- `a-z`: `97-122`

```pl0
BEGIN
    WRITE 72 TO SCREEN;      ; 'H'
    WRITE 69 TO SCREEN + 1;  ; 'E'
    WRITE 76 TO SCREEN + 2;  ; 'L'
    WRITE 76 TO SCREEN + 3;  ; 'L'
    WRITE 79 TO SCREEN + 4   ; 'O'
END.
```

#### Reading Buttons

Button bits (active low - 0 when pressed):
- Bit 0: Button A
- Bit 1: Button B
- Bit 2: Button X
- Bit 3: Button Y

```pl0
VAR buttons;
BEGIN
    IN buttons;
    IF buttons ## 255 THEN
        ; Some button is pressed
        WRITE 2 TO BORDER
END.
```



### Complete Examples

#### Example 1: Hello World

```pl0
CONST WHITE = 1;
VAR i;

BEGIN
    ; Set screen colors
    WRITE 6 TO BORDER;
    WRITE 14 TO BGCOLOR;
    
    ; Write "HELLO" to screen
    WRITE 72 TO SCREEN;      ; H
    WRITE 69 TO SCREEN + 1;  ; E
    WRITE 76 TO SCREEN + 2;  ; L
    WRITE 76 TO SCREEN + 3;  ; L
    WRITE 79 TO SCREEN + 4;  ; O
    
    ; Set all to white color
    i := 0;
    WHILE i < 5 DO
    BEGIN
        WRITE WHITE TO COLOR + i;
        i := i + 1
    END
END.
```

#### Example 2: Animated Border

```pl0
VAR color, delay, i;

PROCEDURE wait;
VAR j;
BEGIN
    j := 0;
    WHILE j < 1000 DO
        j := j + 1
END;

BEGIN
    color := 0;
    
    WHILE 1 = 1 DO
    BEGIN
        WRITE color TO BORDER;
        CALL wait;
        
        color := color + 1;
        IF color > 15 THEN
            color := 0
    END
END.
```

#### Example 3: Button-Controlled Cursor

```pl0
CONST BTN_ALL = 255;
VAR buttons, x, y, pos;

PROCEDURE drawCursor;
BEGIN
    pos := y * 40 + x;
    WRITE 42 TO SCREEN + pos;    ; '*' character
    WRITE 7 TO COLOR + pos       ; Yellow
END;

BEGIN
    x := 0;
    y := 0;
    
    WHILE 1 = 1 DO
    BEGIN
        IN buttons;
        
        IF buttons ## BTN_ALL THEN
        BEGIN
            CALL drawCursor;
            
            x := x + 1;
            IF x > 39 THEN
            BEGIN
                x := 0;
                y := y + 1;
                IF y > 29 THEN
                    y := 0
            END
        END
    END
END.
```

#### Example 4: Factorial Calculator

```pl0
VAR n, result;

PROCEDURE factorial;
VAR i;
BEGIN
    result := 1;
    i := n;
    
    WHILE i > 1 DO
    BEGIN
        result := result * i;
        i := i - 1
    END
END;

BEGIN
    n := 5;
    CALL factorial;
    OUT result         ; Output: 120
END.
```

#### Example 5: Screen Fill Pattern

```pl0
CONST ROWS = 30, COLS = 40;
VAR row, col, pos, char;

PROCEDURE fillRow;
BEGIN
    col := 0;
    WHILE col < COLS DO
    BEGIN
        pos := row * COLS + col;
        char := 65 + col;         ; 'A' + column offset
        
        WRITE char TO SCREEN + pos;
        WRITE row TO COLOR + pos;  ; Color based on row
        
        col := col + 1
    END
END;

BEGIN
    WRITE 0 TO BORDER;
    WRITE 0 TO BGCOLOR;
    
    row := 0;
    WHILE row < ROWS DO
    BEGIN
        CALL fillRow;
        row := row + 1
    END
END.
```

#### Example 6: Simple Game Loop

```pl0
CONST PLAYER_CHAR = 64;    ; '@' symbol
VAR playerX, playerY, buttons, oldPos, newPos;

PROCEDURE clearPlayer;
BEGIN
    oldPos := playerY * 40 + playerX;
    WRITE 32 TO SCREEN + oldPos  ; Space character
END;

PROCEDURE drawPlayer;
BEGIN
    newPos := playerY * 40 + playerX;
    WRITE PLAYER_CHAR TO SCREEN + newPos;
    WRITE 1 TO COLOR + newPos    ; White
END;

PROCEDURE handleInput;
BEGIN
    IN buttons;
    
    ; Button A pressed (bit 0)
    IF buttons < 255 THEN
    BEGIN
        CALL clearPlayer;
        playerX := playerX + 1;
        IF playerX > 39 THEN
            playerX := 0;
        CALL drawPlayer
    END
END;

BEGIN
    ; Initialize
    playerX := 20;
    playerY := 15;
    
    WRITE 6 TO BORDER;
    WRITE 14 TO BGCOLOR;
    
    CALL drawPlayer;
    
    ; Game loop
    WHILE 1 = 1 DO
        CALL handleInput
END.
```



### Tips and Best Practices

#### 1. Structure Your Code

Use procedures to organize your code into logical sections:

```pl0
PROCEDURE init;
BEGIN
    ; Initialization code
END;

PROCEDURE update;
BEGIN
    ; Update game state
END;

PROCEDURE render;
BEGIN
    ; Draw to screen
END;

BEGIN
    CALL init;
    WHILE 1 = 1 DO
    BEGIN
        CALL update;
        CALL render
    END
END.
```

#### 2. Use Meaningful Names

```pl0
; Bad
VAR x, y, z, a, b;

; Good
VAR playerX, playerY, score, lives, currentLevel;
```

#### 3. Use Constants for Magic Numbers

```pl0
; Bad
IF x > 39 THEN
    x := 0;

; Good
CONST MAX_X = 39;
IF x > MAX_X THEN
    x := 0;
```

#### 4. Calculate Screen Positions Carefully

```pl0
CONST SCREEN_WIDTH = 40;
VAR row, col, screenPos;

BEGIN
    screenPos := row * SCREEN_WIDTH + col;
    WRITE 65 TO SCREEN + screenPos
END.
```

#### 5. Remember Integer Division

```pl0
VAR half;
BEGIN
    half := 5 / 2;      ; Result: 2 (not 2.5!)
END.
```

To work with fractions, multiply first:

```pl0
VAR percentage;
BEGIN
    percentage := (score * 100) / maxScore
END.
```

#### 6. Watch Your Semicolons

```pl0
; Correct
BEGIN
    x := 1;    ; Separates statements
    y := 2     ; No semicolon before END
END;

; Wrong
BEGIN
    x := 1;
    y := 2;    ; Extra semicolon causes error
END;
```

#### 7. Use BEGIN-END for Multiple Statements

```pl0
; Single statement - no BEGIN-END needed
IF x > 0 THEN
    y := 1;

; Multiple statements - need BEGIN-END
IF x > 0 THEN
BEGIN
    y := 1;
    z := 2
END;
```

#### 8. Create Helper Procedures

```pl0
PROCEDURE clearScreen;
VAR i;
BEGIN
    i := 0;
    WHILE i < 1200 DO
    BEGIN
        WRITE 32 TO SCREEN + i;  ; Space
        i := i + 1
    END
END;

PROCEDURE setBorder;
BEGIN
    WRITE borderColor TO BORDER
END;
```

#### 9. Limit Variable Scope

Declare variables in procedures when they're only needed locally:

```pl0
VAR globalScore;

PROCEDURE calculateBonus;
VAR tempValue, multiplier;
BEGIN
    tempValue := globalScore;
    multiplier := 2;
    globalScore := tempValue * multiplier
END;
```

#### 10. Test Incrementally

Build your program in small steps:

1. Start with basic structure
2. Add one feature at a time
3. Test after each addition
4. Use the border color for debugging:

```pl0
BEGIN
    WRITE 5 TO BORDER;     ; Green = reached this point
    ; ... your code ...
    WRITE 2 TO BORDER      ; Red = reached end
END.
```



### Common Errors and Solutions

#### Error: "Unexpected input after program"

*Problem*: Missing period at the end

```pl0
; Wrong
BEGIN
    x := 1
END

; Correct
BEGIN
    x := 1
END.
```

#### Error: "Undefined variable"

*Problem*: Variable not declared

```pl0
; Wrong
BEGIN
    x := 1
END.

; Correct
VAR x;
BEGIN
    x := 1
END.
```

#### Error: "Parse error"

*Problem*: Usually a syntax mistake

Common causes:
- Missing semicolon between statements
- Extra semicolon before `END`
- Misspelled keywords
- Missing `THEN` after `IF`
- Missing `DO` after `WHILE`

#### Debugging Techniques

Use border color changes to trace execution:

```pl0
VAR x;
BEGIN
    WRITE 5 TO BORDER;     ; Checkpoint 1
    x := 10;
    WRITE 13 TO BORDER;    ; Checkpoint 2
    WHILE x > 0 DO
    BEGIN
        WRITE 2 TO BORDER;  ; In loop
        x := x - 1
    END;
    WRITE 1 TO BORDER      ; Done
END.
```



### Quick Reference Card

#### Program Structure
```pl0
CONST name = value;
VAR name1, name2;
PROCEDURE name;
BEGIN statements END;
BEGIN main END.
```

#### Operators
```
+  -  *  /          Arithmetic
=  ##  <  <=  >  >=  Comparison
```

#### Control Flow
```pl0
IF condition THEN statement
WHILE condition DO statement
BEGIN stmt1; stmt2; stmt3 END
```

#### I/O
```pl0
READ var FROM addr
WRITE expr TO addr
IN var
OUT expr
```

#### Hardware
```
SCREEN   $0400    BORDER    $D000
COLOR    $D800    BGCOLOR   $D001
BUTTONS  $DC00    CURSOR_X  $D002
                  CURSOR_Y  $D003
```

