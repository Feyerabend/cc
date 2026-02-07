
## Documentation

An example following the Bayesian approach structure,
focusing on a tool that becomes *more* valuable in the LLM era:


### Code Documentation and Comments

*1. Starting with a prior belief.* A programmer begins with the belief that
"Extensive code documentation and comments are often redundant. Good code should
be self-documenting through clear naming and structure." This belief might
stem from experiences where comments became outdated, contradicted the code,
or cluttered otherwise clean implementations. The prior is that minimal
documentation is best practice.

*2. Gathering new evidence.* As LLMs become integrated into development
workflows, the programmer observes several patterns: AI-assisted code generation
tools produce better results when given well-documented codebases to reference.
When using LLMs for code review or bug detection, the AI provides more accurate
and contextual suggestions when comments explain *why* certain design decisions
were made, not just *what* the code does. They notice that LLMs can automatically
generate comprehensive API documentation from well-commented code, but struggle
with uncommented "self-documenting" code that lacks intent explanation.

*3. Updating beliefs (posterior).* The programmer revises their position:
"In the LLM era, documentation serves dual purposes. Human understanding *and*
AI context. Comments explaining intent, architectural decisions, and edge cases
are now critical infrastructure that multiplies in value." The posterior belief
recognises that documentation isn't just about human readability anymore;
it's training data and context for AI assistants.

*4. Iteration and further evidence.* Over time, they experiment with different
documentation styles, discovering that structured comments (like JSDoc or docstrings)
enable better LLM assistance, that architectural decision records (ADRs)
help AI tools understand system constraints, and that inline comments explaining
"why not" (rejected approaches) prevent LLMs from suggesting already-dismissed solutions.

The programmer adopts a new practice: *writing documentation with both human
and AI consumers in mind*, creating a richer knowledge layer that amplifies
the effectiveness of AI development tools while maintaining long-term codebase
intelligibility.

Obvious projects here is naturally experiencing all of this!
