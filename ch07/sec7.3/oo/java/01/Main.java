
// Main.java
// Set Lonnert, 1999



public class Main {

/*
  public static void main(String args[]) {
    Context c = new Context();
    
    String input = "(+ 5 3)";  // 5 + 3
    
    Lexer lex = new Lexer(input);
    lex.init();
    
    Parser p = new Parser();
    NumberExp expr = null;
    try {
        expr = p.parse(lex);
        System.out.println(expr + " -> " + expr.evaluate(c));
        // Output: (+ 5 3) -> 8
    } catch (Parser.SyntaxErrorException e) {
        System.out.println(e);
    }
  }*/

  public static void main(String args[]) {
    Context c = new Context();
    
    VariableExp p = new VariableExp("p");
    VariableExp q = new VariableExp("q");
    
    c.assign(p, 12);
    c.assign(q, 4);
    
    String input = "(+ (/ p q) (* 2 (- p (% p q))))";  // p/q + 2*(p-(p%q))
    
    Lexer lex = new Lexer(input);
    lex.init();
    
    Parser p1 = new Parser();
    NumberExp expr = null;
    try {
        expr = p1.parse(lex);
        System.out.println("p <- " + c.lookup("p"));
        System.out.println("q <- " + c.lookup("q"));
        System.out.println(expr + " -> " + expr.evaluate(c));
        // Output:
        // p <- 12
        // q <- 4
        // (+ (/ p q) (* 2 (- p (% p q)))) -> 27
        // Calculation: 12/4 + 2*(12-(12%4)) = 3 + 2*(12-0) = 3 + 24 = 27
    } catch (Parser.SyntaxErrorException e) {
        System.out.println(e);
    }
  }



/*
  public static void main(String args[]) {
    Context c = new Context();
    
    VariableExp a = new VariableExp("a");
    VariableExp b = new VariableExp("b");
    
    c.assign(a, 7);
    c.assign(b, 3);
    
    String input = "(+ (* a b) (~ b))";  // a * b + (-b)
    
    Lexer lex = new Lexer(input);
    lex.init();
    
    Parser p = new Parser();
    NumberExp expr = null;
    try {
        expr = p.parse(lex);
        System.out.println("a <- " + c.lookup("a"));
        System.out.println("b <- " + c.lookup("b"));
        System.out.println(expr + " -> " + expr.evaluate(c));
        // Output:
        // a <- 7
        // b <- 3
        // (+ (* a b) (~ b)) -> 18
    } catch (Parser.SyntaxErrorException e) {
        System.out.println(e);
    }
  }*/


/*
  public static void main(String args[]) {
    Context c = new Context();
    
    VariableExp x = new VariableExp("x");
    VariableExp y = new VariableExp("y");
    
    c.assign(x, 10);
    c.assign(y, 5);
    
    String input = "(* (- x y) 2)";  // (x - y) * 2
    
    Lexer lex = new Lexer(input);
    lex.init();
    
    Parser p = new Parser();
    NumberExp expr = null;
    try {
        expr = p.parse(lex);
        System.out.println("x <- " + c.lookup("x"));
        System.out.println("y <- " + c.lookup("y"));
        System.out.println(expr + " -> " + expr.evaluate(c));
        // Output: 
        // x <- 10
        // y <- 5
        // (* (- x y) 2) -> 10
    } catch (Parser.SyntaxErrorException e) {
        System.out.println(e);
    }
  }*/

/*
  public static void main(String args[]) {
    Context c = new Context();
    
    VariableExp z = new VariableExp("z");
    c.assign(z, 0);
    
    String input = "(/ 10 z)";  // 10 / z (division by zero)
    
    Lexer lex = new Lexer(input);
    lex.init();
    
    Parser p = new Parser();
    NumberExp expr = null;
    try {
        expr = p.parse(lex);
        System.out.println("z <- " + c.lookup("z"));
        System.out.println(expr + " -> ");
        try {
            System.out.println(expr.evaluate(c));
        } catch (DivideExp.EvaluationErrorException e) {
            System.out.println("Error: " + e.getMessage());
            // Output: Error: division by zero.
        }
    } catch (Parser.SyntaxErrorException e) {
        System.out.println(e);
    }
  }*/
}
