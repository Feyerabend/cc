
## LLMs Transforming the Craftsmanship Model

So far, we have largely avoided discussing LLMs in relation to methodology and philosophy,
in part because the transformations have been exceptionally rapid. This repository is an
attempt to address that gap.

*Code quality and maintainability*--The emphasis might shift from writing maintainable
code to writing maintainable *prompts* and effectively reviewing LLM-generated code.
"Craft" could become more about knowing what good code looks like and how to guide AI
toward it, rather than writing every line yourself. However, this also risks lowering
standards if developers accept AI output without deep understanding.

*Personal style and adaptability*--Individual coding style may matter less when much
code is AI-generated. Instead, "personal style" might evolve into distinctive approaches
to problem decomposition, prompt engineering, and AI collaboration workflows. The
craftsperson's toolkit expands to include knowing which tasks to delegate to AI versus
handle manually, and how to blend both effectively.

*Mentorship and apprenticeship*--This could be most profoundly affected. Traditional
learning-by-doing becomes complicated when AI can generate solutions instantly. Juniors
might struggle to develop intuition and tacit knowledge if they rely too heavily on AI.
Mentorship may need to focus more on judgment, architecture, and problem-framing rather
than syntax and implementation details.

*New aspects of craftsmanship might emerge:*
- Skill in evaluating and improving AI-generated code
- Ability to break problems into AI-suitable vs. human-suitable components  
- Understanding when AI solutions are "good enough" versus when human refinement
  is essential
- Developing a refined sense for what AI can and cannot do well

The core question: does craftsmanship require direct creation,
or can it exist in skillful orchestration and refinement?


__What you need to know?__

*Domain and context understanding*--You must deeply understand the *problem space*: What are you actually
trying to solve? What constraints exist? What could go wrong? This isn't code knowledge--it's about the real-world
system you're building for. Without this, you can't even properly specify what you want the AI to create.

*Architectural judgment*--You need to understand how pieces fit together: data flows, dependencies, performance
characteristics, security boundaries. You don't necessarily need to write every algorithm, but you must know
*which* algorithms matter, where bottlenecks occur, what tradeoffs exist. This is systems thinking more than coding skill.

*Code literacy for evaluation*--You need enough understanding to *read* and *critically assess* what the AI produces.
Can you spot subtle bugs, security vulnerabilities, or maintainability issues? This requires knowing what good code
looks like, common pitfalls, edge cases--even if you didn't write it yourself.

*The substrate/interface knowledge*--Crucially, you need to understand what you're *connecting to*: APIs, databases,
hardware constraints, user interfaces, existing codebases. The AI might generate perfect code in isolation that fails
because it misunderstands the environment it must operate within.


__Why you need these__

Because *verification is harder than generation*. An AI can produce plausible-looking code quickly,
but only someone with genuine understanding can determine if it's *correct, appropriate, and safe* for the specific context.
The responsibility doesn't disappear--it shifts from creation to validation.


__How deep must this knowledge go?__

Here's where it gets interesting. You might not need to know *how to implement* a particular sorting algorithm,
but you need to know:
- That choice of algorithm matters for your data characteristics
- How to recognise when the AI chose poorly
- What the performance implications are
- How it interacts with the rest of your system

It's less about memorising implementations and more about having a *mental model* of how software systems
work--cause and effect, tradeoffs, failure modes.


__The dangerous middle ground__

The real risk is developers who know *just enough* to use AI tools but not enough to catch
their mistakes. They can generate code but lack the judgment to evaluate it.

So perhaps the answer is: you need *conceptual depth* more than *implementation breadth*.
Understanding principles, patterns, and system behaviour becomes more critical than remembering
syntax or algorithm details. But that understanding must be genuine--tested through
experience--not superficial.


__To know that algorithm choice matters for your data characteristics__

Yes, you need concrete knowledge of algorithms--not necessarily how to implement quicksort
from scratch, but you need to know:
- O(n log n) vs O(n²) isn't just abstract notation--you need to viscerally understand what
  happens when n = 1,000 vs 1,000,000
- Hash tables vs binary trees: when does each degrade? What's the memory vs speed tradeoff?
- Sequential vs random access patterns on your actual hardware

You can't get this from reading--you need to have *experienced* the pain of choosing wrong.
You need to have watched a program crawl because you sorted a million items with bubble sort.


__To recognise when AI chose poorly__

You absolutely need to read the actual code it generated. Which means:
- Language fluency: understanding idioms, recognising anti-patterns, spotting subtle bugs
- Knowledge of standard library implementations: knowing that Python's `list.sort()` is
  Timsort (stable, adaptive), while a naive implementation might not be
- Ability to trace execution mentally: "what happens when this input is empty?
  When it's malicious? When it's unexpectedly large?"


__To understand performance implications__

This requires multi-layered knowledge:
- *Algorithm theory*: Big-O complexity
- *Implementation details*: Does this language use reference counting or GC? Are these copies or views? 
- *System knowledge*: CPU cache behaviour, disk I/O, network latency, database query plans
- *Empirical experience*: Having actually profiled code and been surprised by what's slow


__How it interacts with the rest of your system__

This demands:
- Reading and understanding the existing codebase (language fluency essential)
- Knowing the libraries/frameworks being used--their contracts, limitations, quirks
- Understanding concurrency models, state management, error propagation
- Knowledge of the deployment environment


__So what's the minimum viable knowledge?__

Here's my revised position: You need *layered understanding*:

1. *Theoretical foundation*: Algorithm complexity, data structures, design patterns--the conceptual toolkit
2. *Language competence*: Ability to read code fluently, recognise idioms and anti-patterns,
   understand the execution model
3. *Empirical intuition*: Experience-based sense of what performs well, what breaks, what's
   maintainable--gained through trial and error
4. *System context*: Understanding of the specific environment, constraints, and existing code

You might not need to *write* every algorithm from memory, but you need to have *implemented enough algorithms*
that you *understand* them deeply. Reading AI-generated code without this foundation you might spot obvious errors,
but miss subtle problems.


__The uncomfortable truth__

To effectively use AI as a programming tool, you probably, just guessing, need 70-80% of the knowledge
you'd need to program without it. The AI doesn't reduce the knowledge requirement as much as we might
hope--it shifts *where* you spend your time, from writing to reviewing and architecting.


*Case in point: An [example](./new/) shows that an LLM can get things wrong,
and you as a human might have to spot such errors, even when you done quite
right to [start](./original/) with?*

