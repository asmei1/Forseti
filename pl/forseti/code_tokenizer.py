import copy
from typing import List
from .program import Program
from .tokenized_program import TokenizedProgram
from .code_parser import CodeParser
from .utils.multiprocessing import execute_function_in_multiprocesses


class CodeTokenizer:
    def __init__(self, code_parser: CodeParser, n_processors: int = -1) -> None:
        self.code_parser = code_parser
        self.__n_processors = n_processors

    @staticmethod
    def multiprocessing_parsing(code_parser_and_program):
        code_parser, program = code_parser_and_program
        return code_parser.parse(program)

    def parse_programs(self, programs_sets: List[Program]) -> List[TokenizedProgram]:
        if self.__n_processors == 1:
            programs = [self.code_parser.parse(program) for program in programs_sets]
        else:
            parsers = [copy.deepcopy(self.code_parser) for _ in range(len(programs_sets))]
            programs = execute_function_in_multiprocesses(CodeTokenizer.multiprocessing_parsing, zip(parsers, programs_sets), self.__n_processors)

        filtered_programs = []
        for p in programs:
            if len(p.code_units) > 0:
                filtered_programs.append(p)

        return filtered_programs
