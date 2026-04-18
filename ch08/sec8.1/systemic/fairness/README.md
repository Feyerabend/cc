
## Fairness

*This entry is an open exploration. A starting framework is provided below, but you are
expected to investigate, extend, and form your own understanding.*

Fairness in computing asks: when multiple parties share a resource or interact with a system,
are they treated equitably? It is a concept with multiple distinct meanings depending on context,
and the tension between them is itself one of the most interesting aspects of the subject.

Fairness is not the same as equality--giving everyone exactly the same--nor is it the same as
optimality--getting the most out of a resource. It is a constraint on how the resource is
distributed, based on some principle of what distribution is just. Different principles lead
to very different systems.


### Starting Points for Exploration

*CPU scheduling fairness:*

An operating system must decide which of many competing processes gets the CPU at each moment.
A naive policy that always runs the highest-priority process starves lower-priority ones. A
round-robin policy gives every process equal time regardless of what they need. The Linux
Completely Fair Scheduler (CFS) attempts to give every process CPU time proportional to its
weight, tracking "virtual runtime" to ensure no process falls too far behind. What does
"fair" mean here? Is equal time fair? Is proportional time fair?

*Network fairness:*

When multiple TCP connections share a bottleneck link, TCP congestion control should, in theory,
allocate bandwidth fairly. Jain's fairness index is a measure: given n flows with allocations x1...xn,
it ranges from 1/n (completely unfair, one flow gets everything) to 1 (perfectly fair, all flows
get equal share). Is equal bandwidth allocation the right fairness criterion? What if one flow is
a video call and another is a background backup?

*Algorithmic fairness:*

When a machine learning model makes decisions that affect people--loan approvals, hiring screens,
bail recommendations--fairness becomes a question of whether different demographic groups are
treated consistently. But "fairness" has multiple incompatible mathematical definitions:
- *Demographic parity:* equal positive decision rates across groups.
- *Equalised odds:* equal true positive and false positive rates across groups.
- *Individual fairness:* similar individuals are treated similarly.
It has been proven mathematically that these definitions cannot all be satisfied simultaneously
when group base rates differ. How do you choose?

*Resource allocation and starvation:*

Any priority-based system risks starvation: low-priority tasks may never receive resources if
high-priority ones are always present. Ageing is a common remedy: the longer a task has waited,
the higher its priority grows. This guarantees eventual service but at the cost of priority
purity. What is the right balance?

*Fairness vs. efficiency:*

Maximum efficiency often means allocating resources to whoever can use them most productively,
which tends to advantage those who already have more. Fairness may require sacrificing some
efficiency to ensure equitable distribution. In network design, max-min fairness (maximise the
minimum allocation across all flows) explicitly trades global throughput for fairness. When is
that trade-off worth making?


### Questions to Answer

1. What does "fairness" mean in a CPU scheduler? Is there one correct definition?
2. Find the mathematical definition of Jain's fairness index and compute it for a few example allocations.
3. What is the difference between procedural fairness (fair process) and outcome fairness
   (fair result)? Can you have one without the other?
4. In machine learning: find one real-world case where an algorithmic decision system was
   found to be unfair. What was the unfairness? How was it detected? How was it addressed?
5. Is fairness a technical property or a social one? Who should define what "fair" means in
   a given system?
6. Can fairness and optimality coexist? Under what conditions?

Write your answers. Some of these have no single correct answer. The goal is to reason
carefully and be able to defend a position.
