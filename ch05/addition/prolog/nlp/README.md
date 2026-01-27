
## Natural Language Parser for Prolog

Natural language parsing has been a main sector in the AI field for a long time.
A Prolog-based natural language parser using *Definite Clause Grammars (DCG)* notation.
This system extends the Mini-Prolog interpreter with DCG support, making it easy to
write and experiment with natural language grammars--but you are advised to improve on the
existing `mprolog.py`first, however.

This parser demonstrates how Prolog's logical foundation makes it particularly well-suited
for natural language processing, as it has been done. DCGs provide a declarative, elegant
way to specify grammars while Prolog's unification and backtracking handle the parsing automatically.

- *DCG Notation*: Write grammars using the intuitive `-->` syntax
- *Automatic Transformation*: DCG rules are automatically converted to difference-list predicates
- *Multiple Parses*: Finds all possible parse trees for ambiguous sentences
- *Extensible*: Easy to add new grammar rules and lexicon entries
- *Interactive REPL*: Test grammars interactively


#### What are DCGs?

Definite Clause Grammars (DCGs) are a notation for expressing grammars in Prolog.
They provide a clean, declarative way to specify grammar rules.

A simple DCG rule:
```prolog
sentence --> noun_phrase, verb_phrase.
```

This is automatically transformed into:
```prolog
sentence(S0, S) :- noun_phrase(S0, S1), verb_phrase(S1, S).
```

The transformation uses *difference lists*--a Prolog idiom where the input sentence
is represented as the difference between two lists (what comes in, and what's left over).


#### Core Components

1. *mprolog.py* - The base Prolog interpreter with:
   - Parser combinator-based parser
   - Unification algorithm
   - SLD resolution with backtracking
   - Support for atoms, variables, compounds, and lists

2. *nlp_prolog.py* - DCG extension layer:
   - Parses `-->` DCG syntax
   - Transforms DCG rules to Prolog clauses
   - Provides sentence parsing interface
   - Manages grammar database

3. *nlp_examples.py* - Demonstrations:
   - Arithmetic expression parser
   - Question parser (who, what, where..)
   - Command parser (imperatives)
   - Complex sentences with relative clauses
   - Semantic annotation examples


### Interactive Mode

Run the interactive parser:
```bash
python nlp_prolog.py
```

Commands:
- `parse <sentence>` - Parse a sentence
- `add <dcg_rule>` - Add a new DCG rule
- `show` - Display all grammar rules
- `demo` - Run built-in demonstration
- `quit` - Exit


Examples:
```
> parse the cat chases the mouse
Parsing: ['the', 'cat', 'chases', 'the', 'mouse']
✓ Valid sentence! (1 parse(s) found)

> parse the sleeps cat
Parsing: ['the', 'sleeps', 'cat']
✗ Invalid sentence

> add noun --> [bird].
✓ Rule added

> parse the bird sleeps
Parsing: ['the', 'bird', 'sleeps']
✓ Valid sentence! (1 parse(s) found)
```


Running the examples. To see various grammars:
```bash
python nlp_examples.py
```

This demonstrates:
- Arithmetic expressions: `one plus two times three`
- Questions: `what did alice read`
- Commands: `take the key`
- Complex sentences: `the cat that chased the dog sleeps`



### Grammar Specification

#### Basic Structure

```prolog
% Non-terminals use -->
sentence --> noun_phrase, verb_phrase.

% Terminals in square brackets
noun --> [cat].
noun --> [dog].

% Can have multiple arguments
noun_phrase --> determiner, noun.
noun_phrase --> noun.  % Alternative rule
```

#### Terminal Symbols

Terminal symbols (actual words) are enclosed in square brackets:
```prolog
determiner --> [the].
determiner --> [a].
```

#### Non-terminal Symbols

Non-terminals can call other non-terminals:
```prolog
noun_phrase --> determiner, adjective, noun.
verb_phrase --> verb, noun_phrase.
```

#### Prolog Goals in Grammars

You can embed Prolog goals using braces `{...}`:
```prolog
sentence(Sem) --> noun_phrase(NP), verb_phrase(VP), {combine(NP, VP, Sem)}.
```

This allows semantic processing during parsing.


### How It Works

#### DCG Transformation

Input DCG rule:
```prolog
sentence --> noun_phrase, verb_phrase.
```

Transformed to:
```prolog
sentence(S0, S) :- 
    noun_phrase(S0, S1), 
    verb_phrase(S1, S).
```

Terminal rule:
```prolog
noun --> [cat].
```

Transformed to:
```prolog
noun([cat|S], S).
```

#### Difference Lists

The key insight is *difference lists*.
Instead of consuming and returning lists,
predicates take two arguments:
- `S0` - the input list
- `S` - what's left after parsing

This is more efficient than list concatenation
and naturally handles left-to-right parsing.


#### Example Trace

Parsing "the cat sleeps":
```
sentence([the, cat, sleeps], [])
  ├─ noun_phrase([the, cat, sleeps], [sleeps])
  │    ├─ determiner([the, cat, sleeps], [cat, sleeps])
  │    └─ noun([cat, sleeps], [sleeps])
  └─ verb_phrase([sleeps], [])
       └─ verb([sleeps], [])
```


### Extending the Parser

#### Adding Vocabulary

```python
db.add_dcg_rule("noun --> [bird].")
db.add_dcg_rule("verb --> [flies].")
```

#### Adding Grammar Rules

```python
# Add prepositional phrases
db.add_dcg_rule("sentence --> noun_phrase, verb_phrase, prep_phrase.")
db.add_dcg_rule("prep_phrase --> preposition, noun_phrase.")
db.add_dcg_rule("preposition --> [in].")
db.add_dcg_rule("preposition --> [on].")
```

#### Creating Custom Grammars

```python
from nlp_prolog import DCGDatabase, Atom, Compound, Variable

db = DCGDatabase()

# Add your grammar
grammar = """
sentence --> greeting, name.
greeting --> [hello].
greeting --> [hi].
name --> [world].
name --> [alice].
""".strip()

for line in grammar.split('\n'):
    if line.strip():
        db.add_dcg_rule(line)

# Parse a sentence
words = ["hello", "alice"]
solutions = db.parse_sentence("sentence", words)

if solutions:
    print("Valid!")
else:
    print("Invalid!")
```


### Example Grammars

#### 1. Simple English

```prolog
sentence --> noun_phrase, verb_phrase.
noun_phrase --> determiner, noun.
verb_phrase --> verb, noun_phrase.

determiner --> [the].
noun --> [cat].
verb --> [chases].
```

Accepts: "the cat chases the mouse"


#### 2. Arithmetic Expressions

```prolog
expr --> term, [plus], expr.
expr --> term.
term --> factor, [times], term.
term --> factor.
factor --> [lparen], expr, [rparen].
factor --> number.
number --> [one].
number --> [two].
```

Accepts: "(one plus two) times three"


#### 3. Questions

```prolog
question --> wh_word, aux, noun_phrase, verb_phrase.
wh_word --> [what].
wh_word --> [who].
aux --> [does].
noun_phrase --> [alice].
verb_phrase --> [read].
```

Accepts: "what does alice read"


### Advanced Features

#### Ambiguity Resolution

The parser try to find all possible parses for ambiguous sentences:

```prolog
% This grammar is ambiguous
noun_phrase --> determiner, noun_phrase.
noun_phrase --> adjective, noun_phrase.
noun_phrase --> noun.
```

For "the big cat", it finds multiple parse trees.


#### Semantic Annotations

DCGs can build semantic representations:

```prolog
sentence(sem(NP, VP)) --> noun_phrase(NP), verb_phrase(VP).
noun_phrase(np(Det, N)) --> determiner(Det), noun(N).
```

This builds structured representations during parsing.


#### Parametric Rules

Rules can have arguments to pass information:

```prolog
% Agreement checking
noun_phrase(Number) --> determiner(Number), noun(Number).
determiner(singular) --> [the].
noun(singular) --> [cat].
noun(plural) --> [cats].
```


### Comparison to Other Approaches

#### Advantages of Prolog/DCG

1. *Declarative*: Describe what valid sentences are, not how to parse them
2. *Bidirectional*: Can generate sentences as well as parse them
3. *Natural backtracking*: Handles ambiguity automatically
4. *Composable*: Easy to combine and extend grammars
5. *Pattern matching*: Unification is more powerful than string matching

#### When to Use This Approach

- Prototyping grammars quickly
- Educational purposes (learning NLP/parsing)
- Small to medium grammars
- When you need all parse trees
- Logic-based semantic processing

### When NOT to Use This Approach, And Better Use Alternatives

- Production NLP systems (use spaCy, NLTK, etc.)
- Statistical/ML approaches needed
- Very large grammars (10,000+ rules)
- Performance-critical applications


### Technical Details

#### Parser Combinators

The base Prolog interpreter uses parser combinators for parsing:
- Compositional parsing functions
- Type-safe in spirit
- Functional programming style

#### Unification Algorithm

Standard Robinson unification with occurs check:
```python
unify(term1, term2, environment) -> environment | fail
```

#### SLD Resolution

Selection rule: leftmost goal first
Backtracking: chronological backtracking through choice points

#### Difference Lists

Represented as pairs of list variables:
```prolog
append([], L, L).
append([H|T], L, [H|R]) :- append(T, L, R).

% Becomes more efficient with difference lists:
append(X-Y, Y-Z, X-Z).  % Constant time!
```

### Limitations

1. *No Left Recursion*: DCGs can't handle left-recursive rules directly
   ```prolog
   % This will loop infinitely:
   noun_phrase --> noun_phrase, adjective.
   ```

2. *Performance*: Not optimized for large-scale parsing

3. *No Probabilities*: Can't model statistical aspects of language

4. *Simple Feature Passing*: More complex feature structures require extensions


### Future Enhancements

Possible extensions:
- Chart parsing for efficiency
- Feature structures for agreement
- Semantic composition
- Parse tree visualisation
- Left-recursion handling
- Tabling/memoization
- Integration with word embeddings

Ideas for improvement of existing:
- Add more example grammars
- Implement feature structures
- Add semantic interpretation
- Create additional visualisation tools
- Performance optimisations


#### Related Systems

Go further with:
- SWI-Prolog DCG library (the gold standard)
- Grammatical Framework (GF)
- NLTK's Chart Parsers
- [Earley](./../../parsers/earley/) parsers


