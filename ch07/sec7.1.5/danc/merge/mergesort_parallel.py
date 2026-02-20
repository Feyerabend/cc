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

def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    with mp.Pool(2) as pool:
        left = pool.apply_async(merge_sort, (arr[:mid],))
        right = pool.apply_async(merge_sort, (arr[mid:],))
        left, right = left.get(), right.get()
    
    return merge(left, right)

if __name__ == "__main__":
    arr = [64, 34, 25, 12, 22, 11, 90]
    sorted_arr = merge_sort(arr)
    print(f"Sorted: {sorted_arr}")
