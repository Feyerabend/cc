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