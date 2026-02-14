
## History of BASIC

*BASIC* (Beginner's All-purpose Symbolic Instruction Code) was created in 1964 at Dartmouth College
by John G. Kemeny and Thomas E. Kurtz. Their mission was to make computing accessible to students and
non-specialists, particularly in an educational context. At the time, programming required expertise
in languages like Fortran or COBOL and access to batch-processing systems with punch cards. BASIC,
designed for time-sharing systems, allowed interactive programming with immediate feedback, a radical
shift that aligned with its pedagogical goal of teaching problem-solving through coding.

The original Dartmouth BASIC was simple, with commands like `PRINT`, `LET`, `IF...THEN`, and `GOTO`.
Its English-like syntax and minimalistic design made it an ideal teaching tool. Distributed freely,
it was adopted by other institutions, setting the stage for its widespread use.


### Pedagogical Value

BASIC's design was rooted in education, and its pedagogical impact was profound:

- *Lowering Barriers*: BASIC's intuitive syntax allowed students with no prior computing experience
  to write programs quickly. Commands like `INPUT` and `PRINT` mirrored natural language, making
  abstract concepts like variables and loops tangible.

- *Immediate Feedback*: Running a program line-by-line in an interactive environment helped learners
  see cause-and-effect relationships, reinforcing debugging and logical thinking skills.

- *Encouraging Exploration*: BASIC's simplicity enabled students to experiment, fostering creativity.
  For example, writing a program to print patterns or calculate grades gave students a sense of
  ownership over technology.

- *Democratising Computing*: By teaching BASIC in schools and colleges, educators empowered non-STEM
  students to engage with computers, broadening participation in an era when computing was elitist.

- *Foundation for Computational Thinking*: BASIC introduced core programming concepts (variables,
  conditionals, loops) in a forgiving environment, preparing students for more complex languages.

In the 1970s and 1980s, BASIC's role in education expanded as microcomputers entered classrooms and homes.
Books like *BASIC Computer Games* (1978)--yes I have one still--and magazines like *Creative Computing*
provided engaging exercises, turning learning into a playful, self-directed activity. This approach
influenced modern educational tools like Scratch, which prioritise interactive learning.


### Rise on Microcomputers

BASIC's popularity surged in the 1970s and 1980s with the microcomputer revolution. Its low resource
requirements (minimally fitting in just 4KB of RAM) and simplicity made it perfect for early personal
computers. Naturally it could be expanded with more features. Developments include:

- *1975: Altair BASIC*: Developed by Bill Gates and Paul Allen for the Altair 8800, this was
  Microsoft's first product. Distributed on paper tape, it brought programming to hobbyists.[^code]

- *Home Computers*: Manufacturers embedded BASIC interpreters in ROM, making it the default interface
  for machines like the Commodore 64, Apple II, Atari 400/800, and Sinclair ZX Spectrum. Users could
  boot directly into BASIC, encouraging experimentation.
  - *Commodore BASIC* (1977) powered the PET and Commodore 64, widely used in homes and schools.
  - *Applesoft BASIC* (1978), written by Microsoft for the Apple II, added graphics and floating-point math.
  - *Sinclair BASIC* (1980) was optimized for the ZX80 and ZX Spectrum's limited memory.

- *Cultural Impact*: BASIC's accessibility democratised programming. Students, hobbyists, and children
wrote games, utilities, and educational tools, fostering a DIY programming culture. Publications like
*Compute!* shared BASIC listings, amplifying its reach.

BASIC became synonymous with personal computing, particularly in education, where it was a staple in
computer literacy curricula.

[^code]: A released source version can be found at: https://www.gatesnotes.com/microsoft-original-source-code.


### Dialects of BASIC

#### 1. *Dartmouth BASIC* (1964) - *The Original*

The first BASIC implementation was designed for time-sharing systems at Dartmouth College, focusing on education
and accessibility. It introduced the core syntax that would influence all future variants.

```basic
10 REM CALCULATE AVERAGE OF THREE NUMBERS
20 INPUT "ENTER THREE NUMBERS: "; A, B, C
30 LET AVG = (A + B + C) / 3
40 PRINT "THE AVERAGE IS"; AVG
50 END
```

*Historical Significance*: Dartmouth BASIC pioneered the concept of interactive programming for non-specialists,
with its English-like commands and straightforward execution model fundamentally changing who could program computers.


#### 2. *Microsoft BASIC* (1975) - *The Foundation of an Empire*

Initially developed for the Altair 8800, Microsoft BASIC became the foundation of Bill Gates and Paul Allen's software
empire. It was adapted for dozens of microcomputers and established many conventions that persisted across later dialects.

```basic
10 PRINT "RANDOM NUMBERS:"
20 FOR I = 1 TO 5
30 N = INT(RND(1) * 100) + 1
40 PRINT N
50 NEXT I
60 GOTO 10
```

*Historical Significance*: This dialect launched Microsoft as a company and established the precedent of licensing
software separately from hardware. Its widespread adoption created the first standard BASIC that worked across multiple
manufacturers' computers.


#### 3. *Tiny BASIC* (1975-1976) - *The First Open Source Movement*

Developed in response to Altair BASIC's $150 price tag, Tiny BASIC emerged from the Homebrew Computer Club when
Dr. Li-Chen Wang created a minimal BASIC interpreter published with the notation "Copyleft"--an early precursor
to open-source licensing.

```basic
10 REM TINY BASIC PRIME NUMBER FINDER
20 N=3
30 PRINT 2
40 GOSUB 100
50 N=N+2
60 IF N<100 THEN 40
70 END
100 FOR I=3 TO SQR(N) STEP 2
110 IF N/I=INT(N/I) THEN RETURN
120 NEXT I
130 PRINT N
140 RETURN
```

*Historical Significance*: Tiny BASIC represented computing's first significant "copyleft" project, with its
specification published in the People's Computer Company newsletter and implementations shared freely. This
challenge to proprietary software models preceded the Free Software movement by nearly a decade and demonstrated
the potential of community-developed software.


#### 4. *Commodore BASIC* (1977) - *The People's Programming Language*

Embedded in ROM on Commodore's wildly popular PET, VIC-20, and Commodore 64 computers, this dialect introduced
millions of users to programming through direct hardware access commands.

```basic
10 POKE 53280,0: POKE 53281,0: REM BLACK SCREEN AND BORDER VIC II
20 FOR I = 0 TO 24
30 POKE 1024+(I*40), 42: REM PLOT ASTERISK DOWN SCREEN EDGE
40 POKE 55296+(I*40), 1: REM COLOR IT WHITE
50 NEXT I
60 FOR T = 1 TO 1000: NEXT T: REM DELAY LOOP
70 GOTO 10
```

*Historical Significance*: Commodore BASIC exemplified how programming languages could be tailored to specific
hardware. Its `PEEK` and `POKE` commands gave users direct memory access, encouraging a generation to experiment
with graphics and sound by manipulating the computer's memory directly.


#### 4. *BBC BASIC* (1981) - *The Educational Standard*

Developed for the BBC Microcomputer System as part of the UK's Computer Literacy Project, BBC BASIC combined
educational accessibility with advanced features like procedures, multi-line IF statements, and built-in assembly
language.

```basic
10 MODE 2
20 PROCdrawSquare(640, 512, 200)
30 END
40 
50 DEF PROCdrawSquare(x, y, size)
60   LOCAL s2
70   s2 = size/2
80   MOVE x-s2, y-s2
90   DRAW x+s2, y-s2
100  DRAW x+s2, y+s2
110  DRAW x-s2, y+s2
120  DRAW x-s2, y-s2
130 ENDPROC
```

*Historical Significance*: BBC BASIC showed how a teaching language could evolve to include structured programming
concepts without sacrificing accessibility. Its influence on UK education created a generation of programmers who
benefited from its balance of simplicity and sophistication.


#### 5. *ABC80 BASIC* (1978) - *The Scandinavian Speedster*

Developed for the Luxor ABC80 computer, this dialect became dominant in Nordic countries, particularly Sweden,
and was known for its exceptional execution speed and efficient memory usage. Its performance rivaled that of
BBC BASIC despite being developed earlier.

```basic
10 REM ABC80 BASIC - HORISONTAL SCROLLING ASTERISK
20 PRINT CHR$(12); : REM CLEAR SCREEN
30 FOR X% = 0 TO 39
40 ; CUR(X%, 10);"*"; : REM MOVE CURSOR TO COLUMN X%, ROW 10
50 FOR W% = 1% TO 100% : NEXT W% : REM SMALL DELAY
60 ; CUR(X%, 10);" "; : REM MOVE CURSOR BACK TO COLUMN X%, ROW 10
70 NEXT X%
90 GOTO 30
```

*Historical Significance*: ABC80 BASIC demonstrated that interpreted languages could achieve performance comparable
to compiled code through careful optimisation ("semi-compiled" or tokenized). Its popularity in educational settings
throughout Scandinavia created a generation of programmers who benefited from its balance of accessibility and power.
The machine's dominance in Swedish schools and universities established a strong computing culture.


#### 6. *BBC BASIC* (1981) - *The Educational Standard*

Bundled with early versions of MS-DOS, GW-BASIC became the default BASIC implementation on IBM PCs and compatibles,
bringing the language into business environments.

```basic
10 SCREEN 1: CLS
20 COLOR 1
30 LINE (0,0)-(319,199),3,B
40 FOR I = 1 TO 100
50   X = INT(RND * 300) + 10
60   Y = INT(RND * 180) + 10
70   CIRCLE (X,Y), 5, 2
80 NEXT I
90 LOCATE 23, 10: PRINT "PRESS ANY KEY TO CONTINUE"
100 A$ = INPUT$(1)
```

*Historical Significance*: GW-BASIC bridged the gap between home computers and business machines, establishing
BASIC as a universal language across computing environments.


#### 6. *QuickBASIC* (1985) - *The Professional Evolution*

Microsoft's QuickBASIC transformed BASIC from an interpreted language into a modern development environment with
a compiler, subroutines, and structured programming constructs.

```basic
' Modern structured programming approach
DECLARE SUB DrawBox (x1!, y1!, x2!, y2!)
SCREEN 12

DrawBox 100, 100, 300, 200
DrawBox 150, 150, 250, 350

SUB DrawBox (x1, y1, x2, y2)
    LINE (x1, y1)-(x2, y2), 15, B
END SUB
```

*Historical Significance*: QuickBASIC represented BASIC's coming of age, answering critics who dismissed
it as unstructured and inefficient. Its IDE and compiler technologies influenced future development
environments.


#### 7. *Visual Basic* (1991) - *The Business Revolution*

Reimagining BASIC for Windows' graphical environment, Visual Basic pioneered event-driven programming and
visual development techniques that democratized business application creation.

```basic
GraphicsWindow.BackgroundColor = "Black"
GraphicsWindow.PenColor = "White"
GraphicsWindow.Width = 480
GraphicsWindow.Height = 320

For i = 1 To 100
  x = Math.GetRandomNumber(GraphicsWindow.Width)
  y = Math.GetRandomNumber(GraphicsWindow.Height)
  GraphicsWindow.DrawText(x, y, "*")
EndFor
```

*Historical Significance*: Small Basic demonstrated the enduring value of BASIC's pedagogical approach,
adapting its simplicity for modern object-oriented environments while maintaining the focus on immediate
feedback and visual results.


#### 9. *Visual Basic* (1991) - *The Business Revolution*

Microsoft's return to BASIC's educational origins, designed specifically to teach programming concepts
to beginners in the modern era.

```basic
Private Sub Command1_Click()
    If Text1.Text = "" Then
        MsgBox "Please enter your name", vbExclamation, "Input Required"
    Else
        Label1.Caption = "Hello, " & Text1.Text & "!"
        Text1.Text = ""
    End If
End Sub
```

*Historical Significance*: Visual Basic transformed BASIC from a learning tool to an enterprise development
platform. Its visual form designer and event model created a template for rapid application development
that continues in modern frameworks.


### Decline of BASIC

BASIC's dominance faded in the late 1980s and 1990s due to technical, cultural, and pedagogical factors:

- *Performance*: Interpreted BASIC was slow compared to compiled languages like C or Pascal, limiting
  its use for complex applications.

- *Unstructured Code*: Early BASIC's reliance on `GOTO` produced "spaghetti code," criticised for being
  unmaintainable. Structured dialects like QuickBASIC mitigated this, but the stigma persisted.

- *Professionalization*: As software development formalised, languages with strong typing and modularity
  (e.g., C++) during the late 80 became industry standards, marginalising BASIC's beginner-focused design.

- *Hardware Advances*: Powerful PCs and GUI-based operating systems (e.g., Windows) reduced the need for
  lightweight languages. Visual Basic thrived briefly for rapid application development but was later
  eclipsed by .NET and C#.

- *Educational Shift*: BASIC faced criticism in academia for encouraging bad habits. In 1975, Edsger
  Dijkstra famously critiqued BASIC, stating it "cripples the mind" by allowing unstructured programming,
  potentially hindering students' ability to learn disciplined coding practices. This view gained
  traction as educators favored languages like Pascal, which emphasised structure.

[^cripple]: Dijkstra, E. W. (1975). EWD498: *How do we tell truths that might hurt?*
Archived by the University of Texas:
https://www.cs.utexas.edu/users/EWD/ewd04xx/EWD498.PDF

By the 2000s, BASIC was a niche language, though Visual Basic and open-source projects like FreeBASIC
persisted. Its educational role diminished as Python and visual tools like Scratch took over.


### Criticisms of BASIC

BASIC faced significant criticism, particularly from academics and professional programmers:

- *Unstructured Programming*: The heavy use of `GOTO` led to convoluted code, making it hard to teach
  modular design. Critics argued this instilled poor habits in beginners, complicating transitions to
  languages like C or Pascal.

- *Oversimplification*: BASIC's simplicity, while pedagogically valuable, was seen as a double-edged
  sword. It shielded learners from low-level concepts like memory management, leaving them unprepared
  for systems programming.

- *Lack of Standardization*: The proliferation of dialects created inconsistencies, frustrating learners
  who moved between platforms (e.g., Commodore BASIC's `POKE` vs. Applesoft's `HPLOT`).

- *Perceived Amateurism*: BASIC's association with hobbyists and "toy" programs led to a perception that
  it was not serious, alienating it from professional and academic circles.

- *Pedagogical Harm*: Dijkstra and others argued that BASIC's leniency (e.g., no type declarations)
  fostered sloppy thinking, potentially limiting students' ability to grasp rigorous programming principles.

Despite these critiques, defenders noted that BASIC's accessibility sparked interest in computing for
millions, and structured dialects like QuickBASIC addressed some concerns. The debate reflects a tension
between ease of learning and preparation for advanced programming.


### Lessons from BASIC

BASIC's history offers valuable insights, particularly in pedagogy and language design:

1. *Pedagogical Power of Simplicity*: BASIC's success in education stemmed from its low entry barrier,
   showing that beginner-friendly tools can inspire lifelong interest in computing. Modern tools like
   Python and Scratch build on this legacy.

2. *Balancing Simplicity and Structure*: BASIC's unstructured nature was both a strength (easy to learn)
   and a weakness (hard to scale). This highlights the need for languages to evolve with learners, as
   seen in QuickBASIC's structured features.

3. *Ecosystem Drives Adoption*: BASIC's integration into microcomputers made it ubiquitous, underscoring
   the importance of accessibility and distribution in educational tools.

4. *Criticism Informs Progress*: The backlash against BASIC spurred improvements in programming education,
  leading to languages like Pascal and Python that balance simplicity with discipline.

5. *Cultural Legacy*: BASIC's role in fostering a DIY programming culture shows how tools shape communities.
   Its decline reflects the challenge of staying relevant amid technological shifts.

6. *Pedagogical Evolution*: BASIC's immediate feedback and interactivity remain gold standards in teaching.
   However, its criticisms emphasize the need for tools that transition learners to advanced concepts without
   sacrificing engagement.


### Conclusion

BASIC was a cornerstone of the microcomputer era, transforming computing from an elite discipline to a tool
for all. Its pedagogical value--rooted in simplicity, interactivity, and accessibility--made it a gateway for
millions to learn programming, shaping the tech industry and educational practices. However, criticisms of
its unstructured design and perceived limitations highlight the challenges of balancing beginner-friendliness
with rigour. BASIC's rise and fall illustrate the power of accessible tools and the need for evolution in
response to changing needs. Its legacy endures in modern educational languages and the ethos of democratising
technology.

