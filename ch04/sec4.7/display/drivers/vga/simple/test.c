#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/pio.h"
#include "hardware/dma.h"
#include "hardware/clocks.h"
#include "hardware/irq.h"

// Pin definitions for simplified 3-bit VGA
#define RED_PIN     0
#define GREEN_PIN   1  
#define BLUE_PIN    2
#define HSYNC_PIN   3
#define VSYNC_PIN   4

// VGA timing constants (640x480 @ 60Hz)
#define H_ACTIVE    640
#define H_FRONT     16
#define H_SYNC      96
#define H_BACK      48
#define H_TOTAL     (H_ACTIVE + H_FRONT + H_SYNC + H_BACK)  // 800

#define V_ACTIVE    480
#define V_FRONT     10
#define V_SYNC      2
#define V_BACK      33
#define V_TOTAL     (V_ACTIVE + V_FRONT + V_SYNC + V_BACK)  // 525

#define PIXEL_CLOCK 25175000  // 25.175 MHz

// PIO programs
const uint16_t hsync_program[] = {
    //     .wrap_target
    0x80a0, //  0: pull   block           
    0xa027, //  1: mov    x, osr          
    0x0041, //  2: jmp    x--, 4          [1]
    0x001f, //  3: jmp    2               [31]
    0xe000, //  4: set    pins, 0         
    0xe01f, //  5: set    pins, 0         [31]
    0xe01f, //  6: set    pins, 0         [31]
    0xe000, //  7: set    pins, 0         
    0xe001, //  8: set    pins, 1         
    0xe01f, //  9: set    pins, 1         [31]
    0xe00c, // 10: set    pins, 1         [12]
    0xc000, // 11: irq    nowait 0        
    //     .wrap
};

const uint16_t vsync_program[] = {
    //     .wrap_target
    0x80a0, //  0: pull   block           
    0xa027, //  1: mov    x, osr          
    0x2040, //  2: wait   1 irq, 0        
    0x0042, //  3: jmp    x--, 2          
    0xa046, //  4: mov    y, isr          
    0x2041, //  5: wait   1 irq, 0 side 1 
    0x0085, //  6: jmp    y--, 5          
    0xe000, //  7: set    pins, 0         
    0x2040, //  8: wait   1 irq, 0        
    0x2040, //  9: wait   1 irq, 0        
    0xa04f, // 10: mov    y, !null        
    0xe001, // 11: set    pins, 1         
    0x2041, // 12: wait   1 irq, 0 side 1 
    0x008c, // 13: jmp    y--, 12         
    0xc001, // 14: irq    nowait 1        
    //     .wrap
};

const uint16_t rgb_program[] = {
    //     .wrap_target
    0x80a0, //  0: pull   block           
    0xa027, //  1: mov    x, osr          
    0xe000, //  2: set    pins, 0         
    0x2041, //  3: wait   1 irq, 1        
    0x80a0, //  4: pull   block           
    0xa027, //  5: mov    x, osr          
    0x6003, //  6: out    pins, 3         
    0x0046, //  7: jmp    x--, 6          
    //     .wrap
};

// Frame buffer for 640x480x3bit (1 pixel per byte for simplicity)
uint8_t framebuffer[H_ACTIVE * V_ACTIVE];

// DMA channels
int dma_channel;

void init_pio_vga() {
    PIO pio = pio0;
    
    // Add programs to PIO
    uint hsync_offset = pio_add_program(pio, (const pio_program_t*)hsync_program);
    uint vsync_offset = pio_add_program(pio, (const pio_program_t*)vsync_program);
    uint rgb_offset = pio_add_program(pio, (const pio_program_t*)rgb_program);
    
    // Configure HSYNC state machine (SM0)
    uint hsync_sm = 0;
    pio_sm_config hsync_config = pio_get_default_sm_config();
    sm_config_set_wrap(&hsync_config, hsync_offset, hsync_offset + 11);
    sm_config_set_set_pins(&hsync_config, HSYNC_PIN, 1);
    sm_config_set_clkdiv(&hsync_config, (float)clock_get_hz(clk_sys) / PIXEL_CLOCK);
    pio_gpio_init(pio, HSYNC_PIN);
    pio_sm_set_consecutive_pindirs(pio, hsync_sm, HSYNC_PIN, 1, true);
    pio_sm_init(pio, hsync_sm, hsync_offset, &hsync_config);
    
    // Configure VSYNC state machine (SM1)
    uint vsync_sm = 1;
    pio_sm_config vsync_config = pio_get_default_sm_config();
    sm_config_set_wrap(&vsync_config, vsync_offset, vsync_offset + 14);
    sm_config_set_set_pins(&vsync_config, VSYNC_PIN, 1);
    sm_config_set_sideset_pins(&vsync_config, VSYNC_PIN);
    pio_gpio_init(pio, VSYNC_PIN);
    pio_sm_set_consecutive_pindirs(pio, vsync_sm, VSYNC_PIN, 1, true);
    pio_sm_init(pio, vsync_sm, vsync_offset, &vsync_config);
    
    // Configure RGB state machine (SM2)
    uint rgb_sm = 2;
    pio_sm_config rgb_config = pio_get_default_sm_config();
    sm_config_set_wrap(&rgb_config, rgb_offset, rgb_offset + 7);
    sm_config_set_out_pins(&rgb_config, RED_PIN, 3);
    sm_config_set_set_pins(&rgb_config, RED_PIN, 3);
    sm_config_set_clkdiv(&rgb_config, (float)clock_get_hz(clk_sys) / (PIXEL_CLOCK * 5));
    
    // Initialize RGB pins
    for (int i = 0; i < 3; i++) {
        pio_gpio_init(pio, RED_PIN + i);
        pio_sm_set_consecutive_pindirs(pio, rgb_sm, RED_PIN + i, 1, true);
    }
    pio_sm_init(pio, rgb_sm, rgb_offset, &rgb_config);
    
    // Start the state machines
    pio_sm_set_enabled(pio, hsync_sm, true);
    pio_sm_set_enabled(pio, vsync_sm, true);
    pio_sm_set_enabled(pio, rgb_sm, true);
    
    // Push initial values
    pio_sm_put_blocking(pio, hsync_sm, H_ACTIVE + H_FRONT - 1);
    pio_sm_put_blocking(pio, vsync_sm, V_ACTIVE - 1);
}

void setup_dma() {
    dma_channel = dma_claim_unused_channel(true);
    
    dma_channel_config config = dma_channel_get_default_config(dma_channel);
    channel_config_set_transfer_data_size(&config, DMA_SIZE_8);
    channel_config_set_read_increment(&config, true);
    channel_config_set_write_increment(&config, false);
    channel_config_set_dreq(&config, pio_get_dreq(pio0, 2, true));
    
    dma_channel_configure(
        dma_channel,
        &config,
        &pio0->txf[2],      // Write to RGB PIO FIFO
        framebuffer,        // Read from framebuffer
        H_ACTIVE * V_ACTIVE,// Transfer count
        false               // Don't start yet
    );
}

void draw_test_pattern() {
    // Create a simple test pattern
    for (int y = 0; y < V_ACTIVE; y++) {
        for (int x = 0; x < H_ACTIVE; x++) {
            int pixel_index = y * H_ACTIVE + x;
            uint8_t color = 0;
            
            // Vertical color bars
            if (x < H_ACTIVE / 8) {
                color = 0;  // Black
            } else if (x < H_ACTIVE * 2 / 8) {
                color = 1;  // Red
            } else if (x < H_ACTIVE * 3 / 8) {
                color = 2;  // Green
            } else if (x < H_ACTIVE * 4 / 8) {
                color = 3;  // Yellow (Red + Green)
            } else if (x < H_ACTIVE * 5 / 8) {
                color = 4;  // Blue
            } else if (x < H_ACTIVE * 6 / 8) {
                color = 5;  // Magenta (Red + Blue)
            } else if (x < H_ACTIVE * 7 / 8) {
                color = 6;  // Cyan (Green + Blue)
            } else {
                color = 7;  // White
            }
            
            // Add some horizontal lines
            if (y % 60 == 0) {
                color = 7;  // White lines
            }
            
            framebuffer[pixel_index] = color;
        }
    }
}

void draw_moving_pattern() {
    static int frame_counter = 0;
    
    for (int y = 0; y < V_ACTIVE; y++) {
        for (int x = 0; x < H_ACTIVE; x++) {
            int pixel_index = y * H_ACTIVE + x;
            
            // Moving diagonal stripes
            int stripe = (x + y + frame_counter) / 40;
            uint8_t color = stripe & 7;  // Cycle through 8 colors
            
            framebuffer[pixel_index] = color;
        }
    }
    
    frame_counter++;
}

int main() {
    stdio_init_all();
    
    printf("Initializing VGA output...\n");
    
    // Initialize VGA
    init_pio_vga();
    setup_dma();
    
    // Draw initial test pattern
    draw_test_pattern();
    
    printf("VGA initialized. You should see color bars on your monitor.\n");
    printf("Press any key to switch to moving pattern...\n");
    
    // Start DMA transfer
    dma_channel_start(dma_channel);
    
    bool moving_pattern = false;
    
    while (true) {
        // Check for keyboard input to switch patterns
        int c = getchar_timeout_us(0);
        if (c != PICO_ERROR_TIMEOUT) {
            moving_pattern = !moving_pattern;
            printf("Switched to %s pattern\n", moving_pattern ? "moving" : "static");
        }
        
        if (moving_pattern) {
            // Wait for DMA completion before updating framebuffer
            dma_channel_wait_for_finish_blocking(dma_channel);
            
            draw_moving_pattern();
            
            // Restart DMA
            dma_channel_set_read_addr(dma_channel, framebuffer, true);
        }
        
        sleep_ms(16);  // ~60 FPS update rate
    }
    
    return 0;
}