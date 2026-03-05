#include "generic_list.h"
#include <stdio.h>

DEFINE_LIST(int, int_list)

void print_int(int x) {
    printf("%d\n", x);
}

int main() {
    int_list_list list;
    int_list_init(&list);

    int_list_push_front(&list, 1);
    int_list_push_front(&list, 2);
    int_list_push_back(&list, 3);

    int_list_print(&list, print_int);

    int_list_replace(&list, 1, 10);
    int_list_remove(&list, 2);

    int_list_print(&list, print_int);

    int_list_clear(&list);
    return 0;
}
