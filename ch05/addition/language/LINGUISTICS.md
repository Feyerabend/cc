
## Linguistics and Computational Linguistics

Linguistics, the scientific study of language, has evolved dramatically over the
centuries, with roots in philosophy and strong ties to computing. The emphasis here
is on how linguistics shifted from descriptive studies of language to formal,
generative models that could be implemented computationally, mirroring the analytic
tradition's push for precision. This history underscores language as a structured
system amenable to rules, parsing, and even automation--concepts central to compilers and AI.


### History

Linguistics as a modern discipline began in the 19th century, but its relevant threads
for computing trace back to philosophical inquiries into language structure and meaning.

Ferdinand de Saussure, often called the father of modern linguistics, laid the groundwork
in his posthumously published *Course in General Linguistics* (1916). Saussure introduced
the distinction between *langue* (the abstract system of language) and *parole* (actual speech acts),
emphasising language as a system of signs where meaning arises from differences
(e.g., "cat" means what it does because it's not "bat" or "hat"). This structuralist
view treated language as a network of relations, not isolated words--in a way much like
how data structures in computing rely on relational contexts.

Structuralism influenced anthropologists like Claude Lévi-Strauss and linguists like
Roman Jakobson, who applied it to phonology (sound systems) and morphology (word formation).
The key idea was that language is rule-governed and analysable into discrete units
(phonemes, morphemes), actually prefiguring tokenization in compilers.


![Syntactic Structures](./../../assets/image/chomsky.png)

#### Generative Grammar and Chomsky's Revolution (1950s-1970s)

Noam Chomsky transformed linguistics with his 1957 book *Syntactic Structures*[^synt],
challenging behaviorist views (e.g., B.F. Skinner's idea that language is learned through stimulus-response).
Chomsky proposed generative grammar: a finite set of rules that can generate infinite sentences. This included:
- *Syntax*: Hierarchical structures (phrase structure rules, tree diagrams) to explain sentence formation.
- *Semantics*: Deep structures underlying surface forms, addressing ambiguity (e.g., "Flying planes can be dangerous").
- *Pragmatics*: Later expansions on context and use.

Chomsky's hierarchy of grammars (regular, context-free, context-sensitive, recursively enumerable) directly
inspired formal language theory in *computer science*, used in compiler design (e.g., context-free grammars
for parsing programming languages). His universal grammar hypothesis--that humans have an innate language
faculty--sparked debates on whether language is biologically hardwired, influencing AI models of "learning" language.

This era aligned with analytic philosophy: Chomsky's work operationalised Wittgenstein's "logical form"
and Russell's logical atomism, turning abstract ideas into testable, rule-based systems.

[^synt]: Chomsky, N. (2002). *Syntactic structures* (2nd ed.). Mouton de Gruyter.
A favourite of mine for its clarity, even though I do not agree with the rationalist view
as I'm more inclined to empiricists like Quine.


#### Post-Chomskyan Developments and Pragmatics (1970s-Present)

By the 1970s, linguists like J.L. Austin and John Searle developed speech act theory, focusing on
pragmatics--how language performs actions (e.g., promises, commands). H.P. Grice's coöperative
principle and implicatures explained implied meanings beyond literal semantics.

Cognitive linguistics (e.g., George Lakoff's conceptual metaphors) shifted toward embodied meaning,
where language reflects human experience (e.g., "time is money"). Meanwhile, sociolinguistics
examined power and culture in language (e.g., Pierre Bourdieu's linguistic capital).

These broadened the analytic focus: From rigid structure to flexible, context-dependent use,
anticipating challenges in AI like handling sarcasm or cultural nuances; are we still there?


### Computational Linguistics: From Rules to Data

Computational linguistics (CL) emerged in the mid-20th century, applying linguistic theories
to machines. It evolved from rule-based systems to statistical and neural approaches, bridging
philosophy's "language as logic" with computing's "language as processable data."


#### Early Rule-Based Era (1950s-1980s)

Inspired by Chomsky, early CL focused on machine translation (MT). The Georgetown-IBM experiment
(1954) translated Russian to English using dictionaries and rules, but failed on ambiguity--echoing
philosophical puzzles like Quine's "gavagai" (indeterminacy of translation).[^joke]

Key developments was:
- Parsers: Algorithms like Earley's (1970) for context-free grammars, turning Chomsky's trees into code.
- Semantic networks: Roger Schank's scripts (1970s) modeled understanding via story structures.
- Expert systems: Like SHRDLU (1970) by Terry Winograd, which parsed natural language commands
  in a block world, demonstrating syntax-semantics integration.

Much of this was developed in and central to the AI field of the time.
This also mirrored analytic philosophy: Machines enforced logical clarity,
dissolving ambiguities through formal rules.

[^joke]: I must include the famous and somewhat apocryphal anecdote from the early days
of machine translation that illustrates the challenges of ambiguity in language processing.
It was about a biblical quote from Matthew 26:41 that reads:
"The spirit is willing, but the flesh is weak."
In this story, this English sentence was fed into an early computer system for translation
into Russian, and then translated back into English. The result came out garbled as something like
"The vodka is good, but the meat is rotten"..


#### Statistical Shift (1980s-2000s)

IBM's statistical MT (1980s) used probabilities from corpora, influenced by information
theory (Claude Shannon). Tools like hidden Markov models handled speech recognition.

Frederick Jelinek's quip--"Every time I fire a linguist, the performance of the speech
recognizer goes up"--highlighted the move from hand-crafted rules to data-driven methods.
This era saw:
- Corpus linguistics: Large text collections (e.g., Brown Corpus, 1960s) for empirical analysis.
- WordNet (1985): A lexical database grouping synonyms, aiding semantic processing.

Pragmatics entered via discourse analysis tools, like those for anaphora resolution
(e.g., "he" referring back).


#### Neural and Deep Learning Era (2010s-Present)

Deep learning revolutionised CL with models like word2vec (2013) for embeddings,
capturing semantic relations statistically. Transformers (2017) enabled LLMs like GPT,
trained on vast data to predict text.

Key ideas here:
- Distributional semantics: "You shall know a word by the company it keeps"
  (J.R. Firth, 1957), implemented in vectors.
- Multimodality: Models like CLIP (2021) integrate vision and language, testing
  the "collapse to language" thesis.

CL now tackles philosophy's "other traditions": Handling context (BERT, 2018),
bias (from cultural data), and emergence (how LLMs "understand" without explicit rules).


### Ideas Explored and To Explore

Linguistics and CL have inspired countless implementations, from practical tools to
speculative experiments. Below, we highlight some ideas that *have been explored*
and suggest *new ideas to explore*, building on historical foundations. These blend
rigour with interpretation, inviting hands-on work in code or theory.


#### Ideas That Have Been Explored

These concepts have been implemented, often revealing tensions between formal
structure and human-like flexibility.

1. *Generative Grammars in Parsers*
   - *Explored*: Chomsky's grammars underpin tools like Yacc (1970s) for compiler
     construction and NLTK (2001) for Python-based parsing. Projects like Stanford
     Parser (2003) apply them to natural language, generating syntax trees for sentences.
   - *Insights*: Demonstrates how ambiguity in English leads to multiple parses,
     mirroring philosophical debates on meaning.

2. *Statistical Semantics in Word Embeddings*
   - *Explored*: Word2vec and GloVe (2014) operationalize distributional hypotheses,
     used in search engines (e.g., Google) and sentiment analysis. Debias methods (2016)
     address cultural biases in vectors.
   - *Insights*: Shows pragmatics in action--embeddings capture use-based meaning but
     struggle with rare contexts.

3. *Pragmatic Inference in Dialogue Systems*
   - *Explored*: Systems like ELIZA (1966) simulated conversation via pattern matching;
     modern chatbots (e.g., Dialogflow) use Gricean implicatures for intent detection.
   - *Insights*: Highlights human limitation--bots fail on sarcasm, echoing hermeneutic
     views of context.

4. *Multimodal Language Processing*
   - *Explored*: Models like VisualBERT (2019) fuse images and text, used in captioning
     (e.g., Microsoft COCO dataset challenges).
   - *Insights*: Tests the "language bottleneck"--non-verbal data improves understanding
     but still relies on symbolic bridges.


#### Ideas To Explore

These build on history, departing into future experiments.
Use tools like Hugging Face for LLMs or NLTK for basics.
You might return to this after exploring other chapters in the book.

1. *Chomskyan Hierarchy Simulator with LLMs*
   - *Description*: Build a Python tool that generates sentences from different
     Chomsky grammar levels (e.g., regular for simple patterns, context-sensitive
     for complex), then uses an LLM to "parse" them naturalistically.
     Compare rule-based vs. probabilistic outputs.
   - *Departure*: Extends generative grammar to neural era, testing if LLMs can
     "rediscover" universal grammar from data.
   - *Something to Think About*: Do LLMs enforce analytic precision or introduce
     pragmatic "errors"? Could this detect innate biases in AI?

2. *Structuralist Sign Network Visualizer*
   - *Description*: Create a web app (using NetworkX) that maps word relations
     from a corpus as a Saussurean sign system graph. Input text, output interactive
     differences (e.g., oppositions like "hot/cold").
   - *Departure*: Operationalizes early structuralism computationally, contrasting
     with Chomsky's hierarchies.
   - *Something to Think About*: How does power (e.g., from biased corpora) distort
     the network? Can it model post-structuralist "slippage"?

3. *Pragmatic Bias Detector in Historical Texts*
   - *Description*: Use an LLM to analyze old linguistic works (e.g., Saussure vs.
     modern sociolinguistics) for implicatures tied to culture/power. Output "deconstructed"
     versions with highlighted biases.
   - *Departure*: Brings hermeneutics to CL, using AI to interpret history interpretively.
   - *Something to Think About*: Can machines simulate Gricean cooperation across eras?
     What if AI "invents" implicatures?

4. *Embodied Language Game Simulator*
   - *Description*: Develop a game where agents "learn" language via simulated
     experiences (e.g., metaphors like "grasp an idea" tied to virtual actions).
     Integrate LLMs for dynamic rule evolution.
   - *Departure*: From cognitive linguistics, testing if embodiment escapes the analytic
     "structure-only" trap.
   - *Something to Think About*: If language evolves in simulation, does it converge on
     Chomsky's universals or diverge culturally?

These ideas hopefully invite iteration, blending history
with creation to probe language's computable limits.
