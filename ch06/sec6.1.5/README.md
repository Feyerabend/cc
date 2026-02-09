
## On Programming as Craft: A Critical Reflection

What emerges from the reading list in the book is an implicit philosophy:
programming as a *practice*.


### The Craftsmanship Proposition

McBreen's *Software Craftsmanship* serves as the ideological anchor, arguing
for professional pride and deliberate skill cultivation. *The Pragmatic Programmer*
grounds mastery in adaptability. The craftsman must be a pragmatist, choosing
tools and techniques contextually rather than dogmatically. Ousterhout's
philosophy of design insists that simplicity itself is a hard-won craft achievement.
And Hermans reveals that the "craft" isn't just in the artifact (the code) but in the
*craftsperson*--how our cognitive architecture shapes what we can build and maintain.

What makes programming a craft? Say, rather than mere engineering? The traditional
craftsperson works with material resistance. The person works with wood grain,
clay texture, metal temper. The programmer works with *conceptual* resistance:
the brittleness of abstractions, the weight of dependencies, the friction between
human intention and computational logic. Brooks showed us that this resistance
doesn't scale linearly; throwing more people at a problem compounds communication
complexity. This wan't a solution. The craft lies in navigating these inherent
difficulties with judgment, taste, and hard-earned intuition.

Davidson-Pilon builds on Bayesian methods requiring embracing uncertainty and
modeling it explicitly. A mindset shift away from deterministic thinking. This
points to a deeper aspect of craft. Understanding is not just *how* systems work,
but *what they know and don't know*, probabilistically reasoning about incomplete
worlds. The craftsperson thus works with uncertainty as raw material.


### The Tension Between Craft and Scale

Yet there's an unresolved tension in this collection. Brooks wrote about industrial-scale
software development--teams, coordination, deadlines. Craftsmanship evokes the solitary
artisan, the apprentice-master relationship, the bespoke object. Can these coexist?
Perhaps the answer lies in Hermans: understanding cognition helps us design better
team structures, better documentation, better handoffs. The craft becomes *enabling others
to practice the craft*.

Or perhaps we're witnessing the inevitable friction between artisanal ideals and
capitalist velocity. The "software craftsman" is a rhetorical move--an attempt
to reclaim dignity and quality in an industry that often treats code as disposable
inventory.


### Craft or Obsolescence?

And now, the specter at the feast: large language models.

If craftsmanship is about judgment, taste, and deep understanding of material properties,
what happens when an LLM can generate plausible code on demand? Possible outcomes:

*1. Elevation of craft.* LLMs handle the rote, the boilerplate, the well-trodden patterns.
This frees human attention for the genuinely difficult: architectural decisions, subtle
trade-offs, domain modeling, understanding *why* something should exist. The craft __moves
up the abstraction ladder__. Ousterhout's simplicity and Brooks's conceptual integrity become
*more* important, not less, because the volume of generated code makes bad design choices
catastrophic at scale.

*2. Deskilling and dependency.* If a generation of programmers learns to prompt rather than
comprehend, Hermans's cognitive strategies atrophy. We lose the ability to read, debug, and
reason about systems we didn't write. The craft becomes archaeological--deciphering
LLM-generated code as scholars decode ancient texts. Mastery becomes rare, perhaps irrelevant.
The "mythical man-month" becomes the "mythical prompt"--and we learn that throwing more
LLM queries at a problem doesn't solve conceptual incoherence either.
([More](./../addition/deskilling/).)

*3. New crafts emerge.* Perhaps programming-as-typing was never the core craft anyway. The
real skills--problem decomposition, abstraction design, navigating ambiguity, understanding
users and domains--remain human. LLMs become power tools: dangerous in untrained hands,
multipliers in skilled ones. Davidson-Pilon's Bayesian thinking becomes crucial: we must
reason probabilistically about LLM outputs, understanding confidence, verifying claims,
modeling uncertainty.

*4. Hybridization.* The distinction between human and LLM authorship blurs. Craftsmanship
becomes collaborative choreography: knowing when to scaffold a problem for an LLM, when to
intervene, when to reject generated solutions. The Pragmatic Programmer's adaptability
takes on new meaning--adapting not just techniques, but *collaborators*, human and synthetic.


### Conclusion

What these books argue in total, is that programming *can* be a craft--but it
requires choosing to treat it as one. It's a stance, not a given. McBreen's "new imperative"
was prescient: in an age of automation, what remains uniquely human is caring about
quality beyond mere functionality, cultivating judgment that can't be easily replicated.

LLMs don't invalidate this. They might sharpen the question: what are we *for*? If not
typing syntax, then what? Perhaps: understanding problems deeply, designing systems
that endure, making wise trade-offs under uncertainty, mentoring others, knowing
when *not* to build. The craft may survive, transform--or it plainly doesn't. We become
tenders of machines we no longer understand. The choice, for now, remains ours.
What's your opinion here?


### References

- Brooks, F. P., Jr. (1995). *The mythical man-month: Essays on software engineering* (Anniversary ed.). Addison-Wesley.
  - A classic in software engineering, this book explores the challenges of managing
  large software projects and introduces the famous concept of the "mythical man-month."
  Brooks discusses the pitfalls of trying to add manpower to a late project and
  offers timeless insights on project management in software development.

- Davidson-Pilon, C. (2015). *Bayesian methods for hackers: Probabilistic programming and Bayesian inference*. Addison-Wesley Professional.
  - An accessible, practice-oriented introduction to Bayesian reasoning for programmers,
  this book bridges statistical theory and computational implementation. Davidson-Pilon
  emphasises probabilistic modeling, uncertainty, and inference using modern tools,
  showing how Bayesian thinking can be applied to real-world problems where data is'
  incomplete, noisy, or ambiguous.

- Hermans, F. (2021). *The programmer's brain: What every programmer needs to know about cognition*. Manning Publications.
  - Cognitive science applied to software development, with practical strategies for
  improving code comprehension, learning new languages, and debugging.

- McBreen, P. (2002). *Software craftsmanship: The new imperative*. Addison-Wesley. 
  - This book advocates for a shift in mindset from being merely a software
  developer to becoming a software craftsman. McBreen emphasises professionalism,
  skill development, and taking pride in one's work, focusing on the importance
  of quality in software creation.

- Ousterhout, J. (2021). *A philosophy of software design* (2nd ed.). Yaknyam Press.
  - John Ousterhout presents a philosophy centered around simplifying software
  design and avoiding unnecessary complexity. The book focuses on the importance
  of clarity and simplicity, offering principles that guide developers in creating
  clean, easy-to-understand systems.

- Thomas, D., & Hunt, A. (2019). *The pragmatic programmer: Your journey to mastery* (20th anniversary ed.). Addison-Wesley Professional.  
  - A must-read for any developer, this book provides practical advice on writing
  clean, maintainable, and efficient code. The authors emphasise the importance of
  flexibility and adaptability in software development, offering numerous tips
  and techniques for solving everyday programming challenges.



![Brain](./../assets/image/brain.png)
![Bayesian](./../assets/image/bayesian.png)
![Design](./../assets/image/design.png)
![Mythical](./../assets/image/mythical.png)
![Pragmatic](./../assets/image/pragmatic.png)
![Software](./../assets/image/software.png)


