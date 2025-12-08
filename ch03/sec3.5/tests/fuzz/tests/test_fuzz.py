import unittest
import random
import string
from interpreter import SimpleInterpreter
from database import Database

class TestFuzz(unittest.TestCase):
    def test_fuzz_commands(self):
        db = Database()
        interpreter = SimpleInterpreter(db)
        
        for _ in range(10000):  # Run many iterations
            # Generate random command
            cmd_type = random.choice(["add", "delete", "increment", "invalid"])
            key = ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(1, 20)))
            value = random.choice([str(random.randint(0, 1000)), ''.join(random.choices(string.printable, k=10))])
            
            if cmd_type == "add":
                command = f"add {key} {value}"
            elif cmd_type == "delete":
                command = f"delete {key}"
            elif cmd_type == "increment":
                command = f"increment {key} {random.randint(1, 100)}"
            else:
                command = ''.join(random.choices(string.printable, k=random.randint(5, 50)))
            
            try:
                result = interpreter.execute(command)
                # No assertion; just ensure no crash
            except ValueError:
                pass  # Expected for invalid cases

if __name__ == "__main__":
    unittest.main()
