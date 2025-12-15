#ifndef GAME_H
#define GAME_H

#include "display.h"
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

// ECS Core Types

typedef int EntityID;

// Dynamic Array
typedef struct {
    void* data;
    int size;
    int capacity;
    int elem_size;
} Array;

// Hash Map Entry
typedef struct MapEntry {
    int key;
    void* value;
    struct MapEntry* next;
} MapEntry;

// Hash Map
typedef struct {
    MapEntry* entries;
    int capacity;
    int size;
} HashMap;

// System interface
typedef struct System System;
typedef struct World World;

struct System {
    void (*update)(System* self, World* world, float dt);
    void (*cleanup)(System* self);
};

// World structure
struct World {
    int next_entity_id;
    HashMap entity_components;
    HashMap components;
    HashMap component_entities;
    Array systems;
    Array dead_entities;  // NEW: Track entities to delete
    float camera_x;
    float camera_y;
    bool game_over;
    int score;
    EntityID player_entity;
};

// Component Types

enum ComponentType {
    CT_POSITION = 1,
    CT_VELOCITY,
    CT_SPRITE,
    CT_PLAYER,
    CT_COLLIDER,
    CT_PHYSICS,
    CT_ENEMY,
    CT_PLATFORM,
    CT_COLLECTIBLE,
    CT_ANIMATION
};

// Position component
typedef struct {
    float x, y;
} PositionComponent;

// Velocity component
typedef struct {
    float x, y;
} VelocityComponent;

// Sprite component
typedef struct {
    uint16_t color;
    uint8_t width;
    uint8_t height;
    const uint8_t* bitmap;
} SpriteComponent;

// Player component
typedef struct {
    bool on_ground;
    int jump_count;
    int max_jumps;
    int lives;
} PlayerComponent;

// Collider component
typedef struct {
    float width;
    float height;
    float offset_x;
    float offset_y;
} ColliderComponent;

// Physics component
typedef struct {
    float gravity;
    float max_fall_speed;
    float friction;
    bool affected_by_gravity;
} PhysicsComponent;

// Enemy component
typedef struct {
    float move_speed;
    float move_direction;
    float patrol_start;
    float patrol_end;
} EnemyComponent;

// Platform component
typedef struct {
    bool solid;
    bool one_way;
} PlatformComponent;

// Collectible component
typedef struct {
    int points;
    bool collected;
} CollectibleComponent;

// Animation component
typedef struct {
    const uint8_t** frames;
    int frame_count;
    int current_frame;
    float frame_time;
    float time_accumulator;
} AnimationComponent;

// Helper Functions

// Array functions
void array_init(Array* arr, int elem_size);
void array_add(Array* arr, void* item);
void* array_get(Array* arr, int index);
void array_remove(Array* arr, int index);  // NEW: Remove element
void array_free(Array* arr);

// HashMap functions
void hashmap_init(HashMap* map, int capacity);
void hashmap_put(HashMap* map, int key, void* value);
void* hashmap_get(HashMap* map, int key);
int hashmap_contains(HashMap* map, int key);
void hashmap_remove(HashMap* map, int key);  // NEW: Remove entry
void hashmap_free(HashMap* map);

// World functions
void world_init(World* world);
EntityID world_create_entity(World* world);
void world_add_component(World* world, EntityID entity, int type, void* data, int data_size);
void* world_get_component(World* world, EntityID entity, int type);
int world_has_component(World* world, EntityID entity, int type);
Array world_query(World* world, int* required, int req_count);
void world_add_system(World* world, System* system);
void world_update(World* world, float dt);
void world_destroy_entity(World* world, EntityID entity);  // Deferred deletion
void world_destroy_entity_immediate(World* world, EntityID entity);  // NEW: Immediate deletion
void world_free(World* world);

// Collision detection
bool check_collision(float x1, float y1, float w1, float h1,
                     float x2, float y2, float w2, float h2);

// Game initialization
void game_init(World* world);
void game_create_level(World* world);

// System Declarations

// Input System
typedef struct {
    System base;
    bool last_jump_pressed;
} InputSystem;
InputSystem* create_input_system(void);

// Physics System
typedef struct {
    System base;
} PhysicsSystem;
PhysicsSystem* create_physics_system(void);

// Collision System
typedef struct {
    System base;
} CollisionSystem;
CollisionSystem* create_collision_system(void);

// Enemy AI System
typedef struct {
    System base;
} EnemyAISystem;
EnemyAISystem* create_enemy_ai_system(void);

// Animation System
typedef struct {
    System base;
} AnimationSystem;
AnimationSystem* create_animation_system(void);

// Render System
typedef struct {
    System base;
} RenderSystem;
RenderSystem* create_render_system(void);

#endif // GAME_H
