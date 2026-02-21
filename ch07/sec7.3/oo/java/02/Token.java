
// Token.java
// Set Lonnert, 1999

public class Token {
  String name;
  int value; // int representation
  int token; // type

  Token(int _tok) {
    token = _tok; name = ""; value = 0;
  }
  Token(int _tok, String _n) {
    token = _tok; name = _n; value = 0;
  }
  Token(int _tok, int _val) {
    token = _tok; name = ""; value = _val;
  }
  public String toString() {
    switch (token) {
      case Symbol.IDENT    : return "Identifier"; 
      case Symbol.PLUS     : return "Plus";
      case Symbol.LPAREN   : return "Left bracket"; 
      case Symbol.RPAREN   : return "Right bracket";
      case Symbol.MINUS    : return "Minus";
      case Symbol.MULTIPLY : return "Multiply";
      case Symbol.DIVIDE   : return "Divide";
      case Symbol.NUMBER   : return "Number";
      case Symbol.MODULO   : return "Modulo";
      case Symbol.UMINUS   : return "Unary minus";
      case Symbol.UNKNOWN  : return "Unknown";
      default              : return "";
    }
  }
}
