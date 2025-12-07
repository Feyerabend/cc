class Database:
    def __init__(self):
        self.store = {}

    def add(self, key, value):
        # Try to fix common issues with numeric strings
        # Convert numeric strings to integers (including negative numbers)
        if isinstance(value, str):
            try:
                # Try to convert to int - this handles positive, negative, and zero
                if value.strip() and not ('.' in value or 'e' in value.lower() or '+' in value):
                    value = int(value)
            except ValueError:
                # If conversion fails, keep as string
                pass
        self.store[key] = value

    def delete(self, key):
        if key in self.store:
            del self.store[key]

    def get(self, key):
        return self.store.get(key)

    def is_integer(self, key):
        value = self.get(key)
        return isinstance(value, int)