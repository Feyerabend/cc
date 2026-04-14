#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <complex.h>   /* C99 complex arithmetic */

#define PI 3.14159265358979323846

/*
 * dft
 * Computes the N-point DFT of x[] and stores results in X[].
 * Complexity: O(N^2).
 * Both arrays must have length N.
 */
void dft(const double *x, double complex *X, int N) {
    for (int k = 0; k < N; k++) {
        X[k] = 0.0;
        for (int n = 0; n < N; n++) {
            double angle = -2.0 * PI * k * n / N;
            X[k] += x[n] * (cos(angle) + sin(angle) * I);
        }
    }
}

int main(void) {
    const int N  = 16;
    const double fs = 16.0;   /* Hz */

    double x[N];
    double complex X[N];

    /* Test signal: single 2 Hz tone */
    for (int n = 0; n < N; n++)
        x[n] = sin(2.0 * PI * 2.0 * n / fs);

    dft(x, X, N);

    printf("DFT output (magnitude):\n");
    for (int k = 0; k < N / 2; k++) {
        double freq = k * fs / N;
        double mag  = cabs(X[k]) / N;
        /* Print a simple bar chart */
        printf("  f = %5.1f Hz  |  mag = %.3f  ", freq, mag);
        int bars = (int)(mag * 40 + 0.5);
        for (int b = 0; b < bars; b++) putchar('#');
        putchar('\n');
    }
    return 0;
}
