import time
from machine import Pin

# LED pins for traffic lights
red_light = Pin(0, Pin.OUT)
yellow_light = Pin(1, Pin.OUT)
green_light = Pin(2, Pin.OUT)

# LED pin for pedestrian signal
walk_signal = Pin(25, Pin.OUT)  # on-board LED

# button for pedestrian crossing
button = Pin(15, Pin.IN, Pin.PULL_DOWN)

# states
STATE_GREEN = 0
STATE_YELLOW = 1
STATE_YELLOW_RED = 2
STATE_RED = 3

# timing constants
green_time = 5
yellow_time = 2
yellow_red_time = 1
red_time = 5
walk_time = 5

# interrupt handler for pedestrian button press
def pedestrian_button_pressed(pin):
    global button_pressed
    button_pressed = True # set flag button pressed

# setup interrupt for the pedestrian button
button.irq(trigger=Pin.IRQ_RISING, handler=pedestrian_button_pressed)

def set_traffic_lights(green, yellow, red):
    green_light.value(green)
    yellow_light.value(yellow)
    red_light.value(red)

def set_walk_signal(walk):
    walk_signal.value(walk)

def traffic_light():
    global button_pressed

    # init
    state = STATE_GREEN
    button_pressed = False

    while True:
        if state == STATE_GREEN:
            set_traffic_lights(1, 0, 0)  # Green on
            set_walk_signal(0)           # Don't Walk
            time.sleep(green_time)
            state = STATE_YELLOW

        elif state == STATE_YELLOW:
            set_traffic_lights(0, 1, 0)  # Yellow on
            set_walk_signal(0)           # Don't Walk
            time.sleep(yellow_time)
            state = STATE_YELLOW_RED

        elif state == STATE_YELLOW_RED:
            set_traffic_lights(0, 1, 1)  # Yellow and red on
            set_walk_signal(0)           # Don't Walk
            time.sleep(yellow_red_time)
            state = STATE_RED

        elif state == STATE_RED:
            set_traffic_lights(0, 0, 1)  # Red on
            if button_pressed == True:
                set_walk_signal(1)       # Walk
                time.sleep(walk_time)    # Walk timer
                set_walk_signal(0)       # Don't Walk
            else:
                set_walk_signal(0)       # Don't Walk
                time.sleep(red_time)     # Wait for timer
            state = STATE_GREEN

# run
traffic_light()
