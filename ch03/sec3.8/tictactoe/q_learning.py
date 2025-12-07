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

# after training, play a game
def play_game(env, agent, opponent, starting_player=PLAYER_X):
    """
    Play a single game of Tic-Tac-Toe with the trained Q-learning agent.
    The opponent can be another agent or a human player.
    """
    state = env.reset()
    env.render()
    current_player = starting_player

    while not env.done:
        if current_player == PLAYER_X:
            # Agent makes a move
            action = agent.choose_action(state)
        else:
            # Opponent makes a move (can be random or human input)
            if opponent == "random":
                action = random.choice(env.get_valid_moves())
            elif opponent == "human":
                print("Valid moves:", env.get_valid_moves())
                action = tuple(map(int, input("Enter your move as row,col (0-indexed): ").split(',')))

        next_state, reward, done = env.step(action, current_player)
        env.render()

        if done:
            if env.winner == PLAYER_X:
                print("Agent wins!")
            elif env.winner == PLAYER_O:
                print("Opponent wins!")
            else:
                print("It's a draw!")
            break

        # Switch players
        current_player = PLAYER_O if current_player == PLAYER_X else PLAYER_X
        state = next_state

# Example: Play against a random opponent
play_game(env, agent, opponent="random")

# Example: Uncomment to play against a human
#play_game(env, agent, opponent="human")
