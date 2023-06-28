from typing import List, Optional


class TilesManager:
    def __init__(self, tokens: List) -> None:
        self._tokens = tokens
        self._marks = [False] * len(self._tokens)
        self._size = len(self._tokens)

    def set_mark(self, index: int, mark: bool):
        self._marks[index] = mark

    def is_marked(self, index: int) -> bool:
        return self._marks[index]

    def get_index_of_next_marked_token(self, index: int) -> Optional[int]:
        for i in range(index, len(self._marks)):
            if self.is_marked(i):
                return i
        return None

    def get_index_of_next_unmarked_token(self, index: int) -> Optional[int]:
        for i in range(index, len(self._marks)):
            if not self.is_marked(i):
                return i

        return None

    def size(self):
        return self._size

    @property
    def tokens(self):
        return self._tokens

    @property
    def marks(self):
        return self._marks
