import threading

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

def insertion_sort(arr):
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
    return arr

def merge_sort(arr, threshold=32):
    if len(arr) <= 1:
        return arr
    
    # If small, use sequential insertion sort (modifies in-place, but return copy for consistency)
    if len(arr) < threshold:
        return insertion_sort(arr[:])  # Copy to avoid modifying original prematurely
    
    mid = len(arr) // 2
    
    left_result = None
    right_result = None
    
    # Threads for parallel execution
    left_thread = threading.Thread(target=lambda: setattr(merge_sort, 'left_result', merge_sort(arr[:mid], threshold)))
    right_thread = threading.Thread(target=lambda: setattr(merge_sort, 'right_result', merge_sort(arr[mid:], threshold)))
    
    left_thread.start()
    right_thread.start()
    
    left_thread.join()
    right_thread.join()
    
    return merge(merge_sort.left_result, merge_sort.right_result)

if __name__ == "__main__":
    arr = [64, 34, 25, 12, 22, 11, 90]
    sorted_arr = merge_sort(arr)
    print(f"Sorted: {sorted_arr}")
