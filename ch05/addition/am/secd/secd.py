from collections import namedtuple

State = namedtuple('State', ('stack', 'environment', 'control', 'dump'))

def check_stack(stack, n, cmd_name, types=None):
    if len(stack) < n:
        raise ValueError(f"{cmd_name} requires {n} elements on the stack, got {len(stack)}")
    if types:
        for i, (val, expected) in enumerate(zip(stack[-n:], types), 1):
            if not isinstance(val, expected):
                raise TypeError(f"{cmd_name} expects {expected.__name__} at position {i}, got {type(val).__name__}")

def ADD_command(stack, env, control, dump):
    check_stack(stack, 2, "ADD", types=[(int, float), (int, float)])
    b, a = stack.pop(), stack.pop()
    stack.append(a + b)

def SUB_command(stack, env, control, dump):
    check_stack(stack, 2, "SUB", types=[(int, float), (int, float)])
    b, a = stack.pop(), stack.pop()
    stack.append(b - a)

def MUL_command(stack, env, control, dump):
    check_stack(stack, 2, "MUL", types=[(int, float), (int, float)])
    b, a = stack.pop(), stack.pop()
    stack.append(a * b)

def DIV_command(stack, env, control, dump):
    check_stack(stack, 2, "DIV", types=[(int, float), (int, float)])
    b, a = stack.pop(), stack.pop()
    if b == 0:
        raise ValueError("Division by zero")
    stack.append(a / b)

def EQ_command(stack, env, control, dump):
    check_stack(stack, 2, "EQ")
    b, a = stack.pop(), stack.pop()
    stack.append(a == b)

def LT_command(stack, env, control, dump):
    check_stack(stack, 2, "LT", types=[(int, float), (int, float)])
    b, a = stack.pop(), stack.pop()
    stack.append(b < a)

def GT_command(stack, env, control, dump):
    check_stack(stack, 2, "GT", types=[(int, float), (int, float)])
    b, a = stack.pop(), stack.pop()
    stack.append(b > a)

def LEQ_command(stack, env, control, dump):
    check_stack(stack, 2, "LEQ", types=[(int, float), (int, float)])
    b, a = stack.pop(), stack.pop()
    stack.append(b <= a)

def POP_command(stack, env, control, dump):
    check_stack(stack, 1, "POP")
    stack.pop()

def DUP_command(stack, env, control, dump):
    check_stack(stack, 1, "DUP")
    stack.append(stack[-1])

def SWAP_command(stack, env, control, dump):
    check_stack(stack, 2, "SWAP")
    a, b = stack.pop(), stack.pop()
    stack.append(a)
    stack.append(b)

def CONS_command(stack, env, control, dump):
    check_stack(stack, 2, "CONS")
    b, a = stack.pop(), stack.pop()
    stack.append([b, a])

def CAR_command(stack, env, control, dump):
    check_stack(stack, 1, "CAR", types=[list])
    stack.append(stack.pop()[0])

def CDR_command(stack, env, control, dump):
    check_stack(stack, 1, "CDR", types=[list])
    stack.append(stack.pop()[1])

def NIL_command(stack, env, control, dump):
    stack.append([])

def ATOM_command(stack, env, control, dump):
    check_stack(stack, 1, "ATOM")
    stack.append(not isinstance(stack.pop(), list))

def SEL_command(stack, env, control, dump):
    if len(stack) < 1 or len(control) < 2:
        raise ValueError("SEL requires one stack element and two control branches")
    condition = stack.pop()
    then_branch, else_branch = control[:2]
    dump.append(control[2:].copy())
    control[:] = then_branch if condition else else_branch

def JOIN_command(stack, env, control, dump):
    if not dump:
        raise ValueError("JOIN requires a non-empty dump")
    control[:] = dump.pop()

def RTN_command(stack, env, control, dump):
    if len(stack) < 1 or len(dump) < 3:
        raise ValueError("RTN requires one stack element and three dump elements")
    result = stack.pop()
    control[:] = dump.pop()
    stack[:] = dump.pop()
    env[:] = dump.pop()
    stack.append(result)

def LD_command(stack, env, control, dump):
    if len(control) < 2:
        raise ValueError("LD requires two indices")
    i, j = control.pop(0), control.pop(0)
    if i >= len(env):
        raise IndexError(f"Environment access error: frame {i} out of bounds")
    if not isinstance(env[i], list):
        raise TypeError(f"Environment frame {i} must be a list, got {type(env[i]).__name__}")
    if j >= len(env[i]):
        raise IndexError(f"Environment access error: index [{i},{j}] out of bounds")
    value = env[i][j]
    stack.append(value)

def LDC_command(stack, env, control, dump):
    if not control:
        raise ValueError("LDC requires a value in control")
    stack.append(control.pop(0))

def LDF_command(stack, env, control, dump):
    if not control:
        raise ValueError("No function body in control for LDF")
    func_code = control.pop(0)
    closure = [func_code, env.copy()]
    print(f"LDF created closure: {closure}")  # Debug
    stack.append(closure)

def AP_command(stack, env, control, dump):
    check_stack(stack, 2, "AP")
    args = stack.pop()
    closure = stack.pop()
    print(f"AP: args={args}, closure={closure}")  # Debug
    if not isinstance(closure, list) or len(closure) != 2:
        raise TypeError(f"Expected closure [code, env], got: {closure}")
    func_code, closure_env = closure
    if not isinstance(closure_env, list):
        raise TypeError(f"Closure environment must be a list, got: {closure_env}")
    if not isinstance(args, list):
        args = [args]
    dump.append(env.copy())
    dump.append(stack.copy())
    dump.append(control.copy())
    env[:] = [args] + closure_env
    stack[:] = []
    control[:] = func_code.copy() if isinstance(func_code, list) else [func_code]

def RAP_command(stack, env, control, dump):
    check_stack(stack, 2, "RAP")
    args = stack.pop()
    closure = stack.pop()
    print(f"RAP: args={args}, closure={closure}")  # Debug
    if not isinstance(closure, list) or len(closure) != 2:
        raise TypeError(f"Expected closure [code, env], got: {closure}")
    func_code, closure_env = closure
    if not isinstance(closure_env, list):
        raise TypeError(f"Closure environment must be a list, got: {closure_env}")
    if not isinstance(args, list):
        args = [args]
    dump.append(env.copy())
    dump.append(stack.copy())
    dump.append(control.copy())
    env[:] = [args] + closure_env
    stack[:] = []
    control[:] = func_code.copy() if isinstance(func_code, list) else [func_code]

def DUM_command(stack, env, control, dump):
    env.insert(0, None)

COMMANDS = {
    'ADD': ADD_command,
    'SUB': SUB_command,
    'MUL': MUL_command,
    'DIV': DIV_command,
    'EQ': EQ_command,
    'LT': LT_command,
    'GT': GT_command,
    'LEQ': LEQ_command,
    'POP': POP_command,
    'DUP': DUP_command,
    'SWAP': SWAP_command,
    'CONS': CONS_command,
    'CAR': CAR_command,
    'CDR': CDR_command,
    'NIL': NIL_command,
    'ATOM': ATOM_command,
    'SEL': SEL_command,
    'JOIN': JOIN_command,
    'RTN': RTN_command,
    'LD': LD_command,
    'LDC': LDC_command,
    'LDF': LDF_command,
    'AP': AP_command,
    'RAP': RAP_command,
    'DUM': DUM_command,
}

def secd_eval(code, debug=False, max_steps=1000, log_file=None):
    state = State([], [], code.copy(), [])
    steps = 0
    while state.control and steps < max_steps:
        steps += 1
        if debug:
            log = f"\nStep {steps}:\nStack: {state.stack}\nEnvironment: {state.environment}\nControl: {state.control}\nDump: {state.dump}\n---"
            if log_file:
                with open(log_file, 'a') as f:
                    f.write(log + "\n")
            else:
                print(log)
        state = secd_step(state, debug)
    if steps >= max_steps:
        raise RuntimeError("Maximum steps exceeded")
    return state.stack[0] if state.stack else None

def secd_step(state, debug=False):
    stack, env, control, dump = state
    if not control:
        return state
    cmd = control.pop(0)
    if debug:
        print(f"Executing: {cmd}")
        print(f"Stack before: {stack}")
    try:
        if isinstance(cmd, str) and cmd in COMMANDS:
            COMMANDS[cmd](stack, env, control, dump)
        elif isinstance(cmd, (int, float, str, bool, list)):
            stack.append(cmd)
        else:
            raise ValueError(f"Unknown command: {cmd}")
    except Exception as e:
        if debug:
            print(f"Error executing {cmd}: {e}")
            print(f"Stack: {stack}")
            print(f"Environment: {env}")
            print(f"Control: {control}")
        raise
    if debug:
        print(f"Stack after: {stack}")
        print(f"Environment: {env}")
        print(f"Control: {control}")
        print(f"Dump: {dump}")
    return State(stack, env, control, dump)

if __name__ == "__main__":
    # Test 1: Simple arithmetic
    code1 = ['LDC', 5, 'LDC', 3, 'ADD']
    print("\nTest 1 (5 + 3):", secd_eval(code1))  # Output: 8

    # Test 2: Conditional
    code2 = ['LDC', True, 'SEL', ['LDC', 10], ['LDC', 20], 'JOIN']
    print("\nTest 2 (SEL True 10 20):", secd_eval(code2))  # Output: 10

    # Test 3: Function application
    code3 = [
        'LDC', 3,           # Push 3
        'LDC', 5,           # Push 5
        'CONS',             # Create [5, 3]
        'LDF', [            # Create function
            'LD', 0, 0,     # Load first arg (5)
            'LD', 0, 1,     # Load second arg (3)
            'ADD',          # Add them
            'RTN'           # Return result
        ],
        'SWAP',             # Swap to [[[...], []], [5, 3]]
        'AP'                # Apply function to args
    ]
    print("\nTest 3 (Function 5+3):", secd_eval(code3))  # Output: 8

    # Test 4: Identity function
    code4 = [
        'LDC', 42,          # Push 42
        'LDF', ['LD', 0, 0, 'RTN'],  # Create function
        'SWAP',             # Swap to [[closure], 42]
        'AP'                # Apply function to arg
    ]
    print("\nTest 4 (Identity function):", secd_eval(code4))  # Output: 42

    # Test 5: List construction
    code5 = [
        'NIL',              # Push []
        'LDC', 1,           # Push 1
        'CONS',             # Create [1, []]
        'LDC', 2,           # Push 2
        'CONS',             # Create [2, [1, []]]
        'LDC', 3,           # Push 3
        'CONS'              # Create [3, [2, [1, []]]]
    ]
    print("\nTest 5 (List construction):", secd_eval(code5))  # Output: [3, [2, [1, []]]]

    # Test 6: Subtraction order
    code6 = ['LDC', 3, 'LDC', 5, 'SUB']
    print("\nTest 6 (5 - 3):", secd_eval(code6))  # Output: 2

    # Test 7: Division by zero
    code7 = ['LDC', 5, 'LDC', 0, 'DIV']
    try:
        print("\nTest 7 (Division by zero):", secd_eval(code7))
    except ValueError as e:
        print("\nTest 7 (Division by zero):", str(e))  # Output: Division by zero

    # Test 8: Insufficient stack
    code8 = ['LDC', 5, 'ADD']
    try:
        print("\nTest 8 (Insufficient stack for ADD):", secd_eval(code8))
    except ValueError as e:
        print("\nTest 8 (Insufficient stack for ADD):", str(e))  # Output: ADD requires 2 elements...

    # Test 9: List length function
    code9 = [
        'DUM',              # env = [None]
        'LDF', [            # Length function
            'LD', 0, 0,     # Load list arg
            'ATOM',         # Check if atom (empty)
            'SEL',          # Branch
            ['LDC', 0, 'RTN'],  # Return 0 if empty
            [               # Else
                'LD', 0, 0, # Load list
                'CDR',      # Get tail
                'LD', 0, 0, # Load length function from env[0][0]
                'AP',       # Apply to tail
                'LDC', 1,   # Push 1
                'ADD',      # Add 1 to result
                'RTN'       # Return
            ],
            'JOIN'
        ],
        'NIL',              # stack = [[]]
        'CONS',             # env = [[closure], None]
        'LDF', ['LD', 0, 0, 'RTN'],  # Identity function
        'NIL',              # Push []
        'LDC', 1,           # Push 1
        'CONS',             # [1, []]
        'LDC', 2,           # Push 2
        'CONS',             # [2, [1, []]]
        'LDC', 3,           # Push 3
        'CONS',             # [3, [2, [1, []]]]
        'SWAP',             # Swap to [[identity, [[closure], None]], [3, [2, [1, []]]]]
        'AP',               # Apply identity to get [3, [2, [1, []]]]
        'RAP'               # Apply length function
    ]
    print("\nTest 9 (List length):", secd_eval(code9))  # Output: 3