class Database:
    def __init__(self):
        self.store = {}

    def add(self, key, value):
        # Convert numeric strings to integers (including negative numbers)
        if isinstance(value, str):
            try:
                # Only convert if the string has no leading/trailing whitespace
                # and doesn't contain decimal points, scientific notation, or plus signs
                if (value == value.strip() and  # No leading/trailing whitespace
                    value.strip() and  # Not empty after stripping
                    not ('.' in value or 'e' in value.lower() or '+' in value)):
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