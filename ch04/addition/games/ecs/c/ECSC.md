
## Entity-Component-System (ECS) Architecture in C

The Entity-Component-System (ECS) architecture is a data-oriented design
pattern commonly used in game development and simulation software. It
emphasises *composition* over *inheritance*, making systems more flexible,
performant, and scalable compared to traditional object-oriented approaches.
ECS separates *data* (components) from *logic* (systems) and uses entities as
mere identifiers, which helps with cache efficiency and parallelisation.

This guide provides an introductory overview of implementing ECS in C. C's
procedural nature requires using structs, pointers, and manual memory management,
differing from higher-level languages with classes or templates. We'll focus
on the core concepts and a basic implementation, without diving into a full
game example. For production use, consider adding error handling, optimisations,
and testing.


#### Why ECS in C?

- *Performance*: C allows fine-grained control over memory layouts,
  ideal for ECS's data-oriented focus.
- *Portability*: ECS in C can run on embedded systems or platforms
  with limited resources.
- *Challenges*: No built-in containers or polymorphism, so we'll use
  custom data structures (e.g., dynamic arrays, hash tables) and
  function pointers.

| Traditional OOP | ECS |
|-----------------|-----|
| Deep class hierarchies | Flat component structs |
| Methods tied to objects | Systems process data in batches |
| Scattered memory access | Contiguous, cache-friendly data |
| Hard to extend | Easy to add/remove components |

### Core Concepts

#### 1. Entity
An entity is a unique identifier (e.g., an integer) that groups components.
It has no data or behavior itself—it's just an ID.

```c
typedef int EntityID;
```

#### 2. Component
Components are pure data structs with no logic. They describe properties
or states (e.g., position, health).

```c
// Example Components
typedef struct {
    float x, y, z;
} PositionComponent;

typedef struct {
    float x, y, z;
} VelocityComponent;

typedef struct {
    int current, max;
} HealthComponent;
```

#### 3. System
Systems contain logic that operates on entities with specific components.
They query the world for matching entities and process them in batches.

Systems are implemented as structs with function pointers to simulate polymorphism.

```c
typedef struct {
    void (*update)(void* self, struct World* world, float dt);
    // Optional: init, on_event, etc.
} System;
```

#### 4. World (Manager)
The world manages entities, components, and systems. It handles storage,
queries, and updates.

Storage often uses:
- A counter for entity IDs.
- Hash maps or arrays for components (e.g., component type to entity-component
  mappings).
- Indices for fast queries.

### Basic Implementation

We'll use simplified custom containers:
- *Dynamic Array*: For lists (e.g., systems, query results).
- *Hash Map*: For mappings (e.g., entity to components).
  A simple implementation with integer keys.

Assume these helpers are defined (implementations sketched later):

```c
// Dynamic Array
typedef struct {
    void* data;
    int size;
    int capacity;
    int elem_size;
} Array;

void array_init(Array* arr, int elem_size);
void array_add(Array* arr, void* item);
void* array_get(Array* arr, int index);
void array_free(Array* arr);

// Hash Map (simple, for int keys)
typedef struct {
    struct MapEntry* entries;
    int capacity;
    int size;
} HashMap;

struct MapEntry {
    int key;
    void* value;
    // Chaining for collisions (linked list)
    struct MapEntry* next;
};

void hashmap_init(HashMap* map, int capacity);
void hashmap_put(HashMap* map, int key, void* value);
void* hashmap_get(HashMap* map, int key);
int hashmap_contains(HashMap* map, int key);
void hashmap_free(HashMap* map);
```

#### Component Types
Use integers to identify component types (e.g., via enums or defines).

```c
enum ComponentType {
    CT_POSITION = 1,
    CT_VELOCITY,
    CT_HEALTH,
    // Add more as needed
};
```

#### World Structure

```c
typedef struct {
    int next_entity_id;
    HashMap entity_components;  // EntityID -> Array of ComponentType
    HashMap components;         // ComponentType -> HashMap (EntityID -> Component data)
    HashMap component_entities; // ComponentType -> Array of EntityID (for fast queries)
    Array systems;              // Array of System*
} World;

void world_init(World* world) {
    world->next_entity_id = 1;
    hashmap_init(&world->entity_components, 100);
    hashmap_init(&world->components, 10);
    hashmap_init(&world->component_entities, 10);
    array_init(&world->systems, sizeof(System*));
}

EntityID world_create_entity(World* world) {
    EntityID id = world->next_entity_id++;
    Array* comp_types = malloc(sizeof(Array));
    array_init(comp_types, sizeof(int));
    hashmap_put(&world->entity_components, id, comp_types);
    return id;
}

void world_add_component(World* world, EntityID entity, int type, void* data, int data_size) {
    if (!hashmap_contains(&world->entity_components, entity)) return;

    // Get or create per-type storage
    HashMap* type_map = hashmap_get(&world->components, type);
    if (!type_map) {
        type_map = malloc(sizeof(HashMap));
        hashmap_init(type_map, 100);
        hashmap_put(&world->components, type, type_map);
    }
    void* comp_copy = malloc(data_size);
    memcpy(comp_copy, data, data_size);
    hashmap_put(type_map, entity, comp_copy);

    // Update indices
    Array* entities_with_type = hashmap_get(&world->component_entities, type);
    if (!entities_with_type) {
        entities_with_type = malloc(sizeof(Array));
        array_init(entities_with_type, sizeof(EntityID));
        hashmap_put(&world->component_entities, type, entities_with_type);
    }
    array_add(entities_with_type, &entity);

    // Update entity's component list
    Array* entity_comps = hashmap_get(&world->entity_components, entity);
    array_add(entity_comps, &type);
}

void* world_get_component(World* world, EntityID entity, int type) {
    HashMap* type_map = hashmap_get(&world->components, type);
    if (!type_map) return NULL;
    return hashmap_get(type_map, entity);
}

int world_has_component(World* world, EntityID entity, int type) {
    Array* entity_comps = hashmap_get(&world->entity_components, entity);
    if (!entity_comps) return 0;
    for (int i = 0; i < entity_comps->size; i++) {
        int* comp_type = array_get(entity_comps, i);
        if (*comp_type == type) return 1;
    }
    return 0;
}

// Simple Query: Returns array of EntityID matching required components
Array world_query(World* world, int* required, int req_count) {
    Array result;
    array_init(&result, sizeof(EntityID));

    if (req_count == 0) return result;

    // Start with entities having the first required component
    Array* base_set = hashmap_get(&world->component_entities, required[0]);
    if (!base_set) return result;

    for (int i = 0; i < base_set->size; i++) {
        EntityID* entity = array_get(base_set, i);
        int has_all = 1;
        for (int j = 1; j < req_count; j++) {  // Start from 1 since 0 is already in base_set
            if (!world_has_component(world, *entity, required[j])) {
                has_all = 0;
                break;
            }
        }
        if (has_all) array_add(&result, entity);
    }
    return result;
}

void world_add_system(World* world, System* system) {
    array_add(&world->systems, &system);
}

void world_update(World* world, float dt) {
    for (int i = 0; i < world->systems.size; i++) {
        System* sys_ptr = array_get(&world->systems, i);
        (*sys_ptr)->update(*sys_ptr, world, dt);
    }
}

void world_free(World* world) {
    // Free all allocations (components, arrays, maps)
    // Implement cleanup logic here
}
```

#### Example System: MovementSystem

```c
typedef struct {
    System base;
} MovementSystem;

void movement_update(void* self, World* world, float dt) {
    int required[] = {CT_POSITION, CT_VELOCITY};
    Array entities = world_query(world, required, 2);

    for (int i = 0; i < entities.size; i++) {
        EntityID* entity = array_get(&entities, i);
        PositionComponent* pos = world_get_component(world, *entity, CT_POSITION);
        VelocityComponent* vel = world_get_component(world, *entity, CT_VELOCITY);
        pos->x += vel->x * dt;
        pos->y += vel->y * dt;
        pos->z += vel->z * dt;
    }

    array_free(&entities);
}

MovementSystem* create_movement_system() {
    MovementSystem* sys = malloc(sizeof(MovementSystem));
    sys->base.update = movement_update;
    return sys;
}
```

### Usage Example

```c
int main() {
    World world;
    world_init(&world);

    EntityID player = world_create_entity(&world);
    PositionComponent pos = {0.0f, 0.0f, 0.0f};
    VelocityComponent vel = {1.0f, 0.0f, 0.0f};
    world_add_component(&world, player, CT_POSITION, &pos, sizeof(PositionComponent));
    world_add_component(&world, player, CT_VELOCITY, &vel, sizeof(VelocityComponent));

    MovementSystem* movement = create_movement_system();
    world_add_system(&world, &movement->base);

    world_update(&world, 1.0f);  // Simulate one second

    // Cleanup
    world_free(&world);
    free(movement);
    return 0;
}
```

### Helper Implementations (Sketched)

#### Dynamic Array

```c
void array_init(Array* arr, int elem_size) {
    arr->elem_size = elem_size;
    arr->size = 0;
    arr->capacity = 8;
    arr->data = malloc(arr->capacity * elem_size);
}

void array_add(Array* arr, void* item) {
    if (arr->size >= arr->capacity) {
        arr->capacity *= 2;
        arr->data = realloc(arr->data, arr->capacity * arr->elem_size);
    }
    memcpy((char*)arr->data + arr->size * arr->elem_size, item, arr->elem_size);
    arr->size++;
}

void* array_get(Array* arr, int index) {
    return (char*)arr->data + index * arr->elem_size;
}

void array_free(Array* arr) {
    free(arr->data);
}
```

#### Hash Map (Basic with Chaining)

```c
unsigned int hash(int key) {
    return key % 100;  // Simple hash; improve for production
}

void hashmap_init(HashMap* map, int capacity) {
    map->entries = calloc(capacity, sizeof(struct MapEntry));
    map->capacity = capacity;
    map->size = 0;
}

void hashmap_put(HashMap* map, int key, void* value) {
    unsigned int idx = hash(key);
    struct MapEntry* entry = &map->entries[idx];
    if (!entry->value) {
        entry->key = key;
        entry->value = value;
    } else {
        while (entry->next) entry = entry->next;
        entry->next = malloc(sizeof(struct MapEntry));
        entry->next->key = key;
        entry->next->value = value;
    }
    map->size++;
}

void* hashmap_get(HashMap* map, int key) {
    unsigned int idx = hash(key);
    struct MapEntry* entry = &map->entries[idx];
    while (entry) {
        if (entry->key == key) return entry->value;
        entry = entry->next;
    }
    return NULL;
}

int hashmap_contains(HashMap* map, int key) {
    return hashmap_get(map, key) != NULL;
}

// Free function would recurse through chains and free
```

### Best Practices and Extensions

- *Keep Components Small*: Focus on single responsibilities
  (e.g., separate position and rotation if needed).
- *Optimize Queries*: Use archetypes (grouping by component sets) for larger systems.
- *Events*: Add a queue for inter-system communication (e.g., collision events).
- *Memory Management*: Use pools or arenas to reduce allocations.
- *Debugging*: Add functions to inspect entities/components.
- *Extensions*: Implement removal/destruction, events, or parallel updates.

ECS in C requires discipline but yields high performance. Start small,
profile often, and expand as needed. For more, explore open-source ECS
libraries like Flecs or EnTT (adapted to C).
