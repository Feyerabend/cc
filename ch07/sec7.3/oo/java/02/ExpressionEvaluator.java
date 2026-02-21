
// ExpressionEvaluator.java - Facade for the interpreter system

/**
 * Facade pattern: simplified interface to the expression system.
 */
public class ExpressionEvaluator {
    private final Parser parser;
    
    public ExpressionEvaluator() {
        this.parser = new Parser();
    }
    
    // Overloaded evaluate methods
    public int evaluate(String expression) {
        return evaluate(expression, new Context());
    }
    
    public int evaluate(String expression, Context context) {
        try {
            Lexer lexer = new Lexer(expression);
            lexer.init();
            NumberExp parsedExpression = parser.parse(lexer);
            return parsedExpression.evaluate(context);
        } catch (Exception e) {
            throw new RuntimeException("Error evaluating expression: " + expression, e);
        }
    }
    
    public int evaluate(NumberExp expression) {
        return evaluate(expression, new Context());
    }
    
    public int evaluate(NumberExp expression, Context context) {
        return expression.evaluate(context);
    }
    
    // Parse only, without evaluation
    public NumberExp parse(String expression) {
        try {
            Lexer lexer = new Lexer(expression);
            lexer.init();
            return parser.parse(lexer);
        } catch (Exception e) {
            throw new RuntimeException("Error parsing expression: " + expression, e);
        }
    }
}
