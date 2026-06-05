
## JVM Interpreter Architecture: Native vs Custom Class Separation

This JVM interpreter implementation provides a *clean separation* between:
1. *Native Java Standard Library Classes* - Implemented in Python
   (e.g., `System`, `StringBuilder`, `Object`)
2. *Custom User Classes* - Loaded from `.class` files and executed as bytecode

The key insight is that these two types of classes need different execution strategies:
- *Native classes*: Call Python code directly (fast, no bytecode interpretation needed)
- *Custom classes*: Parse and execute JVM bytecode (slower, but necessary for user code)


### Architecture Components

#### 1. Native Registry (`native_registry.py`)

The *Native Registry* is the central registry for all Java standard library implementations.

*Features:*
- Singleton pattern - one global registry
- Stores native constructors, methods, and static fields
- Checked FIRST before attempting bytecode interpretation
- Clear API: `has_native_method()`, `invoke_native_method()`, etc.

*Example Registration:*
```python
# Register java.lang.StringBuilder
registry.register_constructor("java.lang.StringBuilder", 
                             lambda: JavaLangStringBuilder())
registry.register_method("java.lang.StringBuilder", "append", 
                        lambda self, value: self.append(value))
```

- Explicitly separates "what's native" from "what's bytecode"
- Easy to extend with new native classes
- No confusion - if it's in the registry, it's native; otherwise, it's custom


#### 2. Object Representation (`java_objects.py`)

*Two Types of Objects:*

__NativeObject (for stdlib)__
```python
class NativeObject:
    """Base for native Java objects implemented in Python"""
    def __init__(self, class_name: str):
        self.class_name = class_name
        self.fields: Dict[str, Any] = {}
```

- Implements behavior in Python code
- Examples: `JavaLangObject`, `JavaLangStringBuilder`, `JavaIoPrintStream`

__JavaObject (for custom classes)__
```python
class JavaObject:
    """Internal representation of custom Java objects from .class files"""
    def __init__(self, class_name: str):
        self.class_name = class_name
        self.fields: Dict[str, Any] = {}
```

- Behavior defined by bytecode, NOT Python code
- Fields stored in dictionary
- Methods executed by interpreter

*Why As Separate?*
- `NativeObject`: Behavior is Python code - methods are Python functions
- `JavaObject`: Behavior is bytecode - methods are executed by interpreter
- Both share same interface (`get_field`, `set_field`) for uniform field access


#### 3. Object Factory (`java_objects.py`)

The *Object Factory* provides unified object creation:

```python
def create_object(self, class_name: str) -> Any:
    # Check native registry first
    if self.native_registry.has_native_constructor(class_name):
        return self.native_registry.create_native_object(class_name)
    
    # Otherwise, create custom JavaObject
    return JavaObject(class_name)
```

*Benefits:*
- Single entry point for object creation
- Automatically chooses correct object type
- Used by `new` bytecode instruction


#### 4. Updated Interpreter (`interpreter_v2.py`)

The interpreter now *always checks native registry first*:

__Example: `invokevirtual`__
```python
def instr_invokevirtual(self):
    # ... parse class_name, method_name, args ...
    
    # CHECK NATIVE FIRST
    if self.native_registry.has_native_method(actual_class, method_name):
        result = self.native_registry.invoke_native_method(
            actual_class, method_name, obj, args
        )
    else:
        # Custom bytecode method
        result = self._invoke_bytecode_method(
            actual_class, method_name, descriptor, obj, args
        )
```

*Order of Operations:*
1. Parse method reference from constant pool
2. *Check if method is native* (fast path)
3. If native: call Python function directly
4. If not native: load bytecode and interpret it

__Example: `getstatic`__
```python
def instr_getstatic(self):
    class_name, field_name = self._resolve_field_ref(index)
    
    # CHECK NATIVE FIRST
    if self.native_registry.has_native_static_field(class_name, field_name):
        value = self.native_registry.get_native_static_field(class_name, field_name)
    else:
        # Custom class static field
        value = self.class_loader.resolve_field(class_name, field_name)
```


### Execution Flow Examples

#### Example 1: Calling System.out.println()

*Java Bytecode:*
```
getstatic java/lang/System.out
ldc "Hello World"
invokevirtual java/io/PrintStream.println(Ljava/lang/String;)V
```

*Execution:*
1. `getstatic`: 
   - Checks native registry for `java.lang.System.out`
   - *Found!* Returns `JavaIoPrintStream` instance
   - Pushes to stack

2. `ldc`: Pushes "Hello World" string to stack

3. `invokevirtual`:
   - Checks native registry for `java.io.PrintStream.println`
   - *Found!* Calls Python method `JavaIoPrintStream.println("Hello World")`
   - Prints to stdout

*Result:* Fast execution - no bytecode interpretation needed!

#### Example 2: Calling Custom Class Method

*Java Bytecode:*
```
new com/example/MyClass
dup
invokespecial com/example/MyClass.<init>()V
invokevirtual com/example/MyClass.doSomething()I
```

*Execution:*
1. `new`:
   - Object factory checks native registry
   - *Not found!* Creates `JavaObject("com.example.MyClass")`
   - Pushes to stack

2. `invokespecial` (constructor):
   - Checks native registry for `com.example.MyClass.<init>`
   - *Not found!* Loads bytecode from `.class` file
   - Creates sub-interpreter and executes constructor bytecode

3. `invokevirtual`:
   - Checks native registry for `com.example.MyClass.doSomething`
   - *Not found!* Loads bytecode from `.class` file
   - Creates sub-interpreter and executes method bytecode
   - Returns result

*Result:* Full bytecode interpretation for custom classes

#### Example 3: Mixed Native and Custom

*Java Code:*
```java
public class MyClass {
    public static void main(String[] args) {
        StringBuilder sb = new StringBuilder();  // Native!
        sb.append("Hello");                      // Native!
        System.out.println(sb.toString());       // All native!
    }
}
```

*Execution:*
1. `MyClass.main()` - Custom bytecode (loaded from file)
2. `new StringBuilder()` - Native (fast instantiation)
3. `sb.append("Hello")` - Native (Python method call)
4. `System.out` - Native (static field)
5. `sb.toString()` - Native (returns Python string)
6. `println()` - Native (Python print)

*Result:* Custom main method orchestrates native stdlib calls!


### Benefits of This Architecture

#### 1. *Clear Separation of Concerns*
- Native registry handles stdlib
- Interpreter handles bytecode
- No conflation or confusion

#### 2. *Performance*
- Native calls are fast (direct Python function calls)
- Only interpret bytecode when necessary
- Can optimize native implementations freely

#### 3. *Correctness*
- Proper JVM semantics for object references
- Correct field storage (instance vs static)
- Proper polymorphism (checks actual object class)

#### 4. *Extensibility*
- Easy to add new native classes (just register them)
- Easy to add new bytecode instructions (just add to dispatch table)
- No need to modify core interpreter for stdlib additions

#### 5. *Maintainability*
- Native implementations in one place (`native_registry.py`)
- Bytecode execution in one place (`interpreter_v2.py`)
- Clear boundaries make debugging easier


### How to Add a New Native Class

*Example: Adding `java.util.ArrayList`*

```python
# 1. Create native implementation
class JavaUtilArrayList(NativeObject):
    def __init__(self):
        super().__init__("java.util.ArrayList")
        self.elements = []
    
    def add(self, element: Any) -> bool:
        self.elements.append(element)
        return True
    
    def get(self, index: int) -> Any:
        return self.elements[index]
    
    def size(self) -> int:
        return len(self.elements)

# 2. Register in native registry
registry.register_constructor("java.util.ArrayList", lambda: JavaUtilArrayList())
registry.register_method("java.util.ArrayList", "add", lambda self, element: self.add(element))
registry.register_method("java.util.ArrayList", "get", lambda self, index: self.get(index))
registry.register_method("java.util.ArrayList", "size", lambda self: self.size())
registry.register_method("java.util.ArrayList", "<init>", lambda self: None)
```

*That's it!* Now all Java code that uses `ArrayList` will automatically use this native implementation.


### Testing the Architecture

*Test 1: Pure Native*
```java
public class TestNative {
    public static void main(String[] args) {
        System.out.println("Hello!");
    }
}
```
Expected: Fast execution, no bytecode interpretation except `main()`.

*Test 2: Pure Custom*
```java
public class TestCustom {
    private int value;
    
    public void setValue(int v) {
        this.value = v;
    }
    
    public int getValue() {
        return this.value;
    }
    
    public static void main(String[] args) {
        TestCustom obj = new TestCustom();
        obj.setValue(42);
        // Should return 42
    }
}
```
Expected: Full bytecode interpretation, proper field storage.

*Test 3: Mixed*
```java
public class TestMixed {
    public static void main(String[] args) {
        StringBuilder sb = new StringBuilder();
        sb.append("Value: ");
        sb.append(computeValue());
        System.out.println(sb.toString());
    }
    
    private static int computeValue() {
        return 42;
    }
}
```
Expected: Native StringBuilder + System.out, custom computeValue().


### Conclusion

This architecture provides:
- *Clarity*: Explicit separation of native vs custom
- *Performance*: Fast native calls, interpret only when needed
- *Correctness*: Proper JVM semantics throughout
- *Extensibility*: Easy to add new features

The key principle for this implementation:
*Check native first, then fall back to bytecode.*
