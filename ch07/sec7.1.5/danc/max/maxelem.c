#include <stdio.h>

// Divide-and-Conquer: Find maximum using recursion
int findMax(int arr[], int low, int high) {
    // Base case: only one element
    if (low == high) {
        return arr[low];
    }

    // Divide: find middle
    int mid = low + (high - low) / 2;

    // Conquer: recursively find max in left and right halves
    int leftMax  = findMax(arr, low, mid);
    int rightMax = findMax(arr, mid + 1, high);

    // Combine: return the larger one
    return (leftMax > rightMax) ? leftMax : rightMax;
}

int main() {
    int arr[] = {13, 1, 45, 7, 92, 33, 58, 105, 22, 67};
    int n = sizeof(arr) / sizeof(arr[0]);

    int max = findMax(arr, 0, n - 1);

    printf("Array: ");
    for (int i = 0; i < n; i++) {
        printf("%d ", arr[i]);
    }
    printf("\nMaximum element = %d\n", max);

    return 0;
}
