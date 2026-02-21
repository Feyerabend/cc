
// VariableExp.java - Enhanced with immutability and visitor pattern

/**
 * Represents a variable reference in an expression.
 */
public class VariableExp extends NumberExp {
    private final String name;
    
    public VariableExp(String name) {
        if (name == null || name.isEmpty()) {
            throw new IllegalArgumentException("Variable name cannot be null or empty");
        }
        this.name = name;
    }
    
    // Static factory method
    public static VariableExp of(String name) {
        return new VariableExp(name);
    }
    
    @Override
    protected int evaluateImpl(Context context) {
        if (!context.containsVariable(name)) {
            throw new EvaluationException("Undefined variable: " + name);
        }
        return context.lookup(name);
    }
    
    @Override
    protected NumberExp copyImpl() {
        return this; // Immutable, so return self
    }
    
    @Override
    protected NumberExp replaceImpl(String varName, NumberExp replacement) {
        return name.equals(varName) ? replacement.copy() : this;
    }
    
    @Override
    public <T> T accept(ExpressionVisitor<T> visitor) {
        return visitor.visit(this);
    }
    
    @Override
    public String toString() {
        return name;
    }
    
    // Accessor
    public String getName() {
        return name;
    }
}
