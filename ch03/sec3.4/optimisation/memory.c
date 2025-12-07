#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>

#define ROWS 1000
#define COLS 1000

// Row-major traversal (cache-friendly)
void sum_row_major(int matrix[ROWS][COLS], long long *result) {
    *result = 0;
    for (int i = 0; i < ROWS; i++) {
        for (int j = 0; j < COLS; j++) {
            *result += matrix[i][j];
        }
    }
}

// Column-major traversal (cache-unfriendly)
void sum_col_major(int matrix[ROWS][COLS], long long *result) {
    *result = 0;
    for (int j = 0; j < COLS; j++) {
        for (int i = 0; i < ROWS; i++) {
            *result += matrix[i][j];
        }
    }
}

// Blocked/tiled traversal (optimised for cache)
void sum_blocked(int matrix[ROWS][COLS], long long *result) {
    *result = 0;
    const int BLOCK_SIZE = 64;
    
    for (int ii = 0; ii < ROWS; ii += BLOCK_SIZE) {
        for (int jj = 0; jj < COLS; jj += BLOCK_SIZE) {
            for (int i = ii; i < ii + BLOCK_SIZE && i < ROWS; i++) {
                for (int j = jj; j < jj + BLOCK_SIZE && j < COLS; j++) {
                    *result += matrix[i][j];
                }
            }
        }
    }
}

// Memory alignment example
typedef struct {
    char a;      // 1 byte
    int b;       // 4 bytes
    char c;      // 1 byte
} UnalignedStruct;  // Typically 12 bytes due to padding

typedef struct {
    int b;       // 4 bytes
    char a;      // 1 byte
    char c;      // 1 byte
} AlignedStruct;    // Typically 8 bytes - better memory usage

int main() {
    int (*matrix)[COLS] = malloc(sizeof(int[ROWS][COLS]));
    
    // Initialize matrix
    for (int i = 0; i < ROWS; i++) {
        for (int j = 0; j < COLS; j++) {
            matrix[i][j] = (i + j) % 100;
        }
    }

    long long result;
    clock_t start, end;

    printf("-- Memory Access Pattern Optimisation --\n\n");

    // Row-major (cache-friendly)
    start = clock();
    sum_row_major(matrix, &result);
    end = clock();
    printf("Row-major (cache-friendly): %lld\n", result);
    printf("Time: %.6f seconds\n\n", (double)(end - start) / CLOCKS_PER_SEC);

    // Column-major (cache-unfriendly)
    start = clock();
    sum_col_major(matrix, &result);
    end = clock();
    printf("Column-major (cache-unfriendly): %lld\n", result);
    printf("Time: %.6f seconds\n\n", (double)(end - start) / CLOCKS_PER_SEC);

    // Blocked (optimised)
    start = clock();
    sum_blocked(matrix, &result);
    end = clock();
    printf("Blocked/tiled (optimised): %lld\n", result);
    printf("Time: %.6f seconds\n\n", (double)(end - start) / CLOCKS_PER_SEC);

    printf("Memory alignment impact:\n");
    printf("UnalignedStruct size: %zu bytes\n", sizeof(UnalignedStruct));
    printf("AlignedStruct size: %zu bytes\n", sizeof(AlignedStruct));
    printf("Memory saved per struct: %zu bytes\n", 
           sizeof(UnalignedStruct) - sizeof(AlignedStruct));

    free(matrix);
    return 0;
}
