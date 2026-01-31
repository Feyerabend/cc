## Some History of Intermediate Code

### UNCOL: Universal Computer Oriented Language

The concept of intermediate code, specifically the idea of a universal intermediate language, can trace its origins back to UNCOL (Universal Computer Oriented Language), which was proposed in 1958 by a SHARE ad-hoc committee. UNCOL was a theoretical design aimed at simplifying the compilation process across different machine architectures and high-level programming languages. While it was never fully implemented, its influence on the development of compilers and intermediate representations has had a lasting impact.

### Core Idea of UNCOL

UNCOL was envisioned as a universal intermediate language that would bridge the gap between high-level programming languages and machine code. The idea was based on the principle of two-step compilation:
1. Front-End: Each high-level programming language (e.g. Fortran, COBOL) would have a compiler that translated the source code into UNCOL.
2. Back-End: A separate compiler would then take this UNCOL code and translate it into the machine code specific to the target computer architecture.

This two-phase approach meant that, theoretically, fewer compilers would be needed. Instead of requiring multiple compilers for each language and each machine, there would only need to be one compiler front-end for each language and one back-end for each machine architecture, which significantly reduced development effort.

Why It Was Important (in Theory)

The promise of UNCOL was substantial:
- Reduced Development Effort: By centralizing the translation into an intermediate format, fewer compilers would be needed. This could potentially streamline the development of compilers for both new languages and new machine architectures.
- Increased Portability: Programs written in any high-level language could, in theory, be easily ported to different computer systems by simply using a different back-end compiler, enabling easier cross-platform execution.

Why It Didn't Happen (in Practice)

Despite its ambitious goals, UNCOL faced numerous challenges:
- Complexity: The task of designing a universal intermediate language capable of representing the nuances of many different programming languages proved to be far more difficult than anticipated. Each programming language has unique features, making it tough to standardize their representation in a single language.
- Technological Limitations: The computing power available at the time was not sufficient to handle the complexities of converting high-level code into an intermediate representation, and then translating that into machine code efficiently. Compiler technology was still in its early stages, and many aspects of machine and language design were still evolving.

Impact on Modern Compiler Design

Although UNCOL itself was never fully realized, its legacy is seen in the intermediate representations used in modern compilers. UNCOL laid the groundwork for the development of bytecode systems (such as UCSD Pascal's p-code and Java bytecode) and modern intermediate representations used to compile high-level languages to machine code for various architectures. These modern systems, such as the Architecture Neutral Distribution Format (ANDF), are direct descendants of the ideas proposed by UNCOL.

For instance, Java's bytecode, which is designed to run on the Java Virtual Machine (JVM), follows a similar idea of a universal intermediate representation that can be executed on any system that supports the JVM, similar to the vision of UNCOL.

### Conclusion

In summary, while UNCOL did not achieve its goal of becoming the universal intermediate language, it played a significant conceptual role in the development of compiler theory. The idea of using an intermediate language to bridge the gap between high-level languages and machine code remains a cornerstone of modern compiler design.

#### References:
1.	Conway, M. E. (1958). Proposal for an UNCOL. Communications of the ACM, 1(10), 5-8. doi:10.1145/368924.368928
2.	Sammet, J. E. (1969). Programming Languages: History and Fundamentals, Prentice-Hall. Chapter X.2: UNCOL (Significant Unimplemented Concepts), p. 708.
3.	Macrakis, S. (1993). From UNCOL to ANDF: Progress in Standard Intermediate Languages, Open Software Foundation Research Institute, RI-ANDF-TP2-1.
4.	Steel, T. B., Jr. (1960). UNCOL: Universal Computer Oriented Language Revisited, Datamation, Jan/Feb. p. 18.


---


---

### Java

..


