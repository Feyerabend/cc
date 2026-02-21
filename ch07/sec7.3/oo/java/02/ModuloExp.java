
// ModuloExp.java - Concrete binary operation with exception handling

public class ModuloExp extends BinaryExpression {
    
    public ModuloExp(NumberExp left, NumberExp right) {
        super(left, right, "%");
    }
    
    @Override
    protected int compute(int leftValue, int rightValue) {
        if (rightValue == 0) {
            throw new EvaluationException("Modulo by zero");
        }
        return leftValue % rightValue;
    }
    
    @Override
    protected BinaryExpression createCopy(NumberExp newLeft, NumberExp newRight) {
        return new ModuloExp(newLeft, newRight);
    }
    
    @Override
    protected NumberExp copyImpl() {
        return new ModuloExp(left.copy(), right.copy());
    }
    
    @Override
    public <T> T accept(ExpressionVisitor<T> visitor) {
        return visitor.visit(this);
    }
}
