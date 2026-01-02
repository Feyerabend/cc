# ir_lowering.py

from typing import List
from cat_free import Free, Pure, Impure
from ir import IRInstr, IRProgram


def lower_free(program: Free) -> IRProgram:
    """
    Lower a Free program into a linear IR.
    """

    instructions: List[IRInstr] = []

    def walk(node: Free):
        if isinstance(node, Pure):
            return

        if isinstance(node, Impure):
            instructions.append(IRInstr(node.functor))

            # advance structurally, NOT by interpretation
            next_node = node.functor.run_step(None)
            walk(next_node)
            return

        raise TypeError(f"Unknown Free node: {node}")

    walk(program)
    return IRProgram(instructions)
