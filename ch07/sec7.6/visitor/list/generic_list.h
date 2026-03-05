#ifndef GENERIC_LIST_H
#define GENERIC_LIST_H

#include <stdlib.h>
#include <stdio.h>

/*
    DEFINE_LIST(type, prefix)

    Generates:

        prefix_node
        prefix_list

        prefix_init
        prefix_push_front
        prefix_push_back
        prefix_remove
        prefix_replace
        prefix_print
        prefix_clear
*/

#define DEFINE_LIST(TYPE, PREFIX)                                              \
                                                                               \
typedef struct PREFIX##_node {                                                 \
    TYPE data;                                                                 \
    struct PREFIX##_node* next;                                                \
} PREFIX##_node;                                                               \
                                                                               \
typedef struct {                                                               \
    PREFIX##_node* head;                                                       \
} PREFIX##_list;                                                               \
                                                                               \
static void PREFIX##_init(PREFIX##_list* list) {                               \
    list->head = NULL;                                                         \
}                                                                              \
                                                                               \
static PREFIX##_node* PREFIX##_create_node(TYPE value,                         \
                                           PREFIX##_node* next) {              \
    PREFIX##_node* node =                                                      \
        (PREFIX##_node*)malloc(sizeof(PREFIX##_node));                         \
    node->data = value;                                                        \
    node->next = next;                                                         \
    return node;                                                               \
}                                                                              \
                                                                               \
static void PREFIX##_push_front(PREFIX##_list* list, TYPE value) {             \
    list->head = PREFIX##_create_node(value, list->head);                      \
}                                                                              \
                                                                               \
static void PREFIX##_push_back(PREFIX##_list* list, TYPE value) {              \
    PREFIX##_node** current = &list->head;                                     \
    while (*current)                                                           \
        current = &((*current)->next);                                         \
    *current = PREFIX##_create_node(value, NULL);                              \
}                                                                              \
                                                                               \
static void PREFIX##_remove(PREFIX##_list* list, TYPE value) {                 \
    PREFIX##_node** current = &list->head;                                     \
    while (*current) {                                                         \
        if ((*current)->data == value) {                                       \
            PREFIX##_node* temp = *current;                                    \
            *current = temp->next;                                             \
            free(temp);                                                        \
            return;                                                            \
        }                                                                      \
        current = &((*current)->next);                                         \
    }                                                                          \
}                                                                              \
                                                                               \
static void PREFIX##_replace(PREFIX##_list* list,                              \
                             TYPE old_value,                                   \
                             TYPE new_value) {                                 \
    PREFIX##_node* current = list->head;                                       \
    while (current) {                                                          \
        if (current->data == old_value) {                                      \
            current->data = new_value;                                         \
            return;                                                            \
        }                                                                      \
        current = current->next;                                               \
    }                                                                          \
}                                                                              \
                                                                               \
static void PREFIX##_print(PREFIX##_list* list,                                \
                           void (*printer)(TYPE)) {                            \
    PREFIX##_node* current = list->head;                                       \
    while (current) {                                                          \
        printer(current->data);                                                \
        current = current->next;                                               \
    }                                                                          \
}                                                                              \
                                                                               \
static void PREFIX##_clear(PREFIX##_list* list) {                              \
    PREFIX##_node* current = list->head;                                       \
    while (current) {                                                          \
        PREFIX##_node* temp = current;                                         \
        current = current->next;                                               \
        free(temp);                                                            \
    }                                                                          \
    list->head = NULL;                                                         \
}

#endif
