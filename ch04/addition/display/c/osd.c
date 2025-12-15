#include "osd_menu.h"
#include <string.h>
#include <stdio.h>

// Internal state
static struct {
    menu_t *root_menu;
    menu_t *current_menu;
    menu_t *menu_stack[MAX_MENU_DEPTH];
    uint8_t stack_depth;
    uint8_t selected_index;
    menu_state_t state;
    menu_style_t style;
    bool needs_redraw;
    uint32_t last_button_time;
} menu_ctx;

// Default style configuration
const menu_style_t default_menu_style = {
    .x = 40,
    .y = 30,
    .width = 240,
    .height = 180,
    .bg_color = 0x2945,           // Dark blue-gray
    .border_color = COLOR_CYAN,
    .text_color = COLOR_WHITE,
    .selected_bg_color = COLOR_BLUE,
    .selected_text_color = COLOR_YELLOW,
    .disabled_color = 0x7BEF,     // Light gray
    .title_bg_color = COLOR_BLUE,
    .title_text_color = COLOR_WHITE
};

// Helper: clamp value to range
static int clamp(int value, int min, int max) {
    if (value < min) return min;
    if (value > max) return max;
    return value;
}

// Helper: get current time in ms
static uint32_t get_time_ms(void) {
    return to_ms_since_boot(get_absolute_time());
}

// Internal: navigate menu
static void navigate_up(void) {
    if (menu_ctx.selected_index > 0) {
        menu_ctx.selected_index--;
        menu_ctx.needs_redraw = true;
    }
}

static void navigate_down(void) {
    if (menu_ctx.current_menu && 
        menu_ctx.selected_index < menu_ctx.current_menu->item_count - 1) {
        menu_ctx.selected_index++;
        menu_ctx.needs_redraw = true;
    }
}

static void enter_submenu(menu_t *submenu) {
    if (menu_ctx.stack_depth < MAX_MENU_DEPTH - 1) {
        menu_ctx.menu_stack[menu_ctx.stack_depth++] = menu_ctx.current_menu;
        menu_ctx.current_menu = submenu;
        menu_ctx.selected_index = 0;
        menu_ctx.needs_redraw = true;
    }
}

static void go_back(void) {
    if (menu_ctx.stack_depth > 0) {
        menu_ctx.current_menu = menu_ctx.menu_stack[--menu_ctx.stack_depth];
        menu_ctx.selected_index = 0;
        menu_ctx.needs_redraw = true;
    } else {
        osd_menu_hide();
    }
}

static void activate_item(void) {
    if (!menu_ctx.current_menu) return;
    
    menu_item_t *item = &menu_ctx.current_menu->items[menu_ctx.selected_index];
    
    if (!item->enabled) return;
    
    switch (item->type) {
        case MENU_ITEM_ACTION:
            if (item->data.action) {
                item->data.action();
            }
            break;
            
        case MENU_ITEM_SUBMENU:
            if (item->data.submenu) {
                enter_submenu(item->data.submenu);
            }
            break;
            
        case MENU_ITEM_TOGGLE:
            if (item->data.toggle.value) {
                *item->data.toggle.value = !(*item->data.toggle.value);
                if (item->data.toggle.callback) {
                    item->data.toggle.callback(*item->data.toggle.value);
                }
                menu_ctx.needs_redraw = true;
            }
            break;
            
        case MENU_ITEM_BACK:
            go_back();
            break;
            
        case MENU_ITEM_VALUE:
            // Value items are adjusted with X/Y buttons, not activated
            break;
    }
}

static void adjust_value(int direction) {
    if (!menu_ctx.current_menu) return;
    
    menu_item_t *item = &menu_ctx.current_menu->items[menu_ctx.selected_index];
    
    if (item->type == MENU_ITEM_VALUE && item->enabled && item->data.value.value) {
        int *val = item->data.value.value;
        int new_val = *val + (direction * item->data.value.step);
        new_val = clamp(new_val, item->data.value.min, item->data.value.max);
        
        if (new_val != *val) {
            *val = new_val;
            if (item->data.value.callback) {
                item->data.value.callback(*val);
            }
            menu_ctx.needs_redraw = true;
        }
    }
}

// Button callbacks
static void button_a_callback(button_t button) {
    (void)button;
    if (menu_ctx.state == MENU_STATE_VISIBLE) {
        activate_item();
    }
}

static void button_b_callback(button_t button) {
    (void)button;
    if (menu_ctx.state == MENU_STATE_VISIBLE) {
        go_back();
    }
}

static void button_x_callback(button_t button) {
    (void)button;
    if (menu_ctx.state == MENU_STATE_VISIBLE) {
        adjust_value(-1);  // Decrease value
    }
}

static void button_y_callback(button_t button) {
    (void)button;
    if (menu_ctx.state == MENU_STATE_VISIBLE) {
        adjust_value(1);  // Increase value
    }
}

// Public API implementation
void osd_menu_init(void) {
    memset(&menu_ctx, 0, sizeof(menu_ctx));
    menu_ctx.style = default_menu_style;
    menu_ctx.state = MENU_STATE_HIDDEN;
    menu_ctx.needs_redraw = false;
    
    // Register button callbacks
    button_set_callback(BUTTON_A, button_a_callback);
    button_set_callback(BUTTON_B, button_b_callback);
    button_set_callback(BUTTON_X, button_x_callback);
    button_set_callback(BUTTON_Y, button_y_callback);
}

void osd_menu_set_root(menu_t *menu) {
    menu_ctx.root_menu = menu;
    menu_ctx.current_menu = menu;
    menu_ctx.stack_depth = 0;
    menu_ctx.selected_index = 0;
}

void osd_menu_show(void) {
    if (menu_ctx.state != MENU_STATE_VISIBLE && menu_ctx.current_menu) {
        menu_ctx.state = MENU_STATE_VISIBLE;
        menu_ctx.needs_redraw = true;
    }
}

void osd_menu_hide(void) {
    menu_ctx.state = MENU_STATE_HIDDEN;
    menu_ctx.needs_redraw = true;
}

void osd_menu_toggle(void) {
    if (menu_ctx.state == MENU_STATE_VISIBLE) {
        osd_menu_hide();
    } else {
        osd_menu_show();
    }
}

bool osd_menu_is_visible(void) {
    return menu_ctx.state == MENU_STATE_VISIBLE;
}

void osd_menu_set_style(const menu_style_t *style) {
    if (style) {
        menu_ctx.style = *style;
        menu_ctx.needs_redraw = true;
    }
}

void osd_menu_update(void) {
    // Manual navigation using button state checks (alternative to callbacks)
    uint32_t now = get_time_ms();
    
    if (menu_ctx.state == MENU_STATE_VISIBLE) {
        // Check for direct button presses with debounce
        if (now - menu_ctx.last_button_time > 150) {
            if (button_pressed(BUTTON_A)) {
                navigate_up();
                menu_ctx.last_button_time = now;
            } else if (button_pressed(BUTTON_B)) {
                navigate_down();
                menu_ctx.last_button_time = now;
            }
        }
    }
}

void osd_menu_render(void) {
    if (!menu_ctx.current_menu) return;
    
    // Only redraw if needed
    if (!menu_ctx.needs_redraw) return;
    
    menu_style_t *s = &menu_ctx.style;
    
    if (menu_ctx.state == MENU_STATE_HIDDEN) {
        // Could restore background here if we saved it
        menu_ctx.needs_redraw = false;
        return;
    }
    
    // Draw border
    display_fill_rect(s->x - 2, s->y - 2, s->width + 4, s->height + 4, s->border_color);
    
    // Draw background
    display_fill_rect(s->x, s->y, s->width, s->height, s->bg_color);
    
    // Draw title bar
    display_fill_rect(s->x, s->y, s->width, 16, s->title_bg_color);
    display_draw_string(s->x + 4, s->y + 4, menu_ctx.current_menu->title, 
                       s->title_text_color, s->title_bg_color);
    
    // Draw menu items
    uint16_t item_y = s->y + 20;
    const uint16_t item_height = 18;
    
    for (uint8_t i = 0; i < menu_ctx.current_menu->item_count; i++) {
        menu_item_t *item = &menu_ctx.current_menu->items[i];
        bool is_selected = (i == menu_ctx.selected_index);
        
        uint16_t bg = is_selected ? s->selected_bg_color : s->bg_color;
        uint16_t fg = item->enabled ? 
                     (is_selected ? s->selected_text_color : s->text_color) :
                     s->disabled_color;
        
        // Draw item background if selected
        if (is_selected) {
            display_fill_rect(s->x + 2, item_y, s->width - 4, item_height, bg);
        }
        
        // Build item text with value/state indicators
        char item_text[MENU_ITEM_MAX_LEN + 16];
        snprintf(item_text, sizeof(item_text), "%s", item->text);
        
        // Add indicators based on type
        switch (item->type) {
            case MENU_ITEM_SUBMENU:
                strcat(item_text, " >");
                break;
                
            case MENU_ITEM_TOGGLE:
                if (item->data.toggle.value) {
                    strcat(item_text, *item->data.toggle.value ? " ON" : " OFF");
                }
                break;
                
            case MENU_ITEM_VALUE:
                if (item->data.value.value) {
                    char val_str[12]; // NB: UPPER CASE
                    snprintf(val_str, sizeof(val_str), " %d", *item->data.value.value);
                    strcat(item_text, val_str);
                }
                break;
                
            case MENU_ITEM_BACK:
                // Could add back arrow
                break;
                
            default:
                break;
        }
        
        // Draw item text
        display_draw_string(s->x + 6, item_y + 5, item_text, fg, bg);
        
        item_y += item_height;
        
        // Stop if we exceed menu bounds
        if (item_y + item_height > s->y + s->height) break;
    }
    
    // Draw help text at bottom
    const char *help = "A:SELECT B:BACK X/Y:ADJUST";
    display_draw_string(s->x + 4, s->y + s->height - 12, help, 
                       s->text_color, s->bg_color);
    
    menu_ctx.needs_redraw = false;
}

// Menu creation helpers
menu_t* menu_create(const char *title) {
    static menu_t menus[16];  // Static allocation pool
    static uint8_t menu_count = 0;
    
    if (menu_count >= 16) return NULL;
    
    menu_t *menu = &menus[menu_count++];
    memset(menu, 0, sizeof(menu_t));
    strncpy(menu->title, title, MENU_TITLE_MAX_LEN - 1);
    
    return menu;
}

void menu_add_action(menu_t *menu, const char *text, menu_action_callback_t callback) {
    if (!menu || menu->item_count >= MAX_MENU_ITEMS) return;
    
    menu_item_t *item = &menu->items[menu->item_count++];
    memset(item, 0, sizeof(menu_item_t));
    strncpy(item->text, text, MENU_ITEM_MAX_LEN - 1);
    item->type = MENU_ITEM_ACTION;
    item->data.action = callback;
    item->enabled = true;
}

void menu_add_submenu(menu_t *menu, const char *text, menu_t *submenu) {
    if (!menu || !submenu || menu->item_count >= MAX_MENU_ITEMS) return;
    
    menu_item_t *item = &menu->items[menu->item_count++];
    memset(item, 0, sizeof(menu_item_t));
    strncpy(item->text, text, MENU_ITEM_MAX_LEN - 1);
    item->type = MENU_ITEM_SUBMENU;
    item->data.submenu = submenu;
    submenu->parent = menu;
    item->enabled = true;
}

void menu_add_toggle(menu_t *menu, const char *text, bool *value, menu_toggle_callback_t callback) {
    if (!menu || !value || menu->item_count >= MAX_MENU_ITEMS) return;
    
    menu_item_t *item = &menu->items[menu->item_count++];
    memset(item, 0, sizeof(menu_item_t));
    strncpy(item->text, text, MENU_ITEM_MAX_LEN - 1);
    item->type = MENU_ITEM_TOGGLE;
    item->data.toggle.value = value;
    item->data.toggle.callback = callback;
    item->enabled = true;
}

void menu_add_value(menu_t *menu, const char *text, int *value, int min, int max, int step, 
                    menu_value_callback_t callback) {
    if (!menu || !value || menu->item_count >= MAX_MENU_ITEMS) return;
    
    menu_item_t *item = &menu->items[menu->item_count++];
    memset(item, 0, sizeof(menu_item_t));
    strncpy(item->text, text, MENU_ITEM_MAX_LEN - 1);
    item->type = MENU_ITEM_VALUE;
    item->data.value.value = value;
    item->data.value.min = min;
    item->data.value.max = max;
    item->data.value.step = step;
    item->data.value.callback = callback;
    item->enabled = true;
}

void menu_add_back(menu_t *menu) {
    if (!menu || menu->item_count >= MAX_MENU_ITEMS) return;
    
    menu_item_t *item = &menu->items[menu->item_count++];
    memset(item, 0, sizeof(menu_item_t));
    strncpy(item->text, "< BACK", MENU_ITEM_MAX_LEN - 1);
    item->type = MENU_ITEM_BACK;
    item->enabled = true;
}

void menu_item_set_enabled(menu_t *menu, uint8_t index, bool enabled) {
    if (!menu || index >= menu->item_count) return;
    menu->items[index].enabled = enabled;
    menu_ctx.needs_redraw = true;
}
