
## Optimisation

Optimisation, in its broadest sense, is the pursuit of the best possible outcome given a
set of constraints. While often framed in mathematical and computational terms, the concept
has deep philosophical roots, touching on ideas of efficiency, trade-offs, and even human
decision-making.

At its core, optimisation reflects a fundamental tension between perfection and practicality.
In philosophy, this relates to the *ideal* vs. *the real*--we may strive for the best, but
constraints (whether physical, logical, or ethical) often force us to settle for something
less than perfect. This mirrors the idea in engineering and science that optimisation is
rarely about finding a single, absolute best solution but rather the best possible one given
limited resources.

Another philosophical aspect of optimisation is goal-setting and values. What does it mean
to "optimise" something? The answer depends entirely on what we consider valuable. In economics,
it might mean maximising wealth; in ethics, it could mean maximising happiness (utilitarianism);
in AI, it might mean optimising for accuracy, fairness, or interpretability. This subjectivity
means that optimisation is always tied to deeper philosophical questions about what we should
strive for.

Furthermore, optimisation involves trade-offs-the recognition that improving one aspect of a
system often comes at the cost of another. This resonates with ethical dilemmas, such as the
trolley problem, where choosing the optimal outcome involves weighing different kinds of harm.
In economics and environmental science, this appears in the form of Pareto efficiency, where
an optimal state is reached when no further improvements can be made without making something
else worse.

Finally, there is a teleological perspective: the idea that all systems, whether biological,
social, or artificial, evolve toward some form of optimisation. Evolution itself is often
analogised as an optimisation process. refining species over time through natural selection.
In human systems, markets, technologies, and even moral frameworks evolve through a similar
process, constantly seeking better solutions to emerging challenges. 

Ultimately, optimisation is not just a mathematical tool-it is a way of thinking about problems,
balancing competing priorities, and navigating the complexities of life itself. It asks us to
confront limits, define what we value, and acknowledge that "the best" is often a moving target,
shaped by context and perspective.



## Optimisation in Practice

Optimisation is a fundamental principle in many scientific and engineering disciplines,
aiming to find the best possible outcome under given constraints. At its core, optimisation
involves either maximisation (e.g., profit, utility, reward) or minimisation (e.g., cost,
loss, risk). Despite differences in formulation, the underlying mathematical and computational
techniques often share common ground across fields.

From control systems to economics, artificial intelligence, and statistical learning,
optimisation serves as a unifying framework for decision-making. Each field adapts the
concept based on its unique goals, constraints, and methodologies.


### Applications Across Domains


__1. Control Systems: Precision and Stability__

Control theory is widely used in robotics, aerospace, and industrial automation, where
minimising a cost function ensures system stability and efficiency. Examples include:
- Self-driving cars adjusting speed and steering to minimise deviation from an optimal trajectory.
- Flight control systems optimising thrust and aerodynamic forces to maintain stability.
- Energy grids minimising power loss while ensuring demand is met efficiently.

These systems often rely on techniques like PID controllers, Kalman filters, and model predictive
control (MPC) to optimise real-time decision-making.

- Mathematical Perspective: A common formulation is in optimal control theory, where
  we define a function $\`J(x, u)\`$ (cost function), and we seek to minimise:
```math
  J = \int_0^T L(x(t), u(t)) dt + \Phi(x(T))
```
  where $\`x(t)\`$ is the system state, $\`u(t)\`$ is the control input, $\`L(x,u)\`$ 
  is the running cost, and $\`\Phi(x(T))\`$ is the terminal cost.


__2. Economics: Decision-Making at Scale__

Optimisation plays a crucial role in individual, corporate, and societal decision-making.
- Consumers maximise utility when choosing goods under budget constraints.
- Firms optimise production levels to maximise profits while managing costs.
- Governments design policies to optimise economic welfare, balancing equity and efficiency.

Methods like game theory, linear programming, and behavioural economics models help solve
complex economic optimisation problems.

Organizations (firms) maximise profit, defined as revenue minus costs.
Example: A firm seeks to maximise its profit function:
```math
\max_{\text{price}, \text{output}} \quad \pi = \text{Revenue} - \text{Cost}
```
where revenue depends on price and quantity, and cost depends on production.

- Mathematical Perspective: In game theory and microeconomics, utility functions measure
preference over outcomes. A social welfare function aggregates individual utilities:
```math
W(U_1, U_2, …, U_n)
```
where $\`U_i\`$ is the utility of individual $\`i\`$, and different formulations (e.g., Pareto
efficiency, Rawlsian max-min fairness[^rawls]) lead to different solutions.

[^rawls]: John Rawls' A Theory of Justice (1971).


__3. Artificial Intelligence: Learning and Adaptation__

Many AI techniques revolve around maximising rewards or minimising loss.
- Reinforcement Learning (RL): Used in robotics, game AI (e.g., AlphaGo), and autonomous
  systems where agents learn optimal strategies by maximising cumulative rewards.
- Neural Network Training: Deep learning models minimise loss functions to improve accuracy,
  using gradient-based optimisation methods like SGD (stochastic gradient descent).
- Search and Planning: AI algorithms optimise search paths in applications such as route
  planning (Google Maps), supply chain logistics, and recommendation systems.

Example: In reinforcement learning (RL), an agent interacts with an environment and selects
actions to maximise future expected rewards.
- Mathematical Perspective: The optimisation problem in RL is formulated using the Bellman
equation:
```math
V(s) = \max_a \sum_{s{\prime}} P(s' \mid s, a) \left[ R(s, a) + \gamma V(s{\prime}) \right]
```
where $\`V(s)\`$ is the value function, $\`P(s{\prime} | s, a)\`$ is the transition
probability, $\`R(s, a)\`$
is the reward, and $\`\gamma\`$ is a discount factor.



__4. Statistical Learning and Decision Theory__

Statistical methods focus on minimising the expected error to improve predictions and decisions
under uncertainty.
- Machine Learning: Supervised models optimise loss functions (e.g., cross-entropy for
  classification, MSE for regression).
- Bayesian Decision Theory: Optimises decision-making under probabilistic uncertainty, crucial in
  medical diagnosis, financial risk analysis, and automated trading.
- Experimental Design: Ensures efficient data collection in fields like drug development and
  industrial process optimisation.

- Example: In supervised learning, given input x and true output y, a model produces a prediction
  $\`f(x)\`$. A loss function $\`L(y, f(x))\`$ measures the error, and the goal is to minimise
  the expected loss:
```math
\min_f \mathbb{E}_{(x,y) \sim P} [ L(y, f(x)) ]
```
- Common Loss Functions:
- Mean Squared Error (MSE) for regression:
```math
L(y, f(x)) = (y - f(x))^2
```
- Cross-entropy loss for classification:
```math
L(y, f(x)) = - \sum y_i \log f(x_i)
```


### Complementary Areas and Broader Perspectives

Optimisation interacts with various fields that extend its principles:
- Operations Research (OR): Focuses on large-scale decision-making, including supply chain management,
  logistics, and manufacturing optimisation.
- Information Theory: Optimises data compression and transmission, crucial in networking, cryptography,
  and communications.
- Computational Complexity: Studies the efficiency of optimisation algorithms, influencing areas like
  the P vs. NP problem and algorithmic game theory.
- Systems Biology: Uses optimisation to model biological networks, enzyme pathways, and genetic evolution.

Across all these domains, convex optimisation, dynamic programming, evolutionary algorithms, and Monte Carlo
methods provide powerful tools to tackle real-world optimisation challenges.



### Common Theme: Optimisation Across Domains

The core idea across all these fields is optimisation, but different domains frame it as
maximisation or minimisation:

| Field               | Objective                          | Function Type          |
|---------------------|------------------------------------|------------------------|
| Control Systems     | Minimise cost function             | $\`J(x, u)\`$          |
| Economics           | Maximise utility/profit/welfare    | $\`U(x), \pi(x)\`$     |
| Research (AI)       | Maximise expected rewards          | $\`V(s)\`$ (Bellman)   |
| Statistics/ML	      | Minimise expected loss             | $\`\mathbb{E}[L(y, f(x))]\`$ |

- Duality: Many problems can be framed in both ways. For example, maximising rewards is equivalent
  to minimising negative rewards.
- Connections: Economic models influence machine learning (e.g., multi-agent reinforcement learning).
  Statistical learning theory underpins AI algorithms.


### Projects

1. *The Trade-Off Simulator*: Develop a simple interactive program that demonstrates the trade-offs
   in optimisation problems. For example, a web-based tool where users adjust parameters (e.g.,
   speed vs. energy consumption in a self-driving car) and see how optimising for one affects the others.

2. *Resource-Constrained AI Training*: Implement a simple neural network that can only be trained
   with limited computational resources (e.g., a fixed number of floating-point operations).
   Investigate how different optimisation techniques (gradient clipping, learning rate scheduling,
   weight quantisation) affect the final model performance.

3. *Evolutionary Algorithm for Problem-Solving*: Write a genetic algorithm that optimises a complex
   function (e.g., traveling salesman problem, game AI, or image compression). Reflect on how evolutionary
   principles like mutation and selection contribute to optimisation.

4. *Ethical Optimisation in AI*: Build a decision-making AI (e.g., a reinforcement learning agent)
   and implement different reward structures. Compare the outcomes when optimising for different
   values (e.g., individual gain vs. collective welfare). How does the chosen objective shape the
   behaviour of the AI?

5. *Real-Time Control System*: Implement a PID controller in a small robotic simulation or an interactive
   program. Optimise for stability and response time, and analyse how tuning the parameters affects
   the outcome.

6. *Game Theory and Competitive Optimisation*: Simulate an economic system with multiple agents trying
   to maximise their own rewards while competing for shared resources. Explore the Nash equilibrium
   and Pareto efficiency in different scenarios.

7. *Energy-Efficient Computing*: Optimise a computational task (e.g., matrix multiplication, sorting)
   to reduce energy consumption. Compare different algorithms and hardware-level optimisations
   (e.g., parallel processing, lower precision computation).

8. *Multi-Objective Optimisation*: Implement an optimisation algorithm that must balance multiple
   competing objectives (e.g., a web server that must optimise both speed and security, or a route
   planner that minimises both time and fuel consumption).

9. *AI Fairness and Bias in Optimisation*: Train an AI model with different fairness constraints
   (e.g., balancing accuracy across different groups). Explore how optimising for fairness can
   conflict with optimising for accuracy.

10. *Compression and Information Theory*: Implement a simple data compression algorithm and analyse
    the trade-off between compression ratio and loss of information. Compare entropy-based methods
    with lossy and lossless techniques.

11. *Dynamic Programming Challenge*: Solve a classic dynamic programming problem (e.g.,
    knapsack problem, shortest path) and analyse the time-space trade-off of memoization.

12. *Optimisation in Programming Languages*: Write a simple compiler optimisation pass that transforms
    inefficient code into a more optimised form (e.g., constant folding, loop unrolling).

13. *Interactive Visualisation of Optimisation Algorithms*: Create a visualisation tool that shows how
    different optimisation techniques (gradient descent, simulated annealing, genetic algorithms)
    solve the same problem in different ways.

14. *Reinforcement Learning in Games*: Implement a basic AI that learns to play a simple game (e.g.,
    tic-tac-toe, a small grid-world environment) using Q-learning or deep reinforcement learning.
    Experiment with different reward structures.

15. *Constraint Satisfaction Problems*: Implement a constraint solver for a problem like Sudoku or
    scheduling, exploring how different heuristics improve performance.



### Critique of Optimisation

Optimisation is often framed as an unquestioned good--an essential tool for progress, efficiency,
and success. However, the pursuit of optimisation, especially when taken to extremes, can lead to
unintended negative consequences. In both theory and practice, optimisation is not always neutral;
it embodies values, priorities, and trade-offs that shape outcomes in ways that may not always be
desirable.


### General Criticism of Optimisation as a Universal Goal

__1.	Optimisation as Reductionism__

Many optimisation problems involve simplifying complex, multi-dimensional realities into quantifiable
metrics. This reductionist approach can lead to distortions, where important aspects of a system
(such as ethical concerns, fairness, or long-term consequences) are either ignored or misrepresented.
For example, economic models optimising for GDP growth often fail to account for environmental degradation,
wealth inequality, or social well-being.


__2.	The Problem of Overfitting to Metrics__

In machine learning, overfitting refers to a model that performs well on training data but fails in
the real world. In broader systems, when a single metric is over-optimised, it can lead to perverse
incentives. Goodhart's Law captures this idea:
"When a measure becomes a target, it ceases to be a good measure."[^good]
- Example: Social media algorithms are optimised for engagement, which maximises time spent on platforms,
  but this often leads to the spread of sensationalist or divisive content.

[^good]: In other words, once a specific metric is optimised for, especially in systems involving
human behaviour, it often gets manipulated in ways that undermine its original purpose. This phenomenon
is common in economics, artificial intelligence, and organisational management. For example, if a
school optimises for higher standardised test scores, teachers may "teach to the test" rather than
fostering deeper learning. In AI, optimising for engagement in social media algorithms can lead to
clickbait and misinformation. The core issue is that a chosen metric is always an imperfect proxy
for a broader goal, and when it is treated as the objective itself, unintended distortions arise.
This makes Goodhart's Law a crucial cautionary principle in optimisation--highlighting that blindly
chasing a metric can degrade the very system it was meant to improve.


__3.	Trade-Off Blindness__

Optimisation always involves trade-offs, but when optimisation becomes an unquestioned goal, it often
ignores broader social, ethical, or environmental consequences.
- Example: Über optimises for rider demand and driver efficiency, but in some cities, this has led to
  worsening traffic congestion.


__4.	Short-Termism vs. Long-Term Stability__

Optimisation often emphasises immediate gains over long-term resilience. The financial sector’s emphasis
on optimising short-term profits contributed to the 2008 financial crisis, as financial products were
designed for immediate returns rather than systemic stability.



### Specific Criticism of Optimisation in Different Fields

__1. Technology and AI: Optimisation for Engagement and Its Social Consequences__

Social media platforms optimise for engagement--measured by clicks, likes, and time spent on the platform.
While this is beneficial for business models based on advertising revenue, it has significant social costs:
- The spread of misinformation and conspiracy theories, as false or emotionally charged content often
  outperforms factual reporting.
- Increased political polarisation, as algorithms favour content that reinforces existing beliefs.
- The mental health impact of social media addiction, particularly among young people.

References:
- Zuboff, Shoshana. *The Age of Surveillance Capitalism* (2019) - Critiques how big tech companies optimise
  user behaviour for profit.
- Tufekci, Zeynep. *Twitter and Tear Gas* (2017) - Analyses how social media optimisation affects political
  movements and misinformation.
- Noble, Safiya Umoja. *Algorithms of Oppression* (2018) - Explores how optimisation in search engines
  leads to racial and gender biases.


__2. Economics: The Tyranny of Profit Optimisation__

Capitalism heavily relies on optimising for profit, often without sufficient checks on externalities
such as environmental damage, labor exploitation, or economic inequality.
- The gig economy optimises labor costs for companies like Über and DoorDash, but at the expense
  of job stability and worker protections.
- Supply chain optimisation maximises efficiency but makes global systems fragile (e.g.,
  semiconductor shortages during the covid-19 pandemic).
- Amazon's warehouse logistics optimise for speed but create gruelling conditions for workers.

References:
- Piketty, Thomas. *Capital in the Twenty-First Century* (2013) - Analyses how economic optimisation
  for capital accumulation leads to inequality.
- Klein, Naomi. *This Changes Everything* (2014) - Critiques how economic optimisation ignores
  climate consequences.



__3. Environmental Consequences of Over-Optimisation__

Many environmental issues arise from optimising for short-term economic or technological gains
rather than long-term sustainability.
- Industrial agriculture optimises for yield, leading to monoculture farming, soil depletion, and biodiversity loss.
- Fossil fuel optimisation maximised energy efficiency for decades but accelerated climate change.
- Overfishing optimises short-term profit but leads to ecosystem collapse.

References:
- Meadows, Donella et al. *The Limits to Growth* (1972) - A classic critique of optimisation-driven resource depletion.
- Raworth, Kate. *Doughnut Economics* (2017) - Proposes balancing optimisation with sustainability.



### What's the Alternative?

Rather than blindly pursuing optimisation, we should consider meta-optimisation: optimising what
we optimise for. Some alternative frameworks include:

- *Satisficing* (Simon, 1956) - Instead of always optimising for the absolute best, consider solutions
  that are "good enough" and balance multiple needs.[^simon]

[^simon]: Herbert A. Simon introduced the concept of satisficing in his 1956 paper "Rational Choice and the Structure of the Environment", published in *Psychological Review* (Vol. 63, No. 2, pp. 129-138). Also, Simon, H.A. (1967[1957]). *Models of man: social and rational : mathematical essays on rational human behavior in a social setting.* (5 pr.) London.

- *Resilience Thinking* (Holling, 1973) - Instead of maximising efficiency, design systems that can adapt
  to changing conditions.[^holling]

[^holling]: Holling, C. S. (1973). "Resilience and Stability of Ecological Systems." *Annual Review of Ecology and Systematics*, 4(1), 1-23.

- A close alternative to resilience is Nassim Nicholas Taleb arguing that excessive optimisation makes
  systems fragile by removing necessary redundancies and buffers, leaving them vulnerable to unpredictable
  shocks. In *The Black Swan* and *Antifragile*, he criticises the pursuit of efficiency in finance,
  technology, and policymaking, warning that it often ignores randomness and leads to catastrophic failures.
  Instead of optimising for a narrow definition of "best," he advocates for antifragility—building systems
  that thrive on uncertainty and disorder, much like biological evolution or decentralised markets.
  In his view, true resilience comes not from rigid optimisation but from adaptability and robustness
  in the face of uncertainty.

- Ethical AI & Value-Sensitive Design - Instead of purely optimising for performance, incorporate
  ethical constraints into optimisation goals.



### Conclusion

Optimisation is a powerful tool, but it is not inherently good or neutral. It encodes priorities and
trade-offs that can lead to systemic failures if taken too far or applied blindly. The key is to ask:
What are we optimising for, and at what cost?


### Projects

Here are some project ideas that encourage you to explore the limits of optimisation—both its benefits
and its unintended consequences. These projects are all related to computing, programming, and system
design, and they challenge students to think critically about optimisation in different contexts.


__1. Social Media Algorithm and Engagement Optimisations__

*Build a simplified social media feed algorithm that prioritises engagement. Then analyse the unintended consequences.*

Steps:
- Create a dataset of posts with different engagement metrics (likes, comments, shares).
- Implement an algorithm that optimises for engagement.
- Simulate a user browsing the feed and measure how engagement increases.
- Modify the algorithm to optimise for other metrics (e.g., factual accuracy) and compare trade-offs.

Critical Discussion:
- Does the algorithm push more extreme content?
- How does prioritising engagement affect misinformation?
- What happens if you optimise for diversity of viewpoints instead?



__2. AI Ethics: Bias in Optimisation__

*Train a machine learning model on biased data and examine how optimisation reinforces discrimination.*

Steps:
- Use a dataset (e.g., a hiring dataset) and train a classifier to predict success based on attributes
  like education, experience, and demographics.
- Measure accuracy and optimise for it.
- Then analyse whether certain groups (e.g., gender, race) are disproportionately filtered out.
- Implement fairness constraints and compare the trade-offs.

Critical Discussion:
- How does optimising for accuracy lead to bias?
- What does it mean to optimise for fairness?
- What are the trade-offs between fairness and performance?

> [!NOTE]  
> Use synthetic datasets to avoid privacy concerns.



__3. Economic Optimisation vs. Worker Well-Being (Gig Economy Simulation)__

*Simulate a gig economy platform like Über and examine how optimising for profit affects workers.*

Steps:
- Create a simulation where drivers sign up, receive ride requests, and earn money.
- Optimise for platform profit (e.g., lower driver pay, increase ride costs).
- Track worker earnings, job satisfaction, and company revenue.
- Modify the system to optimise for worker well-being instead and analyse trade-offs.

Critical Discussion:
- Does optimising for profit create precarious working conditions?
- How can platforms balance fairness with economic efficiency?



__4. Environmental Trade-Offs in Supply Chain Optimisations__

*Model a supply chain that minimises costs and maximises profit, then introduce sustainability constraints.*

Steps:
- Simulate a company that sources raw materials, manufactures products, and distributes them.
- Optimise for cost reduction (cheaper suppliers, faster delivery, minimal storage costs).
- Introduce carbon footprint tracking and require emission reductions.
- Compare the profit vs. sustainability trade-offs.

Critical Discussion:
- How does cost-cutting optimisation lead to environmental damage?
- Can sustainability be optimised without sacrificing profit?



__5. Resilience vs. Efficiency in System Design__

*Build a system (network, power grid, database, etc.) and compare an optimised version vs. a resilient one.*

Steps:
- Create a network where messages must be delivered between nodes.
- Optimise for speed and minimal redundancy.
- Introduce failures (server crashes, network congestion).
- Compare performance between the optimised and resilient versions.

Critical Discussion:
- Can we express "resiliant systems" in different ways, in relation to programming?
- How does optimisation make systems fragile?
- What are real-world examples of systems collapsing due to over-optimisation?



__6. Over-Optimisation in Machine Learning (Overfitting Experiment)__

*Train a model that is overly optimised for training accuracy and see how it fails in real-world cases.*

Steps:
- Train a neural network on a small dataset and measure accuracy.
- Keep optimising the model until it overfits (high training accuracy, low test accuracy).
- Introduce noise or slightly modify test data and observe how performance drops.
- Implement regularisation techniques and measure trade-offs.

Critical Discussion:
- Why does too much optimisation make models worse?
- What are real-world examples of overfitting in AI applications?



__7. Ethics of Autonomous Decision-Making (Trolley Problem for AI)__

*Create an AI system that must make ethical trade-offs in an optimisation problem.*

Steps:
- Simulate a self-driving car that must optimise for safety, speed, and energy efficiency.
- Introduce scenarios where the car must decide (e.g., hitting an obstacle vs. swerving into pedestrians).
- Implement different optimisation strategies and analyse how decisions change.

Critical Discussion:
- Should AI optimise for human life at all costs?
- How do ethical constraints change optimisation strategies?

