#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define STATES 3
#define ACTIONS 2
#define GAMMA 0.9
#define THETA 0.0001

// Transition probabilities: P[s][a][s']
// For each (state, action), probability of landing in next state s'
double P[STATES][ACTIONS][STATES] = {
    // From state 0
    {
        {0.8, 0.2, 0.0}, // action 0
        {0.0, 0.9, 0.1}  // action 1
    },
    // From state 1
    {
        {0.1, 0.8, 0.1},
        {0.0, 0.2, 0.8}
    },
    // From state 2
    {
        {0.0, 0.0, 1.0},
        {0.0, 0.0, 1.0}
    }
};

// Rewards for each (s, a, s')
double R[STATES][ACTIONS][STATES] = {
    {
        {+5, 0, 0},
        {0, +1, -1}
    },
    {
        {-1, 0, +2},
        {0, 0, +10}
    },
    {
        {0, 0, 0},
        {0, 0, 0}
    }
};

double V[STATES];       // Value function
int policy[STATES];     // Greedy policy

void value_iteration() {
    double delta;
    int i, a, s_prime;
    do {
        delta = 0.0;
        for (int s = 0; s < STATES; s++) {
            double v = V[s];
            double max_value = -INFINITY;
            for (a = 0; a < ACTIONS; a++) {
                double value = 0.0;
                for (s_prime = 0; s_prime < STATES; s_prime++) {
                    value += P[s][a][s_prime] *
                             (R[s][a][s_prime] + GAMMA * V[s_prime]);
                }
                if (value > max_value) {
                    max_value = value;
                    policy[s] = a;
                }
            }
            V[s] = max_value;
            if (fabs(v - V[s]) > delta) {
                delta = fabs(v - V[s]);
            }
        }
    } while (delta > THETA);
}

void print_results() {
    printf("Optimal Value Function:\n");
    for (int s = 0; s < STATES; s++) {
        printf("V[%d] = %.4f\n", s, V[s]);
    }
    printf("\nOptimal Policy (0=left, 1=right):\n");
    for (int s = 0; s < STATES; s++) {
        printf("Policy[%d] = %d\n", s, policy[s]);
    }
}

int main() {
    value_iteration();
    print_results();
    return 0;
}
