
## Some History of Intermediate Code


### UNCOL: Universal Computer Oriented Language

The concept of intermediate code, specifically the idea of a universal intermediate language,
can trace its origins back to UNCOL (Universal Computer Oriented Language), which was proposed
in 1958 by a SHARE ad-hoc committee. UNCOL was a theoretical design aimed at simplifying the
compilation process across different machine architectures and high-level programming languages.
While it was never fully implemented, its influence on the development of compilers and intermediate
representations has had a lasting impact.


#### Core Idea of UNCOL

UNCOL was envisioned as a universal intermediate language that would bridge the gap between
high-level programming languages and machine code. The idea was based on the principle of two-step compilation:

1. Front-End: Each high-level programming language (e.g. Fortran, COBOL)
   would have a compiler that translated the source code into UNCOL.

2. Back-End: A separate compiler would then take this UNCOL code and translate
   it into the machine code specific to the target computer architecture.

This two-phase approach meant that, theoretically, fewer compilers would be needed. Instead of requiring
multiple compilers for each language and each machine, there would only need to be one compiler front-end
for each language and one back-end for each machine architecture, which significantly reduced development effort.

##### Why It Was Important (in Theory)

The promise of UNCOL was substantial:

- Reduced Development Effort: By centralizing the translation into an intermediate format,
  fewer compilers would be needed. This could potentially streamline the development of
  compilers for both new languages and new machine architectures.

- Increased Portability: Programs written in any high-level language could, in theory,
  be easily ported to different computer systems by simply using a different back-end compiler,
  enabling easier cross-platform execution.


##### Why It Didn't Happen (in Practice)

Despite its ambitious goals, UNCOL faced numerous challenges:

- Complexity: The task of designing a universal intermediate language capable of representing
  the nuances of many different programming languages proved to be far more difficult than anticipated.
  Each programming language has unique features, making it tough to standardise their representation in a single language.

- Technological Limitations: The computing power available at the time was not sufficient to handle
  the complexities of converting high-level code into an intermediate representation, and then
  translating that into machine code efficiently. Compiler technology was still in its early stages,
  and many aspects of machine and language design were still evolving.


##### Impact on Modern Compiler Design

Although UNCOL itself was never fully realised, its legacy is seen in the intermediate representations
used in modern compilers. UNCOL laid the groundwork for the development of bytecode systems
(such as UCSD Pascal's p-code and Java bytecode) and modern intermediate representations used to compile
high-level languages to machine code for various architectures. These modern systems, such as the
Architecture Neutral Distribution Format (ANDF), are direct descendants of the ideas proposed by UNCOL.

For instance, Java's bytecode, which is designed to run on the Java Virtual Machine (JVM),
follows a similar idea of a universal intermediate representation that can be executed on
any system that supports the JVM, similar to the vision of UNCOL.


#### Conclusion

In summary, while UNCOL did not achieve its goal of becoming the universal intermediate language,
it played a significant conceptual role in the development of compiler theory. The idea of using
an intermediate language to bridge the gap between high-level languages and machine code remains
a cornerstone of modern compiler design.

##### References
1. Conway, M. E. (1958). Proposal for an UNCOL. Communications of the ACM,
   1(10), 5-8. doi:10.1145/368924.368928
2. Sammet, J. E. (1969). Programming Languages: History and Fundamentals,
   Prentice-Hall. Chapter X.2: UNCOL (Significant Unimplemented Concepts), p. 708.
3. Macrakis, S. (1993). From UNCOL to ANDF: Progress in Standard Intermediate Languages,
   Open Software Foundation Research Institute, RI-ANDF-TP2-1.
4. Steel, T. B., Jr. (1960). UNCOL: Universal Computer Oriented Language Revisited,
   Datamation, Jan/Feb. p. 18.


### Java: Bridging Internal IR and External VM Interface

Java represents a fascinating convergence of the intermediate representation concepts pioneered
by UNCOL and the virtual machine approach exemplified by Pascal P-code. When Java was developed by
Sun Microsystems in the mid-1990s, it built upon decades of compiler theory while introducing a
practical solution that would become ubiquitous in modern software development.


#### Java Bytecode as Intermediate Representation

From a compiler perspective, Java bytecode functions as an intermediate representation.
The Java compiler (javac) performs a multi-stage compilation process:

1. *Front-End Processing*: The compiler parses Java source code, performs semantic analysis, and builds an abstract syntax tree (AST).

2. *IR Generation*: The compiler transforms the AST into Java bytecode--a platform-independent intermediate form.

3. *Optimisation*: Various optimisations can be performed on the bytecode itself before execution.

In this sense, Java bytecode serves the same role as traditional compiler IRs:
it's an intermediate step between high-level source code and executable code.
However, unlike traditional IRs which are typically internal to the compiler
and never exposed to users, Java bytecode is explicitly designed to be portable and persistent.


#### Java Bytecode as External VM Interface

What distinguishes Java from traditional compiler IRs is that the bytecode also
serves as an *external interface* to the Java Virtual Machine. This dual nature is crucial:

- *Persistence*: Unlike traditional IRs that exist only during compilation,
  Java bytecode is saved to .class files and distributed as the executable form of the program.

- *Standardization*: The bytecode instruction set is formally specified and
  remains stable across JVM implementations, making it a true interface specification.

- *Multiple Front-Ends*: Just as UNCOL envisioned, the JVM can execute bytecode generated
  from multiple source languages--not just Java, but also Kotlin, Scala, Groovy, and others.
  Each language has its own compiler front-end that targets the same bytecode interface.

- *Multiple Back-Ends*: Different JVM implementations (HotSpot, OpenJ9, GraalVM)
  can execute the same bytecode on different hardware platforms and with different optimisation strategies.


#### The Internal-External Continuum

*Internal IR View*: Within the JVM itself, bytecode undergoes further transformation.
Modern JVMs use Just-In-Time (JIT) compilation, where bytecode is treated as an input IR
that gets compiled into native machine code at runtime. The JIT compiler may use additional
internal IRs (such as HotSpot's C1 and C2 compiler IRs) during this process.
From this perspective, bytecode is simply the first stage of a multi-level IR chain.

*External VM Interface View*: From the perspective of language designers and application
developers, bytecode is the stable, documented interface to the execution environment.
It's the contract between the compiler and the runtime, much like an API is the contract
between different software components.


#### Achieving UNCOL's Vision

In many ways, Java achieved what UNCOL set out to do,
though not quite in the way originally envisioned:

- *Language Independence*: The JVM successfully supports multiple programming languages
  through a common bytecode interface.
- *Platform Independence*: The "write once, run anywhere" principle realises UNCOL's portability goals.
- *Practical Implementation*: Unlike UNCOL, Java found the right balance of abstraction--high-level
  enough to be portable, but low-level enough to be efficiently implementable.

The key difference is that Java embraced the virtual machine model rather than attempting
to create a direct path to native code compilation. This added layer of abstraction--the
runtime VM--turned out to be crucial for achieving practical portability.


#### Lessons for Compiler Design

Java's success with bytecode demonstrates several important principles:

1. *IR as Interface*: An intermediate representation can serve double duty as both
   an internal compiler structure and an external interface specification.
2. *Delayed Commitment*: By deferring final code generation to runtime, the system
   can make platform-specific optimizations with full knowledge of the execution environment.
3. *Layered IRs*: Modern systems often use multiple levels of IR--from high-level bytecode
   to low-level machine IRs--each serving different purposes in the compilation pipeline.

This layered approach, where the boundary between "internal IR" and "external VM interface"
becomes deliberately blurred, represents a sophisticated evolution of the ideas first proposed
in UNCOL and pioneered in practical form by Pascal P-code.

