#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <float.h> // For DBL_MAX
#include <time.h>


typedef struct {
    double x;       // Feature 1 (e.g., Average Order Value)
    double y;       // Feature 2 (e.g., Number of Orders)
    int cluster_id; // cluster this point belongs to
} Point;

double euclidean_distance(Point p1, Point p2) {
    return sqrt(pow(p1.x - p2.x, 2) + pow(p1.y - p2.y, 2));
}

void initialize_centroids(Point *centroids, int k, Point *data, int num_points) {
    // A simple approach: pick k random data points as initial centroids
    // In a real application, you might use k-means++ for better initialization
    for (int i = 0; i < k; i++) {
        int random_index = rand() % num_points;
        centroids[i] = data[random_index];
        centroids[i].cluster_id = i; // Assign a temporary cluster_id for centroids
    }
}

int assign_to_clusters(Point *data, int num_points, Point *centroids, int k) {
    int assignments_changed = 0;
    for (int i = 0; i < num_points; i++) {
        double min_dist = DBL_MAX;
        int closest_centroid_id = -1;

        for (int j = 0; j < k; j++) {
            double dist = euclidean_distance(data[i], centroids[j]);
            if (dist < min_dist) {
                min_dist = dist;
                closest_centroid_id = j;
            }
        }
        if (data[i].cluster_id != closest_centroid_id) {
            data[i].cluster_id = closest_centroid_id;
            assignments_changed = 1;
        }
    }
    return assignments_changed;
}

void update_centroids(Point *data, int num_points, Point *centroids, int k) {
    // Array to store sum of x and y for each cluster, and count of points in each cluster
    double *sum_x = (double *)calloc(k, sizeof(double));
    double *sum_y = (double *)calloc(k, sizeof(double));
    int *counts = (int *)calloc(k, sizeof(int));

    if (!sum_x || !sum_y || !counts) {
        fprintf(stderr, "Memory allocation failed in update_centroids.\n");
        exit(EXIT_FAILURE);
    }

    // Sum up coordinates for each cluster
    for (int i = 0; i < num_points; i++) {
        int cluster_id = data[i].cluster_id;
        if (cluster_id >= 0 && cluster_id < k) {
            sum_x[cluster_id] += data[i].x;
            sum_y[cluster_id] += data[i].y;
            counts[cluster_id]++;
        }
    }

    // calc new centroid positions
    for (int i = 0; i < k; i++) {
        if (counts[i] > 0) { // avoid division by zero if a cluster is empty
            centroids[i].x = sum_x[i] / counts[i];
            centroids[i].y = sum_y[i] / counts[i];
        }
        // if a cluster becomes empty, a common strategy is to reinitialise its centroid,
        // but for simplicity, we'll just leave it where it was.
    }

    free(sum_x);
    free(sum_y);
    free(counts);
}

void kmeans(Point *data, int num_points, int k, int max_iterations) {
    Point *centroids = (Point *)malloc(k * sizeof(Point));
    if (!centroids) {
        fprintf(stderr, "Memory allocation failed for centroids.\n");
        exit(EXIT_FAILURE);
    }

    // 1. Init centroids
    initialize_centroids(centroids, k, data, num_points);
    printf("Initial Centroids:\n");
    for(int i=0; i<k; ++i) {
        printf("C%d: (%.2f, %.2f)\n", i, centroids[i].x, centroids[i].y);
    }

    int iteration = 0;
    int assignments_changed;

    do {
        iteration++;
        printf("\n--- Iteration %d ---\n", iteration);

        // 2. Assign points to clusters
        assignments_changed = assign_to_clusters(data, num_points, centroids, k);
        printf("Assignments changed: %s\n", assignments_changed ? "Yes" : "No");

        // 3. Update centroids
        update_centroids(data, num_points, centroids, k);
        printf("Updated Centroids:\n");
        for(int i=0; i<k; ++i) {
            printf("C%d: (%.2f, %.2f)\n", i, centroids[i].x, centroids[i].y);
        }

    } while (assignments_changed && iteration < max_iterations);

    printf("\nK-means converged after %d iterations (or reached max iterations).\n", iteration);
    printf("\nFinal Cluster Assignments:\n");
    for (int i = 0; i < num_points; i++) {
        printf("Point (%.2f, %.2f) -> Cluster %d\n", data[i].x, data[i].y, data[i].cluster_id);
    }

    printf("\nFinal Centroids:\n");
    for (int i = 0; i < k; i++) {
        printf("Cluster %d Centroid: (%.2f, %.2f)\n", i, centroids[i].x, centroids[i].y);
    }

    free(centroids);
}

int main() {
    // seed random number generator for centroid init
    srand(time(NULL)); // Requires #include <time.h>

    // Example data
    // Customer ID | Average Order Value (AOV) | Number of Orders (NO)
    Point customer_data[] = {
        {50,   3, -1},   // -1 indicates unassigned initially
        {60,   2, -1},
        {200, 10, -1},
        {220,  9, -1},
        {70,   4, -1},
        {30,   2, -1},
        {180,  8, -1},
        {40,   3, -1},
        {210, 11, -1},
        {65,   5, -1}
    };
    int num_customers = sizeof(customer_data) / sizeof(Point);
    int k = 3; // We want 3 customer segments
    int max_iterations = 100; // Cap on iterations to prevent infinite loops

    printf("Starting K-means with %d points and %d clusters.\n", num_customers, k);
    kmeans(customer_data, num_customers, k, max_iterations);

    return 0;
}

