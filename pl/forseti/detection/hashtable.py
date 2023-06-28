class Hashtable:
    def __init__(self) -> None:
        self.dict = {}

    def add(self, hash_value, data):
        if hash_value in self.dict:
            values = self.dict[hash_value]
            values.append(data)
            self.dict.setdefault(hash_value, values)
        else:
            self.dict.setdefault(hash_value, [data])

    def get(self, hash_value):
        if hash_value in self.dict:
            return self.dict[hash_value]
        return []

    def clear(self):
        self.dict.clear()

    def create_hash(self, sequence):
        hash_value = 0
        for c in sequence:
            hash_value = (hash_value << 1) + ord(c)
        return hash_value
