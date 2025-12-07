import unittest
from database import Database
from interpreter import SimpleInterpreter
from procedures import DatabaseProcedures

class TestIntegration(unittest.TestCase):

    def setUp(self):
        """Set up the test environment, creating a fresh database and interpreter instance."""
        self.db = Database()
        self.interpreter = SimpleInterpreter(self.db)

    def test_add_key(self):
        """Test adding a key and checking if it's properly inserted into the database."""
        result = self.interpreter.execute("add user_1 50")
        self.assertEqual(result, "Added user_1: 50")
        self.assertEqual(self.db.get("user_1"), 50)

    def test_increment_key(self):
        """Test incrementing an existing key in the database."""
        # First add the key
        self.db.add("user_2", 100)
        result = self.interpreter.execute("increment user_2 10")
        self.assertEqual(result, "Incremented user_2 by 10")
        self.assertEqual(self.db.get("user_2"), 110)

    def test_increment_command(self):
        """Test that incrementing a non-integer key raises a ValueError."""
        self.db.add("user_3", "some_string")  # Add a non-integer value
        with self.assertRaises(ValueError):  # Expect a ValueError to be raised
            self.interpreter.execute("increment user_3 10")

    def test_increment_non_integer_key(self):
        """Test incrementing a key with a non-integer value raises a ValueError."""
        self.db.add("user_3", "not_a_number")  # Add a string value to the database
        with self.assertRaises(ValueError) as context:
            self.interpreter.execute("increment user_3 10")
        self.assertEqual(str(context.exception), "Value of key 'user_3' is not an integer")

    def test_increment_non_existent_key(self):
        """Test incrementing a non-existent key raises a ValueError."""
        with self.assertRaises(ValueError) as context:
            self.interpreter.execute("increment non_existent_key 10")
        self.assertEqual(str(context.exception), "Key 'non_existent_key' does not exist")

    def test_delete_key(self):
        """Test deleting an existing key."""
        self.db.add("user_4", 200)
        result = self.interpreter.execute("delete user_4")
        self.assertEqual(result, "Deleted user_4")
        self.assertIsNone(self.db.get("user_4"))

    def test_delete_non_existent_key(self):
        """Test deleting a non-existent key should result in a successful 'no-op'."""
        result = self.interpreter.execute("delete non_existent_key")
        self.assertEqual(result, "Deleted non_existent_key")  # A successful no-op response
        self.assertIsNone(self.db.get("non_existent_key"))

    def test_add_with_non_integer_value(self):
        """Test adding a key with a non-integer value."""
        result = self.interpreter.execute("add user_5 some_string")
        self.assertEqual(result, "Added user_5: some_string")
        self.assertEqual(self.db.get("user_5"), "some_string")

    def test_bulk_delete(self):
        """Test the bulk delete feature with a prefix."""
        self.db.add("user_6_1", 500)
        self.db.add("user_6_2", 600)
        self.db.add("user_6_3", 700)

        # Call the bulk delete procedure
        DatabaseProcedures.bulk_delete(self.db, "user_6")
        
        # Check if all keys with prefix "user_6" are deleted
        self.assertIsNone(self.db.get("user_6_1"))
        self.assertIsNone(self.db.get("user_6_2"))
        self.assertIsNone(self.db.get("user_6_3"))

    def test_invalid_command(self):
        """Test invalid commands to ensure the interpreter responds correctly."""
        result = self.interpreter.execute("unknown_command user_7")
        self.assertEqual(result, "Invalid command")

    def test_add_with_numeric_string(self):
        """Test adding a key with a numeric string should be converted to integer."""
        result = self.interpreter.execute("add user_8 123")
        self.assertEqual(result, "Added user_8: 123")
        self.assertEqual(self.db.get("user_8"), 123)

    def tearDown(self):
        """Clean up after each test to ensure no leftover state."""
        del self.db
        del self.interpreter

if __name__ == "__main__":
    unittest.main()