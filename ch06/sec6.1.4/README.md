
## Methodologies under LLMs

### Code Reviews and Pair Programming

*Transforms and Intensifies*

Code reviews become *absolutely essential* but fundamentally different:
- Previously: reviewing human-written code for bugs, style, logic
- With LLMs: *validating AI output*--checking for subtle bugs,
  security issues, inappropriate patterns, and verifying it actually
  solves the problem correctly

The skill shifts from "does this code work?" to "did the AI understand the requirements?
Are there hidden assumptions? Does this integrate properly with our system?"

*Pair programming evolves* into:
- *Human-AI pairing*: one person prompting, another reviewing output in real-time
- *Human-human pairing*: both working with AI, but focused on architectural
  decisions and validation rather than typing code
- The "navigator" role intensifies--less about catching typos, more about
  strategic oversight

*Future:* Even more critical than before, but requires new skills in AI output evaluation.


### Iterative Refactoring

*Becomes Paradoxical*

This one gets weird:
- Refactoring assumes you understand the code intimately enough to improve it
- But if LLM generated it, do you have that understanding?
- You could ask the LLM to refactor its own code--but does that count as "craftsmanship"?

*Two scenarios emerge:*

1. *Shallow refactoring*: "This generated code is messy, regenerate it better"
   -- fast but doesn't build understanding
2. *Deep refactoring*: Manually reworking AI-generated code to truly understand and improve it
   -- this might be where real learning happens

*The risk:* Developers skip refactoring entirely because "it works, and I didn't write it anyway,
so why invest the effort to understand it deeply?"

*Future:* Could split into two camps--those who use LLMs to infinitely regenerate until
"good enough," versus those who manually refactor AI output as a learning/quality practice.
The second group maintains craft skills; the first doesn't.


### TDD and Small, Incremental Steps

*Potentially Strengthened, But Role Changes*

TDD could become *more powerful* with LLMs:
- Write tests first (human-written, expressing requirements precisely)
- Generate implementation via LLM
- Tests validate the AI output
- Iterate until tests pass

This actually gives you *more confidence* because:
- Tests are human-authored (you understand them)
- Multiple implementations can be generated and tested quickly
- The tests serve as a specification the LLM must meet

*But there's a trap:*
- If you ask the LLM to write both tests and implementation, you've lost the validation benefit
- Tests might pass but test the wrong thing

*The methodology transforms* from "test to guide design" to
"test to validate AI understanding of requirements."

*Future:* TDD becomes even more important as a *validation framework* for AI output.
The tests become the human's specification that the AI must satisfy.


### Building Personal Coding Standards and Style

*Faces Existential Crisis*

This is deeply problematic:
- How do you develop a personal style when you're not writing the code?
- Do you develop a "prompting style" instead?
- Does your style become "how you curate and modify AI output"?

*What might survive:*
- Standards for *when* to use LLMs vs. write manually
- Preferences for *how* to structure prompts
- Criteria for *evaluating* AI-generated code
- Patterns for *integrating* AI and human-written code

*What's lost:*
- The muscle memory of writing code in a certain way
- The aesthetic feel of your own coding voice
- The unconscious patterns that emerge from repeated practice

*Future:* "Personal style" migrates from code production to code orchestration and curation.
But it's less embodied, more abstract. This might be the biggest loss for the craft philosophy.


### Tool Proficiency and Customisation

*Completely Reshapes*

The toolset changes radically:
- *Traditional tools* (IDE, debugger, version control) still essential but used differently
- *New tools* emerge: prompt libraries, AI output validators, code comparison tools, AI-assisted refactoring tools

*What stays important:*
- Deep knowledge of your IDE for reading/navigating AI-generated code quickly
- Version control becomes more important (tracking what was AI vs. human)
- Debugging skills intensify (debugging code you didn't write)

*What becomes new:*
- Proficiency with LLM interfaces and prompt engineering
- Tools for managing prompt libraries and patterns
- Systems for tracking which code was generated how (provenance)

*Future:* Tool mastery remains crucial but the toolkit expands dramatically.
The craftsperson's tools now include AI itself.


### Regular Retrospective and Self-Improvement

*Changes Focus Dramatically*

Retrospectives need to examine different questions:
- "Where did the LLM solve problems elegantly that I wouldn't have?"
- "Where did I accept AI output I shouldn't have?"
- "Which of my prompts led to good vs. poor code?"
- "When should I have written code manually instead?"

*New patterns to identify:*
- Over-reliance on AI for problems you should understand deeply
- Prompting patterns that consistently produce good/bad results
- Areas where your validation skills are weak

*The learning loop changes:*
You're not just learning from your code; you're learning from your *interaction with AI*.

*Future:* Retrospectives become more meta--reflecting on the human-AI collaboration process,
not just the code produced.


### Mentoring and Knowledge Sharing

*Most Fundamentally Disrupted*

This is where the craft model really breaks down:

*Traditional mentoring:*
- Junior watches senior write code
- Junior tries, senior reviews
- Knowledge transfers through observation and practice

*With LLMs:*
- Both junior and senior can generate code instantly
- What does the senior know that the junior doesn't?
- How do you teach tacit knowledge when the LLM generates solutions?

*What mentoring becomes:*
- Teaching *judgment*: how to evaluate AI output
- Teaching *problem decomposition*: how to structure tasks for LLMs
- Teaching *architectural thinking*: how pieces should fit together
- Teaching *when not to use AI*: knowing when manual coding is better

*The critical problem:*
Juniors might never develop the *foundational understanding* that comes from
struggling to implement algorithms, debugging obscure errors, or refactoring
messy code. They learn to prompt and review, but do they learn to
*think like the computer*?

*Future:* Mentoring splits into two tracks:
1. *Fundamentals track*: Teaching core CS concepts, algorithms, system design
   *without* LLMs initially--building the foundation needed to evaluate AI output
2. *AI-augmented track**: Teaching effective LLM collaboration--but only after foundations are solid




### Overall Assessment

*Most endangered:* Personal coding style, traditional mentoring, the tactile relationship with code

*Most transformed:* Code review (now AI validation), TDD (now AI specification), tool proficiency (expanded toolkit)

*Most strengthened:* Retrospectives (meta-learning), testing as validation framework

*The fundamental tension:*

These methodologies assumed you build understanding *through the act of creation*.
LLMs break that link. You can have creation without understanding, or understanding without creation.

The methodologies that survive will be those that:
1. Force deep engagement with problem structure (TDD, architecture)
2. Validate understanding independently (testing, code review)
3. Build judgment through reflection (retrospectives)

The ones that fade are those that depended on *learning through doing* when the AI is now doing it for you.

*The existential question for craft philosophy:*
Can you become a master craftsperson by exclusively curating and refining the work of others?
Or does mastery require you to have once built from raw materials yourself?


