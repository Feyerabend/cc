#include <stdio.h>
#include <math.h>

#define PI 3.14159265358979323846

/*
 * sample_signal
 * Samples a continuous sine wave at a given rate and stores
 * the result in the caller-supplied buffer.
 *
 * f_signal  : frequency of the sine wave (Hz)
 * fs        : sampling rate (Hz)
 * n_samples : number of samples to collect
 * out       : output buffer (length >= n_samples)
 */
void sample_signal(double f_signal, double fs, int n_samples, double *out) {
    double dt = 1.0 / fs;          /* period between samples */
    for (int n = 0; n < n_samples; n++) {
        double t = n * dt;
        out[n] = sin(2.0 * PI * f_signal * t);
    }
}

int main(void) {
    const double f_signal = 5.0;   /* Hz */
    const double fs_good  = 100.0; /* Hz--well above Nyquist */
    const double fs_alias = 8.0;   /* Hz--below Nyquist */
    const int    N        = 20;

    double buf[N];

    printf("-- Adequate sampling (fs = %.0f Hz)\n", fs_good);
    sample_signal(f_signal, fs_good, N, buf);
    for (int i = 0; i < N; i++)
        printf("  x[%2d] = %+.4f\n", i, buf[i]);

    printf("\n-- Aliased sampling (fs = %.0f Hz)\n", fs_alias);
    sample_signal(f_signal, fs_alias, N, buf);
    for (int i = 0; i < N; i++)
        printf("  x[%2d] = %+.4f\n", i, buf[i]);

    return 0;
}

