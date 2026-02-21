
// DivideExp.java
// Set Lonnert, 1999

public class DivideExp extends NumberExp {
  NumberExp op1, op2;
  public DivideExp(NumberExp _op1, NumberExp _op2) {
    op1 = _op1;
    op2 = _op2;
  }
  static class EvaluationErrorException extends RuntimeException {
    EvaluationErrorException() { }
    EvaluationErrorException(String s) {
      super(s);
    }
  }
  int evaluate(Context _rho) {
    if (op2.evaluate(_rho) != 0) {
      return (op1.evaluate(_rho) / op2.evaluate(_rho));
    } else {
      throw new
        DivideExp.EvaluationErrorException("division by zero.");
    }
  }
  NumberExp copy() {
    return new DivideExp(op1.copy(), op2.copy());
  }
  NumberExp replace(String _name, NumberExp _number) {
    return new DivideExp(
      op1.replace(_name, _number),
        op2.replace(_name, _number));
  }
  public String toString() {
    return "(/ " + op1.toString() + " " + op2.toString() + ")";
  }
}
