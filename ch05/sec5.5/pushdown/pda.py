class PushdownAutomaton:
    
    def __init__(self):
        self.stack = []
    
    def push(self, symbol):
        self.stack.append(symbol)
    
    def pop(self):
        if not self.is_empty():
            return self.stack.pop()
        return None
    
    def peek(self):
        if not self.is_empty():
            return self.stack[-1]
        return None
    
    def is_empty(self):
        return len(self.stack) == 0
    
    def check_balanced(self, input_string):
        # Clear stack for new input
        self.stack = []
        
        # Matching pairs
        pairs = {'(': ')', '[': ']', '{': '}'}
        opening = set(pairs.keys())
        closing = set(pairs.values())
        
        for char in input_string:
            if char in opening:
                # Push opening brackets
                self.push(char)
            elif char in closing:
                # Check matching closing bracket
                if self.is_empty():
                    return False  # No matching opening bracket
                
                top = self.pop()
                if pairs[top] != char:
                    return False  # Mismatched brackets
        
        # Stack should be empty for balanced input
        return self.is_empty()


def main():
    # Create PDA instance
    pda = PushdownAutomaton()
    
    # Test cases
    test_cases = [
        "(())",
        "({[]})",
        "(()",
        "([)]",
        "{[()]}",
        "((())",
        "",
        "(a + b) * [c - {d / e}]",  # With other characters
    ]
    
    print("Testing PDA for balanced parentheses\n")
    
    for test in test_cases:
        result = pda.check_balanced(test)
        status = "ACCEPTED" if result else "REJECTED"
        print(f"Input: '{test}'")
        print(f"Result: {status}")
        print()


if __name__ == "__main__":
    main()
