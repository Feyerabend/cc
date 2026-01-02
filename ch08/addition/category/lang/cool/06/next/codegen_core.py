# codegen_core.py

from abc import ABC, abstractmethod
from ir import IRInstr


class CodeAlgebra(ABC):
    """
    Algebra over IR instructions.
    """

    @abstractmethod
    def begin(self):
        pass

    @abstractmethod
    def emit(self, instr: IRInstr):
        pass

    @abstractmethod
    def end(self):
        pass
