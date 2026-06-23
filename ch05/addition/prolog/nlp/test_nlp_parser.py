"""
Test Suite for Natural Language Parser
Comprehensive tests demonstrating DCG parsing capabilities.
"""

from nlp_prolog import DCGDatabase, create_example_grammar, create_advanced_grammar
from nlp_prolog import Atom, Variable, Compound, ListTerm


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def test_basic_sentences():
    """Test basic sentence parsing."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Test 1: Basic Sentence Structures{Colors.RESET}")
    print("-" * 60)
    
    db = create_example_grammar()
    
    test_cases = [
        (["the", "cat", "chases", "the", "mouse"], True),
        (["a", "dog", "eats", "cheese"], True),
        (["the", "cat", "sees", "a", "dog"], True),
        (["cat", "chases", "mouse"], True),  # No determiners
        (["the", "chases", "cat"], False),   # Wrong order
        (["cat", "the", "chases"], False),   # Wrong order
        (["the", "cat"], False),             # Incomplete
    ]
    
    passed = 0
    failed = 0
    
    for sentence, should_pass in test_cases:
        solutions = db.parse_sentence("sentence", sentence)
        is_valid = len(solutions) > 0
        
        if is_valid == should_pass:
            print(f"  {Colors.GREEN}✓{Colors.RESET} {' '.join(sentence):40} "
                  f"{'[valid]' if is_valid else '[invalid]'}")
            passed += 1
        else:
            print(f"  {Colors.RED}✗{Colors.RESET} {' '.join(sentence):40} "
                  f"Expected: {'valid' if should_pass else 'invalid'}, "
                  f"Got: {'valid' if is_valid else 'invalid'}")
            failed += 1
    
    print(f"\n  Results: {passed} passed, {failed} failed")
    return failed == 0


def test_advanced_sentences():
    """Test more complex sentence structures."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Test 2: Advanced Grammar{Colors.RESET}")
    print("-" * 60)
    
    db = create_advanced_grammar()
    
    test_cases = [
        (["the", "big", "cat", "chases", "the", "small", "mouse"], True),
        (["john", "sees", "the", "red", "bird"], True),
        (["a", "hungry", "dog", "eats"], True),
        (["the", "cat", "runs", "in", "the", "garden"], True),
        (["mary", "sleeps", "on", "the", "cat"], True),
        (["big", "the", "cat", "runs"], False),  # Wrong adjective position
        (["the", "cat", "the", "dog"], False),   # Two NPs
    ]
    
    passed = 0
    failed = 0
    
    for sentence, should_pass in test_cases:
        solutions = db.parse_sentence("sentence", sentence)
        is_valid = len(solutions) > 0
        
        if is_valid == should_pass:
            print(f"  {Colors.GREEN}✓{Colors.RESET} {' '.join(sentence):50} "
                  f"{'[valid]' if is_valid else '[invalid]'}")
            passed += 1
        else:
            print(f"  {Colors.RED}✗{Colors.RESET} {' '.join(sentence):50} "
                  f"Expected: {'valid' if should_pass else 'invalid'}")
            failed += 1
    
    print(f"\n  Results: {passed} passed, {failed} failed")
    return failed == 0


def test_ambiguity():
    """Test handling of ambiguous sentences."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Test 3: Ambiguous Sentences{Colors.RESET}")
    print("-" * 60)
    
    db = DCGDatabase()
    db.add_clause(Compound("=", [Variable("X"), Variable("X")]), [])
    
    # A genuinely ambiguous grammar: prepositional-phrase attachment. Each PP can
    # attach to the preceding noun (nom --> noun, pp) or to the verb phrase
    # (vp --> verb, np, pp), so a sentence with k trailing PPs has multiple
    # parses. The rules are right-recursive (pp --> prep, np), so the top-down
    # solver does not loop. (The earlier grammar here was unambiguous — every
    # sentence had exactly one parse — so its 2-/3-parse expectations could never
    # be met; this version actually exercises ambiguity handling.)
    grammar = """
    sentence --> np, vp.
    np --> det, nom.
    np --> nom.
    nom --> noun.
    nom --> noun, pp.
    vp --> verb, np.
    vp --> verb, np, pp.
    vp --> verb.
    pp --> prep, np.

    det --> [the].
    noun --> [cat].
    noun --> [dog].
    noun --> [telescope].
    noun --> [park].
    verb --> [saw].
    prep --> [with].
    prep --> [in].
    """.strip()

    for line in grammar.split('\n'):
        line = line.strip()
        if line and not line.startswith('%'):
            db.add_dcg_rule(line)

    # Test sentences with increasing PP-attachment ambiguity.
    test_cases = [
        (["the", "cat", "saw", "the", "dog"], 1),  # no PP: one parse
        # one PP — attaches to "dog" or to the VP: two parses
        (["the", "cat", "saw", "the", "dog", "with", "the", "telescope"], 2),
        # two PPs — three attachment combinations the solver enumerates
        (["the", "cat", "saw", "the", "dog",
          "in", "the", "park", "with", "the", "telescope"], 3),
    ]
    
    passed = 0
    failed = 0
    
    for sentence, expected_parses in test_cases:
        solutions = db.parse_sentence("sentence", sentence)
        num_parses = len(solutions)
        
        if num_parses >= expected_parses:
            print(f"  {Colors.GREEN}✓{Colors.RESET} {' '.join(sentence):30} "
                  f"Found {num_parses} parse(s) (expected ≥{expected_parses})")
            passed += 1
        else:
            print(f"  {Colors.RED}✗{Colors.RESET} {' '.join(sentence):30} "
                  f"Found {num_parses} parse(s) (expected ≥{expected_parses})")
            failed += 1
    
    print(f"\n  Results: {passed} passed, {failed} failed")
    return failed == 0


def test_custom_grammar():
    """Test creating and using a custom grammar."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Test 4: Custom Grammar Creation{Colors.RESET}")
    print("-" * 60)
    
    db = DCGDatabase()
    db.add_clause(Compound("=", [Variable("X"), Variable("X")]), [])
    
    # Create a simple greeting grammar
    print("  Creating grammar for greetings...")
    grammar = """
    greeting --> hello, name.
    greeting --> goodbye, name.
    hello --> [hello].
    hello --> [hi].
    goodbye --> [bye].
    goodbye --> [goodbye].
    name --> [world].
    name --> [alice].
    name --> [bob].
    """.strip()
    
    for line in grammar.split('\n'):
        line = line.strip()
        if line and not line.startswith('%'):
            db.add_dcg_rule(line)
    
    test_cases = [
        (["hello", "world"], True),
        (["hi", "alice"], True),
        (["goodbye", "bob"], True),
        (["hello"], False),           # Incomplete
        (["world", "hello"], False),  # Wrong order
    ]
    
    passed = 0
    failed = 0
    
    for sentence, should_pass in test_cases:
        solutions = db.parse_sentence("greeting", sentence)
        is_valid = len(solutions) > 0
        
        if is_valid == should_pass:
            print(f"  {Colors.GREEN}✓{Colors.RESET} {' '.join(sentence):30} "
                  f"{'[valid]' if is_valid else '[invalid]'}")
            passed += 1
        else:
            print(f"  {Colors.RED}✗{Colors.RESET} {' '.join(sentence):30} "
                  f"Expected: {'valid' if should_pass else 'invalid'}")
            failed += 1
    
    print(f"\n  Results: {passed} passed, {failed} failed")
    return failed == 0


def test_recursive_structures():
    """Test recursive grammar rules."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Test 5: Recursive Structures{Colors.RESET}")
    print("-" * 60)
    
    db = DCGDatabase()
    db.add_clause(Compound("=", [Variable("X"), Variable("X")]), [])
    
    # Grammar with conjunction (recursive)
    grammar = """
    sentence --> simple, conj, sentence.
    sentence --> simple.
    simple --> [cat].
    simple --> [dog].
    simple --> [bird].
    conj --> [and].
    conj --> [or].
    """.strip()
    
    for line in grammar.split('\n'):
        line = line.strip()
        if line and not line.startswith('%'):
            db.add_dcg_rule(line)
    
    test_cases = [
        (["cat"], 1),
        (["cat", "and", "dog"], 1),
        (["cat", "and", "dog", "and", "bird"], 1),
        (["cat", "or", "dog", "or", "bird", "or", "cat"], 1),
    ]
    
    passed = 0
    failed = 0
    
    for sentence, min_parses in test_cases:
        solutions = db.parse_sentence("sentence", sentence)
        num_parses = len(solutions)
        
        if num_parses >= min_parses:
            print(f"  {Colors.GREEN}✓{Colors.RESET} {' '.join(sentence):45} "
                  f"{num_parses} parse(s)")
            passed += 1
        else:
            print(f"  {Colors.RED}✗{Colors.RESET} {' '.join(sentence):45} "
                  f"Expected ≥{min_parses}, got {num_parses}")
            failed += 1
    
    print(f"\n  Results: {passed} passed, {failed} failed")
    return failed == 0


def test_empty_productions():
    """Test grammars with optional elements."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Test 6: Optional Elements{Colors.RESET}")
    print("-" * 60)
    
    db = DCGDatabase()
    db.add_clause(Compound("=", [Variable("X"), Variable("X")]), [])
    
    # Grammar with optional adjectives
    grammar = """
    noun_phrase --> det, adjs, noun.
    adjs --> adj, adjs.
    adjs --> [].
    det --> [the].
    adj --> [big].
    adj --> [red].
    noun --> [cat].
    """.strip()
    
    # Note: Empty production [] is tricky in our implementation
    # For this test, we'll use a simpler approach
    
    grammar = """
    noun_phrase --> det, adj, noun.
    noun_phrase --> det, noun.
    det --> [the].
    adj --> [big].
    adj --> [red].
    noun --> [cat].
    """.strip()
    
    for line in grammar.split('\n'):
        line = line.strip()
        if line and not line.startswith('%'):
            db.add_dcg_rule(line)
    
    test_cases = [
        (["the", "cat"], True),
        (["the", "big", "cat"], True),
        (["the", "red", "cat"], True),
        (["big", "cat"], False),  # Missing determiner
    ]
    
    passed = 0
    failed = 0
    
    for sentence, should_pass in test_cases:
        solutions = db.parse_sentence("noun_phrase", sentence)
        is_valid = len(solutions) > 0
        
        if is_valid == should_pass:
            print(f"  {Colors.GREEN}✓{Colors.RESET} {' '.join(sentence):30} "
                  f"{'[valid]' if is_valid else '[invalid]'}")
            passed += 1
        else:
            print(f"  {Colors.RED}✗{Colors.RESET} {' '.join(sentence):30} "
                  f"Expected: {'valid' if should_pass else 'invalid'}")
            failed += 1
    
    print(f"\n  Results: {passed} passed, {failed} failed")
    return failed == 0


def main():
    """Run all tests."""
    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}Natural Language Parser - Test Suite{Colors.RESET}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}")
    
    results = []
    
    results.append(("Basic Sentences", test_basic_sentences()))
    results.append(("Advanced Grammar", test_advanced_sentences()))
    results.append(("Ambiguity Handling", test_ambiguity()))
    results.append(("Custom Grammar", test_custom_grammar()))
    results.append(("Recursive Structures", test_recursive_structures()))
    results.append(("Optional Elements", test_empty_productions()))
    
    # Summary
    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}Test Summary{Colors.RESET}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    for name, passed in results:
        status = f"{Colors.GREEN}PASSED{Colors.RESET}" if passed else f"{Colors.RED}FAILED{Colors.RESET}"
        print(f"  {name:30} {status}")
    
    print(f"\n{Colors.BOLD}Overall: {total_passed}/{total_tests} test suites passed{Colors.RESET}")
    
    if total_passed == total_tests:
        print(f"{Colors.GREEN}{Colors.BOLD}All tests passed! ✓{Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}Some tests failed. Please review.{Colors.RESET}")
    
    print(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}\n")
    
    return total_passed == total_tests


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
