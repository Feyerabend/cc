// IntegerExp.java - Enhanced with constructor chaining and visitor support

/**
 * Represents an integer literal in an expression.
 */
public class IntegerExp extends NumberExp {
    private final int value;
    
    // Constructor chaining
    public IntegerExp(int value) {
        this(value, true);
    }
    
    // Base constructor with validation 
    private IntegerExp(int value, boolean validate) {
        if (validate && (value < Integer.MIN_VALUE || value > Integer.MAX_VALUE)) {
            throw new IllegalArgumentException("Value out of integer range");
        }
        this.value = value;
    }
    
    // Static factory method
    public static IntegerExp of(int value) {
        return new IntegerExp(value);
    }
    
    // Static factory method with caching for common values (-128 to 127)
    private static final IntegerExp[] CACHE = new IntegerExp[256];
    static {
        for (int i = 0; i < CACHE.length; i++) {
            CACHE[i] = new IntegerExp(i - 128, false);
        }
    }
    
    public static IntegerExp valueOf(int value) {
        if (value >= -128 && value <= 127) { // Common values are cached
            return CACHE[value + 128];
        }
        return new IntegerExp(value);
    }
    
    @Override
    protected int evaluateImpl(Context context) {
        return value;
    }
    
    @Override
    protected NumberExp copyImpl() {
        return this; // Immutable, so return self
    }
    
    @Override
    protected NumberExp replaceImpl(String name, NumberExp replacement) {
        return this; // Integer expressions don't contain variables
    }
    
    @Override
    public <T> T accept(ExpressionVisitor<T> visitor) {
        return visitor.visit(this);
    }
    
    @Override
    public String toString() {
        return Integer.toString(value);
    }
    
    // Accessor
    public int getValue() {
        return value;
    }
}
