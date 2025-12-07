import time
import sys

def benchmark_string_concat():
    print("-- String Concatenation Optimisation --\n")
    n = 10000
    
    # UNOPTIMISED: Using + operator in loop
    start = time.time()
    result = ""
    for i in range(n):
        result += str(i) + ","
    time1 = time.time() - start
    print(f"Using + operator: {time1:.4f}s")
    
    # OPTIMISED: Using list and join
    start = time.time()
    parts = []
    for i in range(n):
        parts.append(str(i))
    result = ",".join(parts)
    time2 = time.time() - start
    print(f"Using list + join: {time2:.4f}s ({time1/time2:.2f}x faster)")
    
    # OPTIMIED: Using list comprehension
    start = time.time()
    result = ",".join(str(i) for i in range(n))
    time3 = time.time() - start
    print(f"List comprehension + join: {time3:.4f}s ({time1/time3:.2f}x faster)")
    
    # OPTIMISED: Using string builder pattern (for very large strings)
    start = time.time()
    result = ",".join(map(str, range(n)))
    time4 = time.time() - start
    print(f"Using map + join: {time4:.4f}s ({time1/time4:.2f}x faster)\n")


def benchmark_string_search():
    print("-- String Search Optimisation --\n")
    
    text = "a" * 100000 + "needle" + "b" * 100000
    
    # UNOPTIMISED: Linear search
    start = time.time()
    found = False
    search = "needle"
    for i in range(len(text) - len(search) + 1):
        if text[i:i+len(search)] == search:
            found = True
            break
    time1 = time.time() - start
    print(f"Manual linear search: {time1:.6f}s")
    
    # OPTIMISED: Built-in find
    start = time.time()
    pos = text.find("needle")
    time2 = time.time() - start
    print(f"Built-in find(): {time2:.6f}s ({time1/time2:.1f}x faster)")
    
    # OPTIMISED: Using 'in' operator
    start = time.time()
    found = "needle" in text
    time3 = time.time() - start
    print(f"Using 'in' operator: {time3:.6f}s ({time1/time3:.1f}x faster)\n")


def benchmark_string_formatting():
    print("-- String Formatting Optimisation --\n")
    n = 50000
    
    # UNOPTIMISED: Using % formatting
    start = time.time()
    results = []
    for i in range(n):
        results.append("Number: %d, Square: %d" % (i, i*i))
    time1 = time.time() - start
    print(f"% formatting: {time1:.4f}s")
    
    # BETTER: Using .format()
    start = time.time()
    results = []
    for i in range(n):
        results.append("Number: {}, Square: {}".format(i, i*i))
    time2 = time.time() - start
    print(f".format() method: {time2:.4f}s ({time1/time2:.2f}x faster)")
    
    # OPTIMISED: Using f-strings
    start = time.time()
    results = []
    for i in range(n):
        results.append(f"Number: {i}, Square: {i*i}")
    time3 = time.time() - start
    print(f"f-strings: {time3:.4f}s ({time1/time3:.2f}x faster)")
    
    # MOST OPTIMISED: f-strings with list comprehension
    start = time.time()
    results = [f"Number: {i}, Square: {i*i}" for i in range(n)]
    time4 = time.time() - start
    print(f"f-strings + comprehension: {time4:.4f}s ({time1/time4:.2f}x faster)\n")


def benchmark_string_splitting():
    print("-- String Splitting Optimisation --\n")
    
    text = ",".join(str(i) for i in range(10000))
    
    # UNOPTIMISED: Manual splitting
    start = time.time()
    parts = []
    current = ""
    for char in text:
        if char == ",":
            parts.append(current)
            current = ""
        else:
            current += char
    if current:
        parts.append(current)
    time1 = time.time() - start
    print(f"Manual splitting: {time1:.4f}s")
    
    # OPTIMISED: Built-in split
    start = time.time()
    parts = text.split(",")
    time2 = time.time() - start
    print(f"Built-in split(): {time2:.4f}s ({time1/time2:.1f}x faster)\n")


def benchmark_string_case():
    print("-- String Case Conversion --\n")
    
    words = ["Hello", "World", "Python", "Optimisation"] * 10000
    
    # UNOPTIMISED: Converting each time
    start = time.time()
    count = 0
    for word in words:
        if word.lower() == "python":
            count += 1
    time1 = time.time() - start
    print(f"Convert each time: {time1:.4f}s")
    
    # OPTIMISED: Pre-convert comparison string
    start = time.time()
    count = 0
    target = "python"
    for word in words:
        if word.lower() == target:
            count += 1
    time2 = time.time() - start
    print(f"Pre-converted target: {time2:.4f}s ({time1/time2:.2f}x faster)")
    
    # MORE OPTIMISED: Use str.casefold() for better comparison
    start = time.time()
    count = 0
    target = "python"
    for word in words:
        if word.casefold() == target:
            count += 1
    time3 = time.time() - start
    print(f"Using casefold(): {time3:.4f}s\n")


def main():
    print("=" * 40)
    print("STRING OPERATIONS OPTIMISATION BENCHMARKS")
    print("=" * 40 + "\n")
    
    benchmark_string_concat()
    benchmark_string_search()
    benchmark_string_formatting()
    benchmark_string_splitting()
    benchmark_string_case()
    
    print("\n=== Key Takeaways ===")
    print("1. Use join() for concatenating multiple strings")
    print("2. Use f-strings for formatting (Python 3.6+)")
    print("3. Use built-in string methods over manual loops")
    print("4. Pre-compute values outside loops when possible")
    print("5. List comprehensions are faster than loops")

if __name__ == "__main__":
    main()
