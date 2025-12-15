#include <stdio.h>
#include "pico/stdlib.h"
#include "pico/time.h"
#include "display.h"
#include "game.h"

// Game state
static World world;
static bool game_running = true;
static uint32_t last_frame_time = 0;
static const float TARGET_FPS = 60.0f;
static const float FRAME_TIME_MS = 1000.0f / TARGET_FPS;

// Button callback for exiting (Button X)
void button_x_callback(button_t button) {
    if (button == BUTTON_X) {
        game_running = false;
    }
}

// Button callback for restart (when game over)
void button_restart_callback(button_t button) {
    if (world.game_over && button == BUTTON_Y) {
        // Clean up old world
        world_free(&world);
        
        // Reinit
        game_init(&world);
        
        printf("Game restarted!\n");
    }
}

int main() {
    // Init stdio for debug output
    stdio_init_all();
    sleep_ms(2000); // Give time for USB serial to connect
    
    printf("\n-+- Platform Game Starting -+-\n");
    
    // Initialize display
    display_error_t display_result = display_pack_init();
    if (display_result != DISPLAY_OK) {
        printf("ERROR: Display init failed: %s\n", 
               display_error_string(display_result));
        return 1;
    }
    printf("Display init successfull\n");
    
    // Initialize buttons
    display_error_t button_result = buttons_init();
    if (button_result != DISPLAY_OK) {
        printf("ERROR: Button init failed: %s\n",
               display_error_string(button_result));
        return 1;
    }
    printf("Buttons initiated\n");
    
    // Set up button callbacks
    button_set_callback(BUTTON_X, button_x_callback);
    
    // Initialize game world
    printf("Init game world ..\n");
    game_init(&world);
    printf("Game world created with player entity ID: %d\n", world.player_entity);
    
    // Show startup message
    display_clear(COLOR_BLACK);
    display_draw_string(DISPLAY_WIDTH/2 - 50, DISPLAY_HEIGHT/2 - 20, 
                       "PLATFORM GAME", COLOR_WHITE, COLOR_BLACK);
    display_draw_string(DISPLAY_WIDTH/2 - 60, DISPLAY_HEIGHT/2, 
                       "A/B: Move  Y: Jump", COLOR_YELLOW, COLOR_BLACK);
    display_draw_string(DISPLAY_WIDTH/2 - 40, DISPLAY_HEIGHT/2 + 20, 
                       "X: Exit", COLOR_RED, COLOR_BLACK);
    sleep_ms(2000);
    
    printf("Starting game loop ..\n");
    last_frame_time = to_ms_since_boot(get_absolute_time());
    
    // Main game loop
    uint32_t frame_count = 0;
    uint32_t fps_timer = last_frame_time;
    uint32_t fps = 0;
    
    while (game_running) {
        uint32_t current_time = to_ms_since_boot(get_absolute_time());
        uint32_t delta_time_ms = current_time - last_frame_time;
        
        // Cap frame time to prevent huge jumps (e.g., after breakpoint)
        if (delta_time_ms > 100) {
            delta_time_ms = 100;
        }
        
        // Only update if enough time has passed (frame limiting)
        if (delta_time_ms >= FRAME_TIME_MS) {
            float dt = delta_time_ms / 1000.0f; // Convert to seconds
            
            // Update button states
            buttons_update();
            
            // Update game world (all systems)
            world_update(&world, dt);
            
            // Check for restart when game over
            if (world.game_over) {
                button_set_callback(BUTTON_Y, button_restart_callback);
            }
            
            // FPS counter
            frame_count++;
            if (current_time - fps_timer >= 1000) {
                fps = frame_count;
                frame_count = 0;
                fps_timer = current_time;
                
                // Print debug info every second
                printf("FPS: %d | Score: %d | Entities alive: %d\n", 
                       fps, world.score, 
                       world.entity_components.size);
            }
            
            last_frame_time = current_time;
        } else {
            // Sleep a bit to not consume 100% CPU
            sleep_ms(1);
        }
        
        // Allow watchdog to be fed if configured
        tight_loop_contents();
    }
    
    // Cleanup
    printf("\n-= Shutting down =-\n");
    printf("Final score: %d\n", world.score);
    
    // Clean up game world
    world_free(&world);
    printf("Game world cleaned up\n");
    
    // Show exit message
    display_clear(COLOR_BLACK);
    display_draw_string(DISPLAY_WIDTH/2 - 30, DISPLAY_HEIGHT/2, 
                       "BYE!", COLOR_WHITE, COLOR_BLACK);
    sleep_ms(1000);
    
    // Clean up display
    display_cleanup();
    printf("Display cleaned up\n");
    
    printf("Game exited cleanly\n");
    return 0;
}
