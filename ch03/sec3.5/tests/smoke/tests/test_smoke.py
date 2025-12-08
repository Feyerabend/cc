import unittest
from database import Database
from interpreter import SimpleInterpreter

class TestSmoke(unittest.TestCase):
    def test_smoke_basic_operations(self):
        db = Database()
        interpreter = SimpleInterpreter(db)
        
        # Basic add
        result = interpreter.execute("add smoke_key 42")
        self.assertEqual(result, "Added smoke_key: 42")
        self.assertEqual(db.get("smoke_key"), 42)
        
        # Basic increment
        result = interpreter.execute("increment smoke_key 8")
        self.assertEqual(result, "Incremented smoke_key by 8")
        self.assertEqual(db.get("smoke_key"), 50)
        
        # Basic delete
        result = interpreter.execute("delete smoke_key")
        self.assertEqual(result, "Deleted smoke_key")
        self.assertIsNone(db.get("smoke_key"))
        
        # Invalid command (should not crash)
        result = interpreter.execute("invalid")
        self.assertEqual(result, "Invalid command")

if __name__ == "__main__":
    unittest.main()
