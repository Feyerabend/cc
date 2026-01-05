"""
Educational CUDA Simulator
==========================
Yet another Python-based CUDA simulator designed to help understand GPU
programming concepts including thread hierarchy, memory types,
and parallel execution patterns.
"""

import threading
import time
from typing import Callable, Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
import json


class MemoryType(Enum):
    """Different types of GPU memory"""
    GLOBAL = "global"      # Accessible by all threads, slow but large
    SHARED = "shared"      # Shared within a block, fast but small
    CONSTANT = "constant"  # Read-only, cached, fast for uniform access
    LOCAL = "local"        # Per-thread private memory


@dataclass
class ThreadContext:
    """
    Represents a CUDA thread's execution context.
    
    In CUDA:
    - threadIdx: index within the block (0 to blockDim-1)
    - blockIdx: which block this thread belongs to (0 to gridDim-1)
    - blockDim: total threads per block
    - gridDim: total blocks in the grid
    """
    threadIdx: int
    blockIdx: int
    blockDim: int
    gridDim: int
    
    @property
    def global_id(self) -> int:
        """Calculate global thread ID across all blocks"""
        return self.blockIdx * self.blockDim + self.threadIdx
    
    @property
    def warp_id(self) -> int:
        """Warp ID (groups of 32 threads that execute together)"""
        return self.threadIdx // 32
    
    def __str__(self):
        return (f"Thread[block={self.blockIdx}, thread={self.threadIdx}, "
                f"global={self.global_id}]")


class MemorySystem:
    """
    Simulates GPU memory hierarchy with different access patterns and speeds.
    
    Memory Hierarchy (from fastest to slowest):
    1. Registers (per-thread, not simulated here)
    2. Shared Memory (per-block, ~100x faster than global)
    3. Constant Memory (read-only, cached)
    4. Global Memory (large but slow)
    """
    
    def __init__(self, visualize: bool = True):
        self.global_memory: Dict[str, List[Any]] = {}
        self.shared_memory: Dict[str, Dict[int, List[Any]]] = {}
        self.constant_memory: Dict[str, Any] = {}
        self.memory_locks: Dict[str, threading.Lock] = {}
        self.visualize = visualize
        
        # Track memory access patterns for educational purposes
        self.access_stats = {
            'global_reads': 0,
            'global_writes': 0,
            'shared_reads': 0,
            'shared_writes': 0,
        }
    
    def allocate_global(self, name: str, size: int, dtype: type = int) -> None:
        """
        Allocate global memory (like cudaMalloc in CUDA).
        Global memory is slow but large and accessible by all threads.
        """
        self.global_memory[name] = [dtype() for _ in range(size)]
        self.memory_locks[name] = threading.Lock()
        
        if self.visualize:
            print(f"  Allocated GLOBAL memory '{name}': {size} elements of type {dtype.__name__}")
    
    def allocate_shared(self, name: str, block_id: int, size: int) -> None:
        """
        Allocate shared memory for a specific block (like __shared__ in CUDA).
        Shared memory is fast but limited and only accessible within a block.
        """
        if name not in self.shared_memory:
            self.shared_memory[name] = {}
        self.shared_memory[name][block_id] = [0] * size
        
        if self.visualize:
            print(f"⚡ Allocated SHARED memory '{name}' for block {block_id}: {size} elements")
    
    def set_constant(self, name: str, value: Any) -> None:
        """
        Set constant memory (read-only, like __constant__ in CUDA).
        Constant memory is cached and optimized for uniform access.
        """
        self.constant_memory[name] = value
        if self.visualize:
            print(f"  Set CONSTANT memory '{name}' = {value}")
    
    def read_global(self, name: str, index: int) -> Any:
        """Read from global memory (simulates slow access)"""
        self.access_stats['global_reads'] += 1
        time.sleep(0.00001)  # Simulate slow access
        return self.global_memory[name][index]
    
    def write_global(self, name: str, index: int, value: Any) -> None:
        """Write to global memory (simulates slow access)"""
        self.access_stats['global_writes'] += 1
        time.sleep(0.00001)  # Simulate slow access
        self.global_memory[name][index] = value
    
    def get_stats(self) -> Dict[str, int]:
        """Return memory access statistics"""
        return self.access_stats.copy()


class CUDAKernel:
    """
    Base class for CUDA kernels with common GPU functions.
    Provides thread synchronization and atomic operations.
    """
    
    def __init__(self, memory: MemorySystem):
        self.memory = memory
        self.barriers: Dict[int, Dict] = {}  # Per-block barriers
    
    def __syncthreads(self, ctx: ThreadContext) -> None:
        """
        Synchronize all threads in a block (like __syncthreads() in CUDA).
        
        This is crucial for:
        - Ensuring shared memory is fully written before reading
        - Coordinating work between threads in a block
        
        Educational Note: This only syncs threads WITHIN a block, not across blocks!
        """
        block_id = ctx.blockIdx
        
        if block_id not in self.barriers:
            self.barriers[block_id] = {
                'count': 0,
                'lock': threading.Lock(),
                'condition': threading.Condition(threading.Lock()),
                'expected': ctx.blockDim
            }
        
        barrier = self.barriers[block_id]
        
        with barrier['condition']:
            barrier['count'] += 1
            if barrier['count'] >= barrier['expected']:
                barrier['count'] = 0
                barrier['condition'].notify_all()
            else:
                barrier['condition'].wait()
    
    def atomicAdd(self, array: List[Any], index: int, value: Any) -> Any:
        """
        Atomic addition (like atomicAdd in CUDA).
        
        Atomic operations are essential when multiple threads write to
        the same memory location to prevent race conditions.
        
        Returns: the old value before addition
        """
        # Find which memory array this is
        array_name = None
        for name, mem in self.memory.global_memory.items():
            if mem is array:
                array_name = name
                break
        
        if array_name and array_name in self.memory.memory_locks:
            with self.memory.memory_locks[array_name]:
                old_value = array[index]
                array[index] += value
                return old_value
        return 0


class CUDASimulator:
    """
    Main CUDA simulator that manages kernel execution and provides
    educational visualization of GPU parallel execution.
    """
    
    def __init__(self, max_concurrent_threads: int = 256, visualize: bool = True):
        self.memory = MemorySystem(visualize)
        self.kernels: Dict[str, Callable] = {}
        self.max_concurrent_threads = max_concurrent_threads
        self.visualize = visualize
        self.execution_log: List[str] = []
    
    def register_kernel(self, name: str, kernel_func: Callable) -> None:
        """Register a kernel function for later execution"""
        self.kernels[name] = kernel_func
        if self.visualize:
            print(f"  Registered kernel: {name}")
    
    def launch_kernel(self, 
                     name: str,
                     grid_dim: int,
                     block_dim: int,
                     *args,
                     shared_mem_size: int = 0) -> Dict[str, Any]:
        """
        Launch a kernel with specified grid and block dimensions.
        
        Args:
            name: Kernel function name
            grid_dim: Number of blocks in the grid
            block_dim: Number of threads per block
            *args: Arguments to pass to the kernel
            shared_mem_size: Size of shared memory per block
        
        Returns:
            Dictionary with execution statistics
        """
        if name not in self.kernels:
            raise ValueError(f"Kernel '{name}' not registered")
        
        total_threads = grid_dim * block_dim
        
        if self.visualize:
            print(f"\n{'='*70}")
            print(f"  LAUNCHING KERNEL: {name}")
            print(f"{'='*70}")
            print(f"Grid Dimension:  {grid_dim} blocks")
            print(f"Block Dimension: {block_dim} threads/block")
            print(f"Total Threads:   {total_threads} threads")
            print(f"Shared Memory:   {shared_mem_size} bytes/block")
            print(f"{'='*70}\n")
            
            self._visualize_grid(grid_dim, block_dim)
        
        start_time = time.time()
        
        # Use thread pool to simulate concurrent execution
        with ThreadPoolExecutor(max_workers=min(self.max_concurrent_threads, total_threads)) as executor:
            futures = []
            
            # Allocate shared memory for each block
            if shared_mem_size > 0:
                for block_id in range(grid_dim):
                    self.memory.allocate_shared('shared', block_id, shared_mem_size)
            
            # Launch all threads
            for block_id in range(grid_dim):
                for thread_id in range(block_dim):
                    ctx = ThreadContext(thread_id, block_id, block_dim, grid_dim)
                    future = executor.submit(self._execute_thread, name, ctx, list(args))
                    futures.append(future)
            
            # Wait for completion
            for future in futures:
                future.result()
        
        execution_time = time.time() - start_time
        
        stats = {
            'kernel_name': name,
            'grid_dim': grid_dim,
            'block_dim': block_dim,
            'total_threads': total_threads,
            'execution_time': execution_time,
            'memory_stats': self.memory.get_stats()
        }
        
        if self.visualize:
            print(f"\n  Kernel completed in {execution_time:.4f}s")
            print(f"  Throughput: {total_threads/execution_time:.0f} threads/second\n")
        
        return stats
    
    def _execute_thread(self, kernel_name: str, ctx: ThreadContext, args: List[Any]) -> None:
        """Execute a single thread"""
        kernel = self.kernels[kernel_name]
        cuda_kernel = CUDAKernel(self.memory)
        
        # Execute the kernel function with thread context
        kernel(cuda_kernel, ctx, *args)
    
    def _visualize_grid(self, grid_dim: int, block_dim: int) -> None:
        """Visualise the thread grid structure"""
        print("Thread Grid Structure:")
        print("┌" + "─" * (grid_dim * 8 - 1) + "┐")
        
        for block_id in range(min(grid_dim, 8)):  # Show max 8 blocks
            line = "│"
            for _ in range(min(block_dim, 32)):  # Show max 32 threads
                line += "█"
            if block_dim > 32:
                line += ".."
            line += f" Block {block_id}"
            print(line)
        
        if grid_dim > 8:
            print("│ .. ({} more blocks)".format(grid_dim - 8))
        
        print("└" + "─" * (grid_dim * 8 - 1) + "┘")
        print()


# EXAMPLE KERNELS - Educational implementations

def vector_add_kernel(cuda: CUDAKernel, ctx: ThreadContext,
                     a: List[float], b: List[float], c: List[float]) -> None:
    """
    Vector Addition Kernel (Most basic parallel operation)
    
    Each thread adds one pair of elements: c[i] = a[i] + b[i]
    
    This demonstrates:
    - One-to-one thread-to-data mapping
    - Independent thread operations (no synchronization needed)
    - Coalesced memory access pattern
    """
    idx = ctx.global_id
    
    if idx < len(a):
        c[idx] = a[idx] + b[idx]


def dot_product_kernel(cuda: CUDAKernel, ctx: ThreadContext,
                      a: List[float], b: List[float], result: List[float]) -> None:
    """
    Dot Product Kernel (Parallel reduction pattern)
    
    Computes sum of element-wise products: result = sum(a[i] * b[i])
    
    This demonstrates:
    - Atomic operations for thread coordination
    - Reduction pattern (many threads -> one result)
    - Race condition prevention
    """
    idx = ctx.global_id
    
    if idx < len(a):
        partial = a[idx] * b[idx]
        cuda.atomicAdd(result, 0, partial)


def matrix_transpose_kernel(cuda: CUDAKernel, ctx: ThreadContext,
                           input_matrix: List[float],
                           output_matrix: List[float],
                           width: int, height: int) -> None:
    """
    Matrix Transpose Kernel (2D data mapping)
    
    Transposes a matrix: output[j][i] = input[i][j]
    
    This demonstrates:
    - 2D thread indexing
    - Non-coalesced memory access patterns
    - How to map threads to 2D data structures
    """
    row = ctx.blockIdx
    col = ctx.threadIdx
    
    if row < height and col < width:
        input_idx = row * width + col
        output_idx = col * height + row
        output_matrix[output_idx] = input_matrix[input_idx]


def histogram_kernel(cuda: CUDAKernel, ctx: ThreadContext,
                    data: List[int], histogram: List[int], num_bins: int) -> None:
    """
    Histogram Kernel (Demonstrates atomic contention)
    
    Counts frequency of values in bins.
    
    This demonstrates:
    - Heavy use of atomic operations
    - Potential for thread contention
    - Non-uniform memory access patterns
    """
    idx = ctx.global_id
    
    if idx < len(data):
        bin_idx = data[idx] % num_bins
        cuda.atomicAdd(histogram, bin_idx, 1)


# EDUCATIONAL EXAMPLES

def example_1_basic_vector_operations():
    """Example 1: Basic Vector Operations"""
    print("\n" + "-"*70)
    print("EXAMPLE 1: Basic Vector Addition")
    print("-"*70)
    print("Demonstrates: Basic parallel execution, thread-to-data mapping\n")
    
    sim = CUDASimulator(visualize=True)
    
    # Problem size
    N = 256
    
    # Allocate memory
    sim.memory.allocate_global('a', N, float)
    sim.memory.allocate_global('b', N, float)
    sim.memory.allocate_global('c', N, float)
    
    # Initialize data
    sim.memory.global_memory['a'] = [float(i) for i in range(N)]
    sim.memory.global_memory['b'] = [float(i * 2) for i in range(N)]
    
    # Register and launch kernel
    sim.register_kernel('vector_add', vector_add_kernel)
    stats = sim.launch_kernel('vector_add', 
                             8,   # grid_dim: 8 blocks
                             32,  # block_dim: 32 threads per block
                             sim.memory.global_memory['a'],
                             sim.memory.global_memory['b'],
                             sim.memory.global_memory['c'])
    
    # Verify results
    result = sim.memory.global_memory['c']
    print(f"Results (first 10 elements):")
    for i in range(10):
        print(f"  {sim.memory.global_memory['a'][i]} + "
              f"{sim.memory.global_memory['b'][i]} = {result[i]}")


def example_2_reduction_pattern():
    """Example 2: Parallel Reduction (Dot Product)"""
    print("\n" + "-"*70)
    print("EXAMPLE 2: Parallel Reduction - Dot Product")
    print("-"*70)
    print("Demonstrates: Atomic operations, reduction pattern\n")
    
    sim = CUDASimulator(visualize=True)
    
    N = 128
    
    sim.memory.allocate_global('a', N, float)
    sim.memory.allocate_global('b', N, float)
    sim.memory.allocate_global('result', 1, float)
    
    # Initialize with simple values for easy verification
    sim.memory.global_memory['a'] = [1.0] * N
    sim.memory.global_memory['b'] = [2.0] * N
    
    sim.register_kernel('dot_product', dot_product_kernel)
    sim.launch_kernel('dot_product', 4, 32,
                     sim.memory.global_memory['a'],
                     sim.memory.global_memory['b'],
                     sim.memory.global_memory['result'])
    
    result = sim.memory.global_memory['result'][0]
    expected = N * 1.0 * 2.0
    print(f"Dot product result: {result}")
    print(f"Expected: {expected}")
    print(f"Correct: {abs(result - expected) < 0.01}")


def example_3_configuration_comparison():
    """Example 3: Comparing Different Grid/Block Configurations"""
    print("\n" + "-"*70)
    print("EXAMPLE 3: Configuration Comparison")
    print("-"*70)
    print("Demonstrates: Impact of different thread configurations\n")
    
    N = 1024
    
    configurations = [
        (32, 32),   # 32 blocks x 32 threads = 1024 threads
        (16, 64),   # 16 blocks x 64 threads = 1024 threads
        (64, 16),   # 64 blocks x 16 threads = 1024 threads
        (1, 1024),  # 1 block x 1024 threads = 1024 threads
    ]
    
    print(f"Testing {len(configurations)} configurations with {N} total threads:\n")
    
    for grid_dim, block_dim in configurations:
        sim = CUDASimulator(visualize=False)
        
        sim.memory.allocate_global('a', N, float)
        sim.memory.allocate_global('b', N, float)
        sim.memory.allocate_global('c', N, float)
        
        sim.memory.global_memory['a'] = [1.0] * N
        sim.memory.global_memory['b'] = [2.0] * N
        
        sim.register_kernel('vector_add', vector_add_kernel)
        stats = sim.launch_kernel('vector_add', grid_dim, block_dim,
                                 sim.memory.global_memory['a'],
                                 sim.memory.global_memory['b'],
                                 sim.memory.global_memory['c'])
        
        print(f"Grid: {grid_dim:4d} blocks × {block_dim:4d} threads/block = "
              f"{stats['total_threads']:4d} threads | "
              f"Time: {stats['execution_time']:.4f}s")


def main():
    """Run all educational examples"""
    print("""
                Educational CUDA Simulator
       Learn GPU programming concepts through simulation
    """)
    
    examples = [
        ("Basic Vector Operations", example_1_basic_vector_operations),
        ("Parallel Reduction", example_2_reduction_pattern),
        ("Configuration Comparison", example_3_configuration_comparison),
    ]
    
    print("\nExamples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\nRunning all examples..\n")
    
    for name, example_func in examples:
        try:
            example_func()
            time.sleep(1)  # Pause between examples
        except Exception as e:
            print(f"Error in {name}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "-"*70)
    print("All examples completed!")
    print("-"*70)


if __name__ == "__main__":
    main()
