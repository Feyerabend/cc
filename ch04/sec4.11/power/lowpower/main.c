#include "display.h"
#include "pico/stdlib.h"
#include "hardware/clocks.h"
#include "hardware/watchdog.h"
#include "hardware/xosc.h"
#include "hardware/pll.h"
#include "hardware/vreg.h"
#include "hardware/sync.h"

#include <stdio.h>


// Watchdog timeout (8 seconds) ~ safe for most power operations
// Getting too low risks unwanted resets during clock/voltage changes
#define WATCHDOG_TIMEOUT_MS 8000

// Power state tracking
static uint32_t wake_count = 0;

// Button pins for wake
#define BTN_A_PIN 12
#define BTN_B_PIN 13
#define BTN_X_PIN 14
#define BTN_Y_PIN 15

// Reset button on GPIO 22 (add external button between GPIO22 and GND)
#define RESET_BTN_PIN 22

static void setup_watchdog(void) {
    // Enable watchdog with 8 second timeout
    watchdog_enable(WATCHDOG_TIMEOUT_MS, true);
    printf("Watchdog enabled: %d ms timeout\n", WATCHDOG_TIMEOUT_MS);
}

static void feed_watchdog(void) {
    watchdog_update();
}

static void check_reset_button(void) {
    // If reset button pressed, trigger watchdog reset
    if (!gpio_get(RESET_BTN_PIN)) {
        printf("RESET BUTTON PRESSED - Triggering reset...\n");
        disp_clear(COLOR_BLACK);
        disp_draw_text(60, 100, "RESETTING...", COLOR_RED, COLOR_BLACK);
        sleep_ms(500);
        watchdog_reboot(0, 0, 0);
        while(1) tight_loop_contents();
    }
}

static void display_power_info(const char *state, uint32_t freq_khz, float voltage) {
    char buf[64];
    
    disp_clear(COLOR_BLACK);
    disp_draw_text(10, 20, "POWER STATE:", COLOR_CYAN, COLOR_BLACK);
    disp_draw_text(10, 40, state, COLOR_WHITE, COLOR_BLACK);
    
    snprintf(buf, sizeof(buf), "Clock: %lu kHz", (unsigned long)freq_khz);
    disp_draw_text(10, 70, buf, COLOR_YELLOW, COLOR_BLACK);
    
    snprintf(buf, sizeof(buf), "Voltage: %.2fV", voltage);
    disp_draw_text(10, 90, buf, COLOR_GREEN, COLOR_BLACK);
    
    feed_watchdog();
}

// Safe clock change with validation
static bool safe_clock_change(uint32_t freq_khz, enum vreg_voltage voltage) {
    printf("Attempting clock change to %lu kHz\n", (unsigned long)freq_khz);
    
    // Set voltage first (must be high enough for frequency)
    vreg_set_voltage(voltage);
    sleep_ms(10);
    feed_watchdog();
    
    // Try to change frequency with error handling
    bool success = set_sys_clock_khz(freq_khz, true);
    
    if (!success) {
        printf("WARNING: Clock change failed, restoring defaults\n");
        vreg_set_voltage(VREG_VOLTAGE_1_10);
        sleep_ms(10);
        set_sys_clock_khz(125000, true);
        return false;
    }
    
    // Re-init USB/UART after clock change
    stdio_init_all();
    feed_watchdog();
    
    printf("Clock changed successfully to %lu kHz\n", (unsigned long)freq_khz);
    return true;
}

// Demo 1: DVFS with safety checks
static void demo_dvfs(void) {
    printf("\n-- DVFS Demo --\n");
    
    typedef struct {
        uint32_t freq_khz;
        enum vreg_voltage voltage;
        const char *desc;
    } dvfs_config_t;
    
    dvfs_config_t configs[] = {
        {250000, VREG_VOLTAGE_1_20, "Max Performance"},
        {125000, VREG_VOLTAGE_1_10, "Normal (default)"},
        {48000,  VREG_VOLTAGE_0_95, "Low Power"},
        {24000,  VREG_VOLTAGE_0_90, "Ultra Low Power"}
    };
    
    for (int i = 0; i < 4; i++) {
        feed_watchdog();
        check_reset_button();
        
        printf("Setting %s: %lu kHz\n", configs[i].desc, 
               (unsigned long)configs[i].freq_khz);
        
        if (!safe_clock_change(configs[i].freq_khz, configs[i].voltage)) {
            disp_clear(COLOR_BLACK);
            disp_draw_text(10, 100, "Clock change failed!", COLOR_RED, COLOR_BLACK);
            sleep_ms(2000);
            break;
        }
        
        // Update display
        float voltage = 0.80f + (configs[i].voltage * 0.05f);
        display_power_info(configs[i].desc, configs[i].freq_khz, voltage);
        
        // Do some work to show the speed difference
        disp_draw_text(10, 120, "Performing work..", COLOR_RED, COLOR_BLACK);
        uint32_t start = time_us_32();
        
        volatile uint32_t dummy = 0;
        for (int j = 0; j < 100000; j++) {
            dummy += j;
            if (j % 10000 == 0) feed_watchdog();
        }
        
        uint32_t elapsed = time_us_32() - start;
        char buf[64];
        snprintf(buf, sizeof(buf), "Work time: %lu us", (unsigned long)elapsed);
        disp_draw_text(10, 140, buf, COLOR_WHITE, COLOR_BLACK);
        
        snprintf(buf, sizeof(buf), "Power saved: ~%d%%", 
                 (int)((1.0f - (float)configs[i].freq_khz / 250000.0f) * 100));
        disp_draw_text(10, 160, buf, COLOR_MAGENTA, COLOR_BLACK);
        
        for (int j = 0; j < 30; j++) {
            sleep_ms(100);
            feed_watchdog();
            check_reset_button();
        }
    }
    
    // Restore to normal
    safe_clock_change(125000, VREG_VOLTAGE_1_10);
    printf("DVFS demo complete - restored to 125MHz\n");
}

// Demo 2: WFI with timeout protection
static volatile bool button_wake = false;
static volatile uint32_t wfi_wake_count = 0;

static void button_irq_handler(uint gpio, uint32_t events) {
    button_wake = true;
    wfi_wake_count++;
}

static void demo_wfi(void) {
    printf("\n-- WFI (Wait for Interrupt) Demo --\n");
    
    disp_clear(COLOR_BLACK);
    disp_draw_text(10, 40, "WFI DEMO", COLOR_CYAN, COLOR_BLACK);
    disp_draw_text(10, 70, "CPU will idle using WFI", COLOR_YELLOW, COLOR_BLACK);
    disp_draw_text(10, 90, "Saves ~50%% power", COLOR_GREEN, COLOR_BLACK);
    disp_draw_text(10, 120, "Press Button A to wake", COLOR_WHITE, COLOR_BLACK);
    disp_draw_text(10, 140, "Auto-timeout: 10 sec", COLOR_CYAN, COLOR_BLACK);
    
    sleep_ms(2000);
    feed_watchdog();
    
    // Set up button interrupt with callback
    button_wake = false;
    wfi_wake_count = 0;
    gpio_set_irq_enabled_with_callback(BTN_A_PIN, GPIO_IRQ_EDGE_FALL, true, &button_irq_handler);
    
    printf("Entering WFI - CPU will idle until button press or timeout\n");
    
    disp_draw_text(10, 160, "CPU SLEEPING..", COLOR_RED, COLOR_BLACK);
    
    uint32_t wfi_count = 0;
    absolute_time_t start = get_absolute_time();
    absolute_time_t timeout = delayed_by_ms(start, 10000); // 10 second timeout
    
    // Keep entering WFI until button pressed or timeout
    while (!button_wake && !time_reached(timeout)) {
        __wfi();  // CPU sleeps here - saves power!
        wfi_count++;
        
        // Feed watchdog periodically (every ~100 WFI cycles)
        if (wfi_count % 100 == 0) {
            feed_watchdog();
        }
        
        check_reset_button();
    }
    
    uint32_t elapsed_ms = absolute_time_diff_us(start, get_absolute_time()) / 1000;
    
    // Disable interrupt
    gpio_set_irq_enabled(BTN_A_PIN, GPIO_IRQ_EDGE_FALL, false);
    
    feed_watchdog();
    
    char buf[64];
    if (button_wake) {
        disp_draw_text(10, 160, "WOKE BY BUTTON", COLOR_GREEN, COLOR_BLACK);
        printf("Woke from WFI by button press!\n");
    } else {
        disp_draw_text(10, 160, "TIMEOUT REACHED", COLOR_YELLOW, COLOR_BLACK);
        printf("WFI timeout reached\n");
    }
    
    snprintf(buf, sizeof(buf), "WFI cycles: %lu", (unsigned long)wfi_count);
    disp_draw_text(10, 180, buf, COLOR_GREEN, COLOR_BLACK);
    
    snprintf(buf, sizeof(buf), "Sleep time: %lu ms", (unsigned long)elapsed_ms);
    disp_draw_text(10, 200, buf, COLOR_GREEN, COLOR_BLACK);
    
    printf("WFI cycles: %lu, Time: %lu ms\n", 
           (unsigned long)wfi_count, (unsigned long)elapsed_ms);
    
    sleep_ms(3000);
    feed_watchdog();
}

// Demo 3: Peripheral power down with safety
static void demo_peripheral_power(void) {
    printf("\n=== Peripheral Power Demo ===\n");
    
    disp_clear(COLOR_BLACK);
    disp_draw_text(10, 40, "PERIPHERAL POWER", COLOR_CYAN, COLOR_BLACK);
    disp_draw_text(10, 70, "Disabling unused clocks", COLOR_YELLOW, COLOR_BLACK);
    
    const char *peripherals[] = {
        "ADC - Analog to Digital",
        "RTC - Real Time Clock",
        "USB - (if not used)"
    };
    
    for (int i = 0; i < 3; i++) {
        char buf[64];
        snprintf(buf, sizeof(buf), "%s", peripherals[i]);
        disp_draw_text(10, 100 + i * 20, buf, COLOR_WHITE, COLOR_BLACK);
    }
    
    sleep_ms(2000);
    feed_watchdog();
    
    disp_draw_text(10, 180, "Disabling..", COLOR_RED, COLOR_BLACK);
    
    // Disable ADC clock (safe - we're not using it)
    clock_stop(clk_adc);
    printf("Disabled ADC clock\n");
    
    sleep_ms(1000);
    feed_watchdog();
    
    disp_draw_text(10, 180, "ADC clock stopped", COLOR_GREEN, COLOR_BLACK);
    disp_draw_text(10, 200, "Saves ~0.5-1mA", COLOR_MAGENTA, COLOR_BLACK);
    
    sleep_ms(3000);
    feed_watchdog();
    
    // Re-enable
    disp_draw_text(10, 180, "Re-enabling ADC..", COLOR_YELLOW, COLOR_BLACK);
    clock_configure(clk_adc,
                    0,
                    CLOCKS_CLK_ADC_CTRL_AUXSRC_VALUE_CLKSRC_PLL_USB,
                    48 * MHZ,
                    48 * MHZ);
    
    printf("Re-enabled ADC clock\n");
    sleep_ms(2000);
    feed_watchdog();
}

// Demo 4: Duty cycle with watchdog feeding
static void demo_duty_cycle(void) {
    printf("\n-- Duty Cycle Demo --\n");
    
    disp_clear(COLOR_BLACK);
    disp_draw_text(10, 40, "DUTY CYCLE DEMO", COLOR_CYAN, COLOR_BLACK);
    disp_draw_text(10, 70, "Active 10%, Sleep 90%", COLOR_YELLOW, COLOR_BLACK);
    disp_draw_text(10, 100, "Common for sensors", COLOR_WHITE, COLOR_BLACK);
    
    sleep_ms(2000);
    feed_watchdog();
    
    for (int cycle = 0; cycle < 5; cycle++) {
        char buf[64];
        
        feed_watchdog();
        check_reset_button();
        
        // Active phase (100ms)
        disp_clear(COLOR_BLACK);
        snprintf(buf, sizeof(buf), "ACTIVE - Cycle %d/5", cycle + 1);
        disp_draw_text(10, 100, buf, COLOR_GREEN, COLOR_BLACK);
        disp_draw_text(10, 120, "Reading sensors..", COLOR_YELLOW, COLOR_BLACK);
        
        printf("Cycle %d: ACTIVE\n", cycle + 1);
        
        // Simulate sensor reading
        volatile uint32_t dummy = 0;
        for (int i = 0; i < 50000; i++) {
            dummy += i;
        }
        
        sleep_ms(100);
        
        // Sleep phase (900ms)
        disp_clear(COLOR_BLACK);
        snprintf(buf, sizeof(buf), "SLEEPING - Cycle %d/5", cycle + 1);
        disp_draw_text(10, 100, buf, COLOR_RED, COLOR_BLACK);
        disp_draw_text(10, 120, "Power saving mode..", COLOR_MAGENTA, COLOR_BLACK);
        
        printf("Cycle %d: SLEEP (900ms)\n", cycle + 1);
        
        // Sleep in chunks to feed watchdog
        for (int i = 0; i < 9; i++) {
            sleep_ms(100);
            feed_watchdog();
            check_reset_button();
        }
    }
    
    disp_clear(COLOR_BLACK);
    disp_draw_text(10, 100, "Duty cycle complete!", COLOR_GREEN, COLOR_BLACK);
    disp_draw_text(10, 120, "Avg power: ~10% of full", COLOR_YELLOW, COLOR_BLACK);
    
    printf("Duty cycle demo complete\n");
    sleep_ms(3000);
    feed_watchdog();
}

// Demo 5: Combined with extra safety
static void demo_combined(void) {
    printf("\n-- Combined Power Saving Demo --\n");
    
    disp_clear(COLOR_BLACK);
    disp_draw_text(10, 30, "COMBINED STRATEGY", COLOR_CYAN, COLOR_BLACK);
    disp_draw_text(10, 60, "1. Lower frequency", COLOR_YELLOW, COLOR_BLACK);
    disp_draw_text(10, 80, "2. Lower voltage", COLOR_YELLOW, COLOR_BLACK);
    disp_draw_text(10, 100, "3. Disable peripherals", COLOR_YELLOW, COLOR_BLACK);
    disp_draw_text(10, 120, "4. Use WFI for idle", COLOR_YELLOW, COLOR_BLACK);
    
    sleep_ms(3000);
    feed_watchdog();
    
    // Step 1: Lower frequency and voltage
    disp_clear(COLOR_BLACK);
    disp_draw_text(10, 80, "Setting low power mode..", COLOR_YELLOW, COLOR_BLACK);
    
    if (!safe_clock_change(48000, VREG_VOLTAGE_0_95)) {
        disp_draw_text(10, 100, "Failed! Aborting..", COLOR_RED, COLOR_BLACK);
        sleep_ms(2000);
        return;
    }
    
    printf("Switched to 48MHz @ 0.95V\n");
    
    display_power_info("Low Power Mode", 48000, 0.95f);
    disp_draw_text(10, 120, "Power: ~30% of max", COLOR_GREEN, COLOR_BLACK);
    
    sleep_ms(2000);
    feed_watchdog();
    
    // Step 2: Disable ADC
    disp_draw_text(10, 140, "Disabling ADC..", COLOR_YELLOW, COLOR_BLACK);
    clock_stop(clk_adc);
    sleep_ms(1000);
    feed_watchdog();
    
    disp_draw_text(10, 140, "ADC disabled", COLOR_GREEN, COLOR_BLACK);
    disp_draw_text(10, 160, "Power: ~28% of max", COLOR_GREEN, COLOR_BLACK);
    
    sleep_ms(2000);
    feed_watchdog();
    
    // Step 3: Use WFI with timeout
    disp_draw_text(10, 180, "Using WFI for 3 seconds..", COLOR_YELLOW, COLOR_BLACK);
    
    for (int i = 0; i < 30; i++) {
        __wfi();
        sleep_ms(100);
        if (i % 5 == 0) feed_watchdog();
        check_reset_button();
    }
    
    disp_draw_text(10, 180, "WFI complete", COLOR_GREEN, COLOR_BLACK);
    disp_draw_text(10, 200, "Power: ~15% of max!", COLOR_GREEN, COLOR_BLACK);
    
    printf("Combined strategy achieved ~85%% power reduction\n");
    
    sleep_ms(4000);
    feed_watchdog();
    
    // Restore
    disp_clear(COLOR_BLACK);
    disp_draw_text(10, 100, "Restoring normal mode..", COLOR_YELLOW, COLOR_BLACK);
    
    clock_configure(clk_adc, 0, CLOCKS_CLK_ADC_CTRL_AUXSRC_VALUE_CLKSRC_PLL_USB,
                    48 * MHZ, 48 * MHZ);
    
    safe_clock_change(125000, VREG_VOLTAGE_1_10);
    
    disp_draw_text(10, 120, "Restored to normal", COLOR_GREEN, COLOR_BLACK);
    
    printf("Restored to 125MHz @ 1.10V\n");
    sleep_ms(2000);
    feed_watchdog();
}

// Safe button wait with watchdog
static void wait_for_button(void) {
    disp_draw_text(10, 220, "Press any button..", COLOR_CYAN, COLOR_BLACK);
    
    // Wait for release first
    while (button_pressed(BUTTON_A) || button_pressed(BUTTON_B) ||
           button_pressed(BUTTON_X) || button_pressed(BUTTON_Y)) {
        buttons_update();
        sleep_ms(10);
        feed_watchdog();
        check_reset_button();
    }
    
    // Wait for press
    while (true) {
        buttons_update();
        feed_watchdog();
        check_reset_button();
        
        if (button_just_pressed(BUTTON_A) || button_just_pressed(BUTTON_B) ||
            button_just_pressed(BUTTON_X) || button_just_pressed(BUTTON_Y)) {
            break;
        }
        sleep_ms(10);
    }
}

int main() {
    // Check if this was a watchdog reset
    bool watchdog_reset = watchdog_caused_reboot();
    
    stdio_init_all();
    sleep_ms(2000);
    
    printf("\n  Raspberry Pi Pico Power Management Demo\n");
    printf("    (With Watchdog Protection)\n\n");
    
    if (watchdog_reset) {
        printf("\n*** RECOVERED FROM WATCHDOG RESET ***\n\n");
    }
    
    // Setup reset button (external button on GPIO22)
    gpio_init(RESET_BTN_PIN);
    gpio_set_dir(RESET_BTN_PIN, GPIO_IN);
    gpio_pull_up(RESET_BTN_PIN);
    printf("Reset button on GPIO %d (press to reset)\n", RESET_BTN_PIN);
    
    // Enable watchdog
    setup_watchdog();
    
    // Init display
    disp_config_t cfg = disp_get_default_config();
    cfg.use_dma = true;
    cfg.spi_baudrate = 31250000;
    
    disp_error_t err = disp_init(&cfg);
    if (err != DISP_OK) {
        printf("Display init failed: %s\n", disp_error_string(err));
        return 1;
    }
    
    buttons_init();
    feed_watchdog();
    
    // Show intro
    disp_clear(COLOR_BLACK);
    
    if (watchdog_reset) {
        disp_draw_text(30, 60, "RECOVERED FROM HALT", COLOR_RED, COLOR_BLACK);
        disp_draw_text(40, 80, "System was reset!", COLOR_YELLOW, COLOR_BLACK);
        sleep_ms(3000);
        feed_watchdog();
    }
    
    disp_clear(COLOR_BLACK);
    disp_draw_text(40, 80, "POWER MANAGEMENT", COLOR_CYAN, COLOR_BLACK);
    disp_draw_text(90, 110, "DEMO", COLOR_CYAN, COLOR_BLACK);
    disp_draw_text(10, 150, "With Watchdog Protection", COLOR_YELLOW, COLOR_BLACK);
    disp_draw_text(10, 170, "Reset: GPIO22 to GND", COLOR_GREEN, COLOR_BLACK);
    sleep_ms(3000);
    feed_watchdog();
    
    while (true) {
        feed_watchdog();
        check_reset_button();
        
        // Main menu
        disp_clear(COLOR_BLACK);
        disp_draw_text(50, 10, "POWER DEMO MENU", COLOR_WHITE, COLOR_BLACK);
        disp_draw_text(10, 50, "A: DVFS (Voltage/Freq)", COLOR_GREEN, COLOR_BLACK);
        disp_draw_text(10, 75, "B: WFI Idle Mode", COLOR_YELLOW, COLOR_BLACK);
        disp_draw_text(10, 100, "X: Peripheral Power", COLOR_CYAN, COLOR_BLACK);
        disp_draw_text(10, 125, "Y: Duty Cycle Demo", COLOR_MAGENTA, COLOR_BLACK);
        
        disp_draw_text(10, 165, "Hold both A+B:", COLOR_WHITE, COLOR_BLACK);
        disp_draw_text(10, 185, "  Combined Strategy", COLOR_GREEN, COLOR_BLACK);
        
        disp_draw_text(10, 215, "Reset: GPIO22->GND", COLOR_RED, COLOR_BLACK);
        
        printf("\nSelect demo: A/B/X/Y or A+B for combined\n");
        
        // Wait for selection
        while (true) {
            buttons_update();
            feed_watchdog();
            check_reset_button();
            
            // Check for combined (A+B)
            if (button_pressed(BUTTON_A) && button_pressed(BUTTON_B)) {
                sleep_ms(200);
                demo_combined();
                break;
            }
            else if (button_just_pressed(BUTTON_A)) {
                demo_dvfs();
                break;
            } else if (button_just_pressed(BUTTON_B)) {
                demo_wfi();
                break;
            } else if (button_just_pressed(BUTTON_X)) {
                demo_peripheral_power();
                break;
            } else if (button_just_pressed(BUTTON_Y)) {
                demo_duty_cycle();
                break;
            }
            
            sleep_ms(10);
        }
        
        wait_for_button();
    }
    
    disp_deinit();
    return 0;
}
