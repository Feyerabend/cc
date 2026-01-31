# tac.py
# Generate Three-Address Code (TAC) for lambda calculus.
# TAC represents lambda calculus operations as a linear sequence of instructions,
# making the evaluation order explicit and enabling optimization opportunities.

from parser import ASTNode, Var, Lam, App

class TACInstruction:
    """Represents a TAC instruction for lambda calculus."""
    def __init__(self, op, arg1=None, arg2=None, result=None):
        self.op = op          # Operation: 'VAR', 'LAM', 'APP'
        self.arg1 = arg1      # First argument
        self.arg2 = arg2      # Second argument
        self.result = result  # Result variable (temporary)

    def __str__(self):
        if self.op == 'LAM':
            # Lambda: result = λparam.body_temp
            return f"{self.result} = LAM {self.arg1} {self.arg2}"
        elif self.op == 'APP':
            # Application: result = func_temp arg_temp
            return f"{self.result} = APP {self.arg1} {self.arg2}"
        elif self.op == 'VAR':
            # Variable reference: result = var_name
            return f"{self.result} = VAR {self.arg1}"
        return f"{self.result} = {self.op} {self.arg1} {self.arg2}"

def generate_tac(ast):
    """
    Generate TAC from lambda AST.
    
    This function converts a lambda calculus AST into a linear sequence of
    three-address code instructions. Each instruction has at most three
    addresses (two operands and one result).
    
    The TAC representation:
    1. Makes evaluation order explicit
    2. Uses temporary variables for intermediate results
    3. Simplifies complex expressions into simple operations
    4. Enables easier code analysis and optimization
    
    Returns:
        tuple: (list of TACInstructions, final result variable name)
    """
    instructions = []    # List of TACInstruction
    temp_counter = [1]   # Use list to allow modification in nested function

    def traverse(node):
        """
        Recursively traverse AST and generate TAC instructions.
        Each node gets assigned to a temporary variable.
        """
        temp_var = f"t{temp_counter[0]}"
        temp_counter[0] += 1

        if isinstance(node, Var):
            # Variable: simply reference it
            instructions.append(TACInstruction('VAR', node.name, result=temp_var))
        
        elif isinstance(node, Lam):
            # Lambda: first process body, then create lambda with param
            body_temp = traverse(node.body)
            instructions.append(TACInstruction('LAM', node.param, body_temp, result=temp_var))
        
        elif isinstance(node, App):
            # Application: first evaluate function and argument
            func_temp = traverse(node.func)
            arg_temp = traverse(node.arg)
            instructions.append(TACInstruction('APP', func_temp, arg_temp, result=temp_var))
        
        else:
            raise ValueError(f"Unknown AST node type: {type(node)}")

        return temp_var

    final_result = traverse(ast)
    return instructions, final_result

def print_tac(instructions, final_var):
    """
    Print TAC instructions in a readable format.
    
    This shows the linearized form of the lambda expression, making
    the order of operations explicit.
    """

    print("\nTHREE-ADDRESS CODE (TAC) REPRESENTATION\n")
    for idx, instr in enumerate(instructions, 1):
        print(f"{idx:3d}: {instr}")
    print(f"\nFinal result in: {final_var}\n")

def optimize_tac(instructions):
    """
    Example TAC optimization: eliminate dead code.
    
    This is a simple demonstration of how TAC enables optimization.
    A real optimizer would do much more (constant folding, inlining, etc.)
    """
    # Find which temporaries are actually used
    used_temps = set()
    for instr in instructions:
        if instr.arg1 and isinstance(instr.arg1, str) and instr.arg1.startswith('t'):
            used_temps.add(instr.arg1)
        if instr.arg2 and isinstance(instr.arg2, str) and instr.arg2.startswith('t'):
            used_temps.add(instr.arg2)
    
    # Keep the last instruction's result
    if instructions:
        used_temps.add(instructions[-1].result)
    
    # Filter out unused instructions (dead code elimination)
    optimized = []
    for instr in instructions:
        if instr.result in used_temps:
            optimized.append(instr)
            # Mark dependencies as used
            if instr.arg1 and isinstance(instr.arg1, str) and instr.arg1.startswith('t'):
                used_temps.add(instr.arg1)
            if instr.arg2 and isinstance(instr.arg2, str) and instr.arg2.startswith('t'):
                used_temps.add(instr.arg2)
    
    return optimized
