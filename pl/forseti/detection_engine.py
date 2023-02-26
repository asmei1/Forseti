from typing import List
from collections import deque
from .tokenized_program import TokenizedProgram
from .flatten_code_units import FlattenCodeUnits
from .unroll_code_units import UnrollCodeUnits

class DetectionEngine:
    def __init__(self) -> None:
        pass

    def analyze(self, tokenized_programs: List[TokenizedProgram]):
        for tokenized_program in tokenized_programs:
            unrolled_program = UnrollCodeUnits.unroll(tokenized_program, False)
            # flatten_program = FlattenCodeUnits.flatten(tokenized_program)
            # debug = 0
            # stack = [(0, code_unit.ast) for code_unit in tokenized_program.code_units]
            for code_unit in unrolled_program.code_units:
                print("======================================================================") 
                stack = deque()
                stack.extendleft([(0, code_unit.ast)])
                
                while stack:
                    level, token = stack.popleft()
                    print(level * "--", token.name, token.type_name, token.token_kind.name, token.variable_token_kind.short_name, token.location[1], token.location[2], token.location[0])
                    stack.extendleft(reversed([[level+1, child] for child in token.children]))

        

        print("analyzing")

        