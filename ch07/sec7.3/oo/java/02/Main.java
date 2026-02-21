
// Main.java - Example client code with modern OO features

public class Main {
    public static void main(String[] args) {

        // Example 1: Using factory methods and builder pattern
        Context context = Context.builder()
            .withVariable("x", 10)
            .withVariable("y", 5)
            .build();
            
        NumberExp expression = ExpressionBuilder.start("x")
            .multiply("y")
            .minus(5)
            .divide(5)
            .build();
            
        System.out.println("Expression: " + expression);
        System.out.println("Result: " + expression.evaluate(context));
        

        // Example 2: Using static factory methods
        NumberExp a = IntegerExp.valueOf(10);
        NumberExp b = VariableExp.of("y");
        NumberExp c = NumberExp.create(a, "+", b);
        
        System.out.println("Expression: " + c);
        System.out.println("Result: " + c.evaluate(context));
        

        // Example 3: Using method chaining with fluent interface
        NumberExp chainedExpr = NumberExp.create(5)
            .plus(NumberExp.create("x"))
            .times(NumberExp.create("y"));
            
        System.out.println("Expression: " + chainedExpr);
        System.out.println("Result: " + chainedExpr.evaluate(context));
        

        // Example 4: Using the facade for simplicity
        ExpressionEvaluator evaluator = new ExpressionEvaluator();
        int result = evaluator.evaluate("(+ (* x y) (~ 5))", context);
        
        System.out.println("Result from evaluator: " + result);
        

        // Example 5: Using the visitor pattern
        ExpressionPrinter printer = new ExpressionPrinter();
        System.out.println("Printed expression: " + expression.accept(printer));
    }
    

    // Example visitor implementation
    static class ExpressionPrinter implements ExpressionVisitor<String> {
        @Override
        public String visit(IntegerExp exp) {
            return Integer.toString(exp.getValue());
        }
        
        @Override
        public String visit(VariableExp exp) {
            return exp.getName();
        }
        
        @Override
        public String visit(PlusExp exp) {
            return "(" + exp.getLeft().accept(this) + " + " + exp.getRight().accept(this) + ")";
        }
        
        @Override
        public String visit(MinusExp exp) {
            return "(" + exp.getLeft().accept(this) + " - " + exp.getRight().accept(this) + ")";
        }
        
        @Override
        public String visit(MultiplyExp exp) {
            return "(" + exp.getLeft().accept(this) + " * " + exp.getRight().accept(this) + ")";
        }
        
        @Override
        public String visit(DivideExp exp) {
            return "(" + exp.getLeft().accept(this) + " / " + exp.getRight().accept(this) + ")";
        }
        
        @Override
        public String visit(ModuloExp exp) {
            return "(" + exp.getLeft().accept(this) + " % " + exp.getRight().accept(this) + ")";
        }
        
        @Override
        public String visit(UnaryMinusExp exp) {
            return "(-" + exp.getOperand().accept(this) + ")";
        }
    }
}
