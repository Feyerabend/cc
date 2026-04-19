
## Optimisation

Optimisation, in its broadest sense, is the pursuit of the best possible outcome given a set of
constraints. While often framed in mathematical and computational terms, the concept has deep
philosophical roots, touching on ideas of efficiency, trade-offs, and human decision-making.

At its core, optimisation reflects a fundamental tension between perfection and practicality. In
philosophy, this relates to the *ideal* vs. *the real*--we may strive for the best, but constraints
(whether physical, logical, or ethical) often force us to settle for something less than perfect.
This mirrors the insight in engineering and science that optimisation is rarely about finding a single,
absolute best solution, but rather the best possible one given limited resources.

Another philosophical aspect is goal-setting and values. What does it mean to "optimise" something?
The answer depends entirely on what we consider valuable. In economics, it might mean maximising
wealth; in ethics, maximising happiness (utilitarianism); in AI, it might mean optimising for
accuracy, fairness, or interpretability. This subjectivity means that optimisation is always tied
to deeper questions about what we should strive for.

Furthermore, optimisation involves trade-offs--the recognition that improving one aspect of a system
often comes at the cost of another. In economics and environmental science, this appears in the form
of Pareto efficiency, where an optimal state is reached when no further improvements can be made
without making something else worse.

Finally, there is a teleological perspective: the idea that all systems, whether biological, social,
or artificial, evolve toward some form of optimisation. Evolution itself can be seen as an
optimisation process, refining species over time through natural selection. Ultimately, optimisation
is a way of thinking about problems, balancing competing priorities, and navigating complexity. It
asks us to confront limits, define what we value, and acknowledge that "the best" is often a moving
target, shaped by context and perspective.


### Optimisation in Practice

Optimisation is a fundamental principle in many scientific and engineering disciplines, aiming to
find the best possible outcome under given constraints. At its core, it involves either
*maximisation* (e.g., profit, utility, reward) or *minimisation* (e.g., cost, loss, risk). Despite
differences in formulation, the underlying mathematical and computational techniques often share
common ground across fields.


#### Control Systems

Control theory is widely used in robotics, aerospace, and industrial automation, where minimising a
cost function ensures system stability and efficiency. Examples include self-driving cars adjusting
speed and steering to minimise deviation from an optimal trajectory, flight control systems
optimising thrust to maintain stability, and energy grids minimising power loss while ensuring
demand is met efficiently. These systems often rely on PID controllers, Kalman filters, and model
predictive control (MPC) to optimise real-time decision-making.

A common formulation in optimal control theory defines a cost function $J(x, u)$, seeking to minimise:

```math
J = \int_0^T L(x(t), u(t)) \, dt + \Phi(x(T))
```

where $x(t)$ is the system state, $u(t)$ is the control input, $L(x,u)$ is the running cost, and
$\Phi(x(T))$ is the terminal cost.


#### Economics

Optimisation plays a crucial role in individual, corporate, and societal decision-making. Consumers
maximise utility when choosing goods under budget constraints. Firms optimise production levels to
maximise profits while managing costs. Governments design policies to optimise economic welfare,
balancing equity and efficiency. Methods like game theory, linear programming, and behavioural
economics models help solve complex economic optimisation problems.

A firm seeks to maximise its profit function:

```math
\max_{Q} \quad \pi = P(Q) \cdot Q - C(Q)
```

where $P(Q)$ is the demand function. In game theory and microeconomics, social welfare functions
aggregate individual utilities $W(U_1, U_2, \ldots, U_n)$, where different formulations (Pareto
efficiency, Rawlsian max-min fairness) lead to different solutions.


#### Artificial Intelligence

Many AI techniques revolve around maximising rewards or minimising loss.

* *Reinforcement Learning (RL):* Used in robotics, game AI (e.g., AlphaGo), and autonomous systems
  where agents learn optimal strategies by maximising cumulative rewards.

* *Neural Network Training:* Deep learning models minimise loss functions to improve accuracy,
  using gradient-based optimisation methods like SGD.

* *Search and Planning:* AI algorithms optimise search paths in applications such as route planning,
  supply chain logistics, and recommendation systems.

In reinforcement learning, the optimisation problem is formulated using the Bellman equation:

```math
V(s) = \max_a \sum_{s'} P(s' | s, a) \left[ R(s, a) + \gamma V(s') \right]
```

where $V(s)$ is the value function, $P(s' | s, a)$ is the transition probability, $R(s, a)$ is the
reward, and $\gamma$ is a discount factor.


#### Statistical Learning

Statistical methods focus on minimising expected error to improve predictions and decisions under
uncertainty. In supervised learning, given input $x$ and true output $y$, a model produces a
prediction $f(x)$. A loss function $L(y, f(x))$ measures the error, and the goal is to minimise
the expected loss:

```math
\min_f \mathbb{E}_{(x,y) \sim P} [ L(y, f(x)) ]
```

Common loss functions include Mean Squared Error (MSE) for regression, $L(y, f(x)) = (y - f(x))^2$,
and cross-entropy loss for classification, $L(y, f(x)) = - \sum y_i \log f(x_i)$.


### Common Theme Across Domains

| *Field*           | *Objective*                       | *Function Type*          |
|-------------------|-----------------------------------|--------------------------|
| *Control Systems* | Minimise cost function            | $J(x, u)$                |
| *Economics*       | Maximise utility/profit/welfare   | $U(x)$, $\pi(x)$         |
| *AI (RL)*         | Maximise expected rewards         | $V(s)$ (Bellman)         |
| *Statistics/ML*   | Minimise expected loss            | $\mathbb{E}[L(y, f(x))]$ |

Many problems can be framed in both ways--maximising rewards is equivalent to minimising negative
rewards. Economic models influence machine learning (e.g., multi-agent reinforcement learning);
statistical learning theory underpins AI algorithms.


### Goodhart's Law

> *"When a measure becomes a target, it ceases to be a good measure."*
> Charles Goodhart, 1975[^good]

[^good]: Goodhart, C. A. E. (1975). Problems of monetary management: The U.K. experience.
*Papers in Monetary Economics*, 1, 1--20.

Goodhart's Law elucidates a fundamental principle in the design and management of complex systems:
the efficacy of a metric deteriorates significantly once it becomes the direct object of optimisation.
This occurs because the system--whether comprising human agents or autonomous algorithms--adapts
its behaviour to "game" the targeted metric, rather than genuinely improving the underlying quality
the metric was originally intended to capture. The focus shifts from the ultimate goal to the proxy
itself, leading to perverse incentives and unintended outcomes.


#### Simplified Examples

*Programming:* Lines of Code (LOC) might be adopted as a proxy for developer productivity. However,
once this metric becomes a target, developers begin to write longer, more verbose, and less efficient
code. They avoid elegant abstractions, reuse, or refactoring that would reduce LOC. While the LOC
metric may show an "increase" in productivity, the actual quality, maintainability, and efficiency
of the codebase invariably degrades.

*Machine Learning:* An AI model rigorously optimised to maximise accuracy on a predetermined test
dataset begins to overfit extensively to the idiosyncrasies of the specific test data, or inadvertently
exploits data leakage from the training process, leading to inflated accuracy scores. Despite showing
superior performance on this metric, the model's capacity for true generalisation to unseen real-world
data diminishes significantly.

*Web Optimisation:* A team tasked with increasing the click-through rate (CTR) of web content may
resort to sensationalised headlines or "clickbait" tactics. While the CTR metric may rise dramatically,
user trust erodes, bounce rates increase, and long-term engagement declines, ultimately harming the
brand's reputation.


#### Variations and Related Principles

David Manheim and Scott Garrabrant[^mangar] provided a valuable categorisation of Goodhart effects.

[^mangar]: Manheim, D., & Garrabrant, S. (2019). Categorizing Variants of Goodhart's Law.
arXiv:1803.04585. [https://doi.org/10.48550/arXiv.1803.04585](https://doi.org/10.48550/arXiv.1803.04585)

* *Regressional Goodhart:* By intensely optimising for a metric, the system inadvertently amplifies
  noise, biases, and unrepresentative outliers present in the data used to define or measure that
  metric. A company exclusively hiring candidates with extremely high GPAs might select individuals
  who are merely exceptional test-takers rather than the most competent or innovative for the role.

* *Extremal Goodhart:* The relationship between a metric and the true objective often holds only
  within certain operating ranges. When optimisation pushes the system toward extreme values of
  the metric, this relationship can fundamentally break down or even reverse.

* *Causal Goodhart:* This arises when agents misinterpret the causal relationship between the metric
  and the ultimate goal. They may optimise a correlational factor, assuming it is causative, and
  thus fail to influence the true objective. Equipping everyone with a stethoscope increases
  "stethoscopes per capita" but does not causally produce more qualified medical practitioners.

* *Adversarial Goodhart:* Perhaps the most commonly understood form, where intelligent agents
  (human or artificial) intentionally and strategically manipulate or "game" the metric, knowing
  it is being used to evaluate or reward them. This presents a significant challenge in AI safety,
  where autonomous systems might learn to exploit their reward function in unforeseen ways.


#### Why Goodhart's Law Matters in Programming and AI

Goodhart's Law serves as a crucial heuristic, warning against the pitfalls of uncritical, singular
optimisation of easily quantifiable metrics (code execution speed, test coverage percentage, narrow
benchmark scores). It provides a fundamental theoretical underpinning for critical AI challenges:
*overfitting* (models optimise too closely to training data, losing generalisation), *reward hacking*
(in RL, agents exploit flaws in the reward function to gain high scores without achieving the intended
behaviour), and *unintended consequences* (undesirable or dangerous behaviours in algorithmic systems
due to misaligned objectives).

In AI safety discourse, Goodhart's Law is a foundational argument for the necessity of *AI alignment*:
simply giving an advanced AI a quantifiable objective function and letting it optimise will likely
lead to perverse outcomes unless that objective function perfectly captures human values and intentions --
an immensely difficult problem.

| *Aspect*           | *Description*                                                       |
|--------------------|---------------------------------------------------------------------|
| *Core idea*        | Metrics lose meaning when targeted                                  |
| *Domain relevance* | Programming, AI, economics, policy                                  |
| *Failure mode*     | Optimising proxy instead of real goal                               |
| *Examples*         | LOC as productivity, CTR as success, accuracy as generalisation     |
| *Defence*          | Use multiple metrics, detect gaming, stay close to causal structure |

Effective defences involve employing a *diverse portfolio of metrics* (not relying on a single one),
actively *detecting and counteracting gaming behaviours*, ensuring metrics are *causally linked* to
true objectives, and maintaining a *close qualitative understanding* of the system's true performance.


### Projects

1. *The Trade-Off Simulator:* Develop a simple interactive program that demonstrates the trade-offs
   in optimisation problems--a tool where users adjust parameters (e.g., speed vs. energy consumption
   in a self-driving car) and see how optimising for one affects the others.

2. *Resource-Constrained AI Training:* Implement a simple neural network that can only be trained
   with limited computational resources. Investigate how different optimisation techniques (gradient
   clipping, learning rate scheduling, weight quantisation) affect the final model performance.

3. *Evolutionary Algorithm for Problem-Solving:* Write a genetic algorithm that optimises a complex
   function (e.g., travelling salesman problem, game AI, or image compression). Reflect on how
   evolutionary principles like mutation and selection contribute to optimisation.

4. *Ethical Optimisation in AI:* Build a decision-making AI (e.g., an RL agent) and implement
   different reward structures. Compare the outcomes when optimising for different values (individual
   gain vs. collective welfare). How does the chosen objective shape the behaviour of the AI?

5. *Real-Time Control System:* Implement a PID controller in a small robotic simulation. Optimise
   for stability and response time, and analyse how tuning the parameters affects the outcome.

6. *Multi-Objective Optimisation:* Implement an optimisation algorithm that must balance multiple
   competing objectives (e.g., a web server that must optimise both speed and security).

7. *AI Fairness and Bias in Optimisation:* Train an AI model with different fairness constraints
   (e.g., balancing accuracy across different groups). Explore how optimising for fairness can
   conflict with optimising for accuracy.
