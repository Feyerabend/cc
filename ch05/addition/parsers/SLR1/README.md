
## SLR(1)

*SLR(1)* stands for *Simple LR(1) parser*.
It is a type of bottom-up parser used in compiler design.
It's one of the simplest and most efficient methods for parsing context-free grammars.

Key characteristics:
- *LR* = Left-to-right scan, Rightmost derivation in reverse
- *(1)* = Uses 1 lookahead token to make parsing decisions
- *Simple* = Uses a simplified method for constructing the
  parsing table compared to more complex LR parsers

SLR(1) parsers use two main components:
1. *Action table*: Determines whether to shift (read next token) or reduce (apply a grammar rule)
2. *Goto table*: Determines the next state after a reduction

This program implements an SLR(1) parser for a simple arithmetic expression grammar:

```
E -> E + T | T       (addition)
T -> T * F | F       (multiplication)
F -> ( E ) | num     (parentheses and numbers)
```

*The program:*
1. *Tokenises* an input expression (e.g., `"3 + 4 * (2 + 5)"`) into tokens: `num`, `+`, `*`, `(`, `)`, `$`
2. *Parses* using a state machine with 12 states (0-11)
3. *Uses shift-reduce actions*:
   - *Shift*: Push the current token and move to a new state
   - *Reduce*: Apply a grammar production rule and backtrack states
   - *Accept*: Successfully parsed the input
4. *Respects operator precedence*: `*` binds tighter than `+` (multiplication before addition)
5. *Handles parentheses* for grouping expressions

The parser validates that the expression follows the grammar rules
and reports success or raises a syntax error if the input is malformed.

The diagram below shows:
- Shift transitions (solid arrows with terminal symbols like num, +, *, (, ))
- Goto transitions (labeled with non-terminals like E, T, F)
- Reduce actions (noted with self-loops or notes showing which production is reduced)
- Accept action (transition to final state with $)

```mermaid
stateDiagram-v2
    [*] --> State0
    
    State0 --> State5: num
    State0 --> State4: (
    State0 --> State1: E (goto)
    State0 --> State2: T (goto)
    State0 --> State3: F (goto)
    
    State1 --> State6: +
    State1 --> [*]: $ (accept)
    
    State2 --> State7: *
    State2 --> State2: +/)/$ (reduce by E→T)
    
    State3 --> State3: +/*/)/$ (reduce by T→F)
    
    State4 --> State5: num
    State4 --> State4: (
    State4 --> State8: E (goto)
    State4 --> State2: T (goto)
    State4 --> State3: F (goto)
    
    State5 --> State5: +/*/)/$ (reduce by F→num)
    
    State6 --> State5: num
    State6 --> State4: (
    State6 --> State9: T (goto)
    State6 --> State3: F (goto)
    
    State7 --> State5: num
    State7 --> State4: (
    State7 --> State10: F (goto)
    
    State8 --> State6: +
    State8 --> State11: )
    
    State9 --> State7: *
    State9 --> State9: +/)/$ (reduce by E→E+T)
    
    State10 --> State10: +/*/)/$ (reduce by T→T*F)
    
    State11 --> State11: +/*/)/$ (reduce by F→(E))
    
    note right of State1
        Accept state
    end note
    
    note right of State2
        Reduce: E → T
    end note
    
    note right of State3
        Reduce: T → F
    end note
    
    note right of State5
        Reduce: F → num
    end note
    
    note right of State9
        Reduce: E → E+T
    end note
    
    note right of State10
        Reduce: T → T*F
    end note
    
    note right of State11
        Reduce: F → (E)
    end note
```








