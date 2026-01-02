# ir.py

from dataclasses import dataclass
from typing import List
from cat_free import FunctorF


@dataclass
class IRInstr:
    op: FunctorF


@dataclass
class IRProgram:
    instructions: List[IRInstr]
