import unittest
import tempfile
import os
import json
import time
from unittest.mock import Mock, patch, MagicMock
from database import Database
from interpreter import SimpleInterpreter
from procedures import DatabaseProcedures

class TestDatabaseAdvanced(unittest.TestCase):
    """Advanced database tests with edge cases and performance considerations"""
    
    def setUp(self):
        self.db = Database()

    def test_add_edge_cases(self):
        """Test edge cases for adding values"""
        # Test empty string
        self.db.add("empty", "")
        self.assertEqual(self.db.get("empty"), "")
        
        # Test whitespace-only string
        self.db.add("whitespace", "   ")
        self.assertEqual(self.db.get("whitespace"), "   ")
        
        # Test negative numeric strings
        self.db.add("negative", "-123")
        self.assertEqual(self.db.get("negative"), -123)
        
        # Test floating point strings (should remain as string)
        self.db.add("float_str", "123.45")
        self.assertEqual(self.db.get("float_str"), "123.45")
        
        # Test large numbers
        self.db.add("large", "9999999999999999999")
        self.assertEqual(self.db.get("large"), 9999999999999999999)
        
        # Test zero
        self.db.add("zero", "0")
        self.assertEqual(self.db.get("zero"), 0)

    def test_key_types_and_validation(self):
        """Test different key types and validation"""
        # Test with special characters in keys
        valid_keys = ["key_1", "key123", "KEY", "k"]
        for key in valid_keys:
            self.db.add(key, "value")
            self.assertEqual(self.db.get(key), "value")

    def test_concurrent_operations(self):
        """Test thread safety concerns (pseudo-test for TDD)"""
        # This test defines the expected behavior for concurrent access
        # Implementation would need actual threading protection
        import threading
        
        def add_items(start, end):
            for i in range(start, end):
                self.db.add(f"key_{i}", i)
        
        # This test currently will fail without proper synchronization
        # but defines the expected behavior for implementation
        threads = []
        for i in range(0, 3):
            thread = threading.Thread(target=add_items, args=(i*10, (i+1)*10))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify all items were added
        for i in range(30):
            self.assertIsNotNone(self.db.get(f"key_{i}"))

    def test_memory_limits(self):
        """Test behavior with large datasets"""
        # Test adding many items
        for i in range(1000):
            self.db.add(f"key_{i}", i)
        
        # Verify random access still works
        self.assertEqual(self.db.get("key_500"), 500)
        self.assertEqual(len(self.db.store), 1000)

    def test_type_coercion_edge_cases(self):
        """Test edge cases in type conversion"""
        # Test strings that look numeric but aren't
        test_cases = [
            ("123abc", "123abc"),  # Should remain string
            ("  123  ", "  123  "),  # Should remain string (has spaces)
            ("+123", "+123"),  # Should remain string (has plus sign)
            ("123.0", "123.0"),  # Should remain string (has decimal)
            ("1e5", "1e5"),  # Should remain string (scientific notation)
        ]
        
        for value, expected in test_cases:
            self.db.add("test_key", value)
            self.assertEqual(self.db.get("test_key"), expected)


class TestInterpreterAdvanced(unittest.TestCase):
    """Advanced interpreter tests with complex scenarios"""
    
    def setUp(self):
        self.db = Database()
        self.interpreter = SimpleInterpreter(self.db)

    def test_command_parsing_edge_cases(self):
        """Test edge cases in command parsing"""
        # Test commands with extra whitespace
        result = self.interpreter.execute("  add   key1   123  ")
        # This test will fail initially - need to handle whitespace
        
        # Test commands with special characters in values
        result = self.interpreter.execute("add key1 'hello world'")
        # This test will fail initially - need to handle quoted values
        
        # Test multi-word values
        result = self.interpreter.execute("add key1 hello world")
        self.assertEqual(result, "Added key1: hello world")

    def test_command_history_and_undo(self):
        """Test command history tracking (TDD - implement later)"""
        # This defines expected behavior for command history
        self.interpreter.execute("add key1 100")
        self.interpreter.execute("increment key1 50")
        self.interpreter.execute("delete key1")
        
        # Expected: ability to undo last command
        # result = self.interpreter.undo()
        # self.assertEqual(result, "Undone: delete key1")
        # self.assertEqual(self.db.get("key1"), 150)

    def test_batch_commands(self):
        """Test executing multiple commands at once"""
        batch_commands = [
            "add user1 100",
            "add user2 200",
            "increment user1 50"
        ]
        
        # This test defines expected behavior for batch execution
        # results = self.interpreter.execute_batch(batch_commands)
        # expected = [
        #     "Added user1: 100",
        #     "Added user2: 200", 
        #     "Incremented user1 by 50"
        # ]
        # self.assertEqual(results, expected)

    def test_query_commands(self):
        """Test query/read operations"""
        self.db.add("key1", 123)
        self.db.add("key2", "hello")
        
        # Test get command (to be implemented)
        # result = self.interpreter.execute("get key1")
        # self.assertEqual(result, "key1: 123")
        
        # Test list command (to be implemented)
        # result = self.interpreter.execute("list")
        # self.assertIn("key1: 123", result)
        # self.assertIn("key2: hello", result)

    def test_conditional_operations(self):
        """Test conditional operations"""
        self.db.add("counter", 10)
        
        # Test conditional increment (to be implemented)
        # result = self.interpreter.execute("increment_if_greater counter 5 20")
        # self.assertEqual(result, "Incremented counter by 20")
        # self.assertEqual(self.db.get("counter"), 30)


class TestDatabaseProceduresAdvanced(unittest.TestCase):
    """Advanced tests for database procedures"""
    
    def setUp(self):
        self.db = Database()

    def test_bulk_operations_with_patterns(self):
        """Test bulk operations with more complex patterns"""
        # Setup test data
        test_data = {
            "user_admin_1": 100,
            "user_regular_1": 200,
            "user_admin_2": 300,
            "admin_system": 400,
            "guest_user": 500
        }
        
        for key, value in test_data.items():
            self.db.add(key, value)
        
        # Test bulk delete with pattern matching
        DatabaseProcedures.bulk_delete(self.db, "user_admin")
        
        # Verify correct items were deleted
        self.assertIsNone(self.db.get("user_admin_1"))
        self.assertIsNone(self.db.get("user_admin_2"))
        self.assertIsNotNone(self.db.get("user_regular_1"))
        self.assertIsNotNone(self.db.get("admin_system"))
        self.assertIsNotNone(self.db.get("guest_user"))

    def test_bulk_increment(self):
        """Test bulk increment operation (TDD - to be implemented)"""
        # Setup test data
        for i in range(5):
            self.db.add(f"counter_{i}", i * 10)
        
        # Expected: bulk increment all counters
        # DatabaseProcedures.bulk_increment(self.db, "counter_", 5)
        
        # Verify all counters were incremented
        # for i in range(5):
        #     expected = (i * 10) + 5
        #     self.assertEqual(self.db.get(f"counter_{i}"), expected)

    def test_atomic_operations(self):
        """Test atomic operations (TDD - to be implemented)"""
        self.db.add("account_a", 1000)
        self.db.add("account_b", 500)
        
        # Expected: atomic transfer between accounts
        # DatabaseProcedures.transfer(self.db, "account_a", "account_b", 200)
        
        # self.assertEqual(self.db.get("account_a"), 800)
        # self.assertEqual(self.db.get("account_b"), 700)

    def test_data_validation_procedures(self):
        """Test data validation procedures"""
        # Setup invalid data scenarios
        self.db.add("negative_age", -25)
        self.db.add("valid_age", 30)
        self.db.add("string_data", "not_a_number")
        
        # Expected: validation procedures
        # invalid_keys = DatabaseProcedures.validate_positive_integers(self.db, ["negative_age", "valid_age", "string_data"])
        # self.assertEqual(invalid_keys, ["negative_age", "string_data"])


class TestErrorHandlingAndLogging(unittest.TestCase):
    """Test error handling and logging capabilities"""
    
    def setUp(self):
        self.db = Database()
        self.interpreter = SimpleInterpreter(self.db)

    def test_detailed_error_messages(self):
        """Test that error messages are descriptive and helpful"""
        # Test increment on non-existent key
        with self.assertRaises(ValueError) as context:
            self.interpreter.execute("increment missing_key 10")
        
        error_msg = str(context.exception)
        self.assertIn("missing_key", error_msg)
        self.assertIn("does not exist", error_msg)

    def test_error_recovery(self):
        """Test system behavior after errors"""
        # Execute valid command
        result1 = self.interpreter.execute("add key1 100")
        self.assertEqual(result1, "Added key1: 100")
        
        # Execute invalid command
        try:
            self.interpreter.execute("increment key2 10")
        except ValueError:
            pass
        
        # Verify system still works after error
        result2 = self.interpreter.execute("add key2 200")
        self.assertEqual(result2, "Added key2: 200")

    @patch('builtins.print')
    def test_command_logging(self, mock_print):
        """Test command logging (TDD - to be implemented)"""
        # Expected: commands should be logged
        # self.interpreter.execute("add key1 100")
        # mock_print.assert_called_with("LOG: Executed command 'add key1 100'")


class TestPerformanceAndBenchmarks(unittest.TestCase):
    """Performance and benchmark tests"""
    
    def setUp(self):
        self.db = Database()

    def test_large_dataset_performance(self):
        """Test performance with large datasets"""
        start_time = time.time()
        
        # Add 10,000 items
        for i in range(10000):
            self.db.add(f"key_{i}", i)
        
        add_time = time.time() - start_time
        
        # Test retrieval performance
        start_time = time.time()
        for i in range(0, 10000, 100):  # Sample every 100th item
            self.db.get(f"key_{i}")
        
        get_time = time.time() - start_time
        
        # Assert reasonable performance (adjust thresholds as needed)
        self.assertLess(add_time, 5.0, "Adding 10,000 items should take less than 5 seconds")
        self.assertLess(get_time, 0.1, "Getting 100 items should take less than 0.1 seconds")

    def test_memory_usage_bounds(self):
        """Test memory usage stays within bounds"""
        import sys
        
        initial_size = sys.getsizeof(self.db.store)
        
        # Add many items
        for i in range(1000):
            self.db.add(f"key_{i}", f"value_{i}")
        
        final_size = sys.getsizeof(self.db.store)
        
        # Verify reasonable memory growth
        growth = final_size - initial_size
        self.assertLess(growth, 1024 * 1024, "Memory growth should be reasonable")


class TestDataPersistence(unittest.TestCase):
    """Test data persistence capabilities (TDD)"""
    
    def setUp(self):
        self.db = Database()
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_save_and_load(self):
        """Test saving and loading database state"""
        # Setup test data
        test_data = {
            "user1": 100,
            "user2": "hello",
            "user3": 42
        }
        
        for key, value in test_data.items():
            self.db.add(key, value)
        
        # Expected: save to file
        # self.db.save_to_file(self.temp_file.name)
        
        # Create new database and load
        # new_db = Database()
        # new_db.load_from_file(self.temp_file.name)
        
        # Verify data was loaded correctly
        # for key, value in test_data.items():
        #     self.assertEqual(new_db.get(key), value)

    def test_backup_and_restore(self):
        """Test backup and restore functionality"""
        # Setup test data
        self.db.add("important_data", 12345)
        
        # Expected: create backup
        # backup_data = self.db.create_backup()
        
        # Modify original data
        self.db.delete("important_data")
        self.db.add("new_data", "something")
        
        # Expected: restore from backup
        # self.db.restore_from_backup(backup_data)
        
        # Verify restoration
        # self.assertEqual(self.db.get("important_data"), 12345)
        # self.assertIsNone(self.db.get("new_data"))


class TestSecurityAndValidation(unittest.TestCase):
    """Security and input validation tests"""
    
    def setUp(self):
        self.db = Database()
        self.interpreter = SimpleInterpreter(self.db)

    def test_injection_prevention(self):
        """Test prevention of injection attacks"""
        # Test SQL-like injection attempts (even though we're not using SQL)
        malicious_commands = [
            "add key1'; DROP TABLE users; --",
            "add key1 value; import os; os.system('rm -rf /')",
            "add ../../../etc/passwd malicious_value"
        ]
        
        for command in malicious_commands:
            # Should either execute safely or return invalid command
            result = self.interpreter.execute(command)
            # Database should remain in valid state
            self.assertIsInstance(self.db.store, dict)

    def test_key_sanitization(self):
        """Test key sanitization and validation"""
        # Test various potentially problematic keys
        problematic_keys = [
            "key with spaces",
            "key/with/slashes", 
            "key\nwith\nnewlines",
            "verylongkey" * 100,  # Very long key
            "",  # Empty key
            "key\x00with\x00nulls"  # Keys with null bytes
        ]
        
        # Expected: keys should be validated/sanitized
        for key in problematic_keys:
            # This test defines expected behavior - implementation needed
            pass

    def test_value_size_limits(self):
        """Test limits on value sizes"""
        # Test very large value
        large_value = "x" * 10000
        
        # Expected: should handle large values gracefully
        result = self.interpreter.execute(f"add key1 {large_value}")
        # Should either succeed or fail gracefully with clear error


if __name__ == "__main__":
    # Create test suite with different verbosity levels
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestDatabaseAdvanced,
        TestInterpreterAdvanced, 
        TestDatabaseProceduresAdvanced,
        TestErrorHandlingAndLogging,
        TestPerformanceAndBenchmarks,
        TestDataPersistence,
        TestSecurityAndValidation
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)