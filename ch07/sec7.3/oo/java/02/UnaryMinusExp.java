// UnaryMinusExp.java - Enhanced unary operation

public class UnaryMinusExp extends NumberExp {
    private final NumberExp operand;
    
    public UnaryMinusExp(NumberExp operand) {
        if (operand == null) {
            throw new IllegalArgumentException("Operand cannot be null");
        }
        this.operand = operand;
    }
    
    @Override
    protected int evaluateImpl(Context context) {
        return -operand.evaluate(context);
    }
    
    @Override
    protected NumberExp copyImpl() {
        return new UnaryMinusExp(operand.copy());
    }
    
    @Override
    protected NumberExp replaceImpl(String name, NumberExp replacement) {
        NumberExp newOperand = operand.replace(name, replacement);
        return (newOperand == operand) ? this : new UnaryMinusExp(newOperand);
    }
    
    @Override
    public <T> T accept(ExpressionVisitor<T> visitor) {
        return visitor.visit(this);
    }
    
    @Override
    public String toString() {
        return "(~ " + operand.toString() + ")";
    }
    
    // Accessor
    public NumberExp getOperand() {
        return operand;
    }
}
