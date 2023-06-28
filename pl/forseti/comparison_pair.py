from dataclasses import dataclass, field
from typing import List
from .tokenized_program import TokenizedProgram
from .token import Token


@dataclass
class ComparisonPair:
    program_a: TokenizedProgram
    program_b: TokenizedProgram
    tokens_a: List[Token]
    tokens_b: List[Token]
