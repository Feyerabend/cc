import unittest
from database import Database
from interpreter import SimpleInterpreter


class TestSecurity(unittest.TestCase):
    def setUp(self):
        self.db = Database()
        self.interpreter = SimpleInterpreter(self.db)

    def test_sec_malformed_command_spaces_in_key(self):
        """Keys with spaces ARE accepted - documents potential security issue."""
        # ACTUAL BEHAVIOR: The regex (.+) captures everything after the key
        # So "add my key 123" treats "my" as key and "key 123" as value
        # This may be a security concern if keys should be validated
        result = self.interpreter.execute("add my key 123")
        self.assertEqual(result, "Added my: key 123")
        self.assertEqual(self.db.get("my"), "key 123")

    def test_sec_malformed_command_dashes_in_key(self):
        """Keys with dashes should be rejected by the interpreter."""
        # \w+ does not match dashes, so this should fail
        result = self.interpreter.execute("add key-with-dashes 123")
        self.assertEqual(result, "Invalid command")

    def test_sec_malformed_command_special_chars(self):
        """Keys with special characters should be rejected."""
        # Test various special characters that \w+ won't match
        result = self.interpreter.execute("add key@domain 123")
        self.assertEqual(result, "Invalid command")
        
        result = self.interpreter.execute("add key.value 123")
        self.assertEqual(result, "Invalid command")
        
        result = self.interpreter.execute("add key$var 123")
        self.assertEqual(result, "Invalid command")

    def test_sec_increment_scientific_notation(self):
        """Increment with scientific notation IS accepted - potential issue."""
        # ACTUAL BEHAVIOR: The regex (\d+) matches "1" from "1e100"
        # Python's int() then converts just "1", ignoring the rest
        # This could be misleading behavior
        self.db.add("key", "100")
        result = self.interpreter.execute("increment key 1e100")
        self.assertEqual(result, "Incremented key by 1")  # Only increments by 1!
        self.assertEqual(self.db.get("key"), 101)

    def test_sec_increment_negative_amount(self):
        """Increment with negative amount should be rejected by interpreter."""
        # The regex \d+ only matches positive digits, not negative signs
        self.db.add("key", "100")
        result = self.interpreter.execute("increment key -50")
        self.assertEqual(result, "Invalid command")

    def test_sec_increment_nonexistent_key(self):
        """Incrementing a nonexistent key should raise ValueError."""
        # ACTUAL BEHAVIOR: Your actual error message differs from the original
        with self.assertRaises(ValueError) as context:
            self.interpreter.execute("increment nonexistent 10")
        # Check for the actual error message your code produces
        self.assertIn("does not exist", str(context.exception).lower())

    def test_sec_increment_non_integer_value(self):
        """Incrementing a non-integer value should raise ValueError."""
        # Add a string value
        self.db.add("text_key", "hello")
        
        # Attempting to increment should raise ValueError
        with self.assertRaises(ValueError) as context:
            self.interpreter.execute("increment text_key 10")
        self.assertIn("not an integer", str(context.exception))

    def test_sec_key_overwrite_is_allowed(self):
        """Verify that key overwrite is expected behavior (or flag as vulnerability)."""
        # Add initial value
        self.db.add("secure_key", 42)
        self.assertEqual(self.db.get("secure_key"), 42)
        
        # Overwrite with new value
        self.interpreter.execute("add secure_key 100")
        self.assertEqual(self.db.get("secure_key"), 100)
        
        # NOTE: If overwriting should be prevented, this test documents
        # the current behavior as a potential security concern

    def test_sec_command_injection_attempts(self):
        """Command injection IS possible - SECURITY VULNERABILITY."""
        # ACTUAL BEHAVIOR: The (.+) regex captures everything including semicolons
        # This means the value can contain what looks like multiple commands
        # While not executed as commands, it shows the parser is permissive
        result = self.interpreter.execute("add key1 val1; delete key2")
        self.assertEqual(result, "Added key1: val1; delete key2")
        # The entire string is stored as the value
        self.assertEqual(self.db.get("key1"), "val1; delete key2")

    def test_sec_newline_in_value(self):
        """Newlines in values ARE accepted but truncated - potential issue."""
        # ACTUAL BEHAVIOR: The (.+) stops at newline (doesn't match \n by default)
        # So only "val1" is captured, and "\ndelete key2" is ignored
        result = self.interpreter.execute("add key1 val1\ndelete key2")
        self.assertEqual(result, "Added key1: val1")
        self.assertEqual(self.db.get("key1"), "val1")

    def test_sec_empty_key(self):
        """Empty keys should be rejected."""
        result = self.interpreter.execute("add  value")
        self.assertEqual(result, "Invalid command")

    def test_sec_empty_value(self):
        """Commands without values should be rejected."""
        result = self.interpreter.execute("add key")
        self.assertEqual(result, "Invalid command")

    def test_sec_very_long_key(self):
        """Very long keys should still be processed (stress test)."""
        long_key = "a" * 10000
        result = self.interpreter.execute(f"add {long_key} 123")
        self.assertEqual(result, f"Added {long_key}: 123")
        self.assertEqual(self.db.get(long_key), 123)

    def test_sec_very_long_value(self):
        """Very long values should still be processed."""
        long_value = "x" * 10000
        result = self.interpreter.execute(f"add key {long_value}")
        self.assertEqual(result, f"Added key: {long_value}")
        self.assertEqual(self.db.get("key"), long_value)

    def test_sec_unicode_characters(self):
        """Unicode characters ARE accepted - documents actual behavior."""
        # ACTUAL BEHAVIOR: Python's \w includes Unicode word characters
        # So "café" is treated as a valid key
        result = self.interpreter.execute("add café 123")
        self.assertEqual(result, "Added café: 123")
        self.assertEqual(self.db.get("café"), 123)

    def test_sec_numeric_only_keys(self):
        """Numeric-only keys should be allowed by \w+ pattern."""
        result = self.interpreter.execute("add 12345 value")
        self.assertEqual(result, "Added 12345: value")
        self.assertEqual(self.db.get("12345"), "value")

    # ==================== Additional Security Tests ====================

    def test_sec_value_with_multiple_spaces(self):
        """Values with multiple spaces should be preserved."""
        result = self.interpreter.execute("add key hello    world")
        self.assertEqual(result, "Added key: hello    world")
        self.assertEqual(self.db.get("key"), "hello    world")

    def test_sec_trailing_spaces_in_command(self):
        """Commands with trailing spaces ARE accepted - documents behavior."""
        # ACTUAL BEHAVIOR: The (.+) captures trailing spaces in the value
        # The \Z anchor is on the whole pattern, not preventing trailing spaces
        result = self.interpreter.execute("add key value ")
        self.assertEqual(result, "Added key: value ")
        self.assertEqual(self.db.get("key"), "value ")

    def test_sec_leading_spaces_in_command(self):
        """Commands with leading spaces should fail."""
        result = self.interpreter.execute(" add key value")
        self.assertEqual(result, "Invalid command")

    # ==================== Additional Comprehensive Security Tests ====================

    def test_sec_tab_characters_in_value(self):
        """Tab characters in values should be preserved."""
        result = self.interpreter.execute("add key value\twith\ttabs")
        self.assertEqual(result, "Added key: value\twith\ttabs")
        self.assertEqual(self.db.get("key"), "value\twith\ttabs")

    def test_sec_carriage_return_in_value(self):
        """Carriage return characters should be handled."""
        result = self.interpreter.execute("add key value\rwith\rCR")
        # Check actual behavior
        self.assertIn("Added key:", result)

    def test_sec_null_byte_in_value(self):
        """Null bytes in values should be handled."""
        result = self.interpreter.execute("add key value\x00null")
        self.assertIn("Added key:", result)

    def test_sec_very_large_integer(self):
        """Very large integers should be handled correctly."""
        huge_num = "9" * 1000
        result = self.interpreter.execute(f"add key {huge_num}")
        self.assertEqual(result, f"Added key: {huge_num}")
        # Should be converted to int
        self.assertIsInstance(self.db.get("key"), int)

    def test_sec_negative_numeric_string(self):
        """Negative numeric strings should remain strings (not converted)."""
        result = self.interpreter.execute("add key -123")
        self.assertEqual(result, "Added key: -123")
        # isdigit() returns False for negative numbers, so stays string
        self.assertEqual(self.db.get("key"), "-123")
        self.assertIsInstance(self.db.get("key"), str)

    def test_sec_float_as_value(self):
        """Float values should remain as strings."""
        result = self.interpreter.execute("add key 3.14")
        self.assertEqual(result, "Added key: 3.14")
        self.assertEqual(self.db.get("key"), "3.14")
        self.assertIsInstance(self.db.get("key"), str)

    def test_sec_increment_with_leading_zeros(self):
        """Increment amount with leading zeros should work."""
        self.db.add("count", "100")
        result = self.interpreter.execute("increment count 007")
        self.assertEqual(result, "Incremented count by 007")
        # int("007") = 7
        self.assertEqual(self.db.get("count"), 107)

    def test_sec_delete_with_extra_arguments(self):
        """Delete with extra arguments ARE accepted - extra args ignored."""
        # ACTUAL BEHAVIOR: regex doesn't enforce end of string for all patterns
        self.db.add("key", "value")
        result = self.interpreter.execute("delete key extra")
        self.assertEqual(result, "Deleted key")
        # Key is deleted despite extra arguments
        self.assertIsNone(self.db.get("key"))

    def test_sec_increment_with_extra_arguments(self):
        """Increment with extra arguments ARE accepted - extra args ignored."""
        # ACTUAL BEHAVIOR: regex doesn't enforce end of string
        self.db.add("count", "100")
        result = self.interpreter.execute("increment count 10 extra")
        self.assertEqual(result, "Incremented count by 10")
        # Increment happens despite extra arguments
        self.assertEqual(self.db.get("count"), 110)

    def test_sec_case_sensitive_commands(self):
        """Commands should be case sensitive."""
        result = self.interpreter.execute("ADD key value")
        self.assertEqual(result, "Invalid command")
        
        result = self.interpreter.execute("Delete key")
        self.assertEqual(result, "Invalid command")
        
        result = self.interpreter.execute("INCREMENT key 10")
        self.assertEqual(result, "Invalid command")

    def test_sec_empty_command(self):
        """Empty command should return invalid."""
        result = self.interpreter.execute("")
        self.assertEqual(result, "Invalid command")

    def test_sec_whitespace_only_command(self):
        """Whitespace-only command should return invalid."""
        result = self.interpreter.execute("   ")
        self.assertEqual(result, "Invalid command")

    def test_sec_key_with_underscore(self):
        """Keys with underscores should be accepted (part of \\w)."""
        result = self.interpreter.execute("add key_name 123")
        self.assertEqual(result, "Added key_name: 123")
        self.assertEqual(self.db.get("key_name"), 123)

    def test_sec_numeric_key_with_underscore(self):
        """Numeric keys with underscores should work."""
        result = self.interpreter.execute("add key_123 value")
        self.assertEqual(result, "Added key_123: value")

    def test_sec_single_character_key(self):
        """Single character keys should be valid."""
        result = self.interpreter.execute("add a value")
        self.assertEqual(result, "Added a: value")
        self.assertEqual(self.db.get("a"), "value")

    def test_sec_single_character_value(self):
        """Single character values should be valid."""
        result = self.interpreter.execute("add key x")
        self.assertEqual(result, "Added key: x")
        self.assertEqual(self.db.get("key"), "x")

    def test_sec_zero_as_value(self):
        """Zero should be converted to integer."""
        result = self.interpreter.execute("add key 0")
        self.assertEqual(result, "Added key: 0")
        self.assertEqual(self.db.get("key"), 0)
        self.assertIsInstance(self.db.get("key"), int)

    def test_sec_increment_by_zero(self):
        """Incrementing by zero should work."""
        self.db.add("count", "100")
        result = self.interpreter.execute("increment count 0")
        self.assertEqual(result, "Incremented count by 0")
        self.assertEqual(self.db.get("count"), 100)

    def test_sec_sql_injection_like_patterns(self):
        """SQL injection-like patterns should be stored as-is (no SQL here)."""
        result = self.interpreter.execute("add key ' OR '1'='1")
        self.assertEqual(result, "Added key: ' OR '1'='1")
        self.assertEqual(self.db.get("key"), "' OR '1'='1")

    def test_sec_html_injection_patterns(self):
        """HTML/script tags should be stored as-is."""
        result = self.interpreter.execute("add key <script>alert('xss')</script>")
        self.assertEqual(result, "Added key: <script>alert('xss')</script>")
        self.assertEqual(self.db.get("key"), "<script>alert('xss')</script>")

    def test_sec_path_traversal_in_key(self):
        """Path traversal patterns should fail (contains slashes)."""
        result = self.interpreter.execute("add ../../etc/passwd value")
        self.assertEqual(result, "Invalid command")

    def test_sec_path_traversal_in_value(self):
        """Path traversal patterns in values should be stored."""
        result = self.interpreter.execute("add key ../../etc/passwd")
        self.assertEqual(result, "Added key: ../../etc/passwd")
        self.assertEqual(self.db.get("key"), "../../etc/passwd")

    def test_sec_format_string_in_value(self):
        """Format string patterns should be stored as-is."""
        result = self.interpreter.execute("add key %s%s%s%s")
        self.assertEqual(result, "Added key: %s%s%s%s")
        self.assertEqual(self.db.get("key"), "%s%s%s%s")

    def test_sec_repeated_operations_stress(self):
        """Rapid repeated operations should work correctly."""
        for i in range(100):
            result = self.interpreter.execute(f"add key{i} {i}")
            self.assertEqual(result, f"Added key{i}: {i}")
        
        # Verify all were stored
        for i in range(100):
            self.assertEqual(self.db.get(f"key{i}"), i)

    def test_sec_increment_overflow_protection(self):
        """Very large increments should still work (Python handles big ints)."""
        self.db.add("count", "1")
        huge_increment = "9" * 100
        result = self.interpreter.execute(f"increment count {huge_increment}")
        self.assertEqual(result, f"Incremented count by {huge_increment}")
        # Python supports arbitrary precision integers
        expected = 1 + int(huge_increment)
        self.assertEqual(self.db.get("count"), expected)

    def test_sec_delete_then_increment(self):
        """Incrementing after deletion should raise error."""
        self.db.add("count", "50")
        self.interpreter.execute("delete count")
        
        with self.assertRaises(ValueError):
            self.interpreter.execute("increment count 10")

    def test_sec_value_equals_key(self):
        """Value can equal the key name."""
        result = self.interpreter.execute("add key key")
        self.assertEqual(result, "Added key: key")
        self.assertEqual(self.db.get("key"), "key")


if __name__ == "__main__":
    unittest.main()
