from typing import List
from collections import deque
from .token import Token
from .code_unit import CodeUnit
from .tokenized_program import TokenizedProgram


class FlattenCodeUnits:
    @staticmethod
    def __flatten_ast__(ast: Token) -> List[Token]:
        stack = deque()
        stack.extendleft([ast])
        flatten_ast: List[Token] = []
        while stack:
            token = stack.popleft()
            flatten_ast.append(token)
            stack.extendleft(reversed([child for child in token.children]))
        return flatten_ast

    @staticmethod
    def flatten(tokenized_program: TokenizedProgram) -> TokenizedProgram:
        for code_unit in [code_unit for code_unit in tokenized_program.code_units]:
            code_unit.ast = FlattenCodeUnits.__flatten_ast__(code_unit.ast)

        return tokenized_program
