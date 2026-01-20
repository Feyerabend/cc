class StateMachineTokenizer:
    def __init__(self):
        self.tokens = []
        self.state = "START"

    def tokenize(self, input_string):
        self.tokens = []
        self.state = "START"
        buffer = ""
        i = 0

        while i < len(input_string):
            char = input_string[i]

            if self.state == "START":
                if char.isalpha():  # start of an identifier
                    self.state = "IDENTIFIER"
                    buffer += char
                elif char.isdigit():  # start of a number
                    self.state = "NUMBER"
                    buffer += char
                elif char in "+-*/=":  # operators, including '='
                    self.tokens.append(("OPERATOR", char))
                elif char.isspace():
                    pass  # ignore spaces
                else:
                    raise ValueError(f"Unexpected character: {char}")

            elif self.state == "IDENTIFIER":
                if char.isalnum():  # continue identifier
                    buffer += char
                else:  # identifier ends
                    self.tokens.append(("IDENTIFIER", buffer))
                    buffer = ""
                    self.state = "START"
                    continue  # skip the current character and reprocess it in the next loop

            elif self.state == "NUMBER":
                if char.isdigit():  # continue number
                    buffer += char
                else:  # number ends
                    self.tokens.append(("NUMBER", buffer))
                    buffer = ""
                    self.state = "START"
                    continue  # skip the current character and reprocess it in the next loop

            i += 1

        # Flush remaining buffer
        if buffer:
            if self.state == "IDENTIFIER":
                self.tokens.append(("IDENTIFIER", buffer))
            elif self.state == "NUMBER":
                self.tokens.append(("NUMBER", buffer))

        return self.tokens



# test
tokenizer = StateMachineTokenizer()
print(tokenizer.tokenize("x = 42 + y * 5"))
# output: [
#   ('IDENTIFIER', 'x'),
#   ('OPERATOR', '='),
#   ('NUMBER', '42'),
#   ('OPERATOR', '+'),
#   ('IDENTIFIER', 'y'),
#   ('OPERATOR', '*'),
#   ('NUMBER', '5')
# ]
