from typing import List, Optional


class TilesManager:
    def __init__(self, tokens: List, token_to_str) -> None:
        self.tokens = [token_to_str(token) for token in tokens]
        self.marks = [False] * len(self.tokens)
        self.size = len(self.tokens)

    def get_index_of_next_marked_token(self, index: int) -> Optional[int]:
        for i in range(index, len(self.marks)):
            if self.marks[i]:
                return i
        return None

    def get_index_of_next_unmarked_token(self, index: int) -> Optional[int]:
        for i in range(index, len(self.marks)):
            if not self.marks[i]:
                return i

        return None
