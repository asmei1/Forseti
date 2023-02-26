import logging
from copy import deepcopy
from typing import List, Tuple, Set
from collections import deque
from .tokenized_program import TokenizedProgram
from .code_unit import CodeUnit
from .token import Token, TokenKind, VariableTokenKind

class UnrollCodeUnits:
    @staticmethod
    def __get_function_call_parent__(token: Token) -> Tuple[int, Token]:
        current_token = token
        previous_token = token
        while True:
            if current_token.token_kind != TokenKind.FunctionCall:
                if current_token.token_kind not in [TokenKind.VariableDecl, TokenKind.BinaryOp]:
                    return (current_token.children.index(previous_token), current_token)
            if not current_token.parent_token:
                return (len(current_token.children)-1, current_token)

            previous_token = current_token
            current_token = current_token.parent_token

    @staticmethod
    def __get_parent__(token: Token) -> Token:
        current_token = token
        while True:
            if not current_token.parent_token:
                return current_token
            current_token = current_token.parent_token

    @staticmethod
    def __is_simple_function__(root_token: Token) -> bool:
        stack = deque()
        stack.extendleft(root_token.children)
        while stack:
            token = stack.popleft()
            if token.token_kind == TokenKind.FunctionCall:
                return False
            stack.extendleft(reversed(token.children))
        return True


    @staticmethod
    def __get_function_calls__(all_asts: List[List[Token]]) -> List[Token]:
        function_call_tokens: List[Token] = []
        for ast in all_asts:
            stack = deque()
            stack.extendleft([ast])
            while stack:
                token = stack.popleft()
                if token.token_kind == TokenKind.FunctionCall:
                    function_call_tokens.append(token)
                stack.extendleft(reversed(token.children))
        return function_call_tokens
    
    @staticmethod
    def unroll(tokenized_program: TokenizedProgram,  remove_unrolled_functions: bool = True, unroll_only_simple_functions = True,
                max_unrolls_tries: int = 10) -> TokenizedProgram:
        all_asts = [code_unit.ast for code_unit in tokenized_program.code_units]
        candidate_asts: List[Token] = [] 
        if unroll_only_simple_functions:
            candidate_asts = [ast for ast in all_asts if UnrollCodeUnits.__is_simple_function__(ast)]
        else:
            candidate_asts = all_asts
        
        previous_function_call_tokens: List[Token] = []
        to_remove: Set[int] = set() 
        
        # -------------------------------------------------
        # TODO: Think about detecting non trivial recurence
        # -------------------------------------------------
        for _ in range(max_unrolls_tries):
            function_call_tokens: List[Token] = UnrollCodeUnits.__get_function_calls__(all_asts)
            
            if previous_function_call_tokens == function_call_tokens:
                break

            previous_function_call_tokens = function_call_tokens

            unrolled_tokens: List[Tuple[Token, Token]] = []
            for function_call_token in reversed(function_call_tokens):
                root_token = UnrollCodeUnits.__get_parent__(function_call_token)
                for candidate_function_token in candidate_asts:

                    candidate_function_name = candidate_function_token.name.split('(', 1)[0]

                    if candidate_function_name == function_call_token.name:
                        if root_token.name == candidate_function_token.name and root_token.type_name == candidate_function_token.type_name:
                            logging.debug("Recursive unrolling is not supported now!")
                            continue
                        if function_call_token.children[0].type_name == candidate_function_token.type_name:
                            unrolled_tokens.append((function_call_token, candidate_function_token))

            for function_token, replacement in unrolled_tokens:
                to_remove.add(all_asts.index(replacement))
                parent = function_token.parent_token
                copied_tokens = []
                # Copy tokens from function body
                for token_to_copy in replacement.children:
                    if token_to_copy.token_kind != TokenKind.ParameterDecl:
                        if token_to_copy.token_kind == TokenKind.Return:
                            if token_to_copy.children:
                                result_token: Token = None
                                if parent.token_kind == TokenKind.VariableDecl:
                                    result_token = deepcopy(parent)
                                    result_token.name = "="
                                    result_token.token_kind = TokenKind.BinaryOp
                                    result_token.parent_token = parent.parent_token
                                    
                                    decl_ref_token = deepcopy(parent)
                                    decl_ref_token.parent_token = result_token
                                    decl_ref_token.children = []
                                    decl_ref_token.token_kind = TokenKind.DeclRefExpr
                                    
                                    result_token.children = [decl_ref_token]

                                else:
                                    # Create artificial token to "store" function result 
                                    result_token = Token("forseti_function_call_result")
                                    result_token.type_name = token_to_copy.children[0].type_name
                                    result_token.token_kind = TokenKind.VariableDecl
                                    result_token.variable_token_kind = token_to_copy.children[0].variable_token_kind
                                    result_token.location = parent.location
                                    result_token.parent_token = parent


                                copied_tokens.append(result_token)

                                for return_sub_token in token_to_copy.children:
                                    copied_token = deepcopy(return_sub_token)
                                    copied_token.parent_token = result_token
                                    result_token.children.append(copied_token)
                                    # copied_tokens.append(copied_token)
                        else:
                            copied_token = deepcopy(token_to_copy)
                            copied_token.parent_token = parent
                            copied_tokens.append(copied_token)

                # Replace call token with copied tokens  
                index = parent.children.index(function_token)
                parent.children.remove(function_token)

                # If call token is used as input parameters to other function,
                # place replacement above.
                if parent.token_kind in [TokenKind.BinaryOp, TokenKind.FunctionCall, TokenKind.VariableDecl]:
                    position, parent_outside_of_expression = UnrollCodeUnits.__get_function_call_parent__(parent)
                    for token in copied_tokens:
                        token.parent_token = parent_outside_of_expression

                    if parent.token_kind is TokenKind.VariableDecl:
                        parent_outside_of_expression.children[position:position] = copied_tokens[:-1]
                        position = position + len(copied_tokens)
                        parent_outside_of_expression.children.insert(position, copied_tokens[-1])
                    else:
                        parent_outside_of_expression.children[position:position] = copied_tokens
                else:
                # Replace call token with copied tokens  
                    parent.children[index:index] = copied_tokens

        if remove_unrolled_functions:
            for index in sorted(to_remove, reverse=True):
                candidate_asts.pop(index)
                
        if unroll_only_simple_functions:
            for ast in all_asts:
                if ast not in candidate_asts:
                    candidate_asts.append(ast)


        unrolled_program = tokenized_program
        unrolled_program.code_units = [CodeUnit(ast) for ast in candidate_asts]
        return unrolled_program




