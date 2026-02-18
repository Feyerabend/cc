#include <stdlib.h>
#include <string.h>
#include "hashmap.h"

typedef struct Entry {
    char* key;
    int   value;
    struct Entry* next;
} Entry;

struct HashMap {
    Entry** buckets;
    int     num_buckets;
    int     size;
};

static unsigned long hash(const char* str) {
    unsigned long hash = 5381;
    int c;
    while ((c = *str++))
        hash = ((hash << 5) + hash) + c; // hash * 33 + c
    return hash;
}

HashMap* hashmap_create(int initial_capacity) {
    HashMap* hm = malloc(sizeof(HashMap));
    if (!hm) return NULL;
    hm->num_buckets = initial_capacity;
    hm->size = 0;
    hm->buckets = calloc(initial_capacity, sizeof(Entry*));
    if (!hm->buckets) { free(hm); return NULL; }
    return hm;
}

void hashmap_destroy(HashMap* hm) {
    for (int i = 0; i < hm->num_buckets; i++) {
        Entry* curr = hm->buckets[i];
        while (curr) {
            Entry* next = curr->next;
            free(curr->key);
            free(curr);
            curr = next;
        }
    }
    free(hm->buckets);
    free(hm);
}

int hashmap_put(HashMap* hm, const char* key, int value) {
    int bucket_idx = hash(key) % hm->num_buckets;
    Entry* curr = hm->buckets[bucket_idx];
    
    // Check if key exists — update value
    while (curr) {
        if (strcmp(curr->key, key) == 0) {
            curr->value = value;
            return 1;
        }
        curr = curr->next;
    }
    
    // New key — insert at head of bucket
    Entry* new_entry = malloc(sizeof(Entry));
    if (!new_entry) return 0;
    new_entry->key = strdup(key);
    new_entry->value = value;
    new_entry->next = hm->buckets[bucket_idx];
    hm->buckets[bucket_idx] = new_entry;
    hm->size++;
    return 1;
}

int hashmap_get(HashMap* hm, const char* key, int* out) {
    int bucket_idx = hash(key) % hm->num_buckets;
    Entry* curr = hm->buckets[bucket_idx];
    
    while (curr) {
        if (strcmp(curr->key, key) == 0) {
            *out = curr->value;
            return 1;
        }
        curr = curr->next;
    }
    return 0; // not found
}

int hashmap_contains(HashMap* hm, const char* key) {
    int dummy;
    return hashmap_get(hm, key, &dummy);
}

int hashmap_remove(HashMap* hm, const char* key) {
    int bucket_idx = hash(key) % hm->num_buckets;
    Entry* curr = hm->buckets[bucket_idx];
    Entry* prev = NULL;
    
    while (curr) {
        if (strcmp(curr->key, key) == 0) {
            if (prev) prev->next = curr->next;
            else hm->buckets[bucket_idx] = curr->next;
            free(curr->key);
            free(curr);
            hm->size--;
            return 1;
        }
        prev = curr;
        curr = curr->next;
    }
    return 0;
}

int hashmap_size(HashMap* hm) { return hm->size; }
