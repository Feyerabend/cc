from hypothesis import given, strategies as st

@given(st.text(), st.text(), st.text())
def test_string_concatenation_associativity(a, b, c):
    """Associativity: (a + b) + c == a + (b + c)"""
    left_assoc = (a + b) + c
    right_assoc = a + (b + c)
    assert left_assoc == right_assoc, \
        f"Associativity failed: {left_assoc} != {right_assoc}"

@given(st.text())
def test_string_concatenation_identity(s):
    """Identity element is empty string"""
    assert s + "" == s, "Right identity failed"
    assert "" + s == s, "Left identity failed"

@given(st.text(), st.text())
def test_string_concatenation_length(a, b):
    """Length is additive for concatenation"""
    concatenated = a + b
    assert len(concatenated) == len(a) + len(b), \
        "Length additivity violated"

@given(st.text())
def test_string_reverse_twice(s):
    """Reversing twice yields original string"""
    assert s[::-1][::-1] == s, "Double reverse failed"

@given(st.text(), st.text())
def test_string_substring_property(a, b):
    """Concatenation contains original strings as substrings"""
    concatenated = a + b
    assert a in concatenated, "Left substring missing"
    assert b in concatenated, "Right substring missing"

if __name__ == "__main__":
    import pytest
    # Run all tests in this module
    pytest.main([__file__])
