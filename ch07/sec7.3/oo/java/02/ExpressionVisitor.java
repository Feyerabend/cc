
// ExpressionVisitor.java - Visitor pattern for expression traversal

/**
 * Visitor interface for expression traversal and transformation.
 */
public interface ExpressionVisitor<T> {
    T visit(IntegerExp exp);
    T visit(VariableExp exp);
    T visit(PlusExp exp);
    T visit(MinusExp exp);
    T visit(MultiplyExp exp);
    T visit(DivideExp exp);
    T visit(ModuloExp exp);
    T visit(UnaryMinusExp exp);
}
