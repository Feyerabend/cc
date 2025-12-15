from machine import Pin
import time

# setup LED on Pin 1 and button on Pin 20, GP15
led = Pin(0, Pin.OUT)  # LED on Pin 1
button = Pin(15, Pin.IN, Pin.PULL_DOWN)  # .. with internal pull-down resistor

while True:
    if button.value() == 1:  # button is pressed (reads high)
        led.on()
    else:
        led.off()
    time.sleep(0.1)  # delay to avoid bouncing issues
