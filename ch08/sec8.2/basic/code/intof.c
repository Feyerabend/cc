#include <stdint.h>
#include <stdlib.h>

/* Vulnerable: count * item_size may silently wrap around */
void *alloc_items(int count, int item_size) {
    return malloc(count * item_size);
}

/* Safe: use size_t and verify before multiplying */
void *alloc_items_safe(size_t count, size_t item_size) {
    if (item_size > 0 && count > SIZE_MAX / item_size)
        return NULL;
    return malloc(count * item_size);
}
