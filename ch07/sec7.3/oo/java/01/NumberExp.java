
// NumberExp.java
// Set Lonnert, 1999

abstract class NumberExp {
  abstract int evaluate(Context _con);
  abstract NumberExp replace(String _name, NumberExp _number);
  abstract NumberExp copy();
}
