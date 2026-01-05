
## CUDA (Compute Unified Device Architecture)

*CUDA* is a parallel computing platform and application programming interface (API)
created by NVIDIA. It allows software developers to use NVIDIA graphics processing
units (GPUs) for general purpose processing--an approach termed *GPGPU* (General-Purpose
computing on Graphics Processing Units). CUDA enables dramatic increases in computing
performance by harnessing the power of the GPU's massively parallel architecture.

CUDA was first released in 2007 and has since become the dominant platform for GPU
computing in scientific research, machine learning, computer vision, and various
high-performance computing applications. Unlike traditional CPU programming, where
a few powerful cores execute instructions sequentially, CUDA enables developers to
leverage thousands of smaller, efficient cores working in parallel.

The CUDA platform includes:
- A C/C++ language extension for GPU programming
- A software development kit (SDK) with libraries and tools
- A runtime API for managing GPU devices and memory
- Optimised libraries for common operations (cuBLAS, cuFFT, cuDNN, etc.)


### Architecture

#### Thread Hierarchy

CUDA organizes parallel execution into a hierarchical structure:

```
Grid
├── Block 0
│   ├── Thread 0
│   ├── Thread 1
│   ├── ...
│   └── Thread N
├── Block 1
│   ├── Thread 0
│   └── ...
└── Block M
```

- *Thread*: The basic unit of execution. Each thread executes the same kernel code with a unique ID.
- *Block*: A group of threads that can cooperate through shared memory and synchronization. Blocks execute independently.
- *Grid*: A collection of blocks that execute a kernel function.

This hierarchy maps directly to GPU hardware, where blocks are scheduled on
*Streaming Multiprocessors (SMs)*, and threads within a block execute in groups of 32 called *warps*.


#### Memory Hierarchy

CUDA provides several memory spaces with different scopes and access speeds:

| Memory Type | Scope | Speed | Size | Lifetime |
|-------------|-------|-------|------|----------|
| *Registers* | Per-thread | Fastest | ~64KB per SM | Kernel execution |
| *Shared Memory* | Per-block | Very fast | ~48-164KB per SM | Kernel execution |
| *Local Memory* | Per-thread | Slow (off-chip) | Limited | Kernel execution |
| *Global Memory* | All threads | Slow (off-chip) | GBs (device RAM) | Application |
| *Constant Memory* | All threads | Fast (cached) | 64KB | Application |
| *Texture Memory* | All threads | Fast (cached) | Variable | Application |


#### Example Memory Layout

```
┌─────────────────────────────────────────┐
│           GPU Device (Global Memory)    │
│  ┌───────────────────────────────────┐  │
│  │   Streaming Multiprocessor (SM)   │  │
│  │  ┌──────────────────────────────┐ │  │
│  │  │   Shared Memory (Fast)       │ │  │
│  │  ├──────────────────────────────┤ │  │
│  │  │   Registers  │  Registers    │ │  │
│  │  │   Thread 0   │  Thread 1     │ │  │
│  │  └──────────────────────────────┘ │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### Programming Model

#### Kernel Functions

A *kernel* is a function that runs on the GPU. It's defined using the `__global__`
keyword and executed by many threads in parallel.

```cuda
// CPU code (host)
__global__ void vectorAdd(float *a, float *b, float *c, int n) {
    // Calculate unique thread index
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    // Perform computation
    if (idx < n) {
        c[idx] = a[idx] + b[idx];
    }
}

int main() {
    // Allocate and initialize data...
    
    // Launch kernel with 256 blocks, 256 threads per block
    vectorAdd<<<256, 256>>>(d_a, d_b, d_c, n);
    
    // Synchronize and copy results back...
}
```

#### Execution Configuration

Kernels are launched with the syntax: `kernel<<<gridDim, blockDim>>>(args)`

- `gridDim`: Number of blocks in the grid (can be 1D, 2D, or 3D)
- `blockDim`: Number of threads per block (can be 1D, 2D, or 3D)

Example configurations:
```cuda
// 1D: 256 blocks × 256 threads = 65,536 total threads
myKernel<<<256, 256>>>(args);

// 2D: 16×16 blocks × 16×16 threads per block = 65,536 total threads
dim3 grid(16, 16);
dim3 block(16, 16);
myKernel<<<grid, block>>>(args);
```

#### Thread Indexing

Built-in variables help identify each thread:

```cuda
// 1D indexing
int idx = blockIdx.x * blockDim.x + threadIdx.x;

// 2D indexing (e.g., for matrices)
int row = blockIdx.y * blockDim.y + threadIdx.y;
int col = blockIdx.x * blockDim.x + threadIdx.x;

// 3D indexing
int x = blockIdx.x * blockDim.x + threadIdx.x;
int y = blockIdx.y * blockDim.y + threadIdx.y;
int z = blockIdx.z * blockDim.z + threadIdx.z;
```

### Memory Management

CUDA requires explicit memory management between host (CPU) and device (GPU):

```cuda
float *h_data;  // Host pointer
float *d_data;  // Device pointer

// Allocate host memory
h_data = (float*)malloc(size);

// Allocate device memory
cudaMalloc(&d_data, size);

// Copy host to device
cudaMemcpy(d_data, h_data, size, cudaMemcpyHostToDevice);

// Launch kernel to process d_data
kernel<<<grid, block>>>(d_data);

// Copy device to host
cudaMemcpy(h_data, d_data, size, cudaMemcpyDeviceToHost);

// Free memory
cudaFree(d_data);
free(h_data);
```


### Synchronization

#### Thread Synchronization

Threads within a block can synchronize using:

```cuda
__syncthreads();  // Barrier: all threads in block wait here
```

This is crucial when threads need to cooperate,
for example when using shared memory:

```cuda
__global__ void example(float *data) {
    __shared__ float shared_data[256];
    
    // Each thread loads data
    shared_data[threadIdx.x] = data[threadIdx.x];
    
    // Wait for all threads to finish loading
    __syncthreads();
    
    // Now all threads can safely access shared_data
    float value = shared_data[255 - threadIdx.x];
}
```

#### Device Synchronization

The host (CPU) can wait for GPU operations to complete:

```cuda
cudaDeviceSynchronize();  // Wait for all GPU operations to finish
```

### Atomic Operations

When multiple threads write to the same memory location,
*atomic operations* prevent race conditions:

```cuda
__global__ void histogram(int *data, int *hist, int n) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (idx < n) {
        int bin = data[idx];
        atomicAdd(&hist[bin], 1);  // Atomic increment
    }
}
```

Common atomic operations: `atomicAdd()`, `atomicSub()`, `atomicMin()`, `atomicMax()`, `atomicCAS()`, etc.

### Performance Considerations

#### Coalesced Memory Access

For optimal performance, threads in a warp should access consecutive memory locations:

```cuda
// Good: Coalesced access
int idx = blockIdx.x * blockDim.x + threadIdx.x;
data[idx] = value;  // Thread i accesses data[i]

// Bad: Strided access
int idx = threadIdx.x * stride;
data[idx] = value;  // Threads access non-consecutive locations
```

#### Occupancy

*Occupancy* is the ratio of active warps to maximum possible warps on an SM.
Higher occupancy typically means better performance by hiding memory latency.

Factors affecting occupancy:
- Register usage per thread
- Shared memory usage per block
- Block size (threads per block)

#### Divergent Branches

Threads in a warp execute in lockstep (SIMT - Single Instruction, Multiple Threads).
When threads take different paths in conditional code, both paths must execute serially:

```cuda
// Potentially divergent (bad if condition varies within warp)
if (threadIdx.x < 16) {
    // Path A
} else {
    // Path B - both paths execute if any thread needs them
}

// Better: aligned with warp boundaries (32 threads)
if (threadIdx.x < 32) {
    // All threads in warps 0-1 take this path
}
```

### Common Patterns

#### Map (Element-wise operations)

Each thread processes one element independently:

```cuda
__global__ void saxpy(float a, float *x, float *y, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) {
        y[i] = a * x[i] + y[i];  // y = a*x + y
    }
}
```

#### Reduction

Combining many values into one (e.g., sum, max):

```cuda
__global__ void reduce_sum(float *input, float *output, int n) {
    __shared__ float partial_sum[256];
    int tid = threadIdx.x;
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    // Load and initialize
    partial_sum[tid] = (idx < n) ? input[idx] : 0;
    __syncthreads();
    
    // Reduction in shared memory
    for (int stride = blockDim.x / 2; stride > 0; stride >>= 1) {
        if (tid < stride) {
            partial_sum[tid] += partial_sum[tid + stride];
        }
        __syncthreads();
    }
    
    // Write block result
    if (tid == 0) {
        output[blockIdx.x] = partial_sum[0];
    }
}
```

#### Stencil

Each element depends on its neighbors (e.g., convolution, blur):

```cuda
__global__ void blur(float *input, float *output, int width, int height) {
    int x = blockIdx.x * blockDim.x + threadIdx.x;
    int y = blockIdx.y * blockDim.y + threadIdx.y;
    
    if (x > 0 && x < width-1 && y > 0 && y < height-1) {
        float sum = 0.0f;
        for (int dy = -1; dy <= 1; dy++) {
            for (int dx = -1; dx <= 1; dx++) {
                sum += input[(y+dy)*width + (x+dx)];
            }
        }
        output[y*width + x] = sum / 9.0f;
    }
}
```

### CUDA Libraries

NVIDIA provides highly optimized libraries for common operations:

- *cuBLAS*: Basic Linear Algebra Subprograms (matrix operations)
- *cuFFT*: Fast Fourier Transforms
- *cuDNN*: Deep Neural Networks
- *cuSPARSE*: Sparse matrix operations
- *Thrust*: C++ template library for parallel algorithms
- *cuRAND*: Random number generation
- *NPP*: Image and video processing

### Applications

CUDA is widely used in:

- *Machine Learning & AI*: Training neural networks (PyTorch, TensorFlow)
- *Scientific Computing*: Molecular dynamics, climate modeling, fluid dynamics
- *Computer Vision*: Image processing, object detection, video analysis
- *Financial Modeling*: Risk analysis, options pricing, Monte Carlo simulations
- *Cryptocurrency*: Bitcoin mining, blockchain validation
- *Medical Imaging*: CT reconstruction, MRI processing
- *Rendering*: Ray tracing, video encoding/decoding

### Hardware Requirements

- NVIDIA GPU with compute capability 3.0 or higher
- CUDA Toolkit (includes compiler, libraries, and tools)
- Compatible C/C++ compiler (gcc, clang, MSVC)

#### Compute Capability

Different GPU architectures have different capabilities:

| Architecture | Compute Capability | Example GPUs | Year |
|--------------|--------------------|--------------|------|
| Kepler | 3.0 - 3.7 | GTX 780, Tesla K40 | 2012 |
| Maxwell | 5.0 - 5.3 | GTX 980, Titan X | 2014 |
| Pascal | 6.0 - 6.2 | GTX 1080, Tesla P100 | 2016 |
| Volta | 7.0 - 7.2 | Titan V, Tesla V100 | 2017 |
| Turing | 7.5 | RTX 2080, Titan RTX | 2018 |
| Ampere | 8.0 - 8.6 | RTX 3090, A100 | 2020 |
| Hopper | 9.0 | H100 | 2022 |

### Example: Complete Vector Addition

```cuda
#include <stdio.h>
#include <cuda_runtime.h>

__global__ void vectorAdd(const float *A, const float *B, float *C, int N) {
    int i = blockDim.x * blockIdx.x + threadIdx.x;
    if (i < N) {
        C[i] = A[i] + B[i];
    }
}

int main() {
    int N = 1000000;
    size_t size = N * sizeof(float);
    
    // Allocate host memory
    float *h_A = (float*)malloc(size);
    float *h_B = (float*)malloc(size);
    float *h_C = (float*)malloc(size);
    
    // Initialize host arrays
    for (int i = 0; i < N; i++) {
        h_A[i] = i;
        h_B[i] = i * 2;
    }
    
    // Allocate device memory
    float *d_A, *d_B, *d_C;
    cudaMalloc(&d_A, size);
    cudaMalloc(&d_B, size);
    cudaMalloc(&d_C, size);
    
    // Copy host to device
    cudaMemcpy(d_A, h_A, size, cudaMemcpyHostToDevice);
    cudaMemcpy(d_B, h_B, size, cudaMemcpyHostToDevice);
    
    // Launch kernel
    int threadsPerBlock = 256;
    int blocksPerGrid = (N + threadsPerBlock - 1) / threadsPerBlock;
    vectorAdd<<<blocksPerGrid, threadsPerBlock>>>(d_A, d_B, d_C, N);
    
    // Copy device to host
    cudaMemcpy(h_C, d_C, size, cudaMemcpyDeviceToHost);
    
    // Verify results
    for (int i = 0; i < 10; i++) {
        printf("%.0f + %.0f = %.0f\n", h_A[i], h_B[i], h_C[i]);
    }
    
    // Free memory
    cudaFree(d_A);
    cudaFree(d_B);
    cudaFree(d_C);
    free(h_A);
    free(h_B);
    free(h_C);
    
    return 0;
}
```

Compile with: `nvcc -o vector_add vector_add.cu`

### Advantages

- *Massive Parallelism*: Thousands of cores executing simultaneously
- *High Memory Bandwidth*: Up to 900 GB/s on modern GPUs
- *Mature Ecosystem*: Extensive libraries, tools, and community support
- *Wide Adoption*: Industry standard for GPU computing
- *Ease of Use*: C/C++ extensions make it accessible to traditional programmers

### Limitations

- *NVIDIA-only*: Only works on NVIDIA GPUs (AMD uses ROCm, Intel uses oneAPI)
- *Memory Transfers*: Copying data between CPU and GPU can be a bottleneck
- *Programming Complexity*: Requires understanding of parallel programming concepts
- *Debugging Difficulty*: Parallel bugs can be harder to find and fix
- *Limited Recursion*: GPU recursion support is limited
- *Hardware Dependency*: Code optimization often tied to specific GPU architectures

### Alternatives

- *OpenCL*: Open standard for heterogeneous parallel programming (multi-vendor)
- *ROCm*: AMD's GPU computing platform
- *oneAPI*: Intel's unified programming model
- *Metal*: Apple's GPU framework for macOS/iOS
- *DirectCompute*: Microsoft's GPU computing API for Windows
- *Vulkan Compute*: Cross-platform compute shaders


### References

- [NVIDIA CUDA Documentation](https://docs.nvidia.com/cuda/)
- [CUDA C Programming Guide](https://docs.nvidia.com/cuda/cuda-c-programming-guide/)
- [CUDA Toolkit Download](https://developer.nvidia.com/cuda-downloads)

- Mark Harris, "An Even Easier Introduction to CUDA", NVIDIA Developer Blog
- David Kirk and Wen-mei Hwu, "Programming Massively Parallel Processors: A Hands-on Approach"
