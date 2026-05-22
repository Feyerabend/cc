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

