
*These notes are a translation from a 1992 artificial intelligence course taught by Sten Lindström (1945-2022)
at the Philosophical Institution, Uppsala University.
They represent my initial introduction to neural networks and what was then referred to as "connectionism."*

*The connectionist viewpoint, prominent in the 1980s, modeled computation after the brain's neural structure,
using interconnected nodes to process information in parallel, contrasting with rule-based symbolic AI.
While its core ideas, like distributed representations and learning through weight adjustments, remain
foundational to modern neural networks and deep learning, the term "connectionism" has faded.
It's been replaced by more specific terms like "deep learning" that reflect advanced architectures,
large-scale data, and computational power. Early connectionist models were simpler, constrained by
hardware, and often focused on biological plausibility and cognitive modelling, whereas today's AI
prioritises performance and practical applications, with less emphasis on mimicking the brain.
The term is less used now, as its principles have been absorbed into broader AI research, with modern
methods leveraging sophisticated optimisers and complex architectures far beyond the scope of early
connectionist systems.*

*It can however be beneficial to briefly look at the status of AI from a philosophical
standpoint at that time.*

*You might also notice the e.g. backprop is missing in this. "Learning Representations by Back-Propagating Errors"
(1986) co-authored by Hinton, David Rumelhart, and Ronald Williams in 1986 (published in Nature), was a
landmark publication. It provided a clear and practical method for training neural networks with multiple
hidden layers using backpropagation, which computes gradients efficiently via the chain rule of calculus.*

*Sometimes it takes time to establish ideas.*

---

# Philosophy and Artificial Intelligence, VI, by Sten Lindström. Spring 1992.

## Classical AI versus Connectionism

Within cognitive science and AI, consciousness and mental processes are viewed from an information-theoretic
perspective. Consciousness is thus primarily understood as a complex system that receives, stores, retrieves,
transforms, and transmits information. Cognitive functions of consciousness, such as perception, inference,
memory, language comprehension, and learning, are therefore at the center of interest.

We distinguish between two main directions in AI, which we call classical AI and connectionism, respectively.
The two directions have different understandings regarding the nature of thought. According to the classical
approach, thought is both representational and formal. That it is representational means that consciousness
constructs a model or mental representation of its environment. That it is formal means that consciousness is
thought to work like a computer: it manipulates symbols (mental representations) in accordance with precisely
specified formal rules. Mental representations are conceived as semantically interpreted sentences in a formalised
language: they have both a syntactic form and a semantic content. Each sentence can be seen as an ordered pair
$<\phi, l>$, where $\phi$ is a closed formula (a syntactic expression) and $l$ is a semantic interpretation of the
formalized language. The syntactic component $\phi$ makes it possible to manipulate representations mechanically
in accordance with formal rules: rules that refer only to their formal properties. The semantic component $l$ relates
the symbols in the formal language to objects, properties, and relations in the world. It is this component
that allows the sentences in the formal language to be used to represent the world.

Classical AI aims to construct computers that can represent their environment and reason about it using formal
logical rules. The strategy that classical AI follows to solve a cognitive task has been clearly stated by
David Marr. The first step is to provide an abstract description of the cognitive task to be solved. That is,
one defines the function to be calculated. The next step is to specify a detailed algorithm (a program) that
calculates the desired function. Finally, one shows how the algorithm can be implemented in a computer.

It is clear that this strategy presupposes that one works with well-defined problems and that one has a good
theoretical understanding of the problems one studies.

The connectionist approach is different. Here, one starts from theories about how the brain works. One attempts
to construct computers that resemble the brain as described by neurophysiologists; so-called neural networks composed
of relatively simple components ("neurons") that work in parallel. While classical AI primarily views intelligence
as symbolic thinking, connectionists emphasise learning and adaptive behaviour.

A connectionist model--also called a neural network--is a system consisting of:

- (i) A non-empty set $A$ of simple computational elements called units. Each unit $x$ at any given time $t$ is
  associated with a numerical value $a_x$, or $a_x(t)$, called the activation level at $t$. Units in a neural
  network can be of different types. For example, they can be binary logic units with activation levels of $1$
  (on) and $0$ (off). They can also take continuous values in the interval $[-1, 1]$.

- (ii) An output function that specifies how each unit's output is determined by its activation level.
  Usually, a unit's output is simply equal to its activation level, but it can also be, for example:
  ($output_x = a_x$)
    * (1) $output_x = a_x$ if $a_x > 0$; and $output_x = 0$ if $a_x \leq 0$.

- (iii) A binary relation R $\subseteq$ A x A that indicates how the system's units are connected to each other.
  We say that <x, y> is a link from $x$ to $y$ if and only if $<x, y> \in R$. Each link from one unit $x$ to another
  unit $y$ is associated with a numerical value $w_{xy}$, or $w_{xy}(t)$, called the link's weight. $W_{xy}$ is a
  measure of the strength of the connection from $x$ to $y$.

- (iv) If there is a link from $x$ to $y$, then $y$ receives an input from $x$ that is equal to $x$'s output multiplied
  by the strength $w_{xy}$ of the connection between $x$ and $y$, i.e.
    * (2) $input_{yx} = w_{xy} * output_x$

Thus, a unit $x$ with positive output has a positive effect on $y$ if $w_{xy}$ is positive, and a negative effect
if $w_{xy}$ is negative. We therefore say that the link $<x, y>$ is excitatory if $w_{xy} > 0$ and inhibitory
if $w_{xy} < 0$.

- (v) Each unit $x$ is associated with an activation function $f_x$ that determines how the unit's activation level
    is determined by inputs it receives from other units. A common activation function is the so-called linear
    activation function which determines the activation level of unit $x$ at $t + 1$ as the sum of all inputs
    to $x$ at $t$:
    * (3) $a_x(t + 1) = \sum_{y} input_{xy}(t) = \sum_{y} w_{yx} * output_y$

In a system with binary (0 and 1) instead of continuous activation values, units can be activated if and only
if their total input exceeds a certain threshold:
  * (4) $a_x(t+1)=1 \text{ if } \sum input_{xy}(t) > \theta; \text{ and } a_x(t+1)=0 \text{ otherwise.}$

There are also networks, such as the so-called Boltzmann machines, that use probabilistic rather than deterministic
activation functions. The activation function can, for example, specify the probability $P(a_x(t + 1) = 1)$ for a
binary unit $x$ to be activated at $t + 1$ as a function of the unit's total input at $t$.

- (vi) Some units $x_1,..., x_n$ in the network constitute its input layer, and some others $y_1,..., y_n$ its
  output layer. Units that belong to neither the input layer nor the output layer are called hidden units. The
  network can be given a certain input $<a(x_1),..., a(x_n)>$ by setting the activation levels a($x_i$) of the
  input vector units simultaneously, while the output layer units and the hidden units are set to "rest". The
  activity from the system's input then spreads through it until an equilibrium state may be reached; in which
  case the system produces an output vector $<a(y_1),..., a(y_m)>$ . We can thus speak of the function that
  the network calculates.[^func] If equilibrium is not reached after a given input, then the function that the system
  calculates is undefined for that input.

The function that a given system calculates is naturally dependent on the system's weights. A network capable of
modifying its weights can thus be said to calculate a certain function only relative to a given set of weights.

- (vii) Many neural networks can learn--i.e., modify their input/output behaviour--by changing the weights associated
  with the incoming links. These weights are thus thought to represent the system's knowledge. An elegant learning
  rule is the one proposed by D. O. Hebb (1949). Hebb's idea was that the connection between two neurons is
  strengthened whenever they are activated similarly and simultaneously. A mathematical expression for this idea
  is the following so-called Hebbian rule:
    * (~4~5) $w_{xy}(t+1) = w_{xy}(t) + l \cdot a_x(t) \cdot a_y(t).$

where $l$ is a positive constant indicating the learning rate. Whenever the activation levels of the two units have
the same sign (positive or negative), the connection between them is strengthened in proportion to the product of
their activation levels.

A more powerful learning rule is the so-called delta rule. This rule is based on the idea that a network can be
"trained" by letting the network compare the output it actually produces for a given input with a desired output
and letting the system modify its weights in light of this comparison. The network first receives a
certain input. Then it produces an output pattern using the existing weights in the system.

The delta rule works as follows: first, one provides an input to the system's input discrepancy $d_x - a_x$
between the unit's intended output $d_x$ and its actual output $a_x$. The total error of the output pattern is
calculated as:

```math
Error = \frac{1}{2} \sum (d_x - a_x)^2
```

The idea behind the delta rule is to modify the weights in such a way that Error approaches 0 with repeated training.
The delta rule achieves this by modifying the weight $w_{yx}$ for each link $<y, x>$ leading to an output unit $x$
by the quantity:

```math
\Delta w_{yx} = learning\_rate(d_x - a_x)a_y,
```
i.e., we set the new weights to
```math
w'_{yx} = w_{yx}(t) + \Delta w_{yx}.
```
Given that the system uses the linear activation rule, i.e.
```math
a_x = \sum_y w_{yx} \cdot a_y
```
then $a_x$ after the weights have been modified is given by:
```math
a'_x = \sum_y (w_{yx} + \Delta w_{yx}) \cdot a_y = \sum_y w_{yx} \cdot a_y + \sum_y \Delta w_{yx} \cdot a_y = a_x + \sum_y \Delta w_{yx} \cdot a_y.
```
First, a specific input is given to the system, whereupon the output produced by the system is compared with a desired
output, and the result of the comparison is used by the system itself to modify its weights.

Naturally, one can also "program" a network by modifying the weights of the incoming links. The weights thus correspond
to some extent to the program in a conventional computer.

Connectionist systems that have the ability to learn can be said to be self-organising. The network is "trained" by
receiving a certain input and having the output it produces compared with a desired output. The result of the comparison
is given in the form of an error signal. This is sent back through the network, and then the network is trained again.
The process continues until the network has been distributed in such a way that the desired input-output pattern
has been achieved.


[^func]: I assume here that the network in question is a deterministic system. There are also non-deterministic networks
(e.g., probabilistic ones) whose output for a given input is not uniquely determined. For such networks, one naturally
cannot speak of the function that the network calculates.

