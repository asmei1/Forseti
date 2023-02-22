from typing import List
from .tokenized_program import TokenizedProgram

class DetectionEngine:
    def __init__(self) -> None:
        pass

    def analyze(self, tokenized_programs: List[TokenizedProgram]):
        for tokenized_program in tokenized_programs:
            # stack = [(0, code_unit.ast) for code_unit in tokenized_program.code_units]
            stack = [(0, tokenized_program.code_units[0].ast)]
            
            while stack:
                level, token = stack.pop()
                print(level * "--", token.name, token.type_name, token.token_kind.name, token.variable_token_kind.short_name, token.location[1], token.location[2], token.location[0])
                stack.extend([level+1, child] for child in token.children)

        

        print("analyzing")

        