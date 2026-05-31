#include "types.h"
#include <stdlib.h>
#include <string.h>

IntList* int_list_create(int capacity) {
    IntList* list = (IntList*)malloc(sizeof(IntList));
    list->capacity = capacity > 0 ? capacity : 8;
    list->length = 0;
    list->data = (int*)malloc(list->capacity * sizeof(int));
    return list;
}

IntList* int_list_copy(IntList* src) {
    IntList* list = int_list_create(src->capacity);
    list->length = src->length;
    memcpy(list->data, src->data, src->length * sizeof(int));
    return list;
}

void int_list_free(IntList* list) {
    if (list) {
        free(list->data);
        free(list);
    }
}

void int_list_append(IntList* list, int value) {
    if (list->length >= list->capacity) {
        list->capacity *= 2;
        list->data = (int*)realloc(list->data, list->capacity * sizeof(int));
    }
    list->data[list->length++] = value;
}

String* string_create(int capacity) {
    String* str = (String*)malloc(sizeof(String));
    str->capacity = capacity > 0 ? capacity : 32;
    str->length = 0;
    str->data = (char*)malloc(str->capacity);
    str->data[0] = '\0';
    return str;
}

String* string_copy(String* src) {
    String* str = string_create(src->capacity);
    str->length = src->length;
    memcpy(str->data, src->data, src->length + 1);
    return str;
}

void string_free(String* str) {
    if (str) {
        free(str->data);
        free(str);
    }
}

void string_append_char(String* str, char c) {
    if (str->length + 1 >= str->capacity) {
        str->capacity *= 2;
        str->data = (char*)realloc(str->data, str->capacity);
    }
    str->data[str->length++] = c;
    str->data[str->length] = '\0';
}

void string_append(String* str, const char* data, int len) {
    while (str->length + len + 1 >= str->capacity) {
        str->capacity *= 2;
        str->data = (char*)realloc(str->data, str->capacity);
    }
    memcpy(str->data + str->length, data, len);
    str->length += len;
    str->data[str->length] = '\0';
}

Tuple2* tuple2_create(void* first, void* second) {
    Tuple2* tuple = (Tuple2*)malloc(sizeof(Tuple2));
    tuple->first = first;
    tuple->second = second;
    return tuple;
}

void tuple2_free(
    Tuple2* tuple,
    void (*free_first)(void*),
    void (*free_second)(void*)
) {
    if (tuple) {
        if (free_first && tuple->first) {
            free_first(tuple->first);
        }
        if (free_second && tuple->second) {
            free_second(tuple->second);
        }
        free(tuple);
    }
}

Tuple3* tuple3_create(void* first, void* second, void* third) {
    Tuple3* tuple = (Tuple3*)malloc(sizeof(Tuple3));
    tuple->first = first;
    tuple->second = second;
    tuple->third = third;
    return tuple;
}

void tuple3_free(
    Tuple3* tuple,
    void (*free_first)(void*),
    void (*free_second)(void*),
    void (*free_third)(void*)
) {
    if (tuple) {
        if (free_first && tuple->first) {
            free_first(tuple->first);
        }
        if (free_second && tuple->second) {
            free_second(tuple->second);
        }
        if (free_third && tuple->third) {
            free_third(tuple->third);
        }
        free(tuple);
    }
}
