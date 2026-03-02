#include <stdio.h>

typedef struct {
    void (*speak)(void*);
} Animal;

typedef struct {
    Animal base;
} Dog;

typedef struct {
    Animal base;
} Cat;

void dog_speak(void *self) { printf("Woof\n"); }
void cat_speak(void *self) { printf("Meow\n"); }

void animal_init(Animal *a, void (*speak)(void*)) {
    a->speak = speak;
}

int main() {
    Dog dog;
    Cat cat;
    animal_init(&dog.base, dog_speak);
    animal_init(&cat.base, cat_speak);

    Animal *animals[] = {&dog.base, &cat.base};
    for (int i = 0; i < 2; i++) {
        animals[i]->speak(animals[i]); // Output: Woof, Meow
    }
    return 0;
}

// This code demonstrates a simple implementation of a virtual table (vtable) in C.
// It defines a base structure `Animal` with a function pointer for the `speak` method.
// Two derived structures `Dog` and `Cat` inherit from `Animal`.
// The `animal_init` function initialises the base structure with the appropriate method.
// The `main` function creates instances of `Dog` and `Cat`, initialises them, and calls
// the `speak` method through the base structure pointer, demonstrating polymorphism.
