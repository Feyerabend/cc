# boot.py - Executed at system startup
from machine import Pin
import time

# Init hardware
status_led = Pin(25, Pin.OUT)
status_led.value(0)  # LED off during boot

# Flash LED to indicate boot process
for i in range(3):
    status_led.value(1)
    time.sleep(0.2)
    status_led.value(0)
    time.sleep(0.2)
