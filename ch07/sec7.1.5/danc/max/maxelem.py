import multiprocessing as mp

def find_max(arr, low, high):
    if low == high:
        return arr[low]
    
    mid = low + (high - low) // 2
    
    # Run left and right in parallel processes
    with mp.Pool(2) as pool:
        left_max = pool.apply_async(find_max, (arr, low, mid))
        right_max = pool.apply_async(find_max, (arr, mid + 1, high))
        results = [left_max.get(), right_max.get()]
    
    return max(results)

if __name__ == "__main__":
    arr = [13, 1, 45, 7, 92, 33, 58, 105, 22, 67]
    max_val = find_max(arr, 0, len(arr) - 1)
    print(f"Maximum element = {max_val}")
