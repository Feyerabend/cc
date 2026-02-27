#include <stdio.h>
#include <stdlib.h>


/*  Comparison callbacks  */

int ascending(const void* a, const void* b) {
    return (*(int*)a - *(int*)b);
}

int descending(const void* a, const void* b) {
    return (*(int*)b - *(int*)a);
}


/*  custom_sort: bubble sort driven by a comparison callback  */

void custom_sort(int* arr, size_t count,
                 int (*cmp)(const void*, const void*)) {
    for (size_t i = 0; i < count - 1; i++)
        for (size_t j = 0; j < count - i - 1; j++)
            if (cmp(&arr[j], &arr[j + 1]) > 0) {
                int tmp  = arr[j];
                arr[j]   = arr[j + 1];
                arr[j + 1] = tmp;
            }
}


/*  apply_to_each: map-style transform using a callback  */

typedef void (*transform_fn)(int* val, size_t idx);

void apply_to_each(int* arr, size_t count, transform_fn fn) {
    for (size_t i = 0; i < count; i++)
        fn(&arr[i], i);
}

void double_it(int* val, size_t idx) {
    (void)idx; *val *= 2;
}
void add_ten(int* val, size_t idx) {
    (void)idx; *val += 10;
}
void print_it(int* val, size_t idx) {
    printf("  [%zu] = %d\n", idx, *val);
}


/*  run_pipeline: execute a sequence of transform callbacks  */

void run_pipeline(int* arr, size_t count,
                  transform_fn* pipeline, size_t stages) {
    for (size_t s = 0; s < stages; s++)
        apply_to_each(arr, count, pipeline[s]);
}


/*  helpers  */

static void print_array(const char* label, int* arr, size_t count) {
    printf("%s", label);
    for (size_t i = 0; i < count; i++) printf("%d ", arr[i]);
    printf("\n");
}


/*  main  */

int main(void) {
    /* --- Demo 1: sort ascending vs descending via callback swap --- */
    int arr1[] = {5, 2, 8, 1, 9, 3};
    size_t n1 = sizeof(arr1) / sizeof(arr1[0]);

    print_array("Original:   ", arr1, n1);
    custom_sort(arr1, n1, ascending);
    print_array("Ascending:  ", arr1, n1);
    custom_sort(arr1, n1, descending);
    print_array("Descending: ", arr1, n1);

    printf("\n");

    /* --- Demo 2: apply_to_each ---  */
    int arr2[] = {1, 2, 3, 4, 5};
    size_t n2 = sizeof(arr2) / sizeof(arr2[0]);

    printf("apply double_it then print_it:\n");
    apply_to_each(arr2, n2, double_it);   /* {2, 4, 6, 8, 10} */
    apply_to_each(arr2, n2, print_it);

    printf("\n");

    /* --- Demo 3: pipeline (double → add_ten → print) --- */
    int arr3[] = {1, 2, 3};
    size_t n3 = sizeof(arr3) / sizeof(arr3[0]);

    transform_fn steps[] = { double_it, add_ten, print_it };
    size_t stages = sizeof(steps) / sizeof(steps[0]);

    printf("pipeline (x2 then +10 then print):\n");
    run_pipeline(arr3, n3, steps, stages);
    /* prints: [0]=12  [1]=14  [2]=16 */

    return 0;
}
