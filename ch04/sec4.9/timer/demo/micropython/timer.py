import time
from machine import Pin, Timer
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2, PEN_P4

# Initialize display (use DISPLAY_PICO_DISPLAY_2 for Display Pack 2.0)
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, pen_type=PEN_P4, rotate=0)
display.set_backlight(0.8)
display.set_font("bitmap8")

WHITE = display.create_pen(255, 255, 255)
BLACK = display.create_pen(0, 0, 0)

# Initialize Button A (GPIO 12, pull-up, interrupt on falling edge)
button_a = Pin(12, Pin.IN, Pin.PULL_UP)

# Global counter
counter = 0

# Timer callback (called every 1s via interrupt)
def timer_cb(t):
    global counter
    counter += 1
    update_display()

# Button interrupt handler (triggered on press)
def button_handler(pin):
    global counter
    counter = 0
    update_display()

# Set up button IRQ
button_a.irq(trigger=Pin.IRQ_FALLING, handler=button_handler)

# Set up timer for 1s periodic interrupts
timer = Timer()
timer.init(period=1000, mode=Timer.PERIODIC, callback=timer_cb)

# Function to update display (called from callbacks)
def update_display():
    display.set_pen(BLACK)
    display.clear()
    display.set_pen(WHITE)
    display.text(f"Counter: {counter}", 10, 10, 240, 4)
    display.update()

# Initial display update
update_display()

# Keep the program running
while True:
    time.sleep(0.1)