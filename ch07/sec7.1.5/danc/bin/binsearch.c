#include <stdio.h>

int binarySearchIterative(int arr[], int n, int target) {
    int low = 0, high = n - 1;

    while (low <= high) {
        int mid = low + (high - low) / 2;   // Avoids overflow

        if (arr[mid] == target)
            return mid;                     // Found!
        else if (arr[mid] < target)
            low = mid + 1;                  // Discard left half
        else
            high = mid - 1;                 // Discard right half
    }
    return -1;  // Not found
}

// binary search no recursive version, divide and conquer
int main() {
    int arr[] = {2, 5, 8, 12, 16, 23, 38, 45, 56, 67, 78};
    int n = sizeof(arr)/sizeof(arr[0]);
    int target = 23;

    int result = binarySearchIterative(arr, n, target);

    if (result != -1)
        printf("Target %d found at index %d\n", target, result);
    else
        printf("Target %d not found\n", target);

    return 0;
}
