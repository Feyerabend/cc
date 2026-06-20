# Plan: Translating the JVM Interpreter to ANSI C

## Overview

The Python interpreter is structured as a clean dispatch-table interpreter with
well-separated concerns: parser, class loader, native registry, and per-method
execution engine. Translating it to C follows the same structure. The goal is
idiomatic C89/C90 (ANSI C) with `<stdint.h>` for integer types and
`setjmp`/`longjmp` for exception propagation — no C99 VLAs, no GCC extensions,
no computed goto.

---

## 1. Value Representation

### Tagged Union

Every JVM value on the operand stack or in a local variable slot is typed.
Represent each value as a tagged union:

```c
typedef enum {
    JVM_INT, JVM_LONG, JVM_FLOAT, JVM_DOUBLE, JVM_REF
} JvmTag;

typedef struct {
    JvmTag tag;
    union {
        int32_t  i;
        int64_t  l;
        float    f;
        double   d;
        void    *ref;   /* JavaObject*, JavaArray*, or NULL */
    } v;
} JvmValue;
```

`long` and `double` each occupy two logical stack slots in the JVM spec;
maintain a `category` field (1 or 2) in the type system or simply push a
dummy `JvmValue` placeholder after each 64-bit value to keep slot indices
consistent.

---

## 2. Heap Objects

### JavaObject

```c
typedef struct JavaObject {
    const char      *class_name;   /* interned string */
    struct Field    *fields;       /* name→JvmValue linked list or hash map */
    int              field_count;
} JavaObject;
```

### JavaArray

```c
typedef struct JavaArray {
    const char *component_type;
    int32_t     length;
    JvmValue   *elements;          /* heap-allocated */
} JavaArray;
```

Both are allocated with `malloc`/`free`. A mark-and-sweep GC is out of scope;
use arena allocation or explicit free() at method return, which is sufficient
for short programs. A simple reference-counted allocator is a good middle
ground.

---

## 3. Operand Stack and Local Variables

```c
#define MAX_STACK  256
#define MAX_LOCALS 256

typedef struct Frame {
    JvmValue  stack[MAX_STACK];
    int       sp;                /* stack pointer: index of next free slot */
    JvmValue  locals[MAX_LOCALS];
    int       max_locals;
    const uint8_t *code;
    int       pc;
    int       code_length;
} Frame;
```

Push/pop as inline functions:

```c
static inline void push(Frame *f, JvmValue v) { f->stack[f->sp++] = v; }
static inline JvmValue pop(Frame *f)          { return f->stack[--f->sp]; }
static inline JvmValue peek(Frame *f)         { return f->stack[f->sp-1]; }
```

---

## 4. Constant Pool

The Python parser already models each entry with a tag and fields. In C:

```c
typedef enum {
    CP_UTF8=1, CP_INTEGER=3, CP_FLOAT=4, CP_LONG=5, CP_DOUBLE=6,
    CP_CLASS=7, CP_STRING=8, CP_FIELDREF=9, CP_METHODREF=10,
    CP_INTERFACE_METHODREF=11, CP_NAMEANDTYPE=12,
    CP_INVOKE_DYNAMIC=18
} CpTag;

typedef struct {
    CpTag tag;
    union {
        const char *utf8;
        int32_t     integer;
        float       float_v;
        int64_t     long_v;
        double      double_v;
        uint16_t    index;       /* CLASS, STRING */
        struct { uint16_t class_i, nat_i; } ref;     /* FIELD/METHOD/IFACE */
        struct { uint16_t name_i, desc_i; } nat;     /* NAMEANDTYPE */
    } u;
} CpEntry;
```

Long/Double entries consume two consecutive pool slots (slot N+1 is unused),
just as in the JVM spec.

---

## 5. Dispatch Loop

### Main Interpreter Loop

```c
void interpret(Frame *f, CpEntry *cp, ClassLoader *loader, jmp_buf *exc_env) {
    while (f->pc < f->code_length) {
        uint8_t op = f->code[f->pc++];
        switch (op) {
        case OP_NOP:     break;
        case OP_ICONST_0: push(f, INT_VAL(0)); break;
        /* ... */
        case OP_IRETURN: return;
        /* ... */
        }
    }
}
```

ANSI C `switch` over `uint8_t` compiles to a jump table on any modern compiler;
no computed-goto extension is needed. If the number of cases matters for code
size, group related opcodes into helper functions called from the switch.

---

## 6. Exception Handling

### setjmp / longjmp

```c
typedef struct JavaException {
    JavaObject  *obj;
    const char  *class_name;
} JavaException;

/* Thread-local (or global for single-thread) exception state */
typedef struct ExcState {
    jmp_buf      env;
    JavaException thrown;
    int           active;
} ExcState;
```

`athrow` calls `longjmp`; the interpreter entry point wraps the dispatch loop
in `setjmp`. Each `try`-block boundary in Java bytecode corresponds to an
exception table entry; after `setjmp` fires, walk the exception table to find
the handler PC, then reset the stack and jump.

```c
int saved = setjmp(exc.env);
if (saved != 0) {
    /* exception thrown */
    int handler = find_handler(exc_table, exc_table_len,
                               throw_pc, exc.thrown.class_name);
    if (handler < 0) longjmp(caller_env, 1); /* re-throw */
    f->sp = 0;
    push(f, REF_VAL(exc.thrown.obj));
    f->pc = handler;
}
```

Nested method calls each carry their own `jmp_buf`; `longjmp` propagates up
the C call stack naturally when no handler is found.

---

## 7. Method Invocation

### invokespecial / invokevirtual / invokestatic / invokeinterface

```c
void invoke_method(const char *class_name, const char *method_name,
                   const char *descriptor,
                   Frame *caller, ClassLoader *loader) {
    /* 1. Check native registry */
    NativeMethod *native = lookup_native(class_name, method_name, descriptor);
    if (native) { native->fn(caller, loader); return; }

    /* 2. Look up class file bytecode */
    CodeAttr *code = get_method_code(loader, class_name,
                                     method_name, descriptor);
    if (!code) { /* error */ }

    /* 3. Allocate callee Frame on C stack */
    Frame callee = {0};
    callee.code        = code->bytes;
    callee.code_length = code->length;
    callee.max_locals  = code->max_locals;

    /* 4. Pop args from caller stack into callee locals */
    int nargs = count_args(descriptor);
    /* ... */

    interpret(&callee, cp, loader, &exc_env);
    /* 5. Push return value onto caller stack */
}
```

The callee `Frame` lives on the C stack — no heap allocation per call.

### Overload Resolution by Descriptor

`lookup_native` and `get_method_code` both take `descriptor` and match on
`name + descriptor`, exactly as in the Python implementation. In C, descriptor
comparison is `strcmp`.

---

## 8. Class Loader

```c
typedef struct ClassFile {
    CpEntry  *cp;
    int       cp_count;
    char     *this_class;   /* resolved name */
    char     *super_class;
    Method   *methods;
    int       method_count;
    Field    *fields;
    int       field_count;
} ClassFile;

typedef struct ClassLoader {
    ClassFile **classes;    /* hash map: name → ClassFile* */
    int         class_count;
    char      **class_path; /* directories to search */
    int         path_count;
} ClassLoader;
```

`load_class(loader, name)` searches `class_path` for `name.class`, parses it
with the C port of the binary class-file parser, and caches in the hash map.

Static initializers (`<clinit>`) are run on first load, same as in Python.

Superclass method lookup walks `super_class` pointers until `java.lang.Object`.

---

## 9. Native Registry

### Structure

```c
typedef void (*NativeFn)(Frame *caller, ClassLoader *loader);

typedef struct NativeMethod {
    const char *class_name;
    const char *method_name;
    const char *descriptor;   /* NULL means match any descriptor */
    NativeFn    fn;
} NativeMethod;
```

The registry is a flat array sorted by `(class_name, method_name, descriptor)`,
binary-searched at call time. For constructors, a separate table maps
`class_name → NativeConstructorFn`.

### java.util Separation

As in the Python version, `java_util.c` is a standalone compilation unit that
calls `native_registry_register(...)` at startup. It depends only on the
registry API header — no other core files. Adding or removing it requires
no changes to the core interpreter files.

---

## 10. Class File Parser

The binary parser reads a `.class` file sequentially:

1. Magic (`0xCAFEBABE`), minor/major version  
2. Constant pool (count-1 entries, 1-indexed)  
3. Access flags, this_class, super_class (indices into CP)  
4. Interfaces, fields, methods (each with attributes)  
5. `Code` attribute: max_stack, max_locals, code bytes, exception table,
   nested attributes  

All multi-byte integers are big-endian; use `(buf[0]<<8)|buf[1]` etc.

Long and Double constants span two pool entries; after reading entry N
containing a Long/Double, skip entry N+1.

---

## 11. String Handling

Java `String` objects are represented as `char *` (UTF-8) in the Python version.
The same works in C:

- `ldc` of a String constant: resolve CP entry to UTF-8 `const char *`, push as
  `REF_VAL(strdup(utf8))` (or intern via a string pool to avoid duplicates).
- String concatenation: `malloc` a new buffer, `strcat`. For `invokedynamic`
  string concat (Java 9+), intercept the bootstrap method and handle it natively
  rather than implementing `invokedynamic` in full.

---

## 12. Arrays

Array opcodes:

| Opcode      | C operation                                       |
|-------------|---------------------------------------------------|
| `newarray`  | `malloc(sizeof(JavaArray)) + malloc(n * sizeof(JvmValue))` |
| `anewarray` | Same, with `component_type` from CP               |
| `arraylength` | `((JavaArray*)ref)->length`                     |
| `iaload`    | `((JavaArray*)ref)->elements[index].v.i`          |
| `iastore`   | `((JavaArray*)ref)->elements[index] = val`        |
| `aaload/aastore` | Same with `.v.ref`                           |
| bounds check | Compare index vs length; throw via `longjmp`    |

---

## 13. Type Conversions and Integer Semantics

| Python helper | C equivalent                                      |
|---------------|---------------------------------------------------|
| `_i32(v)`     | `(int32_t)(v)`  — C cast truncates naturally      |
| `_i64(v)`     | `(int64_t)(v)`                                    |
| `int(a/b)` (idiv) | `a / b` — C integer division truncates toward zero |
| `i2b`         | `(int32_t)(int8_t)(v & 0xFF)`                     |
| `i2s`         | `(int32_t)(int16_t)(v & 0xFFFF)`                  |
| `i2c`         | `(int32_t)(uint16_t)(v & 0xFFFF)`                 |

Bitwise shifts: `ishr` uses `(int32_t)v >> n` (arithmetic, implementation-
defined in C89, but universally right on two's-complement targets). `iushr`
uses `(uint32_t)v >> n` (logical).

---

## 14. tableswitch / lookupswitch Alignment

After reading the opcode byte at offset `pc-1`, skip padding until
`pc % 4 == 0`. Read `default`, `low`, `high` (for tableswitch) or
`default`, `npairs` (for lookupswitch) as big-endian signed 32-bit ints.

In C, use a helper:

```c
static int32_t read_s32(const uint8_t *code, int *pc) {
    int32_t v = ((int32_t)code[*pc]   << 24)
              | ((int32_t)code[*pc+1] << 16)
              | ((int32_t)code[*pc+2] <<  8)
              | ((int32_t)code[*pc+3]);
    *pc += 4;
    return v;
}
```

---

## 15. Not Implemented / Explicit Gaps

These are explicitly outside scope for a C port of the current Python version:

- **`invokedynamic`** (lambda, modern string concat): add a fixed native hook
  for `StringConcatFactory`; full `invokedynamic` resolution requires a
  bootstrap method interpreter and is a significant additional project.
- **Garbage collection**: use a simple bump-pointer arena or reference counting;
  a proper GC is out of scope.
- **Bytecode verification**: skip; trust the input `.class` files.
- **Threading**: single-threaded; no `synchronized`, no `java.util.concurrent`.
- **Reflection**: `Class.forName`, `Method.invoke`, etc. — skipped.
- **Classloading hierarchy**: no custom ClassLoader objects; single system
  loader only.
- **Native method interface (JNI)**: native methods backed by C functions loaded
  from shared libraries — not needed since all natives are compiled in.
- **Java module system** (Java 9+ module-info.class): ignored.
- **Floating-point strictness** (`strictfp`, NaN bit patterns): follow the host
  platform's IEEE 754 behavior; good enough for educational use.

---

## 16. File Structure

```
jvm_c/
  include/
    jvm.h           -- all public types (JvmValue, Frame, ClassFile, ...)
    native.h        -- NativeMethod registration API
  src/
    parser.c        -- .class binary parser
    interpreter.c   -- dispatch loop, Frame management
    class_loader.c  -- class loading, superclass lookup
    native_core.c   -- java.lang.{Object,String,Integer,Long,Double,Math,System,...}
    java_util.c     -- java.util.{ArrayList,HashMap,HashSet,TreeMap,...}
    java_objects.c  -- JavaObject / JavaArray heap management
    main.c          -- entry point: parse args, load class, run main()
  Makefile
```

---

## 17. Build

ANSI C, no extensions required:

```makefile
CC     = cc
CFLAGS = -ansi -pedantic -Wall -Wextra -O2
SRC    = src/parser.c src/interpreter.c src/class_loader.c \
         src/native_core.c src/java_util.c src/java_objects.c src/main.c
OBJ    = $(SRC:.c=.o)

jvm: $(OBJ)
	$(CC) $(CFLAGS) -o $@ $(OBJ)

clean:
	rm -f $(OBJ) jvm
```

---

## 18. Migration Order

A suggested order that keeps the project runnable at each step:

1. `jvm.h`: define `JvmValue`, `Frame`, `ClassFile`, `CpEntry`, `JavaObject`,
   `JavaArray`
2. `parser.c`: port the binary class-file parser; write a `main()` that dumps
   CP and method names to verify
3. `interpreter.c`: implement constants, loads/stores, arithmetic, control flow;
   test with hand-crafted code arrays
4. `class_loader.c`: class path lookup, superclass chain, `<clinit>` execution
5. `native_core.c`: `System.out.println`, `String` methods, `Integer`/`Math`;
   enough to run hello-world
6. `interpreter.c` (round 2): invocation opcodes, array opcodes, exception
   handling with `setjmp`
7. `java_util.c`: ArrayList, HashMap, HashSet, Iterator, Arrays, Collections
8. Integration test: run the same `Example.java` used by the Python test suite

---

## 19. Testing in C

Mirror the Python test suite with a simple hand-written test runner:

```c
#define ASSERT_EQ(a, b, msg) \
    do { if ((a) != (b)) { fprintf(stderr, "FAIL: %s\n", msg); failures++; } \
         else { passes++; } } while(0)
```

Each test function crafts a `Frame` with hand-written bytecode, calls
`interpret()`, and asserts the stack top value — exactly as the Python tests do.
No external test framework needed; the Makefile `test` target runs the binary
and checks exit code.
