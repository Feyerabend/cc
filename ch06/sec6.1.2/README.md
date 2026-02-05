
## Change of Some Philosophies Approach Under LLMs

The craft philosophy may face an existential crisis because its core value
is *embodied knowledge through direct engagement with materials*.


__What breaks__

- "Deep respect for the materials of the code" -- but you didn't write the code,
  didn't feel the resistance of the language, didn't experience the computer's response to your choices
- "Holistic understanding" -- how can you have holistic understanding of a system where large portions emerged from a black box?
- "Continuous integration of all aspects" -- but the LLM generates components in ways you didn't experience building


__What might evolve__

A new form of craft emerges: *the craft of orchestration and curation*. The "materials" become:
- The problem space itself (deep domain understanding)
- The LLM as a tool with its own grain and characteristics (knowing what it does well/poorly)
- The art of code review and refinement
- Architectural judgment about how pieces should fit

The *tactile relationship with code* diminishes.


#### The "Scientific" Approach Under LLMs

The scientific philosophy actually *gains power* in some ways but faces different challenges.

*What strengthens:*
- *Rapid hypothesis testing* -- generate multiple implementations instantly,
  benchmark them, gather data
- *Controlled experiments* -- "Does algorithm X outperform algorithm Y for this data?"
  becomes trivially easy to test
- *Empirical validation* -- you can generate test cases, run experiments,
  measure outcomes at unprecedented speed
- *A/B testing approaches* -- generate variants, measure, iterate

*What becomes problematic:*
- *Understanding causation* -- when the LLM generates code, you have measurements
  but less understanding of *why* it performs as it does
- *Reproducibility* -- LLM outputs vary; the same prompt may yield different implementations
- *Confounding variables* -- is poor performance due to the algorithm,
  the specific implementation, or an LLM artifact?

__What might evolve__

The scientific approach becomes *meta-scientific*: you're not just testing your code, you're
testing the LLM's code-generation capabilities, developing empirical knowledge about
*what prompts produce what qualities of code* for different problem types.


#### A New Synthesis?

We might see a *three-phase methodology* emerge:

### Phase 1: Empirical Exploration (Scientific + LLM)
- Generate multiple approaches via LLM
- Benchmark and measure systematically  
- Identify promising directions through data
- Build empirical understanding of the problem space

### Phase 2: Craft Refinement (Hybrid)
- Deep reading and understanding of generated code
- Holistic integration and architectural coherence
- Manual refinement of critical paths
- Development of "feel" for the system through review and modification

### Phase 3: Validated Integration (Scientific)
- Rigorous testing of the integrated whole
- Performance profiling and optimization
- Documentation of what works and why
- Regression testing to prevent degradation


#### The Uncomfortable Questions

*For craft:* Can you be a craftsperson if you didn't make the thing? Is there craft in *selection*
and *refinement* rather than *creation*? The Shaker furniture maker chooses wood carefully and
finishes it beautifully--but they still cut and joined it themselves.

*For science:* If you can't explain *why* the code works (because the LLM wrote it in ways you don't
fully understand), is it science or just empiricism? You have measurements but potentially less theory.


#### What Knowledge Do You Actually Need?

Going back to your earlier challenge, to execute any of these approaches with LLMs, you need:
1. *Architectural knowledge* -- to structure the problem for the LLM
2. *Algorithmic literacy* -- to evaluate what it produces  
3. *Implementation fluency* -- to read, debug, and refine generated code
4. *Empirical experience* -- to know what "good" looks like
5. *Domain expertise* -- to verify correctness beyond syntax

The LLM doesn't eliminate these requirements. It might even *intensify* them because you
need the judgment to evaluate code you didn't write, which is arguably harder than writing it yourself.


#### A Completely New Philosophy?

Perhaps what emerges is *"Programming as Curation"*:
- Framing problems precisely
- Generating and evaluating multiple solutions
- Synthesising the best elements from various approaches  
- Ensuring coherence and quality across AI-generated and human-written code
- Building and maintaining understanding of a system you orchestrated but didn't entirely author

This curator needs deep technical knowledge (can't curate what you can't evaluate)
but expresses it differently than the traditional craftsperson or scientist.

