#ifndef OSD_MENU_H
#define OSD_MENU_H

#include <stdint.h>
#include <stdbool.h>
#include "display.h"

// Menu configuration
#define MAX_MENU_ITEMS 8
#define MAX_MENU_DEPTH 4
#define MENU_TITLE_MAX_LEN 32
#define MENU_ITEM_MAX_LEN 28

// Menu item types
typedef enum {
    MENU_ITEM_ACTION,      // Executes a callback
    MENU_ITEM_SUBMENU,     // Opens a submenu
    MENU_ITEM_TOGGLE,      // Boolean toggle
    MENU_ITEM_VALUE,       // Numeric value with +/- adjustment
    MENU_ITEM_BACK         // Go back to parent menu
} menu_item_type_t;

// Fwd decl
typedef struct menu_item_s menu_item_t;
typedef struct menu_s menu_t;

// Callback types
typedef void (*menu_action_callback_t)(void);
typedef void (*menu_toggle_callback_t)(bool value);
typedef void (*menu_value_callback_t)(int value);

// Menu item structure
struct menu_item_s {
    char text[MENU_ITEM_MAX_LEN];
    menu_item_type_t type;
    
    union {
        menu_action_callback_t action;      // For MENU_ITEM_ACTION
        menu_t *submenu;                    // For MENU_ITEM_SUBMENU
        struct {
            bool *value;
            menu_toggle_callback_t callback;
        } toggle;                           // For MENU_ITEM_TOGGLE
        struct {
            int *value;
            int min;
            int max;
            int step;
            menu_value_callback_t callback;
        } value;                            // For MENU_ITEM_VALUE
    } data;
    
    bool enabled;  // Can be disabled to gray out
};

// Menu structure
struct menu_s {
    char title[MENU_TITLE_MAX_LEN];
    menu_item_t items[MAX_MENU_ITEMS];
    uint8_t item_count;
    menu_t *parent;  // NULL for root menu
};

// Menu display configuration
typedef struct {
    uint16_t x;
    uint16_t y;
    uint16_t width;
    uint16_t height;
    uint16_t bg_color;
    uint16_t border_color;
    uint16_t text_color;
    uint16_t selected_bg_color;
    uint16_t selected_text_color;
    uint16_t disabled_color;
    uint16_t title_bg_color;
    uint16_t title_text_color;
} menu_style_t;

// Menu system state
typedef enum {
    MENU_STATE_HIDDEN,
    MENU_STATE_VISIBLE,
    MENU_STATE_ANIMATING
} menu_state_t;

// Public API
void osd_menu_init(void);
void osd_menu_set_root(menu_t *menu);
void osd_menu_show(void);
void osd_menu_hide(void);
void osd_menu_toggle(void);
void osd_menu_update(void);
void osd_menu_render(void);
bool osd_menu_is_visible(void);
void osd_menu_set_style(const menu_style_t *style);

// Menu creation helpers
menu_t* menu_create(const char *title);
void menu_add_action(menu_t *menu, const char *text, menu_action_callback_t callback);
void menu_add_submenu(menu_t *menu, const char *text, menu_t *submenu);
void menu_add_toggle(menu_t *menu, const char *text, bool *value, menu_toggle_callback_t callback);
void menu_add_value(menu_t *menu, const char *text, int *value, int min, int max, int step, menu_value_callback_t callback);
void menu_add_back(menu_t *menu);
void menu_item_set_enabled(menu_t *menu, uint8_t index, bool enabled);

// Default style (can be customised)
extern const menu_style_t default_menu_style;

#endif // OSD_MENU_H
