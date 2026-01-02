# codegen_state.py

from dataclasses import dataclass, field
from typing import List


@dataclass
class CodeState:
    declarations: List[str] = field(default_factory=list)
    statements: List[str] = field(default_factory=list)

    def dump(self) -> str:
        return "\n".join(self.declarations + self.statements)
