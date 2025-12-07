import unittest
import time
from database import Database
from procedures import DatabaseProcedures

class TestPerformance(unittest.TestCase):
    def setUp(self):
        self.db = Database()

    def test_perf_add_many_keys(self):
        start_time = time.time()
        for i in range(10000):
            self.db.add(f"perf_key_{i}", i)
        end_time = time.time()
        self.assertLess(end_time - start_time, 0.1)  # Expect under 100ms; adjust based on your machine

    def test_perf_bulk_delete_many(self):
        # Populate with many keys
        for i in range(10000):
            self.db.add(f"perf_prefix_{i}", i)
        for i in range(5000):
            self.db.add(f"other_{i}", i)
        
        start_time = time.time()
        DatabaseProcedures.bulk_delete(self.db, "perf_prefix")
        end_time = time.time()
        self.assertLess(end_time - start_time, 0.05)  # Expect quick scan and delete
        
        # Verify
        self.assertIsNone(self.db.get("perf_prefix_0"))
        self.assertEqual(self.db.get("other_0"), 0)

if __name__ == "__main__":
    unittest.main()
