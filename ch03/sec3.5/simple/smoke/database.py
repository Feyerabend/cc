class Database:
    def __init__(self):
        self.store = {}

    def add(self, key, value):
        # Convert numeric strings to integers
        if isinstance(value, str) and value.isdigit():
            value = int(value)
        self.store[key] = value

    def delete(self, key):
        if key in self.store:
            del self.store[key]

    def get(self, key):
        return self.store.get(key)

    def is_integer(self, key):
        value = self.get(key)
        return isinstance(value, int)
