
> “All things are number” (Πάντα ἀριθμός ἐστι) -- so held the Pythagoreans,
> who believed that the structure of reality itself could be understood through
> the harmonies and relationships of numbers. This idea, preserved in Aristotle’s
> *Metaphysics* (A5, 985b), would echo through the philosophies of Plato and beyond.

## Project

The focus of this project is to understand the inner workings of floating-point numbers,
the challenges they introduce in computation, and alternative representations of real numbers.
Floating-point numbers are integral to numerical computing, enabling the representation
of a vast range of values, from extremely small to extremely large, but they come with
limitations. Understanding these limitations, and the trade-offs with alternatives, is
crucial in fields such as scientific computing, engineering, and data analysis.


### Research questions

1. How do floating-point numbers work?
	- Explain the structure of floating-point numbers, covering components such as the
      sign bit, exponent, and mantissa. Delve into concepts like precision, rounding,
      and representation limits.
	- Describe IEEE 754, the standard format for floating-point arithmetic, including
      single, double, and extended precision.
	- Examine how common operations, like addition and multiplication, work with
      floating-point numbers, and explore common pitfalls in arithmetic, like rounding
      errors and overflow/underflow.

2. Historical context of floating-point arithmetic
	- Explore the history of floating-point numbers, starting from the early methods
      of approximating real numbers to the development of the IEEE standard in the 1980s.
	- Discuss early computer architectures and the challenges that influenced the
      design of floating-point arithmetic.

3. Alternatives to floating-point numbers
	- Fixed-point representation: Describe how it works and compare its strengths
      and weaknesses with floating-point representation, especially in resource-constrained
      systems like embedded devices.
	- Arbitrary-precision arithmetic: Explain how libraries or algorithms provide precision
      beyond standard floating-point limits, and discuss trade-offs in terms of speed and memory.
	- Rational numbers: Describe how representing numbers as fractions avoids precision
      loss in some cases and is sometimes used in algebraic computation systems.
	- Interval arithmetic: Explore how this alternative bounds calculations within a range
      to better manage precision in critical applications, like physics simulations.

4. Comparing floating-point and alternative representations
	- Discuss practical scenarios in which floating-point numbers are preferable
      (e.g. fast calculations where small errors are acceptable) versus when alternatives
      are better suited (e.g., exact calculations required in financial transactions).
	- Explore specific cases or fields where each representation is commonly used,
      including scientific research, finance, video games, and industrial applications.

5. Advanced topics (optional)
	- Explain advanced floating-point concepts, such as subnormal numbers, denormalised
      numbers, and rounding modes (e.g., round-to-nearest, round-toward-zero).
	- Examine specific examples of floating-point-related issues in software
      (e.g. famous failures due to floating-point errors, such as the
      Vancouver Stock Exchange issue).


### Deliverables

- Research paper or report: Students can compile their findings into a structured document,
  including sections on each of the research questions above, with examples, figures, and
  code snippets if applicable.
- Presentation: A presentation summarising key insights from their research, aiming to explain
  floating-point concepts in an engaging way that would be accessible to classmates who may
  not have a technical background.
- Code demonstration (optional): A coding component that could involve creating a simple
  program to demonstrate the limitations of floating-point arithmetic versus an alternative
  representation, such as comparing floating-point precision to arbitrary-precision libraries
  in Python or using interval arithmetic libraries.


### Evaluation criteria

The project can be evaluated based on:

- Clarity and depth of research: Are floating-point concepts explained clearly? Is the historical
  context accurately represented?
- Comparison and analysis: Are the differences between floating-point and alternatives clearly
  delineated? Is there a well-structured analysis of when to use each representation?
- Presentation quality: Is the presentation accessible, engaging, and effective for an audience
  with a diverse technical background?
- Coding and practical demonstrations (optional): Are code examples provided to illustrate concepts?
  Are the demonstrations effective in showing the limitations and strengths of different representations?

This project is designed to help you not only understand floating-point numbers but also appreciate
their importance in computational contexts, alongside alternative methods for representing numbers.
It offers a mix of theory, history, and practical application, which can deepen your understanding
of numerical computation and its implications.


### Suggested start of project

1. How do Floating-Point Numbers Work?

Starting Point: Floating-point numbers are representations of real numbers that allow a wide range of values by separating a number into three parts: the sign, exponent, and mantissa (or significand). The IEEE 754 standard for floating-point arithmetic, established in 1985, provides guidelines for how these numbers should be stored and manipulated in binary form.

- Sign Bit: Indicates whether the number is positive or negative.
- Exponent: Determines the range of values; allows representation of very large or small numbers.
- Mantissa: Contains the actual digits of the number, affecting precision.

Suggested Exploration: Start with examples of 32-bit (single precision) and 64-bit (double precision) floating-point numbers. For instance, explain how the binary breakdown of 3.14159 would look in IEEE 754 format. Explore the difference in precision between single and double precision and why certain calculations may lose accuracy, especially in iterative processes or when handling large and small numbers together.


2. Historical Context of Floating-Point Arithmetic

Starting Point: The concept of floating-point representation has evolved over time as computing needs grew. Early computers used fixed-point numbers due to limited hardware capabilities. However, as more complex calculations were needed (e.g., scientific simulations), floating-point representation became essential.

- Early Challenges: Fixed-point numbers couldn't handle the wide range of values required by scientific computations, which led to the development of floating-point representations.
- IEEE 754 Standard: Before IEEE 754, there were various ways to represent floating-point numbers, leading to compatibility issues. IEEE 754 standardised floating-point representation, making computations more reliable across systems.

Suggested Exploration: Look at notable figures in the field, like William Kahan, who contributed to the IEEE standard. Also, consider researching notable historical events, like the Apollo missions, which relied heavily on precise floating-point calculations.


3. Alternatives to Floating-Point Numbers

Starting Point: Although floating-point numbers are widely used, they aren't perfect.
For instance, they struggle with representing certain numbers exactly (like 0.1 in
binary). Various alternative representations exist to address specific weaknesses of
floating-point arithmetic.

- Fixed-Point Representation: Useful for applications with predictable range and
  precision needs, like embedded systems. Fixed-point numbers avoid some rounding
  issues but have limited dynamic range.[^fixed]

- Arbitrary-Precision Arithmetic: Allows more precise calculations by allocating
  more bits for storage as needed. This is slower than fixed-precision but can be
  invaluable in fields like cryptography or symbolic computation.

- Rational Numbers and Interval Arithmetic: Rational representations avoid
  floating-point precision errors by storing numbers as fractions, while interval
  arithmetic uses ranges to handle uncertain values.

Suggested Exploration: Consider exploring a few simple calculations that show when
floating-point numbers fail and how alternatives can provide more accurate results.
Investigate specific libraries (e.g., Python's decimal and fractions modules) that
handle arbitrary-precision and rational numbers, respectively.

[^fixed]: See e.g. https://www.wedolow.com/en/resources/fixed-point-precision-efficiency/

4. Comparing Floating-Point and Alternative Representations

Starting Point: Each representation has strengths and weaknesses, which are often
tied to the type of application and computational requirements. Floating-point
arithmetic is fast and can handle a wide range of values, but it's prone to rounding
errors and precision loss. Alternatives like arbitrary-precision are slower but
provide exact results.

- Use Cases: Floating-point is suited to applications where approximate values
  are acceptable, such as real-time graphics. On the other hand, rational numbers
  might be better for symbolic mathematics, where precision is critical.

- Error Accumulation and Stability: Floating-point calculations can accumulate errors
  over iterative processes. Some alternatives, like interval arithmetic, can provide
  error bounds, which is valuable in simulations and physics calculations.

Suggested Exploration: Use examples that show where floating-point is less suitable
and where an alternative might yield better results. For instance, analyze a financial
calculation where precision is vital and arbitrary-precision is used, then compare it
with a floating-point version to highlight the differences.


5. Advanced topics (optional)

Starting point: Advanced topics could include looking at how floating-point numbers
handle edge cases, like very small (subnormal) numbers or how different rounding modes
affect calculations. These nuances become important in scientific computing and when
implementing custom floating-point systems.

- Subnormal and denormal numbers: These are used when numbers are too small to be
  represented normally. They allow the representation of numbers close to zero but
  reduce precision.

- Rounding modes: IEEE 754 defines multiple rounding modes (e.g., round-to-nearest,
  round-toward-zero). Each mode has its impact on the stability and accuracy of 
  calculations, particularly in long-running algorithms.

Suggested exploration: Research some specific edge cases, like the difference between
0.1 and 1/10 in floating-point arithmetic, which is non-exact due to binary representation
limitations. Look at a famous case like the Patriot missile error[^error], which was a result of
floating-point precision issues, and how alternative systems could potentially avoid such issues.

[^error]: See https://www-users.cse.umn.edu/~arnold/disasters/patriot.html.


### Code

#### Float

A Python program that simulates floating-point arithmetic by decomposing numbers
into their sign, mantissa, and exponent components, in line with the
*IEEE 754 floating-point standard*.

* Code [float.py](./float.py).
* Description [FLOAT.md](./FLOAT.md).


#### Fixed

We start with something very small that represent a very small range of numbers,
as 2 bits are used for the integer part, and 3 bits for the fractional part.
It is in practice not very useful in general, but it easy to follow the calculations
and transformations of fixed point numbers in principal.

* Code [fixed23.c](./fixed32.c).
* Description [FIXED23.md](./FIXED23.md).

Next, we transfer to fixed point numbers that are useful such as Q16.16.

* Code [fixed.c](./fixed.c).
* Description [FIXED.md](./FIXED.md).


#### Fractions

Some programming languages offer built-in support for fractional numbers,
allowing developers to perform precise arithmetic using exact representations of
rational numbers. Python, for example, includes a Fraction type in its standard
library. This is particularly useful when floating-point arithmetic may introduce
rounding errors.

In contrast, C, as a low-level language, does not include native support for
fractions; any handling of fractions must be explicitly implemented or managed
by the programmer.

* Code [frac.c](./frac.c).
* Code [frac.py](./frac.py).

* Description [FRAC.md](./FRAC.md).

An extension of fractional numbers is the field of symbolic computation, which
allows to perform algebraic operations on expressions symbolically rather than
numerically. In symbolic computation, fractions remain in exact form and can be
manipulated as algebraic entities, and expressions can be expanded, factored,
or simplified without resort to approximation.

* Code [symb.c](./symb.c).
* Code [symb.py](./symb.py).

