/*
 * forward_pass.c
 *
 * Compile:  gcc -O2 -o forward_pass forward_pass.c -lm
 * Run:      ./forward_pass
 *
 * Implements the forward pass for a small feedforward network
 * with architecture [2, 3, 1] entirely from first principles.
 *
 * This mirrors the Python version but makes the raw arithmetic
 * explicit: there is no framework, no autograd, no abstraction.
 * Each weight multiplication and addition is written out.
 *
 * Layer dimensions:
 *   Input:   2 units
 *   Hidden:  3 units  (ReLU activation)
 *   Output:  1 unit   (Sigmoid activation)
 */

#include <math.h>
#include <stdio.h>

#define INPUT_DIM  2
#define HIDDEN_DIM 3
#define OUTPUT_DIM 1

static double relu(double z) {
    return z > 0.0 ? z : 0.0;
}

static double sigmoid(double z) {
    return 1.0 / (1.0 + exp(-z));
}

static void matmul_add(
    const double *W, const double *b,
    const double *h_in, double *z_out,
    int rows, int cols)
{
    for (int i = 0; i < rows; i++) {
        double sum = b[i];
        for (int j = 0; j < cols; j++) {
            sum += W[i * cols + j] * h_in[j];
        }
        z_out[i] = sum;
    }
}

static void apply_activation(
    const double *z, double *h, int n,
    double (*act)(double))
{
    for (int i = 0; i < n; i++) {
        h[i] = act(z[i]);
    }
}

static double bce_loss(double y_hat, double y) {
    double eps = 1e-9;
    return -(y * log(y_hat + eps) + (1.0 - y) * log(1.0 - y_hat + eps));
}

int main(void) {
    /*
     * Weights for hidden layer: shape [HIDDEN_DIM, INPUT_DIM]
     * Stored in row-major order. W1[i][j] = W1[i * INPUT_DIM + j]
     */
    double W1[HIDDEN_DIM * INPUT_DIM] = {
         0.5, -0.2,
        -0.3,  0.8,
         0.1,  0.4
    };
    double b1[HIDDEN_DIM] = { 0.0, 0.1, -0.1 };

    /* Weights for output layer: shape [OUTPUT_DIM, HIDDEN_DIM] */
    double W2[OUTPUT_DIM * HIDDEN_DIM] = { 0.6, -0.5, 0.3 };
    double b2[OUTPUT_DIM] = { 0.05 };

    double x[INPUT_DIM] = { 0.5, -0.3 };
    double y = 1.0;

    /* Hidden layer */
    double z1[HIDDEN_DIM];
    double h1[HIDDEN_DIM];

    matmul_add(W1, b1, x, z1, HIDDEN_DIM, INPUT_DIM);
    apply_activation(z1, h1, HIDDEN_DIM, relu);

    /* Output layer */
    double z2[OUTPUT_DIM];
    double h2[OUTPUT_DIM];

    matmul_add(W2, b2, h1, z2, OUTPUT_DIM, HIDDEN_DIM);
    apply_activation(z2, h2, OUTPUT_DIM, sigmoid);

    double loss = bce_loss(h2[0], y);

    printf("Input:          [%.3f, %.3f]\n", x[0], x[1]);
    printf("z1 (pre-act):   [%.4f, %.4f, %.4f]\n", z1[0], z1[1], z1[2]);
    printf("h1 (after ReLU):[%.4f, %.4f, %.4f]\n", h1[0], h1[1], h1[2]);
    printf("z2 (pre-act):   [%.4f]\n", z2[0]);
    printf("y_hat (sigmoid):[%.6f]\n", h2[0]);
    printf("Target y:        %.1f\n", y);
    printf("BCE loss:        %.6f\n", loss);

    return 0;
}
