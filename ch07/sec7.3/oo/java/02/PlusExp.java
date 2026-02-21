
// PlusExp.java - Concrete binary operation

public class PlusExp extends BinaryExpression {
    
    public PlusExp(NumberExp left, NumberExp right) {
        super(left, right, "+");
    }
    
    @Override
    protected int compute(int leftValue, int rightValue) {
        return leftValue + rightValue;
    }
    
    @Override
    protected BinaryExpression createCopy(NumberExp newLeft, NumberExp newRight) {
        return new PlusExp(newLeft, newRight);
    }
    
    @Override
    protected NumberExp copyImpl() {
        return new PlusExp(left.copy(), right.copy());
    }
    
    @Override
    public <T> T accept(ExpressionVisitor<T> visitor) {
        return visitor.visit(this);
    }
}
