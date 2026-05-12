"""
GOFAI (Good Old-Fashioned AI) 8-Puzzle Solver
Demonstrates classic AI search algorithms

Key GOFAI Concepts Demonstrated:
1. State space search
2. Breadth-First Search (BFS) - guarantees optimal solution
3. Depth-First Search (DFS) - explores deeply first
4. A* Search with heuristics - informed search
5. Problem representation as states and operators
6. Systematic exploration without learning
"""

from collections import deque
import heapq
import time

class EightPuzzle:
    """
    Represents the 8-puzzle problem state and operations
    
    The puzzle is represented as a 3x3 grid:
    1 2 3
    4 5 6  
    7 8 _  (where _ is the empty space, represented as 0)
    """
    
    GOAL_STATE = (1, 2, 3, 4, 5, 6, 7, 8, 0)
    
    def __init__(self, initial_state):
        self.initial_state = tuple(initial_state)
        self.goal_state = self.GOAL_STATE
    
    def display_state(self, state):
        """Display the puzzle state in a readable 3x3 format"""
        print("┌───────────┐")
        for i in range(3):
            row = state[i*3:(i+1)*3]
            display_row = [str(x) if x != 0 else ' ' for x in row]
            print(f"│ {display_row[0]} │ {display_row[1]} │ {display_row[2]} │")
            if i < 2:
                print("├───┼───┼───┤")
        print("└───┘───┘───┘")
    
    def get_neighbors(self, state):
        """
        Generate all possible next states from current state
        The empty space (0) can move up, down, left, or right
        """
        neighbors = []
        zero_idx = state.index(0)
        row, col = zero_idx // 3, zero_idx % 3
        
        # Possible moves: up, down, left, right
        moves = [
            (-1, 0, "UP"),    # Move empty space up
            (1, 0, "DOWN"),   # Move empty space down  
            (0, -1, "LEFT"),  # Move empty space left
            (0, 1, "RIGHT")   # Move empty space right
        ]
        
        for dr, dc, direction in moves:
            new_row, new_col = row + dr, col + dc
            
            # Check if move is within bounds
            if 0 <= new_row < 3 and 0 <= new_col < 3:
                new_idx = new_row * 3 + new_col
                
                # Create new state by swapping empty space with target
                new_state = list(state)
                new_state[zero_idx], new_state[new_idx] = new_state[new_idx], new_state[zero_idx]
                
                neighbors.append((tuple(new_state), direction))
        
        return neighbors
    
    def manhattan_distance(self, state):
        """
        Heuristic function: Manhattan distance
        Sum of distances each tile is from its goal position
        """
        distance = 0
        for i, tile in enumerate(state):
            if tile != 0:  # Don't count empty space
                # Current position
                curr_row, curr_col = i // 3, i % 3
                # Goal position (tile value - 1 gives goal index)
                goal_idx = tile - 1
                goal_row, goal_col = goal_idx // 3, goal_idx % 3
                # Manhattan distance
                distance += abs(curr_row - goal_row) + abs(curr_col - goal_col)
        return distance
    
    def is_solvable(self, state):
        """
        Check if puzzle state is solvable
        An 8-puzzle is solvable if the number of inversions is even
        """
        # Remove the empty space and count inversions
        tiles = [x for x in state if x != 0]
        inversions = 0
        for i in range(len(tiles)):
            for j in range(i + 1, len(tiles)):
                if tiles[i] > tiles[j]:
                    inversions += 1
        return inversions % 2 == 0

class PuzzleSolver:
    """Collection of different search algorithms for solving the 8-puzzle"""
    
    def __init__(self, puzzle):
        self.puzzle = puzzle
        self.stats = {}
    
    def breadth_first_search(self):
        """
        BFS: Explores all states at depth d before exploring depth d+1
        Guarantees shortest solution but uses lots of memory
        """
        print("Running Breadth-First Search...")
        start_time = time.time()
        
        queue = deque([(self.puzzle.initial_state, [])])
        visited = {self.puzzle.initial_state}
        nodes_explored = 0
        
        while queue:
            current_state, path = queue.popleft()
            nodes_explored += 1
            
            if current_state == self.puzzle.goal_state:
                end_time = time.time()
                self.stats['BFS'] = {
                    'solution_length': len(path),
                    'nodes_explored': nodes_explored,
                    'time_taken': end_time - start_time,
                    'path': path
                }
                return current_state, path
            
            for neighbor_state, move in self.puzzle.get_neighbors(current_state):
                if neighbor_state not in visited:
                    visited.add(neighbor_state)
                    queue.append((neighbor_state, path + [move]))
        
        return None, []
    
    def depth_first_search(self, max_depth=20):
        """
        DFS: Explores deeply before backtracking
        Uses less memory but may find suboptimal solutions
        """
        print("Running Depth-First Search...")
        start_time = time.time()
        
        stack = [(self.puzzle.initial_state, [])]
        visited = set()
        nodes_explored = 0
        
        while stack:
            current_state, path = stack.pop()
            
            if len(path) > max_depth:  # Depth limit
                continue
                
            if current_state in visited:
                continue
                
            visited.add(current_state)
            nodes_explored += 1
            
            if current_state == self.puzzle.goal_state:
                end_time = time.time()
                self.stats['DFS'] = {
                    'solution_length': len(path),
                    'nodes_explored': nodes_explored,
                    'time_taken': end_time - start_time,
                    'path': path
                }
                return current_state, path
            
            # Add neighbors to stack (reversed for consistent ordering)
            neighbors = self.puzzle.get_neighbors(current_state)
            for neighbor_state, move in reversed(neighbors):
                if neighbor_state not in visited:
                    stack.append((neighbor_state, path + [move]))
        
        return None, []
    
    def a_star_search(self):
        """
        A*: Uses heuristic to guide search toward goal
        Combines actual cost (g) with heuristic estimate (h)
        f(n) = g(n) + h(n)
        """
        print("Running A* Search...")
        start_time = time.time()
        
        # Priority queue: (f_score, g_score, state, path)
        heap = [(0, 0, self.puzzle.initial_state, [])]
        visited = set()
        nodes_explored = 0
        
        while heap:
            f_score, g_score, current_state, path = heapq.heappop(heap)
            
            if current_state in visited:
                continue
                
            visited.add(current_state)
            nodes_explored += 1
            
            if current_state == self.puzzle.goal_state:
                end_time = time.time()
                self.stats['A*'] = {
                    'solution_length': len(path),
                    'nodes_explored': nodes_explored,
                    'time_taken': end_time - start_time,
                    'path': path
                }
                return current_state, path
            
            for neighbor_state, move in self.puzzle.get_neighbors(current_state):
                if neighbor_state not in visited:
                    new_g_score = g_score + 1
                    h_score = self.puzzle.manhattan_distance(neighbor_state)
                    new_f_score = new_g_score + h_score
                    
                    heapq.heappush(heap, (
                        new_f_score, 
                        new_g_score, 
                        neighbor_state, 
                        path + [move]
                    ))
        
        return None, []
    
    def compare_algorithms(self):
        """Run all algorithms and compare their performance"""
        print("Comparing Search Algorithms")
        print("=" * 50)
        
        # Check if puzzle is solvable first
        if not self.puzzle.is_solvable(self.puzzle.initial_state):
            print("This puzzle configuration is not solvable!")
            return
        
        print("Initial State:")
        self.puzzle.display_state(self.puzzle.initial_state)
        print("\nGoal State:")
        self.puzzle.display_state(self.puzzle.goal_state)
        print()
        
        # Run all algorithms
        self.breadth_first_search()
        self.depth_first_search()
        self.a_star_search()
        
        # Display comparison
        print("\nAlgorithm Comparison:")
        print("-" * 60)
        print(f"{'Algorithm':<12} {'Steps':<8} {'Nodes':<8} {'Time (s)':<10}")
        print("-" * 60)
        
        for algo, stats in self.stats.items():
            print(f"{algo:<12} {stats['solution_length']:<8} "
                  f"{stats['nodes_explored']:<8} {stats['time_taken']:<10.4f}")
    
    def show_solution(self, algorithm='A*'):
        """Display step-by-step solution"""
        if algorithm not in self.stats:
            print(f"{algorithm} has not been run yet!")
            return
        
        print(f"\n{algorithm} Solution Steps:")
        print("=" * 40)
        
        current_state = self.puzzle.initial_state
        self.puzzle.display_state(current_state)
        
        for i, move in enumerate(self.stats[algorithm]['path'], 1):
            print(f"\nStep {i}: Move {move}")
            # Apply the move to get next state
            for next_state, next_move in self.puzzle.get_neighbors(current_state):
                if next_move == move:
                    current_state = next_state
                    break
            self.puzzle.display_state(current_state)

def create_random_puzzle(moves=20):
    """Create a random solvable puzzle by scrambling from goal state"""
    import random
    
    puzzle = EightPuzzle(EightPuzzle.GOAL_STATE)
    current_state = EightPuzzle.GOAL_STATE
    
    for _ in range(moves):
        neighbors = puzzle.get_neighbors(current_state)
        current_state, _ = random.choice(neighbors)
    
    return current_state

# Example usage and demonstrations
def demo_easy_puzzle():
    """Demo with an easy puzzle (just a few moves from solution)"""
    print("1: Easy Puzzle (2 moves from solution)")
    print("=" * 50)
    
    # This puzzle is 2 moves away from solution
    initial_state = (1, 2, 3, 4, 5, 6, 0, 7, 8)
    puzzle = EightPuzzle(initial_state)
    solver = PuzzleSolver(puzzle)
    
    solver.compare_algorithms()
    solver.show_solution('A*')

def demo_medium_puzzle():
    """Demo with a medium difficulty puzzle"""
    print("\n\n2: Medium Puzzle")
    print("=" * 50)
    
    # This puzzle requires more moves
    initial_state = (1, 2, 3, 4, 0, 5, 7, 8, 6)
    puzzle = EightPuzzle(initial_state)
    solver = PuzzleSolver(puzzle)
    
    solver.compare_algorithms()

def interactive_demo():
    """Let students create their own puzzle"""
    print("\n\nDEMO: Create Your Own Puzzle!")
    print("=" * 50)
    print("Enter 9 numbers (0-8, where 0 is the empty space)")
    print("Example: 1 2 3 4 0 5 7 8 6")
    
    while True:
        try:
            user_input = input("Enter puzzle state: ").strip().split()
            if len(user_input) != 9:
                print("Please enter exactly 9 numbers!")
                continue
            
            state = tuple(int(x) for x in user_input)
            
            # Validate input
            if set(state) != set(range(9)):
                print("Please use each number 0-8 exactly once!")
                continue
            
            puzzle = EightPuzzle(state)
            if not puzzle.is_solvable(state):
                print("This puzzle is not solvable! Try another configuration.")
                continue
            
            solver = PuzzleSolver(puzzle)
            solver.compare_algorithms()
            
            show_steps = input("\nShow step-by-step solution? (y/n): ")
            if show_steps.lower().startswith('y'):
                solver.show_solution('A*')
            
            break
            
        except ValueError:
            print("Please enter valid numbers!")

if __name__ == "__main__":
    print("GOFAI 8-Puzzle Solver Demonstration")
    print("=" * 50)
    print("This demonstrates classical AI search techniques:")
    print("- State space representation")
    print("- Systematic search algorithms (BFS, DFS, A*)")
    print("- Heuristic-guided search")
    print("- No machine learning - pure algorithmic problem solving")
    
    # Run demonstrations
    demo_easy_puzzle()
    demo_medium_puzzle()
    
    # Interactive session
    print("\n" + "="*60)
    try_interactive = input("\nWould you like to try your own puzzle? (y/n): ")
    if try_interactive.lower().startswith('y'):
        interactive_demo()
    
    print("\nGOFAI Takeaways:")
    print("- Problems represented as states and operators")
    print("- Systematic exploration of solution space")
    print("- Different algorithms have different trade-offs")
    print("- Heuristics can guide search without learning")
    print("- Deterministic, explainable problem-solving")
    print("- No training data needed - just problem definition")


