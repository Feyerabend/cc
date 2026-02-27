#ifndef EVENT_LANG_H
#define EVENT_LANG_H

#include <stddef.h>
#include <stdbool.h>

// Event data structure - can hold different types
typedef struct {
    enum {
        EVENT_DATA_INT,
        EVENT_DATA_FLOAT,
        EVENT_DATA_STRING,
        EVENT_DATA_PTR
    } type;
    union {
        int i;
        float f;
        char *s;
        void *ptr;
    } value;
} EventData;

// Forward declarations
typedef struct Event Event;
typedef struct EventListener EventListener;
typedef struct EventSystem EventSystem;

// Callback function type
typedef void (*EventCallback)(const Event *event, void *user_data);

// Event structure
struct Event {
    char *name;
    EventData data;
    double timestamp;
};

// Event listener (callback registration)
struct EventListener {
    char *event_name;
    EventCallback callback;
    void *user_data;
    bool once;  // Fire only once then auto-remove
    EventListener *next;
};

// Event system (manages all events and listeners)
struct EventSystem {
    EventListener *listeners;
    size_t listener_count;
};

// Core API
EventSystem *event_system_create(void);
void event_system_destroy(EventSystem *sys);

// Register event listeners
void event_on(EventSystem *sys, const char *event_name, EventCallback callback, void *user_data);
void event_once(EventSystem *sys, const char *event_name, EventCallback callback, void *user_data);
void event_off(EventSystem *sys, const char *event_name, EventCallback callback);

// Emit events
void event_emit(EventSystem *sys, const char *event_name, EventData data);
void event_emit_int(EventSystem *sys, const char *event_name, int value);
void event_emit_float(EventSystem *sys, const char *event_name, float value);
void event_emit_string(EventSystem *sys, const char *event_name, const char *value);

// Utility
size_t event_listener_count(EventSystem *sys, const char *event_name);

#endif // EVENT_LANG_H
