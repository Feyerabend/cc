"""
Natural Language Parser for Mini-Prolog
Extends mprolog.py with DCG (Definite Clause Grammar) support
for parsing natural language sentences.

DCG notation is transformed into difference lists for efficient parsing.
For example:
    sentence --> noun_phrase, verb_phrase.
becomes:
    sentence(S0, S) :- noun_phrase(S0, S1), verb_phrase(S1, S).
"""

import sys
import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

# Import core Prolog components from mprolog
from mprolog import (
    Term, Atom, Variable, Compound, ListTerm,
    Database, Environment, unify, substitute, solve,
    parse_input, format_solution,
    ParseError, satisfy, literal, one_of, seq, choice, many, many1,
    fmap, bind, ws, token, symbol, parens, parse_result, sep_by,
    item
)


# DCG Parser Extensions
def parse_dcg_rule():
    """Parse a DCG rule: head --> body."""
    def parser(input_str: str):
        # Parse head (a compound term or atom)
        from mprolog import parse_term
        head, rest = token(parse_term())(input_str)
        
        # Expect -->
        _, rest = token(symbol("-->"))(rest)
        
        # Parse body (DCG goals)
        body, rest = parse_dcg_body()(rest)
        
        return (head, body), rest
    return parser


def parse_dcg_body():
    """Parse DCG body: terminals, non-terminals, and Prolog goals."""
    def parser(input_str: str):
        goals = []
        rest = input_str
        
        while True:
            try:
                # Try to parse a DCG goal
                goal, rest = parse_dcg_goal()(rest)
                goals.append(goal)
                
                # Check for comma
                try:
                    _, rest = token(symbol(","))(rest)
                except ParseError:
                    break
            except ParseError:
                break
        
        if not goals:
            raise ParseError("Expected at least one DCG goal")
        
        return goals, rest
    return parser


def parse_dcg_goal():
    """Parse a single DCG goal: terminal list, non-terminal, or Prolog goal."""
    def parser(input_str: str):
        rest = input_str
        
        # Skip whitespace
        _, rest = ws()(rest)
        
        # Try terminal list: [word1, word2, ...]
        if rest.startswith('['):
            from mprolog import parse_list
            terminal_list, rest = token(parse_list())(rest)
            return ('terminal', terminal_list), rest
        
        # Try Prolog goal in braces: {Goal}
        if rest.startswith('{'):
            _, rest = literal('{')(rest)
            _, rest = ws()(rest)
            
            # Parse until closing brace
            goal_str = ""
            depth = 0
            i = 0
            while i < len(rest):
                if rest[i] == '{':
                    depth += 1
                    goal_str += rest[i]
                elif rest[i] == '}':
                    if depth == 0:
                        break
                    depth -= 1
                    goal_str += rest[i]
                else:
                    goal_str += rest[i]
                i += 1
            
            if i >= len(rest):
                raise ParseError("Unclosed brace in Prolog goal")
            
            rest = rest[i+1:]
            
            from mprolog import parse_term
            goal, _ = parse_term()(goal_str.strip())
            return ('prolog', goal), rest
        
        # Otherwise, it's a non-terminal (compound term or atom)
        from mprolog import parse_term
        nonterminal, rest = token(parse_term())(rest)
        return ('nonterminal', nonterminal), rest
    
    return parser


def dcg_to_prolog(head: Term, dcg_body: List[Tuple]) -> Tuple[Term, List[Term]]:
    """
    Transform a DCG rule into a standard Prolog clause.
    
    Example:
        sentence --> noun_phrase, verb_phrase.
    becomes:
        sentence(S0, S) :- noun_phrase(S0, S1), verb_phrase(S1, S).
    """
    # Create difference list variables
    var_counter = [0]
    
    def new_var():
        var_counter[0] += 1
        return Variable(f"S{var_counter[0] - 1}")
    
    # Add two arguments to the head for the difference list
    s_in = new_var()
    s_out = new_var()
    
    if isinstance(head, Atom):
        new_head = Compound(head.name, [s_in, s_out])
    elif isinstance(head, Compound):
        new_head = Compound(head.functor, list(head.args) + [s_in, s_out])
    else:
        raise ValueError(f"Invalid DCG head: {head}")
    
    # Transform body
    prolog_goals = []
    current_var = s_in
    
    for goal_type, goal_data in dcg_body:
        if goal_type == 'terminal':
            # Terminal: match words from the input
            # [word1, word2] becomes: S1 = [word1, word2 | S2]
            next_var = new_var()
            
            # Create the list structure
            if isinstance(goal_data, ListTerm):
                # Build nested list with tail
                terminal_list = ListTerm(list(goal_data.elements), next_var)
                prolog_goals.append(Compound("=", [current_var, terminal_list]))
                current_var = next_var
            elif isinstance(goal_data, Atom) and goal_data.name == "[]":
                # Empty terminal list, no change
                pass
            else:
                raise ValueError(f"Invalid terminal: {goal_data}")
        
        elif goal_type == 'nonterminal':
            # Non-terminal: call with difference list
            next_var = new_var()
            
            if isinstance(goal_data, Atom):
                new_goal = Compound(goal_data.name, [current_var, next_var])
            elif isinstance(goal_data, Compound):
                new_goal = Compound(goal_data.functor, 
                                   list(goal_data.args) + [current_var, next_var])
            else:
                raise ValueError(f"Invalid non-terminal: {goal_data}")
            
            prolog_goals.append(new_goal)
            current_var = next_var
        
        elif goal_type == 'prolog':
            # Regular Prolog goal: add as-is
            prolog_goals.append(goal_data)
        
        else:
            raise ValueError(f"Unknown goal type: {goal_type}")
    
    # Unify final variable with output
    if current_var != s_out:
        prolog_goals.append(Compound("=", [current_var, s_out]))
    
    return new_head, prolog_goals


# Extended Database with DCG support
class DCGDatabase(Database):
    """Database that can handle DCG rules."""
    
    def add_dcg_rule(self, rule_str: str):
        """Parse and add a DCG rule to the database."""
        try:
            (head, dcg_body), _ = parse_dcg_rule()(rule_str.strip())
            prolog_head, prolog_body = dcg_to_prolog(head, dcg_body)
            self.add_clause(prolog_head, prolog_body)
            return True
        except Exception as e:
            print(f"Error parsing DCG rule: {e}")
            return False
    
    def parse_sentence(self, grammar_start: str, sentence: List[str]) -> List[Environment]:
        """
        Parse a sentence using the DCG grammar.
        
        Args:
            grammar_start: The start symbol (e.g., "sentence")
            sentence: List of words to parse
        
        Returns:
            List of successful parse environments
        """
        # Create the query: grammar_start(Sentence, [])
        sentence_list = ListTerm([Atom(word) for word in sentence])
        empty_list = Atom("[]")
        
        query = Compound(grammar_start, [sentence_list, empty_list])
        
        # Solve the query
        solutions = solve([query], Environment(), self)
        return solutions


# Initialize database with example grammar
def create_example_grammar() -> DCGDatabase:
    """Create a database with a simple English grammar."""
    db = DCGDatabase()
    
    # Add standard Prolog predicates
    db.add_clause(Compound("=", [Variable("X"), Variable("X")]), [])
    
    # Define a simple grammar using DCG notation
    grammar_rules = """
    % Simple English Grammar
    
    % A sentence is a noun phrase followed by a verb phrase
    sentence --> noun_phrase, verb_phrase.
    
    % A noun phrase can be a determiner followed by a noun
    noun_phrase --> determiner, noun.
    noun_phrase --> noun.
    
    % A verb phrase is a verb optionally followed by a noun phrase
    verb_phrase --> verb, noun_phrase.
    verb_phrase --> verb.
    
    % Lexicon - terminals
    determiner --> [the].
    determiner --> [a].
    
    noun --> [cat].
    noun --> [dog].
    noun --> [mouse].
    noun --> [cheese].
    
    verb --> [chases].
    verb --> [eats].
    verb --> [sees].
    """.strip()
    
    # Parse and add each DCG rule
    for line in grammar_rules.split('\n'):
        line = line.strip()
        if line and not line.startswith('%'):
            db.add_dcg_rule(line)
    
    return db


# More advanced grammar with features
def create_advanced_grammar() -> DCGDatabase:
    """Create a more sophisticated grammar with semantic features."""
    db = DCGDatabase()
    
    # Add standard predicates
    db.add_clause(Compound("=", [Variable("X"), Variable("X")]), [])
    
    # Grammar with semantic analysis
    grammar_rules = """
    % Grammar with semantic representation
    
    % sentence(Sem) --> noun_phrase(NP), verb_phrase(VP), {combine(NP, VP, Sem)}.
    sentence --> noun_phrase, verb_phrase.
    
    % Noun phrases with number agreement
    noun_phrase --> determiner, adjective, noun.
    noun_phrase --> determiner, noun.
    noun_phrase --> proper_noun.
    
    % Verb phrases
    verb_phrase --> verb, noun_phrase.
    verb_phrase --> verb, preposition, noun_phrase.
    verb_phrase --> verb.
    
    % Prepositional phrases
    prep_phrase --> preposition, noun_phrase.
    
    % Lexicon
    determiner --> [the].
    determiner --> [a].
    determiner --> [an].
    
    adjective --> [big].
    adjective --> [small].
    adjective --> [red].
    adjective --> [hungry].
    
    noun --> [cat].
    noun --> [dog].
    noun --> [mouse].
    noun --> [bird].
    noun --> [fish].
    noun --> [garden].
    
    proper_noun --> [john].
    proper_noun --> [mary].
    
    verb --> [chases].
    verb --> [eats].
    verb --> [sees].
    verb --> [runs].
    verb --> [sleeps].
    
    preposition --> [in].
    preposition --> [on].
    preposition --> [under].
    preposition --> [with].
    """.strip()
    
    for line in grammar_rules.split('\n'):
        line = line.strip()
        if line and not line.startswith('%'):
            db.add_dcg_rule(line)
    
    return db


# REPL for testing
def main():
    """Interactive DCG parser REPL."""
    print("-" * 50)
    print("Natural Language Parser with DCG Support")
    print("-" * 50)
    print()
    print("Commands:")
    print("  parse <sentence>  - Parse a sentence")
    print("  add <dcg_rule>    - Add a new DCG rule")
    print("  show              - Show database")
    print("  demo              - Run demonstration")
    print("  quit              - Exit")
    print("-" * 50)
    
    # Create database with example grammar
    db = create_advanced_grammar()
    
    while True:
        try:
            line = input("\n> ").strip()
            
            if not line:
                continue
            
            if line in ["quit", "exit", "q"]:
                print("Bye!")
                break
            
            if line == "demo":
                # Run demonstration
                print("\nDemonstration - Parsing English Sentences")
                print("-" * 60)
                
                test_sentences = [
                    ["the", "cat", "chases", "the", "mouse"],
                    ["a", "dog", "eats"],
                    ["john", "sees", "the", "big", "bird"],
                    ["the", "hungry", "cat", "chases", "a", "mouse"],
                    ["mary", "sleeps"],
                    ["the", "dog", "runs", "in", "the", "garden"],
                ]
                
                for sentence in test_sentences:
                    print(f"\nSentence: {' '.join(sentence)}")
                    solutions = db.parse_sentence("sentence", sentence)
                    
                    if solutions:
                        print(f"  ✓ Valid ({len(solutions)} parse(s))")
                    else:
                        print("  ✗ Invalid")
                
                continue
            
            if line == "show":
                print(f"\nDatabase has {len(db.clauses)} clauses:")
                for i, (head, body) in enumerate(db.clauses[:20]):  # Show first 20
                    if body:
                        body_str = ', '.join(str(g) for g in body)
                        print(f"  {head} :- {body_str}.")
                    else:
                        print(f"  {head}.")
                if len(db.clauses) > 20:
                    print(f"  ... and {len(db.clauses) - 20} more")
                continue
            
            if line.startswith("parse "):
                sentence_str = line[6:].strip()
                words = sentence_str.lower().split()
                
                print(f"Parsing: {words}")
                solutions = db.parse_sentence("sentence", words)
                
                if solutions:
                    print(f"✓ Valid sentence! ({len(solutions)} parse(s) found)")
                    for i, sol in enumerate(solutions[:3]):  # Show first 3
                        print(f"  Parse {i+1}: {format_solution(sol, [])}")
                else:
                    print("✗ Invalid sentence")
                
                continue
            
            if line.startswith("add "):
                rule_str = line[4:].strip()
                if db.add_dcg_rule(rule_str):
                    print("✓ Rule added")
                else:
                    print("✗ Failed to add rule")
                continue
            
            print("Unknown command. Type 'demo' for a demonstration.")
        
        except KeyboardInterrupt:
            print("\nInterrupted")
            break
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
