
## The Metcalfe Machine

The "Metcalfe machine," introduced in Howard H. Metcalfe's 1963 paper
*A Parametrised Compiler Based on Mechanical Linguistics*, is an early
example of a recursive, syntax-directed approach to compiler construction.
This method leverages production rules defined by a formal grammar, allowing
the compiler to parse and generate code in a structured, rule-driven manner.
Metcalfe's work anticipated and influenced the development of later
meta-compilation systems such as META II, which formalised these techniques
for constructing compilers.

Metcalfe's machine operates using a stack-based mechanism to manage recursive
procedure calls, conditional control flow, and input/output pointers. This
structure made it particularly suited to implementing context-free grammars
and laid important groundwork for recursive descent parsing--a technique
still widely used in parser generators like ANTLR and hand-crafted parsers.

This approach belongs to the broader family of "meta-compilers," tools designed
to automate the creation of compilers and interpreters for both domain-specific
and general-purpose languages. Key descendants and related innovations include
Schorre's META II, TREE-META, and later systems that extended these ideas into
efficient frameworks for real-world language implementation.

For additional details, Metcalfe's work is referenced in the *Annual Review in
Automatic Programming* and has been revisited in educational texts like Mick
Farmer's *Compiler Physiology for Beginners*. Broader discussions of
meta-compilers and syntax-directed translation appear in the context of tools
like SYNTAX, Packrat parsers, and more recent grammar-composition frameworks
that emphasise declarative language definitions.[^ref]


### Virtual Machines

As an example of how to parse text, we use an implementation of a "machine"
that picks out characters (or tokens) from an input "tape", matching expected
characters and acting accordingly (like a program). There is also an output "tape"
where results can be stored.

Production rules are an old concept used in theories such as parsing (they also
appear in other contexts, e.g., expert systems). A simple block of production
rules looks like this:

```
  S → A B  
  A → a | ac  
  B → b | cb
```

From this, we can generate a limited set of "products":
```
  S → AB →  aB →   ab  
  S → AB →  aB →  acb  
  S → AB → acB →  acb  
  S → AB → acB → accb
```

You can likely follow the substitutions in each
step, where terminal symbols in lowercase replace the
non-terminal placeholders in uppercase.


### The Machine

Here is a brief overview of the instructions this machine can use:

`call <label>`
: Push the current input and output positions onto a stack.
Then call a subprogram or subroutine at the specified label (recursive calls are allowed).

`false <label>`
: Conditional jump; if flag is false, then jump to the label.

`flag false`
: Set the flag to false.

`flag true`
: Set the flag to true.

`match <item>`
: Compare an item with the current input. If it matches,
advance the input pointer and set flag to true; otherwise set it to false.

`print <item>`
: Write the current item to the output.

`return`
: Return from a subroutine call. Pop the return address
from the stack and set the program counter accordingly.
Also pop the input and output pointer positions from a separate stack.

`stop`
: Stop the machine and print the output.

`true <label>`
: Conditional jump; if flag is true, jump to the label.


I've attempted to implement the machine described above in
'met.py' and 'calfe.py'. The former, 'met.py', translates a program
written in the instruction language above into a binary format.
The latter, 'calfe.py', interprets this binary and applies it to a
given input formula as an array.


### Sample Run

A sample file 'etf.mc' (a simple text format) — an abbreviation for
expression, term, factor — defines a program that converts infix
expressions into prefix notation. For example, an expression like
'(45+89)' would be translated into '+ 45 89'. To allow abstraction,
the character i is used as a placeholder for any number or variable.
This setup enables the machine to function as a basic parser.

First, compile (or assemble) the source file 'etf.mc' into a binary
file 'etf.b'. Then run the binary with a sample input file
etf.test, which might contain an expression such as "(,i,+,i,)".
This expression is parsed into a list
"['(', 'i', '+', 'i', ')']" to facilitate matching where tokens might
be multiple characters, such as 'ab'.

```shell
> python3 met.py -v -i etf.mc -o etf.b  
> python3 calfe.py -v -t etf.test -i etf.b -o etf.out
```

The result should be: '+ i i'.

The test file etf.test contains a line at the end that reads:
'(,i,+,i,)'. You can modify that expression to reflect your own
tests, for example:
'(,(,i,+,i,),*,i,+,(,i,*,i,*,i,),)'.

[^ref]: Howard H. Metcalfe, A Parametrized Compiler based on Mechanical Linguistics,
Annual Review in Automatic Programming: International Tracts in Computer Science
and Technology and Their Application, Vol. 4, ed. Richard Goodman,
The Macmillan Company, New York, 1964. Reprinted Pergamon Press, 2014.
Also see Mick Farmer, Compiler Physiology for Beginners, Chartwell-Bratt,
Bromley, 1985.
Another relevant source is:
Hopcroft, John E., Motwani, Rajeev, and Ullman, Jeffrey D.,
Introduction to Automata Theory, Languages, and Computation, 3rd ed.,
New International ed., Pearson Addison-Wesley, Harlow, 2014.
