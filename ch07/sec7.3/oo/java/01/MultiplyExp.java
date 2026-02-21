
// MultiplyExp.java
// Set Lonnert, 1999

public class MultiplyExp extends NumberExp {
  NumberExp op1, op2;
  public MultiplyExp(NumberExp _op1, NumberExp _op2) {
    op1 = _op1;
    op2 = _op2;
  }
  int evaluate(Context _rho) {
    return (op1.evaluate(_rho) * op2.evaluate(_rho));
  }
  NumberExp copy() {
    return new MultiplyExp(op1.copy(), op2.copy());
  }
  NumberExp replace(String _name, NumberExp _number) {
    return new MultiplyExp(
      op1.replace(_name, _number),
        op2.replace(_name, _number));
  }
  public String toString() {
    return "(* " + op1.toString() + " " + op2.toString() + ")";
  }
}
