from collections import deque

def bfs(graph, start):
    visited = set()
    queue = deque([start])

    print("Breadth-First Search (BFS) traversal starting from vertex", start)

    while queue:
        vertex = queue.popleft()
        if vertex not in visited:
            print(vertex, end=" ")
            visited.add(vertex)
            queue.extend(neighbor for neighbor in graph[vertex] if neighbor not in visited)

    print()

graph = {
    0: [1, 2],
    1: [0, 3, 4],
    2: [0, 3],
    3: [1, 2, 4],
    4: [1, 3]
}

bfs(graph, 0)