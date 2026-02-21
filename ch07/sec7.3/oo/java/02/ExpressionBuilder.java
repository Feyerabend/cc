// ExpressionBuilder.java - Builder pattern for complex expressions

/**
 * Builder for creating complex expressions fluently.
 */
public class ExpressionBuilder {
    private NumberExp current;
    
    private ExpressionBuilder(NumberExp initial) {
        this.current = initial;
    }
    
    // Static factory methods
    public static ExpressionBuilder start(int value) {
        return new ExpressionBuilder(new IntegerExp(value));
    }
    
    public static ExpressionBuilder start(String variableName) {
        return new ExpressionBuilder(new VariableExp(variableName));
    }
    
    public static ExpressionBuilder start(NumberExp exp) {
        return new ExpressionBuilder(exp);
    }
    
    // Fluent interface methods
    public ExpressionBuilder plus(int value) {
        current = new PlusExp(current, new IntegerExp(value));
        return this;
    }
    
    public ExpressionBuilder plus(String variableName) {
        current = new PlusExp(current, new VariableExp(variableName));
        return this;
    }
    
    public ExpressionBuilder plus(NumberExp exp) {
        current = new PlusExp(current, exp);
        return this;
    }
    
    public ExpressionBuilder minus(int value) {
        current = new MinusExp(current, new IntegerExp(value));
        return this;
    }
    
    public ExpressionBuilder minus(String variableName) {
        current = new MinusExp(current, new VariableExp(variableName));
        return this;
    }
    
    public ExpressionBuilder minus(NumberExp exp) {
        current = new MinusExp(current, exp);
        return this;
    }
    
    public ExpressionBuilder multiply(int value) {
        current = new MultiplyExp(current, new IntegerExp(value));
        return this;
    }
    
    public ExpressionBuilder multiply(String variableName) {
        current = new MultiplyExp(current, new VariableExp(variableName));
        return this;
    }
    
    public ExpressionBuilder multiply(NumberExp exp) {
        current = new MultiplyExp(current, exp);
        return this;
    }
    
    public ExpressionBuilder divide(int value) {
        current = new DivideExp(current, new IntegerExp(value));
        return this;
    }
    
    public ExpressionBuilder divide(String variableName) {
        current = new DivideExp(current, new VariableExp(variableName));
        return this;
    }
    
    public ExpressionBuilder divide(NumberExp exp) {
        current = new DivideExp(current, exp);
        return this;
    }
    
    public ExpressionBuilder modulo(int value) {
        current = new ModuloExp(current, new IntegerExp(value));
        return this;
    }
    
    public ExpressionBuilder modulo(String variableName) {
        current = new ModuloExp(current, new VariableExp(variableName));
        return this;
    }
    
    public ExpressionBuilder modulo(NumberExp exp) {
        current = new ModuloExp(current, exp);
        return this;
    }
    
    public ExpressionBuilder negate() {
        current = new UnaryMinusExp(current);
        return this;
    }
    
    // Terminal operation
    public NumberExp build() {
        return current;
    }
}
