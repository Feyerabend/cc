/**
 * Abstract representation of a numeric expression.
 * Provides template methods and common operations for all expressions.
 */
public abstract class NumberExp {
    // Abstract methods that subclasses must implement
    protected abstract int evaluateImpl(Context context);
    protected abstract NumberExp copyImpl();
    protected abstract NumberExp replaceImpl(String name, NumberExp replacement);
    
    // Template method pattern
    public final int evaluate(Context context) {
        validateContext(context);
        return evaluateImpl(context);
    }
    
    // Factory method for expression creation
    public static NumberExp create(int value) {
        return new IntegerExp(value);
    }
    
    // Overloaded factory methods
    public static NumberExp create(String variableName) {
        return new VariableExp(variableName);
    }
    
    public static NumberExp create(NumberExp left, String operator, NumberExp right) {
        switch (operator) {
            case "+": return new PlusExp(left, right);
            case "-": return new MinusExp(left, right);
            case "*": return new MultiplyExp(left, right);
            case "/": return new DivideExp(left, right);
            case "%": return new ModuloExp(left, right);
            default: throw new IllegalArgumentException("Unknown operator: " + operator);
        }
    }
    
    // Template method pattern with final methods for common behavior
    public final NumberExp copy() {
        return copyImpl();
    }
    
    public final NumberExp replace(String name, NumberExp replacement) {
        if (name == null || replacement == null) {
            throw new IllegalArgumentException("Neither name nor replacement can be null");
        }
        return replaceImpl(name, replacement);
    }
    
    // Common validation - part of template method pattern
    protected void validateContext(Context context) {
        if (context == null) {
            throw new EvaluationException("Context cannot be null");
        }
    }
    
    // Exception hierarchy
    public static class EvaluationException extends RuntimeException {
        public EvaluationException(String message) {
            super(message);
        }
        
        public EvaluationException(String message, Throwable cause) {
            super(message, cause);
        }
    }
    
    // Visitor pattern support
    public abstract <T> T accept(ExpressionVisitor<T> visitor);
    
    // Fluent interface for expression composition
    public NumberExp plus(NumberExp other) {
        return new PlusExp(this, other);
    }
    
    public NumberExp minus(NumberExp other) {
        return new MinusExp(this, other);
    }
    
    public NumberExp times(NumberExp other) {
        return new MultiplyExp(this, other);
    }
    
    public NumberExp dividedBy(NumberExp other) {
        return new DivideExp(this, other);
    }
    
    public NumberExp mod(NumberExp other) {
        return new ModuloExp(this, other);
    }
    
    public NumberExp negated() {
        return new UnaryMinusExp(this);
    }
}
