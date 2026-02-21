
// IntegerExp.java
// Set Lonnert, 1999

public class IntegerExp extends NumberExp {
  int num;
  public IntegerExp(int _number) {
    num = _number;
  }
  int evaluate(Context _rho) {
    return num;
  }
  NumberExp copy() {
    return new IntegerExp(num);
  }
  NumberExp replace(String _name, NumberExp _number) {
    return new IntegerExp(num);
  }
  public String toString() {
    return Integer.toString(num);
  }
}
