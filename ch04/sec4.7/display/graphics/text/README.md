
### Text

While text was first presented as a simple stream of characters, the technical
side of displaying it soon revealed deeper challenges. Early terminals and teletypes
treated text as nothing more than sequences of fixed-width symbols: each character
occupied the same amount of space, and there was little concern for elegance or
typography. But as soon as text moved onto screens capable of graphics, the issue
of how to represent letters, words, and pages became more complex.

At the heart of the matter lies the way text was represented on early computer screens.
Two traditions coexisted. Vector displays, oscilloscope-like x/y screens, drew letters
by steering the electron beam along line segments, allowing arbitrary scaling and
rotation but at the cost of complexity and brightness. Raster displays, which soon
became dominant, treated the screen as a grid of pixels. Each character was stored
as a small bitmap, a pattern of black-and-white dots. While effective at low resolutions,
this method quickly showed its limits: letters appeared blocky at small sizes, and
scaling them up produced jagged edges. Making digital text both legible and
aesthetically pleasing became a central challenge in the development of modern computing.

One solution came in the form of vector fonts, which describe letters not as fixed
grids of pixels, but as mathematical shapes--lines, curves, and outlines. With this
approach, a single definition of a letter could be rendered at any size or resolution,
always smooth and consistent. The invention of scalable font technologies such as
PostScript and later TrueType allowed computers to display and print text with high
quality, bridging the gap between digital convenience and the long tradition of
typography.

Typesetting itself posed further challenges. Text is not merely a collection of isolated
letters; it is arranged into words, lines, paragraphs, and pages, each governed by rules
of spacing and alignment. Computers had to learn to handle kerning (the subtle adjustment
of space between letter pairs), line breaking, justification, and hyphenation. Early word
processors often struggled with these issues, producing awkwardly spaced documents.
Sophisticated systems such as Donald Knuth’s TeX provided more advanced algorithms for
typesetting, ensuring that mathematical formulas, footnotes, and complex layouts could
be rendered with professional quality.

Another challenge came with internationalisation. The original ASCII character set was
limited to 128 symbols, enough for English letters, numbers, and some punctuation, but
far too restrictive for other languages. Extensions such as ISO-8859 added support for
accented characters, while entirely different systems were devised for scripts like
Chinese or Arabic. The eventual adoption of Unicode, which assigns a unique code point
to virtually every symbol in every writing system, created a universal foundation for
digital text. With it came the technical ability to mix scripts and symbols
seamlessly--Latin, Cyrillic, Greek, Arabic, Chinese, mathematical symbols, even
emojis--within the same document.

On-screen rendering also evolved. Techniques such as anti-aliasing blurred the hard edges
of pixels to create smoother-looking letters. Later, sub-pixel rendering took advantage
of the structure of colour displays to increase the apparent resolution of text even further.
Combined with the increasing density of pixels on modern displays, these advances mean that
text on today’s screens can rival or surpass the sharpness of printed paper.

Thus, the journey of text on computers has moved from the mechanical clatter of teletypes,
through the blocky pixels of early monitors, to the fluid and sophisticated typography of
modern systems. It is a story of continuous refinement, where the needs of human readers
and writers pushed engineers and designers to solve problems of representation, encoding,
and rendering. Text may appear simple at first glance, but behind every line on a screen
lies a complex interplay of mathematics, engineering, and design.

