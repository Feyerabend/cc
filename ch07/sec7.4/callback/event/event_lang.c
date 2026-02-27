#define _POSIX_C_SOURCE 200809L
#include "event_lang.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

// Helper to get current timestamp
static double get_timestamp(void) {
    return (double)clock() / CLOCKS_PER_SEC;
}

// Create a new event system
EventSystem *event_system_create(void) {
    EventSystem *sys = malloc(sizeof(EventSystem));
    if (!sys) return NULL;
    
    sys->listeners = NULL;
    sys->listener_count = 0;
    return sys;
}

// Destroy event system and free all resources
void event_system_destroy(EventSystem *sys) {
    if (!sys) return;
    
    EventListener *current = sys->listeners;
    while (current) {
        EventListener *next = current->next;
        free(current->event_name);
        free(current);
        current = next;
    }
    
    free(sys);
}

// Internal helper to add a listener
static void add_listener(EventSystem *sys, const char *event_name, 
                        EventCallback callback, void *user_data, bool once) {
    if (!sys || !event_name || !callback) return;
    
    EventListener *listener = malloc(sizeof(EventListener));
    if (!listener) return;
    
    listener->event_name = strdup(event_name);
    listener->callback = callback;
    listener->user_data = user_data;
    listener->once = once;
    listener->next = sys->listeners;
    
    sys->listeners = listener;
    sys->listener_count++;
}

// Register a persistent event listener
void event_on(EventSystem *sys, const char *event_name, 
              EventCallback callback, void *user_data) {
    add_listener(sys, event_name, callback, user_data, false);
}

// Register a one-time event listener
void event_once(EventSystem *sys, const char *event_name, 
                EventCallback callback, void *user_data) {
    add_listener(sys, event_name, callback, user_data, true);
}

// Remove event listener
void event_off(EventSystem *sys, const char *event_name, EventCallback callback) {
    if (!sys || !event_name) return;
    
    EventListener **current = &sys->listeners;
    while (*current) {
        EventListener *listener = *current;
        if (strcmp(listener->event_name, event_name) == 0 && 
            listener->callback == callback) {
            *current = listener->next;
            free(listener->event_name);
            free(listener);
            sys->listener_count--;
        } else {
            current = &listener->next;
        }
    }
}

// Emit an event with custom data
void event_emit(EventSystem *sys, const char *event_name, EventData data) {
    if (!sys || !event_name) return;
    
    // Create event
    Event event = {
        .name = (char *)event_name,
        .data = data,
        .timestamp = get_timestamp()
    };
    
    // Find and call all matching listeners
    EventListener **current = &sys->listeners;
    while (*current) {
        EventListener *listener = *current;
        
        if (strcmp(listener->event_name, event_name) == 0) {
            // Call the callback
            listener->callback(&event, listener->user_data);
            
            // Remove if it's a one-time listener
            if (listener->once) {
                *current = listener->next;
                free(listener->event_name);
                free(listener);
                sys->listener_count--;
                continue;
            }
        }
        
        current = &listener->next;
    }
}

// Convenience: emit integer event
void event_emit_int(EventSystem *sys, const char *event_name, int value) {
    EventData data = {
        .type = EVENT_DATA_INT,
        .value.i = value
    };
    event_emit(sys, event_name, data);
}

// Convenience: emit float event
void event_emit_float(EventSystem *sys, const char *event_name, float value) {
    EventData data = {
        .type = EVENT_DATA_FLOAT,
        .value.f = value
    };
    event_emit(sys, event_name, data);
}

// Convenience: emit string event
void event_emit_string(EventSystem *sys, const char *event_name, const char *value) {
    EventData data = {
        .type = EVENT_DATA_STRING,
        .value.s = (char *)value
    };
    event_emit(sys, event_name, data);
}

// Get count of listeners for a specific event
size_t event_listener_count(EventSystem *sys, const char *event_name) {
    if (!sys || !event_name) return 0;
    
    size_t count = 0;
    EventListener *current = sys->listeners;
    while (current) {
        if (strcmp(current->event_name, event_name) == 0) {
            count++;
        }
        current = current->next;
    }
    
    return count;
}
