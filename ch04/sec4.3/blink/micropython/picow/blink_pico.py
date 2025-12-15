import machine
import time

# Initialize the onboard LED on Pico W
led = machine.Pin("LED", machine.Pin.OUT)

# Blink LED
while True:
    led.value(1)  # Turn LED on
    time.sleep(1)  # Wait 1 second
    led.value(0)  # Turn LED off
    time.sleep(1)  # Wait 1 second
    
# Pin 25: On the Raspberry Pi Pico (non-WiFi version),
# the onboard LED is connected to GPIO pin 25.

# Pico W Difference: On the Raspberry Pi Pico W, the
# onboard LED is not directly connected to a standard
# GPIO pin like pin 25. Instead, it’s controlled via
# the Wi-Fi chip (CYW43439), and you need to use a
# special pin designation, often referred to as "LED"
# or machine.Pin("LED", machine.Pin.OUT) in MicroPython.
