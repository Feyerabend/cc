import unittest
from main import some_function

class TestMain(unittest.TestCase):
    def test_some_function(self):
        self.assertEqual(some_function(2, 3), 5)

if __name__ == '__main__':
    unittest.main()
