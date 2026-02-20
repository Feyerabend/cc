#include <stdio.h>
#include <stdbool.h>

#define V 5  // num of vertices

void bfs(int graph[V][V], int start) {
    bool visited[V] = {false};
    int queue[V], front = 0, rear = 0;

    visited[start] = true;
    queue[rear++] = start;

    printf("Breadth-First Search (BFS) traversal starting from vertex %d:\n", start);

    while (front < rear) {
        int current = queue[front++];
        printf("%d ", current);

        for (int i = 0; i < V; i++) {
            if (graph[current][i] == 1 && !visited[i]) {
                visited[i] = true;
                queue[rear++] = i;
            }
        }
    }
    printf("\n");
}

int main() {
    int graph[V][V] = {
        {0, 1, 1, 0, 0},
        {1, 0, 0, 1, 1},
        {1, 0, 0, 1, 0},
        {0, 1, 1, 0, 1},
        {0, 1, 0, 1, 0}
    };

    bfs(graph, 0);
    return 0;
}