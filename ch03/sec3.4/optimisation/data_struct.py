import time
from collections import deque, defaultdict, Counter
import bisect

def benchmark_list_vs_set():
    print("--- List vs Set for Membership Testing ---\n")
    
    n = 10000
    data = list(range(n))
    data_set = set(data)
    lookups = [i for i in range(0, n, 10)] + [n + 1000]  # Include non-existent
    
    # UNOPTIMISED: Using list
    start = time.time()
    found_count = sum(1 for item in lookups if item in data)
    time1 = time.time() - start
    print(f"List membership (O(n)): {time1:.6f}s")
    
    # OPTIMISED: Using set
    start = time.time()
    found_count = sum(1 for item in lookups if item in data_set)
    time2 = time.time() - start
    print(f"Set membership (O(1)): {time2:.6f}s ({time1/time2:.1f}x faster)\n")


def benchmark_list_operations():
    print("--- List Operations Optimisation ---\n")
    
    n = 10000
    
    # UNOPTIMISED: Insert at beginning of list
    start = time.time()
    data = []
    for i in range(n):
        data.insert(0, i)
    time1 = time.time() - start
    print(f"Insert at beginning (list): {time1:.4f}s")
    
    # OPTIMISED: Use deque for beginning insertions
    start = time.time()
    data = deque()
    for i in range(n):
        data.appendleft(i)
    time2 = time.time() - start
    print(f"Insert at beginning (deque): {time2:.4f}s ({time1/time2:.1f}x faster)")
    
    # Append is fast for both
    start = time.time()
    data = []
    for i in range(n):
        data.append(i)
    time3 = time.time() - start
    print(f"Append at end (list): {time3:.4f}s\n")


def benchmark_dict_operations():
    print("--- Dictionary Operations ---\n")
    
    data = [(f"key_{i}", i) for i in range(10000)]
    
    # UNOPTIMISED: Checking key existence with exception
    start = time.time()
    result = {}
    for key, value in data:
        try:
            result[key] += value
        except KeyError:
            result[key] = value
    time1 = time.time() - start
    print(f"Using try/except: {time1:.4f}s")
    
    # BETTER: Using get() with default
    start = time.time()
    result = {}
    for key, value in data:
        result[key] = result.get(key, 0) + value
    time2 = time.time() - start
    print(f"Using get(): {time2:.4f}s ({time1/time2:.2f}x faster)")
    
    # OPTIMISED: Using defaultdict
    start = time.time()
    result = defaultdict(int)
    for key, value in data:
        result[key] += value
    time3 = time.time() - start
    print(f"Using defaultdict: {time3:.4f}s ({time1/time3:.2f}x faster)\n")


def benchmark_counting():
    print("--- Counting Elements ---\n")
    
    data = [i % 100 for i in range(50000)]
    
    # UNOPTIMISED: Manual counting with dict
    start = time.time()
    counts = {}
    for item in data:
        if item in counts:
            counts[item] += 1
        else:
            counts[item] = 1
    time1 = time.time() - start
    print(f"Manual counting: {time1:.4f}s")
    
    # BETTER: Using defaultdict
    start = time.time()
    counts = defaultdict(int)
    for item in data:
        counts[item] += 1
    time2 = time.time() - start
    print(f"Using defaultdict: {time2:.4f}s ({time1/time2:.2f}x faster)")
    
    # OPTIMISED: Using Counter
    start = time.time()
    counts = Counter(data)
    time3 = time.time() - start
    print(f"Using Counter: {time3:.4f}s ({time1/time3:.2f}x faster)\n")


def benchmark_sorted_search():
    print("--- Searching in Sorted Data ---\n")
    
    n = 100000
    data = list(range(0, n * 2, 2))  # Even numbers
    search_items = [i * 2 for i in range(0, n//10, 1)]
    
    # UNOPTIMISED: Linear search
    start = time.time()
    found = [item for item in search_items if item in data]
    time1 = time.time() - start
    print(f"Linear search: {time1:.4f}s")
    
    # OPTIMISED: Binary search
    start = time.time()
    found = []
    for item in search_items:
        idx = bisect.bisect_left(data, item)
        if idx < len(data) and data[idx] == item:
            found.append(item)
    time2 = time.time() - start
    print(f"Binary search: {time2:.4f}s ({time1/time2:.1f}x faster)\n")


def benchmark_list_comprehension():
    print("--- List Construction ---\n")
    
    n = 100000
    
    # UNOPTIMISED: Using append in loop
    start = time.time()
    result = []
    for i in range(n):
        if i % 2 == 0:
            result.append(i * i)
    time1 = time.time() - start
    print(f"Using append: {time1:.4f}s")
    
    # OPTIMISED: List comprehension
    start = time.time()
    result = [i * i for i in range(n) if i % 2 == 0]
    time2 = time.time() - start
    print(f"List comprehension: {time2:.4f}s ({time1/time2:.2f}x faster)")
    
    # MEMORY OPTIMISED: Generator expression (for large datasets)
    start = time.time()
    result = sum(i * i for i in range(n) if i % 2 == 0)
    time3 = time.time() - start
    print(f"Generator expression: {time3:.4f}s ({time1/time3:.2f}x faster)\n")


def benchmark_duplicate_removal():
    print("--- Removing Duplicates ---\n")
    
    data = [i % 1000 for i in range(50000)]
    
    # UNOPTIMISED: Using list with 'in' check
    start = time.time()
    unique = []
    for item in data:
        if item not in unique:
            unique.append(item)
    time1 = time.time() - start
    print(f"List with 'in' check: {time1:.4f}s")
    
    # BETTER: Using set intermediate
    start = time.time()
    seen = set()
    unique = []
    for item in data:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    time2 = time.time() - start
    print(f"Set-based tracking: {time2:.4f}s ({time1/time2:.1f}x faster)")
    
    # OPTIMISED: Using set (if order doesn't matter)
    start = time.time()
    unique = list(set(data))
    time3 = time.time() - start
    print(f"Direct set conversion: {time3:.4f}s ({time1/time3:.1f}x faster)")
    
    # OPTIMISED: Using dict.fromkeys (preserves order in Python 3.7+)
    start = time.time()
    unique = list(dict.fromkeys(data))
    time4 = time.time() - start
    print(f"dict.fromkeys (ordered): {time4:.4f}s ({time1/time4:.1f}x faster)\n")


def main():
    print("=" * 40)
    print("DATA STRUCTURE OPTIMISATION BENCHMARKS")
    print("=" * 40 + "\n")
    
    benchmark_list_vs_set()
    benchmark_list_operations()
    benchmark_dict_operations()
    benchmark_counting()
    benchmark_sorted_search()
    benchmark_list_comprehension()
    benchmark_duplicate_removal()
    
    print("\n=== Key Takeaways ===")
    print("1. Use sets for membership testing (O(1) vs O(n))")
    print("2. Use deque for frequent insertions at both ends")
    print("3. Use defaultdict/Counter for counting operations")
    print("4. Use binary search (bisect) on sorted data")
    print("5. List comprehensions are faster than loops")
    print("6. Choose data structures based on access patterns")
    print("7. Use generators for memory efficiency with large datasets")

if __name__ == "__main__":
    main()
