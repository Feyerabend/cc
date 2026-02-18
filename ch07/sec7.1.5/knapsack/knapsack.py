#!/usr/bin/env python3
"""
Knapsack Problem

This module demonstrates multiple algorithmic paradigms for solving
the 0/1 Knapsack Problem, from naive recursion to optimized dynamic programming.
"""

import time
from typing import List, Tuple, Dict, Optional


# PARADIGM 1: DIVIDE AND CONQUER (Naive Recursion)

def knapsack_recursive(W: int, wt: List[int], val: List[int], n: int) -> int:
    """
    Solve 0/1 Knapsack using pure recursion (divide and conquer).
    
    Algorithmic Paradigm: Divide and Conquer
    - Recursively try including/excluding each item
    - Exponential time due to overlapping subproblems
    
    Time Complexity: O(2^n) - exponential
    Space Complexity: O(n) - recursion stack depth
    
    Use: Education only - impractical for n > 25
    """
    # Base case: no items or no capacity
    if n == 0 or W == 0:
        return 0
    
    # If current item's weight exceeds capacity, skip it
    if wt[n-1] > W:
        return knapsack_recursive(W, wt, val, n-1)
    
    # Return maximum of including or excluding item
    else:
        include = val[n-1] + knapsack_recursive(W - wt[n-1], wt, val, n-1)
        exclude = knapsack_recursive(W, wt, val, n-1)
        return max(include, exclude)



# PARADIGM 2: DYNAMIC PROGRAMMING - TABULATION (Bottom-Up)

def knapsack_dp(W: int, wt: List[int], val: List[int], n: int) -> Tuple[int, List[int]]:
    """
    Solve 0/1 Knapsack using tabulation (bottom-up dynamic programming).
    
    Algorithmic Paradigm: Dynamic Programming (Bottom-Up)
    - Builds solution table iteratively from base cases
    - No recursion stack overhead
    - Easy to backtrack for solution reconstruction
    
    Time Complexity: O(n x W) - polynomial
    Space Complexity: O(n x W) - DP table
    
    Use: Production code (standard approach)
    """
    # Initialize DP table
    dp = [[0 for _ in range(W + 1)] for _ in range(n + 1)]
    
    # Build table in bottom-up manner
    for i in range(1, n + 1):
        for w in range(1, W + 1):
            # If current item fits in knapsack
            if wt[i-1] <= w:
                # Choose max of including or excluding item
                include = val[i-1] + dp[i-1][w - wt[i-1]]
                exclude = dp[i-1][w]
                dp[i][w] = max(include, exclude)
            else:
                # Item doesn't fit, carry forward previous best
                dp[i][w] = dp[i-1][w]
    
    # Backtrack to find selected items
    selected_items = []
    i, w = n, W
    
    while i > 0 and w > 0:
        # If value came from including item i
        if dp[i][w] != dp[i-1][w]:
            selected_items.append(i-1)  # 0-indexed
            w -= wt[i-1]
        i -= 1
    
    # Reverse to get items in order
    selected_items.reverse()
    
    return dp[n][W], selected_items


# TESTING

def validate_solution(W: int, wt: List[int], val: List[int], 
                     result: int, selected: List[int]) -> bool:
    """Validate that a knapsack solution is correct."""
    n = len(val)
    
    # Check all items exist
    if not all(0 <= i < n for i in selected):
        print("(-) Invalid item index in solution")
        return False
    
    # Check weight constraint
    total_weight = sum(wt[i] for i in selected)
    if total_weight > W:
        print(f"(-) Weight {total_weight} exceeds capacity {W}")
        return False
    
    # Check value matches
    total_value = sum(val[i] for i in selected)
    if total_value != result:
        print(f"(-) Value mismatch: {total_value} != {result}")
        return False
    
    print("(+) Solution validated successfully")
    return True




if __name__ == "__main__":
    # Example usage
    val = [60, 100, 120]
    wt = [10, 20, 30]
    W = 50
    n = len(val)
    
    print("KNAPSACK PROBLEM - ENHANCED IMPLEMENTATION\n")
    print(f"Items: {n}")
    print(f"Values: {val}")
    print(f"Weights: {wt}")
    print(f"Capacity: {W}")
    
    # Recursive approach (for comparison)
    print("\n1. RECURSIVE APPROACH (Divide & Conquer)")
    print("-"*60)
    start = time.time()
    result_rec = knapsack_recursive(W, wt, val, n)
    time_rec = time.time() - start
    print(f"Maximum value: {result_rec}")
    print(f"Time: {time_rec*1000:.4f}ms")
    print("Note: O(2^n) - exponential time")
    
    # Dynamic programming approach
    print("\n2. DYNAMIC PROGRAMMING (Tabulation)")
    print("-"*60)
    start = time.time()
    result_dp, selected = knapsack_dp(W, wt, val, n)
    time_dp = time.time() - start
    print(f"Maximum value: {result_dp}")
    print(f"Selected items (0-indexed): {selected}")
    print(f"Time: {time_dp*1000:.4f}ms")
    print("Note: O(n x W) - polynomial time")
    
    # Validation
    print("\n3. VALIDATION")
    print("-"*60)
    validate_solution(W, wt, val, result_dp, selected)
    
    # Show selected items details
    print("\n4. SOLUTION DETAILS")
    print("-"*60)
    total_weight = sum(wt[i] for i in selected)
    total_value = sum(val[i] for i in selected)
    print(f"Selected items:")
    for idx in selected:
        print(f"  Item {idx}: value={val[idx]}, weight={wt[idx]}")
    print(f"Total weight: {total_weight}/{W}")
    print(f"Total value: {total_value}")
    
    print("Done.")
