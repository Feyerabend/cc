
## Attribute Grammar Parser

This project implements a recursive descent parser in Python based on an attribute
grammar for a simplified expression language. To reduce complexity, features like
member access (`.`), array indexing (`[]`), bitwise operators (`&`, `|`, `^`), and
modulus (`%`) have been removed. Float literals have been added, and type attributes
("int" or "float") are now computed with inherited attributes for a type environment
(symbol table mapping variables to types) and synthesized attributes for expression
types.

- Identifiers (with pre-defined types in the environment)
- Integer and float literals
- Binary operators: `+`, `-`, `*`, `/`
- Unary minus
- Assignment `=` (left side must be an identifier; type-checked for compatibility)
- Parentheses for grouping

The parser builds an Abstract Syntax Tree (AST) and computes types during parsing. Type rules:
- Operations: Result is "float" if any operand is "float" or if division (`/`); otherwise "int".
- Assignment: Checks compatibility (e.g., "float" = "int" is allowed, but "int" = "float" is not).

This demonstrates inherited attributes (environment passed top-down) and synthesised
attributes (types computed bottom-up), aligning with the concept of attribute grammars
for semantic analysis like type checking.


### Attribute Grammar Specification

This attribute grammar has been simplified by removing postfix operations and some operators.
It now includes inherited attributes (`inh_env`: dict of variable names to types "int" or "float")
and synthesized attributes (`.ast`: AST node, `.syn_type`: "int" or "float"). The environment
is fixed (passed at the root) and not updated; assignments only check types against the environment.
Errors are raised for undefined variables or type mismatches.

Operator precedence: assignment lowest (right-associative), additive (+, -) medium (left-associative),
multiplicative (*, /) high (left-associative), unary minus highest.


#### Nonterminals

- `E`: Expression
- `A`: Additive expression
- `S`: Signed term
- `T`: Term
- `P`: Primary
- `AddOp`: Additive operator
- `MultOp`: Multiplicative operator


#### Productions and Semantic Rules

All nonterminals have attributes: `inh_env` (inherited), `syn_type` (synthesized), `ast` (synthesized AST node).

```
1. `E → A`
   `A.inh_env = E.inh_env`
   `E.ast = A.ast`
   `E.syn_type = A.syn_type`

2. `E → A = E1`
   `A.inh_env = E.inh_env`
   `E1.inh_env = E.inh_env`
      Check: A.ast.type must be 'IDENT' (lvalue restriction)
      Check: compatible(A.syn_type, E1.syn_type) or error
   `E.ast = nnode('ASSIGNMENT')`
   `E.ast.var = A.ast`
   `E.ast.node1 = E1.ast`
   `E.ast.data_type = E1.syn_type`
   `E.syn_type = E1.syn_type`

3. `A → S`
   `S.inh_env = A.inh_env`
   `A.ast = S.ast`
   `A.syn_type = S.syn_type`

4. `A → A1 AddOp S`
   `A1.inh_env = A.inh_env`
   `S.inh_env = A.inh_env`
   `A.ast = nnode(AddOp.type)`
   `A.ast.node1 = A1.ast`
   `A.ast.node2 = S.ast`
   `A.syn_type = "float" if "float" in (A1.syn_type, S.syn_type) else "int"`
   `A.ast.data_type = A.syn_type`

5. `AddOp → +`
   `AddOp.type = 'ADD'`

6. `AddOp → -`
   `AddOp.type = 'SUB'`

7. `S → T`
   `T.inh_env = S.inh_env`
   `S.ast = T.ast`
   `S.syn_type = T.syn_type`

8. `S → - T`
   `T.inh_env = S.inh_env`
   `S.ast = nnode('UMINUS')`
   `S.ast.node1 = T.ast`
   `S.syn_type = T.syn_type`
   `S.ast.data_type = S.syn_type`

9. `T → P`
   `P.inh_env = T.inh_env`
   `T.ast = P.ast`
   `T.syn_type = P.syn_type`

10. `T → T1 MultOp P`
    `T1.inh_env = T.inh_env`
    `P.inh_env = T.inh_env`
    `T.ast = nnode(MultOp.type)`
    `T.ast.node1 = T1.ast`
    `T.ast.node2 = P.ast`
    `T.syn_type = "float" if MultOp.type == 'DIVIDE' or "float" in (T1.syn_type, P.syn_type) else "int"`
    `T.ast.data_type = T.syn_type`

11. `MultOp → *`
    `MultOp.type = 'MULTIPLY'`

12. `MultOp → /`
    `MultOp.type = 'DIVIDE'`

13. `P → IDENT`
    `P.syn_type = P.inh_env[IDENT.lexval]` (error if undefined)
    `P.ast = nnode('IDENT')`
    `P.ast.name = IDENT.lexval`
    `P.ast.data_type = P.syn_type`

14. `P → INT`
    `P.syn_type = "int"`
    `P.ast = nnode('NUMBER')`
    `P.ast.value = int(INT.lexval)`
    `P.ast.data_type = "int"`

15. `P → FLOAT`
    `P.syn_type = "float"`
    `P.ast = nnode('NUMBER')`
    `P.ast.value = float(FLOAT.lexval)`
    `P.ast.data_type = "float"`

16. `P → ( E )`
    `E.inh_env = P.inh_env`
    `P.ast = E.ast`
    `P.syn_type = E.syn_type`
```

##### Notes

- The grammar uses left-recursive productions for left-associative operators.
- The root is `E`, parsed with an initial `inh_env`. Produces `E.ast` (with
  `data_type` fields) as the final AST.
- Type compatibility for assignment: "int" = "int", "float" = "float",
  "float" = "int" (promotion allowed), but not "int" = "float".
- No environment updates; assumes pre-defined variable types.
- To evaluate: Pass `inh_env` top-down; compute `syn_type` and `ast` bottom-up,
  with checks.



#### Attribute Grammar Integration

This version introduces inherited attributes (`inh_env`) to demonstrate top-down
flow (e.g., looking up variable types). Synthesized attributes (`syn_type`, `ast`)
handle bottom-up computation (e.g., inferring operation result types). This extends
the previous [02](./../02/) version for basic type checking during parsing.

- *Inherited Attributes*: `inh_env` flows top-down to provide context for leaves (identifiers).
- *Synthesized Attributes*: Types and AST nodes flow bottom-up, with unification-like rules for operators.
- *Explicit Mapping*: Code comments reference productions; semantic actions (type computation, checks) are embedded.
- *Advantages*: Embeds semantics (type checking) in parsing, beyond syntax validation.


### Project Ideas

Limitations:
- Fixed environment (no declarations or updates).
- Basic types ("int", "float") only;
  no further inference or coercion beyond defined rules.
- Integers and floats only; no other literals.
- No error recovery.

Future Improvements:
- Add declarations to update the environment
  (threading updated env as synthesised attribute).
- Support more types or advanced checking.
- Integrate an interpreter to evaluate the AST with types.

This serves as an educational example of attribute grammars
with both *inherited* and *synthesised* attributes.

