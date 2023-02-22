
from typing import List
from .program import Program
from .tokenized_program import TokenizedProgram
from .code_parser import CodeParser


class CodeTokenizer:
    def __init__(self, code_parser: CodeParser) -> None:
        self.code_parser = code_parser

    def parse_programs(self, programs_sets: List[Program]) -> List[TokenizedProgram]:
        return [self.code_parser.parse(program) for program in programs_sets]

        