
## A compiler in the classical style (the brittle foil)

`calc.c` is the "compiler implemented in the classical style" referred to at the
top of [../README.md](../README.md): every token, AST node, and TAC instruction
is `malloc`'d individually and must be freed by hand. It is the *motivation* for
arena allocation, not an endorsement of this style.

It compiles a tiny expression language

```
program   := statement*
statement := IDENT '=' expr ';'  |  'print' expr ';'
expr      := term  (('+' | '-') term)*
term      := factor (('*' | '/') factor)*
factor    := NUMBER | IDENT | '(' expr ')'
```

through the usual phases — **lex → parse (AST) → three-address code** — and
prints the generated TAC.

### Run

```sh
make run     # build and run
make asan    # build with AddressSanitizer/UBSan to confirm it is leak-free
make clean
```

### The point

The code is correct: it leaks nothing. Look at the bottom of `calc.c` —

```c
free_tac(&tac);
free_program(&prog);
free_tokens(&tokens);
```

three separate hand-written cleanup walks, each of which must mirror its
allocation exactly. `free_ast` recurses; `free_tokens` frees every interned
lexeme; temporaries from `new_temp` are owned by their caller. Every `malloc`
has a matching `free`, and getting any of them wrong means a leak or a crash.

Now compare [../arena.c](../arena.c), where the same kind of short-lived,
uniform-lifetime data is released with a single `arena_destroy()`. That contrast
is the entire argument of the chapter's §5.7 discussion of ownership: classical
manual memory management is *possible* but fragile; making lifetimes explicit
(an arena, or — in Lark — affine types) removes the bookkeeping rather than
tidying it.
