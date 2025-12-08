
## Premature Optimisation & the Controversy Around GO TO

* Dijkstra, E. W. (1968). "Go To Statement Considered Harmful." *Communications of the ACM*, 11(3), pp.147-148.

* Knuth, D. E. (1974). "Structured Programming with go to Statements." *ACM Computing Surveys*, 6(4), pp.261-301.


*Project: Think about optimisation, some historical perspectives, future, and what you can add? Discuss!*


### Premature Optimisation

Donald Knuth famously remarked in his 1974 paper "Structured Programming with go to Statements":

> "Programmers waste enormous amounts of time thinking about, or worrying about, the speed of noncritical parts of their programs, and these attempts at efficiency actually have a strong negative impact when debugging and maintenance are considered. We should forget about small efficiencies, say about 97% of the time: premature optimization is the root of all evil. Yet we should not pass up our opportunities in that critical 3%."

Knuth's statement is widely cited as a foundational idea in software development. His advice cautioned
against early focus on optimisation, emphasizing the importance of first ensuring correctness, clarity,
and maintainability. Optimisation, he argued, should be reserved for critical sections of code identified
as bottlenecks through profiling or performance analysis.

This principle does not dismiss the importance of efficiency; rather, it warns that an obsession with
premature optimisation can lead to convoluted code that is harder to maintain or debug. Knuth advocated
that developers should prioritize good program design, which inherently minimizes inefficiencies, and
focus on optimisation only after a program is both functional and robust.


### GOTO and Structured Programming

The debate over the goto statement reached a pivotal moment with Edsger Dijkstra’s 1968 letter to the
editor (N. Wirth) in *Communications of the ACM*, titled by the editor as "Go To Statement Considered Harmful."
Dijkstra argued that unrestricted use of goto led to "spaghetti code," making programs harder to understand,
test, and maintain. Instead, he championed structured programming constructs, such as loops and conditionals,
to achieve clarity and logical flow.

While Dijkstra's arguments were influential, the title "considered harmful" has often been misunderstood
as advocating for the total prohibition of goto. In reality, Dijkstra's critique was more nuanced, urging
developers to minimise goto usage rather than eliminate it entirely. He emphasized structured programming
principles to improve reliability and maintainability in codebases.


### Knuth's Balanced View

Knuth's 1974 paper revisited the goto debate, offering a more pragmatic perspective. He acknowledged that
structured programming principles were generally beneficial but argued that rigid adherence could be
counterproductive in certain cases. Specifically, he pointed out that goto could occasionally offer a mor
 efficient or elegant solution, particularly in performance-critical code.

Knuth highlighted how goto had historically been essential in assembler programming, making the transition
to higher-level structured languages challenging for some programmers. He suggested that eliminating goto
should not be a goal in itself; instead, the aim should be to write clear, maintainable programs where
structured constructs naturally minimize the need for goto.


### Cultural Legacy

The debates surrounding goto and optimisation have shaped modern programming practices. Dijkstra's advocacy
for structured programming laid the foundation for cleaner, more reliable code, while Knuth's insights
provided a balanced approach, respecting both practical needs and theoretical principles. Together, their
perspectives underscore the importance of clarity and judicious decision-making in programming, rejecting
dogmatic approaches in favor of pragmatic, thoughtful development practices.


### My Take

The foundational purpose of programming languages is to bridge the gap between human understanding and
machine operation. While computers themselves require only low-level machine instructions to function,
human programmers need abstraction to make sense of and manage the complexity of what machines do.
High-level languages allow us to conceptualize, organize, and express our intentions in a way that
aligns with our cognitive processes, rather than the machine's operation.

Historically, constructs like *goto* emerged as natural extensions of machine operations, especially
in assembly language, where direct control over jumps and memory was essential. Early high-level
languages mirrored this closeness to the hardware, often inheriting goto as a "natural" mechanism for
control flow. However, as software complexity grew, overusing goto revealed its weaknesses: it disrupts
the structure, introduces brittleness, and undermines readability and maintainability. These issues
arise because goto is in a way more aligned with the machine's needs than our higher-level reasoning.

Edsger Dijkstra's critique of goto and the structured programming movement were responses to these
shortcomings, advocating for constructs that better align with how humans reason about logic and flow.
These ideas paved the way for modern languages designed around readability, modularity, and abstraction,
which prioritize the programmer's ability to understand and maintain code.

Donald Knuth's nuanced perspective reminds us that while structured programming improves clarity, strict
rules should not overshadow practicality. In certain performance-critical or unique cases, goto might
still provide an optimal solution. This balance between theory and practical need has shaped programming
practices.


### Extending to AI and LLMs

The rise of large language models (LLMs) shows how high-level abstractions, even in programming languages,
can be effectively parsed and understood by artificial intelligence. LLMs operate at a level *akin* to human
cognition, "interpreting" and generating high-level language constructs to solve problems or assist programmers.
This parallels our own reliance on abstractions to navigate the machine's complexity. Here, I think that the
high-level constructs in high-level languages have their parallel with LLMs in that both serve as mediators
between human intent and low-level execution.

If AI could fully understand and manipulate machine instructions without requiring intermediate high-level
abstractions, it could bypass the layers we rely on. Such an AI could optimise and execute tasks directly in
ways humans find hard to conceptualize. This might raise significant challenges:

1. High-level languages provide us with a sense of control and understanding. A direct AI-machine interface
   could obscure these processes, making it harder for us to verify or debug its operations. This opacity
   might erode trust in the system.

2. High-level languages are not just about machine efficiency but also about collaboration and communication
   among developers. Even if AI can operate directly on machine code, high-level abstractions will remain
   vital for humans to engage with the software lifecycle. Not the least for the code we already have.

3. The coexistence of human programmers and AI might lead to hybrid systems where AI handles low-level
   optimisation while humans focus on high-level design and logic, with both communicating through familiar
   abstractions.

The history of goto illustrates the tension between machine-oriented constructs and human-oriented reasoning in
programming. While AI has the potential to transcend human limitations, programming languages and constructs like
structured programming will likely remain essential, as they cater to our cognitive needs and collaborative
workflows. Future AI systems, even those capable of direct machine interfacing, must balance their power with
transparency and alignment with human understanding. This ensures that as we evolve our tools, we haveto or should
retain our ability to guide and control the systems we create?

