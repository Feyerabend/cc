
## Foundations

We begin with an introduction to fundamental programming concepts,
including variables, control structures, and functions. Along the way,
we'll explore these topics in greater depth and cover related foundational
concepts. To enhance your understanding, you'll be encouraged to use
LLMs alongside your learning process. These tools will offer immediate
feedback, code suggestions, and explanations, helping you grasp the
material more effectively.

The chapter on fundamentals in the book offers multiple avenues for exploration, each designed to
deepen your understanding of fundamental concepts.


### Example: Projects on numbers


#### 1. Integer representations in different bases

- Objective: Write a program to convert numbers between binary, octal, decimal, and hexadecimal.
  Implement the conversions ad understand the importance of each base and how they're used in
  computing (e.g., binary for logic, hexadecimal for compactness in memory addresses).

- Extension: Examine Binary-Coded Decimal (BCD), where each decimal digit is represented in
  binary. Explore why it's useful (e.g. decimal displays in calculators) and implement basic
  addition or subtraction with it to understand encoding limitations.

#### 2. Creating a custom base or number representation

- Objective: Design your own base system (e.g. base-7 or base-12) and implement a converter
  that converts to and from this custom system to decimal. This exercise helps you to understand
  the flexibility of base systems and the algorithmic logic for base conversion.

- Extension: Non-positional systems. Implement simple arithmetic with Roman numerals, a
  non-positional system. This project can illustrate the practical limitations
  of such systems in complex computation, showing why positional systems are favoured in
  computing.

#### 3. Representing negative numbers in binary

- Objective: Implement positive and negative integers using two's complement and one's
  complement representations. Manually convert between decimal and two's complement binary
  and write a program that can perform addition and subtraction with it.

- Challenge: Explore edge cases, such as integer overflow and underflow, to understand
  the significance of bit-width limitations in two's complement arithmetic.

#### 4. Investigating alternative numerical representations

- Objective: Experiment with unique representations like Gray code, where consecutive
  numbers differ by only one bit, and explore its applications (e.g., in error reduction
  for digital sensors).

- Challenge: Examine binary as a base for storing information in ways other than numbers,
  like characters (ASCII) or images (binary pixel representation). This will give you a
  broader understanding of how versatile binary is in computing beyond just encoding numbers.

#### 5. Understanding checksum and parity in data transmission

- Objective: You can implement a simple parity check (single or double) to illustrate
  how error detection works in data transmission. Extend this by implementing a simple
  checksum algorithm to see how checksums verify data integrity in transmitted data.

- Challenge: Implement Hamming code for error correction, investigate how numerical
  representations directly impact data reliability in transmission.

#### 6. Compare efficiency of different representations

- Objective: Compare efficiency and accuracy in different numerical systems by
  conducting a study. For instance, measure memory usage or computational speed for
  calculations in different formats (e.g., binary vs. BCD vs. floating-point) and
  analyse which is most efficient for specific types of calculations.

- Challenge: Research a use case (e.g., financial software, scientific computation,
  or graphics) and determine which number system or representation is best suited
  for it and why.


#### 7. Simulating big numbers and arbitrary-precision arithmetic

- Objective: Implement basic operations (addition, subtraction, multiplication)
  for very large integers by storing digits in arrays. This introduces the concept
  of arbitrary precision, a foundation of BigInteger and BigDecimal classes that
  can be found in e.g. Java.

- Extension: Implement arbitrary-precision decimals to explore exact decimal
  arithmetic, avoiding floating-point imprecision and understanding where
  arbitrary-precision libraries are valuable in real applications.

#### 8. Exploring floating-point arithmetic and precision limits

- Objective: Take floating-point representation (IEEE 754) and experiment with
  representing simple decimal values like 0.1, 0.2, etc., in floating-point format.
  Examine why operations like 0.1 + 0.2 might not equal 0.3 precisely.

- Extension: Create a simplified floating-point calculator that handles a limited
  range and precision. This illustrates how floating-point numbers approximate
  real numbers and the effect of rounding errors.


Here, as an *example* for exploring deeper, we focus on the representation of
numbers in computers, stemming from the mathematical constructs of
`real numbers.' We explore in code floating-point and fixed-point
representations, fractions, and symbolic calculations, as well as the strengths
and limitations of each approach. Code examples are provided to help you get
started with practical applications.
