
*In the folder [avh](./avh/) you can find a simple, early HTML browser in a version high-level Java language.*


## Early Development of Java

Java's origins trace back to June 1991, when a small team at Sun Microsystems, led by James Gosling, initiated
a project codenamed "Green." The goal was to create a programming language for consumer electronics, such as
smart TVs, set-top boxes, and handheld devices, which required a simple, robust, portable, and secure language
due to their limited resources and networked environments. Initially called "Greentalk" (with a .gt file extension),
the language was soon renamed "Oak," inspired by an oak tree outside Gosling's office. Oak drew influences
from C, C++, Smalltalk, Lisp, and Ada, but was designed to be more lightweight and secure.

By 1993, the consumer electronics market hadn't materialised as expected, and the Green team pivoted. The emerging
World Wide Web offered a new opportunity: a platform for dynamic, interactive content. The team realised Oak could
enable applets--small programs embedded in web pages—that could run on any browser with a Java Virtual Machine (JVM).
This platform independence ("write once, run anywhere") became a cornerstone of Java's appeal. In 1994, the team
developed a prototype browser called *WebRunner*[^hotjava], a clone of the Mosaic browser, written in Oak.
The name "WebRunner" was a nod to the movie *Blade Runner*.

[^hotjava]: https://en.wikipedia.org/wiki/HotJava

In 1995, Sun Microsystems decided to make Oak public and rebranded it as *Java*, a name chosen for its simplicity
and evocation of coffee (reflecting the team's caffeine--fueled work sessions). Java was officially announced at
the SunWorld conference in May 1995, alongside the renamed *HotJava* browser. Netscape's agreement to support
Java applets in its Navigator browser gave Java a massive boost, making it a key technology for the early web.
The first Java Development Kit (JDK 1.0), released in 1996, included core features like classes, objects, inheritance,
exceptions, threads, and basic libraries for networking and graphics.


### HotJava and Its HTML Parser

*HotJava* was a modular, extensible web browser developed by Sun Microsystems to showcase Java's capabilities,
particularly its support for applets. Announced in May 1995, HotJava was the first browser to execute Java applets,
demonstrating dynamic content like animations and interactive applications directly in web pages. Unlike contemporary
browsers like Mosaic or early Netscape Navigator, which relied on static HTML and hard-coded protocols, HotJava
was designed to be dynamic, downloading new code (applets) or protocol handlers as needed. This made it a
proof-of-concept for Java's potential to revolutionise web interactivity.[^hjref]

[^hjref]: https://javaalmanac.io/jdk/pre1.0/hotjava-alpha3/doc/overview/hotjava/index.html,
https://www.oracle.com/technetwork/java/hotjava-142072.html

*I gained access to an early beta version of Java “for educational purposes,” which included not only the
parser but also the full source code. After exploring the language for some time, I wrote an introductory
book on Java that was published in two editions, with a total circulation of 16,000 copies--a remarkably
high number for a programming book in Swedish, especially considering the typical print runs in this field.
At the time, the future of Java looked very promising:*

> Lonnert, S. (1997). *Programmering i JAVA* (1st ed.). KnowWare Publ. https://libris.kb.se/bib/2324303

- *Purpose and Functionality*: The parser was responsible for reading HTML files, interpreting tags, and
  constructing a document structure to render pages and execute embedded applets. It was designed to handle
  the relatively simple HTML standards of the mid-1990s (pre-HTML5), which included basic tags for text
  formatting, links, images, and forms. The parser needed to be robust enough to deal with "dirty" or poorly
  formatted HTML, a common issue at the time.[^hjparser]
  
[^hjparser]: https://docs.oracle.com/javase/8/docs/api/javax/swing/text/html/parser/Parser.html

- *Integration with Java Libraries*: The HotJava parser's code was significant enough to be reused in the
  standard Java libraries, specifically in the `javax.swing.text.html` package. The `HTMLEditorKit` class,
  introduced in later JDK versions (e.g., Java 1.4.2), references the "Hot Java parser" as its default parser,
  indicating its influence on Java's HTML processing capabilities. This suggests the parser was lightweight
  and SGML-inspired, with some leniency to accommodate real-world HTML variations.

- *Limitations*: HotJava's parser, and the browser itself, faced challenges due to the performance constraints
  of early Java Virtual Machines. Parsing and rendering were sluggish compared to native browsers, and HotJava's
  functionality was limited—supporting fewer features than competitors like Netscape Navigator. The parser
  likely prioritized compatibility with simple HTML and applet integration over advanced features like DHTML
  or JavaScript, which later parsers (e.g., jsoup) addressed.

- *Legacy*: The HotJava parser laid groundwork for Java's HTML processing tools. Its code reuse in the JDK's
  `HTMLEditorKit` shows it was a foundational piece of Java's text-processing ecosystem. However, as HTML
  evolved and browsers became more complex, third-party libraries like jsoup and HTMLCleaner surpassed the
  standard Java parser, which only supported ancient HTML versions (e.g., HTML 1.0).


### Context and Critical Perspective

HotJava and its parser were developed in a period of rapid web growth, where standards were loose, and browsers
competed to define the internet's future. Sun's vision for Java and HotJava was ambitious: a platform-independent
ecosystem where code could move freely across networks. However, HotJava's sluggish performance and limited
adoption (it was discontinued by the early 2000s) highlight the gap between vision and practicality. The parser's
reuse in Java's standard libraries suggests it was well-engineered for its time, but its inability to keep pace
with evolving web standards limited its long-term impact.

The narrative around Java's early success is often tied to marketing and Netscape's adoption, but critical
examination reveals challenges. Java applets, while innovative, were resource-intensive and posed security
risks, leading to their decline. HotJava's parser, while functional, was overshadowed by more robust solutions
as HTML grew more complex. Still, the project's influence on Java's ecosystem and the broader web cannot be
understated--it proved that a single language could unify diverse platforms, even if the implementation had flaws.


### Sources

- Information on Java's early development and HotJava's origins.
	* https://en.wikipedia.org/wiki/HotJava
	* https://romanglushach.medium.com/the-evolution-of-java-a-historical-perspective-e15c3d7e5f85

- Details about the HotJava parser.
	* https://everything.explained.today/HotJava/
	* https://handwiki.org/wiki/Software:HotJava


