import itertools
from typing import List, Tuple
from .tokenized_program import TokenizedProgram
from .comparison_pair import ComparisonPair 
from .token import Token 


class ComparisonPairsGenerator:
    def __init__(self, compare_whole_programs: bool, max_number_of_differences_in_single_comparison_pair: int,
                 assign_functions_based_on_types: bool) -> None:
        self.__compare_whole_programs__ = compare_whole_programs
        self.__max_number_of_differences_in_single_comparison_pair__ = max_number_of_differences_in_single_comparison_pair
        self.__assign_functions_based_on_types__ = assign_functions_based_on_types

        if compare_whole_programs and assign_functions_based_on_types:
            raise Exception("Comparison pairs cannot be generated based on their types if you want compare entire programs!")


    def generate(self, programs: List[TokenizedProgram], selected_programs_to_compare: List[str]) -> List[ComparisonPair]:
        
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


        comparison_pairs: List[ComparisonPair] = []
        for pair in itertools.combinations(asts, 2):
            (program_a, ast_a), (program_b, ast_b) = pair

            if selected_programs_to_compare:
                if not (program_a.author in selected_programs_to_compare or program_b.author in selected_programs_to_compare):
                    continue
                
            if program_a is program_b:
                continue

            if self.__max_number_of_differences_in_single_comparison_pair__ != -1 \
                and abs(len(ast_a) - len(ast_b)) > self.__max_number_of_differences_in_single_comparison_pair__:
                continue

            if ast_a[0].token_kind != ast_b[0].token_kind: 
                continue

            if self.__assign_functions_based_on_types__:
                if ast_a[0].name != ast_b[0].name:
                    continue
                if ast_a[0].type_name != ast_b[0].type_name: 
                    continue
            
            comparison_pairs.append(ComparisonPair(program_a, program_b, ast_a, ast_b))


        return comparison_pairs