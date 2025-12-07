import unittest
from database import Database
from procedures import DatabaseProcedures

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db = Database()

    def test_add_and_get(self):
        self.db.add("key1", "123")
        self.assertEqual(self.db.get("key1"), 123)  # Numeric string converted to int
        self.db.add("key2", "hello")
        self.assertEqual(self.db.get("key2"), "hello")  # Non-numeric string stored as-is
        self.db.add("key3", 456)
        self.assertEqual(self.db.get("key3"), 456)  # Integer stored directly

    def test_delete(self):
        self.db.add("key1", 123)
        self.db.delete("key1")
        self.assertIsNone(self.db.get("key1"))  # Ensure key is deleted
        self.db.delete("nonexistent")  # No error when deleting a non-existent key

    def test_is_integer(self):
        self.db.add("key1", "123")
        self.assertTrue(self.db.is_integer("key1"))
        self.db.add("key2", "hello")
        self.assertFalse(self.db.is_integer("key2"))
        self.db.add("key3", 456)
        self.assertTrue(self.db.is_integer("key3"))
        self.assertFalse(self.db.is_integer("nonexistent"))  # Key does not exist

    def test_increment_value(self):
        self.db.add("key1", 100)
        DatabaseProcedures.increment_value(self.db, "key1", 50)
        self.assertEqual(self.db.get("key1"), 150)

        self.db.add("key2", "hello")
        with self.assertRaises(ValueError):
            DatabaseProcedures.increment_value(self.db, "key2", 10)  # Cannot increment non-integer value

        with self.assertRaises(ValueError):
            DatabaseProcedures.increment_value(self.db, "nonexistent", 10)  # Non-existent key

    def test_bulk_delete(self):
        self.db.add("user1", "data1")
        self.db.add("user2", "data2")
        self.db.add("admin1", "data3")
        DatabaseProcedures.bulk_delete(self.db, "user")
        self.assertIsNone(self.db.get("user1"))
        self.assertIsNone(self.db.get("user2"))
        self.assertIsNotNone(self.db.get("admin1"))  # Other keys remain

if __name__ == "__main__":
    unittest.main()