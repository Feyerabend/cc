
## Cat Algol

A categorical programming experiment in C

This project is a prototype that models basic elements of
*category theory* directly in C. It defines:
- *Objects* (types such as integers, booleans, unit, product types)
- *Morphisms* (functions between objects)
- *Composition* of morphisms
- *Functors* (structure-preserving mappings between categories)
- A small virtual machine layer to evaluate categorical expressions

The goal is to treat fragments of C code as if they were objects and morphisms
in the sense of category theory, allowing categorical reasoning at the systems level.


### Objects

Objects in this system represent *types* or structured values.
The implementation uses an enumeration:

```c
typedef enum {
    OBJ_INT,
    OBJ_BOOL,
    OBJ_UNIT,
    OBJ_PRODUCT,
    OBJ_ARROW,
    OBJ_FUNCTOR_APP
} ObjectTag;
```

In categorical terms:
- These form the *objects in a category*.
- A product type corresponds to a *categorical product*.
- `OBJ_ARROW` represents the *hom-set* construction (a type of morphism object).

The code treats objects not simply as runtime values, but as *first-class structural entities*.
An integer value is an instance of `OBJ_INT`, but the category cares about the *role* of `OBJ_INT`
as a node in the graph of composable arrows.


### Morphisms

Morphisms represent *arrows between objects*. They are implemented as C functions with metadata
describing their domain and codomain. In this prototype, functions are wrapped with descriptors
that state their type signature.

Conceptually:
- If `f: A -> B` and `g: B -> C`, the composition `g ∘ f` is also a morphism in the system.
- The code ensures the domain of `g` matches the codomain of `f`, enforcing categorical
  composition rules at runtime.


### Composition

Composition is implemented by creating a new morphism whose application executes
`f` and then feeds its output into `g`.

In categorical language:
```
(A --f--> B) --g--> C  ⇒  A --(g∘f)--> C
```

In C, composition behaves like:
```c
Value composed(Value x) {
    return g(f(x));
}
```

The system tracks this as:
- domain: A
- codomain: C
- proof obligations verified at runtime using assertions


### Functors

Functors are implemented as mappings from:
- objects to objects
- morphisms to morphisms

A functor `F` is represented as a structure with function pointers that define
how to translate an object tag and a morphism descriptor. The functor tests demonstrate:
1. Identity functors
2. Functors over container-like objects
3. Type-transforming functors that preserve composition structure

When the code applies a functor to a morphism, it verifies:
`F(g ∘ f) = F(g) ∘ F(f)`.

This is the *functoriality law*, enforced operationally.



### Category Theory in Practice

| Category Theory Term | In This Code |
|----------------------|--------------|
| Object               | Tagged type (`OBJ_INT`, etc.) |
| Morphism             | Function descriptor with domain/codomain |
| Composition          | New morphism from chaining functions |
| Identity Morphism    | A function returning its argument unchanged |
| Product Object       | Pair of objects, matched with C structs |
| Functor              | Mapping of object and morphism constructors |
| Functoriality Law    | Verified by tests and assertive composition |

This prototype therefore models a fragment of the category *Set*, with
extensions toward the category of types and functions seen in typed lambda calculus.



### Execution Model

The code includes a tiny VM that:
- Stores objects and morphisms
- Executes morphism application
- Simulates container application for functors

This forms a *categorical interpreter* where programs are diagrams, not just statements.



### Example Workflow

1. Define base objects (e.g. `OBJ_INT`).
2. Wrap C functions as morphisms with declared signatures.
3. Compose morphisms to form new arrows.
4. Apply functors to objects and arrows.
5. Evaluate via the VM.

This project demonstrates:
- How category theory can be used to structure low-level systems code
- How function composition can be treated as a runtime entity
- How functors offer a uniform way to lift computations into containers
- How categorical thinking clarifies program invariants

The wider implication is a path toward *categorical virtual machines*,
where program correctness is a consequence of the structure of the category.


### Roadmap for Your Projects ..

- Add monads for sequencing and computational effects
- Implement natural transformations between functors
- Extend product types to coproducts (sum types)
- Integrate type inference to validate composition statically
- Provide graph visualisation of morphism networks

