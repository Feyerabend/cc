
## Bootstrapping

A bootstrap, self-hosting programming language is a programming language that is
implemented in itself. The process usually begins with a simple prototype of the
language (often written in another language such as C or assembly). Once this
prototype exists, the language can be used to reimplement its own compiler or
interpreter. At that point, the language is said to be self-hosting, because it
no longer depends on another language for its definition and evolution.

The idea of bootstrapping refers to building progressively more advanced versions
of the language with the help of earlier, simpler ones. For example, an initial
compiler written in C might support only a subset of the language; once that compiler
exists, it can be used to compile a more complete compiler written in the language
itself. Through iteration, the system "lifts itself by its own bootstraps," eventually
becoming a fully featured, self-sustaining environment.

This approach has several advantages:
* It demonstrates the language’s expressive power (since it can describe its own compiler).
* It makes the language independent of external implementation languages in the long run.
* It provides a practical way to evolve and refine the language while staying consistent.

Famous examples include C (early versions of the C compiler were rewritten in C itself),
Lisp, and Rust.
