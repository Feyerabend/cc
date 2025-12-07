class DatabaseProcedures:
    @staticmethod
    def increment_value(db, key, amount):
        # Check if the key exists in the database
        if key not in db.store:
            raise ValueError(f"Key '{key}' does not exist")

        # Get the current value and check if it's an integer
        current_value = db.get(key)

        # If the value is not an integer, raise an error
        if not isinstance(current_value, int):
            raise ValueError(f"Value of key '{key}' is not an integer (found: {type(current_value).__name__})")

        # Perform the increment operation
        db.add(key, current_value + amount)

    @staticmethod
    def bulk_delete(db, prefix):
        keys_to_delete = [key for key in db.store if key.startswith(prefix)]
        for key in keys_to_delete:
            db.delete(key)