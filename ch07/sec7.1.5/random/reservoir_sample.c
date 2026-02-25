/*
 * Reservoir Sampling
 * ==================
 * Uniformly sample k items from a stream of unknown size n,
 * in a single pass using O(k) memory.
 *
 *   Algorithm:
 *
 *   After seeing i+1 elements, every element has exactly k/(i+1)
 *   probability of being in the reservoir.
 *
 *   Base case  (i < k): all items go in, probability = 1 = k/k
 *   Inductive step: item i is chosen with probability k/i.
 *   An existing item survives if it is NOT the one evicted: (k-1)/k.
 *   Combined, each prior item's new probability = k/(i-1) * ... = k/i.
 *
 *   Every item ends up with equal probability k/n in the final sample.
 *
 *   Time complexity: O(n)
 *   Space complexity: O(k)
 *
 *   Advantages:
 *   Works on streaming data -- n is never needed in advance.
 *   The randomization is load-bearing for correctness, not just a
 *   performance hedge (contrast with randomized quicksort).
 *   Used in databases, log sampling, and A/B testing infrastructure.
 */

#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>

/* Fill reservoir[0..k-1] with a uniform random sample from stream[0..n-1]. */
void reservoir_sample(const int *stream, int n, int *reservoir, int k) {
    int i, j;

    for (i = 0; i < n; i++) {
        if (i < k) {
            reservoir[i] = stream[i];
        } else {
            j = rand() % (i + 1);
            if (j < k)
                reservoir[j] = stream[i];
        }
    }
}

int main(void) {
    int stream[] = {10, 20, 30, 40, 50, 60, 70, 80, 90, 100};
    int n = sizeof(stream) / sizeof(stream[0]);
    int k = 4;
    int reservoir[4];
    int i;

    srand((unsigned int)time(NULL) ^ (unsigned int)getpid());

    reservoir_sample(stream, n, reservoir, k);

    printf("Stream (%d elements): ", n);
    for (i = 0; i < n; i++)
        printf("%d ", stream[i]);

    printf("\nSample (%d elements): ", k);
    for (i = 0; i < k; i++)
        printf("%d ", reservoir[i]);

    printf("\n");
    return 0;
}
