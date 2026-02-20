def dfs(graph, vertex, visited):
    print(vertex, end=" ")
    visited.add(vertex)

    for neighbor in graph[vertex]:
        if neighbor not in visited:
            dfs(graph, neighbor, visited)

graph = {
    0: [1, 2],
    1: [0, 3, 4],
    2: [0, 3],
    3: [1, 2, 4],
    4: [1, 3]
}

visited = set()
print("Depth-First Search (DFS) traversal starting from vertex 0:")
dfs(graph, 0, visited)
print()