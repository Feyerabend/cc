
// BinaryExpression.java - Abstract class for binary operations

/**
 * Abstract base class for all binary operations.
 * Uses template method pattern for common behavior.
 */
public abstract class BinaryExpression extends NumberExp {
    protected final NumberExp left;
    protected final NumberExp right;
    protected final String operator;
    
    protected BinaryExpression(NumberExp left, NumberExp right, String operator) {
        if (left == null || right == null) {
            throw new IllegalArgumentException("Operands cannot be null");
        }
        this.left = left;
        this.right = right;
        this.operator = operator;
    }
    
    protected abstract int compute(int leftValue, int rightValue);
    
    @Override
    protected final int evaluateImpl(Context context) {
        int leftValue = left.evaluate(context);
        int rightValue = right.evaluate(context);
        return compute(leftValue, rightValue);
    }
    
    @Override
    protected final NumberExp replaceImpl(String name, NumberExp replacement) {
        NumberExp newLeft = left.replace(name, replacement);
        NumberExp newRight = right.replace(name, replacement);
        
        if (newLeft == left && newRight == right) {
            return this;
        }
        
        return createCopy(newLeft, newRight);
    }
    
    // Factory method for subclasses
    protected abstract BinaryExpression createCopy(NumberExp newLeft, NumberExp newRight);
    
    @Override
    public String toString() {
        return "(" + operator + " " + left.toString() + " " + right.toString() + ")";
    }
    
    // Accessors
    public NumberExp getLeft() {
        return left;
    }
    
    public NumberExp getRight() {
        return right;
    }
    
    public String getOperator() {
        return operator;
    }
}
