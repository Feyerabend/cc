
## Raspberry Pi Pico Power Management

The Raspberry Pi Pico (RP2040) is designed for embedded applications where
power efficiency is essential. Effective power management can extend battery
life from days to months, or even years, depending on the use case.

You may have owned mobile phones where each new generation offers longer use
between charges. This improvement is not solely the result of better batteries
or advances in chemistry; it is also due to more efficient software and smarter
energy management. The same principles can be applied in embedded systems to
achieve comparable reductions in power consumption.

Raspberry Pi Pico: typical power consumption:
- Full speed (125MHz): ~25-40mA
- Low power mode (48MHz): ~8-15mA
- Sleep with WFI: ~5-10mA
- Deep sleep: ~1-2mA
- Dormant mode: ~1.3mA


### Dynamic Voltage and Frequency Scaling (DVFS)

DVFS adjusts both the CPU clock frequency and supply voltage to balance
performance against power consumption. The RP2040 can run from 12MHz up
to 250MHz+.

Power consumption is proportional to:
- *Frequency*: Linear relationship (2x speed = ~2x power)
- *Voltage*: Quadratic relationship (voltage²) for dynamic power

Lower frequency allows lower voltage, giving compounded savings.

```c
// Set voltage first (must be high enough for target frequency)
vreg_set_voltage(VREG_VOLTAGE_0_95);  // 0.95V
sleep_ms(10);  // Allow voltage to stabilize

// Then change frequency
set_sys_clock_khz(48000, true);  // 48MHz

// Re-initialise peripherals that depend on clock
stdio_init_all();
```

Useful for:
- *High performance needed*: 250MHz @ 1.20V (full power)
- *Normal operation*: 125MHz @ 1.10V (default, balanced)
- *Background tasks*: 48MHz @ 0.95V (save ~60% power)
- *Idle monitoring*: 12-24MHz @ 0.85V (save ~80% power)

The CPU is typically the largest power consumer. By reducing both
voltage and frequency when high performance isn't needed, you
achieve sometimes dramatic power savings with minimal code changes.
That is also why code matters.

A temperature sensor that samples every 10 seconds:
- Run at 48MHz during sampling/transmission (~100ms)
- Save ~60% power during that active period
- Use WFI or sleep for the remaining 9.9 seconds



### Wait For Interrupt (WFI)

`__wfi()` is an ARM Cortex-M0+ instruction that puts the CPU core
into an idle state until an interrupt occurs. The processor stops
executing instructions but peripherals continue running.

When `__wfi()` executes:
1. CPU stops fetching/executing instructions
2. Clock to CPU core is gated (stopped)
3. Peripherals, timers, and DMA continue running
4. Any interrupt wakes the CPU instantly
5. Execution resumes at the next instruction

```c
// Set up an interrupt source (timer, GPIO, etc.)
gpio_set_irq_enabled_with_callback(PIN, GPIO_IRQ_EDGE_FALL, 
                                    true, &my_callback);

// Enter low power wait
while (!wake_condition) {
    __wfi();  // Sleep here until interrupt
}

// Clean up
gpio_set_irq_enabled(PIN, GPIO_IRQ_EDGE_FALL, false);
```

Useful when:
- Waiting for user input (button press)
- Waiting for sensor data ready signal
- Waiting for network packets
- Any time you'd use `sleep_ms()` or a busy-wait loop

During idle periods, the CPU is the primary power consumer even
when doing nothing. WFI stops the CPU clock entirely, saving ~50%
of active power. Peripherals continue operating, and wake time
is instant (microseconds).

```c
// BEFORE: Busy waiting (wastes power)
while (!button_pressed) {
    sleep_ms(10);  // CPU still runs at full power
}

// AFTER: Efficient waiting
while (!button_pressed) {
    __wfi();  // CPU truly idles, saves ~50% power
}
```



### Peripheral Clock Management

Each peripheral (ADC, I2C, SPI, UART, PWM, etc.) has its own clock
that can be independently enabled or disabled.
Unused peripherals waste power.

The RP2040 has multiple clock domains. When you disable a peripheral's clock:
- The peripheral stops consuming power
- Registers are preserved (state maintained)
- Re-enabling restores functionality

```c
// Disable ADC clock (saves ~0.5-1mA)
clock_stop(clk_adc);

// Later, re-enable if needed
clock_configure(clk_adc,
    0,
    CLOCKS_CLK_ADC_CTRL_AUXSRC_VALUE_CLKSRC_PLL_USB,
    48 * MHZ,
    48 * MHZ);
```

Clock domains:
- `clk_adc` - Analog to digital converter
- `clk_rtc` - Real-time clock
- `clk_peri` - Peripheral clock (UART, SPI, I2C, PWM)
- `clk_usb` - USB controller

Disable clocks for:
- Unused communication interfaces (if you're not using I2C, disable it)
- ADC when not sampling
- USB if using battery power without USB connection
- PWM when not generating signals

Each peripheral consumes power even when idle. The ADC alone uses ~0.5-1mA.
In battery applications with many unused peripherals, you can save several
milliamps.

#### Warning
It might be obvious, but:
*never disable clocks for peripherals you're actively using!*
This includes:
- Don't disable SPI if controlling a display
- Don't disable UART if using printf/stdio
- Don't disable USB if connected to a computer



### Duty Cycle Management

Instead of running continuously, the system alternates between active periods
(doing work) and sleep periods (idle). This reduces average power consumption
dramatically.

```
Timeline: |--ACTIVE--|-------SLEEP-------|--ACTIVE--|-------SLEEP-------|
   Power: |   HIGH   |        LOW        |   HIGH   |        LOW        |
```

Average power = (Active% × Active_Power) + (Sleep% × Sleep_Power)

```c
while (true) {
    // Active phase: 100ms
    read_sensor();
    process_data();
    transmit_data();
    
    // Sleep phase: 9900ms (90% duty cycle reduction)
    sleep_ms(9900);  // Or use WFI with timer interrupt
}
```

Perfect for:
- *Sensor monitoring*: Sample temperature every minute
- *Data logging*: Record values periodically
- *Motion detection*: Check sensor, sleep if no motion
- *Environmental monitoring*: Wake, measure, transmit, sleep

Most embedded applications don't need continuous operation. A sensor
that samples once per minute only needs to be active 0.01% of the
time. This gives 99.99% power savings during sleep periods.

An example could be battery-powered temperature logger:
- Active: Read sensor + log data = 50ms @ 25mA
- Sleep: 59,950ms (almost 1 minute) @ 2mA

Average current:
```
(50ms × 25mA + 59,950ms × 2mA) / 60,000ms = 2.02mA average

Battery life with 2000mAh battery:
2000mAh / 2.02mA ≈ 990 hours ≈ 41 days

Compare to continuous operation:
2000mAh / 25mA = 80 hours ≈ 3.3 days
```

So *12× longer battery life with duty cycling!*


### Sleep and Dormant Modes

The RP2040 supports deep sleep modes that stop most or all clocks:

- *Sleep Mode*: Most clocks stopped, wake from RTC or GPIO
- *Dormant Mode*: All clocks stopped except external crystal

*Sleep Mode:*
```c
#include "pico/sleep.h"

// Set up wake source (RTC alarm)
datetime_t alarm = {...};
sleep_goto_sleep_until(&alarm);
// Wakes at specified time
```

*Dormant Mode:*
```c
// Configure GPIO wake source
gpio_set_dormant_irq_enabled(PIN, GPIO_IRQ_EDGE_FALL, true);

// Enter dormant (deepest sleep)
sleep_run_from_dormant_source(DORMANT_SOURCE_XOSC);

// After wake, must restore clocks
rosc_write(&rosc_hw->ctrl, ROSC_CTRL_ENABLE_BITS);
set_sys_clock_khz(125000, true);
```

Uses:
- *Sleep mode*: Periodic wake (e.g., every hour) via RTC
- *Dormant mode*: Event-driven wake (button press, sensor interrupt)

These modes achieve the lowest possible power consumption (~1-2mA)
by stopping nearly everything. Wake time is longer (milliseconds
instead of microseconds), but for infrequent events, the power
savings can be massive.

A wildlife camera with motion sensor:
- Dormant mode: ~1.3mA waiting for motion
- Wake on PIR sensor interrupt
- Active: Capture image, log, return to dormant
- Battery life: Years instead of weeks



### Hardware Optimisations

```c
// Disable pull-ups/pull-downs on unused pins
for (int i = 0; i < 29; i++) {
    if (pin_not_used[i]) {
        gpio_set_pulls(i, false, false);
    }
}
```

Reduce SPI/I2C speed:
```c
// Slower communication = less power
spi_set_baudrate(spi0, 1000000);  // 1MHz instead of 10MHz
```

Turn Off LEDs as LEDs consume significant power (5-20mA each).
Disable status LEDs in production, if possible.

Use external voltage regulators as the Pico's onboard regulator
is convenient but not ultra-efficient. For battery applications,
consider:
- External switching regulator (>90% efficiency)
- LDO for very low power applications


### Combined Strategy: Max Power Savings

For maximum battery life, combine multiple techniques:

```c
void ultra_low_power_mode(void) {
    // 1. Lower frequency and voltage
    vreg_set_voltage(VREG_VOLTAGE_0_95);
    sleep_ms(10);
    set_sys_clock_khz(48000, true);
    
    // 2. Disable unused peripherals
    clock_stop(clk_adc);
    clock_stop(clk_usb);
    
    // 3. Disable unused GPIOs
    for (int i = 0; i < 29; i++) {
        if (!gpio_in_use[i]) {
            gpio_set_pulls(i, false, false);
        }
    }
    
    // 4. Use duty cycle: 100ms active, 9900ms sleep
    while (true) {
        // Do work
        perform_task();
        
        // Sleep with WFI
        sleep_ms(9900);  // Internally uses WFI
    }
}
```

*Power reduction:*
- Base: 30mA
- After DVFS: 12mA (60% reduction)
- After peripheral disable: 11mA (63% reduction)
- After duty cycle (1% active): 0.11mA average (99.6% reduction!)



### Tips

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


### Summary

| Technique | Power Savings | Complexity | Wake Time | Use Case |
|-----------|---------------|------------|-----------|----------|
| DVFS | 40-80% | Low | None | Continuous operation, lower performance needs |
| WFI | 50% | Very Low | Instant | Waiting for events/interrupts |
| Peripheral Disable | 5-20% | Low | None | Unused hardware modules |
| Duty Cycle | 90-99% | Low | Varies | Periodic sampling/transmission |
| Sleep Mode | 95% | Medium | ~1ms | RTC-based periodic wake |
| Dormant Mode | 97% | High | ~10ms | Event-driven wake (rare events) |

1. *Start with DVFS*: Easy to implement, significant savings
2. *Use WFI everywhere*: Replace busy-waits with WFI
3. *Disable unused peripherals*: Free power savings
4. *Design for duty cycle*: Most applications don't need continuous operation
5. *Measure everything*: Use actual measurements to validate savings
6. *Combine techniques*: Stack multiple methods for maximum effect

Power management is not all-or-nothing. Even simple techniques like
DVFS and WFI can extend battery life 2-3×. For ultra-low-power applications,
combine all techniques to achieve months or years of battery operation.

