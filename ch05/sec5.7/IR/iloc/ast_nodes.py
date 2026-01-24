from dataclasses import dataclass
from typing import Any, List
from enum import Enum

class NodeType(Enum):
    NUMBER = "NUMBER"
    VARIABLE = "VARIABLE"
    BINOP = "BINOP"
    ASSIGN = "ASSIGN"
    PROGRAM = "PROGRAM"

@dataclass
class ASTNode:
    node_type: NodeType
    value: Any = None
    left: 'ASTNode' = None
    right: 'ASTNode' = None
    children: List['ASTNode'] = None
