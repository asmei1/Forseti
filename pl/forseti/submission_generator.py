import itertools
from typing import List, Tuple
from .tokenized_program import TokenizedProgram
from .submission import Submission 
from .token import Token 
from .code_unit import CodeUnit 


class SubmissionGenerator:
    def __init__(self, compare_whole_programs: bool = True, max_number_of_differences_in_single_submission: int = 15,
                 assign_functions_based_on_types: bool = False) -> None:
        self.__compare_whole_programs__ = compare_whole_programs
        self.__max_number_of_differences_in_single_submission__ = max_number_of_differences_in_single_submission
        self.__assign_functions_based_on_types__ = assign_functions_based_on_types

        if compare_whole_programs and assign_functions_based_on_types:
            raise Exception("Submissions cannot be generated based on their types if you want compare entire programs!")


    def generate(self, programs: List[TokenizedProgram]) -> List[Submission]:
        
        asts: List[Tuple[TokenizedProgram, Token]] = []

        if self.__compare_whole_programs__:
            for program in programs:
                merged_code_units = []
                for code_unit in program.code_units:
                    merged_code_units += code_unit.ast
                asts.append((program, merged_code_units)) 
        else:
            for program in programs:
                for code_unit in program.code_units:
                    asts.append((program, code_unit.ast))


        submissions: List[Submission] = []
        l = list(itertools.combinations(asts, 2))
        for pair in itertools.combinations(asts, 2):
            (program_a, ast_a), (program_b, ast_b) = pair

            if program_a is program_b:
                continue

            if self.__max_number_of_differences_in_single_submission__ != -1 \
                and abs(len(ast_a) - len(ast_b)) > self.__max_number_of_differences_in_single_submission__:
                continue

            if ast_a[0].token_kind != ast_b[0].token_kind: 
                continue

            if self.__assign_functions_based_on_types__:
                if ast_a[0].name != ast_b[0].name:
                    continue
                if ast_a[0].type_name != ast_b[0].type_name: 
                    continue
            
            submissions.append(Submission(program_a, program_b, ast_a, ast_b))


        return submissions