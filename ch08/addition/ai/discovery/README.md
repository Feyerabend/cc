
## The Dual Pathways to Artificial Intelligence: Optimisation and Discovery

The pursuit of artificial intelligence (AI) has long been shaped by a fundamental
philosophical and practical divergence: the prevalent "Optimisation View" and the
less conventional "Discovery Perspective." These views are more of metaphores,
than perhaps actual standpoints. But they reflect the different views. This text
delves into how these differing approaches profoundly influence AI capabilities,
limitations, and their potential to emulate or surpass human intelligence.

The core challenge in AI lies in replicating or extending the multifaceted nature
of intelligence, which encompasses more than just efficient problem-solving. This
pursuit has largely been dominated by two contrasting paradigms. Mainstream AI's
remarkable successes in areas like image recognition, natural language processing,
and strategic game playing are primarily attributed to its prowess in optimising
for specific, quantifiable metrics, such as minimising error rates or maximising
reward signals. This pervasive reliance on objective functions reveals an underlying,
often unstated, assumption within mainstream AI research: that intelligence is
fundamentally about achieving a predefined objective as efficiently and effectively
as possible. This goal-directedness is deeply embedded within the mathematical
formulations that define and govern these systems, making optimisation the central
driving force.

In contrast, the "Discovery Perspective," particularly as championed by researchers
like Kenneth Stanley, posits a counter-intuitive argument: that true intelligence,
especially its creative and open-ended learning facets, may not emerge from direct
optimisation towards a fixed objective. Instead, it may arise as a serendipitous
side effect of a curiosity-driven, divergent search process. Current AI systems,
despite their advancements, exhibit significant and persistent limitations, including
a lack of true understanding, genuine creativity, and an inability to reason beyond
their programming. There are also fundamental theoretical bounds that apply to any
computational system, including AI. These limitations are not simply technical
challenges to be overcome with more data or compute; they appear to be fundamental
consequences, or even inherent byproducts, of the optimisation paradigm itself.
The emergence of the "Discovery Perspective" suggests a recognition of these
deep-seated limitations and a search for an alternative or complementary approach,
indicating that the field of AI may be on the cusp of, or already experiencing,
a conceptual shift.

While the Optimisation View has been undeniably powerful and has driven significant
advancements, its inherent limitations suggest that a more complete and robust
form of artificial intelligence, particularly Artificial General Intelligence
(AGI) capable of human-like adaptability and creativity, may necessitate a
fundamental shift towards, or at least a profound integration of, discovery
principles. Understanding the interplay and distinct contributions of both
paradigms is crucial for charting the future trajectory of AI.


### The Optimisation View in Mainstream AI: Principles and Mechanisms

Mainstream AI, particularly machine learning, is fundamentally characterised by
its use of algorithms trained on data sets to create self-learning models designed
to predict outcomes and classify information without explicit human intervention.
The core principle across diverse learning techniques in AI is to "optimise
an evaluation function to improve the quality of the results according to
certain standard". At its heart, mainstream AI is a process of finding the "best"
configuration or parameters for a model to perform a given task, based on a
quantifiable measure of success or failure.

A profound commonality across all mainstream machine learning paradigms is their
fundamental operation by optimising an explicit or implicit objective function.
Whether it is supervised learning, reinforcement learning, unsupervised learning,
or evolutionary learning, each fundamentally operates by optimising an explicit
or implicit "objective function." This pervasive reliance on objective functions
demonstrates that the "Optimisation View" is not merely one characteristic among
many, but rather the fundamental, unifying principle that defines and drives
virtually all mainstream AI paradigms. This highlights a core design philosophy
where success is always measured against a predefined, quantifiable target.


### Core Optimisation Techniques

*Supervised Learning:* In supervised learning, algorithms are trained on "labeled
data sets that include tags describing each piece of data," effectively providing
an "answer key" to guide the algorithm's interpretation. This method is widely
used for prediction and classification. The performance of a supervised machine learning
model is quantitatively measured by a "loss function," which calculates the "difference"
or "error" between the model's predicted outputs and the actual, desired target values.
The explicit objective during training is to "minimise this difference,
thereby improving the model's accuracy".

An "optimiser" is an algorithmic component specifically designed to minimise the
loss function. Its primary goal is to iteratively adjust the internal parameters
(weights and biases) of the neural network or model in a direction that reduces
the calculated loss, typically through methods like gradient descent. This design choice
carries a significant implication: mainstream AI systems, in their current form,
do not "understand" the task or the world in a human-like, conceptual sense.
Instead, they learn to correlate specific inputs with desired outputs,
effectively optimising a proxy metric for success. The "understanding" or
"meaning" of the task is externalised and encoded within the data labels
provided by humans or the environment, rather than being an emergent, internal
property of the AI system itself. This fundamental reliance on external guidance
for defining "correctness" inherently limits the AI's capacity for true,
independent understanding.

Common loss functions, which define these optimisation targets, include:

* *Mean Squared Error (MSE) / L2 Loss:* Used for regression, it penalises larger errors by squaring
  the differences between predicted and actual values, making it less robust to outliers.

* *Mean Absolute Error (MAE) / L1 Loss:* Another regression function that measures the average absolute
  difference, making it more robust to outliers than MSE.

* *Binary Cross-Entropy Loss:* Ideal for binary classification, quantifying the difference between
  predicted probabilities and actual binary labels.

* *Categorical Cross-Entropy:* Applied to multi-class classification, measuring the discrepancy between
  predicted probabilities and actual labels for each class.

* *Huber Loss:* A hybrid of MSE and MAE, robust to outliers while maintaining smoothness.

* *Log Loss:* Evaluates classification models with probability outputs.


*Reinforcement Learning (RL):* RL trains algorithms through "trial and error," where agents operate
in environments and receive "feedback following each outcome" to "optimise actions to achieve particular
outcomes". The core objective in RL is to "maximise cumulative rewards," known as the "return," which
is the total reward the agent accumulates over time. A "discount factor (γ)" weighs immediate versus
future rewards. RL is often framed as finding a state-action mapping that maximises expected total
reward within a Markov Decision Process (MDP).

Key conceptual issues in RL include "Credit assignment" (attributing rewards to specific actions) and
the "Exploitation vs. Exploration" dilemma. This dilemma is not merely a technical detail specific to
RL but represents an inherent tension within any optimisation process that operates in an unknown or
partially known environment. To achieve optimal performance, an agent must "exploit" what it already
knows to be the best actions. However, to discover potentially *even better* solutions or adapt to new
conditions, it must "explore" unknown possibilities, which carries the risk of suboptimal short-term
performance. This dilemma suggests that a purely optimisation-driven approach, by its very nature, might
struggle with truly novel discovery or "out-of-the-box" thinking if it prioritises the efficient exploitation
of known solutions too heavily. This inherent trade-off limits its capacity for open-ended innovation
and finding solutions that lie far from the initial search space. Prominent examples of successful RL
optimisation include AlphaGo and AlphaZero.

*Unsupervised and Semi-supervised Learning:* Unsupervised learning uses "unlabelled data sets" to train
algorithms, requiring them to "uncover patterns on its own without any outside guidance". For classification
or clustering, the objective is "to find a partition of the dataset with minimum within-cluster distances
and maximum between-cluster distances". Techniques include K-means clustering and Expectation-Maximisation.
Generative models like GANs implicitly optimise for data realism. Semi-supervised learning combines small
amounts of labeled data with larger unlabelled datasets, while self-supervised learning uses inherent
patterns to refine models.

*Evolutionary Learning:* This paradigm frames optimisation as a process akin to "natural selection" within
a "species" of solutions. Genetic Algorithms, for instance, encode solutions as "genes" and evaluate them
with a "fitness function." Solutions with higher fitness reproduce to form the next generation, iteratively
maximising this fitness function until convergence.

The following table summarises these key optimisation techniques:


*Table 1: Key Optimisation Techniques in Mainstream AI*

| ML Paradigm            | Primary Optimisation Objective                    | Key Mechanism/Function                                  | Example Algorithms/Techniques           |
|------------------------|---------------------------------------------------|---------------------------------------------------------|-----------------------------------------|
| Supervised Learning    | Minimise prediction error / Maximise accuracy.    | Loss Functions (MSE, MAE, Cross-Entropy)                | Gradient Descent, Neural Networks       |
| Reinforcement Learning | Maximise cumulative reward                        | Reward Function, Q-function, Policy Gradient            | Q-learning, DQN, AlphaGo                |
| Unsupervised Learning  | Discover data patterns / Optimise cluster quality | Clustering Metrics (e.g., inter/intra-cluster distance) | K-means, EM, GANs, Self-organising Map  |
| Evolutionary Learning  | Maximise solution fitness                         | Fitness Function, Crossover, Mutation                   | Genetic Algorithms, Genetic Programming |


### Inherent Limitations of Optimisation-Driven AI

Despite the remarkable successes of optimisation-driven AI, this paradigm faces fundamental
shortcomings, particularly in achieving human-like understanding, creativity, and open-ended
intelligence.

#### Struggles with Core Cognitive Abilities

AI systems, even the most advanced, process "vast amounts of data and identify patterns, but
they don't 'understand' in a way that humans do". Their comprehension is superficial, based
on statistical correlations rather than deep causal models. This "lack of true understanding"
fundamentally limits AI's ability to operate effectively in scenarios requiring common sense
or inferential reasoning that goes beyond learned patterns. The core mechanism of
optimisation-driven AI involves minimising a predefined loss function or maximising a
predefined reward signal. This process incentivises the AI to find the most efficient path
or configuration *within the given problem space* as defined by the objective function and
the training data. By focusing solely on achieving a predefined, quantifiable goal, AI systems
are not incentivised, nor are their architectures designed, to form deep conceptual models
of the world, infer underlying causal mechanisms, or explore solutions that fall entirely
outside the parameters of the optimisation target. True understanding involves building
internal representations that go beyond mere correlation.

Furthermore, AI "struggles with understanding nuance or context," often leading to "errors in
decision-making that require human intervention". This limitation severely restricts AI's effectiveness
in domains demanding complex, adaptive decision-making beyond predefined rules.

While AI can "generate content or ideas," it "lacks genuine creativity and cannot innovate outside
the scope of its programming". AI's "creativity" is typically recombinatorial or interpolative, confined
by the patterns and parameters it was trained to optimise. It "operates within the constraints of its
programming" and "cannot think creatively or make decisions outside of the parameters set by its developers"
This rigid adherence to programmed objectives or learned data distributions inherently restricts its
capacity for true novelty. Consequently, AI "cannot engage in creative problem-solving or adapt to novel
situations without explicit programming," which severely limits its applicability in innovation-driven
fields like research and development or strategic planning.

The concept of optimisation inherently involves navigating a complex "landscape" to find a minimum
or maximum. A well-known challenge in optimisation is the tendency to get stuck in "local optima"--solutions
that are the best within their immediate vicinity but are not the globally optimal solution. This tendency
can be seen as a metaphor for AI's creative limitations. The optimisation paradigm, by focusing on iterative
improvements towards a specific, fixed goal, makes AI prone to finding only the "best" solutions within a
narrow, pre-defined search space. Genuine creativity, conversely, often involves "jumping" to entirely
different, previously unexplored regions of the solution space, or even redefining the problem itself.
This "jump" is precisely what direct, gradient-following optimisation struggles with if it's not explicitly
incentivised or if the objective function doesn't implicitly guide it there. This highlights a fundamental
creative constraint tied to the optimisation approach.

Directly related to the lack of creativity, AI's inability to "adapt to novel situations without explicit
programming" underscores its struggle with open-ended exploration. Optimisation typically converges on a
"best" solution for a *given* problem, rather than continuously exploring and adapting to evolving problem
definitions or entirely new environments. The "Exploitation vs. Exploration" challenge in Reinforcement
Learning further illustrates this tension. While RL can explore, its exploration is often bounded by the
reward function, which implicitly defines the "space" of desirable outcomes, potentially hindering truly
divergent or objective-free discovery.


### Dependency and Other Practical Limitations

A critical vulnerability of optimisation-driven AI is its heavy reliance on large, high-quality
datasets. "If the input data is biased, incomplete, or of poor quality, AI's output will reflect
these issues, often leading to inaccurate or misleading conclusions". This is encapsulated by the
"garbage in, garbage out" principle. This limitation is critically intertwined with the optimisation
paradigm. If the AI's objective is to minimise error or maximise reward *relative to the training data*,
then any inherent biases, inaccuracies, or ethical flaws present in that data become implicitly optimised
into the model's behaviour. The AI doesn't possess an independent mechanism to question the data's
validity, fairness, or ethical implications; it merely seeks to achieve the best possible performance
*on that specific data*. This means that the optimisation process can inadvertently amplify and perpetuate
societal biases or inaccuracies present in the real-world datasets it learns from, leading to "unfair
outcomes," particularly in sensitive applications like recruitment or financial services. The optimisation
objective itself, being purely mathematical, does not contain inherent mechanisms for ethical reasoning,
bias detection, or a critical assessment of its training data's quality beyond statistical fit.

Other key limitations include:

* *Ethical and Privacy Concerns:* The reliance on "large datasets" for training AI models
  raises significant "privacy issues" and necessitates compliance with regulations like GDPR.

* *Lack of Emotional Intelligence:* AI systems are currently unable to "understand and respond
  to human emotions effectively," which limits their utility in roles requiring empathy.

* *Interpretability:* Many advanced AI models operate as "black boxes," making it challenging
  for human users to understand their decision-making processes.

* *Resource Intensiveness:* Training and deploying complex AI systems require "significant
  computational power," leading to high energy costs and environmental impact.


#### Theoretical Limits

Beyond practical challenges, AI, as a computational system, is subject to fundamental theoretical limits:

* *Physical Constraints:* The Bekenstein bound posits "a maximum amount of information that can
  be contained within a finite region of space with finite energy". This implies a "fundamental
  limit on information density in any system, including AI systems," which could ultimately constrain
  their reasoning and information processing capabilities.

* *Computational Complexity:* Problems are categorised by their inherent difficulty. The P vs NP
  question explores whether quickly verifiable problems can also be quickly solved. If P ≠ NP, some
  problems are "inherently hard to solve, even with significant computational resources". When AI
  encounters such NP-hard problems, its ability to find optimal solutions efficiently could be
  fundamentally limited.

* *Church-Turing Thesis:* This thesis suggests that any effectively calculable function can be
  computed by a Turing machine, "setting a boundary on computability". Consequently, "tasks that
  are not Turing-computable would be beyond the reach of any AI," irrespective of its architecture
  or training data.  

* *Algorithmic Information Theory:* Concepts like Kolmogorov complexity and logical depth provide
  insights into the inherent complexity of algorithms and data, further elucidating potential
  limits on AI's ability to reason about and compress complex information.

* *General Limits of Learning from Complexity:* There is a limit to how much can be learned from
  a system. As the complexity of an information space increases, "the more difficult it becomes
  to explore the possibilities of this information space and derive useful knowledge," demanding
  exponentially more computing time. This suggests a practical and theoretical ceiling to the
  knowledge that can be extracted even with vast resources.


### The Discovery Perspective: Beyond Predefined Objectives

Kenneth Stanley and his colleagues have been prominent critics of the sole reliance on direct
optimisation in the pursuit of advanced AI. They argue that while optimisation is powerful for
well-defined problems, it inherently limits the capacity for true innovation and open-ended
intelligence. Their core argument revolves around the idea that many complex, intelligent
behaviours and profound innovations observed in nature (like evolution leading to human
intelligence) are not the result of direct optimisation towards a single, predefined objective,
but rather emerge from a process of open-ended, divergent search and the accumulation of
diverse capabilities.

This report focuses exclusively on the “Optimisation View” of mainstream AI and its inherent
limitations. It does not address Kenneth Stanley’s work on Novelty Search, Quality Diversity
algorithms, or the mechanisms underlying the “Discovery Perspective.” While we introduce the
general concept of the Discovery Perspective, a thorough exploration of its empirical examples
and specific algorithmic implementations lies beyond the scope of this report and would require
further research. Do you begin to see the potential project directions?


#### Core Tenets of the Discovery Perspective

The "Discovery Perspective" directly challenges the foundational assumption of mainstream AI's
goal-directedness and the pervasive use of explicit objective functions to guide learning. Its
emphasis on "novelty," "exploration," and the "unreasonable effectiveness of indirect search"
suggests that imposing a single, fixed objective function might actually *hinder* the emergence
of complex, truly intelligent, and creative behaviours. This implies a fundamental philosophical
disagreement about the very nature of intelligence itself--is intelligence primarily about
efficient problem-solving within predefined boundaries, or is it about continuous, open-ended
learning, adaptation, and the generation of unforeseen capabilities? This intellectual tension
forms a crucial part of this comparative analysis.

The central principles of this perspective include:

* *Emphasis on Novelty:* Prioritising the exploration of new and diverse behaviours, solutions,
  or regions of a search space, even if their immediate utility or performance against a specific
  objective is not apparent or is even low. The value lies in the novelty itself, as it expands
  the system's repertoire and potential.

* *Quality Diversity:* Instead of seeking to converge on a single "best" solution (as in traditional
  optimisation), the Discovery Perspective often aims to generate and maintain a wide range of
  high-performing, *diverse* solutions. This ensures robustness and adaptability, as a broad
  collection of skills might be more valuable in an unknown future than a single, highly optimised,
  but brittle, solution.

* *The "Unreasonable Effectiveness of Indirect Search":* This concept, central to Stanley's philosophy,
  posits that the most complex, robust, and truly innovative solutions often arise as side effects of a
  search process that is *not* directly optimising for those specific solutions. For instance, biological
  evolution did not directly optimise for human intelligence; rather, it optimised for survival and
  reproduction in diverse environments, and intelligence emerged as a powerful, indirect consequence
  of this open-ended process. This challenges the notion that intelligent systems must be engineered
  by directly optimising for intelligence.

This perspective suggests that to achieve true creativity, adaptability, and open-ended learning,
AI systems might need to abandon or significantly de-emphasise direct, fixed objective functions
in favour of mechanisms that encourage continuous, intrinsic exploration and the accumulation of
diverse skills and knowledge, without a predetermined end goal.


### Comparative Analysis: Optimisation vs. Discovery

A direct comparison of the Optimisation View and the Discovery Perspective reveals their contrasting goals,
methodologies, strengths, and weaknesses, highlighting the scenarios where each is most effective and the
potential for synergistic approaches.


#### Direct Comparison

| Feature/Aspect | Optimisation View | Discovery Perspective |
| ---- | ---- | ---- |
| *Core Goal* | Achieve a predefined, specific objective as efficiently and accurately as possible. | Open-ended exploration, generation of novelty, accumulation of diverse capabilities. |
| *Primary Mechanism* | Explicit objective functions (loss, reward, fitness); gradient-based methods; iterative refinement towards a target. | Mechanisms rewarding behavioural novelty and diversity; indirect search strategies. |
| *Definition of "Success"* | Minimising error, maximising reward, high accuracy on a specific task. | Extent of exploration, diversity of valuable outcomes discovered, even if immediate utility is unclear. |
| *Strengths* | Highly effective for well-defined, static problems; excels at achieving high performance on specific tasks; clear metrics for progress. | Potential for genuine creativity, adaptability to unforeseen circumstances, overcoming local optima; generates diverse, robust solutions. |
| *Weaknesses* | Struggles with true understanding, genuine creativity, contextual nuance, open-ended exploration; highly data-dependent, susceptible to bias; constrained by theoretical limits; prone to local optima. | Less efficient for specific, well-defined tasks; harder to quantify "progress" in traditional terms; research less mature. |
| *Typical Applications* | Image recognition, natural language processing (classification/prediction), strategic game playing (e.g., AlphaGo), automation of repetitive tasks. | Scientific discovery, artistic creation, designing novel robotic behaviours in unstructured environments, Artificial General Intelligence (AGI). |
| *View on Creativity/Understanding* | Creativity is recombinatorial/interpolative; understanding is superficial (pattern recognition). | Creativity is emergent and genuinely novel; fosters deeper, emergent understanding through exploration. |


#### Effectiveness and Synergy

The analysis of optimisations inherent limitations directly highlights critical areas (e.g., creativity,
true understanding, open-endedness) where the "Discovery Perspective" offers a compelling theoretical
solution. For instance, optimisation struggles with "out-of-the-box thinking", while discovery explicitly
promotes novelty. Conversely, optimisations strength lies in its efficiency and high performance for well-defined
tasks, which discovery, by its very nature of open-endedness, might not achieve directly or as quickly. This
fundamental contrast leads to the conclusion that these two paradigms are not mutually exclusive competitors
but rather deeply complementary. A truly robust, adaptable, and versatile AI, especially one aspiring to
human-like intelligence, would likely need to seamlessly integrate both: leveraging optimisation for known,
efficiency-driven problems and employing discovery for novel situations, to expand its knowledge base, or
to generate truly innovative solutions. This moves beyond a simple "either/or" comparison to a more sophisticated
"both/and" synthesis, recognising that each paradigm addresses different facets of intelligence.

A key practical implication arising from this comparison is the stark difference in how "success" is defined and
measured. Optimisations success is inherently quantifiable and straightforward: it's about minimising a loss
function or maximising a reward signal. This provides clear, objective metrics for progress, allows for direct
comparison of algorithms, and facilitates engineering. In contrast, the "Discovery Perspective" prioritises
abstract concepts like novelty, diversity, and open-ended exploration, which are inherently harder to quantify
or assign a single, universal "score." How does one objectively measure "genuine creativity" or the "value of
open-ended exploration" in a way that allows for algorithmic improvement and scientific benchmarking? This
difficulty in defining and measuring success poses a significant challenge for the engineering, evaluation,
and widespread adoption of discovery-driven AI systems, potentially explaining why the optimisation paradigm,
despite its limitations, remains dominant in mainstream research--it's simply easier to define, measure, and
demonstrate progress.


### Human Intelligence as a Benchmark: Bridging the Paradigms

Human intelligence stands as a compelling benchmark, seamlessly integrating both goal-directed optimisation
and open-ended discovery and creativity. We exhibit remarkable ability for highly goal-directed behaviour,
meticulously planning and executing complex tasks, which can be viewed as forms of internal optimisation.
Simultaneously, humans possess profound capacities for creativity, curiosity, and open-ended learning that
transcend predefined goals. We engage in scientific discovery, artistic expression, and constantly learn
and adapt to new situations without explicit "loss functions" or "reward signals" for every piece of knowledge
acquired or skill mastered. This intrinsic drive for exploration and novelty aligns strongly with the Discovery
Perspective. Human learning, particularly "concept learning," is deeply influenced by factors like "motivation
and context, and the necessity of multiple inheritance". These are complex, dynamic factors largely "not been
taken into account" in current mainstream machine learning models, which often rely on a simplified assumption
of a "label". This highlights a more holistic, emergent, and discovery-driven learning process in humans.

Current AI systems consistently struggle with aspects that are quintessential to human intelligence:

* *True Understanding/Common Sense:* AI processes data but "don't 'understand' in a way
  that humans do". Humans possess common sense, allowing robust reasoning even with incomplete
  information, a capability largely absent in AI.  

* *Contextual Nuance:* AI "struggles with understanding nuance or context". Human intelligence
  excels at interpreting subtle cues and implicit meanings.  

* *Genuine Creativity:* AI "lacks genuine creativity and cannot innovate outside the scope of
  its programming". Human creativity involves breaking existing paradigms and making leaps of
  intuition.  

* *Emotional Intelligence:* AI "lacks the ability to understand and respond to human emotions".
  Empathy and social awareness are hallmarks of human intelligence AI has yet to replicate.  

* *Motivation and Multiple Inheritance:* The dependency of human concept learning on "motivation
  and context, and the necessity of multiple inheritance" points to a level of internal drive
  and complex knowledge integration that current optimisation-driven AI, with its reliance on
  external labels and rewards, does not possess.

The persistent limitations of AI in these areas, which are quintessential to human intelligence,
point to the "missing link" in AI's pursuit of human-like intelligence: the integration of discovery.
The "Discovery Perspective," by focusing on open-ended exploration, novelty, and emergent capabilities,
offers a crucial theoretical and practical framework for addressing these "missing links." The
implication is that achieving AGI is not simply about scaling up existing optimisation techniques
with more data or compute, but fundamentally about incorporating mechanisms that foster these
"discovery-like" qualities, allowing AI to learn and adapt in a more holistic, human-like manner.

The observation that human concept learning depends on "motivation and context" reveals a profound
challenge for AI. In the optimisation paradigm, "motivation" is externalised and simplified into a
fixed reward signal or a loss function. Similarly, "context" is typically encoded as static features
within the training data. However, human motivation can be intrinsic, self-generated, evolving, and
not tied to a single, fixed external reward. Human contextual understanding is also dynamic, emergent,
and involves a deep, flexible model of the world, not just a static set of features. The challenge
for AI, therefore, is not merely to incorporate "discovery" algorithms, but to devise computational
frameworks that can internalise and dynamically generate "motivation" and "context" in a human-like,
autonomous way, moving beyond predefined, static objectives and external signals. This points to a
deeper, more philosophical and architectural challenge for AGI, requiring a shift from externally
imposed goals to internally generated drives. If the ultimate goal of AGI is to replicate or even
surpass human-level intelligence across a broad range of tasks and domains, it becomes imperative
to transcend the inherent limitations of pure optimisation. The ability to engage in open-ended
learning, generate truly novel solutions, adapt seamlessly to unforeseen and dynamic situations,
and demonstrate genuine understanding (all hallmarks of human intelligence) strongly suggests that
incorporating or prioritising discovery principles is not merely an option but a necessity for AGI.


### The Future of AI: Towards Open-Ended Intelligence and Beyond

Integrating discovery principles offers a promising path to address current AI limitations and move
towards more robust, adaptable, and genuinely intelligent systems.

By actively encouraging exploration of diverse behavioural spaces and novel solutions, AI can escape
the "local optima trap" inherent in direct optimisation, leading to more robust and globally optimal
solutions that are less brittle to changes in environment or task. By rewarding novelty and divergence
rather than just direct performance, AI systems could develop truly novel solutions, artistic expressions,
and scientific hypotheses that transcend mere recombination of existing data, moving beyond the "cannot
innovate outside the scope of its programming" limitation. Open-ended exploration can equip AI with a
broader repertoire of skills and knowledge, preparing it for unforeseen challenges and dynamic, unstructured
environments. This directly addresses AI's current struggle to "adapt to novel situations without explicit
programming". While not a direct solution, continuous, unsupervised, and curiosity-driven exploration
could lead to the development of more robust, flexible, and comprehensive internal models of the world,
potentially fostering a deeper, more human-like form of understanding and common sense.

Mainstream optimisation-driven AI excels at efficiently solving problems *that are already well-defined*
and come with clear objectives. However, a significant aspect of human intelligence, particularly in
scientific research, innovation, and strategic thinking, is the ability to *identify, formulate, and
prioritise new problems* or questions that lead to breakthroughs. If AI successfully integrates discovery
principles, it could transition from being primarily a tool for optimising solutions to existing problems
to actively exploring unknown domains, identifying novel challenges, and formulating new frontiers of
knowledge. This represents a profound shift in AI's potential role, transforming it from a mere
efficiency engine into a proactive partner in open-ended inquiry and intellectual exploration.

Future AI architectures are likely to be hybrid, where discovery mechanisms are used to generate diverse
hypotheses, novel architectural designs, or a wide array of potential solutions. These outputs could then
be fed into optimisation pipelines for refinement, efficiency, and performance tuning. This would involve
developing AI agents with intrinsic motivations for novelty, curiosity, or complexity, allowing them to
drive their own continuous learning and exploration without constant external rewards or predefined
objectives, moving beyond the limitations of fixed reward functions. Advanced AI systems might even
learn and evolve their own objective functions, dynamically adapting what they consider "important" or
"valuable" based on their ongoing interactions with the world, rather than being confined by static,
human-defined goals.

A core tenet of the "Discovery Perspective" is the idea that the most valuable outcomes often emerge as
*side effects* of open-ended search, not as direct optimisation targets. If future AI adopts this paradigm,
it implies that the most significant breakthroughs or beneficial capabilities might come from AI systems
that were not explicitly designed to achieve those specific outcomes. This raises profound questions about
control, interpretability (AI's black-box nature is a current limitation), and the ability to steer such
systems, as their most valuable contributions might be entirely unforeseen or even unintuitive to their
human creators. It also suggests a more organic, less deterministic, and potentially more surprising path
to advanced AI, where serendipity plays a greater role.

The emergence of increased autonomy and unpredictable creativity in AI raises new and complex ethical dilemmas,
particularly concerning accountability, control, and the potential for unintended consequences. Conversely,
the potential for AI to generate truly novel and impactful discoveries across scientific, artistic, and
technological domains is immense, promising accelerated progress in many fields. As AI becomes more open-ended
and less constrained by predefined objectives, the need for robust AI alignment mechanisms and ethical guidelines
becomes even more critical to ensure that its emergent behaviours align with human values and societal good.


### Conclusion: Synthesising the Paradigms for Advanced AI

Mainstream AI, fundamentally rooted in the Optimisation View, has achieved remarkable successes by minimising
loss functions and maximising rewards across various learning paradigms. However, this optimisation-centric
approach inherently limits AI's capacity for true understanding, genuine creativity, contextual nuance, and
open-ended exploration, and is subject to fundamental theoretical constraints. The "Discovery Perspective,"
championed by Kenneth Stanley's work, offers a crucial alternative by prioritising novelty, diversity, and
indirect search, suggesting a path to overcome these limitations. Human intelligence serves as a compelling
benchmark, seamlessly integrating both goal-directed optimisation for efficiency and open-ended discovery for
innovation and adaptability.

If current AI's significant limitations are deeply rooted in its optimisation-centric nature, and if human
intelligence demonstrably integrates both efficient optimisation and open-ended discovery, then achieving
Artificial General Intelligence (AGI) necessitates a broader, more nuanced definition of "intelligence." It
is not sufficient for AGI to merely solve problems efficiently (the strength of optimisation); it must also
be capable of formulating new problems, generating truly novel solutions, adapting to entirely unknown
environments, and exhibiting intrinsic curiosity (the essence of discovery). This implies that future AI
research needs to expand its conceptual framework and evaluation metrics beyond traditional performance
benchmarks to encompass qualities like adaptability, creativity, intrinsic motivation, and true understanding,
aligning with a more holistic view of intelligence.

The future of AI, particularly in the pursuit of Artificial General Intelligence (AGI), necessitates a
fundamental shift in research focus. It requires moving beyond a singular reliance on optimisation towards
a synergistic blend of optimisation for efficiency and discovery for innovation, adaptability, and genuine
intelligence. This evolution demands a re-evaluation of how we define "intelligence" and "progress" in AI.
It means expanding our metrics beyond purely performance-based scores to include measures of novelty, diversity,
adaptability, and the capacity for open-ended learning and problem-finding. While this report primarily
focuses on AI *approaching* human intelligence, the ultimate implication of synergistically blending
optimisations hyper-efficiency with discovery's open-endedness is the profound potential for AI to *surpass*
human intelligence in ways currently unimaginable. Humans are inherently limited by cognitive biases, finite
lifespans, and the relatively slow speed of biological thought. An AI system that can combine the unparalleled
speed and precision of optimisation with tireless, boundless exploration of novel solution spaces, potentially
across vast datasets and theoretical frameworks that no single human could ever process, could lead to scientific,
artistic, and technological breakthroughs far beyond current human capacity. This moves the discussion from
merely replicating human intelligence to potentially creating a new, qualitatively different, and more powerful
form of intelligence.

Ultimately, the journey towards advanced AI is not merely about scaling up existing algorithms with
more data or computational power (as some suggest might have diminishing returns), but about fundamentally
rethinking its core architectural principles and embracing the complementary strengths of both optimisation
and discovery paradigms.


### Reference

- Lehman, J., & Stanley, K. O. (2020). Novelty search and the problem with objectives. *Artificial Intelligence*, 281, 103234.
- Lehman, J., & Stanley, K. O. (2011, July). Abandoning objectives: Evolution through the search for novelty alone.
  In *Evolutionary Computation (CEC), 2011 IEEE Congress on* (pp. 2002-2009). IEEE.
- Stanley, K. O., & Lehman, J. (2015). *Why greatness cannot be planned: The myth of the objective.* Springer International Publishing.


