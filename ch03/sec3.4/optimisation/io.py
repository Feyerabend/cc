import time
import os

# Generate test data
def generate_test_file(filename, lines=100000):
    with open(filename, 'w') as f:
        for i in range(lines):
            f.write(f"Line {i}: Some sample data with numbers {i * 2}\n")

# UNOPTIMISED: Reading line by line
def read_line_by_line(filename):
    lines = []
    with open(filename, 'r') as f:
        for line in f:
            lines.append(line.strip())
    return lines

# OPTIMISED: Reading with buffering
def read_buffered(filename, buffer_size=8192):
    lines = []
    with open(filename, 'r', buffering=buffer_size) as f:
        for line in f:
            lines.append(line.strip())
    return lines

# OPTIMISED: Read entire file at once
def read_all_at_once(filename):
    with open(filename, 'r') as f:
        content = f.read()
    return content.splitlines()

# OPTIMISED: Using readlines()
def read_with_readlines(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    return [line.strip() for line in lines]

# UNOPTIMISED: Writing line by line without buffering
def write_line_by_line(filename, lines):
    with open(filename, 'w') as f:
        for line in lines:
            f.write(line + '\n')

# OPTIMISED: Writing with buffering
def write_buffered(filename, lines, buffer_size=8192):
    with open(filename, 'w', buffering=buffer_size) as f:
        for line in lines:
            f.write(line + '\n')

# OPTIMISED: Batch writing
def write_batched(filename, lines):
    with open(filename, 'w') as f:
        f.write('\n'.join(lines) + '\n')

# UNOPTIMISED: Multiple file operations
def process_multiple_files_unopt(input_files, output_file):
    all_data = []
    for filename in input_files:
        with open(filename, 'r') as f:
            data = f.read()
            all_data.append(data)
    
    with open(output_file, 'w') as f:
        for data in all_data:
            f.write(data)

# OPTIMISED: Stream processing without loading all to memory
def process_multiple_files_opt(input_files, output_file):
    with open(output_file, 'w') as out_f:
        for filename in input_files:
            with open(filename, 'r') as in_f:
                for chunk in iter(lambda: in_f.read(8192), ''):
                    out_f.write(chunk)

def benchmark_io_operations():
    print("-- I/O Optimisation Benchmarks --\n")
    
    test_file = "test_data.txt"
    output_file = "output_data.txt"
    
    # Generate test data
    print("Generating test data...")
    generate_test_file(test_file)
    file_size = os.path.getsize(test_file) / (1024 * 1024)  # MB
    print(f"Test file size: {file_size:.2f} MB\n")
    
    # Reading benchmarks
    print("--- Reading Benchmarks ---")
    
    start = time.time()
    data1 = read_line_by_line(test_file)
    time1 = time.time() - start
    print(f"Line-by-line (default buffer): {time1:.4f}s")
    
    start = time.time()
    data2 = read_buffered(test_file, buffer_size=65536)
    time2 = time.time() - start
    print(f"Buffered (64KB buffer): {time2:.4f}s ({time1/time2:.2f}x faster)")
    
    start = time.time()
    data3 = read_all_at_once(test_file)
    time3 = time.time() - start
    print(f"Read all at once: {time3:.4f}s ({time1/time3:.2f}x faster)")
    
    start = time.time()
    data4 = read_with_readlines(test_file)
    time4 = time.time() - start
    print(f"Using readlines(): {time4:.4f}s ({time1/time4:.2f}x faster)\n")
    
    # Writing benchmarks
    print("--- Writing Benchmarks ---")
    
    test_lines = [f"Line {i}" for i in range(50000)]
    
    start = time.time()
    write_line_by_line(output_file, test_lines)
    time1 = time.time() - start
    print(f"Line-by-line write: {time1:.4f}s")
    
    start = time.time()
    write_buffered(output_file, test_lines, buffer_size=65536)
    time2 = time.time() - start
    print(f"Buffered write (64KB): {time2:.4f}s ({time1/time2:.2f}x faster)")
    
    start = time.time()
    write_batched(output_file, test_lines)
    time3 = time.time() - start
    print(f"Batched write: {time3:.4f}s ({time1/time3:.2f}x faster)\n")
    
    # Cleanup
    os.remove(test_file)
    os.remove(output_file)
    
    print("\n=== Key Takeaways ===")
    print("1. Use larger buffer sizes for sequential I/O")
    print("2. Batch operations when possible")
    print("3. Stream large files instead of loading entirely")
    print("4. Use appropriate read/write methods for your use case")

if __name__ == "__main__":
    benchmark_io_operations()
