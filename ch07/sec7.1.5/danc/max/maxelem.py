import multiprocessing as mp

# Processes in a Pool may not start processes of their own, so the
# recursion uses plain Process objects: the left half runs in a new
# process while this process handles the right half. Below a certain
# depth the work is too small to be worth a new process.
PARALLEL_DEPTH = 2

def _worker(conn, arr, low, high, depth):
    conn.send(find_max(arr, low, high, depth))
    conn.close()

def find_max(arr, low, high, depth=PARALLEL_DEPTH):
    if low == high:
        return arr[low]
    
    mid = low + (high - low) // 2
    
    if depth <= 0:
        return max(find_max(arr, low, mid, 0), find_max(arr, mid + 1, high, 0))
    
    # Run left and right in parallel processes
    receiver, sender = mp.Pipe(duplex=False)
    left_process = mp.Process(target=_worker, args=(sender, arr, low, mid, depth - 1))
    left_process.start()
    right_max = find_max(arr, mid + 1, high, depth - 1)
    left_max = receiver.recv()
    left_process.join()
    
    return max(left_max, right_max)

if __name__ == "__main__":
    arr = [13, 1, 45, 7, 92, 33, 58, 105, 22, 67]
    max_val = find_max(arr, 0, len(arr) - 1)
    print(f"Maximum element = {max_val}")
