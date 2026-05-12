#include <stdio.h>
#include <stdlib.h>
#include <time.h>

// Define strategies
#define FOOTBALL 0
#define OPERA    1

// Payoff matrix: {Player1 payoff, Player2 payoff}
// Rows: Player1 (Football, Opera)
// Columns: Player2 (Football, Opera)
int payoffs[2][2][2] = {
    {{2, 1}, {0, 0}}, // Player1 chooses Football
    {{0, 0}, {1, 2}}  // Player1 chooses Opera
};

// Structure to hold player data
typedef struct {
    int strategy;
    int total_payoff;
} Player;

// Function to choose strategy based on probability
int choose_strategy(double prob_football) {
    double r = (double)rand() / RAND_MAX;
    return (r < prob_football) ? FOOTBALL : OPERA;
}

// Function to simulate one round
void play_round(Player *p1, Player *p2, int round, double p1_prob, double p2_prob) {
    // Strategy selection based on probabilities
    p1->strategy = choose_strategy(p1_prob);
    p2->strategy = choose_strategy(p2_prob);

    // Get payoffs
    int p1_payoff = payoffs[p1->strategy][p2->strategy][0];
    int p2_payoff = payoffs[p1->strategy][p2->strategy][1];

    // Update total payoffs
    p1->total_payoff += p1_payoff;
    p2->total_payoff += p2_payoff;

    // Print round result
    printf("Round %d:\n", round + 1);
    printf("Player 1 chooses %s, Player 2 chooses %s\n",
           p1->strategy == FOOTBALL ? "Football" : "Opera",
           p2->strategy == FOOTBALL ? "Football" : "Opera");
    printf("Payoffs: Player 1 = %d, Player 2 = %d\n\n", p1_payoff, p2_payoff);
}

// Function to calculate expected payoff in mixed-strategy Nash equilibrium
void calculate_nash_equilibrium() {
    double p = 2.0 / 3.0; // Player 1 probability of choosing Football
    double q = 1.0 / 3.0; // Player 2 probability of choosing Football

    // Expected payoff for Player 1:
    // E1(F) = q*2 + (1-q)*0 = 2q
    // E1(O) = q*0 + (1-q)*1 = 1-q
    // In equilibrium, E1(F) = E1(O) => 2q = 1-q => q = 1/3
    // Expected payoff = 2*(1/3) = 2/3
    double p1_expected = 2.0 * q;

    // Expected payoff for Player 2:
    // E2(F) = p*1 + (1-p)*0 = p
    // E2(O) = p*0 + (1-p)*2 = 2(1-p)
    // In equilibrium, E2(F) = E2(O) => p = 2(1-p) => p = 2/3
    // Expected payoff = 2*(1-2/3) = 2/3
    double p2_expected = p;

    printf("Mixed-Strategy Nash Equilibrium:\n");
    printf("Player 1 chooses Football with probability %.3f, Opera with %.3f\n", p, 1.0 - p);
    printf("Player 2 chooses Football with probability %.3f, Opera with %.3f\n", q, 1.0 - q);
    printf("Expected payoff per round:\n");
    printf("Player 1: %.3f\n", p1_expected);
    printf("Player 2: %.3f\n\n", p2_expected);
}

int main() {
    srand(time(NULL)); // Seed random number generator

    Player player1 = {0, 0};
    Player player2 = {0, 0};

    int num_rounds = 5; // Number of rounds to simulate

    printf("Battle of the Sexes Game Simulation\n");
    printf("Payoff Matrix:\n");
    printf("                Player 2\n");
    printf("               F       O\n");
    printf("Player 1  F  (2,1)   (0,0)\n");
    printf("          O  (0,0)   (1,2)\n\n");

    // Simulate rounds with random strategies (uniform probability)
    printf("Simulation with Random Strategies (p = q = 0.5):\n");
    for (int i = 0; i < num_rounds; i++) {
        play_round(&player1, &player2, i, 0.5, 0.5);
    }

    // Print random strategy results
    printf("Random Strategy Results after %d rounds:\n", num_rounds);
    printf("Player 1 total payoff: %d\n", player1.total_payoff);
    printf("Player 2 total payoff: %d\n", player2.total_payoff);
    printf("Average payoff per round:\n");
    printf("Player 1: %.2f\n", (float)player1.total_payoff / num_rounds);
    printf("Player 2: %.2f\n\n", (float)player2.total_payoff / num_rounds);

    // Reset payoffs for Nash equilibrium simulation
    player1.total_payoff = 0;
    player2.total_payoff = 0;

    // Simulate rounds with mixed-strategy Nash equilibrium probabilities
    printf("Simulation with Mixed-Strategy Nash Equilibrium:\n");
    for (int i = 0; i < num_rounds; i++) {
        play_round(&player1, &player2, i, 2.0 / 3.0, 1.0 / 3.0);
    }

    // Print Nash equilibrium simulation results
    printf("Nash Equilibrium Results after %d rounds:\n", num_rounds);
    printf("Player 1 total payoff: %d\n", player1.total_payoff);
    printf("Player 2 total payoff: %d\n", player2.total_payoff);
    printf("Average payoff per round:\n");
    printf("Player 1: %.2f\n", (float)player1.total_payoff / num_rounds);
    printf("Player 2: %.2f\n", (float)player2.total_payoff / num_rounds);

    // Calculate and display theoretical Nash equilibrium payoffs
    calculate_nash_equilibrium();

    return 0;
}

// This code simulates the "Battle of the Sexes" game
// using both random strategies and mixed-strategy Nash equilibrium.
