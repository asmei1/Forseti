from typing import List


class Node:
    def __init__(self, maximal_match_length: int, data=None, next_node=None, previous_node=None) -> None:
        self._maximal_match_length = maximal_match_length
        self.previous_node: "Node" = previous_node
        self.next_node: "Node" = next_node

        if not data:
            self._data = []
        elif type(data) == list:
            self._data = data
        elif type(data) != list:
            self._data = [data]

    @property
    def maximal_match_length(self) -> int:
        return self._maximal_match_length

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, new_data):
        if type(new_data) == list:
            self._data += new_data
        elif type(new_data) != list:
            self._data.append(new_data)


class LinkedList:
    def __init__(self, root: "Node" = None) -> None:
        self._root = root
        self._size = 0
        self._current_maximal_match_length = None
        self._maximal_match_lengths: List[int] = []

    @property
    def size(self):
        return self._size

    @property
    def maximal_matches(self):
        return self._maximal_match_lengths

    def remove(self, maximal_match_length: int) -> True:
        node: Node = self._root
        while node:
            if node.maximal_match_length == maximal_match_length:
                next_node = node.next_node
                previous_node = node.previous_node

                if next_node:
                    next_node.previous_node = previous_node
                if previous_node:
                    previous_node.next_node = next_node
                else:
                    self._root = node

                self._size -= 1
                self._current_maximal_match_length = node.maximal_match_length

                return True
            else:
                node = node.next_node
        return False

    def find(self, maximal_match_length: int) -> "Node":
        node: Node = self._root
        while node:
            if node.maximal_match_length == maximal_match_length:
                return node
            else:
                if node.maximal_match_length > maximal_match_length:
                    node = node.next_node
                else:
                    node = node.previous_node

        return None

    def add(self, maximal_match_length: int, data):
        if not self._root:
            self._root = Node(maximal_match_length, data)
            self._size += 1
            self._current_maximal_match_length = maximal_match_length
            self._maximal_match_lengths.append(maximal_match_length)
            return maximal_match_length

        node: Node = self._root
        while node:
            if node.maximal_match_length == maximal_match_length:
                node.data = data
                self._root = node
                self._current_maximal_match_length = maximal_match_length
                return maximal_match_length

            elif node.maximal_match_length > maximal_match_length:
                current_node: Node = node
                next_node: Node = node.next_node
                node = next_node
                if next_node:
                    if maximal_match_length > next_node.maximal_match_length:
                        new_node = Node(maximal_match_length, data, next_node=next_node, previous_node=current_node)
                        current_node.next_node = new_node
                        next_node.previous_node = new_node

                        self._size += 1
                        self._root = new_node
                        self._current_maximal_match_length = maximal_match_length
                        self._maximal_match_lengths.append(maximal_match_length)
                        return maximal_match_length
                    else:
                        node = next_node

                else:
                    new_node = Node(maximal_match_length, data, next_node=None, previous_node=current_node)
                    current_node.next_node = new_node

                    self._size += 1
                    self._root = new_node
                    self._current_maximal_match_length = maximal_match_length
                    self._maximal_match_lengths.append(maximal_match_length)
                    return maximal_match_length
            elif node.maximal_match_length < maximal_match_length:
                current_node: Node = node
                previous_node: Node = node.previous_node
                node = previous_node
                if previous_node:
                    if previous_node.maximal_match_length > maximal_match_length:
                        new_node = Node(maximal_match_length, data, next_node=current_node, previous_node=previous_node)
                        current_node.previous_node = new_node
                        previous_node.next_node = new_node

                        self._size += 1
                        self._root = new_node
                        self._current_maximal_match_length = maximal_match_length
                        self._maximal_match_lengths.append(maximal_match_length)
                        return maximal_match_length
                    else:
                        node = previous_node
                else:
                    new_node = Node(maximal_match_length, data, next_node=current_node, previous_node=None)
                    current_node.previous_node = new_node

                    self._size += 1
                    self._root = new_node
                    self._current_maximal_match_length = maximal_match_length
                    self._maximal_match_lengths.append(maximal_match_length)
                    return maximal_match_length

        raise RuntimeError("This should not happen! Check your (my?) code, because it seems like it have a bug.")

    def set_root(self, root: "Node"):
        node = self._root
        while node:
            if node.maximal_match_length == root.maximal_match_length:
                self._root = node
                return self._root.maximal_match_length
            else:
                node = node.next_node()
        raise RuntimeError("This should not happen! Check your (my?) code, because it seems like it have a bug.")
