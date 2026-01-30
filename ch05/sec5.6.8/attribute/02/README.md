
## Attribute Grammar Parser

This project implements a recursive descent parser in Python based on an
attribute grammar for a simple expression language.

- Identifiers and numbers
- Binary operators: `+`, `-`, `*`, `/`, `%`, `&` (AND), `|` (OR), `^` (XOR)
- Unary minus
- Assignment `=`
- Member access `.`
- Array indexing `[]`
- Parentheses for grouping

The parser builds an Abstract Syntax Tree (AST) as it parses, which corresponds
to the synthesised attributes in the attribute grammar. This demonstrates how
attribute grammars extend context-free grammars by attaching semantic rules (here,
AST construction) to productions.


### Attribute Grammar Specification

This attribute grammar formalises the syntax and semantics of the parser, with
adjustments to ensure proper operator precedence and associativity. Specifically,
assignment (`=`) has the lowest precedence (lower than additive operators like
`+`, `-`, `|`, `^`) and is right-associative. Additive operators are left-associative
with medium precedence. Multiplicative operators (`*`, `/`, `%`, `&`) are
left-associative with high precedence. Unary minus has the highest precedence. 
ember access (`.`) and array indexing (`[ ]`) are left-associative postfix operators
with highest precedence (tighter than unary minus).

All attributes are synthesized (computed bottom-up). The primary attribute is
`.ast` for each nonterminal, representing the AST node (as defined in the provided
`ASTNode` class). Terminals like `IDENT` have a `.lexval` attribute (string value,
equivalent to `buf`), and `NUMBER` has a `.numval` attribute (integer value, equivalent
to `int(buf)`). Operators have a `.type` attribute for the operation name.


#### Nonterminals

- `E`: Expression
- `A`: Additive expression
- `S`: Signed term
- `T`: Term
- `F`: Factor
- `P`: Primary
- `AddOp`: Additive operator
- `MultOp`: Multiplicative operator


#### Productions and Semantic Rules

```
1. `E → A`  
   `E.ast = A.ast`

2. `E → A = E1`  
   `E.ast = nnode('ASSIGNMENT')`  
   `E.ast.var = A.ast`  
   `E.ast.node1 = E1.ast`

3. `A → S`  
   `A.ast = S.ast`

4. `A → A1 AddOp T`  
   `A.ast = nnode(AddOp.type)`  
   `A.ast.node1 = A1.ast`  
   `A.ast.node2 = T.ast`

5. `AddOp → +`  
   `AddOp.type = 'ADD'`

6. `AddOp → -`  
   `AddOp.type = 'SUB'`

7. `AddOp → |`  
   `AddOp.type = 'OR'`

8. `AddOp → ^`  
   `AddOp.type = 'XOR'`

9. `S → T`  
   `S.ast = T.ast`

10. `S → - T`  
    `S.ast = nnode('UMINUS')`  
    `S.ast.node1 = T.ast`

11. `T → F`  
    `T.ast = F.ast`

12. `T → T1 MultOp F`  
    `T.ast = nnode(MultOp.type)`  
    `T.ast.node1 = T1.ast`  
    `T.ast.node2 = F.ast`

13. `MultOp → *`  
    `MultOp.type = 'MULTIPLY'`

14. `MultOp → /`  
    `MultOp.type = 'DIVIDE'`

15. `MultOp → %`  
    `MultOp.type = 'MOD'`

16. `MultOp → &`  
    `MultOp.type = 'AND'`

17. `F → P`  
    `F.ast = P.ast`

18. `F → F1 . IDENT`  
    `F.ast = nnode('MEMBER_ACCESS')`  
    `F.ast.node1 = F1.ast`  
    `F.ast.member = IDENT.lexval`

19. `F → F1 [ E ]`  
    `F.ast = nnode('ARRAY_ACCESS')`  
    `F.ast.node1 = F1.ast`  
    `F.ast.index = E.ast`

20. `P → IDENT`  
    `P.ast = nnode('IDENT')`  
    `P.ast.name = IDENT.lexval`

21. `P → NUMBER`  
    `P.ast = nnode('NUMBER')`  
    `P.ast.value = NUMBER.numval`

22. `P → ( E )`  
    `P.ast = E.ast`
```

##### Notes
- The grammar is context-free and uses left-recursive productions for
  left-associative operators (e.g., additive, multiplicative, member access,
  array indexing), which is standard for attribute grammars (though it
  requires careful evaluation ordering, such as L-attributed).
- The root is `E`, and parsing the input produces `E.ast` as the final AST.
- This structure corrects the original parser's placement of assignment checking,
  allowing expressions like `(a + b) = c` (with parentheses) or rejecting invalid
  mixes without error, while properly handling precedence
  (e.g., `a + b = c` parses as `(a + b) = c`).
- No inherited attributes are needed, as all computation flows bottom-up.
- To evaluate, start from terminals and synthesize `.ast` up the parse tree using the rules.


#### Attribute Grammar Integration

Unlike a plain context-free grammar parser (which might just validate syntax),
this parser uses synthesized attributes to compute the AST bottom-up.
Each parsing function corresponds to nonterminals and synthesises an `.ast` attribute:

- *Synthesised Attributes*: All attributes flow bottom-up, building the AST nodes as per the semantic rules.
- *Explicit Mapping*: Comments in the code (e.g., in `parse_E()`, `parse_A()`, etc.)
  reference the attribute grammar productions and explain how the AST is synthesised.
  This highlights semantic actions (e.g., creating specific node types for operations,
  handling associativity) that a basic syntactic parser wouldn't perform.
- *Advantages Over Plain Parsers*:
  - *Semantics Embedded*: The grammar not only recognizes valid strings
    but computes meaningful structures (AST) during parsing.
  - *Precedence and Associativity*: Handled via grammar structure
    (e.g., right-recursive for assignment, left-recursive for operators),
    with attributes ensuring correct node building.
  - *Error Handling*: Raises `SyntaxError` for invalid inputs, providing
    more than just acceptance/rejection.
  - Compared to tools like yacc/ANTLR (which can generate parsers from grammars),
    this manual implementation makes the attribute evaluation explicit and educational.

Full attribute grammar is described above, with productions and semantic rules for AST synthesis.


### Project Ideas

Limitations:
- No type checking or further semantic analysis (e.g., variable resolution).
- Integers only for numbers.
- No floating-point or string literals.
- Assumes valid input without recovery from errors.

Future Improvements:
- Add inherited attributes for more complex semantics (e.g., symbol tables).
- Support more operators or statements.
- Integrate with a code generator or interpreter to evaluate the AST.

This implementation serves as an educational example of attribute grammars in action.
