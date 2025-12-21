from machine import Pin, Timer
import time
import random

# Initialize pins
led = Pin(15, Pin.OUT)  # External LED on GPIO 15, Physical pin 20
button = Pin(12, Pin.IN, Pin.PULL_UP)  # Button on GPIO 12 with pull-up, Physical pin 16

# Global variables
led_on_time = 0  # Timestamp when LED turns on
reaction_time = 0  # Calculated reaction time
waiting_for_press = False  # State flag

# Timer callback to turn on LED
def timer_cb(t):
    global led_on_time, waiting_for_press
    led.value(1)  # Turn on LED
    led_on_time = time.ticks_ms()  # Record time
    waiting_for_press = True
    t.deinit()  # Stop timer until next round

# Button interrupt handler
def button_handler(pin):
    global reaction_time, waiting_for_press
    if waiting_for_press:
        reaction_time = time.ticks_diff(time.ticks_ms(), led_on_time)
        print(f"Reaction time: {reaction_time} ms")
        led.value(0)  # Turn off LED
        waiting_for_press = False
        # Restart timer with random delay (1-5s)
        timer.init(period=random.randint(1000, 5000), mode=Timer.ONE_SHOT, callback=timer_cb)

# Set up button interrupt (falling edge due to pull-up)
button.irq(trigger=Pin.IRQ_FALLING, handler=button_handler)

# Initialize timer with random delay
timer = Timer()
timer.init(period=random.randint(1000, 5000), mode=Timer.ONE_SHOT, callback=timer_cb)

# Main loop
while True:
    time.sleep(0.1)  # Keep CPU responsive