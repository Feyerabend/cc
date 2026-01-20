
def validate_bytecode(bytecode):

    valid_instructions = {
        'SET', 'LOAD', 'STORE',
        'ADD', 'SUB', 'MUL', 'DIV', 'AND', 'OR',
        'LOGICAL_AND', 'LOGICAL_OR', 
        'GEQ', 'LEQ', 'LT', 'GT', 'EQ', 'NEQ',
        'SWAP', 'DUP', 'NEG', 'POP', 'JP', 'JZ',
        'PRINT', 'NOP', 'RET', 'CALL', 'CAT', 'CONS', 'CAR', 'CDR', 'LIST', 'LEN',
        'FLAT', 'NTH', 'IDX', 'HALT'
    }

    for pc, instr in enumerate(bytecode):
        if isinstance(instr, str):  # If the instruction is a string
            if instr not in valid_instructions:  # Only flag strings that are not valid instructions
                # Allow function names or labels (like 'outer') as valid
                if not instr.isidentifier():  # Check if it's a valid function/label identifier
                    raise ValueError(f"Unknown instruction: {instr} at position {pc}")
        elif isinstance(instr, list):  # Allow lists as valid operands
            continue
        elif isinstance(instr, int):  # Handle the case for numeric constants
            continue
        else:
            raise ValueError(f"Invalid bytecode format: {instr} at position {pc}")
