#include <stdio.h>

#define STATES 2
#define ACTIONS 2
#define OBSERVATIONS 2

typedef double vec[STATES];

// Transition probabilities: T[s][a][s']
double T[STATES][ACTIONS][STATES] = {
    { {0.8, 0.2}, {0.1, 0.9} }, // from s0
    { {0.7, 0.3}, {0.2, 0.8} }  // from s1
};

// Observation probabilities: O[s'][z]
double O[STATES][OBSERVATIONS] = {
    { 0.9, 0.1 },  // s0 generates mostly z0
    { 0.2, 0.8 }   // s1 generates mostly z1
};

// Initial belief: uniform
vec belief = {0.5, 0.5};

// Temporary array for update
vec temp;

// Normalize a probability distribution
void normalize(vec b) {
    double sum = 0.0;
    for (int i = 0; i < STATES; i++) sum += b[i];
    for (int i = 0; i < STATES; i++) b[i] /= sum;
}

// Perform belief update: Bayes filter
void update_belief(int action, int observation) {
    for (int s_prime = 0; s_prime < STATES; s_prime++) {
        double sum = 0.0;
        for (int s = 0; s < STATES; s++) {
            sum += T[s][action][s_prime] * belief[s];
        }
        temp[s_prime] = O[s_prime][observation] * sum;
    }
    for (int s = 0; s < STATES; s++) {
        belief[s] = temp[s];
    }
    normalize(belief);
}

// Print current belief
void print_belief() {
    printf("Belief: [");
    for (int i = 0; i < STATES; i++) {
        printf(" %.4f", belief[i]);
    }
    printf(" ]\n");
}

int main() {
    printf("Initial:\n");
    print_belief();

    // Simulate: take action 'right' and observe 'z1'
    int action = 1;
    int observation = 1;
    printf("\nAfter action 'right' and observation 'z1':\n");
    update_belief(action, observation);
    print_belief();

    // Simulate another step: action 'left', observe 'z0'
    action = 0;
    observation = 0;
    printf("\nAfter action 'left' and observation 'z0':\n");
    update_belief(action, observation);
    print_belief();

    return 0;
}