
## Bottom-Up: LR grammar

This *LR(0) parser* processes a grammar and input string while maintaining a stack and an action table to decide shifts and reductions.

### Example Grammar
We will use a simplified grammar:
1. $\( S' \to S \)$  (start production)
2. $\( S \to aSb \)$
3. $\( S \to \epsilon \)$ (epsilon means the empty string)


### Input
Consider the input string: `aabb`.


### Steps in Parsing

An LR parser uses a *parsing table* consisting of states, actions (shift/reduce), and transitions based on the grammar's rules. The parser maintains:
- A *stack* for states and grammar symbols.
- An *input buffer* for remaining tokens.

The parsing table might look like this for the grammar:

| State | $\( a \)$   | $\( b \)$   | $\(\\$\)$ (end) | $\( S \)$   |
|-------|-----------|-----------|--------------|-----------|
| 0     | Shift 2   |           |              | Goto 1    |
| 1     |           |           | Accept       |           |
| 2     | Shift 2   | Reduce 3  |              | Goto 3    |
| 3     |           | Shift 4   | Reduce 2     |           |
| 4     | Reduce 2  |           |              |           |


While both a parsing table and, what we have already studied, a state machine involve states
and transitions (often based on input symbols), a parsing table is more specialized because
it includes actions for both shifting states and reducing based on grammar rules. A state
machine focuses on state transitions and typically doesn't involve grammar application or
reductions. Therefore, they are not the same, even though they share some structural
similarities.


### Parsing Process

We will parse the input `aabb$` (the `$` symbol marks the end of input).


1. Initial State:
   - Stack = `[0]`
   - Input = `aabb$`
   - Action: Shift $\( a \)$.


2. Shift $\( a \)$:
   - Stack = `[0, a, 2]`
   - Input = `abb$`
   - Action: Shift $\( a \)$.


3. Shift $\( a \)$:
   - Stack = `[0, a, 2, a, 2]`
   - Input = `bb$`
   - Action: Reduce $\( S \to \epsilon \)$.


4. Reduce $\( S \to \epsilon \)$:
   - Stack = `[0, a, 2, S, 3]`
   - Input = `bb$`
   - Action: Shift $\( b \)$.


5. Shift $\( b \)$:
   - Stack = `[0, a, 2, S, 3, b, 4]`
   - Input = `b$`
   - Action: Reduce $\( S \to a S b \)$.


6. Reduce $\( S \to a S b \)$:
   - Replace $\( a, S, b \)$ and associated states with $\( S \)$.
   - Stack = `[0, S, 1]`
   - Input = `b$`
   - Action: Shift $\( b \)$.


7. Shift $\( b \)$:
   - Stack = `[0, S, 1, b, 4]`
   - Input = `$`
   - Action: Reduce $\( S \to a S b \)$.


8. Reduce $\( S \to a S b \)$:
   - Replace $\( a, S, b \)$ and associated states with $\( S \)$.
   - Stack = `[0, S, 1]`
   - Input = `$`
   - Action: Accept.


### Code Implementation
Here's an example implementation in Python:

```python
class LRParser:
    def __init__(self, grammar, parsing_table):
        self.grammar = grammar
        self.parsing_table = parsing_table
        self.stack = [0]  # initial state

    def parse(self, input_string):
        input_string += "$"  # end marker
        index = 0

        while True:
            # debug: current stack and input
            print(f"Stack: {self.stack}, Input: {input_string[index:]}")
            
            state = self.stack[-1]
            char = input_string[index] if index < len(input_string) else "$"

            action = self.parsing_table.get((state, char))
            if action is None:
                raise ValueError(f"Error at character {char} with state {state}")

            print(f"Action: {action}")  # debug: action being performed

            if action[0] == "Shift":
                self.stack.append(char)  # push character
                self.stack.append(action[1])  # push new state
                index += 1  # move to next character

            elif action[0] == "Reduce":
                rule_num = action[1]
                lhs, rhs = self.grammar[rule_num]
                print(f"Reducing by rule {rule_num}: {lhs} -> {rhs}")  # debug: reduction details
                
                for _ in range(len(rhs) * 2):  # pop symbols and states
                    self.stack.pop()
                state = self.stack[-1]
                goto_action = self.parsing_table.get((state, lhs))
                
                if not goto_action or goto_action[0] != "Goto":
                    raise ValueError(f"No Goto action found for state {state} and non-terminal {lhs}")
                
                self.stack.append(lhs)  # push the non-terminal
                self.stack.append(goto_action[1])  # push new state

            elif action[0] == "Accept":
                print("Input accepted!")
                return

            else:
                raise ValueError(f"Invalid action {action}")

# {rule_number: (LHS, RHS)}
grammar = {
    1: ("S'", ["S"]),
    2: ("S", ["a", "S", "b"]),
    3: ("S", [])  # empty production
}

# {(state, symbol): action}
parsing_table = {
    (0, "a"): ("Shift", 2),
    (0, "S"): ("Goto", 1),
    (1, "$"): ("Accept", None),
    (2, "a"): ("Shift", 2),
    (2, "b"): ("Reduce", 3),
    (2, "S"): ("Goto", 3),
    (3, "b"): ("Shift", 4),
    (3, "$"): ("Reduce", 2),
    (3, "S"): ("Goto", 1),
    (4, "b"): ("Reduce", 2),
    (4, "$"): ("Reduce", 2),
}

# input and parsing
parser = LRParser(grammar, parsing_table)
parser.parse("aabb")
```
