#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>
#include <string.h>

// Game definitions
#define FOOTBALL 0
#define OPERA    1
#define NUM_ACTIONS 2

// Configuration structure for easy parameter tuning
typedef struct {
    double alpha;           // Learning rate
    double gamma;           // Discount factor
    double temperature;     // Softmax temperature
    double epsilon_start;   // Initial exploration
    double epsilon_decay;   // Exploration decay
    double min_epsilon;     // Minimum exploration
    int window_size;        // Rolling window size
    int num_rounds;         // Total simulation rounds
    int report_interval;    // Reporting frequency
} Config;

// Default configuration
Config default_config = {
    .alpha = 0.1,
    .gamma = 0.0,
    .temperature = 1.0,
    .epsilon_start = 0.3,
    .epsilon_decay = 0.9999,
    .min_epsilon = 0.05,
    .window_size = 1000,
    .num_rounds = 1000000,
    .report_interval = 100000
};

// Payoff matrix: [p1_action][p2_action][player]
static const int payoffs[2][2][2] = {
    {{2, 1}, {0, 0}}, // P1 Football
    {{0, 0}, {1, 2}}  // P1 Opera
};

// Player structure with enhanced tracking
typedef struct {
    int id;
    char name[20];
    double q_table[NUM_ACTIONS];
    int action_counts[NUM_ACTIONS];
    int *action_history;        // Dynamic allocation for full history
    double *payoff_history;     // Track payoffs over time
    int *window_actions;        // Rolling window
    int window_index;
    int window_filled;
    int total_payoff;
    int rounds_played;
} Player;

// Statistics structure
typedef struct {
    double avg_payoff[2];
    double strategy_prob[2][NUM_ACTIONS];
    double window_prob[2][NUM_ACTIONS];
    double nash_distance[2];
    double convergence_rate;
} GameStats;

// Function prototypes
void init_player(Player *player, int id, const char *name, const Config *config);
void cleanup_player(Player *player);
int choose_action_softmax(const Player *player, double temperature);
int choose_action_epsilon_greedy(const Player *player, double epsilon);
void update_q_value(Player *player, int action, double reward, const Config *config);
void update_player_stats(Player *player, int action, double payoff, int round);
void compute_strategy_probabilities(const Player *player, double *probs, double temperature);
void compute_window_probabilities(const Player *player, double *probs, int window_size);
void play_round(Player *p1, Player *p2, int round, double epsilon, const Config *config);
void compute_game_stats(const Player *p1, const Player *p2, GameStats *stats, const Config *config);
void print_round_report(const Player *p1, const Player *p2, int round, const Config *config);
void print_final_report(const Player *p1, const Player *p2, const GameStats *stats, const Config *config);
void print_nash_equilibrium(void);
double calculate_nash_distance(const double *probs);
void run_experiment(const Config *config, const char *experiment_name);

// Initialize player with dynamic memory allocation
void init_player(Player *player, int id, const char *name, const Config *config) {
    player->id = id;
    strncpy(player->name, name, sizeof(player->name) - 1);
    player->name[sizeof(player->name) - 1] = '\0';
    
    // Initialize Q-values to small random values to break symmetry
    for (int i = 0; i < NUM_ACTIONS; i++) {
        player->q_table[i] = ((double)rand() / RAND_MAX - 0.5) * 0.1;
        player->action_counts[i] = 0;
    }
    
    // Allocate memory for tracking
    player->action_history = malloc(config->num_rounds * sizeof(int));
    player->payoff_history = malloc(config->num_rounds * sizeof(double));
    player->window_actions = malloc(config->window_size * sizeof(int));
    
    // Initialize window with balanced actions
    for (int i = 0; i < config->window_size; i++) {
        player->window_actions[i] = i % NUM_ACTIONS;
    }
    
    player->window_index = 0;
    player->window_filled = 0;
    player->total_payoff = 0;
    player->rounds_played = 0;
}

// Cleanup dynamic memory
void cleanup_player(Player *player) {
    free(player->action_history);
    free(player->payoff_history);
    free(player->window_actions);
}

// Softmax action selection with temperature
int choose_action_softmax(const Player *player, double temperature) {
    double q_vals[NUM_ACTIONS];
    double sum_exp = 0.0;
    
    // Apply temperature and compute softmax
    for (int i = 0; i < NUM_ACTIONS; i++) {
        q_vals[i] = exp(player->q_table[i] / temperature);
        sum_exp += q_vals[i];
    }
    
    double prob_football = q_vals[FOOTBALL] / sum_exp;
    return ((double)rand() / RAND_MAX < prob_football) ? FOOTBALL : OPERA;
}

// Epsilon-greedy action selection
int choose_action_epsilon_greedy(const Player *player, double epsilon) {
    if ((double)rand() / RAND_MAX < epsilon) {
        return rand() % NUM_ACTIONS;
    }
    return (player->q_table[FOOTBALL] > player->q_table[OPERA]) ? FOOTBALL : OPERA;
}

// Enhanced Q-value update with optional eligibility traces
void update_q_value(Player *player, int action, double reward, const Config *config) {
    double td_error = reward - player->q_table[action];
    player->q_table[action] += config->alpha * td_error;
}

// Update player statistics
void update_player_stats(Player *player, int action, double payoff, int round) {
    player->action_history[round] = action;
    player->payoff_history[round] = payoff;
    player->action_counts[action]++;
    player->total_payoff += (int)payoff;
    player->rounds_played++;
    
    // Update rolling window
    player->window_actions[player->window_index] = action;
    player->window_index = (player->window_index + 1) % 1000; // Use fixed size for now
    if (player->window_index == 0) {
        player->window_filled = 1;
    }
}

// Compute strategy probabilities from Q-values
void compute_strategy_probabilities(const Player *player, double *probs, double temperature) {
    double q_football = player->q_table[FOOTBALL] / temperature;
    double q_opera = player->q_table[OPERA] / temperature;
    double sum_exp = exp(q_football) + exp(q_opera);
    
    probs[FOOTBALL] = exp(q_football) / sum_exp;
    probs[OPERA] = exp(q_opera) / sum_exp;
}

// Compute probabilities from rolling window
void compute_window_probabilities(const Player *player, double *probs, int window_size) {
    int counts[NUM_ACTIONS] = {0};
    int total = player->window_filled ? window_size : player->window_index;
    
    if (total == 0) {
        probs[FOOTBALL] = probs[OPERA] = 0.5;
        return;
    }
    
    for (int i = 0; i < total; i++) {
        counts[player->window_actions[i]]++;
    }
    
    probs[FOOTBALL] = (double)counts[FOOTBALL] / total;
    probs[OPERA] = (double)counts[OPERA] / total;
}

// Play a single round with enhanced logging
void play_round(Player *p1, Player *p2, int round, double epsilon, const Config *config) {
    int action1, action2;
    
    // Choose actions based on exploration strategy
    if ((double)rand() / RAND_MAX < epsilon) {
        action1 = rand() % NUM_ACTIONS;
        action2 = rand() % NUM_ACTIONS;
    } else {
        action1 = choose_action_softmax(p1, config->temperature);
        action2 = choose_action_softmax(p2, config->temperature);
    }
    
    // Get payoffs
    double payoff1 = payoffs[action1][action2][0];
    double payoff2 = payoffs[action1][action2][1];
    
    // Update Q-values
    update_q_value(p1, action1, payoff1, config);
    update_q_value(p2, action2, payoff2, config);
    
    // Update player statistics
    update_player_stats(p1, action1, payoff1, round);
    update_player_stats(p2, action2, payoff2, round);
    
    // Print periodic reports
    if (round % config->report_interval == 0) {
        print_round_report(p1, p2, round, config);
    }
}

// Calculate distance from Nash equilibrium (2/3, 1/3 for P1; 1/3, 2/3 for P2)
double calculate_nash_distance(const double *probs) {
    double nash_p1[2] = {2.0/3.0, 1.0/3.0};
    double nash_p2[2] = {1.0/3.0, 2.0/3.0};
    
    // Use the first player's Nash as reference (could be parameterized)
    double distance = 0.0;
    for (int i = 0; i < NUM_ACTIONS; i++) {
        distance += fabs(probs[i] - nash_p1[i]);
    }
    return distance;
}

// Compute comprehensive game statistics
void compute_game_stats(const Player *p1, const Player *p2, GameStats *stats, const Config *config) {
    // Average payoffs
    stats->avg_payoff[0] = (double)p1->total_payoff / p1->rounds_played;
    stats->avg_payoff[1] = (double)p2->total_payoff / p2->rounds_played;
    
    // Strategy probabilities
    compute_strategy_probabilities(p1, stats->strategy_prob[0], config->temperature);
    compute_strategy_probabilities(p2, stats->strategy_prob[1], config->temperature);
    
    // Window probabilities
    compute_window_probabilities(p1, stats->window_prob[0], config->window_size);
    compute_window_probabilities(p2, stats->window_prob[1], config->window_size);
    
    // Nash equilibrium distance
    stats->nash_distance[0] = calculate_nash_distance(stats->strategy_prob[0]);
    stats->nash_distance[1] = calculate_nash_distance(stats->strategy_prob[1]);
    
    // Simple convergence measure (could be enhanced)
    stats->convergence_rate = (stats->nash_distance[0] + stats->nash_distance[1]) / 2.0;
}

// Print round report
void print_round_report(const Player *p1, const Player *p2, int round, const Config *config) {
    double p1_probs[NUM_ACTIONS], p2_probs[NUM_ACTIONS];
    double p1_window[NUM_ACTIONS], p2_window[NUM_ACTIONS];
    
    compute_strategy_probabilities(p1, p1_probs, config->temperature);
    compute_strategy_probabilities(p2, p2_probs, config->temperature);
    compute_window_probabilities(p1, p1_window, config->window_size);
    compute_window_probabilities(p2, p2_window, config->window_size);
    
    printf("=== Round %d ===\n", round + 1);
    printf("P1 (%s): Q=[%.3f, %.3f] Prob=[%.3f, %.3f] Window=[%.3f, %.3f]\n",
           p1->name, p1->q_table[FOOTBALL], p1->q_table[OPERA],
           p1_probs[FOOTBALL], p1_probs[OPERA],
           p1_window[FOOTBALL], p1_window[OPERA]);
    printf("P2 (%s): Q=[%.3f, %.3f] Prob=[%.3f, %.3f] Window=[%.3f, %.3f]\n",
           p2->name, p2->q_table[FOOTBALL], p2->q_table[OPERA],
           p2_probs[FOOTBALL], p2_probs[OPERA],
           p2_window[FOOTBALL], p2_window[OPERA]);
    printf("Avg Payoffs: P1=%.3f, P2=%.3f\n\n",
           (double)p1->total_payoff / p1->rounds_played,
           (double)p2->total_payoff / p2->rounds_played);
}

// Print comprehensive final report
void print_final_report(const Player *p1, const Player *p2, const GameStats *stats, const Config *config) {
    printf("\n============================================================\n");
    printf("FINAL RESULTS (%d rounds)\n", config->num_rounds);
    printf("============================================================\n");
    
    printf("Average Payoffs:\n");
    printf("  %s: %.4f\n", p1->name, stats->avg_payoff[0]);
    printf("  %s: %.4f\n", p2->name, stats->avg_payoff[1]);
    
    printf("\nLearned Strategies (Q-values):\n");
    printf("  %s: Football=%.3f, Opera=%.3f\n", p1->name, 
           stats->strategy_prob[0][FOOTBALL], stats->strategy_prob[0][OPERA]);
    printf("  %s: Football=%.3f, Opera=%.3f\n", p2->name,
           stats->strategy_prob[1][FOOTBALL], stats->strategy_prob[1][OPERA]);
    
    printf("\nRecent Behavior (last %d rounds):\n", config->window_size);
    printf("  %s: Football=%.3f, Opera=%.3f\n", p1->name,
           stats->window_prob[0][FOOTBALL], stats->window_prob[0][OPERA]);
    printf("  %s: Football=%.3f, Opera=%.3f\n", p2->name,
           stats->window_prob[1][FOOTBALL], stats->window_prob[1][OPERA]);
    
    printf("\nNash Equilibrium Distance:\n");
    printf("  %s: %.4f\n", p1->name, stats->nash_distance[0]);
    printf("  %s: %.4f\n", p2->name, stats->nash_distance[1]);
    printf("  Combined: %.4f\n", stats->convergence_rate);
    
    printf("\nAction Frequencies:\n");
    printf("  %s: Football=%d (%.3f%%), Opera=%d (%.3f%%)\n", p1->name,
           p1->action_counts[FOOTBALL], 100.0 * p1->action_counts[FOOTBALL] / config->num_rounds,
           p1->action_counts[OPERA], 100.0 * p1->action_counts[OPERA] / config->num_rounds);
    printf("  %s: Football=%d (%.3f%%), Opera=%d (%.3f%%)\n", p2->name,
           p2->action_counts[FOOTBALL], 100.0 * p2->action_counts[FOOTBALL] / config->num_rounds,
           p2->action_counts[OPERA], 100.0 * p2->action_counts[OPERA] / config->num_rounds);
}

// Display theoretical Nash equilibrium
void print_nash_equilibrium(void) {
    printf("\n============================================================\n");
    printf("THEORETICAL NASH EQUILIBRIUM\n");
    printf("============================================================\n");
    printf("Mixed Strategy Nash Equilibrium:\n");
    printf("  Player 1: Football=0.667, Opera=0.333\n");
    printf("  Player 2: Football=0.333, Opera=0.667\n");
    printf("Expected Payoffs:\n");
    printf("  Player 1: 0.667\n");
    printf("  Player 2: 0.667\n");
}

// Run complete experiment
void run_experiment(const Config *config, const char *experiment_name) {
    printf("\n============================================================\n");
    printf("EXPERIMENT: %s\n", experiment_name);
    printf("============================================================\n");
    printf("Parameters: α=%.3f, T=%.2f, ε=%.3f→%.3f, rounds=%d\n",
           config->alpha, config->temperature, config->epsilon_start, 
           config->min_epsilon, config->num_rounds);
    
    // Initialize players
    Player player1, player2;
    init_player(&player1, 1, "Alice", config);
    init_player(&player2, 2, "Bob", config);
    
    // Run simulation
    double epsilon = config->epsilon_start;
    for (int round = 0; round < config->num_rounds; round++) {
        play_round(&player1, &player2, round, epsilon, config);
        epsilon = fmax(config->min_epsilon, epsilon * config->epsilon_decay);
    }
    
    // Compute and display results
    GameStats stats;
    compute_game_stats(&player1, &player2, &stats, config);
    print_final_report(&player1, &player2, &stats, config);
    
    // Cleanup
    cleanup_player(&player1);
    cleanup_player(&player2);
}

int main() {
    srand(time(NULL));
    
    printf("Enhanced Battle of the Sexes Q-Learning Simulation\n");
    printf("Payoff Matrix:\n");
    printf("                Player 2\n");
    printf("               F       O\n");
    printf("Player 1  F  (2,1)   (0,0)\n");
    printf("          O  (0,0)   (1,2)\n");
    
    print_nash_equilibrium();
    
    // Run default experiment
    run_experiment(&default_config, "Default Configuration");
    
    // Run experiment with different parameters
    Config high_temp_config = default_config;
    high_temp_config.temperature = 2.0;
    high_temp_config.num_rounds = 500000;
    run_experiment(&high_temp_config, "High Temperature (More Exploration)");
    
    Config fast_learning_config = default_config;
    fast_learning_config.alpha = 0.3;
    fast_learning_config.epsilon_decay = 0.999;
    run_experiment(&fast_learning_config, "Fast Learning");
    
    return 0;
}