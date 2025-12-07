import time
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading

# CPU-bound task
def compute_intensive_task(n):
    """Simulate CPU-intensive work"""
    result = 0
    for i in range(n):
        result += i ** 2
    return result

# I/O-bound task simulation
def io_bound_task(duration):
    """Simulate I/O-bound work"""
    time.sleep(duration)
    return f"Completed after {duration}s"


def benchmark_cpu_bound():
    print("--- CPU-Bound Task Optimisation ---\n")
    
    tasks = [1000000] * 8
    
    # UNOPTIMISED: Sequential execution
    start = time.time()
    results = [compute_intensive_task(n) for n in tasks]
    time1 = time.time() - start
    print(f"Sequential execution: {time1:.4f}s")
    
    # OPTIMISED: Using ProcessPoolExecutor
    start = time.time()
    with ProcessPoolExecutor(max_workers=mp.cpu_count()) as executor:
        results = list(executor.map(compute_intensive_task, tasks))
    time2 = time.time() - start
    print(f"Parallel (ProcessPool): {time2:.4f}s ({time1/time2:.2f}x faster)")
    print(f"Used {mp.cpu_count()} CPU cores\n")


def benchmark_io_bound():
    print("--- I/O-Bound Task Optimisation ---\n")
    
    tasks = [0.1] * 20  # 20 tasks, each taking 0.1 seconds
    
    # UNOPTIMISED: Sequential execution
    start = time.time()
    results = [io_bound_task(duration) for duration in tasks]
    time1 = time.time() - start
    print(f"Sequential execution: {time1:.4f}s")
    
    # OPTIMISED: Using ThreadPoolExecutor
    start = time.time()
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(io_bound_task, tasks))
    time2 = time.time() - start
    print(f"Multi-threaded: {time2:.4f}s ({time1/time2:.2f}x faster)")
    print(f"Used {10} threads\n")


def matrix_multiply_row(args):
    """Multiply a single row of matrix A with matrix B"""
    row, B = args
    result_row = []
    for j in range(len(B[0])):
        result_row.append(sum(row[k] * B[k][j] for k in range(len(B))))
    return result_row


def benchmark_matrix_multiplication():
    print("--- Matrix Multiplication Parallelisation ---\n")
    
    size = 200
    A = [[i + j for j in range(size)] for i in range(size)]
    B = [[i - j for j in range(size)] for i in range(size)]
    
    # UNOPTIMISED: Sequential
    start = time.time()
    C = []
    for i in range(len(A)):
        row = []
        for j in range(len(B[0])):
            row.append(sum(A[i][k] * B[k][j] for k in range(len(B))))
        C.append(row)
    time1 = time.time() - start
    print(f"Sequential: {time1:.4f}s")
    
    # OPTIMISED: Parallel by rows
    start = time.time()
    with ProcessPoolExecutor(max_workers=mp.cpu_count()) as executor:
        args = [(A[i], B) for i in range(len(A))]
        C = list(executor.map(matrix_multiply_row, args))
    time2 = time.time() - start
    print(f"Parallel: {time2:.4f}s ({time1/time2:.2f}x faster)\n")


def process_chunk(data):
    """Process a chunk of data"""
    return sum(x ** 2 for x in data)


def benchmark_data_processing():
    print("--- Large Dataset Processing ---\n")
    
    data = list(range(10000000))
    num_workers = mp.cpu_count()
    
    # UNOPTIMISED: Process all at once
    start = time.time()
    result = sum(x ** 2 for x in data)
    time1 = time.time() - start
    print(f"Single process: {time1:.4f}s")
    
    # OPTIMISED: Split into chunks and process in parallel
    start = time.time()
    chunk_size = len(data) // num_workers
    chunks = [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]
    
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        results = executor.map(process_chunk, chunks)
        result = sum(results)
    
    time2 = time.time() - start
    print(f"Multi-process ({num_workers} workers): {time2:.4f}s ({time1/time2:.2f}x faster)\n")


def worker_with_shared_state(lock, counter, iterations):
    """Worker that updates shared counter - demonstrates lock overhead"""
    for _ in range(iterations):
        with lock:
            counter.value += 1


def benchmark_shared_state():
    print("--- Shared State vs Independent Processing ---\n")
    
    num_threads = 4
    iterations = 100000
    
    # WITH LOCK: Shared state (slower due to synchronization)
    start = time.time()
    lock = threading.Lock()
    counter = mp.Value('i', 0)
    threads = []
    
    for _ in range(num_threads):
        t = threading.Thread(target=worker_with_shared_state, 
                            args=(lock, counter, iterations))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    time1 = time.time() - start
    print(f"With shared state (lock overhead): {time1:.4f}s")
    
    # WITHOUT LOCK: Independent processing then combine
    def worker_independent(iterations):
        return sum(1 for _ in range(iterations))
    
    start = time.time()
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        results = executor.map(worker_independent, [iterations] * num_threads)
        total = sum(results)
    
    time2 = time.time() - start
    print(f"Independent then combine: {time2:.4f}s ({time1/time2:.2f}x faster)")
    print("Lesson: Minimise shared state for better parallelisation\n")


def main():
    print("=" * 45)
    print("PARALLELISATION & CONCURRENCY OPTIMISATION")
    print("=" * 45 + "\n")
    
    print(f"System has {mp.cpu_count()} CPU cores available\n")
    
    benchmark_cpu_bound()
    benchmark_io_bound()
    benchmark_matrix_multiplication()
    benchmark_data_processing()
    benchmark_shared_state()
    
    print("\n=== Key Takeaways ===")
    print("1. Use multiprocessing for CPU-bound tasks")
    print("2. Use threading for I/O-bound tasks")
    print("3. Minimize shared state between workers")
    print("4. Chunk large datasets for parallel processing")
    print("5. Consider overhead: parallelization isn't always faster")
    print("6. Match worker count to CPU cores for CPU-bound work")
    print("7. Can use more threads than cores for I/O-bound work")

if __name__ == "__main__":
    main()
