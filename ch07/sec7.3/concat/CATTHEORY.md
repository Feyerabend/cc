
### 1. Conceptual mapping

We interpret:

| Category Theory  | C Representation       |
|------------------|------------------------|
| Object           | Stack shape (implicit) |
| Morphism `A → B` | `void (*)(Stack*)`     |
| Composition      | Function chaining      |
| Tensor `⊗`       | Stack concatenation    |
| Identity         | No-op                  |
| swap             | Stack permutation      |
| dup              | Stack copy             |
| pop              | Stack discard          |



### 2. Stack representation

We’ll use a generic value stack:

```c
#include <stdio.h>
#include <stdlib.h>

#define STACK_MAX 256

typedef double Value;

typedef struct {
    Value data[STACK_MAX];
    int top;
} Stack;
```



#### Stack primitives

```c
void push(Stack *s, Value v) {
    if (s->top >= STACK_MAX) {
        printf("Stack overflow\n");
        exit(1);
    }
    s->data[s->top++] = v;
}

Value pop(Stack *s) {
    if (s->top <= 0) {
        printf("Stack underflow\n");
        exit(1);
    }
    return s->data[--s->top];
}
```



### 3. Morphisms

A morphism = stack transformer:

```c
typedef void (*Morphism)(Stack *);
```



### 4. Primitive categorical morphisms



#### Identity

```c
void id(Stack *s) {
    /* no-op */
}
```



#### swap : (A, B) → (B, A)

```c
void swap(Stack *s) {
    Value a = pop(s);
    Value b = pop(s);
    push(s, a);
    push(s, b);
}
```



#### dup : A → (A, A)

```c
void dup(Stack *s) {
    Value a = pop(s);
    push(s, a);
    push(s, a);
}
```



#### pop : A → I

```c
void drop(Stack *s) {
    pop(s);
}
```



### 5. Computational morphisms



#### add

```c
void add(Stack *s) {
    Value a = pop(s);
    Value b = pop(s);
    push(s, b + a);
}
```



#### mul

```c
void mul(Stack *s) {
    Value a = pop(s);
    Value b = pop(s);
    push(s, b * a);
}
```



### 6. Composition = categorical composition

We build a composed morphism.

Since C lacks closures, we simulate via a struct:



#### Composite morphism

```c
typedef struct {
    Morphism f;
    Morphism g;
} Composite;
```



#### Executor

```c
void run_composite(Stack *s, Composite *c) {
    c->f(s);
    c->g(s);
}
```



But we want arbitrary chains → use an array.



### 7. Program = list of morphisms

```c
typedef struct {
    Morphism code[STACK_MAX];
    int length;
} Program;
```



#### Run program

```c
void run(Stack *s, Program *p) {
    for (int i = 0; i < p->length; i++) {
        p->code[i](s);
    }
}
```



### 8. Building concatenative programs

```c
void program_init(Program *p) {
    p->length = 0;
}

void program_add(Program *p, Morphism m) {
    p->code[p->length++] = m;
}
```



### 9. Example program

Equivalent to:

```
dup add mul
```



```c
int main() {
    Stack s = {.top = 0};
    Program p;

    program_init(&p);

    program_add(&p, dup);
    program_add(&p, add);
    program_add(&p, mul);

    push(&s, 3);
    push(&s, 4);

    run(&s, &p);

    printf("Result: %f\n", pop(&s));
}
```



### 10. Tensor (⊗) at C level?

True tensor means:

```
f ⊗ g : (A, B) → (C, D)
```

We simulate by splitting stack.

Minimal approximation:



```c
void tensor(Stack *s, Morphism f, Morphism g) {
    /* naive demo — real version needs typed stack slicing */
    f(s);
    g(s);
}
```

A real implementation needs:

- Stack effect metadata
- Precise slicing
- Separate substack regions



### 11. Linear vs Cartesian discipline



#### Cartesian mode (default)

Allow:
* dup
* drop



#### Linear mode

Disallow duplication/discard:

```c
int LINEAR = 1;

void dup(Stack *s) {
    if (LINEAR) {
        printf("dup forbidden in linear mode\n");
        exit(1);
    }
    Value a = pop(s);
    push(s, a);
    push(s, a);
}
```

Same for `drop`.



### 12. Category-theoretic meaning

This C system models: Free symmetric monoidal category with chosen generators

* Generators = primitive stack words.
* Programs = morphism expressions.
* Execution = morphism evaluation.



### 13. Why C is interesting here

At low level we see:

* Stack = explicit memory
* Tensor = memory layout
* Composition = control flow
* Linear logic = resource discipline
* No hidden copying

This mirrors:

- Linear logic runtime models
- Quantum circuit interpreters
- Compiler IR design
- Dataflow machines



### 14. Powerful extensions

Possible evolutions:



#### (A) Static stack-effect typing (very important)

Attach:

```c
typedef struct {
    int in;
    int out;
    Morphism fn;
} TypedMorphism;
```

Check composition validity.



#### (B) True tensor operator

Split stack into regions.



#### (C) String diagram compiler

Program → graph → optimized schedule.



#### (D) Linear type enforcement

Prevent illegal dup/drop at compile time.



#### (E) Higher-order morphisms

Requires closures / heap-allocated environments.



### 15. Big picture

We’re effectively building: A categorical abstract machine in C

Very close to:

- [SECD](./../../../ch05/addition/am/secd/) machine variants
- Linear logic machines
- Concatenative VM
- Compiler intermediate representations ([IR](./../../../ch05/sec5.7/IR/))
