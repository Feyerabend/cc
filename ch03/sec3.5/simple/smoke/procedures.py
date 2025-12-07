
class DatabaseProcedures:
    @staticmethod
    def increment_value(db, key, amount):
        if not db.is_integer(key):
            raise ValueError(
                f"Value of key '{key}' is not an integer (found: {type(db.get(key)).__name__})"
            )
        current_value = db.get(key)
        db.add(key, current_value + amount)

    # new feature!
    @staticmethod
    def bulk_delete(db, prefix):
        keys_to_delete = [key for key in db.store if key.startswith(prefix)]
        for key in keys_to_delete:
            db.delete(key)
