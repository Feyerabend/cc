
## MDP and POMDP

A Markov Decision Process (MDP) is a mathematical model for sequential decision-making
where an agent interacts with a fully observable, stochastic environment. The environment
is represented by:
- $S$: a set of states
- $A$: a set of actions
- $P(s’|s,a)$: the probability of transitioning to state $s’$ after taking action $a$ in state $s$
- $R(s,a)$: the expected reward from taking action a in state s
- $\gamma \in [0,1]$: a discount factor that controls the weight of future rewards

The agent’s goal is to find a policy $\pi(s)$ that maximizes the expected sum of discounted rewards over time:
```math
\mathbb{E}\left[\sum_{t=0}^{\infty} \gamma^t R(s_t, a_t)\right]
```

MDPs assume the agent always knows the exact state of the environment, which enables algorithms like value
iteration or policy iteration to compute optimal policies using dynamic programming. When the model is unknown,
reinforcement learning methods such as Q-learning estimate values or policies directly from experience.

A Partially Observable Markov Decision Process (POMDP) extends MDPs to environments where the agent cannot
directly observe the true state. Instead, it receives noisy observations and maintains a belief distribution
over states. The components of a POMDP include:
- $S$, $A$, $P$, $R$, $\gamma$: as in an MDP
- $Z$: a set of observations
- $O(z|s’,a)$: the probability of observing $z$ after taking action $a$ and reaching state $s’$

The agent maintains a belief state $b(s)$, a probability distribution over all possible states.
After each action and observation, it updates its belief using Bayesian filtering:
```math
b’(s’) \propto O(z|s’,a) \sum_s P(s’|s,a) b(s)
```

Decision-making is then performed in the continuous belief space. Exact POMDP solutions are intractable
in most practical settings, so approximations such as point-based value iteration or particle filters are used.

Both MDPs and POMDPs are central to reinforcement learning, which is concerned with learning optimal
behavior from reward signals. In supervised learning, training data comes in labeled examples; in contrast,
MDPs and POMDPs model environments where actions influence future observations and rewards, and learning
must occur through exploration and interaction.

These models are foundational in AI fields that require planning and acting under uncertainty, including
robotics, autonomous vehicles, operations research, and strategic game playing. POMDPs, in particular,
are used where sensing is limited or noisy, such as in medical diagnostics, human-robot interaction,
or natural language dialogue systems.


### MDP (Markov Decision Process)

Real-world analogy: A robot in a factory choosing paths
- States: Physical locations (e.g. LoadingDock, AssemblyArea, ChargingStation)
- Actions: Move left, move right, wait, etc.
- Transitions: Probabilistic due to slippery floors or obstacles
  (e.g., 80% chance of moving successfully, 20% chance of slipping).
- Rewards: Defined by task goals (e.g., +10 for delivering a part, -1 for time delay).

The C program computes the optimal policy for the robot to follow
in order to maximise expected cumulative reward over time.


### POMDP (Partially Observable MDP)

Real-world analogy: A mobile healthcare robot with noisy sensors
- States: Patient is awake or asleep, or room is occupied or empty.
- Actions: Enter, wait, alert.
- Observations: Sensor readings (e.g., noise level, motion sensor) that are unreliable or ambiguous.
- Belief state: Since the robot can’t directly observe the true state
  (e.g., can’t see through walls), it maintains a probabilistic belief over all possible states.

The C program performs Bayesian filtering: it updates its belief about the world
state after taking an action and receiving an observation.

### Applications

| Model | Application Domains | Example Task |
|-------|---------------------|--------------|
| MDP   | Robotics, route planning, manufacturing, finance | Path optimisation with known environment |
| POMDP | Autonomous driving, assistive robotics, diagnostic systems, spoken dialogue systems | Decision-making with partial and noisy observations |


### Key Distinction

- *MDP:* Assumes full observability -- the agent always knows exactly which state it’s in.
- *POMDP:* Models uncertainty in both outcome and perception -- the agent never knows
  for sure where it is or what exactly is happening.

These models are used in reinforcement learning, robotics, autonomous agents, and AI planning.


### Samples


*Sample 1: Robot Path Planning in a Warehouse*

* *States:* Grid cells representing locations in the warehouse.
* *Actions:* Move north, south, east, west.
* *Transitions:* Stochastic -- 80% chance of moving in the intended direction, 10% chance of
  sliding to an adjacent cell.
* *Scenario:* A warehouse robot uses value iteration to compute the optimal policy: which
  direction to move from each cell to maximise the chance of reaching the delivery station
  while minimising time penalties.

*Sample 2: Medical Treatment Optimisation*

* *States:* Patient health status (improving, stable, deteriorating).
* *Actions:* Administer drug A, drug B, or wait.
* *Transitions:* Probabilistic treatment outcomes based on clinical trial data.
* *Scenario:* A clinical decision support system models treatment as an MDP. The optimal policy
  maximises expected quality-adjusted life years by choosing treatments based on the patient’s
  current state.

*Sample 3: Dialogue System (POMDP)*

* *States:* User intent (book flight, change seat, cancel booking) -- not directly observable.
* *Observations:* Automatic speech recognition output (noisy transcriptions of user utterances).
* *Scenario:* A spoken dialogue system maintains a belief distribution over user intent and
  chooses actions (ask a clarifying question, confirm, execute the request) to maximise task
  completion rate despite noisy observations.
