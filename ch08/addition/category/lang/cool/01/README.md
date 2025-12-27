
## Categorical Object-Oriented Language (COOL)

*An experimental toy OOP language built on category theory concepts*

```text
                  ┌───────────────┐
                  │   Category    │
                  │   of Types    │
                  └──────┬────────┘
                         │
             Subtyping morphisms (inheritance)
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
   ┌─────────┐     ┌─────────┐     ┌─────────┐
   │  Animal │◄─── │   Dog   │     │   Cat   │
   └─────────┘     └─────────┘     └─────────┘
         ▲               ▲                ▲
         │      Natural transformations   │
         │         (method dispatch)      │
         └────────────────────────────────┘
```

### What is this project?

*COOL* is a starting point, a *minimal, educational toy programming language*
that tries to implement classical object-oriented programming concepts using
the language and intuition of *category theory*.

The main idea is to show that many OOP concepts can be naturally understood as categorical constructions:

| OOP Concept              | Category Theory Interpretation                      | Implementation in COOL                     |
|--------------------------|-----------------------------------------------------|--------------------------------------------|
| Class                    | Object in a category                                | `ClassDef` inherits from `Type`            |
| Inheritance              | Morphism (arrow) between objects                    | `SubtypeMorphism` + subtyping graph        |
| Subtyping                | Existence of a morphism A → B                       | `is_subtype()` checks path in graph        |
| Polymorphism             | Natural transformation between functors             | Dynamic method lookup (`get_method`)       |
| Method overriding        | Different implementations of the same transformation| Method table shadowing in inheritance      |
| Interface                | Universal property / specification of morphisms     | `Interface` with signature matching        |
| Object instantiation     | Element of a type (object)                          | `ObjectInstance` with runtime field values |
| `this` / self            | Identity morphism                                   | Passed implicitly in method environment    |


### Features (as implemented)

- Very simple static type system with subtyping
- Single inheritance
- Classes, fields, methods
- Polymorphic method dispatch
- Basic expressions: literals, variables, binary ops, field access, method calls, new, cast
- Statements: variables, assignment, if, block, return, print
- Runtime object instances with prototype-style field lookup through inheritance chain
- Demonstration program using animals (classic OOP example)


### Current Limitations

- No real parser -> everything is hand-constructed in Python
- Very limited type system (no generics, no unions, no self-types..)
- No closures / lambdas
- No exception handling
- No modules/packages
- Very naive method lookup (just recursive superclass lookup)
- No multiple inheritance / mixins / traits
- Very primitive error handling


### How does it work?

1. *Type Environment* keeps track of all known types and subtyping relations (basically a category)
2. *Classes* are special types that also carry fields + methods
3. *Subtyping* is modeled as morphisms in a graph (transitive closure = composition)
4. *Objects* at runtime are simple dictionaries + a pointer to their class
5. *Method calls* perform dynamic dispatch by walking the inheritance chain (natural transformation application)
6. *Environment* uses chained dictionaries for lexical scoping + `this` binding


### Interesting parts

```python
# Most "categorical" pieces:

class SubtypeMorphism(Morphism):           # A <: B is really a morphism
    def compose(self, other): ..

class TypeEnvironment:
    def is_subtype(self, a, b) -> bool:    # morphism existence check
    def get_morphism_chain(..) -> ..       # actually reconstructs path

class ClassDef.get_method(name):           # natural transformation lookup
    # walks inheritance = follows morphisms upward
```


### Possible extensions ..

```text
- Real parser (even very simple one)
- Parametric polymorphism (generics ≈ functors)
- Multiple inheritance / mixin composition (colimits?)
- Algebraic effects / monadic IO (Kleisli category)
- Kind-level types (2-category)
- Dependent types (very hard)
- Visualisation of the category of types (graphviz?)
```
