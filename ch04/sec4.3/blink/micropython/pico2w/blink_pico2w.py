import machine
import time

# Initialize the onboard LED on Pico 2 W
led = machine.Pin("LED", machine.Pin.OUT)

# Blink the LED
while True:
    led.value(1)  # Turn LED on
    time.sleep(0.5)  # Wait 0.5 seconds
    led.value(0)  # Turn LED off
    time.sleep(0.5)  # Wait 0.5 seconds