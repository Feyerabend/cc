"""
Examples and demonstrations of the Natural Language Parser
This file shows various grammars and parsing examples using DCG notation.
"""

from nlp_prolog import DCGDatabase, Atom, Variable, Compound, ListTerm


def simple_arithmetic_parser():
    """A simple arithmetic expression parser using DCGs."""
    print("\n" + "-" * 50)
    print("Example 1: Arithmetic Expression Parser")
    print("-" * 50)
    
    db = DCGDatabase()
    db.add_clause(Compound("=", [Variable("X"), Variable("X")]), [])
    
    # Arithmetic grammar
    grammar = """
    expr --> term, plus, expr.
    expr --> term.
    
    term --> factor, times, term.
    term --> factor.
    
    factor --> number.
    factor --> lparen, expr, rparen.
    
    plus --> [plus].
    times --> [times].
    lparen --> [lparen].
    rparen --> [rparen].
    number --> [one].
    number --> [two].
    number --> [three].
    """.strip()
    
    for line in grammar.split('\n'):
        line = line.strip()
        if line and not line.startswith('%'):
            db.add_dcg_rule(line)
    
    # Test expressions
    test_cases = [
        ["one", "plus", "two"],
        ["one", "times", "two", "plus", "three"],
        ["lparen", "one", "plus", "two", "rparen", "times", "three"],
        ["one", "plus"],  # Invalid
    ]
    
    for expr in test_cases:
        print(f"\nExpression: {' '.join(expr)}")
        solutions = db.parse_sentence("expr", expr)
        print(f"  {'✓ Valid' if solutions else '✗ Invalid'}")


def question_parser():
    """Parser for different types of questions."""
    print("\n" + "-" * 50)
    print("Example 2: Question Parser")
    print("-" * 50)
    
    db = DCGDatabase()
    db.add_clause(Compound("=", [Variable("X"), Variable("X")]), [])
    
    grammar = """
    question --> wh_word, aux, noun_phrase, verb_phrase.
    question --> aux, noun_phrase, verb_phrase.
    question --> wh_word, verb_phrase.
    
    wh_word --> [what].
    wh_word --> [who].
    wh_word --> [where].
    wh_word --> [when].
    wh_word --> [why].
    wh_word --> [how].
    
    aux --> [is].
    aux --> [are].
    aux --> [do].
    aux --> [does].
    aux --> [did].
    aux --> [will].
    
    noun_phrase --> determiner, noun.
    noun_phrase --> pronoun.
    noun_phrase --> proper_noun.
    
    verb_phrase --> verb, noun_phrase.
    verb_phrase --> verb.
    verb_phrase --> verb, adverb.
    
    determiner --> [the].
    determiner --> [a].
    
    pronoun --> [you].
    pronoun --> [he].
    pronoun --> [she].
    pronoun --> [they].
    
    proper_noun --> [alice].
    proper_noun --> [bob].
    
    noun --> [cat].
    noun --> [book].
    noun --> [meeting].
    
    verb --> [read].
    verb --> [running].
    verb --> [go].
    verb --> [sleep].
    
    adverb --> [quickly].
    adverb --> [slowly].
    """.strip()
    
    for line in grammar.split('\n'):
        line = line.strip()
        if line and not line.startswith('%'):
            db.add_dcg_rule(line)
    
    test_questions = [
        ["what", "is", "the", "cat"],
        ["who", "did", "alice", "read"],
        ["where", "are", "you", "go"],
        ["how", "does", "bob", "sleep"],
        ["what", "running"],  # Should fail
    ]
    
    for question in test_questions:
        print(f"\nQuestion: {' '.join(question)}")
        solutions = db.parse_sentence("question", question)
        print(f"  {'✓ Valid question' if solutions else '✗ Invalid question'}")


def command_parser():
    """Parser for simple imperative commands."""
    print("\n" + "-" * 50)
    print("Example 3: Command Parser (Imperatives)")
    print("-" * 50)
    
    db = DCGDatabase()
    db.add_clause(Compound("=", [Variable("X"), Variable("X")]), [])
    
    grammar = """
    command --> verb, object.
    command --> verb, object, location.
    command --> verb, direction.
    
    object --> determiner, noun.
    object --> noun.
    
    location --> preposition, place.
    
    determiner --> [the].
    determiner --> [a].
    
    verb --> [move].
    verb --> [take].
    verb --> [put].
    verb --> [open].
    verb --> [close].
    verb --> [go].
    
    noun --> [box].
    noun --> [door].
    noun --> [key].
    noun --> [lamp].
    
    preposition --> [in].
    preposition --> [on].
    preposition --> [to].
    preposition --> [under].
    
    place --> [table].
    place --> [room].
    place --> [floor].
    
    direction --> [north].
    direction --> [south].
    direction --> [east].
    direction --> [west].
    """.strip()
    
    for line in grammar.split('\n'):
        line = line.strip()
        if line and not line.startswith('%'):
            db.add_dcg_rule(line)
    
    test_commands = [
        ["take", "the", "key"],
        ["put", "box", "on", "table"],
        ["go", "north"],
        ["open", "the", "door"],
        ["move", "lamp", "to", "room"],
        ["take"],  # Invalid
    ]
    
    for cmd in test_commands:
        print(f"\nCommand: {' '.join(cmd)}")
        solutions = db.parse_sentence("command", cmd)
        print(f"  {'✓ Valid command' if solutions else '✗ Invalid command'}")


def complex_sentence_parser():
    """Parser with relative clauses and conjunctions."""
    print("\n" + "-" * 50)
    print("Example 4: Complex Sentences with Relative Clauses")
    print("-" * 50)
    
    db = DCGDatabase()
    db.add_clause(Compound("=", [Variable("X"), Variable("X")]), [])
    
    grammar = """
    sentence --> simple_sentence.
    sentence --> simple_sentence, conjunction, sentence.
    
    simple_sentence --> noun_phrase, verb_phrase.
    
    noun_phrase --> determiner, noun.
    noun_phrase --> determiner, noun, rel_clause.
    noun_phrase --> proper_noun.
    
    rel_clause --> rel_pronoun, verb_phrase.
    
    verb_phrase --> verb, noun_phrase.
    verb_phrase --> verb.
    
    conjunction --> [and].
    conjunction --> [but].
    conjunction --> [or].
    
    rel_pronoun --> [that].
    rel_pronoun --> [who].
    rel_pronoun --> [which].
    
    determiner --> [the].
    determiner --> [a].
    
    proper_noun --> [alice].
    proper_noun --> [bob].
    
    noun --> [cat].
    noun --> [dog].
    noun --> [book].
    noun --> [idea].
    
    verb --> [likes].
    verb --> [reads].
    verb --> [chased].
    verb --> [runs].
    verb --> [sleeps].
    """.strip()
    
    for line in grammar.split('\n'):
        line = line.strip()
        if line and not line.startswith('%'):
            db.add_dcg_rule(line)
    
    test_sentences = [
        ["the", "cat", "that", "chased", "the", "dog", "sleeps"],
        ["alice", "reads", "the", "book", "and", "bob", "runs"],
        ["the", "dog", "that", "runs", "likes", "alice"],
        ["a", "cat", "sleeps", "and", "a", "dog", "runs", "but", "bob", "reads"],
    ]
    
    for sentence in test_sentences:
        print(f"\nSentence: {' '.join(sentence)}")
        solutions = db.parse_sentence("sentence", sentence)
        count = len(solutions) if solutions else 0
        print(f"  {'✓' if solutions else '✗'} Found {count} parse(s)")


def semantic_parser():
    """Parser that builds semantic representations."""
    print("\n" + "-" * 50)
    print("Example 5: Parser with Semantic Annotations")
    print("-" * 50)
    
    print("\nNote: This demonstrates how DCG rules could be extended")
    print("with semantic features using Prolog goals in braces {}")
    
    print("\nExample DCG rules with semantics:")
    print("-" * 60)
    
    examples = [
        "sentence(sem(S, VP)) --> noun_phrase(S), verb_phrase(VP).",
        "noun_phrase(np(Det, N)) --> determiner(Det), noun(N).",
        "verb_phrase(vp(V, NP)) --> verb(V), noun_phrase(NP).",
    ]
    
    for ex in examples:
        print(f"  {ex}")
    
    print("\nThese rules would build parse trees as they recognise sentences.")
    print("The semantic representations are built compositionally from parts.")


def main():
    print("-" * 50)
    print("Natural Language Parser Examples")
    print("-" * 50)

    simple_arithmetic_parser()
    question_parser()
    command_parser()
    complex_sentence_parser()
    semantic_parser()

    print("\n" + "-" * 50)
    print("All examples completed!")
    print("-" * 50)
    print("\nTo try your own grammars, run: python nlp_prolog.py")
    print()


if __name__ == "__main__":
    main()
