import time
from machine import Pin

# LED pins for traffic lights
red_light = Pin(0, Pin.OUT)
yellow_light = Pin(1, Pin.OUT)
green_light = Pin(2, Pin.OUT)

STATE_GREEN = 0
STATE_YELLOW = 1
STATE_YELLOW_RED = 2
STATE_RED = 3

# timing constants
green_time = 5
yellow_time = 2
yellow_red_time = 1
red_time = 5

def set_traffic_lights(green, yellow, red):
    green_light.value(green)
    yellow_light.value(yellow)
    red_light.value(red)

def traffic_light():
    state = STATE_GREEN # start
    timer = 0

    while True:
        if state == STATE_GREEN:
            set_traffic_lights(1, 0, 0)  # green on
            time.sleep(green_time)
            state = STATE_YELLOW

        elif state == STATE_YELLOW:
            set_traffic_lights(0, 1, 0)  # yellow on
            time.sleep(yellow_time)
            state = STATE_YELLOW_RED

        elif state == STATE_YELLOW_RED:
            set_traffic_lights(0, 1, 1)  # yellow and red on
            time.sleep(yellow_red_time)
            state = STATE_RED

        elif state == STATE_RED:
            set_traffic_lights(0, 0, 1)  # red on
            time.sleep(red_time)
            state = STATE_GREEN

# run
traffic_light()
