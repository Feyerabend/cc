/*
 * attention.c
 *
 * Compile:  gcc -O2 -o attention attention.c -lm
 * Run:      ./attention
 *
 * Computes scaled dot-product attention for a short sequence
 * (n=4 tokens, d_k=3 dimensions) with no external libraries.
 *
 * Steps performed:
 *   1. Compute scores  S = Q * K^T
 *   2. Scale           S = S / sqrt(d_k)
 *   3. Softmax         W = softmax(S)  row-wise
 *   4. Output          O = W * V
 *
 * All matrices are stored in row-major order.
 */

#include <math.h>
#include <stdio.h>

#define N    4
#define D_K  3
#define D_V  3


static void print_matrix(const char *label, const float *m, int rows, int cols) {
    printf("%s:\n", label);
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            printf("%8.4f", m[i * cols + j]);
        }
        printf("\n");
    }
    printf("\n");
}

static void matmul(
    const float *A, const float *B, float *C,
    int m, int k, int n)
{
    for (int i = 0; i < m; i++) {
        for (int j = 0; j < n; j++) {
            float sum = 0.0f;
            for (int p = 0; p < k; p++) {
                sum += A[i * k + p] * B[p * n + j];
            }
            C[i * n + j] = sum;
        }
    }
}

static void softmax_rows(float *A, int rows, int cols) {
    for (int i = 0; i < rows; i++) {
        float max_val = A[i * cols];
        for (int j = 1; j < cols; j++) {
            if (A[i * cols + j] > max_val) {
                max_val = A[i * cols + j];
            }
        }
        float sum = 0.0f;
        for (int j = 0; j < cols; j++) {
            A[i * cols + j] = expf(A[i * cols + j] - max_val);
            sum += A[i * cols + j];
        }
        for (int j = 0; j < cols; j++) {
            A[i * cols + j] /= sum;
        }
    }
}

int main(void) {
    float Q[N * D_K] = {
        1.0f,  0.5f, -0.2f,
        0.3f,  1.2f,  0.1f,
       -0.5f,  0.8f,  0.9f,
        0.7f, -0.3f,  0.4f,
    };

    float K[N * D_K] = {
        0.9f,  0.4f, -0.1f,
        0.2f,  1.1f,  0.3f,
       -0.4f,  0.7f,  1.0f,
        0.6f, -0.2f,  0.5f,
    };

    float V[N * D_V] = {
        1.0f, 0.0f, 0.0f,
        0.0f, 1.0f, 0.0f,
        0.0f, 0.0f, 1.0f,
        0.5f, 0.5f, 0.5f,
    };

    /* K^T: shape (D_K, N) */
    float K_T[D_K * N];
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < D_K; j++) {
            K_T[j * N + i] = K[i * D_K + j];
        }
    }

    /* Scores S = Q * K^T: shape (N, N) */
    float S[N * N];
    matmul(Q, K_T, S, N, D_K, N);

    /* Scale by 1 / sqrt(d_k) */
    float scale = 1.0f / sqrtf((float) D_K);
    for (int idx = 0; idx < N * N; idx++) {
        S[idx] *= scale;
    }

    print_matrix("Scaled scores (Q K^T / sqrt(d_k))", S, N, N);

    /* Softmax row-wise */
    softmax_rows(S, N, N);
    print_matrix("Attention weights (softmax)", S, N, N);

    /* Output O = W * V: shape (N, D_V) */
    float O[N * D_V];
    matmul(S, V, O, N, N, D_V);
    print_matrix("Output (W V)", O, N, D_V);

    /* Row sums of attention weights should all be 1 */
    printf("Row sums of attention weights (should all be 1.0):\n");
    for (int i = 0; i < N; i++) {
        float row_sum = 0.0f;
        for (int j = 0; j < N; j++) {
            row_sum += S[i * N + j];
        }
        printf("  row %d: %.6f\n", i, row_sum);
    }

    return 0;
}
