#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define TABLE_SIZE 10

typedef struct Node {
    char* key;
    int value;
    struct Node* next;
} Node;

typedef struct HashTable {
    Node* table[TABLE_SIZE];
} HashTable;

unsigned int hash(const char* key) {
    unsigned int hash = 0;
    while (*key) {
        hash = (hash * 31) + *key++;
    }
    return hash % TABLE_SIZE;
}

Node* createNode(const char* key, int value) {
    Node* newNode = (Node*)malloc(sizeof(Node));
    newNode->key = strdup(key);
    newNode->value = value;
    newNode->next = NULL;
    return newNode;
}

void insert(HashTable* ht, const char* key, int value) {
    unsigned int index = hash(key);
    Node* current = ht->table[index];

    while (current) {
        if (strcmp(current->key, key) == 0) {
            current->value = value;
            return;
        }
        if (current->next == NULL) break;
        current = current->next;
    }

    Node* newNode = createNode(key, value);
    if (current) {
        current->next = newNode;
    } else {
        ht->table[index] = newNode;
    }
}

int get(HashTable* ht, const char* key) {
    unsigned int index = hash(key);
    Node* current = ht->table[index];
    while (current) {
        if (strcmp(current->key, key) == 0) return current->value;
        current = current->next;
    }
    return -1;
}

void delete(HashTable* ht, const char* key) {
    unsigned int index = hash(key);
    Node* current = ht->table[index];
    Node* prev = NULL;

    while (current) {
        if (strcmp(current->key, key) == 0) {
            if (prev) {
                prev->next = current->next;
            } else {
                ht->table[index] = current->next;
            }
            free(current->key);
            free(current);
            return;
        }
        prev = current;
        current = current->next;
    }
}

void display(HashTable* ht) {
    for (int i = 0; i < TABLE_SIZE; i++) {
        printf("Index %d: ", i);
        Node* current = ht->table[i];
        while (current) {
            printf("(%s: %d) -> ", current->key, current->value);
            current = current->next;
        }
        printf("NULL\n");
    }
}

void freeTable(HashTable* ht) {
    for (int i = 0; i < TABLE_SIZE; i++) {
        Node* current = ht->table[i];
        while (current) {
            Node* temp = current;
            current = current->next;
            free(temp->key);
            free(temp);
        }
    }
}

int main() {
    HashTable ht = {0};
    insert(&ht, "a", 1);
    insert(&ht, "b", 2);
    insert(&ht, "c", 3);
    insert(&ht, "a", 10);
    display(&ht);
    delete(&ht, "b");
    display(&ht);
    printf("%d\n", get(&ht, "a"));
    printf("%d\n", get(&ht, "b"));
    freeTable(&ht);
    return 0;
}