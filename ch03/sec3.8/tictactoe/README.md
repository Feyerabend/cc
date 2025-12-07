
## The Movie *WarGames*

In the 1983 movie *WarGames*[^war], the plot revolves around a young computer whiz named David Lightman, played by Matthew Broderick,
who accidentally hacks into a U.S. military supercomputer called WOPR (War Operation Plan Response). Initially believing that
he is playing a game of chess against a computer, David unwittingly triggers a sequence of events that leads to the simulation
of a global nuclear conflict. The plot centres on David's realization that the WOPR system, designed to simulate and predict
outcomes of military conflicts, has the power to launch real nuclear weapons. The critical moment in the film comes when David, 
using his knowledge of games and computer systems, realises that the only way to prevent global catastrophe is to convince the
supercomputer that nuclear war is not winnable.

A key moment in *WarGames* is when David, after engaging the WOPR in a game of Tic-Tac-Toe, understands the parallel between the
strategy of the game and the futility of nuclear war. The computer plays Tic-Tac-Toe, a game that is simple, deterministic, and
has a known solution where either a player wins or the game results in a draw. The lesson that emerges from the game, which is
applied to nuclear strategy, is that there are no winners in a global thermonuclear war--just like in Tic-Tac-Toe, the best outcome
is a draw.

This revelation is crucial to the plot, as David uses the simple logic of the game to break through to the supercomputer. He
demonstrates to the WOPR system that a nuclear conflict is analogous to a game of Tic-Tac-Toe, where the only logical conclusion
is not to engage at all. The computer, after playing several rounds of Tic-Tac-Toe and analysing the results, concludes that it
is a futile exercise--just as a nuclear war would be. This realisation leads to the cessation of the simulated global conflict
and ultimately prevents the launch of real-world nuclear weapons.

[^war]: See https://www.imdb.com/title/tt0086567/, https://en.wikipedia.org/wiki/WarGames.


### The Significance of Tic-Tac-Toe in *WarGames*

Tic-Tac-Toe is pivotal in *WarGames* not just as a game but as a metaphor for the futility of nuclear war. The movie draws a parallel
between the game's simple structure, where the outcome is either a draw or a win for one player (if both players play optimally),
and the destructive nature of global conflict. The game's deterministic nature provides an easily understandable model for how the
complex, unpredictable nature of war can be reduced to a simpler concept: there are no real winners, only devastation.

The inclusion of Tic-Tac-Toe also plays into the broader theme of *WarGames*---the misunderstanding and misapplication of technology in
high-stakes situations. The WOPR computer, despite its advanced capabilities, is initially unable to understand the implications of
global nuclear war until it engages in the simple, non-threatening game. This shift from a war game to a trivial game like Tic-Tac-Toe
highlights the movie's central critique of the Cold War arms race and the reliance on computer systems to make life-or-death decisions.
The simplicity of Tic-Tac-Toe becomes a stark contrast to the complex, life-threatening scenarios that computers were being used to
simulate and manage at the time.


### Tic-Tac-Toe and the broader concept of AI and decision-making

The Tic-Tac-Toe game also connects to broader questions about artificial intelligence (AI) and decision-making, which have become
increasingly relevant as AI systems are used to simulate and potentially make decisions in warfare. In the movie, the WOPR system is
capable of running simulations of nuclear war but, without understanding the human element--such as the futility of total destruction--it
cannot arrive at a logical conclusion on its own. The game of Tic-Tac-Toe, with its clearly defined rules and outcomes, serves as
a turning point, showing that human judgment and logic are still critical when dealing with AI in high-stakes situations.

In today's world, the lessons from *WarGames* and the simplicity of Tic-Tac-Toe resonate with the ongoing development and deployment of
AI in military contexts. Whether it's AI-controlled drones, missile defense systems, or autonomous weapons, the concern is that these
systems might make decisions without human intervention or oversight. The film serves as a reminder that, much like the game of Tic-Tac-Toe,
certain types of conflict--particularly those involving mass destruction--are best avoided altogether, and AI systems need to be guided
by ethical reasoning and human understanding to ensure they don't lead to catastrophic consequences.

The plot of *WarGames*, especially the use of Tic-Tac-Toe, highlights the intersection of games, AI, and military strategy. The film uses
the simple rules of a children's game to demonstrate that sometimes, in the context of warfare, there is no winning move--only the
avoidance of conflict. This concept, drawn from the game, becomes a metaphor for the broader political and technological concerns
of the 1980s, which still resonate today as AI and automated systems continue to play an increasing role in defense and decision-making.


## Tic-Tac-Toe

To transition to the game of tic-Tac-Toe itself, there are several machine learning (ML) and artificial
intelligence (AI) approaches that can be used to train a model or agent to play the game. Given that
Tic-Tac-Toe is a relatively small and simple game, it is a great candidate for a classic search-based
algorithm. But we will also give you a simple reinforcement learning (RL) approach, to illustrate the method
rather than the applicationn--which is not really the optimal solution.


__1. Minimax algorithm (classic AI)__

The most commonly used AI approach for Tic-Tac-Toe is the Minimax algorithm. Minimax is a tree search algorithm
that works by considering all possible moves at each step and selecting the one that minimizes the opponent's best
possible counter-move (hence "minimax").

*Maximizing Player*: The AI (computer) tries to maximize its own score (i.e. a win).

*Minimizing Player*: The opponent (human or computer) tries to minimize the AI's score (i.e. prevent the AI from winning).

The algorithm works by recursively simulating all possible moves until it reaches the end of the game (win, loss, or draw),
then assigning a value to each terminal state:

```text
  +1 for a win,
  -1 for a loss,
  0 for a draw.
```

__2. Q-Learning (Reinforcement Learning)__

Another way to approach this problem is by using Q-learning, which is a model-free reinforcement learning algorithm.
Q-learning learns a policy (i.e., a mapping from states to actions) that maximizes the expected reward.

In Q-learning:
- The agent learns the value of each action in each state by interacting with the environment.
- The agent updates its action-values (Q-values) after each move and continues learning through exploration and exploitation.

However, even if Q-learning might be an overkill for a simple game like Tic-Tac-Toe, it will give you a simple implementation
for you to explore reinforcement learning.


### 1. Minimax Algorithm for Tic-Tac-Toe

Let's start with the Minimax algorithm implementation for Tic-Tac-Toe.

```python
import math

# constants
EMPTY = 0
PLAYER_X = 1
PLAYER_O = -1

def print_board(board):
    """Prints the Tic-Tac-Toe board."""
    for i in range(3):
        row = ""
        for j in range(3):
            if board[i][j] == PLAYER_X:
                row += "X "
            elif board[i][j] == PLAYER_O:
                row += "O "
            else:
                row += "- "
        print(row)
    print()

def is_winner(board, player):
    """Check if the given player has won."""
    for i in range(3):
        # check rows and columns
        if all(board[i][j] == player for j in range(3)) or all(board[j][i] == player for j in range(3)):
            return True
    # check diagonals
    if board[0][0] == player and board[1][1] == player and board[2][2] == player:
        return True
    if board[0][2] == player and board[1][1] == player and board[2][0] == player:
        return True
    return False

def is_full(board):
    """Check if the board is full."""
    return all(board[i][j] != EMPTY for i in range(3) for j in range(3))

def minimax(board, depth, is_maximizing):
    """Minimax algorithm to evaluate the best move for the maximizing player."""
    if is_winner(board, PLAYER_X):
        return 1  # X wins
    if is_winner(board, PLAYER_O):
        return -1  # O wins
    if is_full(board):
        return 0  # draw

    if is_maximizing:
        best_score = -math.inf
        for i in range(3):
            for j in range(3):
                if board[i][j] == EMPTY:
                    board[i][j] = PLAYER_X  # make the move for X
                    score = minimax(board, depth + 1, False)  # minimize for O
                    board[i][j] = EMPTY  # undo move
                    best_score = max(score, best_score)
        return best_score
    else:
        best_score = math.inf
        for i in range(3):
            for j in range(3):
                if board[i][j] == EMPTY:
                    board[i][j] = PLAYER_O  # make the move for O
                    score = minimax(board, depth + 1, True)  # maximize for X
                    board[i][j] = EMPTY  # undo move
                    best_score = min(score, best_score)
        return best_score

def best_move(board):
    """Returns the best move for the AI (Player X)."""
    best_score = -math.inf
    move = None
    for i in range(3):
        for j in range(3):
            if board[i][j] == EMPTY:
                board[i][j] = PLAYER_X  # make move for X
                score = minimax(board, 0, False)  # minimize for O
                board[i][j] = EMPTY  # undo move
                if score > best_score:
                    best_score = score
                    move = (i, j)
    return move

board = [
    [PLAYER_X, PLAYER_O, EMPTY],
    [PLAYER_X, PLAYER_O, EMPTY],
    [EMPTY, EMPTY, EMPTY]
]

print_board(board)
move = best_move(board)
print(f"Best move for X is at position {move}")
```

`minimax`: This function recursively evaluates the game tree, considering all possible moves.
It returns 1 if player X wins, -1 if player O wins, and 0 if it's a draw.

`best_move`: This function iterates through all possible moves for player X and selects the
one that maximizes the result using the minimax algorithm.

`is_winner`: Checks whether a given player has won the game.

`print_board`: Prints the current state of the board.


For a given game state:

```text
X O - 
X O - 
- - - 
```

The `best_move` function will compute and return the best move for X.

In short, the minimax algorithm is a decision-making framework used in two-player games to
determine the optimal move by assuming that both players play perfectly. The algorithm evaluates
all possible moves, creating a game tree where nodes represent game states. At each step, it
alternates between a "maximizing" player, who seeks to maximize their score, and a "minimizing"
player, who aims to minimize the maximizing player's score. Starting from the end states (leaves),
the algorithm propagates the values back up the tree, with the maximizing and minimizing layers
selecting the best outcomes for their respective objectives. This ensures that the chosen move
at the root leads to the best possible outcome for the player, regardless of the opponent's responses.


### 2. Q-Learning (Reinforcement Learning)

In the Q-learning algorithm, the agent learns by exploring the environment and updating its
knowledge (Q-values) after each action. Here's a simple Q-learning implementation for Tic-Tac-Toe.

First, let's define the environment and Q-learning agent:

```python
import random

EMPTY = 0
PLAYER_X = 1
PLAYER_O = -1

class TicTacToeEnv:
    """Tic-Tac-Toe environment."""
    def __init__(self):
        self.board = [[EMPTY] * 3 for _ in range(3)]  # 3x3 board init with zeros (EMPTY)
        self.done = False
        self.winner = None

    def reset(self):
        """Resets the game environment."""
        self.board = [[EMPTY] * 3 for _ in range(3)]
        self.done = False
        self.winner = None
        return self.board

    def get_valid_moves(self):
        """Returns a list of valid (empty) positions."""
        return [(i, j) for i in range(3) for j in range(3) if self.board[i][j] == EMPTY]

    def is_winner(self, player):
        """Checks if the given player has won the game."""
        for i in range(3):
            if all(self.board[i][j] == player for j in range(3)) or \
               all(self.board[j][i] == player for j in range(3)):
                return True
        if self.board[0][0] == player and self.board[1][1] == player and self.board[2][2] == player:
            return True
        if self.board[0][2] == player and self.board[1][1] == player and self.board[2][0] == player:
            return True
        return False

    def step(self, action, player):
        """Makes a move for the player and returns the next state, reward, and done flag."""
        if self.board[action[0]][action[1]] != EMPTY:
            return self.board, -10, True  # invalid move, penalize the agent

        self.board[action[0]][action[1]] = player
        if self.is_winner(player):
            self.done = True
            self.winner = player
            return self.board, 10, True  # win
        if all(self.board[i][j] != EMPTY for i in range(3) for j in range(3)):
            self.done = True
            self.winner = 0
            return self.board, 0, True  # draw

        return self.board, 0, False  # continue game

    def render(self):
        """Prints the board."""
        for row in self.board:
            print(' '.join(['X' if x == PLAYER_X else 'O' if x == PLAYER_O else '-' for x in row]))
        print()

class QLearningAgent:
    """Q-learning agent for Tic-Tac-Toe."""
    def __init__(self, env, alpha=0.1, gamma=0.9, epsilon=0.1):
        self.env = env
        self.alpha = alpha  # learning rate
        self.gamma = gamma  # discount factor
        self.epsilon = epsilon  # exploration factor
        self.q_table = {}  # Q-value table

    def get_q_value(self, state, action):
        """Get Q-value for a given state-action pair."""
        return self.q_table.get((tuple([tuple(row) for row in state]), action), 0)

    def update_q_value(self, state, action, reward, next_state, next_action):
        """Update the Q-value for a state-action pair."""
        next_q = max([self.get_q_value(next_state, next_a) for next_a in self.env.get_valid_moves()] or [0])
        current_q = self.get_q_value(state, action)
        self.q_table[(tuple([tuple(row) for row in state]), action)] = current_q + self.alpha * (reward + self.gamma * next_q - current_q)

    def choose_action(self, state):
        """Choose an action based on epsilon-greedy strategy."""
        if random.uniform(0, 1) < self.epsilon:
            return random.choice(self.env.get_valid_moves())  # explore
        else:
            # exploit: choose the best action based on current Q-values
            valid_actions = self.env.get_valid_moves()
            q_values = [self.get_q_value(state, action) for action in valid_actions]
            max_q = max(q_values)
            best_actions = [valid_actions[i] for i in range(len(valid_actions)) if q_values[i] == max_q]
            return random.choice(best_actions)  # choose one of the best actions

# training loop
env = TicTacToeEnv()
agent = QLearningAgent(env)

for episode in range(1000):
    state = env.reset()
    done = False
    while not done:
        action = agent.choose_action(state)
        next_state, reward, done = env.step(action, PLAYER_X)
        agent.update_q_value(state, action, reward, next_state, action)
        state = next_state
```

Train the agent:

```python
env = TicTacToeEnv()
agent = QLearningAgent(env)
```

Training loop:

```python
for episode in range(1000):
    state = env.reset()
    done = False
    while not done:
        action = agent.choose_action(state)
        next_state, reward, done = env.step(action, PLAYER_X)
        agent.update_q_value(state, action, reward, next_state, action)
        state = next_state
```

After training, the agent can choose the best action for a given state.

This code implements the basic Q-learning agent for Tic-Tac-Toe. The `TicTacToeEnv` class represents
the game environment, while the `QLearningAgent` class learns a policy for Tic-Tac-Toe.

The Q-learning agent learns the best actions based on the rewards it receives after each move.
The agent explores the environment initially (with random moves), and over time, it updates its
knowledge and moves toward optimal play.


### Algorithm

The Q-learning algorithm is a reinforcement learning technique that enables an agent to learn optimal
behavior in an environment through *trial and error*. It does so by learning an action-value function,
often represented as a Q-table, which estimates the long-term reward of taking a particular action in
a given state. Over time, the agent refines these estimates and uses them to make decisions that maximize
cumulative rewards.

In the context of the provided code for the Tic-Tac-Toe game, Q-learning is used to enable the agent to
learn how to play the game optimally.


*State Representation*

The agent's state is the current configuration of the Tic-Tac-Toe board. Each possible board state is
represented as a tuple, which is a 3x3 grid of numbers, where `EMPTY` is represented by $0$,  `PLAYER_X`
is $1$, and `PLAYER_O` is $-1$.


*Action Selection*

At each step, the agent needs to decide which move to make. This is done using an *epsilon-greedy strategy*:
with a probability of $\epsilon$, the agent explores the environment by randomly choosing a valid move, and
with a probability of $1 - \epsilon$, it exploits its knowledge by choosing the move that maximizes its
estimated future reward (Q-value). The Q-value of an action is learned through experience.


*Q-Value Update*

After each action, the agent receives feedback from the environment, including the next state, the reward
(e.g. $10$ for winning, $-10$ for an invalid move, $0$ for a draw or ongoing game), and a flag indicating
whether the game is done. The agent uses the *Bellman equation* to update its Q-value for the state-action
pair. The update rule is as follows:

$$\[
Q(s, a) = Q(s, a) + \alpha \left( R + \gamma \max_a Q(s', a) - Q(s, a) \right)
\]$$

Where
* $Q(s, a)$ is the current Q-value for taking action $a$ in state $s$.
* $\alpha$ is the *learning rate*, controlling how much new information is incorporated into the current Q-value.
* $R$ is the *reward* received after performing action $a$ in state $s$.
* $\gamma$ is the *discount factor*, representing how much future rewards are valued over immediate rewards.
* $\max_a Q(s', a)$ is the maximum Q-value for the possible actions in the next state $s'$.

The agent updates its Q-table using the current state, action, reward, and the next state to improve its
"understanding" of which actions lead to higher rewards.


*Exploration vs. Exploitation*

The epsilon-greedy strategy helps balance exploration (trying new, unknown actions) and exploitation
(choosing the best-known action). Over time, as the agent learns more about the game, it will shift
from exploration to exploitation, making more informed decisions based on its learned Q-values.

*Game Flow*

In each episode (or game), the agent starts from a fresh board state, selects actions, receives rewards,
and updates its Q-values until the game ends (either by winning, drawing, or making an invalid move).
After many episodes, the agent's Q-table will reflect the best moves to make in various board states,
enabling it to play the game optimally.


### Conclusion

In summary, Q-learning allows the Tic-Tac-Toe agent to progressively learn the optimal strategy by
interacting with the game environment, updating its action-value estimates, and balancing exploration
and exploitation to maximize long-term rewards. The more episodes the agent plays, the better it becomes
at choosing the best moves, leading to an improved performance in the game.


## Projects

If you're familiar with psychology, the term *reinforcement learning* might already sound familiar.
Reinforcement learning (RL) shares its foundational roots with behavioral theories in psychology,
particularly those established in the early 20th century. RL directly builds on psychological concepts
such as learning through rewards, trial-and-error processes, and the development of habits.

Even if you haven't studied psychology, you might use a device, like a fitness tracker, that logs your
activities and provides "rewards" such as badges or notifications. This makes you an active participant
in a form of reinforcement learning. Your are the one being "trained" and respond to triggers.


Here are some possible projects that relate to programming:

__1. Implement RL for "Rock-Paper-Scissors"__

*Rock-Paper-Scissors is a simple game with no environment states, but RL can still be applied to
learn optimal strategies against an opponent.*

Tasks:
- Write a program to simulate the Rock-Paper-Scissors game.
- Implement a Q-learning agent that updates its strategy based on rewards (win: +1, lose: -1, draw: 0).
- Train the agent against:
	1.	A random opponent.
	2.	A human player.

What you will learn:
- Q-learning with no explicit states (action-reward learning).
- Strategy optimization through trial and error.


__2. Reinforcement Learning for a "Grid World"__

*Create a 2D grid where an agent starts at one corner and must reach a goal at the opposite corner while avoiding obstacles.*

The agent receives:
- Positive rewards for reaching the goal.
- Negative rewards for hitting obstacles or taking too long.

Tasks:
- Design the grid world environment (e.g. a 5x5 grid with randomly placed obstacles).
- Implement the Q-learning algorithm to train the agent to navigate the grid.
- Experiment with different grid layouts and reward structures.

What you will learn:
- State-space representation (grid positions as states).
- Exploration vs. exploitation in pathfinding problems.


__3. Train an RL Agent for "Nim"__

*Nim is a mathematical game where players take turns removing objects from heaps.
The player forced to take the last object loses. The agent must learn an optimal strategy.*

Tasks:
- Implement the game logic for Nim.
- Use Q-learning to train the agent to play optimally against:
	1.	A random opponent.
	2.	Another Q-learning agent.

What you will learn:
- State-action pairs for turn-based games.
- Strategy improvement through self-play.


__4. Teach RL to Play "Maze Solver"__

*Create a simple maze (e.g. a 10x10 grid) where the agent must find the shortest path to the goal.
Add dynamic elements like penalties for dead ends or rewards for collecting items in the maze.*

Tasks:
- Write a maze generator or hard-code a simple maze.
- Implement an RL algorithm (Q-learning or SARSA) to find optimal paths.
- Compare performance with and without penalties for wrong turns.

What you will learn:
- Navigating complex environments using RL.
- Trade-offs in reward shaping and discount factors.


__5. Explore RL with "Guess the Number"__

*The agent guesses a number chosen by the environment (e.g. say between 1 and 100).
After each guess, the environment provides feedback: "higher," "lower," or "correct."*

Tasks:
- Implement the environment logic for feedback.
- Train the agent to minimize the number of guesses using Q-learning.
- Experiment with different learning rates and exploration strategies.

What you will learn:
- RL in a purely sequential decision-making task.
- Efficient learning strategies in finite environments.


__6. Play "Connect Four" with RL__

*Connect Four is a turn-based game where players drop pieces into columns of a grid to form a
line of four. You can create a simplified version (e.g. a 4x4 grid) to train an agent.*

Tasks:
- Implement game logic for Connect Four.
- Train the agent to play against:
	1.	A random opponent.
	2.	A human player.

What you will learn:
- Q-table growth in larger state-action spaces.
- Implementing RL in competitive games.


__7. Multi-Armed Bandit Problem__

*Simulate the classic multi-armed bandit problem, where an agent selects from several slot machines
(each with different probabilities of winning) to maximize its cumulative reward.*

Tasks:
- Create a simulation with 5-10 "slot machines" with different fixed probabilities of winning.
- Implement epsilon-greedy or Upper Confidence Bound (UCB) strategies to maximize reward.
- Analyze which strategy converges faster.

What you will learn:
- Exploration-exploitation trade-offs in RL.
- Bandit problems as a simplified RL scenario.


__8. "Snake Game" with RL__

*Implement a simple version of the classic Snake game. The agent learns to move the snake to
maximize its length without hitting walls or itself.*

Tasks:
- Write the Snake game logic (small grid size like 5x5 or 10x10 to start).
- Train the agent using Q-learning or Deep Q-Networks (if more advanced).
- Experiment with different reward schemes (e.g. +10 for eating, -1 per move to encourage speed).

What you will learn:
- Dynamic environments with changing states.
- RL in games with growing state spaces.


__9. Design a Custom Board Game__

*Students design their own simple board game and implement reinforcement learning to solve it.*

Tasks:
- Define rules, state-space, and rewards for the game.
- Write a Q-learning or SARSA-based agent to play it.
- Evaluate the performance of the agent against different opponents or strategies.

What you will learn:
- Application of RL to novel scenarios.
- Balancing complexity and solvability in game design.


__10. Compare RL Techniques in Simple Games__

Pick one game (e.g. Tic-Tac-Toe, Grid World) and implement two RL algorithms:
- Q-learning (done in case Tic-Tac-Toe).
- Monte Carlo methods.
- SARSA.

Tasks:
- Train agents using both algorithms.
- Compare their performance in terms of training time, convergence, and strategy quality.
- Analyze how the choice of algorithm impacts learning.

What you will learn:
- Practical differences between RL algorithms.
- Strengths and weaknesses of various techniques.

These exercises are designed to be approachable for students with basic programming and RL knowledge
while offering opportunities for deeper exploration.
