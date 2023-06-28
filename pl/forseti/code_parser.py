from abc import ABC, abstractmethod
from .program import Program
from .tokenized_program import TokenizedProgram


class CodeParser(ABC):
    @abstractmethod
    def parse(self, program: Program) -> TokenizedProgram:
        pass
