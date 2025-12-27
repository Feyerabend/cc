"""
Categorical Object-Oriented Language (COOL) with Algebraic Data Types
=====================================================================
An OOP language where:
- Sum types are coproducts in the category
- Product types are products in the category
- Pattern matching is case analysis (initial algebra)
- Recursive types are fixed points of functors
- Catamorphisms are the unique morphism from initial algebra
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Set, Tuple, Optional, Union
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
UNIT_TYPE = Type("Unit")  # Terminal object


@dataclass
class TypeParameter(Type):
    """Type parameter (type variable in functors)"""
    variance: str = "invariant"
    bound: Optional[Type] = None
    
    def __init__(self, name: str, variance: str = "invariant", bound: Optional[Type] = None):
        super().__init__(name)
        self.variance = variance
        self.bound = bound


@dataclass
class GenericType(Type):
    """Generic type application: F<T>"""
    base: Type
    type_args: List[Type]
    
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
class ProductType(Type):
    """Product type: A × B (categorical product)"""
    components: List[Tuple[str, Type]]
    
    def __init__(self, components: List[Tuple[str, Type]]):
        self.components = components
        names = ", ".join(f"{name}: {typ}" for name, typ in components)
        super().__init__(f"({names})")
    
    def __eq__(self, other):
        return isinstance(other, ProductType) and self.components == other.components
    
    def __hash__(self):
        return hash(tuple(self.components))


@dataclass
class SumType(Type):
    """Sum type: A + B (categorical coproduct)"""
    variants: Dict[str, Optional[Type]]  # Constructor name -> payload type
    
    def __init__(self, name: str, variants: Dict[str, Optional[Type]]):
        super().__init__(name)
        self.variants = variants
    
    def __eq__(self, other):
        return isinstance(other, SumType) and self._name == other._name
    
    def __hash__(self):
        return hash(self._name)


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



# SUBTYPING MORPHISMS


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



# TYPE ENVIRONMENT


class TypeEnvironment:
    """Manages the category of types and subtyping relations"""
    
    def __init__(self):
        self.types: Dict[str, Type] = {
            "Int": INT_TYPE,
            "String": STRING_TYPE,
            "Bool": BOOL_TYPE,
            "Void": VOID_TYPE,
            "Unit": UNIT_TYPE,
        }
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
        
        # Handle generic types
        if isinstance(subtype, GenericType) and isinstance(supertype, GenericType):
            if subtype.base != supertype.base:
                if not self.is_subtype(subtype.base, supertype.base):
                    return False
            return subtype.type_args == supertype.type_args
        
        # BFS to find path
        visited = set()
        queue = [subtype]
        
        while queue:
            current = queue.pop(0)
            if current == supertype:
                return True
            
            if current in visited:
                continue
            visited.add(current)
            
            for sup, subs in self.subtype_graph.items():
                if current in subs:
                    queue.append(sup)
        
        return False
    
    def substitute_type_params(self, typ: Type, substitutions: Dict[str, Type]) -> Type:
        """Substitute type parameters (functorial mapping)"""
        if isinstance(typ, TypeParameter):
            return substitutions.get(typ.name(), typ)
        elif isinstance(typ, GenericType):
            new_args = [self.substitute_type_params(arg, substitutions) for arg in typ.type_args]
            return GenericType(typ.base, new_args)
        return typ



# RUNTIME VALUES


@dataclass
class Value(ABC):
    """Base runtime value"""
    pass


@dataclass
class IntValue(Value):
    value: int
    
    def __str__(self):
        return str(self.value)


@dataclass
class StringValue(Value):
    value: str
    
    def __str__(self):
        return f'"{self.value}"'


@dataclass
class BoolValue(Value):
    value: bool
    
    def __str__(self):
        return str(self.value).lower()


@dataclass
class UnitValue(Value):
    """Unit value (terminal object)"""
    def __str__(self):
        return "()"


@dataclass
class ProductValue(Value):
    """Product value (tuple)"""
    values: Dict[str, Value]
    
    def __str__(self):
        items = ", ".join(f"{k}={v}" for k, v in self.values.items())
        return f"({items})"


@dataclass
class SumValue(Value):
    """Sum value (tagged union)"""
    constructor: str
    payload: Optional[Value]
    sum_type: SumType
    
    def __str__(self):
        if self.payload:
            return f"{self.constructor}({self.payload})"
        return self.constructor


@dataclass
class ListValue(Value):
    """List value (recursive ADT)"""
    elements: List[Value]
    
    def __str__(self):
        items = ", ".join(str(e) for e in self.elements)
        return f"[{items}]"


@dataclass
class ObjectInstance(Value):
    """Object instance"""
    class_def: 'ClassDef'
    field_values: Dict[str, Value] = field(default_factory=dict)
    
    def get_field(self, name: str) -> Value:
        return self.field_values.get(name)
    
    def set_field(self, name: str, value: Value):
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
    def evaluate(self, env: 'Environment') -> Value:
        pass


@dataclass
class IntLiteral(Expression):
    value: int
    
    def type_check(self, env, type_env):
        return INT_TYPE
    
    def evaluate(self, env):
        return IntValue(self.value)


@dataclass
class StringLiteral(Expression):
    value: str
    
    def type_check(self, env, type_env):
        return STRING_TYPE
    
    def evaluate(self, env):
        return StringValue(self.value)


@dataclass
class BoolLiteral(Expression):
    value: bool
    
    def type_check(self, env, type_env):
        return BOOL_TYPE
    
    def evaluate(self, env):
        return BoolValue(self.value)


@dataclass
class UnitLiteral(Expression):
    """Unit literal - terminal object"""
    
    def type_check(self, env, type_env):
        return UNIT_TYPE
    
    def evaluate(self, env):
        return UnitValue()


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
        
        if self.op == '+':
            if left_type == right_type == INT_TYPE:
                return INT_TYPE
            elif left_type == right_type == STRING_TYPE:
                return STRING_TYPE
        elif self.op in ['-', '*', '/']:
            if left_type == INT_TYPE and right_type == INT_TYPE:
                return INT_TYPE
        elif self.op in ['==', '<', '>', '<=', '>=']:
            return BOOL_TYPE
        
        raise TypeError(f"Type error in binary operation {self.op}")
    
    def evaluate(self, env):
        left = self.left.evaluate(env)
        right = self.right.evaluate(env)
        
        if self.op == '+':
            if isinstance(left, IntValue) and isinstance(right, IntValue):
                return IntValue(left.value + right.value)
            elif isinstance(left, StringValue) and isinstance(right, StringValue):
                return StringValue(left.value + right.value)
        elif self.op == '-' and isinstance(left, IntValue) and isinstance(right, IntValue):
            return IntValue(left.value - right.value)
        elif self.op == '*' and isinstance(left, IntValue) and isinstance(right, IntValue):
            return IntValue(left.value * right.value)
        elif self.op == '//' and isinstance(left, IntValue) and isinstance(right, IntValue):
            return IntValue(left.value // right.value)
        elif self.op == '==':
            return BoolValue(str(left) == str(right))
        elif self.op == '<' and isinstance(left, IntValue) and isinstance(right, IntValue):
            return BoolValue(left.value < right.value)
        
        raise RuntimeError(f"Runtime error in binary operation {self.op}")


@dataclass
class ProductExpr(Expression):
    """Product construction (tuple literal)"""
    components: Dict[str, Expression]
    
    def type_check(self, env, type_env):
        typed_components = [(name, expr.type_check(env, type_env)) 
                           for name, expr in self.components.items()]
        return ProductType(typed_components)
    
    def evaluate(self, env):
        values = {name: expr.evaluate(env) for name, expr in self.components.items()}
        return ProductValue(values)


@dataclass
class ProductAccess(Expression):
    """Product projection (tuple field access)"""
    expr: Expression
    field_name: str
    
    def type_check(self, env, type_env):
        prod_type = self.expr.type_check(env, type_env)
        if not isinstance(prod_type, ProductType):
            raise TypeError(f"Cannot access field on non-product type")
        
        for name, typ in prod_type.components:
            if name == self.field_name:
                return typ
        raise TypeError(f"Field {self.field_name} not found in product")
    
    def evaluate(self, env):
        prod_val = self.expr.evaluate(env)
        if not isinstance(prod_val, ProductValue):
            raise RuntimeError("Cannot access field on non-product value")
        return prod_val.values[self.field_name]


@dataclass
class SumConstructor(Expression):
    """Sum type constructor (injection into coproduct)"""
    sum_type_name: str
    constructor: str
    payload: Optional[Expression]
    
    def type_check(self, env, type_env):
        sum_type = type_env.types.get(self.sum_type_name)
        if not isinstance(sum_type, SumType):
            raise TypeError(f"{self.sum_type_name} is not a sum type")
        
        if self.constructor not in sum_type.variants:
            raise TypeError(f"Unknown constructor {self.constructor}")
        
        expected_type = sum_type.variants[self.constructor]
        if expected_type is None:
            if self.payload is not None:
                raise TypeError(f"Constructor {self.constructor} takes no payload")
        else:
            if self.payload is None:
                raise TypeError(f"Constructor {self.constructor} requires payload")
            payload_type = self.payload.type_check(env, type_env)
            if not type_env.is_subtype(payload_type, expected_type):
                raise TypeError(f"Payload type mismatch")
        
        return sum_type
    
    def evaluate(self, env):
        sum_type = env.type_env.types[self.sum_type_name]
        payload_val = self.payload.evaluate(env) if self.payload else None
        return SumValue(self.constructor, payload_val, sum_type)


@dataclass
class PatternCase:
    """Pattern matching case"""
    constructor: str
    binder: Optional[str]  # Variable name for payload
    body: 'Statement'


@dataclass
class Match(Expression):
    """Pattern matching (catamorphism from initial algebra)"""
    scrutinee: Expression
    cases: List[PatternCase]
    
    def type_check(self, env, type_env):
        scrutinee_type = self.scrutinee.type_check(env, type_env)
        
        if not isinstance(scrutinee_type, SumType):
            raise TypeError("Can only match on sum types")
        
        # Check exhaustiveness
        covered = {case.constructor for case in self.cases}
        required = set(scrutinee_type.variants.keys())
        if covered != required:
            missing = required - covered
            raise TypeError(f"Non-exhaustive pattern match. Missing: {missing}")
        
        # All cases must return same type
        case_types = []
        for case in self.cases:
            case_env = env.extend()
            if case.binder:
                payload_type = scrutinee_type.variants[case.constructor]
                if payload_type:
                    case_env.define(case.binder, None, payload_type)
            case_type = case.body.get_return_type(case_env, type_env)
            case_types.append(case_type)
        
        # For simplicity, require all same type
        result_type = case_types[0]
        for ct in case_types[1:]:
            if ct != result_type:
                raise TypeError("All match cases must return same type")
        
        return result_type
    
    def evaluate(self, env):
        scrutinee_val = self.scrutinee.evaluate(env)
        
        if not isinstance(scrutinee_val, SumValue):
            raise RuntimeError("Can only match on sum values")
        
        for case in self.cases:
            if case.constructor == scrutinee_val.constructor:
                case_env = env.extend()
                if case.binder and scrutinee_val.payload:
                    case_env.define(case.binder, scrutinee_val.payload, 
                                  scrutinee_val.sum_type.variants[case.constructor])
                return case.body.execute(case_env)
        
        raise RuntimeError("Non-exhaustive match (runtime)")


@dataclass
class ListLiteral(Expression):
    """List literal [a, b, c]"""
    elements: List[Expression]
    
    def type_check(self, env, type_env):
        if not self.elements:
            # Empty list - need type annotation in real system
            return type_env.types["List"]
        
        elem_type = self.elements[0].type_check(env, type_env)
        for elem in self.elements[1:]:
            et = elem.type_check(env, type_env)
            if et != elem_type:
                raise TypeError("All list elements must have same type")
        
        list_type = type_env.types.get("List")
        return GenericType(list_type, [elem_type])
    
    def evaluate(self, env):
        values = [elem.evaluate(env) for elem in self.elements]
        return ListValue(values)


@dataclass
class ListCons(Expression):
    """List cons operation: head :: tail"""
    head: Expression
    tail: Expression
    
    def type_check(self, env, type_env):
        head_type = self.head.type_check(env, type_env)
        tail_type = self.tail.type_check(env, type_env)
        
        if not isinstance(tail_type, GenericType) or tail_type.base.name() != "List":
            raise TypeError("Cons tail must be a List")
        
        if tail_type.type_args[0] != head_type:
            raise TypeError("Cons head type must match list element type")
        
        return tail_type
    
    def evaluate(self, env):
        head_val = self.head.evaluate(env)
        tail_val = self.tail.evaluate(env)
        
        if not isinstance(tail_val, ListValue):
            raise RuntimeError("Cons tail must be a list")
        
        return ListValue([head_val] + tail_val.elements)


@dataclass
class NewObject(Expression):
    """Object instantiation"""
    class_name: str
    type_args: List[str] = field(default_factory=list)
    
    def type_check(self, env, type_env):
        if self.class_name not in type_env.types:
            raise TypeError(f"Unknown class: {self.class_name}")
        return type_env.types[self.class_name]
    
    def evaluate(self, env):
        cls = env.type_env.types[self.class_name]
        if not isinstance(cls, ClassDef):
            raise RuntimeError(f"{self.class_name} is not a class")
        
        obj = ObjectInstance(cls)
        for field_name, field in cls.all_fields().items():
            default_val = field.value or self._default_value(field.type)
            obj.set_field(field_name, default_val)
        return obj
    
    def _default_value(self, typ: Type):
        if typ == INT_TYPE:
            return IntValue(0)
        elif typ == STRING_TYPE:
            return StringValue("")
        elif typ == BOOL_TYPE:
            return BoolValue(False)
        return UnitValue()


@dataclass
class FieldAccess(Expression):
    """obj.field"""
    obj: Expression
    field_name: str
    
    def type_check(self, env, type_env):
        obj_type = self.obj.type_check(env, type_env)
        if not isinstance(obj_type, ClassDef):
            raise TypeError(f"Cannot access field on non-object type")
        
        field = obj_type.get_field(self.field_name)
        if not field:
            raise TypeError(f"Field {self.field_name} not found")
        return field.type
    
    def evaluate(self, env):
        obj = self.obj.evaluate(env)
        if not isinstance(obj, ObjectInstance):
            raise RuntimeError("Cannot access field on non-object")
        return obj.get_field(self.field_name)


# STATEMENTS


class Statement(ABC):
    """Base statement"""
    @abstractmethod
    def execute(self, env: 'Environment') -> Optional[Value]:
        pass
    
    def get_return_type(self, env: 'Environment', type_env: TypeEnvironment) -> Type:
        """Get the return type of this statement (for type checking)"""
        return UNIT_TYPE


@dataclass
class ExprStatement(Statement):
    expr: Expression
    
    def execute(self, env):
        return self.expr.evaluate(env)
    
    def get_return_type(self, env, type_env):
        return self.expr.type_check(env, type_env)


@dataclass
class VarDecl(Statement):
    name: str
    type_str: Optional[str]
    type_args: List[str]
    value: Expression
    
    def execute(self, env):
        val = self.value.evaluate(env)
        
        if self.type_str:
            if self.type_args:
                base_type = env.type_env.types[self.type_str]
                type_arg_types = [env.type_env.types[ta] for ta in self.type_args]
                typ = GenericType(base_type, type_arg_types)
            else:
                typ = env.type_env.types[self.type_str]
        else:
            # Type inference
            typ = self.value.type_check(env, env.type_env)
        
        env.define(self.name, val, typ)
        return None


@dataclass
class Assignment(Statement):
    target: Expression
    value: Expression
    
    def execute(self, env):
        val = self.value.evaluate(env)
        
        if isinstance(self.target, Variable):
            typ = env.get_type(self.target.name)
            env.define(self.target.name, val, typ)
        elif isinstance(self.target, FieldAccess):
            obj = self.target.obj.evaluate(env)
            if isinstance(obj, ObjectInstance):
                obj.set_field(self.target.field_name, val)
        else:
            raise RuntimeError("Invalid assignment target")
        
        return None


@dataclass
class BlockStatement(Statement):
    statements: List[Statement]
    
    def execute(self, env):
        result = None
        for stmt in self.statements:
            result = stmt.execute(env)
        return result
    
    def get_return_type(self, env, type_env):
        if not self.statements:
            return UNIT_TYPE
        return self.statements[-1].get_return_type(env, type_env)


@dataclass
class ReturnStatement(Statement):
    value: Expression
    
    def execute(self, env):
        return self.value.evaluate(env)
    
    def get_return_type(self, env, type_env):
        return self.value.type_check(env, type_env)


@dataclass
class PrintStatement(Statement):
    expr: Expression
    
    def execute(self, env):
        val = self.expr.evaluate(env)
        print(f"  >> {val}")
        return None


# CLASS DEFINITIONS


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
    body: Statement
    
    def signature(self) -> FunctionType:
        return FunctionType(self.param_types, self.return_type)


class ClassDef(Type):
    """Class definition"""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.class_fields: Dict[str, Field] = {}
        self.methods: Dict[str, Method] = {}
        self.superclass: Optional['ClassDef'] = None
    
    def add_field(self, f: Field):
        self.class_fields[f.name] = f
    
    def add_method(self, m: Method):
        self.methods[m.name] = m
    
    def get_field(self, name: str) -> Optional[Field]:
        if name in self.class_fields:
            return self.class_fields[name]
        if self.superclass:
            return self.superclass.get_field(name)
        return None
    
    def get_method(self, name: str) -> Optional[Method]:
        if name in self.methods:
            return self.methods[name]
        if self.superclass:
            return self.superclass.get_method(name)
        return None
    
    def all_fields(self) -> Dict[str, Field]:
        result = {}
        if self.superclass:
            result.update(self.superclass.all_fields())
        result.update(self.class_fields)
        return result


# ENVIRONMENT


class Environment:
    """Runtime environment"""
    def __init__(self, type_env: TypeEnvironment, parent: Optional['Environment'] = None):
        self.type_env = type_env
        self.parent = parent
        self.bindings: Dict[str, Tuple[Value, Type]] = {}
    
    def define(self, name: str, value: Value, typ: Type):
        self.bindings[name] = (value, typ)
    
    def get_value(self, name: str) -> Value:
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
    print("=" * 70)
    print("COOL with ALGEBRAIC DATA TYPES")
    print("=" * 70)
    print("Categorical structures:")
    print("- Sum types as coproducts")
    print("- Product types as products")
    print("- Pattern matching as catamorphisms")
    print("- Recursive types as fixed points")
    print("=" * 70)
    
    type_env = TypeEnvironment()
    env = Environment(type_env)
    
    # Example 1: Simple Sum Type (Option)
    print("\n" + "=" * 70)
    print("Example 1: Option<T> - Simple Sum Type (Coproduct)")
    print("=" * 70)
    
    # Define Option<T> = None | Some(T)
    option_int = SumType("OptionInt", {
        "None": None,
        "Some": INT_TYPE
    })
    type_env.register_type(option_int)
    
    print("Defined: OptionInt = None | Some(Int)")
    print("\nCreating values:")
    
    none_val = SumConstructor("OptionInt", "None", None).evaluate(env)
    print(f"  none = {none_val}")
    
    some_val = SumConstructor("OptionInt", "Some", IntLiteral(42)).evaluate(env)
    print(f"  some = {some_val}")
    
    print("\nPattern matching (catamorphism):")
    match_expr = Match(
        Variable("opt"),
        [
            PatternCase("None", None, ReturnStatement(IntLiteral(0))),
            PatternCase("Some", "x", ReturnStatement(Variable("x")))
        ]
    )
    
    env.define("opt", none_val, option_int)
    result = match_expr.evaluate(env)
    print(f"  match none => {result}")
    
    env.define("opt", some_val, option_int)
    result = match_expr.evaluate(env)
    print(f"  match some => {result}")
    
    # Example 2: Either (Binary Coproduct)
    print("\n" + "=" * 70)
    print("Example 2: Either<String, Int> - Binary Coproduct")
    print("=" * 70)
    
    either_type = SumType("Either", {
        "Left": STRING_TYPE,
        "Right": INT_TYPE
    })
    type_env.register_type(either_type)
    
    print("Defined: Either = Left(String) | Right(Int)")
    print("\nCreating values:")
    
    left_val = SumConstructor("Either", "Left", StringLiteral("Error!")).evaluate(env)
    print(f"  left = {left_val}")
    
    right_val = SumConstructor("Either", "Right", IntLiteral(100)).evaluate(env)
    print(f"  right = {right_val}")
    
    print("\nPattern matching to extract value:")
    either_match = Match(
        Variable("result"),
        [
            PatternCase("Left", "err", BlockStatement([
                PrintStatement(StringLiteral("Error occurred:")),
                PrintStatement(Variable("err")),
                ReturnStatement(IntLiteral(-1))
            ])),
            PatternCase("Right", "val", ReturnStatement(Variable("val")))
        ]
    )
    
    env.define("result", right_val, either_type)
    output = either_match.evaluate(env)
    print(f"  Result: {output}")
    
    # Example 3: Product Types (Tuples)
    print("\n" + "=" * 70)
    print("Example 3: Product Types (Categorical Product)")
    print("=" * 70)
    
    print("Creating tuple: (name: String, age: Int, active: Bool)")
    person_tuple = ProductExpr({
        "name": StringLiteral("Alice"),
        "age": IntLiteral(30),
        "active": BoolLiteral(True)
    }).evaluate(env)
    
    print(f"  person = {person_tuple}")
    
    print("\nProjections (π₁, π₂, π₃):")
    env.define("person", person_tuple, ProductType([
        ("name", STRING_TYPE),
        ("age", INT_TYPE),
        ("active", BOOL_TYPE)
    ]))
    
    name = ProductAccess(Variable("person"), "name").evaluate(env)
    age = ProductAccess(Variable("person"), "age").evaluate(env)
    print(f"  person.name = {name}")
    print(f"  person.age = {age}")
    
    # Example 4: Recursive ADT - Binary Tree
    print("\n" + "=" * 70)
    print("Example 4: Binary Tree - Recursive ADT")
    print("=" * 70)
    
    # Define Tree = Leaf | Node(Int, Tree, Tree)
    tree_type = SumType("Tree", {
        "Leaf": None,
        "Node": ProductType([
            ("value", INT_TYPE),
            ("left", Type("Tree")),  # Recursive reference
            ("right", Type("Tree"))
        ])
    })
    type_env.register_type(tree_type)
    type_env.types["Tree"] = tree_type
    
    print("Defined: Tree = Leaf | Node(Int, Tree, Tree)")
    print("\nBuilding tree:")
    print("        5")
    print("       / \\")
    print("      3   7")
    print("     /")
    print("    1")
    
    # Manually construct tree (simplified)
    leaf = SumConstructor("Tree", "Leaf", None).evaluate(env)
    
    node1 = SumValue("Node", ProductValue({
        "value": IntValue(1),
        "left": leaf,
        "right": leaf
    }), tree_type)
    
    node3 = SumValue("Node", ProductValue({
        "value": IntValue(3),
        "left": node1,
        "right": leaf
    }), tree_type)
    
    node7 = SumValue("Node", ProductValue({
        "value": IntValue(7),
        "left": leaf,
        "right": leaf
    }), tree_type)
    
    root = SumValue("Node", ProductValue({
        "value": IntValue(5),
        "left": node3,
        "right": node7
    }), tree_type)
    
    print(f"\n  Tree structure created")
    
    # Example 5: List (Recursive Coproduct)
    print("\n" + "=" * 70)
    print("Example 5: Lists - Initial Algebra")
    print("=" * 70)
    
    # Define List type
    list_class = ClassDef("List")
    type_env.register_type(list_class)
    
    print("List as recursive ADT: List<T> = Nil | Cons(T, List<T>)")
    print("\nCreating lists:")
    
    nums = ListLiteral([IntLiteral(1), IntLiteral(2), IntLiteral(3)]).evaluate(env)
    print(f"  nums = {nums}")
    
    empty = ListLiteral([]).evaluate(env)
    print(f"  empty = {empty}")
    
    # Cons operation
    print("\nCons operation (3 :: [1, 2]):")
    consed = ListCons(
        IntLiteral(3),
        ListLiteral([IntLiteral(1), IntLiteral(2)])
    ).evaluate(env)
    print(f"  result = {consed}")
    
    # Example 6: Result Type (Like Rust)
    print("\n" + "=" * 70)
    print("Example 6: Result<T, E> - Error Handling")
    print("=" * 70)
    
    result_type = SumType("Result", {
        "Ok": INT_TYPE,
        "Err": STRING_TYPE
    })
    type_env.register_type(result_type)
    
    print("Defined: Result = Ok(Int) | Err(String)")
    print("\nSimulating division:")
    
    def safe_divide(a: int, b: int) -> SumValue:
        if b == 0:
            return SumValue("Err", StringValue("Division by zero"), result_type)
        return SumValue("Ok", IntValue(a // b), result_type)
    
    ok_result = safe_divide(10, 2)
    err_result = safe_divide(10, 0)
    
    print(f"  10 / 2 = {ok_result}")
    print(f"  10 / 0 = {err_result}")
    
    print("\nPattern matching on result:")
    result_match = Match(
        Variable("res"),
        [
            PatternCase("Ok", "val", BlockStatement([
                PrintStatement(StringLiteral("Success!")),
                ReturnStatement(Variable("val"))
            ])),
            PatternCase("Err", "msg", BlockStatement([
                PrintStatement(StringLiteral("Error:")),
                PrintStatement(Variable("msg")),
                ReturnStatement(IntLiteral(-1))
            ]))
        ]
    )
    
    env.define("res", err_result, result_type)
    result_match.evaluate(env)
    
    # Example 7: Boolean as Sum Type
    print("\n" + "=" * 70)
    print("Example 7: Bool as Sum Type (True | False)")
    print("=" * 70)
    
    bool_sum = SumType("BoolSum", {
        "True": None,
        "False": None
    })
    type_env.register_type(bool_sum)
    
    print("Defined: BoolSum = True | False")
    print("(Unit + Unit ≅ Bool in categorical sense)")
    
    true_val = SumConstructor("BoolSum", "True", None).evaluate(env)
    false_val = SumConstructor("BoolSum", "False", None).evaluate(env)
    
    print(f"\n  true = {true_val}")
    print(f"  false = {false_val}")
    
    print("\nPattern matching (if-then-else):")
    bool_match = Match(
        Variable("b"),
        [
            PatternCase("True", None, ReturnStatement(StringLiteral("yes"))),
            PatternCase("False", None, ReturnStatement(StringLiteral("no")))
        ]
    )
    
    env.define("b", true_val, bool_sum)
    result = bool_match.evaluate(env)
    print(f"  match true => {result}")
    
    # Example 8: Natural Numbers (Peano)
    print("\n" + "=" * 70)
    print("Example 8: Natural Numbers (Peano Arithmetic)")
    print("=" * 70)
    
    nat_type = SumType("Nat", {
        "Zero": None,
        "Succ": Type("Nat")  # Recursive
    })
    type_env.register_type(nat_type)
    type_env.types["Nat"] = nat_type
    
    print("Defined: Nat = Zero | Succ(Nat)")
    print("Numbers as recursive structure:")
    
    zero = SumValue("Zero", None, nat_type)
    one = SumValue("Succ", zero, nat_type)
    two = SumValue("Succ", one, nat_type)
    three = SumValue("Succ", two, nat_type)
    
    print(f"  0 = {zero}")
    print(f"  1 = {one}")
    print(f"  2 = {two}")
    print(f"  3 = {three}")
    
    # Summary
    print("\n" + "=" * 70)
    print("CATEGORICAL PROPERTIES DEMONSTRATED:")
    print("=" * 70)
    print("✓ Sum Types: Coproducts in Type category (A + B)")
    print("✓ Product Types: Products in Type category (A × B)")
    print("✓ Pattern Matching: Case analysis (catamorphism)")
    print("✓ Constructors: Injections into coproduct")
    print("✓ Projections: Morphisms from product")
    print("✓ Recursive Types: Fixed points of functors (μF)")
    print("✓ Initial Algebras: Lists, Trees, Nat as least fixed points")
    print("✓ Exhaustiveness: All constructors must be covered")
    print("✓ Type Safety: Well-typed programs preserve structure")
    print("=" * 70)
    
    print("\nKey Insights:")
    print("- Sum types model choice/alternatives (OR)")
    print("- Product types model combination (AND)")
    print("- Pattern matching is the eliminator for sum types")
    print("- Tuples provide projection (eliminators for products)")
    print("- Recursive ADTs are fixed points: μF where F is a functor")
    print("- Option ≅ 1 + T (terminal object + type)")
    print("- Bool ≅ 1 + 1 (two-element coproduct)")
    print("- List<T> ≅ μX. 1 + (T × X) (initial algebra)")


if __name__ == "__main__":
    demo()
