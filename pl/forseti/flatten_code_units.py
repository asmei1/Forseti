from typing import List
from .tokenized_program import TokenizedProgram


class FlattenCodeUnits:
    @staticmethod
    def __preorder__(ast):
        tokens = []
        for token in ast.walk_preorder():
            tokens.append(token)
        return tokens

    @staticmethod
    def flatten(tokenized_program: TokenizedProgram) -> TokenizedProgram:
        for code_unit in [code_unit for code_unit in tokenized_program.code_units]:
            code_unit.ast = FlattenCodeUnits.__preorder__(code_unit.ast)

        return tokenized_program
