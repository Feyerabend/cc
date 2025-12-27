"""
Categorical Object-Oriented Language (COOL)
============================================
An OOP language where:
- Classes are objects in a category
- Inheritance forms morphisms (subtyping)
- Interfaces define universal properties
- Composition is categorical composition
- Method dispatch uses natural transformations
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict



# CATEGORY THEORY FOUNDATIONS

class CategoryObject(ABC):
    """Object in a category"""
    @abstractmethod
    def name(self) -> str:
        pass

class Morphism(ABC):
    """Morphism between objects"""
    @abstractmethod
    def source(self) -> CategoryObject:
        pass
    
    @abstractmethod
    def target(self) -> CategoryObject:
        pass
    
    @abstractmethod
    def compose(self, other: 'Morphism') -> 'Morphism':
        """Compose morphisms (if compatible)"""
        pass



# TYPE SYSTEM (Objects in the Type Category)

class Type(CategoryObject):
    """Types are objects in the category"""
    def __init__(self, name: str):
        self._name = name
    
    def name(self) -> str:
        return self._name
    
    def __str__(self):
        return self._name
    
    def __repr__(self):
        return f"Type({self._name})"
    
    def __eq__(self, other):
        return isinstance(other, Type) and self._name == other._name
    
    def __hash__(self):
        return hash(self._name)

# Built-in types
INT_TYPE = Type("Int")
STRING_TYPE = Type("String")
BOOL_TYPE = Type("Bool")
VOID_TYPE = Type("Void")

@dataclass
class FunctionType(Type):
    """Function type: A -> B"""
    param_types: List[Type]
    return_type: Type
    
    def __init__(self, param_types: List[Type], return_type: Type):
        self.param_types = param_types
        self.return_type = return_type
        name = f"({', '.join(str(t) for t in param_types)}) -> {return_type}"
        super().__init__(name)
    
    def __eq__(self, other):
        return (isinstance(other, FunctionType) and 
                self.param_types == other.param_types and
                self.return_type == other.return_type)
    
    def __hash__(self):
        return hash((tuple(self.param_types), self.return_type))



# SUBTYPING MORPHISMS (Arrows in Type Category)

class SubtypeMorphism(Morphism):
    """Subtyping relationship: A <: B"""
    def __init__(self, subtype: Type, supertype: Type):
        self.subtype = subtype
        self.supertype = supertype
    
    def source(self) -> Type:
        return self.subtype
    
    def target(self) -> Type:
        return self.supertype
    
    def compose(self, other: 'SubtypeMorphism') -> 'SubtypeMorphism':
        """Compose A <: B with B <: C gives A <: C"""
        if self.target() != other.source():
            raise TypeError(f"Cannot compose {self} with {other}")
        return SubtypeMorphism(self.source(), other.target())
    
    def __str__(self):
        return f"{self.subtype} <: {self.supertype}"



# TYPE ENVIRONMENT (Category of Types with Subtyping)

class TypeEnvironment:
    """Manages the category of types and subtyping relations"""
    
    def __init__(self):
        self.types: Dict[str, Type] = {
            "Int": INT_TYPE,
            "String": STRING_TYPE,
            "Bool": BOOL_TYPE,
            "Void": VOID_TYPE
        }
        # Subtyping graph: supertype -> set of subtypes
        self.subtype_graph: Dict[Type, Set[Type]] = defaultdict(set)
        
    def register_type(self, typ: Type):
        """Register a new type (object in category)"""
        self.types[typ.name()] = typ
    
    def add_subtype_relation(self, subtype: Type, supertype: Type):
        """Add subtyping morphism: subtype <: supertype"""
        self.subtype_graph[supertype].add(subtype)
    
    def is_subtype(self, subtype: Type, supertype: Type) -> bool:
        """Check if subtype <: supertype (morphism exists)"""
        if subtype == supertype:
            return True
        
        # BFS to find path in subtyping category
        visited = set()
        queue = [subtype]
        
        while queue:
            current = queue.pop(0)
            if current == supertype:
                return True
            
            if current in visited:
                continue
            visited.add(current)
            
            # Check direct supertypes
            for sup, subs in self.subtype_graph.items():
                if current in subs:
                    queue.append(sup)
        
        return False
    
    def get_morphism_chain(self, subtype: Type, supertype: Type) -> Optional[List[SubtypeMorphism]]:
        """Get chain of morphisms from subtype to supertype"""
        if subtype == supertype:
            return []
        
        # BFS with path tracking
        visited = set()
        queue = [(subtype, [])]
        
        while queue:
            current, path = queue.pop(0)
            if current == supertype:
                return path
            
            if current in visited:
                continue
            visited.add(current)
            
            for sup, subs in self.subtype_graph.items():
                if current in subs:
                    morphism = SubtypeMorphism(current, sup)
                    queue.append((sup, path + [morphism]))
        
        return None



# CLASS DEFINITIONS (Objects in OOP Category)

@dataclass
class Field:
    """Class field"""
    name: str
    type: Type
    value: Any = None

@dataclass
class Method:
    """Class method"""
    name: str
    param_names: List[str]
    param_types: List[Type]
    return_type: Type
    body: 'Statement'
    
    def signature(self) -> FunctionType:
        return FunctionType(self.param_types, self.return_type)


@dataclass
class ClassDef(Type):
    """Class definition - object in OOP category"""
    fields: Dict[str, Field] = field(default_factory=dict)
    methods: Dict[str, Method] = field(default_factory=dict)
    superclass: Optional['ClassDef'] = None
    interfaces: List['Interface'] = field(default_factory=list)

    def __init__(self, name: str):
        super().__init__(name)  # Set the name via Type.__init__
        self.fields = {}
        self.methods = {}
        self.superclass = None
        self.interfaces = []

    def add_field(self, f: Field):
        self.fields[f.name] = f
    
    def add_method(self, m: Method):
        self.methods[m.name] = m

    def __eq__(self, other):
        return isinstance(other, ClassDef) and self.name() == other.name()

    def __hash__(self):
        return hash(self.name())

    def get_field(self, name: str) -> Optional[Field]:
        """Get field (with inheritance)"""
        if name in self.fields:
            return self.fields[name]
        if self.superclass:
            return self.superclass.get_field(name)
        return None
    
    def get_method(self, name: str) -> Optional[Method]:
        """Get method (with inheritance) - natural transformation"""
        if name in self.methods:
            return self.methods[name]
        if self.superclass:
            return self.superclass.get_method(name)
        return None
    
    def all_fields(self) -> Dict[str, Field]:
        """Get all fields including inherited"""
        result = {}
        if self.superclass:
            result.update(self.superclass.all_fields())
        result.update(self.fields)
        return result
    
    def all_methods(self) -> Dict[str, Method]:
        """Get all methods including inherited"""
        result = {}
        if self.superclass:
            result.update(self.superclass.all_methods())
        result.update(self.methods)
        return result


@dataclass
class Interface(Type):
    """Interface - universal property (initial/terminal object pattern)"""
    method_signatures: Dict[str, FunctionType] = field(default_factory=dict)
    
    def add_signature(self, name: str, sig: FunctionType):
        self.method_signatures[name] = sig
    
    def is_implemented_by(self, cls: ClassDef) -> bool:
        """Check if class implements interface (morphism exists)"""
        for method_name, signature in self.method_signatures.items():
            method = cls.get_method(method_name)
            if not method:
                return False
            if method.signature() != signature:
                return False
        return True



# RUNTIME VALUES (Instances)

@dataclass
class ObjectInstance:
    """Runtime object instance"""
    class_def: ClassDef
    field_values: Dict[str, Any] = field(default_factory=dict)
    
    def get_field(self, name: str) -> Any:
        return self.field_values.get(name)
    
    def set_field(self, name: str, value: Any):
        self.field_values[name] = value
    
    def __str__(self):
        fields_str = ", ".join(f"{k}={v}" for k, v in self.field_values.items())
        return f"{self.class_def.name()}({fields_str})"



# EXPRESSIONS (Terms in the language)

class Expression(ABC):
    """Base expression"""
    @abstractmethod
    def type_check(self, env: 'Environment', type_env: TypeEnvironment) -> Type:
        pass
    
    @abstractmethod
    def evaluate(self, env: 'Environment') -> Any:
        pass

@dataclass
class IntLiteral(Expression):
    value: int
    
    def type_check(self, env, type_env):
        return INT_TYPE
    
    def evaluate(self, env):
        return self.value

@dataclass
class StringLiteral(Expression):
    value: str
    
    def type_check(self, env, type_env):
        return STRING_TYPE
    
    def evaluate(self, env):
        return self.value

@dataclass
class BoolLiteral(Expression):
    value: bool
    
    def type_check(self, env, type_env):
        return BOOL_TYPE
    
    def evaluate(self, env):
        return self.value

@dataclass
class Variable(Expression):
    name: str
    
    def type_check(self, env, type_env):
        return env.get_type(self.name)
    
    def evaluate(self, env):
        return env.get_value(self.name)

@dataclass
class BinaryOp(Expression):
    op: str  # +, -, *, ==, <, etc.
    left: Expression
    right: Expression
    
    def type_check(self, env, type_env):
        left_type = self.left.type_check(env, type_env)
        right_type = self.right.type_check(env, type_env)
        
        if self.op in ['+', '-', '*', '/']:
            if left_type != INT_TYPE or right_type != INT_TYPE:
                raise TypeError(f"Operator {self.op} requires Int operands")
            return INT_TYPE
        elif self.op in ['==', '<', '>', '<=', '>=']:
            return BOOL_TYPE
        else:
            raise TypeError(f"Unknown operator: {self.op}")
    
    def evaluate(self, env):
        left_val = self.left.evaluate(env)
        right_val = self.right.evaluate(env)
        
        ops = {
            '+': lambda a, b: a + b,
            '-': lambda a, b: a - b,
            '*': lambda a, b: a * b,
            '/': lambda a, b: a // b,
            '==': lambda a, b: a == b,
            '<': lambda a, b: a < b,
            '>': lambda a, b: a > b,
        }
        
        return ops[self.op](left_val, right_val)

@dataclass
class NewObject(Expression):
    """Object instantiation"""
    class_name: str
    
    def type_check(self, env, type_env):
        if self.class_name not in type_env.types:
            raise TypeError(f"Unknown class: {self.class_name}")
        return type_env.types[self.class_name]
    
    def evaluate(self, env):
        cls = env.type_env.types[self.class_name]
        if not isinstance(cls, ClassDef):
            raise RuntimeError(f"{self.class_name} is not a class")
        
        obj = ObjectInstance(cls)
        # Initialize fields with default values (handling inheritance via all_fields)
        for field_name, field in cls.all_fields().items():
            if field.value is not None:
                obj.set_field(field_name, field.value)
            else:
                # Fallback defaults for built-in types when no explicit default given
                if field.type == INT_TYPE:
                    obj.set_field(field_name, 0)
                elif field.type == STRING_TYPE:
                    obj.set_field(field_name, "")
                elif field.type == BOOL_TYPE:
                    obj.set_field(field_name, False)
                else:
                    obj.set_field(field_name, None)
        return obj

@dataclass
class FieldAccess(Expression):
    """obj.field"""
    obj: Expression
    field_name: str
    
    def type_check(self, env, type_env):
        obj_type = self.obj.type_check(env, type_env)
        if not isinstance(obj_type, ClassDef):
            raise TypeError(f"Cannot access field on non-object type: {obj_type}")
        
        field = obj_type.get_field(self.field_name)
        if not field:
            raise TypeError(f"Field {self.field_name} not found in {obj_type.name()}")
        return field.type
    
    def evaluate(self, env):
        obj = self.obj.evaluate(env)
        if not isinstance(obj, ObjectInstance):
            raise RuntimeError(f"Cannot access field on non-object")
        return obj.get_field(self.field_name)

@dataclass
class MethodCall(Expression):
    """obj.method(args) - natural transformation application"""
    obj: Expression
    method_name: str
    args: List[Expression]
    
    def type_check(self, env, type_env):
        obj_type = self.obj.type_check(env, type_env)
        if not isinstance(obj_type, ClassDef):
            raise TypeError(f"Cannot call method on non-object type: {obj_type}")
        
        method = obj_type.get_method(self.method_name)
        if not method:
            raise TypeError(f"Method {self.method_name} not found in {obj_type.name()}")
        
        # Check argument types
        if len(self.args) != len(method.param_types):
            raise TypeError(f"Wrong number of arguments for {self.method_name}")
        
        for arg, expected_type in zip(self.args, method.param_types):
            arg_type = arg.type_check(env, type_env)
            if not type_env.is_subtype(arg_type, expected_type):
                raise TypeError(f"Argument type mismatch: expected {expected_type}, got {arg_type}")
        
        return method.return_type
    
    def evaluate(self, env):
        obj = self.obj.evaluate(env)
        if not isinstance(obj, ObjectInstance):
            raise RuntimeError(f"Cannot call method on non-object")
        
        method = obj.class_def.get_method(self.method_name)
        if not method:
            raise RuntimeError(f"Method {self.method_name} not found")
        
        # Evaluate arguments
        arg_values = [arg.evaluate(env) for arg in self.args]
        
        # Create new environment for method execution
        method_env = env.extend()
        method_env.define("this", obj, obj.class_def)
        
        for param_name, arg_value, param_type in zip(method.param_names, arg_values, method.param_types):
            method_env.define(param_name, arg_value, param_type)
        
        # Execute method body
        return method.body.execute(method_env)

@dataclass
class Cast(Expression):
    """Explicit cast (subtyping morphism application)"""
    expr: Expression
    target_type: str
    
    def type_check(self, env, type_env):
        expr_type = self.expr.type_check(env, type_env)
        target = type_env.types.get(self.target_type)
        if not target:
            raise TypeError(f"Unknown type: {self.target_type}")
        
        if not type_env.is_subtype(expr_type, target):
            raise TypeError(f"Cannot cast {expr_type} to {target}")
        
        return target
    
    def evaluate(self, env):
        return self.expr.evaluate(env)



# STATEMENTS

class Statement(ABC):
    """Base statement"""
    @abstractmethod
    def execute(self, env: 'Environment') -> Any:
        pass

@dataclass
class ExprStatement(Statement):
    expr: Expression
    
    def execute(self, env):
        return self.expr.evaluate(env)

@dataclass
class VarDecl(Statement):
    name: str
    type: str
    value: Expression
    
    def execute(self, env):
        val = self.value.evaluate(env)
        typ = env.type_env.types[self.type]
        env.define(self.name, val, typ)
        return None

@dataclass
class Assignment(Statement):
    """obj.field = value"""
    obj: Expression
    field_name: str
    value: Expression
    
    def execute(self, env):
        obj = self.obj.evaluate(env)
        if not isinstance(obj, ObjectInstance):
            raise RuntimeError(f"Cannot assign to non-object")
        
        val = self.value.evaluate(env)
        obj.set_field(self.field_name, val)
        return None

@dataclass
class IfStatement(Statement):
    condition: Expression
    then_stmt: Statement
    else_stmt: Optional[Statement] = None
    
    def execute(self, env):
        cond = self.condition.evaluate(env)
        if cond:
            return self.then_stmt.execute(env)
        elif self.else_stmt:
            return self.else_stmt.execute(env)
        return None

@dataclass
class BlockStatement(Statement):
    statements: List[Statement]
    
    def execute(self, env):
        result = None
        for stmt in self.statements:
            result = stmt.execute(env)
        return result

@dataclass
class ReturnStatement(Statement):
    value: Expression
    
    def execute(self, env):
        return self.value.evaluate(env)

@dataclass
class PrintStatement(Statement):
    expr: Expression
    
    def execute(self, env):
        val = self.expr.evaluate(env)
        print(f"  >> {val}")
        return None



# ENVIRONMENT (for runtime values)

class Environment:
    """Runtime environment"""
    def __init__(self, type_env: TypeEnvironment, parent: Optional['Environment'] = None):
        self.type_env = type_env
        self.parent = parent
        self.bindings: Dict[str, Tuple[Any, Type]] = {}
    
    def define(self, name: str, value: Any, typ: Type):
        self.bindings[name] = (value, typ)
    
    def get_value(self, name: str) -> Any:
        if name in self.bindings:
            return self.bindings[name][0]
        if self.parent:
            return self.parent.get_value(name)
        raise NameError(f"Undefined variable: {name}")
    
    def get_type(self, name: str) -> Type:
        if name in self.bindings:
            return self.bindings[name][1]
        if self.parent:
            return self.parent.get_type(name)
        raise NameError(f"Undefined variable: {name}")
    
    def extend(self) -> 'Environment':
        return Environment(self.type_env, self)





def demo():
    print("-" * 70)
    print("CATEGORICAL OBJECT-ORIENTED LANGUAGE (COOL)")
    print("-" * 70)
    print("An OOP language built on category theory:")
    print("- Classes are objects in a category")
    print("- Inheritance forms morphisms (subtyping)")
    print("- Method dispatch uses natural transformations")
    print("-" * 70)
    
    # Setup type environment
    type_env = TypeEnvironment()
    
    # Define Animal class (base object)
    print("\n Defining class hierarchy..")
    animal = ClassDef("Animal")
    animal.add_field(Field("name", STRING_TYPE, "Unknown"))
    animal.add_field(Field("age", INT_TYPE, 0))
    animal.add_method(Method(
        "speak",
        [],
        [],
        STRING_TYPE,
        ReturnStatement(StringLiteral("Some sound"))
    ))
    animal.add_method(Method(
        "get_info",
        [],
        [],
        STRING_TYPE,
        ReturnStatement(StringLiteral("Animal info"))
    ))
    type_env.register_type(animal)
    print(f"    Class Animal (base)")
    
    # Define Dog class (morphism: Dog -> Animal)
    dog = ClassDef("Dog")
    dog.superclass = animal
    dog.add_field(Field("breed", STRING_TYPE, "Mixed"))
    dog.add_method(Method(
        "speak",
        [],
        [],
        STRING_TYPE,
        ReturnStatement(StringLiteral("Woof!"))
    ))
    type_env.register_type(dog)
    type_env.add_subtype_relation(dog, animal)
    print(f"    Class Dog <: Animal (morphism)")
    
    # Define Cat class (morphism: Cat -> Animal)
    cat = ClassDef("Cat")
    cat.superclass = animal
    cat.add_field(Field("indoor", BOOL_TYPE, True))
    cat.add_method(Method(
        "speak",
        [],
        [],
        STRING_TYPE,
        ReturnStatement(StringLiteral("Meow!"))
    ))
    type_env.register_type(cat)
    type_env.add_subtype_relation(cat, animal)
    print(f"   Class Cat <: Animal (morphism)")
    
    # Verify subtyping (morphism existence)
    print("\n Verifying categorical structure..")
    print(f"  Dog <: Animal? {type_env.is_subtype(dog, animal)}")
    print(f"  Cat <: Animal? {type_env.is_subtype(cat, animal)}")
    print(f"  Dog <: Cat? {type_env.is_subtype(dog, cat)}")
    
    # Create runtime environment
    env = Environment(type_env)
    
    # Example 1: Polymorphism (functorial behavior)
    print("\n" + "-" * 70)
    print("Example 1: Polymorphism (Natural Transformation)")
    print("-" * 70)
    
    # Create instances
    my_dog = NewObject("Dog").evaluate(env)
    my_dog.set_field("name", "Buddy")
    my_dog.set_field("age", 3)
    my_dog.set_field("breed", "Golden Retriever")
    
    my_cat = NewObject("Cat").evaluate(env)
    my_cat.set_field("name", "Whiskers")
    my_cat.set_field("age", 2)
    my_cat.set_field("indoor", True)
    
    print(f"Created: {my_dog}")
    print(f"Created: {my_cat}")
    
    # Polymorphic method call (natural transformation)
    print("\nCalling 'speak' method (natural transformation):")
    for obj in [my_dog, my_cat]:
        method = obj.class_def.get_method("speak")
        method_env = env.extend()
        method_env.define("this", obj, obj.class_def)
        result = method.body.execute(method_env)
        print(f"  {obj.class_def.name()}.speak() = {result}")
    
    # Example 2: Field access with inheritance
    print("\n" + "-" * 70)
    print("Example 2: Field Access (Inherited Structure)")
    print("-" * 70)
    
    print(f"Dog fields (including inherited):")
    for field_name, field in my_dog.class_def.all_fields().items():
        value = my_dog.get_field(field_name)
        print(f"  {field_name}: {field.type} = {value}")
    
    # Example 3: Type checking with subtyping
    print("\n" + "-" * 70)
    print("Example 3: Type Checking (Categorical Validation)")
    print("-" * 70)
    
    # Define a function that accepts Animal
    def process_animal(animal_obj: ObjectInstance):
        print(f"  Processing: {animal_obj.class_def.name()}")
        print(f"    Name: {animal_obj.get_field('name')}")
        print(f"    Age: {animal_obj.get_field('age')}")
    
    print("Function accepts Animal (or any subtype):")
    process_animal(my_dog)  # Dog <: Animal  
    process_animal(my_cat)  # Cat <: Animal  
    
    # Example 4: Method dispatch demonstration
    print("\n" + "-" * 70)
    print("Example 4: Dynamic Dispatch (Functorial Mapping)")
    print("-" * 70)
    
    animals = [my_dog, my_cat]
    print("Dispatching 'speak' to each animal:")
    for animal_obj in animals:
        method = animal_obj.class_def.get_method("speak")
        if method:
            method_env = env.extend()
            method_env.define("this", animal_obj, animal_obj.class_def)
            sound = method.body.execute(method_env)
            print(f"  {animal_obj.get_field('name')} ({animal_obj.class_def.name()}): {sound}")
    
    # Example 5: Complex program
    print("\n" + "-" * 70)
    print("Example 5: Complete Program")
    print("-" * 70)
    
    # Create a simple program
    program = BlockStatement([
        PrintStatement(StringLiteral("Creating animals..")),
        VarDecl("pet", "Dog", NewObject("Dog")),
        Assignment(
            Variable("pet"),
            "name",
            StringLiteral("Max")
        ),
        Assignment(
            Variable("pet"),
            "age",
            IntLiteral(5)
        ),
        PrintStatement(FieldAccess(Variable("pet"), "name")),
        PrintStatement(FieldAccess(Variable("pet"), "age")),
    ])

    # in psudo-code:

    # pet = Dog()
    # pet.name = "Max"
    # pet.age = 5
    # print(pet.name)
    # print(pet.age)

    print("Executing program:")
    program.execute(env)
    
    print("\n" + "-" * 70)
    print("Categorical properties demonstrated:")
    print("- Objects: Classes in the type category")
    print("- Morphisms: Subtyping relationships (inheritance)")
    print("- Composition: Transitive subtyping (Dog <: Animal <: Object)")
    print("- Natural Transformations: Polymorphic method dispatch")
    print("- Functors: Type-preserving operations")
    print("-" * 70)

if __name__ == "__main__":
    demo()
