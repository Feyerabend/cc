from hypothesis import given
import hypothesis.strategies as st
import unittest
from database import Database
from procedures import DatabaseProcedures

class TestPropertyBased(unittest.TestCase):
    @given(st.text(min_size=1, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))), st.integers())
    def test_prop_add_get_roundtrip(self, key, value):
        db = Database()
        db.add(key, value)
        self.assertEqual(db.get(key), value)  # Property: get returns what was added (if key valid; else adapt)

    @given(st.integers(min_value=0, max_value=1000), st.integers(min_value=1, max_value=100))
    def test_prop_increment_monotonic(self, initial, increment):
        db = Database()
        db.add("prop_key", initial)
        DatabaseProcedures.increment_value(db, "prop_key", increment)
        self.assertEqual(db.get("prop_key"), initial + increment)  # Property: increment increases by exact amount

    @given(st.text(min_size=1))
    def test_prop_delete_idempotent(self, key):
        db = Database()
        db.delete(key)  # First delete (no-op if missing)
        db.delete(key)  # Second delete still no-op
        self.assertIsNone(db.get(key))  # Property: delete is idempotent

if __name__ == "__main__":
    unittest.main()
