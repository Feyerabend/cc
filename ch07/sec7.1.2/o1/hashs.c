#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define TABLE_SIZE 16
#define LOAD_FACTOR 0.75

typedef struct Node {
    char* key;
    int value;
    struct Node* next;
} Node;

typedef struct HashTable {
    Node** table;
    int size;
    int count;
} HashTable;

unsigned int hash(char* key) {
    unsigned int hashValue = 0;
    for (int i = 0; key[i] != '\0'; i++) {
        hashValue = (hashValue * 31) + key[i];
    }
    return hashValue % TABLE_SIZE;
}

Node* createNode(char* key, int value) {
    Node* newNode = (Node*)malloc(sizeof(Node));
    newNode->key = strdup(key);
    newNode->value = value;
    newNode->next = NULL;
    return newNode;
}

HashTable* createTable() {
    HashTable* table = (HashTable*)malloc(sizeof(HashTable));
    table->size = TABLE_SIZE;
    table->count = 0;
    table->table = (Node**)calloc(table->size, sizeof(Node*));
    return table;
}

void resize(HashTable* ht) {
    int newSize = ht->size * 2;
    Node** newTable = (Node**)calloc(newSize, sizeof(Node*));

    for (int i = 0; i < ht->size; i++) {
        Node* current = ht->table[i];
        while (current) {
            unsigned int newIndex = hash(current->key) % newSize;
            Node* next = current->next;
            current->next = newTable[newIndex];
            newTable[newIndex] = current;
            current = next;
        }
    }

    free(ht->table);
    ht->table = newTable;
    ht->size = newSize;
}

void insert(HashTable* ht, char* key, int value) {
    if ((float)ht->count / ht->size >= LOAD_FACTOR) {
        resize(ht);
    }

    unsigned int index = hash(key);
    Node* current = ht->table[index];
    
    while (current) {
        if (strcmp(current->key, key) == 0) {
            current->value = value;
                return;
        }
        current = current->next;
    }

    Node* newNode = createNode(key, value);
    newNode->next = ht->table[index];
    ht->table[index] = newNode;
    ht->count++;
}

Node* search(HashTable* ht, char* key) {
    unsigned int index = hash(key);
    Node* current = ht->table[index];
    while (current) {
        if (strcmp(current->key, key) == 0) {
            return current;
        }
        current = current->next;
    }
    return NULL;
}

void delete(HashTable* ht, char* key) {
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
            ht->count--;
            return;
        }
        prev = current;
        current = current->next;
    }
}

void freeTable(HashTable* ht) {
    for (int i = 0; i < ht->size; i++) {
        Node* current = ht->table[i];
        while (current) {
            Node* next = current->next;
            free(current->key);
            free(current);
            current = next;
        }
    }
    free(ht->table);
    free(ht);
}

void printTable(HashTable* ht) {
    for (int i = 0; i < ht->size; i++) {
        Node* current = ht->table[i];
        if (current == NULL) {
            printf("Index %d: NULL\n", i);
        } else {
            printf("Index %d: ", i);
            while (current) {
                printf("(%s: %d) -> ", current->key, current->value);
                current = current->next;
            }
            printf("NULL\n");
        }
    }
}

int main() {
    HashTable* ht = createTable();

    insert(ht, "apple", 5);
    insert(ht, "banana", 10);
    insert(ht, "grape", 15);
    insert(ht, "kiwi", 40);
    insert(ht, "watermelon", 45);
    insert(ht, "blueberry", 35);
    insert(ht, "orange", 20);
    insert(ht, "mango", 30);
    insert(ht, "strawberry", 25);

    printTable(ht);

    insert(ht, "apple", 50);  // Test updating an existing key

    Node* result = search(ht, "apple");
    if (result) {
        printf("Value for 'apple': %d\n", result->value);  // Should print 50
    }

    delete(ht, "banana");  // Test deleting an existing key
    printTable(ht);

    delete(ht, "nonexistent");  // Test deleting a non-existent key

    insert(ht, "newKey", 100);  // Test inserting a new key
    printTable(ht);

    freeTable(ht);
    return 0;
}