#ifndef HASHMAP_H
#define HASHMAP_H

typedef struct HashMap HashMap;

HashMap* hashmap_create(int initial_capacity);
void     hashmap_destroy(HashMap* hm);

int  hashmap_put(HashMap* hm, const char* key, int value);
int  hashmap_get(HashMap* hm, const char* key, int* out);  // returns 1 if found
int  hashmap_remove(HashMap* hm, const char* key);
int  hashmap_contains(HashMap* hm, const char* key);
int  hashmap_size(HashMap* hm);

#endif // HASHMAP_H
