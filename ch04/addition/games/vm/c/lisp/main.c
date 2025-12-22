#include <stdio.h>
#include "pico/stdlib.h"
#include "display.h"
#include "lisp_vm.h"

// Example game code as a string
static const char GAME_CODE[] = 
";; Sprite-based Space Shooter\n"
"(define player-x 150)\n"
"(define player-y 200)\n"
"(define enemy-x 100)\n"
"(define enemy-y 50)\n"
"(define enemy-dx 2)\n"
"(define score 0)\n"
"\n"
";; Create player sprite (8x8 ship)\n"
"(define player-sprite (make-sprite 8 8))\n"
"(sprite-set-pixel player-sprite 3 0 0x07E0)\n"
"(sprite-set-pixel player-sprite 4 0 0x07E0)\n"
"(sprite-set-pixel player-sprite 2 1 0x07E0)\n"
"(sprite-set-pixel player-sprite 3 1 0x07E0)\n"
"(sprite-set-pixel player-sprite 4 1 0x07E0)\n"
"(sprite-set-pixel player-sprite 5 1 0x07E0)\n"
"(sprite-set-pixel player-sprite 1 2 0x07E0)\n"
"(sprite-set-pixel player-sprite 2 2 0x07E0)\n"
"(sprite-set-pixel player-sprite 5 2 0x07E0)\n"
"(sprite-set-pixel player-sprite 6 2 0x07E0)\n"
"\n"
";; Create enemy sprite (8x8)\n"
"(define enemy-sprite (make-sprite 8 8))\n"
"(sprite-set-pixel enemy-sprite 1 1 0xF800)\n"
"(sprite-set-pixel enemy-sprite 6 1 0xF800)\n"
"(sprite-set-pixel enemy-sprite 2 2 0xF800)\n"
"(sprite-set-pixel enemy-sprite 5 2 0xF800)\n"
"(sprite-set-pixel enemy-sprite 3 3 0xF800)\n"
"(sprite-set-pixel enemy-sprite 4 3 0xF800)\n"
"\n"
";; Button handlers\n"
"(on-button-x (lambda ()\n"
"  (set! player-x (- player-x 4))\n"
"  (if (< player-x 0) (set! player-x 0))))\n"
"\n"
"(on-button-y (lambda ()\n"
"  (set! player-x (+ player-x 4))\n"
"  (if (> player-x 312) (set! player-x 312))))\n"
"\n"
";; Game update\n"
"(on-update (lambda ()\n"
"  ;; Move enemy\n"
"  (set! enemy-x (+ enemy-x enemy-dx))\n"
"  (if (or (< enemy-x 0) (> enemy-x 312))\n"
"    (set! enemy-dx (- 0 enemy-dx)))\n"
"  \n"
"  ;; Check collision\n"
"  (if (collide? player-x player-y 8 8 enemy-x enemy-y 8 8)\n"
"    (begin\n"
"      (set! score (+ score 1))\n"
"      (set! enemy-y 50)\n"
"      (set! enemy-x 100)))\n"
"  \n"
"  ;; Draw everything\n"
"  (clear 0x0000)\n"
"  (draw-sprite player-sprite player-x player-y)\n"
"  (draw-sprite enemy-sprite enemy-x enemy-y)\n"
"  (draw-text 10 10 \"Score:\" 0xFFFF 0x0000)\n"
"  (draw-text 60 10 (number->string score) 0xFFE0 0x0000)))\n"
"\n"
"(start)\n";

int main() {
    // Initialize stdio for debug output
    stdio_init_all();
    sleep_ms(2000);  // Wait for USB connection
    
    printf("\n=== PicoLisp Game System ===\n");
    
    // Initialize display
    disp_config_t disp_cfg = disp_get_default_config();
    disp_error_t err = disp_init(&disp_cfg);
    if (err != DISP_OK) {
        printf("Display init failed: %s\n", disp_error_string(err));
        return 1;
    }
    
    // Allocate framebuffer for smooth rendering
    err = disp_framebuffer_alloc();
    if (err != DISP_OK) {
        printf("Framebuffer alloc failed: %s\n", disp_error_string(err));
        return 1;
    }
    
    // Initialize buttons
    err = buttons_init();
    if (err != DISP_OK) {
        printf("Button init failed: %s\n", disp_error_string(err));
        return 1;
    }
    
    // Clear screen
    disp_framebuffer_clear(COLOR_BLACK);
    disp_framebuffer_draw_text(50, 100, "PicoLisp Loading...", COLOR_GREEN, COLOR_BLACK);
    disp_framebuffer_flush();
    
    // Initialize Lisp VM
    lisp_vm_t vm;
    lisp_init(&vm);
    
    printf("VM initialized, parsing code...\n");
    
    // Parse and run game code
    const char *code_ptr = GAME_CODE;
    while (*code_ptr) {
        lisp_value_t *expr = lisp_parse(&vm, &code_ptr);
        if (!expr) break;
        
        lisp_value_t *result = lisp_eval(&vm, expr, vm.global_env);
        if (vm.error_msg) {
            printf("Error: %s\n", vm.error_msg);
            disp_framebuffer_clear(COLOR_BLACK);
            disp_framebuffer_draw_text(10, 100, "Lisp Error!", COLOR_RED, COLOR_BLACK);
            disp_framebuffer_draw_text(10, 120, vm.error_msg, COLOR_RED, COLOR_BLACK);
            disp_framebuffer_flush();
            while (1) tight_loop_contents();
        }
    }
    
    printf("Game code loaded successfully!\n");
    printf("Memory used: %zu / %d cells\n", vm.heap_used, LISP_HEAP_SIZE);
    
    // Main game loop
    uint32_t last_update = to_ms_since_boot(get_absolute_time());
    uint32_t frame_count = 0;
    uint32_t fps_update = last_update;
    
    while (vm.running) {
        uint32_t now = to_ms_since_boot(get_absolute_time());
        
        // Target 60 FPS (16.67ms per frame)
        if (now - last_update >= 16) {
            last_update = now;
            
            // Update game logic
            lisp_update(&vm);
            
            frame_count++;
            
            // Print FPS every second
            if (now - fps_update >= 1000) {
                printf("FPS: %lu, Heap: %zu cells\n", frame_count, vm.heap_used);
                frame_count = 0;
                fps_update = now;
            }
        }
        
        // Small sleep to prevent CPU overheating
        sleep_us(100);
    }
    
    // Cleanup
    disp_framebuffer_clear(COLOR_BLACK);
    disp_framebuffer_draw_text(100, 120, "Game Over!", COLOR_YELLOW, COLOR_BLACK);
    disp_framebuffer_flush();
    
    lisp_deinit(&vm);
    disp_deinit();
    
    printf("Game exited cleanly\n");
    return 0;
}

// Alternative: Load game from SD card or embedded file
/*
#include "game_script.h"  // Contains: const char GAME_SCRIPT[] = "...";

void load_game_from_file(lisp_vm_t *vm) {
    const char *ptr = GAME_SCRIPT;
    while (*ptr) {
        lisp_value_t *expr = lisp_parse(vm, &ptr);
        if (expr) lisp_eval(vm, expr, vm->global_env);
    }
}
*/

// Helper: Create sprite from bitmap data
/*
void create_sprite_from_bitmap(lisp_vm_t *vm, const char *name, 
                               uint8_t w, uint8_t h, const uint16_t *data) {
    lisp_sprite_t *sprite = lisp_create_sprite(vm, w, h, data);
    lisp_value_t *sprite_val = lisp_alloc(vm, LISP_SPRITE);
    sprite_val->as.sprite = sprite;
    
    lisp_value_t *sym = lisp_symbol(vm, name);
    lisp_env_define(vm, vm->global_env, sym, sprite_val);
}
*/