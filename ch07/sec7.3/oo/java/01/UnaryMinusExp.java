
// UnaryMinusExp.java
// Set Lonnert, 1999

public class UnaryMinusExp extends NumberExp {
  NumberExp op1;
  public UnaryMinusExp(NumberExp _op1) {
    op1 = _op1;
  }
  int evaluate(Context _rho) {
    return (-op1.evaluate(_rho));
  }
  NumberExp copy() {
    return new UnaryMinusExp(op1.copy());
  }
  NumberExp replace(String _name, NumberExp _number) {
    return new UnaryMinusExp(
      op1.replace(_name, _number));
  }
  public String toString() {
    return "(~ " + op1.toString() + ")";
  }
}
