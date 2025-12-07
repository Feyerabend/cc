import unittest
from database import Database
from interpreter import SimpleInterpreter
import os

class TestFunctional(unittest.TestCase):
    
    def setUp(self):
        """Set up the test environment, creating a fresh database and interpreter instance."""
        self.db = Database()
        self.interpreter = SimpleInterpreter(self.db)
        self.input_file = 'input.txt'
        self.output_file = 'output.txt'

    def test_functional(self):
        """Test processing a series of commands from an input file and generating an output file."""
        # Create an example input file with commands
        input_commands = [
            "add user_1 50",
            "increment user_1 10",
            "delete user_1"
        ]
        
        # Write the commands to the input file
        with open(self.input_file, 'w') as f:
            for command in input_commands:
                f.write(f"{command}\n")
        
        # Open the input file and process each command
        output_lines = []
        with open(self.input_file, 'r') as f:
            for line in f:
                command = line.strip()
                output = self.interpreter.execute(command)
                output_lines.append(f"Input: {command}\nOutput: {output}")

        # Write the results to the output file
        with open(self.output_file, 'w') as f:
            for line in output_lines:
                f.write(f"{line}\n")  # Ensure consistent newlines

        # Check the contents of the output file
        with open(self.output_file, 'r') as f:
            result = f.read()

        # Define the expected output format
        expected_output = (
            "Input: add user_1 50\nOutput: Added user_1: 50\n"
            "Input: increment user_1 10\nOutput: Incremented user_1 by 10\n"
            "Input: delete user_1\nOutput: Deleted user_1\n"
        )

        self.assertEqual(result, expected_output)

    def tearDown(self):
        """Clean up by removing the files created during the test."""
        if os.path.exists(self.input_file):
            os.remove(self.input_file)
        if os.path.exists(self.output_file):
            os.remove(self.output_file)

if __name__ == "__main__":
    unittest.main()