// Context.java - Enhanced with generics and proper encapsulation

import java.util.Map;
import java.util.Collections;
import java.util.HashMap;

public class Context {
    private final Map<String, Integer> variables;
    
    // Multiple constructors
    public Context() {
        this(new HashMap<>());
    }
    
    // Constructor chaining
    public Context(Map<String, Integer> initialValues) {
        this.variables = new HashMap<>(initialValues);
    }
    
    // Static factory method with builder support
    public static ContextBuilder builder() {
        return new ContextBuilder();
    }
    
    public void assign(String name, int value) {
        if (name == null || name.isEmpty()) {
            throw new IllegalArgumentException("Variable name cannot be null or empty");
        }
        variables.put(name, value);
    }
    
    public void assign(VariableExp variable, int value) {
        assign(variable.getName(), value);
    }
    
    public int lookup(String name) {
        if (!containsVariable(name)) {
            throw new NumberExp.EvaluationException("Undefined variable: " + name);
        }
        return variables.get(name);
    }
    
    public boolean containsVariable(String name) {
        return variables.containsKey(name);
    }
    
    // Immutable view of all variables
    public Map<String, Integer> getAllVariables() {
        return Collections.unmodifiableMap(variables);
    }
    
    // Builder pattern
    public static class ContextBuilder {
        private final Map<String, Integer> variables = new HashMap<>();
        
        public ContextBuilder withVariable(String name, int value) {
            variables.put(name, value);
            return this;
        }
        
        public ContextBuilder withVariable(VariableExp variable, int value) {
            variables.put(variable.getName(), value);
            return this;
        }
        
        public Context build() {
            return new Context(variables);
        }
    }
}
