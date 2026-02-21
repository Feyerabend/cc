
// VariableExp.java
// Set Lonnert, 1999

public class VariableExp extends NumberExp {
  String var;
  public VariableExp(String _name) {
    var = _name;
  }
  int evaluate(Context _rho) {
    return _rho.lookup(var);
  }
  NumberExp copy() {
    return new VariableExp(var);
  }
  NumberExp replace(String _name, NumberExp _bool) {
    if (_name.equals(var)) {
      return _bool.copy();
    } else {
      return new VariableExp(var);
    }
  }
  public String toString() {
    return var;
  }
}
