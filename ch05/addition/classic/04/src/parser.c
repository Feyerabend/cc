#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "tokens.h"
#include "lexer.h"
#include "ast.h"
#include "parser.h"
#include "util.h"

#define TRUE 1
#define FALSE 0


Symbol symbol;
char buf[MAX_SYM_LEN];

void nextSymbol() {
    Token token = nextToken();
    // skip
    while (token.type == NOP || token.type == ENDOFLINE) {
        token = nextToken();
    }
    // transfer to local use
    symbol = token.type;
    strncpy(buf, token.value, MAX_SYM_LEN - 1);
    buf[MAX_SYM_LEN - 1] = '\0';
    printsymbol(symbol, buf); // DEBUG
}

void error(const char msg[]) {
    printf("Error: %s (buffer: \"%s\")\n", msg, buf);

    exit(EXIT_FAILURE);
}

void warning(const char msg[]) {
    printf("Warning: %s (buffer: \"%s\")\n", msg, buf);
}

int accept(Symbol s) {
    if (symbol == s) {
        nextSymbol();
        return TRUE;
    }
    return FALSE;
}

int expect(Symbol s) {
    if (accept(s)) {
        return TRUE;
    }
    error("expected symbol: ");
    printsymbol(s, buf);
    return FALSE;
}

int recognize(Symbol s) {
    return symbol == s ? TRUE : FALSE;
}


// --- parsing ---

ASTNode *program();
ASTNode *block();
ASTNode *statement();
ASTNode *condition();
ASTNode *expression();
ASTNode *term();
ASTNode *factor();


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

ASTNode *term() {
    ASTNode *node = factor();
    while (symbol == TIMES || symbol == SLASH) {
        char *op = strdup(symbol == TIMES ? "*" : "/");
        nextSymbol();
        ASTNode *opNode = createNode(NODE_TERM, op);
        addChild(opNode, node);          // left child is the current term
        addChild(opNode, factor());      // right child is the next factor
        node = opNode;                   // update node to the new operator node
    }
    return node;
}

ASTNode *expression() {
    ASTNode *node = createNode(NODE_EXPRESSION, NULL);
    if (symbol == PLUS || symbol == MINUS) {
        addChild(node, createNode(NODE_OPERATOR, symbol == PLUS ? "+" : "-"));
        nextSymbol();
    }
    addChild(node, term());
    while (symbol == PLUS || symbol == MINUS) {
        ASTNode *opNode = createNode(NODE_OPERATOR, symbol == PLUS ? "+" : "-");
        nextSymbol();
        addChild(opNode, node);
        addChild(opNode, term());
        node = opNode;
    }
    return node;
}

ASTNode *condition() {
    if (accept(LPAREN)) { // enforce parentheses
        ASTNode *leftExpr = expression();
        if (symbol == EQL || symbol == NEQ || symbol == LSS || symbol == LEQ || symbol == GTR || symbol == GEQ) {
            ASTNode *node = createNode(NODE_CONDITION, symbolToString(symbol));
            nextSymbol();
            addChild(node, leftExpr);        // left-hand side expression
            addChild(node, expression());    // right-hand side expression
            expect(RPAREN);
            return node;
        }
    }
    error("condition: syntax error");
    nextSymbol();
    return NULL;
}

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
        ASTNode *blockNode = createNode(NODE_BLOCK, NULL);
        do {
            addChild(blockNode, statement());
            if (!accept(SEMICOLON)) {
                break;  // allow for optional final semicolon
            }
        } while (symbol != ENDSYM && symbol != ENDOFFILE);
        if (!accept(ENDSYM)) {
            error("statement: expected END");
        }
        return blockNode;
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

ASTNode *program() {
    resetTokens();
    nextSymbol();
    ASTNode *programNode = createNode(NODE_PROGRAM, NULL);
    addChild(programNode, block());
    expect(PERIOD);
    return programNode;
}