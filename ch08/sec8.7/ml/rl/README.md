
## Reinforcement Learning

Reinforcement Learning (RL) is a powerful paradigm in machine learning where an agent learns to make
decisions by interacting with an environment. Unlike other forms of machine learning, RL doesn't rely
on pre-labeled datasets. Instead, the agent learns through trial and error, receiving feedback in the
form of rewards or penalties for its actions.

RL has a wide range of applications, including:
* *Game Playing:* RL has achieved superhuman performance in complex games like Chess, Go, and even video games.
* *Robotics:* Training robots to perform complex tasks such as grasping, walking, and navigating.
* *Autonomous Driving:* Developing self-driving car systems that can make real-time decisions in dynamic environments.
* *Resource Management:* Optimising energy consumption in data centers or managing complex supply chains.
* *Personalised Recommendations:* Enhancing recommendation systems by learning user preferences over time.


### Concepts in Reinforcement Learning

To understand RL, several key concepts are fundamental:

* *Agent:* The learner or decision-maker that interacts with the environment.
* *Environment:* The world with which the agent interacts. It provides states and rewards in response to the agent's actions.
* *State (S):* A complete description of the current situation in the environment.
* *Action (A):* A move or decision made by the agent that can change the state of the environment.
* *Reward (R):* A numerical feedback signal from the environment indicating how good or bad the agent's last action was.
  The agent's goal is to maximise the cumulative reward over time.
* *Policy ($\pi$):* The strategy that the agent uses to decide what action to take in a given state. It maps states to actions.
* *Value Function (V or Q):* Predicts the long-term desirability of a state or a state-action pair.
    * *State-Value Function $V(s)$:* The expected return (total cumulative reward) starting from state $s$ and following a policy $\pi$.
    * *Action-Value Function $Q(s, a)$:* The expected return starting from state $s$, taking action $a$, and thereafter following a policy $\pi$.
* *Model:* An optional component that the agent might learn or be given, which predicts how the environment will behave in response to actions.


### "AI" in Games

Let's look at how different "AI" approaches can be applied to games like Pong, using the provided HTML files as examples.

The `[human.html](./human.html)` file provides a basic Pong game where the paddle is controlled directly by a human player
using the arrow keys. This serves as a baseline to understand the game mechanics before introducing automated players.

The `[classic.html](./classic.html)` file demonstrates a "Classic AI" for Pong. This AI operates based on a set of
pre-programmed rules and heuristics. While it might appear intelligent, it relies on directly knowing the game's internal
state and even "cheats" by predicting the ball's future position.

The classic AI makes decisions based on the following:
* *Reaction Delay:* It simulates human-like delays by not reacting immediately to every ball movement.
* *Ball Prediction:* It predicts the ball's position a few frames ahead (`ball.vx * 3`) to anticipate its trajectory.
  This is a common "cheat" in rule-based game AIs, as a human player wouldn't have perfect future information.
* *Precision Factor:* It introduces a random variation in its paddle alignment, simulating imperfect human precision.
* *Chance of Wrong Direction:* Occasionally, it intentionally moves in the wrong direction, adding a layer of imperfection.
* *Reaction Frequency:* The AI only reacts 80% of the time, further mimicking human response times.

This approach is effective for creating a challenging opponent, but it's not truly "learning." It's following explicit instructions
programmed by a developer.

### Q-Learning

The `[qlearn.html](./qlearn.html)` file introduces a Reinforcement Learning agent using the Q-learning algorithm to play Pong.
Unlike the Classic AI, this agent learns to play the game by interacting with it and optimising its actions
based on rewards. It does not rely on pixels (as in GYM or Gymnasium[^gym]), but information on some parameters
controlling the game, which reduces complexity.

[^gym]: https://github.com/Farama-Foundation/Gymnasium.

The file implements a simple Reinforcement Learning (RL) agent using the Q-learning algorithm to learn how to play
a basic "Pong game" (not really, but anyway bouncing a ball against walls). The key idea is that, unlike a traditional
rule-based or "classic" AI (e.g. one that follows the ball with some randomisation), the Q-learning agent does not
start with any knowledge of how to play. Instead, it discovers an effective policy over time through trial and error,
using rewards to guide its behaviour.


#### Mathematics

Q-learning is a model-free, off-policy RL algorithm. "Model-free" means it doesn't need to understand the underlying dynamics of the
environment, and "off-policy" means it can learn the optimal policy even while following a different exploration policy.

The core of Q-learning is the *Q-value* (or action-value) function, denoted as $Q(s, a)$, which represents the expected maximum
future reward achievable by taking action $a$ in state $s$.

The *Q-learning update rule* is:

```math
Q(s, a) \leftarrow Q(s, a) + \alpha \left[ R + \gamma \max_{a'} Q(s', a') - Q(s, a) \right]
```

Where:
* $Q(s, a)$: The current Q-value for state $s$ and action $a$.
* $\alpha$ (alpha): The *learning rate* (e.g., 0.1 in the code). It determines how much new information overrides old information.
  A higher $\alpha$ means faster learning but can lead to instability.
* $R$: The *immediate reward* received after taking action $a$ in state $s$.
* $\gamma$ (gamma): The *discount factor* (e.g., 0.95 in the code). It determines the importance of future rewards. A $\gamma$ close
  to 0 makes the agent focus on immediate rewards, while a $\gamma$ close to 1 makes it consider long-term rewards.
* $s'$: The *new state* reached after taking action $a$ in state $s$.
* $\max_{a'} Q(s', a')$: The maximum Q-value for the next state $s'$ across all possible actions $a'$. This represents the optimal
  future value from the next state.
* $Q(s, a)$: The old Q-value.

The term $[R + \gamma \max_{a'} Q(s', a') - Q(s, a)]$ is known as the *temporal difference (TD) error*. It represents the difference
between the estimated value of the current action and the better estimate $R + \gamma \max_{a'} Q(s', a')$.

#### Implementation in `qlearn.html`

1. *State Representation:* The continuous game state (paddle and ball positions, ball velocity) is *discretised* into a finite number
   of "bins". This creates a manageable number of states for the Q-table. The state is represented as a string like
   "binnedPaddleX,binnedBallX,binnedBallY,ballVXSign,ballVYSign".
2. *Actions:* The agent has three possible actions: move left (-2), stay still (0), or move right (2).
3. *Q-table:* The `Q` object stores the learned Q-values, mapping a state-action pair (e.g., "stateString,-2") to a numerical Q-value.
4. *Reward System:*
    * The agent receives a reward of +1 for successfully bouncing the ball off the paddle.
    * It receives a penalty of -1 for missing the ball.
    * There's also a "reward shaping" mechanism: if the ball goes below the paddle, its position is reset to prevent the agent from
      exploiting unintended bounces, ensuring it learns to hit the ball from above.
5. *Exploration vs. Exploitation (Epsilon-Greedy Strategy):*
    * The `epsilon` parameter (e.g., 0.1) controls the balance between exploration and exploitation.
    * With a probability of `epsilon`, the agent chooses a random action (exploration).
    * Otherwise, it chooses the action with the highest Q-value for the current state (exploitation). This allows the agent to discover
      new strategies while also utilising what it has already learned.
6. *Learning Loop:* The `gameStep` function is called repeatedly. In each step:
    * The current state `s` is observed.
    * An action `a` is chosen using the epsilon-greedy strategy.
    * The action is performed, leading to a new state `s'` and a reward `r`.
    * The Q-table is updated using the Q-learning formula.
    * The game continues for multiple steps within each `loop` iteration to accelerate training.

#### RL in Games Beyond Pong

RL's strength lies in its ability to learn optimal behaviour in complex environments without explicit programming for every scenario.
This makes it ideal for:

* *Adaptive Difficulty:* Game AI can learn from player behaviour and adjust its difficulty dynamically, providing a more engaging experience.
* *Procedural Content Generation:* RL can be used to generate game levels, quests, or even entire game worlds that are challenging and interesting.
* *NPC Behaviour:* Creating more believable and sophisticated Non-Player Characters (NPCs) that can learn and adapt to player strategies.
* *Game Testing and Balancing:* RL agents can play games repeatedly to discover exploits, balance issues, or identify areas for improvement.
* *Real-time Strategy Games:* Training units to navigate, attack, and manage resources effectively.
* *Player Modelling:* Understanding player preferences and predicting their actions to offer personalised content or challenges.

In conclusion, while a "Classic AI" might offer a strong challenge through clever programming and even "cheats," Reinforcement Learning
provides a more fundamental approach to creating intelligent agents that can learn and adapt autonomously. This makes RL a powerful tool
for developing truly dynamic and engaging game experiences.

Previously on
[Reinforcement Learning](./../../../ch03/tictactoe/README.md).
