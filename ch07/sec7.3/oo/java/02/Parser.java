
// Parser.java
// Set Lonnert, 1999

import java.io.EOFException;

public class Parser {
  Lexer lex;

  Parser() { }

  class SyntaxErrorException extends Exception {
    SyntaxErrorException() { }
    SyntaxErrorException(String s) {
      super(s);
    }
  }

  void match(int _t)
  throws SyntaxErrorException {
    Token tok = lex.current_token();
    try {
      lex.next_token();
    } catch (EOFException e) { return; }
    if (tok.token != _t) {
      throw new SyntaxErrorException(
        "Expected '" + new Token(_t).toString() + "'"
          + ", found '" + tok.toString() + "'");
    }
  }

  NumberExp parse(Lexer _l)
  throws SyntaxErrorException {
    lex = _l;
    return parseExpr();
  }

  NumberExp parseExpr()
  throws SyntaxErrorException {
    Token tok = lex.current_token();
    if (tok.token == Symbol.IDENT) {
      match(Symbol.IDENT);
      VariableExp var = new VariableExp(tok.name);
      return (NumberExp) var;
    } else if (tok.token == Symbol.NUMBER) {
      match(Symbol.NUMBER);
      IntegerExp number = new IntegerExp(tok.value);
      return (NumberExp) number;
    } else if (tok.token == Symbol.UMINUS) {
      match(Symbol.UMINUS);
      NumberExp expr1 = parseExpr();
      UnaryMinusExp uminus = new UnaryMinusExp(expr1);
      return (NumberExp) uminus;
    } else if (tok.token == Symbol.PLUS) {
      match(Symbol.PLUS);
      NumberExp expr1 = parseExpr();
      NumberExp expr2 = parseExpr();
      PlusExp plus = new PlusExp(expr1, expr2);
      return (PlusExp) plus;
    } else if (tok.token == Symbol.MINUS) {
      match(Symbol.MINUS);
      NumberExp expr1 = parseExpr();
      NumberExp expr2 = parseExpr();
      MinusExp minus = new MinusExp(expr1, expr2);
      return (NumberExp) minus;
    } else if (tok.token == Symbol.MULTIPLY) {
      match(Symbol.MULTIPLY);
      NumberExp expr1 = parseExpr();
      NumberExp expr2 = parseExpr();
      MultiplyExp mult = new MultiplyExp(expr1, expr2);
      return (NumberExp) mult;
    } else if (tok.token == Symbol.DIVIDE) {
      match(Symbol.DIVIDE);
      NumberExp expr1 = parseExpr();
      NumberExp expr2 = parseExpr();
      DivideExp div = new DivideExp(expr1, expr2);
      return (NumberExp) div;
    } else if (tok.token == Symbol.MODULO) {
      match(Symbol.MODULO);
      NumberExp expr1 = parseExpr();
      NumberExp expr2 = parseExpr();
      ModuloExp mod = new ModuloExp(expr1, expr2);
      return (NumberExp) mod;
    } else if (tok.token == Symbol.LPAREN) {
      match(Symbol.LPAREN);
      NumberExp expr = parseExpr();
      match(Symbol.RPAREN);
      return expr;
    }
    throw new SyntaxErrorException(
      "Internal error: Unrecognized term");
  }
}
