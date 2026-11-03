import multiprocessing as mp

def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result

# Processes in a Pool may not start processes of their own, so the
# recursion uses plain Process objects: the left half is sorted in a new
# process while this process sorts the right half. Below a certain
# depth the work is too small to be worth a new process.
PARALLEL_DEPTH = 2

def _worker(conn, arr, depth):
    conn.send(merge_sort(arr, depth))
    conn.close()

def merge_sort(arr, depth=PARALLEL_DEPTH):
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    if depth <= 0:
        return merge(merge_sort(arr[:mid], 0), merge_sort(arr[mid:], 0))
    
    receiver, sender = mp.Pipe(duplex=False)
    left_process = mp.Process(target=_worker, args=(sender, arr[:mid], depth - 1))
    left_process.start()
    right = merge_sort(arr[mid:], depth - 1)
    left = receiver.recv()
    left_process.join()
    
    return merge(left, right)

if __name__ == "__main__":
    arr = [64, 34, 25, 12, 22, 11, 90]
    sorted_arr = merge_sort(arr)
    print(f"Sorted: {sorted_arr}")
