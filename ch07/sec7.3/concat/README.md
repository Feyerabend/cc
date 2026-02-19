
## Concatenative Languages

Concatenative programming, the paradigm upon which Forth is built below, constructs programs by composing
functions through sequential placement. This approach establishes an implicit data flow through a stack,
minimising the need for explicitly named variables. Its point-free style, where functions operate without
naming their parameters, and the emphasis on factoring programs into small, reusable functions are
hallmarks of this paradigm. Other concatenative languages, such as Factor, Joy, Cat, and PostScript,
share these characteristics.

Several languages embrace concatenative principles:
- Forth: One of the earliest and most well-known concatenative languages,
  used in embedded systems and low-level programming.
- Factor: A modern concatenative language with a rich type system and higher-order functions.
- Joy: A pure functional concatenative language where programs
  are sequences of functions operating on lists.
- Cat: A strongly typed concatenative language with explicit stack effects.
- PostScript: A concatenative language used in printing and graphics processing.


### Stack-Based Execution and Implicit Data Flow

The core mechanism behind concatenative programming is the stack. Each function (or "word" in Forth
terminology) consumes values from the stack and pushes results back onto it. This eliminates the need
for explicitly named variables, as the data implicitly flows through the function sequence.

```forth
2 3 + 4 * 
```

This places 2 and 3 on the stack, applies + (which consumes both and pushes 5), then places 4 on the
stack, and finally applies * (which consumes 5 and 4, producing 20).


### Point-Free Style and Function Composition

Concatenative programming embodies a "point-free" style, meaning functions do not reference explicit
parameters. Instead, function composition is performed by sequencing operations, where each function
acts as a transformation of the stack. In contrast, applicative languages typically require explicit
function application:

Applicative (Haskell-like):
```haskell
f x = (x + 3) * 4
```
Concatenative (Forth-like):
```forth
: f 3 + 4 * ;
```
Here, f takes whatever is on the stack, adds 3, and multiplies the result by 4, without needing named parameters.


### Factoring and Code Reuse

Concatenative languages encourage breaking programs into small, reusable components. Since functions operate
solely on the stack, they can be freely composed without needing to refactor parameter lists. This makes it
easy to build higher-order abstractions.

For example, in Joy (another concatenative language), defining a square function:
```joy
DEFINE square == dup *.
```
Here, dup duplicates the top value of the stack, and * multiplies the two, computing the square of the input.



### Forth

Forth, a stack-based, concatenative programming language, emerged from Charles H. Moore's quest for
efficiency in astronomical applications during the late 1960s. This unique language is defined by
its minimalist design, remarkable extensibility, and a distinctive approach to program construction.
At its core, Forth operates on a data stack, where operations primarily manipulate values. Programs
are built by concatenating functions in sequence, reflecting its concatenative nature. Employing
postfix notation, operators follow their operands, as seen in "2 3 +," which differs from the more
common infix notation. The language utilises a dictionary-based system, storing definitions, known as
"words," in a searchable dictionary. Forth's interactive nature is facilitated by a REPL (Read-Eval-Print Loop)
environment, enabling immediate feedback and exploration. Furthermore, its ability to produce extremely
compact executables with minimal overhead has been a significant advantage.

The language's history is marked by key milestones. Initial development took place at the National
Radio Astronomy Observatory between 1968 and 1970, followed by the first complete implementation at
Mohasco Industries in 1971. In 1977, Charles Moore founded FORTH, Inc. to commercialise the language.
The 1978 publication of the influential "BYTE Magazine" Forth issue and the 1979 development of fig-Forth
contributed to the language's widespread adoption across numerous platforms. Standardisation efforts
led to FORTH-83 in 1983 and ANSI standardisation (ANS Forth) in 1994.

Forth's influence extends to various areas of computing. PostScript, Adobe's page description language,
adopts Forth's stack-based approach. Open Firmware, a boot environment used in Sun, Apple, and IBM systems,
is based on Forth. Factor, a modern concatenative language, draws inspiration from Forth while incorporating
more advanced features. RPL, the language used in HP calculators, also reflects Forth's influence.
Stack-oriented languages like Retro and ColorForth further illustrate the impact of Forth's design.
Its small footprint has rendered it particularly valuable in embedded systems, where resource constraints
 are paramount.

A typical Forth programming style is exemplified by the following code: `: SQUARED ( n -- n^2 ) DUP * ;`
and `: SUM-OF-SQUARES ( a b -- c ) SQUARED SWAP SQUARED + ;`. This defines two words: `SQUARED`, which
duplicates a value and multiplies it by itself, and `SUM-OF-SQUARES`, which uses `SQUARED` to compute
$a^2 + b^2$. The comments within parentheses illustrate the stack effects, indicating the inputs and outputs.
Forth's philosophy, prioritising simplicity, direct hardware control, and the composition of programs
from small, reusable parts, has solidified its significance, particularly within the realm of embedded
systems, while its influence resonates across diverse computing domains.

The Forth included here, can be a bit picky about whitespace in sample programs. Look at the working
examples. You also direct the input data to the interpreter at the command line, instead of giving
a filename as an argument.

```shell
> ./forth < abc.f
```
