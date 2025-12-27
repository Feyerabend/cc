"""
Categorical Object-Oriented Language (COOL) with Generics
==========================================================
An OOP language where:
- Classes are objects in a category
- Inheritance forms morphisms (subtyping)
- Generics are endofunctors (Type -> Type)
- Type parameters are functorial mappings
- Variance is categorical (co/contravariant functors)
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Set, Tuple, Optional
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
class TypeParameter(Type):
    """Type parameter (type variable in functors)"""
    variance: str = "invariant"  # invariant, covariant, contravariant
    bound: Optional[Type] = None  # upper bound for bounded polymorphism
    
    def __init__(self, name: str, variance: str = "invariant", bound: Optional[Type] = None):
        super().__init__(name)
        self.variance = variance
        self.bound = bound
    
    def __str__(self):
        prefix = {
            "covariant": "+",
            "contravariant": "-",
            "invariant": ""
        }[self.variance]
        bound_str = f" extends {self.bound}" if self.bound else ""
        return f"{prefix}{self._name}{bound_str}"

@dataclass
class GenericType(Type):
    """Generic type application: F<T> where F is a functor Type -> Type"""
    base: Type  # The base generic class
    type_args: List[Type]  # Type arguments
    
    def __init__(self, base: Type, type_args: List[Type]):
        self.base = base
        self.type_args = type_args
        args_str = ", ".join(str(t) for t in type_args)
        super().__init__(f"{base.name()}<{args_str}>")
    
    def __eq__(self, other):
        return (isinstance(other, GenericType) and 
                self.base == other.base and
                self.type_args == other.type_args)
    
    def __hash__(self):
        return hash((self.base, tuple(self.type_args)))

@dataclass
class FunctionType(Type):
    """Function type: (A1, A2, ...) -> B"""
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
        
        # Handle generic types with variance
        if isinstance(subtype, GenericType) and isinstance(supertype, GenericType):
            if subtype.base != supertype.base:
                # Check if base classes have subtype relation
                if not self.is_subtype(subtype.base, supertype.base):
                    return False
            
            # Check variance rules
            base_class = self._get_class_def(subtype.base)
            if base_class and isinstance(base_class, GenericClassDef):
                return self._check_generic_subtyping(
                    subtype.type_args,
                    supertype.type_args,
                    base_class.type_params
                )
            
            # Default: invariant - all type args must match exactly
            return subtype.type_args == supertype.type_args
        
        # Handle type parameters with bounds
        if isinstance(subtype, TypeParameter) and subtype.bound:
            return self.is_subtype(subtype.bound, supertype)
        
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
    
    def _check_generic_subtyping(self, sub_args: List[Type], super_args: List[Type], 
                                  type_params: List[TypeParameter]) -> bool:
        """Check subtyping with variance rules (functorial properties)"""
        if len(sub_args) != len(super_args):
            return False
        
        for sub_arg, super_arg, param in zip(sub_args, super_args, type_params):
            if param.variance == "covariant":
                # Covariant functor: F<A> <: F<B> if A <: B
                if not self.is_subtype(sub_arg, super_arg):
                    return False
            elif param.variance == "contravariant":
                # Contravariant functor: F<A> <: F<B> if B <: A
                if not self.is_subtype(super_arg, sub_arg):
                    return False
            else:  # invariant
                # Invariant: must be exactly equal
                if sub_arg != super_arg:
                    return False
        
        return True
    
    def _get_class_def(self, typ: Type):
        """Get class definition for a type"""
        if isinstance(typ, GenericType):
            return self.types.get(typ.base.name())
        return self.types.get(typ.name())
    
    def substitute_type_params(self, typ: Type, substitutions: Dict[str, Type]) -> Type:
        """Substitute type parameters (functorial mapping)"""
        if isinstance(typ, TypeParameter):
            return substitutions.get(typ.name(), typ)
        elif isinstance(typ, GenericType):
            new_args = [self.substitute_type_params(arg, substitutions) for arg in typ.type_args]
            return GenericType(typ.base, new_args)
        return typ



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
    
    def substitute_types(self, substitutions: Dict[str, Type], type_env: TypeEnvironment) -> 'Method':
        """Substitute type parameters in method signature"""
        new_param_types = [type_env.substitute_type_params(t, substitutions) for t in self.param_types]
        new_return_type = type_env.substitute_type_params(self.return_type, substitutions)
        return Method(self.name, self.param_names, new_param_types, new_return_type, self.body)

class ClassDef(Type):
    """Class definition - object in OOP category"""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.class_fields: Dict[str, Field] = {}
        self.methods: Dict[str, Method] = {}
        self.superclass: Optional['ClassDef'] = None
        self.interfaces: List['Interface'] = []
    
    def add_field(self, f: Field):
        self.class_fields[f.name] = f
    
    def add_method(self, m: Method):
        self.methods[m.name] = m
    
    def get_field(self, name: str) -> Optional[Field]:
        """Get field (with inheritance)"""
        if name in self.class_fields:
            return self.class_fields[name]
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
        result.update(self.class_fields)
        return result
    
    def all_methods(self) -> Dict[str, Method]:
        """Get all methods including inherited"""
        result = {}
        if self.superclass:
            result.update(self.superclass.all_methods())
        result.update(self.methods)
        return result

class GenericClassDef(ClassDef):
    """Generic class - endofunctor Type -> Type"""
    
    def __init__(self, name: str, type_params: List[TypeParameter]):
        super().__init__(name)
        self.type_params = type_params
    
    def __str__(self):
        params_str = ", ".join(str(p) for p in self.type_params)
        return f"{self._name}<{params_str}>"
    
    def instantiate(self, type_args: List[Type], type_env: TypeEnvironment) -> ClassDef:
        """Apply functor to types (instantiate generic class)"""
        if len(type_args) != len(self.type_params):
            raise TypeError(f"Wrong number of type arguments for {self._name}")
        
        # Check bounds
        for arg, param in zip(type_args, self.type_params):
            if param.bound and not type_env.is_subtype(arg, param.bound):
                raise TypeError(f"Type {arg} does not satisfy bound {param.bound}")
        
        # Create substitution map
        substitutions = {param.name(): arg for param, arg in zip(self.type_params, type_args)}
        
        # Create instantiated class
        instantiated = ClassDef(f"{self._name}<{', '.join(str(t) for t in type_args)}>")
        
        # Substitute types in fields
        for field_name, field in self.class_fields.items():
            new_type = type_env.substitute_type_params(field.type, substitutions)
            instantiated.add_field(Field(field_name, new_type, field.value))
        
        # Substitute types in methods
        for method_name, method in self.methods.items():
            new_method = method.substitute_types(substitutions, type_env)
            instantiated.add_method(new_method)
        
        return instantiated

@dataclass
class Interface(Type):
    """Interface - universal property"""
    method_signatures: Dict[str, FunctionType] = field(default_factory=dict)
    
    def add_signature(self, name: str, sig: FunctionType):
        self.method_signatures[name] = sig



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



# EXPRESSIONS


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
    op: str
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
    type_args: List[str] = field(default_factory=list)  # For generics
    
    def type_check(self, env, type_env):
        if self.class_name not in type_env.types:
            raise TypeError(f"Unknown class: {self.class_name}")
        
        base_class = type_env.types[self.class_name]
        
        if self.type_args:
            # Generic instantiation
            type_arg_types = [type_env.types.get(ta, TypeParameter(ta)) for ta in self.type_args]
            return GenericType(base_class, type_arg_types)
        
        return base_class
    
    def evaluate(self, env):
        base_class = env.type_env.types[self.class_name]
        
        if isinstance(base_class, GenericClassDef) and self.type_args:
            # Instantiate generic class (apply functor)
            type_arg_types = [env.type_env.types.get(ta, TypeParameter(ta)) for ta in self.type_args]
            cls = base_class.instantiate(type_arg_types, env.type_env)
        elif isinstance(base_class, ClassDef):
            cls = base_class
        else:
            raise RuntimeError(f"{self.class_name} is not a class")
        
        obj = ObjectInstance(cls)
        # Initialize fields
        for field_name, field in cls.all_fields().items():
            obj.set_field(field_name, field.value or self._default_value(field.type))
        return obj
    
    def _default_value(self, typ: Type):
        if typ == INT_TYPE:
            return 0
        elif typ == STRING_TYPE:
            return ""
        elif typ == BOOL_TYPE:
            return False
        return None

@dataclass
class FieldAccess(Expression):
    """obj.field"""
    obj: Expression
    field_name: str
    
    def type_check(self, env, type_env):
        obj_type = self.obj.type_check(env, type_env)
        
        # Handle generic types
        if isinstance(obj_type, GenericType):
            base_class = type_env.types.get(obj_type.base.name())
            if isinstance(base_class, GenericClassDef):
                # Get instantiated field type
                instantiated = base_class.instantiate(obj_type.type_args, type_env)
                field = instantiated.get_field(self.field_name)
            else:
                field = base_class.get_field(self.field_name) if isinstance(base_class, ClassDef) else None
        elif isinstance(obj_type, ClassDef):
            field = obj_type.get_field(self.field_name)
        else:
            raise TypeError(f"Cannot access field on non-object type: {obj_type}")
        
        if not field:
            raise TypeError(f"Field {self.field_name} not found in {obj_type}")
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
        
        # Handle generic types
        if isinstance(obj_type, GenericType):
            base_class = type_env.types.get(obj_type.base.name())
            if isinstance(base_class, GenericClassDef):
                instantiated = base_class.instantiate(obj_type.type_args, type_env)
                method = instantiated.get_method(self.method_name)
            else:
                method = base_class.get_method(self.method_name) if isinstance(base_class, ClassDef) else None
        elif isinstance(obj_type, ClassDef):
            method = obj_type.get_method(self.method_name)
        else:
            raise TypeError(f"Cannot call method on non-object type: {obj_type}")
        
        if not method:
            raise TypeError(f"Method {self.method_name} not found in {obj_type}")
        
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
    type_str: str
    type_args: List[str]  # For generic types
    value: Expression
    
    def execute(self, env):
        val = self.value.evaluate(env)
        
        # Resolve type
        if self.type_args:
            base_type = env.type_env.types[self.type_str]
            type_arg_types = [env.type_env.types[ta] for ta in self.type_args]
            typ = GenericType(base_type, type_arg_types)
        else:
            typ = env.type_env.types[self.type_str]
        
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



# ENVIRONMENT


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



# DEMONSTRATION


def demo():
    print("-" * 70)
    print("COOL with CATEGORICAL GENERICS")
    print("-" * 70)
    print("Generics as Endofunctors Type → Type")
    print("- Generic classes are functors")
    print("- Type arguments are functorial mappings")
    print("- Variance rules are categorical properties")
    print("-" * 70)
    
    type_env = TypeEnvironment()
    
    # Example 1: Define a generic Box<T> class (covariant functor)
    print("\n  Example 1: Generic Box<T> (Covariant Functor)")
    print("-" * 70)
    
    T = TypeParameter("T", variance="covariant")
    box_class = GenericClassDef("Box", [T])
    box_class.add_field(Field("value", T, None))
    box_class.add_method(Method(
        "get",
        [],
        [],
        T,
        ReturnStatement(FieldAccess(Variable("this"), "value"))
    ))
    box_class.add_method(Method(
        "set",
        ["newValue"],
        [T],
        VOID_TYPE,
        Assignment(Variable("this"), "value", Variable("newValue"))
    ))
    
    type_env.register_type(box_class)
    print(f"    Defined generic class: {box_class}")
    print(f"    Type parameter: {T}")
    print(f"    Fields: value: T")
    print(f"    Methods: get(): T, set(T): Void")
    
    # Create instances with different type arguments
    env = Environment(type_env)
    
    print("\n  Creating Box<Int> and Box<String> instances:")
    int_box = NewObject("Box", ["Int"]).evaluate(env)
    int_box.set_field("value", 42)
    print(f"    Box<Int> with value: {int_box}")
    
    str_box = NewObject("Box", ["String"]).evaluate(env)
    str_box.set_field("value", "Hello")
    print(f"    Box<String> with value: {str_box}")
    
    # Example 2: Bounded polymorphism
    print("\n  Example 2: Bounded Polymorphism")
    print("-" * 70)
    
    # Define Animal hierarchy
    animal = ClassDef("Animal")
    animal.add_field(Field("name", STRING_TYPE, "Unknown"))
    type_env.register_type(animal)
    
    dog = ClassDef("Dog")
    dog.superclass = animal
    dog.add_field(Field("breed", STRING_TYPE, "Mixed"))
    type_env.register_type(dog)
    type_env.add_subtype_relation(dog, animal)
    
    # Define AnimalBox<T extends Animal>
    T_bounded = TypeParameter("T", variance="covariant", bound=animal)
    animal_box = GenericClassDef("AnimalBox", [T_bounded])
    animal_box.add_field(Field("animal", T_bounded, None))
    type_env.register_type(animal_box)
    
    print(f"    Defined: {animal_box}")
    print(f"    Type parameter: {T_bounded}")
    print(f"    Bound: T must be subtype of Animal")
    
    # Create AnimalBox<Dog> (valid because Dog <: Animal)
    dog_box = NewObject("AnimalBox", ["Dog"]).evaluate(env)
    my_dog = NewObject("Dog").evaluate(env)
    my_dog.set_field("name", "Buddy")
    my_dog.set_field("breed", "Golden Retriever")
    dog_box.set_field("animal", my_dog)
    print(f"\n    Created: {dog_box}")
    
    # Example 3: Variance demonstration
    print("\n  Example 3: Variance (Categorical Properties)")
    print("-" * 70)
    
    print("  Covariant functor Box<T>:")
    print("    If Dog <: Animal, then Box<Dog> <: Box<Animal>  ")
    
    box_dog_type = GenericType(box_class, [dog])
    box_animal_type = GenericType(box_class, [animal])
    is_subtype = type_env.is_subtype(box_dog_type, box_animal_type)
    print(f"    Box<Dog> <: Box<Animal>? {is_subtype}")
    
    # Example 4: Contravariant functors
    print("\n  Example 4: Contravariant Functor")
    print("-" * 70)
    
    # Define Comparator<T> (contravariant)
    T_contra = TypeParameter("T", variance="contravariant")
    comparator_class = GenericClassDef("Comparator", [T_contra])
    comparator_class.add_method(Method(
        "compare",
        ["a", "b"],
        [T_contra, T_contra],
        INT_TYPE,
        ReturnStatement(IntLiteral(0))  # Simplified
    ))
    type_env.register_type(comparator_class)
    
    print(f"    Defined: {comparator_class}")
    print(f"    Type parameter: {T_contra}")
    print(f"    Contravariant: If Dog <: Animal, then Comparator<Animal> <: Comparator<Dog>")
    
    comp_dog_type = GenericType(comparator_class, [dog])
    comp_animal_type = GenericType(comparator_class, [animal])
    is_contra_subtype = type_env.is_subtype(comp_animal_type, comp_dog_type)
    print(f"\n    Comparator<Animal> <: Comparator<Dog>? {is_contra_subtype}")
    
    # Example 5: Pair<T, U> (product type, both covariant)
    print("\n  Example 5: Pair<T, U> (Binary Functor)")
    print("-" * 70)
    
    T_pair = TypeParameter("T", variance="covariant")
    U_pair = TypeParameter("U", variance="covariant")
    pair_class = GenericClassDef("Pair", [T_pair, U_pair])
    pair_class.add_field(Field("first", T_pair, None))
    pair_class.add_field(Field("second", U_pair, None))
    type_env.register_type(pair_class)
    
    print(f"    Defined: {pair_class}")
    print(f"    Functor: Type × Type → Type")
    print(f"    Both parameters covariant")
    
    # Create Pair<Int, String>
    pair = NewObject("Pair", ["Int", "String"]).evaluate(env)
    pair.set_field("first", 42)
    pair.set_field("second", "Answer")
    print(f"\n    Created: {pair}")
    
    # Example 6: Function composition with generics
    print("\n  Example 6: Generic Methods (Higher-Order)")
    print("-" * 70)
    
    # Define Optional<T> (Maybe monad)
    T_opt = TypeParameter("T", variance="covariant")
    optional_class = GenericClassDef("Optional", [T_opt])
    optional_class.add_field(Field("hasValue", BOOL_TYPE, False))
    optional_class.add_field(Field("value", T_opt, None))
    optional_class.add_method(Method(
        "getOrElse",
        ["default"],
        [T_opt],
        T_opt,
        BlockStatement([
            ReturnStatement(
                Variable("value")  # Simplified - would need if-else
            )
        ])
    ))
    type_env.register_type(optional_class)
    
    print(f"    Defined: {optional_class}")
    print(f"    Monad-like structure (simplified)")
    
    # Create Optional<Int>
    opt_int = NewObject("Optional", ["Int"]).evaluate(env)
    opt_int.set_field("hasValue", True)
    opt_int.set_field("value", 100)
    print(f"\n    Created: {opt_int}")
    
    # Example 7: List<T> with covariance
    print("\n  Example 7: List<T> (Covariant Collection)")
    print("-" * 70)
    
    T_list = TypeParameter("T", variance="covariant")
    list_class = GenericClassDef("List", [T_list])
    list_class.add_field(Field("size", INT_TYPE, 0))
    # Simplified - would normally have internal array
    type_env.register_type(list_class)
    
    print(f"    Defined: {list_class}")
    print(f"    Covariant functor over element type")
    
    # List<Dog> <: List<Animal> because of covariance
    list_dog_type = GenericType(list_class, [dog])
    list_animal_type = GenericType(list_class, [animal])
    print(f"\n    List<Dog> <: List<Animal>? {type_env.is_subtype(list_dog_type, list_animal_type)}")
    
    # Summary
    print("\n" + "-" * 70)
    print("CATEGORICAL PROPERTIES DEMONSTRATED:")
    print("-" * 70)
    print("  Generics as Endofunctors: F: Type → Type")
    print("  Covariance: F(A) <: F(B) when A <: B")
    print("  Contravariance: F(B) <: F(A) when A <: B")
    print("  Invariance: F(A) = F(B) only when A = B")
    print("  Bounded Polymorphism: Universal properties")
    print("  Type Substitution: Functorial mapping")
    print("  Binary Functors: Type × Type → Type")
    print("-" * 70)

if __name__ == "__main__":
    demo()
