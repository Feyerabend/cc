// MinusExp.java - Concrete binary operation

public class MinusExp extends BinaryExpression {
    
    public MinusExp(NumberExp left, NumberExp right) {
        super(left, right, "-");
    }
    
    @Override
    protected int compute(int leftValue, int rightValue) {
        return leftValue - rightValue;
    }
    
    @Override
    protected BinaryExpression createCopy(NumberExp newLeft, NumberExp newRight) {
        return new MinusExp(newLeft, newRight);
    }
    
    @Override
    protected NumberExp copyImpl() {
        return new MinusExp(left.copy(), right.copy());
    }
    
    @Override
    public <T> T accept(ExpressionVisitor<T> visitor) {
        return visitor.visit(this);
    }
}
