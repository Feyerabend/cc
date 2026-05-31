/*
 * convolution.c
 *
 * Compile:  gcc -O2 -o convolution convolution.c
 * Run:      ./convolution
 *
 * Performs a single 2D cross-correlation of a 5x5 input with a 3x3
 * kernel, with zero-padding of 1 and stride of 1, producing a 5x5
 * output.
 *
 * No libraries. Everything is done with plain arrays and loops.
 * The goal is to make the arithmetic maximally visible.
 *
 * The output spatial dimension formula:
 *   out_size = (in_size + 2 * pad - kernel_size) / stride + 1
 */

#include <stdio.h>
#include <string.h>

#define IN_H    5
#define IN_W    5
#define K_H     3
#define K_W     3
#define PAD     1
#define STRIDE  1

#define OUT_H   ((IN_H + 2*PAD - K_H) / STRIDE + 1)
#define OUT_W   ((IN_W + 2*PAD - K_W) / STRIDE + 1)

#define PADDED_H (IN_H + 2*PAD)
#define PADDED_W (IN_W + 2*PAD)

static void print_matrix(const char *label, const float *m, int rows, int cols) {
    printf("%s:\n", label);
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            printf("%6.1f", m[i * cols + j]);
        }
        printf("\n");
    }
    printf("\n");
}

int main(void) {
    float input[IN_H * IN_W] = {
        1, 2, 3, 0, 1,
        0, 1, 2, 3, 1,
        1, 0, 1, 2, 0,
        2, 1, 0, 1, 2,
        0, 1, 2, 1, 0,
    };

    /* Sobel-x kernel: detects vertical edges (horizontal intensity change) */
    float kernel[K_H * K_W] = {
        -1,  0,  1,
        -2,  0,  2,
        -1,  0,  1,
    };

    /* Build zero-padded input */
    float padded[PADDED_H * PADDED_W];
    memset(padded, 0, sizeof(padded));

    for (int i = 0; i < IN_H; i++) {
        for (int j = 0; j < IN_W; j++) {
            padded[(i + PAD) * PADDED_W + (j + PAD)] = input[i * IN_W + j];
        }
    }

    /* Cross-correlation */
    float output[OUT_H * OUT_W];

    for (int i = 0; i < OUT_H; i++) {
        for (int j = 0; j < OUT_W; j++) {
            float sum = 0.0f;
            for (int m = 0; m < K_H; m++) {
                for (int n = 0; n < K_W; n++) {
                    int pi = i * STRIDE + m;
                    int pj = j * STRIDE + n;
                    sum += kernel[m * K_W + n] * padded[pi * PADDED_W + pj];
                }
            }
            output[i * OUT_W + j] = sum;
        }
    }

    print_matrix("Input", input, IN_H, IN_W);
    print_matrix("Kernel (Sobel-x)", kernel, K_H, K_W);
    print_matrix("Output (cross-correlation, pad=1, stride=1)", output, OUT_H, OUT_W);

    printf("Output size formula: (%d + 2*%d - %d) / %d + 1 = %d x %d\n", IN_H, PAD, K_H, STRIDE, OUT_H, OUT_W);

    return 0;
}
