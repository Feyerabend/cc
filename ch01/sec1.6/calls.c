#include <stdio.h>

// call by value
void modify_value(int x) {
    x = 999;
}

void demo_by_value() {
    int num = 42;
    modify_value(num);
    printf("By Value: %d (unchanged)\n", num);
}

// call by reference
void modify_reference(int *x) {
    *x = 999;
}

void demo_by_reference() {
    int num = 42;
    modify_reference(&num);
    printf("By Reference: %d (changed)\n", num);
}

// call by sharing
typedef struct {
    int value;
} Object;

void modify_object(Object *obj) {
    obj->value = 999;  // Changes the original
}

void reassign_object(Object *obj) {
    Object new = {999};
    obj = &new;  // Does NOT change the original
}

void demo_by_sharing() {
    Object obj1 = {42};
    modify_object(&obj1);
    printf("By Sharing (modify): %d (changed)\n", obj1.value);
    
    Object obj2 = {42};
    reassign_object(&obj2);
    printf("By Sharing (reassign): %d (unchanged)\n", obj2.value);
}

int main() {
    demo_by_value();
    demo_by_reference();
    demo_by_sharing();
    return 0;
}
