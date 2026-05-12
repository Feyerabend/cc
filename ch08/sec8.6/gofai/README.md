
## GOFAI: Good Old-Fashioned Artificial Intelligence

Good Old-Fashioned Artificial Intelligence (GOFAI)--the term coined by philosopher John
Haugeland in 1985--names the dominant paradigm in AI research from the mid-1950s through
roughly the early 1990s. Its central commitment is that *intelligence can be achieved by
manipulating symbolic representations according to explicit formal rules*. Knowledge is
encoded as symbols; reasoning is the mechanical transformation of those symbols; and the
result, if the rules are right, is intelligent behaviour.

This collection of folders examines GOFAI from several angles--technical, historical,
philosophical, and critical. None of them tells the whole story on its own; the full picture
emerges from reading them together.


### The Symbolic Paradigm

The unifying assumption of GOFAI is what Allen Newell and Herbert Simon called the *Physical
Symbol Systems Hypothesis* (1976): a physical symbol system has the necessary and sufficient
means for general intelligent action. Intelligence, on this view, is substrate-independent.
It does not matter whether the symbols are encoded in neurons, vacuum tubes, or silicon; what
matters is their formal structure and the operations defined over them.

This led to a distinctive architecture. A GOFAI system has two separable components: a
*knowledge base* (the encoded facts and rules) and an *inference engine* (the procedure that
applies the rules). The knowledge base can in principle be inspected, corrected, and extended
by a domain expert. Every conclusion has a traceable justification. This *transparency* is
GOFAI's most enduring advantage--and it remains relevant wherever accountability matters more
than raw performance.

The corresponding limitation is equally fundamental. All intelligence in a GOFAI system must
be placed there by a human programmer or knowledge engineer. Nothing is learned from data.
This *knowledge acquisition bottleneck* proved, in practice, to be the paradigm's ceiling:
building and maintaining a knowledge base for any realistic domain is laborious, brittle, and
never quite finished. It was a primary driver of the AI winters, and of the eventual shift
toward data-driven methods.


### The Connectionist Alternative

Running alongside GOFAI throughout its history was a different approach: *connectionism*, or
neural networks. Where symbolic AI encodes knowledge as rules, connectionism encodes nothing
explicitly--intelligence emerges from the pattern of weights learned from experience. Where
symbolic AI reasons by inference steps that can be read and checked, a neural network produces
outputs through distributed activation across a weighted graph: no readable rule, no traceable
step.

The contrast is not merely technical. It reflects a disagreement about what intelligence *is*
and where it comes from. Symbolic AI is top-down: intelligence is imposed through design.
Connectionism is bottom-up: intelligence grows through exposure to data. Both approaches faced
serious challenges in the 1970s and 1980s. Both survived, and their eventual convergence in
modern hybrid systems is one of the more consequential developments in contemporary AI.


### The Folders

Each subfolder approaches this history from a distinct angle. They are designed to be read
alongside each other, not in isolation.

*[`classic/`](./classic/)* -- the symbolic paradigm in code. Forward and backward chaining
expert systems, state space search (BFS, DFS, A*), constraint satisfaction (map colouring,
n-queens), and STRIPS planning on the blocks world. This is GOFAI at its most direct: rules
are written by hand, inference is explicit, every step is traceable. The knowledge acquisition
bottleneck is not hypothetical here--it is visible in every line of the knowledge base.

*[`xor/`](./xor/)* -- the mathematical crisis that stalled connectionism. In 1969, Minsky
and Papert published *Perceptrons*, proving that a single-layer network cannot compute any
function that is not linearly separable--and XOR is the simplest such function. This was not
polemic; it was a theorem. The proof contributed to a decade of reduced interest in neural
networks and reinforced symbolic AI's dominance through the 1970s. The folder explains the
mathematics and its consequences, and connects forward to the backpropagation revival.

*[`nn/`](./nn/)* -- neural networks in code and visualisation. Two foundational learning rules
are demonstrated: Hebbian learning (biologically motivated, unsupervised, the oldest formal
learning rule) and the Delta rule (supervised, error-correcting, the direct precursor to
backpropagation). The HTML file provides an interactive backpropagation demo. Taken together,
these files trace the algorithmic line from the first perceptron learning rule (1957) to the
method that revived the field in 1986.

*[`lindstrom/`](./lindstrom/)* -- a philosophical account of both approaches as they appeared
in 1992. These are translated lecture notes from Sten Lindström's course *Philosophy and
Artificial Intelligence* at Uppsala University. Lindström presents the formal structure of
connectionist models alongside the symbolic alternative and asks what each says about the
nature of mind and cognition. Reading them now, they capture a moment of genuine uncertainty:
neither paradigm had won, and the philosophical questions were still live. The backpropagation
file shows how the second-generation connectionist models looked from the same vantage point.

*[`nonmonotonic/`](./nonmonotonic/)* -- a different crack in the symbolic edifice. Non-monotonic
reasoning was the 1980s attempt to fix symbolic AI from *within*--not by abandoning logic, but
by extending it to handle defaults, exceptions, and retractable conclusions. Classical logic is
monotonic: adding new premises never removes conclusions. Human reasoning is not. The folder
examines the formal systems that tried to bridge this gap (default logic, circumscription,
autoepistemic logic) and asks why they fell short in practice. This is GOFAI self-correcting,
and the correction reveals structural limits.

*[`seasons/`](./seasons/)* -- the arc of AI history. Two winters, several springs, the
institutional pressures that shaped each turn. The account is partly personal: the author was
present at the Second International Conference on Logic Programming in Uppsala in 1984, at the
height of the second spring, and watched the expectations of that moment collide with reality
over the following decade. The section on Stig Kanger--logician, dissertation supervisor,
and quietly prescient figure--connects the international AI story to the Swedish scientific
tradition that ran alongside it.


### Reading the Collection

The folders form a loose argument. `classic/` shows what GOFAI could do. `xor/` and
`nonmonotonic/` show two different places where it ran into limits. `nn/` and `lindstrom/`
show the alternative that was developing in parallel. `seasons/` gives the historical frame
in which all of this happened.

The deeper question that runs through all of them--raised explicitly in `lindstrom/` and
`seasons/`, implicit in the others--is whether the limits of GOFAI are *contingent* (failures
of scale or implementation, in principle fixable) or *structural* (reflecting something about
the nature of intelligence that formal symbol manipulation cannot capture). Dreyfus and Searle
pressed the structural reading from the outside; the AI winters pressed it from the inside.
That question has not been definitively answered, and the current moment--large language
models, hybrid neuro-symbolic systems, renewed interest in reasoning and explainability--
can be read as yet another chapter in the same debate.
