
## Syntax: Abstract Syntax Tree (AST)

__Build__

```shell
make clean
make
make samples
```

The provided code fragments illustrate the basic structure of a simple *recursive descent parser* for a
language close to PL/0. The parser builds an *Abstract Syntax Tree* (AST) while parsing the program's
input according to the language's grammar.

__View__

In the directory of 'tools' you'll find a HTML-file: ast_json.html. Open the file locally, and search
for the AST representation in the 'ast' folder.


### Parsing

__1. Parser Workflow__

The parser reads the tokenised input and processes it using a series of functions corresponding to
various grammar rules. Each function tries to match a specific pattern in the language's grammar.
If a match is found, the parser consumes the matching token and proceeds. If no match is found,
an error is raised. (A very rudimentary error check.)

Here is the skeleton of the parser in incomplete or pseduo-code:

```c
void factor() {
    if (accept(ident)) {
        ;
    } else if (accept(number)) {
        ;
    } else if (accept(lparen)) {
        expression();
        expect(rparen);
    } else {
        error("factor: syntax error");
        nextsym();
    }
}

void term() {
    factor();
    while (sym == times || sym == slash) {
        nextsym();
        factor();
    }
}

void expression() {
    if (sym == plus || sym == minus)
        nextsym();
    term();
    while (sym == plus || sym == minus) {
        nextsym();
        term();
    }
}

void condition() {
    if (accept(oddsym)) {
        expression();
    } else {
        expression();
        if (sym == eql || sym == neq || sym == lss || sym == leq || sym == gtr || sym == geq) {
            nextsym();
            expression();
        } else {
            error("condition: invalid operator");
            nextsym();
        }
    }
}

void statement() {
    if (accept(ident)) {
        expect(becomes);
        expression();
    } else if (accept(callsym)) {
        expect(ident);
    } else if (accept(beginsym)) {
        do {
            statement();
        } while (accept(semicolon));
        expect(endsym);
    } else if (accept(ifsym)) {
        condition();
        expect(thensym);
        statement();
    } else if (accept(whilesym)) {
        condition();
        expect(dosym);
        statement();
    } else {
        error("statement: syntax error");
        nextsym();
    }
}

void block() {
    if (accept(constsym)) {
        do {
            expect(ident);
            expect(eql);
            expect(number);
        } while (accept(comma));
        expect(semicolon);
    }
    if (accept(varsym)) {
        do {
            expect(ident);
        } while (accept(comma));
        expect(semicolon);
    }
    while (accept(procsym)) {
        expect(ident);
        expect(semicolon);
        block();
        expect(semicolon);
    }
    statement();
}

void program() {
    nextsym();
    block();
    expect(period);
}
```

__2. AST Construction__

Each grammar rule corresponds to creating a node in the abstract syntax tree (AST). This tree represents
the structure of the parsed input, reflecting the program's syntactic structure. Each node in the
tree contains information about the language construct it represents (e.g. expressions, statements,
terms, etc.).

__3. Expected Output__

The parser is expected to construct an AST, where each node represents a construct in the source
language. The program's top-level node is a NODE_PROGRAM, and this root node's child would be a
NODE_BLOCK, which holds the core of the program (e.g. variable declarations, statements, and
procedure calls).


### Adding Context and Completing the Code

The provided snippets show functions that handle individual components of the grammar, such as
parsing factors, terms, expressions, statements, conditions, and blocks. The parser builds the
AST incrementally, starting from the root and breaking the input down into smaller components.


#### Main Parser Functions and AST Construction


__program()__

This function is the entry point for parsing the program. It initializes the parsing process and
creates the root of the AST.

```c
ASTNode *program() {
    resetTokens();              // reset token buffer (e.g. prepare lexer)
    nextSymbol();               // move to the next symbol (token)
    
    ASTNode *programNode = createNode(NODE_PROGRAM, NULL);  // create the root AST node (program)
    
    addChild(programNode, block());  // parse the block (which includes statements, variable declarations, etc.)
    
    expect(PERIOD);              // expect the period at the end of the program
    return programNode;          // return the constructed AST for the program
}
```

__block()__

A block is a key structure in the language (similar to a function or procedure scope).
It can contain constant declarations, variable declarations, procedure declarations,
and a list of statements.

```c
ASTNode *block() {
    ASTNode *blockNode = createNode(NODE_BLOCK, NULL);
    if (accept(CONSTSYM)) {
        do {
            ASTNode *constNode = createNode(NODE_CONST_DECL, strdup(buf));
            expect(IDENT);
            expect(EQL);
            addChild(constNode, createNode(NODE_NUMBER, strdup(buf)));
            expect(NUMBER);
            addChild(blockNode, constNode);
        } while (accept(COMMA));
        expect(SEMICOLON);
    }
    if (accept(VARSYM)) {
        do {
            addChild(blockNode, createNode(NODE_VAR_DECL, strdup(buf)));
            expect(IDENT);
        } while (accept(COMMA));
        expect(SEMICOLON);
    }
    while (accept(PROCSYM)) {
        ASTNode *procNode = createNode(NODE_PROC_DECL, strdup(buf));
        expect(IDENT);
        expect(SEMICOLON);
        addChild(procNode, block());
        addChild(blockNode, procNode);
        expect(SEMICOLON);
    }
    addChild(blockNode, statement());
    return blockNode;
}
```


__statement()__

A statement is an action that the program performs, such as assignments, calls, conditionals, and loops.

```c
ASTNode *statement() {
    if (recognize(IDENT)) {
        ASTNode *assignNode = createNode(NODE_ASSIGNMENT, strdup(buf));
        nextSymbol();
        expect(BECOMES);
        addChild(assignNode, expression());
        return assignNode;
    } else if (accept(CALLSYM)) {
        ASTNode *callNode = createNode(NODE_CALL, strdup(buf));
        expect(IDENT);
        return callNode;
    } else if (accept(BEGINSYM)) {
        ASTNode *beginNode = createNode(NODE_BEGIN, NULL);
        do {
            addChild(beginNode, statement());   // *HACK* C-like termination 'begin s1; s2; end'
            if (!accept(SEMICOLON)) {           // rather that Pascal separation 'begin s1 ; s2 end'
                // warning("statement: missing SEMICOLON");
                break;
            }
        } while (symbol != ENDSYM && symbol != ENDOFFILE);
        if (!accept(ENDSYM)) {
            error("statement: expected END");
        }
        return beginNode;
    } else if (accept(IFSYM)) {
        ASTNode *ifNode = createNode(NODE_IF, NULL);
        addChild(ifNode, condition());
        expect(THENSYM);
        addChild(ifNode, statement());
        return ifNode;
    } else if (accept(WHILESYM)) {
        ASTNode *whileNode = createNode(NODE_WHILE, NULL);
        addChild(whileNode, condition());
        expect(DOSYM);
        addChild(whileNode, statement());
        return whileNode;
    } else {
        error("statement: syntax error");
        nextSymbol();
        return NULL;
    }
}
```


__expression() and term()__

These functions handle arithmetic expressions and their components (like terms and factors).

```c
ASTNode *expression() {
    ASTNode *exprNode = createNode(NODE_EXPRESSION, NULL);
    
    if (sym == PLUS || sym == MINUS) {
        nextSymbol();  // handle unary plus or minus
    }
    
    exprNode->children.push_back(term());  // start with a term
    
    // continue with additional terms for the expression (addition or subtraction)
    while (sym == PLUS || sym == MINUS) {
        nextSymbol();
        exprNode->children.push_back(term());
    }
    
    return exprNode;
}

ASTNode *term() {
    ASTNode *termNode = createNode(NODE_TERM, NULL);
    termNode->children.push_back(factor());  // a term starts with a factor

    // continue with multiplication or division if necessary
    while (sym == TIMES || sym == SLASH) {
        nextSymbol();
        termNode->children.push_back(factor());
    }

    return termNode;
}
```


__factor()__

This function parses the basic building blocks of an expression, like numbers, variables, or sub-expressions in parentheses.

```c
ASTNode *factor() {
    if (recognize(IDENT)) {
        ASTNode *identNode = createNode(NODE_IDENTIFIER, strdup(buf));
        nextSymbol();
        return identNode;
    } else if (recognize(NUMBER)) {
        ASTNode *numberNode = createNode(NODE_NUMBER, strdup(buf));
        nextSymbol();
        return numberNode;
    } else if (accept(LPAREN)) {
        ASTNode *expr = expression();
        expect(RPAREN);
        return expr;
    } else {
        error("factor: syntax error");
        nextSymbol();
        return NULL;
    }
}
```

### AST Nodes
- NODE_PROGRAM: Represents the entire program.
- NODE_BLOCK: Represents a certain part of the program, which can include declarations and statements. Limits the scope.
- NODE_STATEMENT: Represents a single statement, such as an assignment or a function call.
- NODE_EXPRESSION: Represents an expression, including terms and factors.
- NODE_IDENTIFIER: Represents a variable or function identifier.
- NODE_NUMBER: Represents a constant number.
- NODE_CALL: Represents a procedure call.


### Conclusion

This parser, designed with recursive descent, processes the tokens generated from a lexer and
builds an Abstract Syntax Tree (AST) representing the structure of the program. Each function
in the parser corresponds to a specific rule in the grammar, and the tree nodes represent language
constructs like variables, expressions, statements, and blocks. The parser constructs this tree
step-by-step by recursively calling the appropriate parsing functions and building the corresponding
AST nodes.
