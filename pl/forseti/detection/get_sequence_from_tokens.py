from typing import List
from ..token import Token

def get_sequence_from_tokens(tokens:List[Token]) -> str:
    return ''.join([token.token_kind.short_name for token in tokens])

