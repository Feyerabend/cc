#include "game.h"
#include "sprites.h"
#include <stdio.h>
#include <assert.h>

// Configuration
#define WORLD_WIDTH 2000  // Much larger world for scrolling
#define GROUND_HEIGHT 220

// Helpers

static unsigned int hash(int key) {
    key = ((key >> 16) ^ key) * 0x45d9f3b;
    key = ((key >> 16) ^ key) * 0x45d9f3b;
    key = (key >> 16) ^ key;
    return (unsigned int)key;
}

void array_init(Array* arr, int elem_size) {
    assert(arr && elem_size > 0);
    arr->elem_size = elem_size;
    arr->size = 0;
    arr->capacity = 8;
    arr->data = malloc(arr->capacity * elem_size);
    assert(arr->data && "Array allocation failed");
}

void array_add(Array* arr, void* item) {
    assert(arr && item);
    if (arr->size >= arr->capacity) {
        arr->capacity *= 2;
        void* new_data = realloc(arr->data, arr->capacity * arr->elem_size);
        assert(new_data && "Array reallocation failed");
        arr->data = new_data;
    }
    memcpy((char*)arr->data + arr->size * arr->elem_size, item, arr->elem_size);
    arr->size++;
}

void* array_get(Array* arr, int index) {
    if (!arr || index < 0 || index >= arr->size) return NULL;
    return (char*)arr->data + index * arr->elem_size;
}

void array_remove(Array* arr, int index) {
    if (!arr || index < 0 || index >= arr->size) return;
    
    if (index < arr->size - 1) {
        memmove((char*)arr->data + index * arr->elem_size,
                (char*)arr->data + (index + 1) * arr->elem_size,
                (arr->size - index - 1) * arr->elem_size);
    }
    arr->size--;
}

void array_free(Array* arr) {
    if (!arr) return;
    free(arr->data);
    arr->data = NULL;
    arr->size = 0;
    arr->capacity = 0;
}

void hashmap_init(HashMap* map, int capacity) {
    assert(map && capacity > 0);
    map->entries = calloc(capacity, sizeof(MapEntry));
    assert(map->entries && "HashMap allocation failed");
    map->capacity = capacity;
    map->size = 0;
}

void hashmap_put(HashMap* map, int key, void* value) {
    assert(map && value);
    
    unsigned int idx = hash(key) % map->capacity;
    MapEntry* entry = &map->entries[idx];
    
    MapEntry* current = entry;
    while (current && current->value) {
        if (current->key == key) {
            current->value = value;
            return;
        }
        current = current->next;
    }
    
    if (!entry->value) {
        entry->key = key;
        entry->value = value;
        entry->next = NULL;
    } else {
        while (entry->next) entry = entry->next;
        entry->next = malloc(sizeof(MapEntry));
        assert(entry->next && "MapEntry allocation failed");
        entry->next->key = key;
        entry->next->value = value;
        entry->next->next = NULL;
    }
    map->size++;
}

void* hashmap_get(HashMap* map, int key) {
    if (!map) return NULL;
    
    unsigned int idx = hash(key) % map->capacity;
    MapEntry* entry = &map->entries[idx];
    
    while (entry && entry->value) {
        if (entry->key == key) return entry->value;
        entry = entry->next;
    }
    return NULL;
}

int hashmap_contains(HashMap* map, int key) {
    return hashmap_get(map, key) != NULL;
}

void hashmap_remove(HashMap* map, int key) {
    if (!map) return;
    
    unsigned int idx = hash(key) % map->capacity;
    MapEntry* entry = &map->entries[idx];
    MapEntry* prev = NULL;
    
    while (entry && entry->value) {
        if (entry->key == key) {
            if (prev) {
                prev->next = entry->next;
                free(entry);
            } else {
                if (entry->next) {
                    MapEntry* next = entry->next;
                    entry->key = next->key;
                    entry->value = next->value;
                    entry->next = next->next;
                    free(next);
                } else {
                    entry->value = NULL;
                    entry->next = NULL;
                }
            }
            map->size--;
            return;
        }
        prev = entry;
        entry = entry->next;
    }
}

void hashmap_free(HashMap* map) {
    if (!map) return;
    
    for (int i = 0; i < map->capacity; i++) {
        MapEntry* entry = map->entries[i].next;
        while (entry) {
            MapEntry* next = entry->next;
            free(entry);
            entry = next;
        }
    }
    free(map->entries);
    map->entries = NULL;
    map->capacity = 0;
    map->size = 0;
}

// World

void world_init(World* world) {
    assert(world);
    world->next_entity_id = 1;
    hashmap_init(&world->entity_components, 100);
    hashmap_init(&world->components, 20);
    hashmap_init(&world->component_entities, 20);
    array_init(&world->systems, sizeof(System*));
    array_init(&world->dead_entities, sizeof(EntityID));
    world->camera_x = 0.0f;
    world->camera_y = 0.0f;
    world->game_over = false;
    world->score = 0;
    world->player_entity = 0;
}

EntityID world_create_entity(World* world) {
    assert(world);
    
    if (world->next_entity_id <= 0) {
        return 0;
    }
    
    EntityID id = world->next_entity_id++;
    Array* comp_types = malloc(sizeof(Array));
    assert(comp_types);
    array_init(comp_types, sizeof(int));
    hashmap_put(&world->entity_components, id, comp_types);
    return id;
}

void world_add_component(World* world, EntityID entity, int type, void* data, int data_size) {
    assert(world && data && data_size > 0);
    
    if (!hashmap_contains(&world->entity_components, entity)) return;
    
    HashMap* type_map = hashmap_get(&world->components, type);
    if (!type_map) {
        type_map = malloc(sizeof(HashMap));
        assert(type_map);
        hashmap_init(type_map, 100);
        hashmap_put(&world->components, type, type_map);
    }
    
    void* comp_copy = malloc(data_size);
    assert(comp_copy);
    memcpy(comp_copy, data, data_size);
    hashmap_put(type_map, entity, comp_copy);
    
    Array* entities_with_type = hashmap_get(&world->component_entities, type);
    if (!entities_with_type) {
        entities_with_type = malloc(sizeof(Array));
        assert(entities_with_type);
        array_init(entities_with_type, sizeof(EntityID));
        hashmap_put(&world->component_entities, type, entities_with_type);
    }
    
    bool already_has = false;
    for (int i = 0; i < entities_with_type->size; i++) {
        EntityID* e = array_get(entities_with_type, i);
        if (e && *e == entity) {
            already_has = true;
            break;
        }
    }
    if (!already_has) {
        array_add(entities_with_type, &entity);
    }
    
    Array* entity_comps = hashmap_get(&world->entity_components, entity);
    if (entity_comps) {
        array_add(entity_comps, &type);
    }
}

void* world_get_component(World* world, EntityID entity, int type) {
    if (!world) return NULL;
    
    HashMap* type_map = hashmap_get(&world->components, type);
    if (!type_map) return NULL;
    return hashmap_get(type_map, entity);
}

int world_has_component(World* world, EntityID entity, int type) {
    if (!world) return 0;
    
    Array* entity_comps = hashmap_get(&world->entity_components, entity);
    if (!entity_comps) return 0;
    
    for (int i = 0; i < entity_comps->size; i++) {
        int* comp_type = array_get(entity_comps, i);
        if (comp_type && *comp_type == type) return 1;
    }
    return 0;
}

Array world_query(World* world, int* required, int req_count) {
    Array result;
    array_init(&result, sizeof(EntityID));
    
    if (!world || !required || req_count == 0) return result;
    
    Array* base_set = hashmap_get(&world->component_entities, required[0]);
    if (!base_set) return result;
    
    for (int i = 0; i < base_set->size; i++) {
        EntityID* entity = array_get(base_set, i);
        if (!entity) continue;
        
        bool is_dead = false;
        for (int d = 0; d < world->dead_entities.size; d++) {
            EntityID* dead = array_get(&world->dead_entities, d);
            if (dead && *dead == *entity) {
                is_dead = true;
                break;
            }
        }
        if (is_dead) continue;
        
        int has_all = 1;
        for (int j = 1; j < req_count; j++) {
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
    assert(world && system);
    array_add(&world->systems, &system);
}

void world_update(World* world, float dt) {
    if (!world) return;
    
    for (int i = 0; i < world->dead_entities.size; i++) {
        EntityID* entity = array_get(&world->dead_entities, i);
        if (entity) {
            world_destroy_entity_immediate(world, *entity);
        }
    }
    world->dead_entities.size = 0;
    
    for (int i = 0; i < world->systems.size; i++) {
        System** sys_ptr = array_get(&world->systems, i);
        if (sys_ptr && *sys_ptr && (*sys_ptr)->update) {
            (*sys_ptr)->update(*sys_ptr, world, dt);
        }
    }
}

void world_destroy_entity(World* world, EntityID entity) {
    if (!world) return;
    array_add(&world->dead_entities, &entity);
}

void world_destroy_entity_immediate(World* world, EntityID entity) {
    if (!world) return;
    
    Array* entity_comps = hashmap_get(&world->entity_components, entity);
    if (!entity_comps) return;
    
    for (int i = 0; i < entity_comps->size; i++) {
        int* comp_type = array_get(entity_comps, i);
        if (!comp_type) continue;
        
        HashMap* type_map = hashmap_get(&world->components, *comp_type);
        if (type_map) {
            void* comp_data = hashmap_get(type_map, entity);
            if (comp_data) {
                free(comp_data);
                hashmap_remove(type_map, entity);
            }
        }
        
        Array* entities_with_type = hashmap_get(&world->component_entities, *comp_type);
        if (entities_with_type) {
            for (int j = entities_with_type->size - 1; j >= 0; j--) {
                EntityID* e = array_get(entities_with_type, j);
                if (e && *e == entity) {
                    array_remove(entities_with_type, j);
                }
            }
        }
    }
    
    array_free(entity_comps);
    free(entity_comps);
    hashmap_remove(&world->entity_components, entity);
}

void world_free(World* world) {
    if (!world) return;
    
    for (int i = 0; i < world->systems.size; i++) {
        System** sys_ptr = array_get(&world->systems, i);
        if (sys_ptr && *sys_ptr) {
            if ((*sys_ptr)->cleanup) {
                (*sys_ptr)->cleanup(*sys_ptr);
            }
            free(*sys_ptr);
        }
    }
    array_free(&world->systems);
    
    for (int type = CT_POSITION; type <= CT_ANIMATION; type++) {
        HashMap* type_map = hashmap_get(&world->components, type);
        if (type_map) {
            for (int i = 0; i < type_map->capacity; i++) {
                MapEntry* entry = &type_map->entries[i];
                while (entry && entry->value) {
                    free(entry->value);
                    entry->value = NULL;
                    entry = entry->next;
                }
            }
            hashmap_free(type_map);
            free(type_map);
        }
    }
    
    for (int i = 0; i < world->entity_components.capacity; i++) {
        MapEntry* entry = &world->entity_components.entries[i];
        while (entry && entry->value) {
            Array* comp_list = entry->value;
            array_free(comp_list);
            free(comp_list);
            entry->value = NULL;
            entry = entry->next;
        }
    }
    
    for (int i = 0; i < world->component_entities.capacity; i++) {
        MapEntry* entry = &world->component_entities.entries[i];
        while (entry && entry->value) {
            Array* entity_list = entry->value;
            array_free(entity_list);
            free(entity_list);
            entry->value = NULL;
            entry = entry->next;
        }
    }
    
    hashmap_free(&world->entity_components);
    hashmap_free(&world->components);
    hashmap_free(&world->component_entities);
    array_free(&world->dead_entities);
}

// Collision
bool check_collision(float x1, float y1, float w1, float h1,
                     float x2, float y2, float w2, float h2) {
    return x1 < x2 + w2 && x1 + w1 > x2 &&
           y1 < y2 + h2 && y1 + h1 > y2;
}

// Input System
void input_update(System* self, World* world, float dt) {
    if (!self || !world || world->game_over) return;
    
    InputSystem* sys = (InputSystem*)self;
    
    int required[] = {CT_PLAYER, CT_POSITION, CT_VELOCITY, CT_PHYSICS};
    Array entities = world_query(world, required, 4);
    
    for (int i = 0; i < entities.size; i++) {
        EntityID* entity = array_get(&entities, i);
        if (!entity) continue;
        
        PlayerComponent* player = world_get_component(world, *entity, CT_PLAYER);
        VelocityComponent* vel = world_get_component(world, *entity, CT_VELOCITY);
        
        if (!player || !vel) continue;
        
        // Improved movement with acceleration
        float move_accel = 500.0f;
        float max_speed = 120.0f;
        
        if (button_pressed(BUTTON_A)) {
            vel->x -= move_accel * dt;
            if (vel->x < -max_speed) vel->x = -max_speed;
        } else if (button_pressed(BUTTON_B)) {
            vel->x += move_accel * dt;
            if (vel->x > max_speed) vel->x = max_speed;
        } else {
            // Apply friction when no input
            vel->x *= 0.85f;
            if (vel->x > -0.1f && vel->x < 0.1f) vel->x = 0;
        }
        
        // Jump logic
        bool jump_pressed = button_pressed(BUTTON_Y);
        if (jump_pressed && !sys->last_jump_pressed) {
            if (player->on_ground || player->jump_count < player->max_jumps) {
                vel->y = -180.0f;
                player->jump_count++;
                player->on_ground = false;
            }
        }
        sys->last_jump_pressed = jump_pressed;
    }
    
    array_free(&entities);
}

InputSystem* create_input_system(void) {
    InputSystem* sys = malloc(sizeof(InputSystem));
    assert(sys);
    sys->base.update = input_update;
    sys->base.cleanup = NULL;
    sys->last_jump_pressed = false;
    return sys;
}

// Physics System - FIXED
void physics_update(System* self, World* world, float dt) {
    if (!self || !world) return;
    
    int required[] = {CT_POSITION, CT_VELOCITY, CT_PHYSICS};
    Array entities = world_query(world, required, 3);
    
    for (int i = 0; i < entities.size; i++) {
        EntityID* entity = array_get(&entities, i);
        if (!entity) continue;
        
        PositionComponent* pos = world_get_component(world, *entity, CT_POSITION);
        VelocityComponent* vel = world_get_component(world, *entity, CT_VELOCITY);
        PhysicsComponent* phys = world_get_component(world, *entity, CT_PHYSICS);
        
        if (!pos || !vel || !phys) continue;
        
        // Apply gravity
        if (phys->affected_by_gravity) {
            vel->y += phys->gravity * dt;
            if (vel->y > phys->max_fall_speed) {
                vel->y = phys->max_fall_speed;
            }
        }
        
        // Apply velocity
        pos->x += vel->x * dt;
        pos->y += vel->y * dt;
        
        // World bounds - FIXED: Use WORLD_WIDTH instead of 800
        if (pos->x < 0) {
            pos->x = 0;
            vel->x = 0;
        }
        if (pos->x > WORLD_WIDTH - 16) {
            pos->x = WORLD_WIDTH - 16;
            vel->x = 0;
        }
        
        // Bottom boundary (death pit)
        if (pos->y > DISPLAY_HEIGHT + 50) {
            // Player fell off - respawn or lose life
            PlayerComponent* player = world_get_component(world, *entity, CT_PLAYER);
            if (player) {
                player->lives--;
                if (player->lives <= 0) {
                    world->game_over = true;
                } else {
                    // Respawn at start - FIXED: spawn on ground
                    pos->x = 50.0f;
                    pos->y = GROUND_HEIGHT - 14.0f; // Place on ground (14 = player height)
                    vel->x = 0;
                    vel->y = 0;
                }
            }
        }
    }
    
    array_free(&entities);
}

PhysicsSystem* create_physics_system(void) {
    PhysicsSystem* sys = malloc(sizeof(PhysicsSystem));
    assert(sys);
    sys->base.update = physics_update;
    sys->base.cleanup = NULL;
    return sys;
}

// Collision System - IMPROVED
void collision_update(System* self, World* world, float dt) {
    if (!self || !world) return;
    
    int player_required[] = {CT_PLAYER, CT_POSITION, CT_COLLIDER, CT_VELOCITY};
    Array players = world_query(world, player_required, 4);
    
    int platform_required[] = {CT_PLATFORM, CT_POSITION, CT_COLLIDER};
    Array platforms = world_query(world, platform_required, 3);
    
    int enemy_required[] = {CT_ENEMY, CT_POSITION, CT_COLLIDER};
    Array enemies = world_query(world, enemy_required, 3);
    
    int collectible_required[] = {CT_COLLECTIBLE, CT_POSITION, CT_COLLIDER};
    Array collectibles = world_query(world, collectible_required, 3);
    
    for (int i = 0; i < players.size; i++) {
        EntityID* player_ent = array_get(&players, i);
        if (!player_ent) continue;
        
        PositionComponent* p_pos = world_get_component(world, *player_ent, CT_POSITION);
        ColliderComponent* p_col = world_get_component(world, *player_ent, CT_COLLIDER);
        VelocityComponent* p_vel = world_get_component(world, *player_ent, CT_VELOCITY);
        PlayerComponent* player = world_get_component(world, *player_ent, CT_PLAYER);
        
        if (!p_pos || !p_col || !p_vel || !player) continue;
        
        // Reset ground state each frame
        player->on_ground = false;
        
        // Platform collision - IMPROVED
        for (int j = 0; j < platforms.size; j++) {
            EntityID* plat_ent = array_get(&platforms, j);
            if (!plat_ent) continue;
            
            PositionComponent* plat_pos = world_get_component(world, *plat_ent, CT_POSITION);
            ColliderComponent* plat_col = world_get_component(world, *plat_ent, CT_COLLIDER);
            PlatformComponent* platform = world_get_component(world, *plat_ent, CT_PLATFORM);
            
            if (!plat_pos || !plat_col || !platform) continue;
            
            if (check_collision(p_pos->x, p_pos->y, p_col->width, p_col->height,
                              plat_pos->x, plat_pos->y, plat_col->width, plat_col->height)) {
                
                // Calculate overlap on each axis
                float overlap_left = (p_pos->x + p_col->width) - plat_pos->x;
                float overlap_right = (plat_pos->x + plat_col->width) - p_pos->x;
                float overlap_top = (p_pos->y + p_col->height) - plat_pos->y;
                float overlap_bottom = (plat_pos->y + plat_col->height) - p_pos->y;
                
                // Find minimum overlap
                float min_overlap = overlap_top;
                int collision_side = 0; // 0=top, 1=bottom, 2=left, 3=right
                
                if (overlap_bottom < min_overlap) { min_overlap = overlap_bottom; collision_side = 1; }
                if (!platform->one_way && overlap_left < min_overlap) { min_overlap = overlap_left; collision_side = 2; }
                if (!platform->one_way && overlap_right < min_overlap) { min_overlap = overlap_right; collision_side = 3; }
                
                // Resolve collision based on side
                if (collision_side == 0 && p_vel->y > 0) {
                    // Landing on top
                    p_pos->y = plat_pos->y - p_col->height;
                    p_vel->y = 0;
                    player->on_ground = true;
                    player->jump_count = 0;
                } else if (collision_side == 1 && p_vel->y < 0 && !platform->one_way) {
                    // Hit bottom
                    p_pos->y = plat_pos->y + plat_col->height;
                    p_vel->y = 0;
                } else if (collision_side == 2 && !platform->one_way) {
                    // Hit from left
                    p_pos->x = plat_pos->x - p_col->width;
                    p_vel->x = 0;
                } else if (collision_side == 3 && !platform->one_way) {
                    // Hit from right
                    p_pos->x = plat_pos->x + plat_col->width;
                    p_vel->x = 0;
                }
            }
        }
        
        // Enemy collision
        for (int j = 0; j < enemies.size; j++) {
            EntityID* enemy_ent = array_get(&enemies, j);
            if (!enemy_ent) continue;
            
            PositionComponent* e_pos = world_get_component(world, *enemy_ent, CT_POSITION);
            ColliderComponent* e_col = world_get_component(world, *enemy_ent, CT_COLLIDER);
            
            if (!e_pos || !e_col) continue;
            
            if (check_collision(p_pos->x, p_pos->y, p_col->width, p_col->height,
                              e_pos->x, e_pos->y, e_col->width, e_col->height)) {
                
                // Check if jumping on enemy
                if (p_vel->y > 0 && p_pos->y + p_col->height - 8 < e_pos->y + e_col->height / 2) {
                    world_destroy_entity(world, *enemy_ent);
                    p_vel->y = -120.0f;
                    world->score += 100;
                } else {
                    // Take damage
                    player->lives--;
                    if (player->lives <= 0) {
                        world->game_over = true;
                    } else {
                        // Knockback
                        float knockback_dir = (p_pos->x < e_pos->x) ? -1.0f : 1.0f;
                        p_vel->x = knockback_dir * 100.0f;
                        p_vel->y = -80.0f;
                    }
                }
            }
        }
        
        // Collectible collision
        for (int j = 0; j < collectibles.size; j++) {
            EntityID* coll_ent = array_get(&collectibles, j);
            if (!coll_ent) continue;
            
            CollectibleComponent* coll = world_get_component(world, *coll_ent, CT_COLLECTIBLE);
            
            if (!coll || coll->collected) continue;
            
            PositionComponent* c_pos = world_get_component(world, *coll_ent, CT_POSITION);
            ColliderComponent* c_col = world_get_component(world, *coll_ent, CT_COLLIDER);
            
            if (!c_pos || !c_col) continue;
            
            if (check_collision(p_pos->x, p_pos->y, p_col->width, p_col->height,
                              c_pos->x, c_pos->y, c_col->width, c_col->height)) {
                coll->collected = true;
                world->score += coll->points;
                world_destroy_entity(world, *coll_ent);
            }
        }
    }
    
    array_free(&players);
    array_free(&platforms);
    array_free(&enemies);
    array_free(&collectibles);
}

CollisionSystem* create_collision_system(void) {
    CollisionSystem* sys = malloc(sizeof(CollisionSystem));
    assert(sys);
    sys->base.update = collision_update;
    sys->base.cleanup = NULL;
    return sys;
}

// Enemy AI System
void enemy_ai_update(System* self, World* world, float dt) {
    if (!self || !world) return;
    
    int required[] = {CT_ENEMY, CT_POSITION, CT_VELOCITY};
    Array entities = world_query(world, required, 3);
    
    for (int i = 0; i < entities.size; i++) {
        EntityID* entity = array_get(&entities, i);
        if (!entity) continue;
        
        EnemyComponent* enemy = world_get_component(world, *entity, CT_ENEMY);
        PositionComponent* pos = world_get_component(world, *entity, CT_POSITION);
        VelocityComponent* vel = world_get_component(world, *entity, CT_VELOCITY);
        
        if (!enemy || !pos || !vel) continue;
        
        vel->x = enemy->move_speed * enemy->move_direction;
        
        if (pos->x <= enemy->patrol_start) {
            enemy->move_direction = 1.0f;
            pos->x = enemy->patrol_start;
        } else if (pos->x >= enemy->patrol_end) {
            enemy->move_direction = -1.0f;
            pos->x = enemy->patrol_end;
        }
    }
    
    array_free(&entities);
}

EnemyAISystem* create_enemy_ai_system(void) {
    EnemyAISystem* sys = malloc(sizeof(EnemyAISystem));
    assert(sys);
    sys->base.update = enemy_ai_update;
    sys->base.cleanup = NULL;
    return sys;
}

// Render System - IMPROVED with better camera
void render_update(System* self, World* world, float dt) {
    if (!self || !world) return;
    
    // Clear screen to sky blue
    display_clear(COLOR_CYAN);
    
    // Update camera to follow player smoothly
    if (world->player_entity > 0) {
        PositionComponent* player_pos = world_get_component(world, world->player_entity, CT_POSITION);
        if (player_pos) {
            // Center camera on player with smooth follow
            float target_camera_x = player_pos->x - DISPLAY_WIDTH / 2;
            
            // Clamp camera to world bounds
            if (target_camera_x < 0) target_camera_x = 0;
            if (target_camera_x > WORLD_WIDTH - DISPLAY_WIDTH) {
                target_camera_x = WORLD_WIDTH - DISPLAY_WIDTH;
            }
            
            // Smooth camera movement
            float camera_speed = 5.0f;
            world->camera_x += (target_camera_x - world->camera_x) * camera_speed * dt;
        }
    }
    
    // Render platforms
    int platform_required[] = {CT_PLATFORM, CT_POSITION, CT_SPRITE};
    Array platforms = world_query(world, platform_required, 3);
    
    for (int i = 0; i < platforms.size; i++) {
        EntityID* entity = array_get(&platforms, i);
        if (!entity) continue;
        
        PositionComponent* pos = world_get_component(world, *entity, CT_POSITION);
        SpriteComponent* sprite = world_get_component(world, *entity, CT_SPRITE);
        
        if (!pos || !sprite) continue;
        
        int screen_x = (int)(pos->x - world->camera_x);
        int screen_y = (int)pos->y;
        
        // Only render if on screen
        if (screen_x + sprite->width >= 0 && screen_x < DISPLAY_WIDTH) {
            display_fill_rect(screen_x, screen_y, sprite->width, sprite->height, sprite->color);
        }
    }
    array_free(&platforms);
    
    // Render collectibles
    int coll_required[] = {CT_COLLECTIBLE, CT_POSITION, CT_SPRITE};
    Array collectibles = world_query(world, coll_required, 3);
    
    for (int i = 0; i < collectibles.size; i++) {
        EntityID* entity = array_get(&collectibles, i);
        if (!entity) continue;
        
        CollectibleComponent* coll = world_get_component(world, *entity, CT_COLLECTIBLE);
        
        if (!coll || coll->collected) continue;
        
        PositionComponent* pos = world_get_component(world, *entity, CT_POSITION);
        SpriteComponent* sprite = world_get_component(world, *entity, CT_SPRITE);
        
        if (!pos || !sprite) continue;
        
        int screen_x = (int)(pos->x - world->camera_x);
        int screen_y = (int)pos->y;
        
        if (screen_x + sprite->width >= 0 && screen_x < DISPLAY_WIDTH) {
            display_fill_rect(screen_x, screen_y, sprite->width, sprite->height, sprite->color);
        }
    }
    array_free(&collectibles);
    
    // Render enemies
    int enemy_required[] = {CT_ENEMY, CT_POSITION, CT_SPRITE};
    Array enemies = world_query(world, enemy_required, 3);
    
    for (int i = 0; i < enemies.size; i++) {
        EntityID* entity = array_get(&enemies, i);
        if (!entity) continue;
        
        PositionComponent* pos = world_get_component(world, *entity, CT_POSITION);
        SpriteComponent* sprite = world_get_component(world, *entity, CT_SPRITE);
        
        if (!pos || !sprite) continue;
        
        int screen_x = (int)(pos->x - world->camera_x);
        int screen_y = (int)pos->y;
        
        if (screen_x + sprite->width >= 0 && screen_x < DISPLAY_WIDTH) {
            display_fill_rect(screen_x, screen_y, sprite->width, sprite->height, sprite->color);
        }
    }
    array_free(&enemies);
    
    // Render player (always render, even off screen slightly)
    int player_required[] = {CT_PLAYER, CT_POSITION, CT_SPRITE};
    Array players = world_query(world, player_required, 3);
    
    for (int i = 0; i < players.size; i++) {
        EntityID* entity = array_get(&players, i);
        if (!entity) continue;
        
        PositionComponent* pos = world_get_component(world, *entity, CT_POSITION);
        SpriteComponent* sprite = world_get_component(world, *entity, CT_SPRITE);
        
        if (!pos || !sprite) continue;
        
        int screen_x = (int)(pos->x - world->camera_x);
        int screen_y = (int)pos->y;
        
        display_fill_rect(screen_x, screen_y, sprite->width, sprite->height, sprite->color);
    }
    array_free(&players);
    
    // UI - Score
    char score_text[32];
    snprintf(score_text, sizeof(score_text), "Score: %d", world->score);
    display_draw_string(5, 5, score_text, COLOR_WHITE, COLOR_BLACK);
    
    // UI - Lives
    if (world->player_entity > 0) {
        PlayerComponent* player = world_get_component(world, world->player_entity, CT_PLAYER);
        if (player) {
            char lives_text[32];
            snprintf(lives_text, sizeof(lives_text), "Lives: %d", player->lives);
            display_draw_string(5, 15, lives_text, COLOR_WHITE, COLOR_BLACK);
        }
    }
    
    // Game over screen
    if (world->game_over) {
        display_draw_string(DISPLAY_WIDTH/2 - 30, DISPLAY_HEIGHT/2, "GAME OVER", COLOR_RED, COLOR_BLACK);
        display_draw_string(DISPLAY_WIDTH/2 - 40, DISPLAY_HEIGHT/2 + 15, "Y: Restart", COLOR_YELLOW, COLOR_BLACK);
    }
}

RenderSystem* create_render_system(void) {
    RenderSystem* sys = malloc(sizeof(RenderSystem));
    assert(sys);
    sys->base.update = render_update;
    sys->base.cleanup = NULL;
    return sys;
}

// Game init - IMPROVED LEVEL with FIXED player spawn position
void game_create_level(World* world) {
    assert(world);
    
    // Create extended ground platforms
    int ground_platform_count = (WORLD_WIDTH / 80) + 2;
    for (int i = 0; i < ground_platform_count; i++) {
        EntityID platform = world_create_entity(world);
        
        PositionComponent pos = {i * 80.0f, GROUND_HEIGHT};
        world_add_component(world, platform, CT_POSITION, &pos, sizeof(PositionComponent));
        
        SpriteComponent sprite = {COLOR_GREEN, 80, 20, NULL};
        world_add_component(world, platform, CT_SPRITE, &sprite, sizeof(SpriteComponent));
        
        ColliderComponent collider = {80, 20, 0, 0};
        world_add_component(world, platform, CT_COLLIDER, &collider, sizeof(ColliderComponent));
        
        PlatformComponent plat = {true, false};
        world_add_component(world, platform, CT_PLATFORM, &plat, sizeof(PlatformComponent));
    }
    
    // Create floating platforms throughout the level
    typedef struct {
        float x;
        float y;
        float w;
    } PlatformData;
    
    PlatformData floating_platforms[] = {
        {150, 180, 60},
        {280, 150, 60},
        {420, 180, 60},
        {580, 140, 70},
        {750, 160, 60},
        {900, 130, 80},
        {1080, 170, 60},
        {1240, 140, 70},
        {1400, 180, 60},
        {1560, 150, 60},
        {1720, 130, 70},
        {1880, 160, 60},
    };
    
    for (int i = 0; i < sizeof(floating_platforms) / sizeof(floating_platforms[0]); i++) {
        EntityID plat = world_create_entity(world);
        PositionComponent pos = {floating_platforms[i].x, floating_platforms[i].y};
        world_add_component(world, plat, CT_POSITION, &pos, sizeof(PositionComponent));
        
        SpriteComponent sprite = {COLOR_GREEN, (uint8_t)floating_platforms[i].w, 15, NULL};
        world_add_component(world, plat, CT_SPRITE, &sprite, sizeof(SpriteComponent));
        
        ColliderComponent collider = {floating_platforms[i].w, 15, 0, 0};
        world_add_component(world, plat, CT_COLLIDER, &collider, sizeof(ColliderComponent));
        
        PlatformComponent plat_comp = {true, false};
        world_add_component(world, plat, CT_PLATFORM, &plat_comp, sizeof(PlatformComponent));
    }
    
    // Create enemies throughout the level
    typedef struct {
        float x;
        float y;
        float patrol_start;
        float patrol_end;
        float speed;
    } EnemyData;
    
    EnemyData enemy_data[] = {
        {250, 200, 200, 350, 30},
        {450, 160, 400, 500, 35},
        {700, 140, 650, 800, 40},
        {1000, 200, 950, 1100, 30},
        {1300, 160, 1250, 1400, 35},
        {1600, 130, 1550, 1750, 40},
    };
    
    for (int i = 0; i < sizeof(enemy_data) / sizeof(enemy_data[0]); i++) {
        EntityID enemy = world_create_entity(world);
        
        PositionComponent e_pos = {enemy_data[i].x, enemy_data[i].y};
        world_add_component(world, enemy, CT_POSITION, &e_pos, sizeof(PositionComponent));
        
        VelocityComponent e_vel = {0, 0};
        world_add_component(world, enemy, CT_VELOCITY, &e_vel, sizeof(VelocityComponent));
        
        SpriteComponent e_sprite = {COLOR_RED, 12, 12, NULL};
        world_add_component(world, enemy, CT_SPRITE, &e_sprite, sizeof(SpriteComponent));
        
        ColliderComponent e_collider = {12, 12, 0, 0};
        world_add_component(world, enemy, CT_COLLIDER, &e_collider, sizeof(ColliderComponent));
        
        EnemyComponent e_comp = {
            enemy_data[i].speed,
            1.0f,
            enemy_data[i].patrol_start,
            enemy_data[i].patrol_end
        };
        world_add_component(world, enemy, CT_ENEMY, &e_comp, sizeof(EnemyComponent));
        
        PhysicsComponent e_phys = {400.0f, 200.0f, 0.9f, true};
        world_add_component(world, enemy, CT_PHYSICS, &e_phys, sizeof(PhysicsComponent));
    }
    
    // Create collectibles (coins) throughout the level
    for (int i = 0; i < 20; i++) {
        EntityID coin = world_create_entity(world);
        
        float coin_x = 150.0f + i * 100.0f;
        float coin_y = 100.0f + (i % 3) * 30.0f;
        
        PositionComponent c_pos = {coin_x, coin_y};
        world_add_component(world, coin, CT_POSITION, &c_pos, sizeof(PositionComponent));
        
        SpriteComponent c_sprite = {COLOR_YELLOW, 8, 8, NULL};
        world_add_component(world, coin, CT_SPRITE, &c_sprite, sizeof(SpriteComponent));
        
        ColliderComponent c_collider = {8, 8, 0, 0};
        world_add_component(world, coin, CT_COLLIDER, &c_collider, sizeof(ColliderComponent));
        
        CollectibleComponent c_comp = {50, false};
        world_add_component(world, coin, CT_COLLECTIBLE, &c_comp, sizeof(CollectibleComponent));
    }
    
    // Create player - FIXED: spawn on ground
    EntityID player = world_create_entity(world);
    world->player_entity = player;
    
    // FIXED: Place player ON the ground platform (ground_y - player_height)
    PositionComponent p_pos = {50.0f, GROUND_HEIGHT - 14.0f};
    world_add_component(world, player, CT_POSITION, &p_pos, sizeof(PositionComponent));
    
    VelocityComponent p_vel = {0, 0};
    world_add_component(world, player, CT_VELOCITY, &p_vel, sizeof(VelocityComponent));
    
    SpriteComponent p_sprite = {COLOR_BLUE, 14, 14, NULL};
    world_add_component(world, player, CT_SPRITE, &p_sprite, sizeof(SpriteComponent));
    
    ColliderComponent p_collider = {14, 14, 0, 0};
    world_add_component(world, player, CT_COLLIDER, &p_collider, sizeof(ColliderComponent));
    
    PlayerComponent p_player = {false, 0, 2, 3};
    world_add_component(world, player, CT_PLAYER, &p_player, sizeof(PlayerComponent));
    
    PhysicsComponent p_phys = {400.0f, 300.0f, 0.85f, true};
    world_add_component(world, player, CT_PHYSICS, &p_phys, sizeof(PhysicsComponent));
}

void game_init(World* world) {
    assert(world);
    
    world_init(world);
    
    // Add systems in order
    world_add_system(world, (System*)create_input_system());
    world_add_system(world, (System*)create_enemy_ai_system());
    world_add_system(world, (System*)create_physics_system());
    world_add_system(world, (System*)create_collision_system());
    world_add_system(world, (System*)create_render_system());
    
    // Create level entities
    game_create_level(world);
}
