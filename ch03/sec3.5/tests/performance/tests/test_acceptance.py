#import unittest
#from database import Database
#from procedures import DatabaseProcedures
#from interpreter import SimpleInterpreter
#import os

import unittest
from database import Database
from interpreter import SimpleInterpreter

class TestAcceptance(unittest.TestCase):
    def setUp(self):
        """Set up a fresh database and interpreter for each test."""
        self.db = Database()
        self.interpreter = SimpleInterpreter(self.db)

    def test_scenario_user_adds_and_updates_records(self):
        """Scenario: A user adds, increments, and deletes records."""
        # Step 1: Add a new record
        result = self.interpreter.execute("add user1 100")
        self.assertEqual(result, "Added user1: 100")

        # Step 2: Increment the record
        result = self.interpreter.execute("increment user1 50")
        self.assertEqual(result, "Incremented user1 by 50")
        self.assertEqual(self.db.get("user1"), 150)

        # Step 3: Delete the record
        result = self.interpreter.execute("delete user1")
        self.assertEqual(result, "Deleted user1")
        self.assertIsNone(self.db.get("user1"))

    def test_scenario_user_cannot_increment_non_numeric_value(self):
        """Scenario: A user tries to increment a non-numeric value."""
        # Step 1: Add a non-numeric value
        self.interpreter.execute("add user2 Hello")

        # Step 2: Attempt to increment the value
        with self.assertRaises(ValueError) as context:
            self.interpreter.execute("increment user2 10")

        # Verify the error message
        self.assertEqual(str(context.exception), "Value of key 'user2' is not an integer")

    def test_scenario_bulk_deletion(self):
        """Scenario: A user deletes all keys with a specific prefix."""
        # Add multiple keys with and without a prefix
        self.interpreter.execute("add prefix_key1 10")
        self.interpreter.execute("add prefix_key2 20")
        self.interpreter.execute("add other_key 30")

        # Perform bulk delete operation
        from procedures import DatabaseProcedures
        DatabaseProcedures.bulk_delete(self.db, "prefix")

        # Verify that only the prefixed keys are deleted
        self.assertIsNone(self.db.get("prefix_key1"))
        self.assertIsNone(self.db.get("prefix_key2"))
        self.assertEqual(self.db.get("other_key"), 30)

if __name__ == "__main__":
    unittest.main()