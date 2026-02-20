#include <stdio.h>
#include <stdbool.h>

#define V 5  // num of vertices

void dfs(int graph[V][V], int vertex, bool visited[]) {
    printf("%d ", vertex);
    visited[vertex] = true;

    for (int i = 0; i < V; i++) {
        if (graph[vertex][i] == 1 && !visited[i]) {
            dfs(graph, i, visited);
        }
    }
}

int main() {
    int graph[V][V] = {
        {0, 1, 1, 0, 0},
        {1, 0, 0, 1, 1},
        {1, 0, 0, 1, 0},
        {0, 1, 1, 0, 1},
        {0, 1, 0, 1, 0}
    };

    bool visited[V] = {false};

    printf("Depth-First Search (DFS) traversal starting from vertex 0:\n");
    dfs(graph, 0, visited);
    printf("\n");

    return 0;
}