
// Lexer.java
// Set Lonnert, 1999

import java.io.EOFException;

public class Lexer {
  static char next_char;
  static Token tok;
  static String input;
  static int next_pos;

  Lexer(String _i) {
    input = _i;
    next_pos = 0;
  }

  static void error(String _s) {
    throw new Lexer.AnalysisErrorException(_s);
  }

  static class AnalysisErrorException extends RuntimeException {
    AnalysisErrorException() { }
    AnalysisErrorException(String s) {
      super(s);
    }
  }

  static void advance()
  throws EOFException { 
    if (next_pos < input.length()) {
      next_char = input.charAt(next_pos);
    } else {
      throw new EOFException();
    }
    ++next_pos;
  }

  static void init() {
    try {
      advance();
      next_token();
    } catch (EOFException e) {
      error("No entry");
    }
  }

  static Token current_token() {
    return tok;
  }

  static void consumeWhitespace() {
    while (Character.isWhitespace(next_char)) {
      try { advance(); }
      catch (EOFException e) { return; }
    }
  }

  static Token next_token()
  throws EOFException {
    consumeWhitespace();
    if (Character.isLetter(next_char)) {
      String identifier = "";
      do {
        identifier += next_char;
        advance();
      } while (Character.isLetterOrDigit(next_char));
      tok = new Token(Symbol.IDENT, identifier);
    } else if (Character.isDigit(next_char)) {
      String number = "";
      do {
        number += next_char;
        advance();
      } while (Character.isDigit(next_char));
      try {
        int i = Integer.parseInt(number);
        tok = new Token(Symbol.NUMBER, i);
      } catch (NumberFormatException e) {
        error("Non-valid integer: " + number);
      }
    } else {
      switch (next_char) {
        case '~': advance(); tok = new Token(Symbol.UMINUS);   break;
        case '+': advance(); tok = new Token(Symbol.PLUS);     break;
        case '-': advance(); tok = new Token(Symbol.MINUS);    break;
        case '*': advance(); tok = new Token(Symbol.MULTIPLY); break;
        case '/': advance(); tok = new Token(Symbol.DIVIDE);   break;
        case '%': advance(); tok = new Token(Symbol.MODULO);   break;
        case '(': advance(); tok = new Token(Symbol.LPAREN);   break;
        case ')': advance(); tok = new Token(Symbol.RPAREN);   break;
        default : advance(); tok = new Token(Symbol.UNKNOWN);  break;
      }
    }
    return tok;
  }
}
