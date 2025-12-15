#include "osd_menu.h"
#include "display.h"
#include <stdio.h>

// Example: Application state variables
static bool wifi_enabled = true;
static bool bluetooth_enabled = false;
static int brightness = 75;
static int volume = 50;
static int contrast = 100;

// Example: Action callbacks
static void action_restart(void) {
    // Display confirmation message
    display_fill_rect(60, 100, 200, 40, COLOR_RED);
    display_draw_string(70, 110, "RESTARTING..", COLOR_WHITE, COLOR_RED);
    sleep_ms(1000);
}

static void action_factory_reset(void) {
    display_fill_rect(60, 100, 200, 40, COLOR_RED);
    display_draw_string(70, 110, "FACTORY RESET!", COLOR_WHITE, COLOR_RED);
    sleep_ms(1000);
    
    // Reset all values
    wifi_enabled = true;
    bluetooth_enabled = false;
    brightness = 75;
    volume = 50;
    contrast = 100;
}

static void action_about(void) {
    display_fill_rect(40, 80, 240, 80, COLOR_BLUE);
    display_draw_string(50, 90, "PICO OSD DISPLAY 1.0", COLOR_WHITE, COLOR_BLUE);
    display_draw_string(50, 105, "BUILT: 2025-10-27", COLOR_WHITE, COLOR_BLUE);
    display_draw_string(50, 120, "PRESS B TO CLOSE", COLOR_YELLOW, COLOR_BLUE);
    
    // Wait for button
    while (!button_just_pressed(BUTTON_B)) {
        buttons_update();
        sleep_ms(10);
    }
}

// Example: Toggle callbacks (called when toggle changes)
static void on_wifi_change(bool enabled) {
    printf("WiFi %s\n", enabled ? "enabled" : "disabled");
    // Add actual WiFi control code here
}

static void on_bluetooth_change(bool enabled) {
    printf("Bluetooth %s\n", enabled ? "enabled" : "disabled");
    // Add actual Bluetooth control code here
}

// Example: Value callbacks (called when value changes)
static void on_brightness_change(int value) {
    printf("Brightness: %d%%\n", value);
    // Could control actual backlight PWM here
}

static void on_volume_change(int value) {
    printf("Volume: %d%%\n", value);
    // Add audio volume control here
}

static void on_contrast_change(int value) {
    printf("Contrast: %d%%\n", value);
    // Add display contrast control here
}

// Build the menu structure
void setup_menus(void) {
    // Create main menu
    menu_t *main_menu = menu_create("MAIN MENU");
    
    // Create submenus
    menu_t *settings_menu = menu_create("SETTINGS");
    menu_t *display_menu = menu_create("DISPLAY");
    menu_t *network_menu = menu_create("NETWORK");
    menu_t *system_menu = menu_create("SYSTEM");
    
    // Build Settings submenu
    menu_add_submenu(settings_menu, "DISPLAY", display_menu);
    menu_add_submenu(settings_menu, "NETWORK", network_menu);
    menu_add_submenu(settings_menu, "SYSTEM", system_menu);
    menu_add_back(settings_menu);
    
    // Build Display submenu
    menu_add_value(display_menu, "BRIGHtNESS", &brightness, 0, 100, 5, on_brightness_change);
    menu_add_value(display_menu, "CONTRAST", &contrast, 50, 150, 10, on_contrast_change);
    menu_add_back(display_menu);
    
    // Build Network submenu
    menu_add_toggle(network_menu, "WIFI", &wifi_enabled, on_wifi_change);
    menu_add_toggle(network_menu, "BLUETOOTH", &bluetooth_enabled, on_bluetooth_change);
    menu_add_back(network_menu);
    
    // Build System submenu
    menu_add_value(system_menu, "VOLUME", &volume, 0, 100, 10, on_volume_change);
    menu_add_action(system_menu, "RESTART", action_restart);
    menu_add_action(system_menu, "FACTORY RESET", action_factory_reset);
    menu_add_back(system_menu);
    
    // Build main menu
    menu_add_submenu(main_menu, "SETTINGS", settings_menu);
    menu_add_action(main_menu, "ABOUT", action_about);
    
    // Set as root menu
    osd_menu_set_root(main_menu);
}

// Example main loop integration
int main(void) {
    stdio_init_all();
    
    // Initialize display and buttons
    display_error_t err = display_pack_init();
    if (err != DISPLAY_OK) {
        printf("Display init failed: %s\n", display_error_string(err));
        return 1;
    }
    
    err = buttons_init();
    if (err != DISPLAY_OK) {
        printf("Buttons init failed: %s\n", display_error_string(err));
        return 1;
    }
    
    // Initialize menu system
    osd_menu_init();
    setup_menus();
    
    // Clear screen
    display_clear(COLOR_BLACK);
    
    // Show some content
    display_draw_string(10, 10, "PRESS ANY BUTTON FOR MENU", COLOR_WHITE, COLOR_BLACK);
    display_draw_string(10, 25, "YOUR APPLICATION ..", COLOR_GREEN, COLOR_BLACK);
    
    printf("Menu system ready!\n");
    
    // Main loop
    bool menu_shown = false;
    while (true) {
        // Update buttons
        buttons_update();
        
        // Toggle menu with any button (first press)
        if (!menu_shown && (button_just_pressed(BUTTON_A) || 
                           button_just_pressed(BUTTON_B) ||
                           button_just_pressed(BUTTON_X) || 
                           button_just_pressed(BUTTON_Y))) {
            osd_menu_show();
            menu_shown = true;
        }
        
        // Update and render menu if visible
        if (osd_menu_is_visible()) {
            osd_menu_update();
            osd_menu_render();
        } else if (menu_shown) {
            // Menu was closed, redraw app content
            display_clear(COLOR_BLACK);
            display_draw_string(10, 10, "PRESS ANY BUTTON FOR MENU", COLOR_WHITE, COLOR_BLACK);
            display_draw_string(10, 25, "YOUR APPLICATION ..", COLOR_GREEN, COLOR_BLACK);
            menu_shown = false;
        }
        
        // Your application logic here
        // ...
        
        sleep_ms(10);
    }
    
    display_cleanup();
    return 0;
}
