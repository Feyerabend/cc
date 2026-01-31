
## Attribute Grammar Concepts

This code qualifies as an implementation of an attribute grammar, or to be more precisely,
a parser that evaluates attributes in a manner consistent with attribute grammar principles.

- *Semantic Rules Attached to Productions*: Attribute grammars extend context-free
  grammars by associating semantic rules with syntactic productions to compute
  attributes during parsing. In this code, the recursive descent parser methods
  (e.g., `expr()`, `term()`, `factor()`, `stmt()`) correspond to productions and
  include embedded semantic actions:

  - In `expr()` and `term()`, it synthesises a dictionary with `"type"` (always "i32" here)
    and `"value"` (computed via constant folding for literals and operators). This is similar
    to the pseudo-grammar example `Expr.type = unify(Expr.type, Term.type)`, where types are
    computed bottom-up based on subexpressions.

  - In `factor()`, for identifiers, it looks up the type from `self.env` (symbol table)
    and assigns a mock value (0). For literals, it directly assigns type and value.

  - In `stmt()`, after parsing the expression, it performs type checking
    (`if expr["type"] != "i32"`) and updates the symbol table
    (`self.env[name] = "i32"`). This attaches semantics
    (type validation and declaration) to the declaration production.

These actions compute and propagate information (types, values) tied directly to the
syntax rules, facilitating analyses like type checking and partial evaluation
(constant folding).


- *Synthesised Attributes*: These flow bottom-up from leaves to root,
  as in the `infer_type` example in the subsection (which computes types
  recursively from subnodes). Here:
  
  - Leaves (e.g., `INT` in `factor()`) synthesise `{"type": "i32", "value": int(tok.value)}`.

  - Operators in `expr()` and `term()` combine child attributes (e.g., adding or multiplying
    `"value"` from left and right subtrees) and propagate a new synthesised attribute upward.

  - This enables constant folding (e.g., `10 + 5` becomes value 15), which is a classic
    use of synthesised attributes for optimisation during parsing.


- *Inherited Attributes*: These flow top-down from parent to children, often for context
  like scope or expected types. Here, the symbol table (`self.env`) acts as a form of inherited context:

  - It's maintained at the parser level (accessible via `self`) and passed implicitly down the recursion stack.

  - In `factor()`, it uses this context to look up variable types/values (inherited from prior declarations).

  - In a more formal attribute grammar, the symbol table could be explicitly threaded as an inherited
    attribute (passed down) and synthesised (updated and returned up). This code approximates that with
    a class-level mutable structure, which is common in practical implementations for simple, single-scope
    languages. It supports "contextual inference" (e.g., ensuring variables are defined before use),
    as mentioned in the subsection.

- *Overall Semantic Analysis During Parsing*: Like the subsection's emphasis on type checking/inference
  (e.g., raising exceptions for mismatches, as in `infer_type`), this parser integrates:

  - Type checking: Enforces "i32" for all expressions and declarations.

  - Name resolution: Checks for undefined variables via `self.env`.

  - Partial evaluation: Computes constant values where possible, though it mocks variable values (0),
    which could be extended for full constant propagation.

This mirrors how languages like OCaml, Haskell, or Rust use attribute-like mechanisms internally.


### Differences and Limitations

- *Informal vs. Formal Specification*: Attribute grammars are typically specified formally
  (e.g., with explicit rules like `Expr.type = unify(...)`). This code embeds the rules
  procedurally in Python, but the structure (computations tied to productions, bottom-up
  synthesis with top-down context) is equivalent in practice. It's not a declarative attribute
  grammar (e.g., no separate AG definition file), but implementations often look like this.

- *Single-Pass Nature*: The parser evaluates attributes in one left-to-right pass, assuming
  declarations precede uses (no forward references). This is L-attributed (suitable for
  recursive descent), aligning with practical attribute grammars.

- *Simplicity*: Only one type ("i32"), no real scopes/nesting, and mock values for variables
  limit it, but the principles hold. It could be extended with more inherited attributes
  (e.g., nested scopes) or synthesised ones (e.g., code generation).

- *Comparison to Subsection Examples*: The `infer_type` function is a post-parse tree walk,
  but this code computes attributes *during parsing* (inline with productions), which is
  more direct to attribute grammar evaluation. The pseudo-rule for addition matches the
  bottom-up type/value computation in `expr()`.


### Demonstration via Execution

To illustrate, running the provided test code produces:

- Output showing constant-folded declarations (e.g., "declare x: i32 = 15" for "10 + 5",
  "declare z: i32 = 13" for "3 * 4 + 1"), demonstrating synthesised value attributes.

- For "x * 2", it outputs "declare y: i32 = 0" (due to mock value), but still checks
  type and resolves "x" via the inherited env.

- Final symbol table: All variables mapped to "i32".

If the code had a type mismatch (e.g., unsupported type) or undefined variable,
it raises errors during parsing, embedding semantic checks.
