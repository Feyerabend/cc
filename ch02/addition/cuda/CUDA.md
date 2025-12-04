
*Project: Explore non-conventional execution models outside of von Neumann
or Harvard, historically or currently, and look at their inner workings.*


## Overview of the Program 'cuda.py'

This Python program is a simulation of a GPU-like environment using a fictional CUDA
Virtual Machine (CUDAVM). The program mimics the concept of CUDA (Compute Unified Device
Architecture), which is a parallel computing platform and programming model developed
by NVIDIA for leveraging the power of GPUs for general-purpose computation (GPGPU).

In this simulation, the program doesn't actually execute on a real GPU but emulates
how kernels (functions executed by many threads in parallel on the GPU) are launched
and executed using threads in Python. The core purpose of this simulation is to mimic
a vector addition operation using the same parallelisation strategies that a GPU might
use, giving us a basic understanding of how CUDA and GPUs work for parallel tasks.

The simulation includes:

- Memory Management: A global memory space is emulated where data is stored and accessed
  by different threads.

- Kernel Definition and Launching: A simple vector addition kernel is defined, which
  is then executed in parallel across multiple threads and blocks (the basic unit of
  parallel execution in CUDA).

- Thread Execution: Each thread performs an addition operation on corresponding elements
  of two input vectors and stores the result in an output vector.


### What is CUDA?

CUDA is a parallel computing platform and programming model created by NVIDIA that
allows developers to use GPUs for more than just graphics rendering. The platform
provides an API that allows developers to write code that can be executed on NVIDIA
GPUs to accelerate a variety of computationally intensive applications (such as
simulations, machine learning, and scientific computing).

A key feature of CUDA is its ability to divide computations into kernels, which are
functions that can be executed in parallel across many threads. These kernels are
launched in blocks of threads, and these blocks are further organized into a grid
structure. The threads in the same block can communicate and share data more easily
than threads in different blocks.

Key Concepts in the Program and their CUDA Equivalents

1. Global Memory:
In the simulation, the global memory is represented as a dictionary (global_memory)
where the data for arrays (such as a, b, and c) are stored. This memory is accessible
by all threads, much like global memory in CUDA.
In real CUDA, global memory is the main memory space of the GPU, where large data sets
are stored for processing. Accessing and managing global memory efficiently is crucial
for performance on GPUs, as improper use can lead to bottlenecks.

2. Kernel:
The kernel in the simulation is the function that is executed by multiple threads in
parallel. The kernel (_vector_add_kernel) adds corresponding elements of two vectors
a and b, and stores the result in c. This is an example of a simple computational
task that can benefit from parallel execution.
In actual CUDA programming, a kernel is written using a specific CUDA C API and executed
by thousands (or more) threads in parallel. Each thread executes the kernel independently,
with different data. This parallelization is what enables GPUs to handle tasks that
would be too slow for CPUs to process efficiently.

3. Blocks and Threads:
The concept of blocks and threads is key in CUDA. In the simulation, the launch_kernel
method mimics launching a kernel with a given number of blocks (blocks_per_grid) and
threads per block (threads_per_block). Each thread executes the kernel function
*independently*, and the blocks are used to organize the execution of the threads.
- Blocks are a group of threads that can cooperate and share data via shared memory in CUDA.
- Threads are the basic units of execution, and in this simulation, they represent the
  individual parallel operations (like adding elements of vectors).

4.	Thread Indexing:
The thread_idx variable represents the unique index of each thread in the grid. In CUDA,
this is calculated using the block and thread indices, ensuring that each thread works
on different data.

```text
thread_idx = block_id * self.threads_per_block + thread_id
```
This allows threads to be assigned different pieces of work, which is essential in achieving
parallelism.


### How the Program Simulates CUDA Execution

* Memory Allocation: The CUDAVM class emulates the allocation of memory for vectors a, b, and c.
In a real GPU environment, memory allocation is done using CUDA’s memory management functions,
such as cudaMalloc, to allocate space on the GPU.

* Kernel Execution: The CUDAInterpreter class simulates the execution of a kernel. The kernel
(_vector_add_kernel) is defined as a Python function that adds elements of two vectors. In CUDA,
kernels are typically written in C and executed by many threads in parallel.

* Parallel Execution: The launch_kernel method spawns multiple threads in Python, with each
thread executing the kernel on a piece of data. While Python threads are not real GPU threads,
they emulate the process of launching parallel computations.

Compare: [CUDA Sample](https://github.com/NVIDIA/cuda-samples/blob/master/Samples/0_Introduction/vectorAdd/vectorAdd.cu).


### Why Use CUDA and GPUs?

1. Parallelism:
The main advantage of using CUDA and GPUs is the ability to process many tasks simultaneously.
GPUs have thousands of cores, each capable of executing a thread independently. This is ideal
for tasks that can be divided into smaller, parallel sub-tasks, such as matrix multiplication,
image processing, simulations, or deep learning.

2. Speed:
For certain types of workloads, GPUs can be orders of magnitude faster than CPUs. This is due
to the massive parallelism in GPUs. For example, scientific simulations that involve large matrix
operations can run much faster on a GPU than on a CPU.

3. Efficiency in Large-Scale Data Processing:
Applications that deal with large amounts of data, such as training neural networks or processing
large datasets (e.g., in physics simulations), can benefit greatly from CUDA. A single GPU can
handle thousands of parallel threads, making it suitable for workloads that require significant
computational power.


### Use Cases of CUDA and GPUs

* Machine Learning & Deep Learning: Many deep learning frameworks, such as TensorFlow and PyTorch,
use CUDA to accelerate training of large models on GPUs. GPUs significantly speed up matrix operations,
which are a core component of training neural networks.

* Scientific Simulations: CUDA is widely used in scientific computing to perform simulations, such
as fluid dynamics, molecular modeling, and physics simulations, which involve complex calculations
that can be parallelised.

* Video and Image Processing: Tasks like video encoding/decoding, real-time image processing, and
rendering benefit from the parallel processing power of GPUs.

* Cryptography: Tasks like hashing, encryption, and decryption can be accelerated using GPUs to
process many data points in parallel.


### Why the Program Simulates CUDA?

* Learning & Understanding Parallel Computing: This simulation helps learners understand the basic
principles of parallel computing and how CUDA works in terms of threads, blocks, and memory.

* Platform Agnostic: By using Python and threading, the program doesn’t require a physical GPU and
can run on any machine. It is a way to conceptually understand how CUDA works without needing access
to a GPU.

* Simple Parallelization Example: The vector addition example is a fundamental operation that highlights
how data can be split and processed concurrently. While this is a basic operation, it scales to much
larger tasks in actual CUDA programming.


### Conclusion

This program is a basic simulation of how CUDA operates, mimicking the parallel processing that happens
on a GPU. The program models memory management, kernel execution, and parallelization through threads
in Python. In real CUDA programming, similar tasks would be executed on an NVIDIA GPU, which would
allow for a much more efficient and faster execution of large-scale parallel computations. The program
serves as an educational tool to understand the basics of CUDA and parallel computing in general.

As a simulation the CUDA Virtual Machine (CUDAVM) in the program doesn’t strictly follow von Neumann
or Harvard models, even though in practice it is run on a von Neumann machine (ordinary Python on a PC).
Instead, it introduces (or simulates) a highly parallelized execution model that is unique to GPUs.
However, you can draw parallels to both architectures:

- From the von Neumann perspective, the program uses shared memory, with the kernel functioning as
  the central "control unit" managing the threads' execution in parallel.

- From the Harvard perspective, there is a loose separation of different memory types (global,
  shared, and local) accessed in parallel by the threads.

Remember that in practice, modern GPUs, which the program simulates, are not directly based on either
von Neumann or Harvard architectures but combine elements from both, along with specialized hardware
designed to efficiently handle massively parallel computations.

