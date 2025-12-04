import threading
from typing import Callable, Dict, List

class CUDAVM:
    def __init__(self):
        self.threads_per_block = 0
        self.blocks_per_grid = 0
        self.global_memory: Dict[str, List[int]] = {}
        self.kernels: Dict[str, Callable] = {}

    def allocate_global_memory(self, name: str, size: int):
        """Allocate memory in the global memory space."""
        self.global_memory[name] = [0] * size

    def define_kernel(self, name: str, kernel: Callable):
        """Define a kernel."""
        self.kernels[name] = kernel

    def launch_kernel(self, name: str, threads_per_block: int, blocks_per_grid: int, *args):
        """Simulate launching a kernel."""
        self.threads_per_block = threads_per_block
        self.blocks_per_grid = blocks_per_grid

        if name not in self.kernels:
            raise ValueError(f"Kernel '{name}' is not defined.")
        
        kernel = self.kernels[name]

        threads = []
        for block_id in range(blocks_per_grid):
            for thread_id in range(threads_per_block):
                thread = threading.Thread(
                    target=self._thread_worker,
                    args=(kernel, block_id, thread_id, *args)
                )
                threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

    def _thread_worker(self, kernel: Callable, block_id: int, thread_id: int, *args):
        """Simulate a CUDA thread executing a kernel."""
        thread_idx = block_id * self.threads_per_block + thread_id
        kernel(block_id, thread_id, thread_idx, *args)

class CUDAInterpreter:
    def __init__(self, vm: CUDAVM):
        self.vm = vm

    def execute(self, script: str):
        """Execute a CUDA-like script."""
        lines = script.strip().split("\n")
        for line in lines:
            self._execute_line(line.strip())

    def _execute_line(self, line: str):
        """Parse and execute a single line of the script."""
        parts = line.split()
        command = parts[0]

        if command == "ALLOCATE_GLOBAL_MEMORY":
            # Allocate global memory
            name = parts[1]
            size = int(parts[2])
            self.vm.allocate_global_memory(name, size)
        elif command == "KERNEL":
            # Define a kernel (currently predefined)
            name = parts[1]
            self.vm.define_kernel(name, self._get_predefined_kernel(name))
        elif command == "LAUNCH_KERNEL":
            # Launch a kernel
            name = parts[1]
            threads_per_block = int(parts[2])
            blocks_per_grid = int(parts[3])
            args = parts[4:]  # Remaining arguments
            args = [self.vm.global_memory[arg] if arg in self.vm.global_memory else arg for arg in args]
            self.vm.launch_kernel(name, threads_per_block, blocks_per_grid, *args)
        else:
            raise ValueError(f"Unknown command: {command}")

    def _get_predefined_kernel(self, name: str):
        """Return predefined kernels."""
        if name == "vector_add":
            return self._vector_add_kernel
        raise ValueError(f"Unknown kernel: {name}")

    def _vector_add_kernel(self, block_id: int, thread_id: int, thread_idx: int, a: List[int], b: List[int], c: List[int]):
        """Predefined kernel for vector addition."""
        if thread_idx < len(a):
            c[thread_idx] = a[thread_idx] + b[thread_idx]
            print(f"\nBlock {block_id}, Thread {thread_id} wrote {a[thread_idx]} + {b[thread_idx]} to c[{thread_idx}]")

# Main program
if __name__ == "__main__":
    # Problem size
    N = 16

    # Initialize CUDA VM
    cuda_vm = CUDAVM()

    # Allocate global memory for a, b, and c
    cuda_vm.allocate_global_memory('a', N)
    cuda_vm.allocate_global_memory('b', N)
    cuda_vm.allocate_global_memory('c', N)

    # Fill arrays a and b with data
    cuda_vm.global_memory['a'] = [i for i in range(N)]
    cuda_vm.global_memory['b'] = [i for i in range(N)]

    # Create the interpreter
    interpreter = CUDAInterpreter(cuda_vm)

    # CUDA-like script
    script = """
    ALLOCATE_GLOBAL_MEMORY c 16
    KERNEL vector_add
    LAUNCH_KERNEL vector_add 4 4 a b c
    """

    # Execute the script
    print("Executing CUDA-like script...")
    interpreter.execute(script)

    # Display the global memory content
    print("\nFinal result in global memory 'c':")
    print(cuda_vm.global_memory["c"])