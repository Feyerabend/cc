#ifndef PROPERTY_TYPES_H
#define PROPERTY_TYPES_H

#include <stddef.h>
#include <stdbool.h>

typedef struct IntList {
    int* data;
    int length;
    int capacity;
} IntList;

typedef struct String {
    char* data;
    int length;
    int capacity;
} String;

typedef struct Tuple2 {
    void* first;
    void* second;
} Tuple2;

typedef struct Tuple3 {
    void* first;
    void* second;
    void* third;
} Tuple3;

IntList* int_list_create(int capacity);
IntList* int_list_copy(IntList* src);
void int_list_free(IntList* list);
void int_list_append(IntList* list, int value);

String* string_create(int capacity);
String* string_copy(String* src);
void string_free(String* str);
void string_append_char(String* str, char c);
void string_append(String* str, const char* data, int len);

Tuple2* tuple2_create(void* first, void* second);
void tuple2_free(Tuple2* tuple, void (*free_first)(void*), void (*free_second)(void*));

Tuple3* tuple3_create(void* first, void* second, void* third);
void tuple3_free(
    Tuple3* tuple,
    void (*free_first)(void*),
    void (*free_second)(void*),
    void (*free_third)(void*)
);

#endif
