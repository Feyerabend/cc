import unittest
from database import Database
from interpreter import SimpleInterpreter

class TestInterpreter(unittest.TestCase):
    def setUp(self):
        self.db = Database()
        self.interpreter = SimpleInterpreter(self.db)

    def test_add_command(self):
        result = self.interpreter.execute("add key1 123")
        self.assertEqual(result, "Added key1: 123")
        self.assertEqual(self.db.get("key1"), 123)  # Numeric string converted to int

        result = self.interpreter.execute("add key2 hello")
        self.assertEqual(result, "Added key2: hello")
        self.assertEqual(self.db.get("key2"), "hello")  # Non-numeric string stored as-is

    def test_delete_command(self):
        self.db.add("key1", 123)
        result = self.interpreter.execute("delete key1")
        self.assertEqual(result, "Deleted key1")
        self.assertIsNone(self.db.get("key1"))

        result = self.interpreter.execute("delete nonexistent")
        self.assertEqual(result, "Deleted nonexistent")  # Command always confirms deletion, even if key doesn't exist

    def test_increment_command(self):
        self.db.add("key1", 100)
        result = self.interpreter.execute("increment key1 50")
        self.assertEqual(result, "Incremented key1 by 50")
        self.assertEqual(self.db.get("key1"), 150)

        self.db.add("key2", "hello")
        with self.assertRaises(ValueError):  # Incrementing a non-integer value raises an error
            self.interpreter.execute("increment key2 10")

        with self.assertRaises(ValueError):  # Incrementing a non-existent key raises an error
            self.interpreter.execute("increment key3 10")

    def test_invalid_command(self):
        result = self.interpreter.execute("unknown command")
        self.assertEqual(result, "Invalid command")

        result = self.interpreter.execute("addkey1")
        self.assertEqual(result, "Invalid command")  # Invalid command syntax

if __name__ == "__main__":
    unittest.main()
