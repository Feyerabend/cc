#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define MAX_POINTS 100
#define MAX_ITER 100
#define DIM 2
#define K 3

typedef struct {
    double x[DIM];
    int cluster;
} Point;

typedef struct {
    double x[DIM];
} Centroid;

double distance(double *a, double *b) {
    double sum = 0.0;
    for (int i = 0; i < DIM; i++)
        sum += (a[i] - b[i]) * (a[i] - b[i]);
    return sqrt(sum);
}

void assign_clusters(Point *points, Centroid *centroids, int n) {
    for (int i = 0; i < n; i++) {
        double min_dist = INFINITY;
        int cluster = -1;
        for (int k = 0; k < K; k++) {
            double d = distance(points[i].x, centroids[k].x);
            if (d < min_dist) {
                min_dist = d;
                cluster = k;
            }
        }
        points[i].cluster = cluster;
    }
}

void update_centroids(Point *points, Centroid *centroids, int n) {
    int count[K] = {0};
    double sum[K][DIM] = {0};

    for (int i = 0; i < n; i++) {
        int c = points[i].cluster;
        for (int d = 0; d < DIM; d++)
            sum[c][d] += points[i].x[d];
        count[c]++;
    }

    for (int k = 0; k < K; k++) {
        if (count[k] == 0) continue; // avoid divide-by-zero
        for (int d = 0; d < DIM; d++)
            centroids[k].x[d] = sum[k][d] / count[k];
    }
}

int main() {
    srand(time(NULL));
    int n = 10;
    Point points[MAX_POINTS] = {
        {{1.0,  2.0}},
        {{1.5,  1.8}},
        {{5.0,  8.0}},
        {{8.0,  8.0}},
        {{1.0,  0.6}},
        {{9.0, 11.0}},
        {{8.0,  2.0}},
        {{10.0, 2.0}},
        {{9.0,  3.0}},
        {{4.5,  6.0}}
    };

    Centroid centroids[K];
    for (int k = 0; k < K; k++) {
        int idx = rand() % n;
        for (int d = 0; d < DIM; d++)
            centroids[k].x[d] = points[idx].x[d];
    }

    for (int iter = 0; iter < MAX_ITER; iter++) {
        int old_assignments[MAX_POINTS];
        for (int i = 0; i < n; i++)
            old_assignments[i] = points[i].cluster;

        assign_clusters(points, centroids, n);
        update_centroids(points, centroids, n);

        int changed = 0;
        for (int i = 0; i < n; i++)
            if (points[i].cluster != old_assignments[i])
                changed++;

        if (changed == 0) break;
    }

    for (int i = 0; i < n; i++) {
        printf("Point (%.2f, %.2f) => Cluster %d\n",
            points[i].x[0], points[i].x[1], points[i].cluster);
    }

    return 0;
}


