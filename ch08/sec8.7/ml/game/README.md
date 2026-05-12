
## Game Theory

Game theory studies strategic interaction: situations where the outcome for each participant
depends on the choices of all participants. It provides a mathematical framework for reasoning
about rational decision-making in competitive and cooperative settings. See [HISTORY.md](./HISTORY.md)
for the development of the field from von Neumann to Nash.

The *Battle of the Sexes* is a canonical coordination game. Two players want to spend an evening
together but have opposite preferences: one prefers football, the other prefers opera. Both agree
that being together is better than being apart, but each would rather the shared event be their
preferred option. This creates a tension between coordination and individual preference.

Two implementations explore the game from different angles:

- `game.c` -- analytical simulation. Computes the mixed-strategy Nash equilibrium analytically
  and runs Monte Carlo rounds at equilibrium probabilities to verify empirical payoffs.
- `battle.c` -- learning-based simulation. Both players independently run Q-learning, adapting
  strategies based on experience without prior knowledge of the payoff matrix.

An interactive analysis is available in `battle_sexes_analysis.html`.


### Mathematics

The Battle of the Sexes is a two-player, two-action normal-form game. The payoff matrix is:

|          | Football | Opera |
|----------|----------|-------|
| Football | (2, 1)   | (0, 0)|
| Opera    | (0, 0)   | (1, 2)|

There are two pure-strategy Nash equilibria: (Football, Football) and (Opera, Opera). In the
mixed-strategy equilibrium, Player 1 chooses Football with probability $p$ and Player 2
chooses Football with probability $q$.

Each player's mixing probability is derived by making the opponent indifferent between their
pure strategies. Setting Player 1's expected payoffs for Football and Opera equal:

```math
2q = 1 - q \;\Rightarrow\; q = \tfrac{1}{3}
```

Symmetrically for Player 2:

```math
p = 2(1-p) \;\Rightarrow\; p = \tfrac{2}{3}
```

At the mixed equilibrium, each player's expected payoff per round is $\tfrac{2}{3}$.

`battle.c` uses Q-learning to let both players discover equilibrium strategies. Each player
maintains a Q-table over actions. At each round, the Q-value is updated:

```math
Q(a) \leftarrow Q(a) + \alpha \bigl[r - Q(a)\bigr]
```

with $\varepsilon$-greedy exploration decaying over time. The softmax action selection
temperature further controls exploration--exploitation balance.


### Concepts

* *Nash Equilibrium:* A strategy profile where no player can increase their expected payoff
  by deviating unilaterally. It is not necessarily socially optimal -- the mixed-strategy
  equilibrium here gives each player $\tfrac{2}{3}$ where coordinating purely would give 1 or 2.
* *Pure vs. Mixed Strategy:* A pure strategy is a deterministic choice; a mixed strategy is
  a probability distribution over actions. Mixed equilibria arise when no pure equilibrium
  exists or when multiple pure equilibria create coordination uncertainty.
* *Coordination vs. Competition:* The Battle of the Sexes is a coordination game, not
  zero-sum. Both players benefit from coordination; the conflict is over *which* equilibrium
  is selected, not over dividing a fixed total.
* *Learning in Games:* Q-learning agents playing against each other may or may not converge
  to Nash equilibrium. In two-player zero-sum games convergence is guaranteed; in coordination
  games it depends on initialisation and learning rates.
* *Focal Points:* In practice, players use contextual cues (Schelling points) to coordinate
  without communication. The analytical model assumes full rationality and common knowledge
  of the payoff matrix.


### Samples


*Sample 1: Battle of the Sexes -- Analytical*

* *Scenario:* `game.c` computes $p = 2/3$, $q = 1/3$ analytically, then runs 10 simulated
  rounds at those probabilities. The empirical payoff distribution converges to $2/3$ per player
  as rounds increase, confirming the theoretical prediction.

*Sample 2: Battle of the Sexes -- Q-Learning*

* *Scenario:* `battle.c` runs 1,000,000 rounds of simultaneous Q-learning. With appropriate
  learning rate and decay, both players' action frequencies converge near the mixed Nash
  equilibrium probabilities, demonstrating that model-free reinforcement learning can discover
  equilibria without explicit knowledge of the payoff matrix.

*Sample 3: Auction Mechanism Design*

* *Data:* Bidders with private valuations competing for a single item.
* *Scenario:* Game theory predicts the bidding strategy in a second-price (Vickrey) auction:
  bidding one's true valuation is a dominant strategy. Mechanism design uses this insight to
  construct auctions that are simultaneously incentive-compatible and revenue-maximising for
  the auctioneer, with applications in spectrum auctions and online advertising.
