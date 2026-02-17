from abstack import StackADT
from array_stack import ArrayStack
from linked_list import LinkedStack

def evaluate_rpn(tokens: list[str], stack: StackADT[float]) -> float:
    """
    Evaluate a Reverse Polish Notation expression.
    Uses the StackADT interface: works with ArrayStack OR LinkedStack.
    e.g. "3 4 + 2 * 7 /" -> ((3+4)*2)/7 = 2.0
    """
    ops = {
        '+': lambda a, b: a + b,
        '-': lambda a, b: a - b,
        '*': lambda a, b: a * b,
        '/': lambda a, b: a / b,
    }
    for token in tokens:
        if token in ops:
            b, a = stack.pop(), stack.pop()
            stack.push(ops[token](a, b))
        else:
            stack.push(float(token))
    return stack.pop()

## Both implementations satisfy the contract--totally interchangeable
expressions = [
    ["3", "4", "+", "2", "*", "7", "/"],   ## -> 2.0
    ["5", "1", "2", "+", "4", "*", "+", "3", "-"],  ## -> 14.0
]

for tokens in expressions:
    result_array  = evaluate_rpn(tokens[:], ArrayStack())
    result_linked = evaluate_rpn(tokens[:], LinkedStack())
    print(f"{'  '.join(tokens)}")
    print(f"  ArrayStack  result: {result_array}")
    print(f"  LinkedStack result: {result_linked}")
    print(f"  Results match: {result_array == result_linked}\n")
