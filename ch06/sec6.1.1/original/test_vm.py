import unittest
from vm import VirtualMachine

class TestVirtualMachine(unittest.TestCase):
    def setUp(self):
        self.vm = VirtualMachine()
        self.vm.memory['x'] = 5  # Predefine 'x' in memory

    def test_precondition_check(self):
        # Null hypothesis: 'x' exists in memory
        precondition = lambda vm: 'x' in vm.memory
        self.assertTrue(precondition(self.vm), "Precondition failed: 'x' not in memory")

    def test_postcondition_check(self):
        # Simulate a program that loads 'x' onto the stack
        program = [
            ('LOAD', 'x'),
            ('CHECK_POSTCONDITION', lambda vm: len(vm.stack) > 0),
        ]
        self.vm.execute(program)
        # Postcondition: Stack should not be empty
        self.assertGreater(len(self.vm.stack), 0, "Postcondition failed: Stack is empty")

    def test_append_operation(self):
        # Test appending an item to a list in VM
        program = [
            ('PUSH', 5),  # Push value to append
            ('PUSH_LIST',),  # Push a new list
            ('APPEND',),  # Append the value to the list
        ]
        self.vm.execute(program)
        self.assertEqual(self.vm.stack[-1], [5], "Failed to append to the list")

    def test_full_program_execution(self):
        # Define the full program with preconditions and postconditions
        program = [
            ('CHECK_PRECONDITION', lambda vm: 'x' in vm.memory),   # ensure 'x' is defined
            ('LOAD', 'x'),                                         # load variable 'x'
            ('CHECK_POSTCONDITION', lambda vm: len(vm.stack) > 0), # ensure stack isn't empty
            ('PUSH_LIST',),                                        # push a new list to the stack
            ('APPEND',),                                           # append 'x' to the list
            ('STORE', 'lst'),                                      # store the list in 'lst'
            ('CHECK_PRECONDITION', lambda vm: 'lst' in vm.memory), # ensure 'lst' exists
            ('LOAD', 'x'),                                         # load 'x'
            ('LOAD', 'lst'),                                       # load 'lst'
            ('PUSH', 0),                                           # push index for list access
            ('INDEX',),                                            # get 'lst[0]'
            ('CHECK_POSTCONDITION', lambda vm: isinstance(vm.stack[-1], int)), # ensure top is an int
            ('ADD',),                                              # add 'x' and 'lst[0]'
            ('HALT',),                                             # halt the program
        ]
        self.vm.execute(program)
        # Final assertion for the program's expected outcome
        self.assertEqual(self.vm.stack[-1], 10, "Program result is incorrect")

if __name__ == '__main__':
    unittest.main()
