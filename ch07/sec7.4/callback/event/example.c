#include "event_lang.h"
#include <stdio.h>

// Example callbacks

void on_user_login(const Event *event, void *user_data) {
    (void)user_data;  // Unused
    if (event->data.type == EVENT_DATA_STRING) {
        printf("[LOGIN] User '%s' logged in at %.3fs\n", 
               event->data.value.s, event->timestamp);
    }
}

void on_score_update(const Event *event, void *user_data) {
    if (event->data.type == EVENT_DATA_INT) {
        int *total_score = (int *)user_data;
        *total_score += event->data.value.i;
        printf("[SCORE] Points earned: %d (Total: %d)\n", 
               event->data.value.i, *total_score);
    }
}

void on_game_over(const Event *event, void *user_data) {
    (void)event;      // Unused
    (void)user_data;  // Unused
    printf("[GAME] Game Over!\n");
}

void on_achievement(const Event *event, void *user_data) {
    (void)user_data;  // Unused
    if (event->data.type == EVENT_DATA_STRING) {
        printf("🏆 Achievement unlocked: %s\n", event->data.value.s);
    }
}

void on_welcome_message(const Event *event, void *user_data) {
    (void)event;      // Unused
    (void)user_data;  // Unused
    printf("[WELCOME] This message appears only once!\n");
}

// Example: Temperature monitoring system
void on_temperature_change(const Event *event, void *user_data) {
    (void)user_data;  // Unused
    if (event->data.type == EVENT_DATA_FLOAT) {
        float temp = event->data.value.f;
        printf("[SENSOR] Temperature: %.1f°C", temp);
        
        if (temp > 30.0f) {
            printf("    HIGH\n");
        } else if (temp < 10.0f) {
            printf("    LOW\n");
        } else {
            printf("   Normal\n");
        }
    }
}

int main(void) {
    // Create the event system
    EventSystem *sys = event_system_create();
    if (!sys) {
        fprintf(stderr, "Failed to create event system\n");
        return 1;
    }
    
    printf("=== Event-Driven Language Demo ===\n\n");
    
    // Example 1: Simple event with callbacks
    printf("--- Example 1: User Login Events ---\n");
    event_on(sys, "user:login", on_user_login, NULL);
    
    event_emit_string(sys, "user:login", "alice");
    event_emit_string(sys, "user:login", "bob");
    printf("\n");
    
    // Example 2: Stateful callbacks (tracking score)
    printf("--- Example 2: Score Tracking ---\n");
    int total_score = 0;
    event_on(sys, "score:update", on_score_update, &total_score);
    
    event_emit_int(sys, "score:update", 100);
    event_emit_int(sys, "score:update", 250);
    event_emit_int(sys, "score:update", 75);
    printf("\n");
    
    // Example 3: One-time events
    printf("--- Example 3: One-Time Events ---\n");
    event_once(sys, "game:start", on_welcome_message, NULL);
    
    event_emit_string(sys, "game:start", "");
    event_emit_string(sys, "game:start", "");  // Won't trigger again
    printf("\n");
    
    // Example 4: Multiple listeners on same event
    printf("--- Example 4: Multiple Listeners ---\n");
    event_on(sys, "game:over", on_game_over, NULL);
    event_on(sys, "game:over", on_achievement, NULL);
    
    EventData final_data = {
        .type = EVENT_DATA_STRING,
        .value.s = "First Victory!"
    };
    event_emit(sys, "game:over", final_data);
    printf("\n");
    
    // Example 5: Temperature sensor simulation
    printf("--- Example 5: Temperature Monitoring ---\n");
    event_on(sys, "sensor:temperature", on_temperature_change, NULL);
    
    event_emit_float(sys, "sensor:temperature", 22.5f);
    event_emit_float(sys, "sensor:temperature", 35.2f);
    event_emit_float(sys, "sensor:temperature", 5.8f);
    event_emit_float(sys, "sensor:temperature", 20.0f);
    printf("\n");
    
    // Show listener statistics
    printf("--- Statistics ---\n");
    printf("Total listeners: %zu\n", sys->listener_count);
    printf("'score:update' listeners: %zu\n", 
           event_listener_count(sys, "score:update"));
    printf("'sensor:temperature' listeners: %zu\n", 
           event_listener_count(sys, "sensor:temperature"));
    printf("\n");
    
    // Remove a listener
    printf("--- Removing Listener ---\n");
    event_off(sys, "score:update", on_score_update);
    printf("Removed score listener. Emitting score event...\n");
    event_emit_int(sys, "score:update", 500);  // Won't print
    printf("(No output - listener removed)\n\n");
    
    // Cleanup
    event_system_destroy(sys);
    printf("Event system destroyed. Demo complete!\n");
    
    return 0;
}
