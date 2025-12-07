import unittest
from database import Database
from interpreter import SimpleInterpreter
from procedures import DatabaseProcedures

class TestRegression(unittest.TestCase):
    def setUp(self):
        self.db = Database()
        self.interpreter = SimpleInterpreter(self.db)

    def test_regression_add_and_increment(self):
        # Regression for basic add and increment (from test_interpreter.py and test_database.py)
        self.interpreter.execute("add reg_key 100")
        self.assertEqual(self.db.get("reg_key"), 100)
        self.interpreter.execute("increment reg_key 20")
        self.assertEqual(self.db.get("reg_key"), 120)

    def test_regression_delete_non_existent(self):
        # Regression for delete behavior on missing keys (from test_integrate.py)
        result = self.interpreter.execute("delete missing_key")
        self.assertEqual(result, "Deleted missing_key")
        self.assertIsNone(self.db.get("missing_key"))

    def test_regression_bulk_delete(self):
        # Regression for bulk delete (from test_database.py)
        self.db.add("reg_prefix1", 10)
        self.db.add("reg_prefix2", 20)
        self.db.add("other_key", 30)
        DatabaseProcedures.bulk_delete(self.db, "reg_prefix")
        self.assertIsNone(self.db.get("reg_prefix1"))
        self.assertIsNone(self.db.get("reg_prefix2"))
        self.assertEqual(self.db.get("other_key"), 30)

    def test_regression_increment_non_integer(self):
        # Regression for error on non-integer increment (from test_integrate.py)
        self.db.add("reg_string", "hello")
        with self.assertRaises(ValueError):
            DatabaseProcedures.increment_value(self.db, "reg_string", 5)

if __name__ == "__main__":
    unittest.main()
