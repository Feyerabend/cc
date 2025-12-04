import threading
import time
import random
from typing import Callable, Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import re

class CUDAMemory:
    """Enhanced memory management with different memory types"""
    def __init__(self):
        self.global_memory: Dict[str, List[Any]] = {}
        self.shared_memory: Dict[str, Dict[int, List[Any]]] = {}  # Per block
        self.constant_memory: Dict[str, Any] = {}
        self.memory_locks: Dict[str, threading.Lock] = {}
    
    def allocate_global(self, name: str, size: int, dtype='int'):
        """Allocate global memory with type support"""
        if dtype == 'int':
            self.global_memory[name] = [0] * size
        elif dtype == 'float':
            self.global_memory[name] = [0.0] * size
        elif dtype == 'bool':
            self.global_memory[name] = [False] * size
        self.memory_locks[name] = threading.Lock()
    
    def allocate_shared(self, name: str, block_id: int, size: int):
        """Allocate shared memory for a specific block"""
        if name not in self.shared_memory:
            self.shared_memory[name] = {}
        self.shared_memory[name][block_id] = [0] * size
    
    def set_constant(self, name: str, value: Any):
        """Set constant memory"""
        self.constant_memory[name] = value
    
    def get_memory(self, name: str, block_id: Optional[int] = None):
        """Get memory reference"""
        if block_id is not None and name in self.shared_memory:
            return self.shared_memory[name].get(block_id, [])
        return self.global_memory.get(name, [])

class ThreadInfo:
    """Thread execution context"""
    def __init__(self, block_id: int, thread_id: int, block_dim: int, grid_dim: int):
        self.blockIdx = block_id
        self.threadIdx = thread_id
        self.blockDim = block_dim
        self.gridDim = grid_dim
        self.global_thread_id = block_id * block_dim + thread_id
        self.warp_id = thread_id // 32  # Simulate warps of 32 threads

class CUDAKernel:
    """Base class for CUDA kernels with built-in functions"""
    def __init__(self, memory: CUDAMemory):
        self.memory = memory
        self.barrier_count = 0
        self.barrier_lock = threading.Lock()
        self.barrier_condition = threading.Condition(self.barrier_lock)
        
    def __syncthreads(self, block_id: int, total_threads_in_block: int):
        """Simulate __syncthreads() barrier synchronization"""
        with self.barrier_condition:
            self.barrier_count += 1
            if self.barrier_count % total_threads_in_block == 0:
                self.barrier_condition.notify_all()
            else:
                self.barrier_condition.wait()
    
    def atomicAdd(self, array: List[Any], index: int, value: Any):
        """Simulate atomic addition"""
        # In real CUDA this would be atomic, here we use locks
        array_name = None
        for name, mem_array in self.memory.global_memory.items():
            if mem_array is array:
                array_name = name
                break
        
        if array_name and array_name in self.memory.memory_locks:
            with self.memory.memory_locks[array_name]:
                if index < len(array):
                    array[index] += value
                    return array[index] - value  # Return old value
        return 0

class EnhancedCUDAVM:
    def __init__(self, max_threads: int = 1024):
        self.memory = CUDAMemory()
        self.kernels: Dict[str, Callable] = {}
        self.max_threads = max_threads
        self.execution_stats = {
            'kernels_launched': 0,
            'total_threads': 0,
            'execution_time': 0.0
        }
        
    def allocate_memory(self, mem_type: str, name: str, size: int, dtype='int', block_id: Optional[int] = None):
        """Unified memory allocation interface"""
        if mem_type == 'global':
            self.memory.allocate_global(name, size, dtype)
        elif mem_type == 'shared' and block_id is not None:
            self.memory.allocate_shared(name, block_id, size)
        elif mem_type == 'constant':
            self.memory.set_constant(name, size)  # In this case, size is the value
    
    def define_kernel(self, name: str, kernel_func: Callable):
        """Register a kernel function"""
        self.kernels[name] = kernel_func
    
    def launch_kernel(self, name: str, grid_dim: int, block_dim: int, shared_mem_size: int = 0, *args):
        """Launch kernel with enhanced parallel execution"""
        if name not in self.kernels:
            raise ValueError(f"Kernel '{name}' not found")
        
        start_time = time.time()
        total_threads = grid_dim * block_dim
        
        # Limit concurrent threads to simulate hardware constraints
        max_concurrent = min(self.max_threads, total_threads)
        
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            futures = []
            
            for block_id in range(grid_dim):
                # Allocate shared memory for this block if requested
                if shared_mem_size > 0:
                    self.memory.allocate_shared('shared_mem', block_id, shared_mem_size)
                
                for thread_id in range(block_dim):
                    thread_info = ThreadInfo(block_id, thread_id, block_dim, grid_dim)
                    
                    future = executor.submit(
                        self._execute_thread,
                        name, thread_info, *args
                    )
                    futures.append(future)
            
            # Wait for all threads to complete
            for future in futures:
                future.result()
        
        execution_time = time.time() - start_time
        self.execution_stats['kernels_launched'] += 1
        self.execution_stats['total_threads'] += total_threads
        self.execution_stats['execution_time'] += execution_time
        
        print(f"Kernel '{name}' executed: {total_threads} threads in {execution_time:.4f}s")
    
    def _execute_thread(self, kernel_name: str, thread_info: ThreadInfo, *args):
        """Execute a single thread with simulation of memory access delays"""
        # Simulate variable execution time based on memory access patterns
        delay = random.uniform(0.001, 0.005)  # 1-5ms simulation
        time.sleep(delay)
        
        kernel = self.kernels[kernel_name]
        kernel_instance = CUDAKernel(self.memory)
        
        # Call the kernel with thread context
        kernel(kernel_instance, thread_info, *args)

class AdvancedCUDAInterpreter:
    def __init__(self, vm: EnhancedCUDAVM):
        self.vm = vm
        self.variables: Dict[str, Any] = {}
        self.functions: Dict[str, List[str]] = {}
        
    def execute(self, script: str):
        """Execute enhanced CUDA-like script"""
        lines = self._preprocess_script(script)
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line or line.startswith('//'):
                i += 1
                continue
                
            if line.startswith('function'):
                i = self._parse_function(lines, i)
            else:
                self._execute_line(line)
                i += 1
    
    def _preprocess_script(self, script: str) -> List[str]:
        """Preprocess script to handle multiline constructs"""
        # Remove comments and normalize whitespace
        lines = []
        for line in script.split('\n'):
            line = line.strip()
            if line and not line.startswith('//'):
                lines.append(line)
        return lines
    
    def _parse_function(self, lines: List[str], start_idx: int) -> int:
        """Parse function definition"""
        func_line = lines[start_idx]
        func_match = re.match(r'function\s+(\w+)\s*\((.*?)\)\s*{', func_line)
        if not func_match:
            raise ValueError(f"Invalid function syntax: {func_line}")
        
        func_name = func_match.group(1)
        func_body = []
        
        i = start_idx + 1
        brace_count = 1
        
        while i < len(lines) and brace_count > 0:
            line = lines[i]
            if '{' in line:
                brace_count += line.count('{')
            if '}' in line:
                brace_count -= line.count('}')
            
            if brace_count > 0:
                func_body.append(line)
            i += 1
        
        self.functions[func_name] = func_body
        return i
    
    def _execute_line(self, line: str):
        """Execute a single line with enhanced command support"""
        # Variable assignment
        if '=' in line and not any(op in line for op in ['==', '!=', '<=', '>=']):
            self._handle_assignment(line)
            return
        
        # Parse command
        parts = self._parse_command(line)
        if not parts:
            return
            
        command = parts[0].upper()
        
        if command == 'ALLOCATE':
            self._handle_allocate(parts[1:])
        elif command == 'SET_ARRAY':
            self._handle_set_array(parts[1:])
        elif command == 'KERNEL':
            self._handle_kernel_definition(parts[1:])
        elif command == 'LAUNCH':
            self._handle_kernel_launch(parts[1:])
        elif command == 'PRINT':
            self._handle_print(parts[1:])
        elif command == 'FOR':
            self._handle_for_loop(line)
        else:
            raise ValueError(f"Unknown command: {command}")
    
    def _parse_command(self, line: str) -> List[str]:
        """Parse command line with support for quoted strings and expressions"""
        # Simple parsing - could be enhanced with proper lexer/parser
        parts = []
        current = ""
        in_quotes = False
        
        for char in line:
            if char == '"' or char == "'":
                in_quotes = not in_quotes
            elif char == ' ' and not in_quotes:
                if current:
                    parts.append(current)
                    current = ""
            else:
                current += char
        
        if current:
            parts.append(current)
        
        return parts
    
    def _handle_assignment(self, line: str):
        """Handle variable assignments"""
        var_name, expression = line.split('=', 1)
        var_name = var_name.strip()
        expression = expression.strip()
        
        # Evaluate expression (simplified)
        if expression.isdigit():
            self.variables[var_name] = int(expression)
        elif expression.replace('.', '').isdigit():
            self.variables[var_name] = float(expression)
        elif expression.startswith('[') and expression.endswith(']'):
            # Array literal
            array_content = expression[1:-1]
            if array_content:
                self.variables[var_name] = [int(x.strip()) for x in array_content.split(',')]
            else:
                self.variables[var_name] = []
        else:
            self.variables[var_name] = expression
    
    def _handle_allocate(self, args: List[str]):
        """Handle memory allocation: ALLOCATE [type] name size [dtype]"""
        if len(args) < 3:
            raise ValueError("ALLOCATE requires at least 3 arguments")
        
        mem_type = args[0].lower()
        name = args[1]
        size = int(self._resolve_value(args[2]))
        dtype = args[3] if len(args) > 3 else 'int'
        
        self.vm.allocate_memory(mem_type, name, size, dtype)
    
    def _handle_set_array(self, args: List[str]):
        """Handle array initialization: SET_ARRAY name [values] or SET_ARRAY name RANGE start end"""
        name = args[0]
        
        if args[1] == 'RANGE':
            start = int(self._resolve_value(args[2]))
            end = int(self._resolve_value(args[3]))
            self.vm.memory.global_memory[name] = list(range(start, end))
        elif args[1] == 'RANDOM':
            size = len(self.vm.memory.global_memory[name])
            min_val = int(args[2]) if len(args) > 2 else 0
            max_val = int(args[3]) if len(args) > 3 else 100
            self.vm.memory.global_memory[name] = [random.randint(min_val, max_val) for _ in range(size)]
        else:
            # Direct value assignment
            values = [int(self._resolve_value(v)) for v in args[1:]]
            self.vm.memory.global_memory[name] = values
    
    def _handle_kernel_definition(self, args: List[str]):
        """Handle kernel definition"""
        kernel_name = args[0]
        
        if kernel_name in self.functions:
            # Custom kernel from function
            def custom_kernel(cuda_kernel: CUDAKernel, thread_info: ThreadInfo, *kernel_args):
                # Execute custom kernel logic
                self._execute_custom_kernel(cuda_kernel, thread_info, self.functions[kernel_name], kernel_args)
            self.vm.define_kernel(kernel_name, custom_kernel)
        else:
            # Predefined kernel
            kernel_func = self._get_predefined_kernel(kernel_name)
            self.vm.define_kernel(kernel_name, kernel_func)
    
    def _handle_kernel_launch(self, args: List[str]):
        """Handle kernel launch: LAUNCH kernel_name grid_dim block_dim [shared_mem] args..."""
        kernel_name = args[0]
        grid_dim = int(self._resolve_value(args[1]))
        block_dim = int(self._resolve_value(args[2]))
        
        shared_mem = 0
        arg_start = 3
        if len(args) > 3 and args[3].isdigit():
            shared_mem = int(args[3])
            arg_start = 4
        
        # Resolve memory arguments
        kernel_args = []
        for arg in args[arg_start:]:
            if arg in self.vm.memory.global_memory:
                kernel_args.append(self.vm.memory.global_memory[arg])
            else:
                kernel_args.append(self._resolve_value(arg))
        
        self.vm.launch_kernel(kernel_name, grid_dim, block_dim, shared_mem, *kernel_args)
    
    def _handle_print(self, args: List[str]):
        """Handle print statements"""
        values = []
        for arg in args:
            if arg in self.vm.memory.global_memory:
                values.append(f"{arg}: {self.vm.memory.global_memory[arg]}")
            elif arg in self.variables:
                values.append(f"{arg}: {self.variables[arg]}")
            else:
                values.append(arg.strip('"\''))
        print(" ".join(values))
    
    def _resolve_value(self, value: str) -> Any:
        """Resolve variable or literal value"""
        if value in self.variables:
            return self.variables[value]
        elif value.isdigit():
            return int(value)
        elif value.replace('.', '').isdigit():
            return float(value)
        else:
            return value
    
    def _execute_custom_kernel(self, cuda_kernel: CUDAKernel, thread_info: ThreadInfo, 
                             function_body: List[str], args: tuple):
        """Execute custom kernel function"""
        # full implementation would need
        # a proper expression evaluator
        for line in function_body:
            if 'global_thread_id' in line:
                # Example: simple assignment using thread ID
                pass
    
    def _get_predefined_kernel(self, name: str) -> Callable:
        """Get predefined kernel implementations"""
        kernels = {
            'vector_add': self._vector_add_kernel,
            'vector_multiply': self._vector_multiply_kernel,
            'matrix_multiply': self._matrix_multiply_kernel,
            'reduce_sum': self._reduce_sum_kernel,
            'saxpy': self._saxpy_kernel,
        }
        
        if name not in kernels:
            raise ValueError(f"Unknown predefined kernel: {name}")
        
        return kernels[name]
    
    def _vector_add_kernel(self, cuda_kernel: CUDAKernel, thread_info: ThreadInfo, 
                          a: List[Any], b: List[Any], c: List[Any]):
        """Vector addition kernel"""
        idx = thread_info.global_thread_id
        if idx < len(a):
            c[idx] = a[idx] + b[idx]
    
    def _vector_multiply_kernel(self, cuda_kernel: CUDAKernel, thread_info: ThreadInfo,
                               a: List[Any], b: List[Any], c: List[Any]):
        """Vector multiplication kernel"""
        idx = thread_info.global_thread_id
        if idx < len(a):
            c[idx] = a[idx] * b[idx]
    
    def _saxpy_kernel(self, cuda_kernel: CUDAKernel, thread_info: ThreadInfo,
                     alpha: float, x: List[Any], y: List[Any]):
        """SAXPY operation: y = alpha * x + y"""
        idx = thread_info.global_thread_id
        if idx < len(x):
            y[idx] = alpha * x[idx] + y[idx]
    
    def _reduce_sum_kernel(self, cuda_kernel: CUDAKernel, thread_info: ThreadInfo,
                          input_array: List[Any], output: List[Any]):
        """Reduction sum with atomic operations"""
        idx = thread_info.global_thread_id
        if idx < len(input_array):
            cuda_kernel.atomicAdd(output, 0, input_array[idx])
    
    def _matrix_multiply_kernel(self, cuda_kernel: CUDAKernel, thread_info: ThreadInfo,
                               a: List[Any], b: List[Any], c: List[Any], n: int):
        """Simple matrix multiplication (assumes square matrices)"""
        row = thread_info.blockIdx
        col = thread_info.threadIdx
        
        if row < n and col < n:
            result = 0
            for k in range(n):
                result += a[row * n + k] * b[k * n + col]
            c[row * n + col] = result

# demo
if __name__ == "__main__":
    # Create enhanced CUDA VM with limited concurrent threads
    cuda_vm = EnhancedCUDAVM(max_threads=64)
    interpreter = AdvancedCUDAInterpreter(cuda_vm)
    
    # Enhanced CUDA-like script
    enhanced_script = """
    // Enhanced CUDA simulation demo
    
    // Set problem size
    N = 1024
    
    // Allocate memory with different types
    ALLOCATE global input_a N int
    ALLOCATE global input_b N int
    ALLOCATE global output_add N int
    ALLOCATE global output_mul N int
    ALLOCATE global reduction_result 1 int
    
    // Initialize arrays
    SET_ARRAY input_a RANGE 1 1025
    SET_ARRAY input_b RANGE 2 1026
    
    // Define and launch vector addition
    KERNEL vector_add
    LAUNCH vector_add 32 32 input_a input_b output_add
    
    // Define and launch vector multiplication  
    KERNEL vector_multiply
    LAUNCH vector_multiply 16 64 input_a input_b output_mul
    
    // Reduction operation
    KERNEL reduce_sum
    LAUNCH reduce_sum 32 32 input_a reduction_result
    
    // Print results
    PRINT "First 10 elements of vector addition:"
    PRINT "Last 10 elements of vector multiplication:"
    PRINT "Reduction sum result:"
    """
    
    print("--- Enhanced CUDA VM Simulator ---")
    print("Executing advanced CUDA-like script...\n")
    
    try:
        interpreter.execute(enhanced_script)
        
        # Display results
        print(f"\nVector Addition (first 10): {cuda_vm.memory.global_memory['output_add'][:10]}")
        print(f"Vector Multiplication (last 10): {cuda_vm.memory.global_memory['output_mul'][-10:]}")
        print(f"Reduction Sum: {cuda_vm.memory.global_memory['reduction_result'][0]}")
        
        # Display execution statistics
        stats = cuda_vm.execution_stats
        print(f"\n--- Execution Statistics ---")
        print(f"Kernels launched: {stats['kernels_launched']}")
        print(f"Total threads executed: {stats['total_threads']}")
        print(f"Total execution time: {stats['execution_time']:.4f}s")
        print(f"Average threads per second: {stats['total_threads']/stats['execution_time']:.0f}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
