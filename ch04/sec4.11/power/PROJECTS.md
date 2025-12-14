
### Project 1: Battery-Powered Weather Station

*What You'll Build:*
A temperature and humidity monitor that runs on batteries
for weeks, updating readings every 10 minutes.

*What You'll Learn:*
- DVFS (running at lower frequency during sampling)
- Duty cycle management (active only 0.03% of the time)
- Real battery life optimisation

*Hardware You'll Need:*
- Raspberry Pi Pico
- DHT22 or BME280 sensor (temperature/humidity)
- Display (optional - LCD or the Pimoroni Display Pack)
- 3× AA batteries (2000mAh) or LiPo battery

*Your Implementation:*
```c
void weather_station(void) {
    // Init your sensor and display here
    
    while (true) {
        // Active phase: Speed up for sensor reading
        set_sys_clock_khz(48000, true);
        stdio_init_all();  // Re-init after clock change
        
        // Read your sensors
        float temp = read_temperature();
        float humidity = read_humidity();
        
        // Display or transmit data
        display_update(temp, humidity);
        // or: transmit_data(temp, humidity);
        
        printf("Temp: %.1fC, Humidity: %.1f%%\n", temp, humidity);
        
        // Sleep phase: 9 minutes 59.8 seconds
        sleep_ms(599800);  // 10 minute interval
    }
}
```

*Your Challenge:*
1. Implement the basic loop above
2. Measure actual power consumption with a multimeter
3. Calculate your battery life: `Battery_mAh / Average_Current_mA = Hours`
4. *Bonus*: Add a button to manually trigger an immediate reading
5. *Advanced*: Store readings in EEPROM and display min/max values

*Expected Results:*
- Average power: ~1.5mA
- Battery life with 2000mAh: ~55 days
- Active time: ~200ms every 10 minutes



### Project 2: Motion-Activated Information Display

*What You'll Build:*
A display that sleeps in ultra-low-power mode and wakes up when you
walk by, showing information for 30 seconds before sleeping again.

*What You'll Learn:*
- GPIO interrupt-based wake
- Deep sleep modes (dormant)
- Clock restoration after wake
- Event-driven power management

*Hardware You'll Need:*
- Raspberry Pi Pico
- PIR motion sensor (HC-SR501 or similar)
- Pimoroni Display Pack or LCD
- 3× AA batteries or LiPo

*Your Implementation:*
```c
void motion_display(void) {
    // Init display and PIR sensor
    #define PIR_PIN 10  // Your motion sensor pin
    
    gpio_init(PIR_PIN);
    gpio_set_dir(PIR_PIN, GPIO_IN);
    
    while (true) {
        printf("Going to sleep.. waiting for motion\n");
        sleep_ms(100);
        
        // Enter dormant mode - ultra low power!
        gpio_set_dormant_irq_enabled(PIR_PIN, GPIO_IRQ_EDGE_RISE, true);
        sleep_run_from_dormant_source(DORMANT_SOURCE_XOSC);
        
        // You just woke up from motion detection!
        
        // Restore system clocks after dormant mode
        rosc_write(&rosc_hw->ctrl, ROSC_CTRL_ENABLE_BITS);
        set_sys_clock_khz(125000, true);
        stdio_init_all();
        
        printf("Motion detected! Waking up..\n");
        
        // Turn on display and show information
        disp_set_backlight(true);
        disp_clear(COLOR_BLACK);
        disp_draw_text(20, 60, "MOTION DETECTED!", COLOR_GREEN, COLOR_BLACK);
        disp_draw_text(20, 100, "Hello! Welcome!", COLOR_YELLOW, COLOR_BLACK);
        
        // Display your information here
        display_show_info();
        
        // Stay active for 30 seconds
        sleep_ms(30000);
        
        // Turn off display before sleeping
        disp_set_backlight(false);
    }
}
```

*Your Challenge:*
1. Get the basic motion detection working
2. Display custom information when triggered (time, temperature, messages)
3. Measure power in dormant mode vs. active mode
4. *Bonus*: Add multiple "screens" that cycle every 5 seconds while active
5. *Advanced*: Add a light sensor - only activate display if it's dark

*Expected Results:*
- Dormant power: ~1.3mA
- Active power: ~30mA (with display)
- Battery life: Months (depends on activation frequency)
- Wake time: ~10ms from dormant



### Project 3: Environmental Data Logger

*What You'll Build:*
A system that logs temperature, humidity, and light levels to an SD card
every minute, optimised for long-term battery operation.

*What You'll Learn:*
- Combining DVFS with duty cycling
- SD card burst writing
- Multi-sensor management
- Long-term data collection strategies

*Hardware You'll Need:*
- Raspberry Pi Pico
- SD card module (SPI)
- BME280 (temperature/humidity) or DHT22
- Light sensor (LDR or BH1750)
- LiPo battery (2000mAh+)

*Your Implementation:*
```c
#include "ff.h"  // FatFS for SD card
                // or checkout the SD card
                // solution under storage

void data_logger(void) {
    FATFS fs;
    FIL file;
    
    // Mount SD card
    f_mount(&fs, "", 1);
    
    uint32_t sample_count = 0;
    
    while (true) {
        // Active phase: Speed up for SD card operations
        set_sys_clock_khz(125000, true);
        stdio_init_all();
        
        // Read all your sensors
        float temp = read_temperature();
        float humidity = read_humidity();
        uint16_t light = read_light_level();
        
        printf("Sample %lu: %.1fC, %.1f%%, Light: %u\n", 
               sample_count++, temp, humidity, light);
        
        // Open file, append data, close immediately
        if (f_open(&file, "datalog.csv", FA_OPEN_APPEND | FA_WRITE) == FR_OK) {
            char buffer[64];
            snprintf(buffer, sizeof(buffer), "%lu,%.1f,%.1f,%u\n",
                     sample_count, temp, humidity, light);
            
            UINT bytes_written;
            f_write(&file, buffer, strlen(buffer), &bytes_written);
            f_close(&file);
        }
        
        // Sleep phase: Lower frequency for minimal power
        set_sys_clock_khz(24000, true);  // Very low power during sleep
        sleep_ms(60000);  // 1 minute interval
    }
}
```

*Your Challenge:*
1. Implement basic sensor reading and SD card logging
2. Add timestamps (use the Pico's timer or RTC)
3. Measure power consumption during active vs. sleep phases
4. Calculate how long your battery will last
5. *Bonus*: Add a "burst mode" button - sample every second for 1 minute
6. *Advanced*: Implement data averaging - only log if value changed significantly

*Expected Results:*
- Active power (SD write): ~40-50mA for ~500ms
- Sleep power: ~2-3mA
- Average power: ~2-3mA
- Battery life with 2000mAh: 30-40 days
- Data points: 43,200 readings per month

*Data Analysis Extension:*
After collecting data for a few days:
1. Remove SD card and analyze data in Excel/Python
2. Plot temperature/humidity trends
3. Find daily patterns (temperature cycles, light patterns)
4. Calculate statistics (min, max, average, standard deviation)



### Project 4: Smart Power Switch (Combined Techniques)

*What You'll Build:*
An intelligent power switch that monitors button presses and controls a
relay, using all power-saving techniques you've learned.

*What You'll Learn:*
- Combining WFI, DVFS, and peripheral management
- Interrupt-driven architecture
- State machine design
- Real-world device control

*Hardware You'll Need:*
- Raspberry Pi Pico
- Relay module (5V or 3.3V)
- Push button
- LED indicator
- Optional: Current sensor (INA219)

*Your Implementation:*
```c
typedef enum {
    STATE_OFF,
    STATE_ON,
    STATE_TIMER
} power_state_t;

void smart_power_switch(void) {
    #define RELAY_PIN 15
    #define BUTTON_PIN 12
    #define LED_PIN 13
    
    power_state_t state = STATE_OFF;
    uint32_t timer_remaining = 0;
    
    // Initialize hardware
    gpio_init(RELAY_PIN);
    gpio_set_dir(RELAY_PIN, GPIO_OUT);
    gpio_put(RELAY_PIN, 0);
    
    gpio_init(LED_PIN);
    gpio_set_dir(LED_PIN, GPIO_OUT);
    
    buttons_init();
    
    // Lower frequency - we don't need speed for this
    vreg_set_voltage(VREG_VOLTAGE_0_95);
    sleep_ms(10);
    set_sys_clock_khz(48000, true);
    stdio_init_all();
    
    // Disable unused peripherals
    clock_stop(clk_adc);
    
    printf("Smart Power Switch Ready\n");
    
    while (true) {
        buttons_update();
        
        // Button A: Toggle on/off
        if (button_just_pressed(BUTTON_A)) {
            if (state == STATE_OFF) {
                state = STATE_ON;
                gpio_put(RELAY_PIN, 1);
                gpio_put(LED_PIN, 1);
                printf("POWER ON\n");
            } else {
                state = STATE_OFF;
                gpio_put(RELAY_PIN, 0);
                gpio_put(LED_PIN, 0);
                timer_remaining = 0;
                printf("POWER OFF\n");
            }
        }
        
        // Button B: Timer mode (30 minute countdown)
        if (button_just_pressed(BUTTON_B)) {
            state = STATE_TIMER;
            timer_remaining = 30 * 60;  // 30 minutes in seconds
            gpio_put(RELAY_PIN, 1);
            gpio_put(LED_PIN, 1);
            printf("TIMER MODE: 30 minutes\n");
        }
        
        // Handle timer countdown
        if (state == STATE_TIMER && timer_remaining > 0) {
            timer_remaining--;
            
            if (timer_remaining == 0) {
                state = STATE_OFF;
                gpio_put(RELAY_PIN, 0);
                gpio_put(LED_PIN, 0);
                printf("TIMER EXPIRED - Power Off\n");
            }
            
            // Show remaining time every minute
            if (timer_remaining % 60 == 0) {
                printf("Time remaining: %lu minutes\n", timer_remaining / 60);
            }
        }
        
        // Idle efficiently between checks
        __wfi();
        sleep_ms(1000);  // Check every second
    }
}
```

*Your Challenge:*
1. Build the basic on/off switch functionality
2. Add the timer mode
3. Measure power consumption in each state
4. *Bonus*: Add a display showing current state and timer countdown
5. *Advanced*: Add current sensing to monitor power usage of connected device
6. *Expert*: Implement multiple timer presets (5, 15, 30, 60 minutes)

*Expected Results:*
- Idle power: ~5-8mA (with low frequency)
- Response time: Instant (WFI wakes on button press)
- Battery life: Weeks to months depending on relay usage



### Learning ..

*Week 1: Basics*
- Complete the power demo from earlier
- Understand DVFS and WFI
- Measure power consumption

*Week 2: Project 1*
- Build the weather station
- Learn duty cycle management
- Calculate battery life

*Week 3: Project 2*
- Build motion-activated display
- Master interrupt-driven wake
- Understand dormant mode

*Week 4: Project 3*
- Build data logger
- Combine multiple techniques
- Analyze collected data

*Week 5: Project 4*
- Build smart power switch
- Create real-world product
- Optimize for production



### Tips

Debugging Low-Power Code:
1. *Add printf statements* before entering sleep modes
2. *Use LED indicators* to show state visually
3. *Test with USB power first*, measure with battery later
4. *Keep a log* of power measurements and changes

Common Mistakes to Avoid:
1. *Don't disable clocks you're using* (e.g., SPI while
   using a display)
2. *Always re-init peripherals* after clock changes
3. *Add delays after voltage changes* (10ms minimum)
4. *Test wake conditions* before entering deep sleep

Making It Production-Ready:
1. Add error handling (SD card failures, sensor errors)
2. Implement watchdog timer for crashes
3. Add low-battery detection and warning
4. Create a proper enclosure
5. Document your power budget



### Stretch Goals

Once you've completed the basic projects, try these more advanced challenges:

1. *Solar-Powered Weather Station*: Add a solar panel and battery management
2. *Wireless Data Logger*: Add WiFi/LoRa for remote data transmission
3. *Multi-Sensor Network*: Multiple Picos communicating via radio
4. *Smart Home Controller*: Expand the power switch to control multiple devices
5. *Wildlife Camera*: Motion-triggered camera with image storage



### Power Measurement Tips

Measuring Current Draw:
1. *Ammeter in series*: Connect between battery and VIN
2. *Multimeter*: Set to mA range, measure supply current
3. *Power profiler*: Use Nordic PPK2 or similar for detailed analysis

What to Measure:
- Baseline (idle)
- Active (full speed)
- Sleep modes
- Peak current (during WiFi transmission, etc.)

Common Issues:
- *Higher than expected?* Check for:
  - Unused peripherals still enabled
  - LEDs still on
  - Pull-up/pull-down resistors on unused pins
  - External components drawing power

